"""Checks of a draft written from Zotero: do its citations hold?

Three checks, from cheap to costly:

1. every ``[@key]`` is a work of the document's collections (no LLM);
2. every literal quotation is in the PDF of a work cited with it (no LLM);
3. every cited sentence says what the cited work says: an LLM judges it against the
   passages of the work closest to the sentence and those consulted while writing
   (one call per paragraph, in a process of its own).

Results go to ``revision/verificacion.json`` and ``revision/verificacion.md``.
"""

import json
import re
from pathlib import Path

from ai_writer.background import now, process_alive, spawn_cli
from ai_writer.citations import find_citations
from ai_writer.consulta import consulted, open_index, scope, write_bibliography
from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMError, UsageLimitError, get_llm_client
from ai_writer.passages import PassageIndex
from ai_writer.processors.quotes import explain_mismatch, fragments, normalize
from ai_writer.support import _query, cited_paragraphs
from ai_writer.validation import DRAFT

RESULT = "revision/verificacion.json"
REPORT = "revision/verificacion.md"
LOG = "revision/verificacion.log"
VERDICTS = ("apoyada", "parcial", "tergiversada", "no_apoyada")
CLOSEST_PASSAGES = 4  # passages of the work nearest to the sentence shown to the judge
CONSULTED_PASSAGES = 2  # plus these many of the ones consulted while writing
MIN_QUOTE_WORDS = 6

_QUOTED = re.compile(r"«([^»]+)»|“([^”]+)”|\"([^\"]+)\"")

JUDGE_SYSTEM = """Eres un revisor estricto de citas en un documento científico. Para cada \
afirmación recibes la frase del documento, la obra citada y pasajes literales de esa obra. \
Decides si los pasajes respaldan lo que la frase atribuye a la obra.

Reglas:
- Juzga SOLO con los pasajes mostrados. No uses tu conocimiento del tema ni de la obra.
- No evalúas el estilo ni la calidad de la frase: solo si la obra dice lo que se le atribuye.
- «apoyada»: los pasajes afirman esto, con el mismo alcance, magnitud y sentido.
- «parcial»: los pasajes tratan de esto pero la frase va más allá: generaliza, añade \
condiciones o presenta como resultado propio de la obra algo que la obra recoge de otra.
- «tergiversada»: los pasajes dicen algo distinto o contrario: otra dirección del efecto, \
otra cifra, otra población u otra conclusión.
- «no_apoyada»: los pasajes no dicen nada de esto.
- Ante la duda entre dos veredictos, elige el más severo.
- En «pasaje» indica el identificador del pasaje que más pesa en tu veredicto, o null.

Responde solo con JSON: {"veredictos": [{"n": <número>, "veredicto": \
"apoyada|parcial|tergiversada|no_apoyada", "motivo": "una frase en español", "pasaje": "<id>"}]}, \
con un veredicto por cada número recibido."""


# -- 1. citations ----------------------------------------------------------


def check_citations(text: str, index: PassageIndex, allowed: set[str] | None) -> dict:
    """Citation keys of ``text`` sorted into valid, unknown, outside the collections and without PDF."""
    keys, malformed, pending = find_citations(text)
    report = {"validas": [], "desconocidas": [], "fuera_de_las_colecciones": [], "sin_pdf": [],
              "mal_formadas": malformed, "pendientes": pending}
    for key in dict.fromkeys(keys):
        work = index.work_of(key)
        if work is None:
            report["desconocidas"].append(key)
        elif allowed is not None and work.item_key not in allowed:
            report["fuera_de_las_colecciones"].append(key)
        else:
            report["validas"].append(key)
            if not index.passages_of(key):
                report["sin_pdf"].append(key)  # nothing to check its sentences against
    return report


# -- 2. literal quotations -------------------------------------------------


def check_quotes(text: str, index: PassageIndex) -> list[dict]:
    """Every quotation of ``MIN_QUOTE_WORDS`` or more in a cited sentence, looked up in the cited works."""
    texts: dict[str, str] = {}

    def full_text(key: str) -> str:
        if key not in texts:
            texts[key] = "\n\n".join(p["texto"] for p in index.passages_of(key))
        return texts[key]

    entries = []
    for paragraph in cited_paragraphs(text):
        for sentence, keys in paragraph["frases"]:
            for match in _QUOTED.finditer(sentence):
                quote = next(group for group in match.groups() if group).strip()
                if len(quote.split()) < MIN_QUOTE_WORDS:
                    continue
                entry = {"seccion": paragraph["seccion"], "cita_literal": quote, "claves": keys,
                         "encontrada_en": None, "mas_parecido": None}
                near = []
                for key in (key for key in keys if full_text(key)):
                    verbatim, closest = _verbatim(quote, full_text(key))
                    if verbatim:
                        entry["encontrada_en"] = key
                        break
                    if closest:
                        near.append((closest, key))
                if entry["encontrada_en"] is None and near:
                    found, key = max(near, key=lambda pair: pair[0]["parecido"])
                    entry["mas_parecido"] = {"clave": key, **found}
                entries.append(entry)
    return entries


def _verbatim(quote: str, text: str) -> tuple[bool, dict | None]:
    """Is ``quote`` in ``text`` word for word? If not, the closest passage and what differs.

    Words the PDF splits or joins and footnote numbers in the paper are not differences;
    a changed, added or dropped word is, however similar the rest.
    """
    words = normalize(text).split()
    for haystack in ("".join(words), "".join(w for w in words if not w.isdigit())):
        position = 0
        for piece in fragments(quote):
            needle = piece.replace(" ", "")
            position = haystack.find(needle, position)
            if position < 0:
                break
            position += len(needle)
        else:
            return True, None
    return False, explain_mismatch(quote, text)


# -- 3. support ------------------------------------------------------------


def _evidence(index: PassageIndex, sentence: str, key: str, seen: dict[str, list[int]]) -> list[dict]:
    """Passages of ``key`` for the judge: the closest to the sentence, then consulted ones."""
    work = index.work_of(key)
    ranked = index.search(_query(sentence), n=10_000, item_keys={work.item_key}, max_per_work=10_000)
    chosen = ranked[:CLOSEST_PASSAGES]
    wanted = {f"{key}#{number}" for number in seen.get(key, [])}
    chosen += [p for p in ranked[CLOSEST_PASSAGES:] if p["id"] in wanted][:CONSULTED_PASSAGES]
    return chosen


def _judge_prompt(pairs: list[dict]) -> str:
    blocks = []
    for pair in pairs:
        passages = "\n".join(
            f"  [{p['id']}] ({p['seccion']}, p. {p['paginas']}) {p['texto']}" for p in pair["pasajes"]
        )
        blocks.append(f"[{pair['n']}] Frase: {pair['frase']}\nObra citada: {pair['clave']} — "
                      f"{pair['titulo']}\nPasajes de la obra:\n{passages}")
    return "Juzga cada una de estas afirmaciones.\n\n" + "\n\n".join(blocks)


def _apply_verdicts(llm, pairs: list[dict]) -> None:
    try:
        answer = llm.complete_json(JUDGE_SYSTEM, _judge_prompt(pairs))
    except UsageLimitError:
        raise
    except LLMError as error:
        answer, failure = None, f"El juez no devolvió una respuesta legible ({error})"
    else:
        failure = "El juez no dio veredicto para esta frase"
    rows = answer.get("veredictos") if isinstance(answer, dict) else answer
    found = {}
    for row in rows if isinstance(rows, list) else []:
        try:
            number, verdict = int(row["n"]), str(row["veredicto"]).strip().lower()
        except (KeyError, TypeError, ValueError):
            continue
        if verdict in VERDICTS:
            found[number] = (verdict, str(row.get("motivo", "")).strip(), row.get("pasaje"))
    for pair in pairs:
        row = pair["row"]
        if pair["n"] in found:
            row["veredicto"], row["motivo"], passage = found[pair["n"]]
            shown = {p["id"]: p for p in pair["pasajes"]}
            if passage in shown:
                row["pasaje"] = {k: shown[passage][k] for k in ("id", "seccion", "paginas", "texto")}
        else:
            row["motivo"] = failure


def judge_support(text: str, index: PassageIndex, seen: dict[str, list[int]], llm=None,
                  previous: list[dict] | None = None, on_progress=None) -> list[dict]:
    """Judge every (sentence, cited work) of ``text``. ``previous`` verdicts are kept, so a
    run cut short by the usage limit resumes where it stopped. ``UsageLimitError`` propagates
    after ``on_progress`` has received what was judged."""
    known = {(e["frase"], e["clave"]): e for e in previous or [] if e["veredicto"] != "sin_juzgar"}
    llm = llm or get_llm_client()
    paragraphs = cited_paragraphs(text)
    entries: list[dict] = []
    for done, paragraph in enumerate(paragraphs, 1):
        to_judge, rows = [], []
        for sentence, keys in paragraph["frases"]:
            for key in keys:
                if (sentence, key) in known:
                    rows.append(known[(sentence, key)])
                    continue
                row = {"seccion": paragraph["seccion"], "frase": sentence, "clave": key,
                       "veredicto": "sin_juzgar", "motivo": "", "pasaje": None}
                rows.append(row)
                work = index.work_of(key)
                passages = _evidence(index, sentence, key, seen) if work else []
                if not passages:
                    row["motivo"] = ("La clave no existe en Zotero" if work is None
                                     else "La obra no tiene PDF indexado: no se puede comprobar")
                    continue
                to_judge.append({"n": len(to_judge) + 1, "frase": sentence, "clave": key,
                                 "titulo": work.title, "pasajes": passages, "row": row})
        if to_judge:
            try:
                _apply_verdicts(llm, to_judge)
            except UsageLimitError:
                if on_progress:
                    on_progress(entries + rows, done - 1, len(paragraphs))
                raise
        entries.extend(rows)
        if on_progress:
            on_progress(entries, done, len(paragraphs))
    return entries


def summary(entries: list[dict]) -> dict:
    """Entries per verdict and ``apoyo``: share of the judged ones that are ``apoyada``."""
    counts = {v: sum(e["veredicto"] == v for e in entries) for v in (*VERDICTS, "sin_juzgar")}
    judged = sum(counts[v] for v in VERDICTS)
    counts["apoyo"] = round(counts["apoyada"] / judged, 3) if judged else None
    return counts


# -- the document ----------------------------------------------------------


def _load(folder: Path) -> dict:
    path = Path(folder) / RESULT
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save(folder: Path, data: dict) -> None:
    path = Path(folder) / RESULT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (Path(folder) / REPORT).write_text(markdown(data), encoding="utf-8")


def _open(folder: Path) -> tuple[str, PassageIndex, set[str] | None]:
    folder = Path(folder)
    project = Project.load(folder)
    if project.fuente != "zotero":
        raise LibraryError("Este documento no toma sus obras de Zotero: no se puede verificar así.")
    if not (folder / DRAFT).exists():
        raise LibraryError(f"Todavía no hay borrador en {DRAFT}.")
    index = open_index()
    allowed = scope(project, index)
    if index.pending(allowed):
        index.update(allowed)
    return (folder / DRAFT).read_text(encoding="utf-8"), index, allowed


def check_document(folder: Path) -> dict:
    """Run the checks that need no LLM, write the bibliography and save the result."""
    text, index, allowed = _open(folder)
    citations = check_citations(text, index, allowed)
    path = write_bibliography(folder, index, citations["validas"])
    previous = _load(folder)
    data = {
        "comprobado": now(),
        "citas": citations,
        "citas_literales": check_quotes(text, index),
        "bibliografia": str(path.relative_to(Path(folder))),
        "juez": previous.get("juez", {"estado": "sin_lanzar"}),
        "apoyo": previous.get("apoyo", []),
    }
    _save(folder, data)
    return data


def start_judge(folder: Path) -> dict:
    """Launch the support judge detached for this document.

    Raises:
        LibraryError: If it is already running.
    """
    data = _load(folder) or check_document(folder)
    if judge_running(data):
        raise LibraryError("El juez de apoyo ya está en marcha para este documento.")
    pid = spawn_cli(["documento", "verificar", str(Path(folder).resolve())], Path(folder) / LOG)
    data["juez"] = {"estado": "en_curso", "pid": pid, "inicio": now(), "hechos": 0, "total": None}
    _save(folder, data)
    return data


def judge_running(data: dict) -> bool:
    judge = data.get("juez", {})
    return judge.get("estado") == "en_curso" and process_alive(judge.get("pid"))


def run_judge(folder: Path, llm=None) -> dict:
    """Judge the draft's cited sentences, saving progress after every paragraph."""
    text, index, _ = _open(folder)
    data = _load(folder) or check_document(folder)
    judge = data.setdefault("juez", {})

    def progress(entries: list[dict], done: int, total: int) -> None:
        data["apoyo"] = entries
        judge.update(hechos=done, total=total)
        _save(folder, data)

    judge.update(estado="en_curso", error=None)
    try:
        data["apoyo"] = judge_support(text, index, consulted(folder), llm, data.get("apoyo"), progress)
        judge.update(estado="terminado", fin=now())
    except UsageLimitError as error:
        judge.update(estado="limite_de_uso", error=str(error))
    except Exception as error:
        judge.update(estado="error", error=str(error))
        _save(folder, data)
        raise
    _save(folder, data)
    return data


def status(folder: Path) -> dict:
    """The saved result, with a judge that died marked as interrupted."""
    data = _load(folder)
    if not data:
        raise LibraryError("Este documento todavía no se ha verificado.")
    judge = data.get("juez", {})
    if judge.get("estado") == "en_curso" and not process_alive(judge.get("pid")):
        judge["estado"] = "interrumpido"
    return data


def overview(data: dict) -> dict:
    """What a tool returns: counts, and the entries that need the student's attention."""
    citations = data["citas"]
    quotes = data["citas_literales"]
    worst = [e for e in data.get("apoyo", []) if e["veredicto"] in ("tergiversada", "no_apoyada", "parcial")]
    order = {"tergiversada": 0, "no_apoyada": 1, "parcial": 2}
    worst.sort(key=lambda e: order[e["veredicto"]])
    return {
        "citas": {name: (len(value) if isinstance(value, list) else value) for name, value in citations.items()},
        "claves_con_problemas": {name: citations[name] for name in
                                 ("desconocidas", "fuera_de_las_colecciones", "sin_pdf", "mal_formadas")
                                 if citations[name]},
        "citas_literales": {"total": len(quotes),
                            "no_encontradas": [q for q in quotes if not q["encontrada_en"]]},
        "juez": data.get("juez", {}),
        "apoyo": summary(data.get("apoyo", [])),
        "frases_a_revisar": [
            {k: e[k] for k in ("seccion", "frase", "clave", "veredicto", "motivo")} for e in worst[:25]
        ],
        "informe": REPORT,
        "bibliografia": data.get("bibliografia"),
    }


def markdown(data: dict) -> str:
    """The report for the student, problems first."""
    citations, quotes, entries = data["citas"], data["citas_literales"], data.get("apoyo", [])
    lines = ["# Verificación del borrador", "", f"Comprobado: {data.get('comprobado', '')}", "",
             "## Citas", "",
             f"{len(citations['validas'])} obras citadas existen y están en las colecciones del documento."]
    labels = {
        "desconocidas": "No existen en Zotero",
        "fuera_de_las_colecciones": "Existen pero no están en las colecciones del documento",
        "sin_pdf": "Sin PDF en Zotero: sus frases no se pueden comprobar",
        "mal_formadas": "Citas mal escritas",
    }
    for name, label in labels.items():
        if citations[name]:
            lines.append(f"- **{label}:** " + ", ".join(citations[name]))
    if citations["pendientes"]:
        lines.append(f"- Quedan {citations['pendientes']} citas por buscar (`[@?]`).")

    lines += ["", "## Citas literales", ""]
    missing = [q for q in quotes if not q["encontrada_en"]]
    lines.append(f"{len(quotes) - len(missing)} de {len(quotes)} citas literales están tal cual en el PDF."
                 if quotes else "El borrador no tiene citas literales de 6 palabras o más.")
    for quote in missing:
        lines.append(f"- **No está en el PDF** ({', '.join(quote['claves'])}): «{quote['cita_literal']}»")
        near = quote["mas_parecido"]
        if near:
            lines.append(f"  - Lo más parecido, en {near['clave']}: «{near['pasaje']}»")
            for change in near["diferencias"]:
                lines.append(f"  - El borrador dice «{change['cita']}» y el PDF dice «{change['texto']}»")
        else:
            lines.append("  - No hay nada parecido en las obras citadas. Si está traducida, déjala en "
                         "el idioma original o quita las comillas.")

    lines += ["", "## Apoyo de las frases citadas", ""]
    judge = data.get("juez", {})
    if not entries:
        lines.append("El juez de apoyo no se ha lanzado todavía." if judge.get("estado") == "sin_lanzar"
                     else f"Juez: {judge.get('estado')}.")
        return "\n".join(lines) + "\n"
    stats = summary(entries)
    apoyo = "sin datos" if stats["apoyo"] is None else f"{stats['apoyo']:.0%}"
    lines += [
        f"Apoyo: {apoyo} ({stats['apoyada']} apoyadas, {stats['parcial']} parciales, "
        f"{stats['tergiversada']} tergiversadas, {stats['no_apoyada']} no apoyadas, "
        f"{stats['sin_juzgar']} sin juzgar). Estado del juez: {judge.get('estado')}.",
        "Un juez automático compara cada frase con pasajes de la obra citada. Se equivoca a veces: "
        "revisa a mano las peores.", "",
    ]
    names = {"tergiversada": "Tergiversada", "no_apoyada": "No apoyada", "parcial": "Parcial",
             "sin_juzgar": "Sin juzgar"}
    for verdict, name in names.items():
        for entry in (e for e in entries if e["veredicto"] == verdict):
            lines.append(f"- **{name}** [@{entry['clave']}] ({entry['seccion'] or 'sin sección'}): «{entry['frase']}»")
            if entry["motivo"]:
                lines.append(f"  - Motivo: {entry['motivo']}")
            if entry.get("pasaje"):
                passage = entry["pasaje"]
                lines.append(f"  - La obra dice ({passage['seccion']}, p. {passage['paginas']}): "
                             f"«{passage['texto'][:600]}»")
    return "\n".join(lines) + "\n"
