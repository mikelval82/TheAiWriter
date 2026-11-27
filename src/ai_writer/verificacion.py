"""Checks of a draft written from Zotero: do its citations hold?

Six checks, five without a model:

1. every ``[@key]`` is a work of the document's collections (no LLM);
2. every literal quotation is in the PDF of a work cited with it (no LLM);
3. every cited sentence says what the cited work says: an LLM judges it against the
   passages of the work closest to the sentence and those consulted while writing
   (one call per paragraph, in a process of its own).
4. a results document's own figures occur in its CSV or Markdown results (no LLM).
5. a call document follows requirements quoted from its official PDFs (no LLM);
6. sentences that tell what a work says carry a citation (no LLM, by their wording).

Results go to ``informes/comprobacion.json`` and ``informes/comprobacion.md``.
"""

import json
import re
from hashlib import sha256
from pathlib import Path

from ai_writer.avisos import add_notice
from ai_writer.background import now, process_alive, spawn_cli
from ai_writer.cifras import check_figures, lines_without_code
from ai_writer.citations import find_citations
from ai_writer.consulta import BIBLIOGRAPHY, consulted, open_index, scope, write_bibliography
from ai_writer.convocatoria import (
    CallFicha,
    budget_inputs_changed,
    check_call,
    check_ficha,
    check_final_pdf,
    final_pdf_is_stale,
    report_lines,
)
from ai_writer.hallazgos import list_findings
from ai_writer.hallazgos_borrador import check_findings, findings_changed
from ai_writer.hallazgos_borrador import report_lines as findings_report_lines
from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMError, UsageLimitError, get_llm_client
from ai_writer.passages import PassageIndex
from ai_writer.quotes import explain_mismatch, fragments, normalize
from ai_writer.sentences import (
    cited_paragraphs,
    fold_text,
    literature_gaps,
    sentence_query,
    uncited_attributions,
)

DRAFT = Path("borrador") / "documento.md"
RESULT = "informes/comprobacion.json"
REPORT = "informes/comprobacion.md"
LOG = "informes/comprobacion.log"
VERDICTS = ("apoyada", "parcial", "tergiversada", "no_apoyada")
CLOSEST_PASSAGES = 4  # passages of the work nearest to the sentence shown to the judge
CONSULTED_PASSAGES = 16  # plus up to these many of the ones consulted while writing
MIN_QUOTE_WORDS = 6
UNJUDGED = "Frase nueva, cambiada o pendiente: falta pasar el juez"

_QUOTED = re.compile(r"«([^»]+)»|“([^”]+)”|\"([^\"]+)\"")

JUDGE_SYSTEM = """Eres un revisor estricto de citas en un documento científico. Para cada \
afirmación recibes la frase del documento, la obra citada y pasajes literales de esa obra. \
Decides si los pasajes respaldan lo que la frase atribuye a la obra.

Reglas:
- Juzga SOLO con los pasajes mostrados. No uses tu conocimiento del tema ni de la obra.
- No evalúas el estilo ni la calidad de la frase: solo si la obra dice lo que se le atribuye.
- El párrafo se muestra para saber a qué se refiere cada frase («estos modelos», «se usó», un \
sujeto omitido). Resuelve esas referencias antes de juzgar; que una frase dependa de la \
anterior no es un fallo. No juzgues el resto del párrafo ni lo uses como prueba de lo que \
dice la obra.
- Se atribuye a la obra la parte de la frase que su cita cierra. No se le atribuye lo que \
la frase dice del propio documento (lo que se hará, se propone o se evaluará, sus hipótesis \
o su valoración) ni lo que se atribuye a otra cita de la misma frase. Si la cita va al final \
y la frase mezcla lo de la obra con lo propio, juzga solo lo que se presenta como de la obra.
- «apoyada»: los pasajes afirman esto, con el mismo alcance, magnitud y sentido.
- «parcial»: los pasajes tratan de esto pero la frase va más allá: generaliza, añade \
condiciones o presenta como resultado propio de la obra algo que la obra recoge de otra.
- «tergiversada»: los pasajes dicen algo distinto o contrario: otra dirección del efecto, \
otra cifra, otra población u otra conclusión.
- «no_apoyada»: los pasajes no dicen nada de esto.
- Ante la duda entre dos veredictos, elige el más severo.
- Para «apoyada», «parcial» y «tergiversada», indica en «pasaje» el identificador de uno de \
los pasajes mostrados que fundamenta el veredicto. En «fragmento» copia un fragmento literal \
breve y consecutivo de ese mismo pasaje. Si ninguna de las muestras da apoyo, usa \
«no_apoyada» y deja «pasaje» y «fragmento» a null.

Responde solo con JSON: {"veredictos": [{"n": <número>, "veredicto": \
"apoyada|parcial|tergiversada|no_apoyada", "motivo": "una frase en español", \
"pasaje": "<id>|null", "fragmento": "<cita literal>|null"}]}, \
con un veredicto por cada número recibido."""


# -- 1. citations ----------------------------------------------------------


def check_citations(text: str, index: PassageIndex, allowed: set[str] | None) -> dict:
    """Sort citation keys into valid, unknown, outside collections and without PDF."""
    keys, malformed, pending = find_citations(text)
    report = {
        "validas": [],
        "desconocidas": [],
        "fuera_de_las_colecciones": [],
        "sin_pdf": [],
        "mal_formadas": malformed,
        "pendientes": pending,
    }
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
    if allowed is not None:  # works of the document's collections that the draft never cites
        cited = {index.work_of(key).item_key for key in report["validas"]}
        report["en_coleccion"] = len(allowed)
        report["sin_citar"] = sorted(index.keys.get(item, item) for item in allowed - cited)
    return report


# -- 2. literal quotations -------------------------------------------------


def check_quotes(text: str, index: PassageIndex) -> list[dict]:
    """Look up quotations of at least ``MIN_QUOTE_WORDS`` in the works cited with them."""
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
                entry = {
                    "seccion": paragraph["seccion"],
                    "cita_literal": quote,
                    "claves": keys,
                    "encontrada_en": None,
                    "mas_parecido": None,
                }
                near = []
                for key in (key for key in keys if full_text(key)):
                    found, closest = verbatim(quote, full_text(key))
                    if found:
                        entry["encontrada_en"] = key
                        break
                    if closest:
                        near.append((closest, key))
                if entry["encontrada_en"] is None and near:
                    found, key = max(near, key=lambda pair: pair[0]["parecido"])
                    entry["mas_parecido"] = {"clave": key, **found}
                entries.append(entry)
    return entries


def verbatim(quote: str, text: str, *, explain: bool = True) -> tuple[bool, dict | None]:
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
    return False, explain_mismatch(quote, text) if explain else None


# -- 3. support ------------------------------------------------------------


def _judge_passages(
    index: PassageIndex, sentence: str, key: str, seen: dict[str, list[int]]
) -> list[dict]:
    """Passages of ``key`` for the judge: the closest to the sentence, then consulted ones.
    Ranked by meaning only: word matches mislead when the draft and the work differ in language."""
    work = index.work_of(key)
    ranked = index.search(
        sentence_query(sentence),
        n=10_000,
        item_keys={work.item_key},
        max_per_work=10_000,
        lexical=False,
    )
    chosen = ranked[:CLOSEST_PASSAGES]
    wanted = {f"{key}#{number}" for number in seen.get(key, [])}
    chosen += [p for p in ranked[CLOSEST_PASSAGES:] if p["id"] in wanted][:CONSULTED_PASSAGES]
    return chosen


def _judge_prompt(pairs: list[dict], paragraph: str) -> str:
    blocks = []
    for pair in pairs:
        passages = "\n".join(
            f"  [{p['id']}] ({p['seccion']}, p. {p['paginas']}) {p['texto']}"
            for p in pair["pasajes"]
        )
        blocks.append(
            f"[{pair['n']}] Frase: {pair['frase']}\nObra citada: {pair['clave']} — "
            f"{pair['titulo']}\nPasajes de la obra:\n{passages}"
        )
    return (
        f"Juzga cada una de estas afirmaciones.\n\nPárrafo del documento: {paragraph}\n\n"
        + "\n\n".join(blocks)
    )


def _apply_verdicts(llm, pairs: list[dict], paragraph: str) -> None:
    try:
        answer = llm.complete_json(JUDGE_SYSTEM, _judge_prompt(pairs, paragraph))
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
            found[number] = (verdict, str(row.get("motivo", "")).strip(),
                             row.get("pasaje"), row.get("fragmento"))
    for pair in pairs:
        row = pair["row"]
        proposed = found.get(pair["n"])
        if proposed is None:
            row["motivo"] = failure
            continue
        verdict, reason, passage_id, excerpt = proposed
        passage = next((p for p in pair["pasajes"] if p["id"] == passage_id), None)
        if passage is None and verdict != "no_apoyada":
            row["motivo"] = "El juez no indicó un pasaje válido de la obra citada."
            continue
        row.update(veredicto=verdict, motivo=reason)
        if passage is not None:
            row["pasaje"] = _passage_record(passage, excerpt)
        elif verdict == "no_apoyada":
            row["pasajes_consultados"] = [
                {key: value for key, value in _passage_record(p).items() if key != "texto"}
                for p in pair["pasajes"][:CLOSEST_PASSAGES]
            ]


def _passage_record(passage: dict, excerpt: object = None) -> dict:
    record = {key: passage[key] for key in (
        "id", "titulo", "archivo", "seccion", "paginas", "zotero_url", "texto"
    ) if key in passage}
    if isinstance(excerpt, str):
        fragment = " ".join(excerpt.split())
        if fragment and fragment in " ".join(passage["texto"].split()):
            record["fragmento"] = fragment
    return record


def _fresh_support(entries: list[dict], index: PassageIndex, allowed: set[str] | None) -> list[dict]:
    """Keep anchored verdicts and recover links in older reports when the passage still matches."""
    current, stamps, passages = [], {}, {}
    for entry in entries:
        if entry["veredicto"] == "sin_juzgar":
            current.append(entry)
            continue
        key = entry["clave"]
        work = index.work_of(key)
        if not work or (allowed is not None and work.item_key not in allowed):
            continue
        if key not in stamps:
            stamps[key] = index.source_stamp(key)
        stamp = stamps[key]
        if not stamp:
            continue
        if entry.get("huella_fuente") == stamp:
            if entry.get("pasaje") or entry["veredicto"] == "no_apoyada":
                current.append(entry)
        elif "huella_fuente" not in entry and (previous := entry.get("pasaje")):
            if key not in passages:
                passages[key] = {p["id"]: p for p in index.passages_of(key)}
            passage = passages[key].get(previous["id"])
            if passage and all(passage[k] == previous[k] for k in ("paginas", "texto", "seccion")):
                current.append({
                    **entry,
                    "huella_fuente": stamp,
                    "pasaje": _passage_record(passage, previous.get("fragmento")),
                })
    return current


def _find(known: dict, sentence: str, key: str, before: str) -> dict | None:
    """The verdict of this sentence, unless the one before it changed: it may refer to it."""
    entry = known.get((sentence, key))
    return entry if entry and entry.get("previa", before) == before else None


def current_support(text: str, entries: list[dict]) -> tuple[list[dict], bool]:
    """``entries`` as they stand for ``text``: without sentences the draft no longer has, and
    with its new or changed ones as ``sin_juzgar``. Also says whether there are any of these."""
    known = {(e["frase"], e["clave"]): e for e in entries}
    current, new = [], False
    for paragraph in cited_paragraphs(text):
        for (sentence, keys), before in zip(paragraph["frases"], paragraph["previas"]):
            for key in keys:
                entry = _find(known, sentence, key, before)
                if entry is None:
                    new = True
                    entry = _row(paragraph, sentence, key, before, UNJUDGED)
                current.append({**entry, "seccion": paragraph["seccion"]})
    return current, new


def _row(paragraph: dict, sentence: str, key: str, before: str, reason: str = "") -> dict:
    return {
        "seccion": paragraph["seccion"],
        "frase": sentence,
        "previa": before,
        "clave": key,
        "veredicto": "sin_juzgar",
        "motivo": reason,
        "pasaje": None,
    }


def judge_support(
    text: str,
    index: PassageIndex,
    seen: dict[str, list[int]],
    llm=None,
    previous: list[dict] | None = None,
    on_progress=None,
    allowed: set[str] | None = None,
) -> list[dict]:
    """Judge every (sentence, cited work) of ``text``. ``previous`` verdicts are kept, so a
    run cut short by the usage limit resumes where it stopped. ``UsageLimitError`` propagates
    after ``on_progress`` has received what was judged."""
    fresh = _fresh_support(previous or [], index, allowed)
    known = {(e["frase"], e["clave"]): e for e in fresh if e["veredicto"] != "sin_juzgar"}
    stamps = {}
    llm = llm or get_llm_client()
    paragraphs = cited_paragraphs(text)
    entries: list[dict] = []
    for done, paragraph in enumerate(paragraphs, 1):
        to_judge, rows = [], []
        for (sentence, keys), before in zip(paragraph["frases"], paragraph["previas"]):
            for key in keys:
                if entry := _find(known, sentence, key, before):
                    rows.append({**entry, "seccion": paragraph["seccion"]})
                    continue
                row = _row(paragraph, sentence, key, before)
                rows.append(row)
                work = index.work_of(key)
                if work and allowed is not None and work.item_key not in allowed:
                    row["motivo"] = "La obra está fuera de las colecciones y no se puede comprobar."
                    continue
                if key not in stamps:
                    stamps[key] = index.source_stamp(key)
                stamp = stamps[key]
                passages = _judge_passages(index, sentence, key, seen) if stamp else []
                if not passages:
                    row["motivo"] = (
                        "La clave no existe en Zotero"
                        if work is None
                        else "La obra no tiene PDF indexado: no se puede comprobar"
                    )
                    continue
                row["huella_fuente"] = stamp
                to_judge.append(
                    {
                        "n": len(to_judge) + 1,
                        "frase": sentence,
                        "clave": key,
                        "titulo": work.title,
                        "pasajes": passages,
                        "row": row,
                    }
                )
        if to_judge:
            try:
                _apply_verdicts(llm, to_judge, paragraph["texto"])
            except UsageLimitError:
                if on_progress:
                    on_progress(entries + rows, done - 1, len(paragraphs))
                raise
        entries.extend(rows)
        if on_progress:
            on_progress(entries, done, len(paragraphs))
    return entries


def draft_fingerprint(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def count_cited_pairs(text: str) -> int:
    return sum(len(keys) for paragraph in cited_paragraphs(text) for _, keys in paragraph["frases"])


def summary(entries: list[dict], *, total: int | None = None) -> dict:
    """Count verdicts for sentence–work pairs, including pairs still awaiting judgment."""
    counts = {v: sum(e["veredicto"] == v for e in entries) for v in VERDICTS}
    judged = sum(counts.values())
    total = max(len(entries), total if total is not None else len(entries))
    return {
        **counts,
        "total": total,
        "juzgadas": judged,
        "sin_juzgar": total - judged,
        "apoyo": round(counts["apoyada"] / judged, 3) if judged else None,
    }


def support_summary(data: dict) -> dict:
    return summary(data.get("apoyo", []), total=data.get("total_pares_citados"))


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
    if not (folder / DRAFT).exists():
        raise LibraryError(f"Todavía no hay borrador en {DRAFT}.")
    index = open_index()
    allowed = scope(project, index)
    if index.pending(allowed):
        index.update(allowed)
    return (folder / DRAFT).read_text(encoding="utf-8"), index, allowed


def check_document(folder: Path, *, bibliography: bool = True) -> dict:
    """Run checks without an LLM and save them; optionally update the bibliography."""
    return _check_document(folder, *_open(folder), bibliography=bibliography)


def _check_document(
    folder: Path, text: str, index: PassageIndex, allowed: set[str] | None, *, bibliography: bool
) -> dict:
    citations = check_citations(text, index, allowed)
    path = (write_bibliography(folder, index, citations["validas"])
            if bibliography else Path(folder) / BIBLIOGRAPHY)
    previous = _load(folder)
    judge = previous.get("juez", {"estado": "sin_lanzar"})
    support = previous.get("apoyo", [])
    if support and not judge_running(previous):  # the draft may have changed since the judge ran
        support, new = current_support(text, _fresh_support(support, index, allowed))
        if new and judge["estado"] == "terminado":
            judge["estado"] = "desactualizado"
    surnames = {m.group(0) for key in index.keys.values() if (m := re.match("[a-z]+", key))}
    uncited = uncited_attributions(text, surnames)
    data = {
        "comprobado": now(),
        "borrador_sha256": draft_fingerprint(text),
        "total_pares_citados": count_cited_pairs(text),
        "citas": citations,
        "citas_literales": check_quotes(text, index),
        "bibliografia": str(path.relative_to(Path(folder))) if path.exists() else None,
        "atribuciones_sin_cita": uncited,
        "fuentes_por_revisar": literature_gaps("\n".join(lines_without_code(text)), uncited),
        "juez": judge,
        "apoyo": support,
    }
    kind = Project.load(folder).tipo
    if kind == "resultados":
        finding_report = check_findings(text, list_findings(folder))
        if finding_report is None:
            data["cifras"] = check_figures(text, Path(folder) / "resultados")
        else:
            data["hallazgos_borrador"] = finding_report
    if kind == "convocatoria":
        try:
            call_ficha = CallFicha.load(folder)
        except LibraryError as error:
            ficha = {"error": str(error)}
        else:
            ficha = check_ficha(folder, call_ficha)
        data["ficha"] = ficha
        if "error" in ficha or ficha["fallidos"]:
            data["convocatoria"] = {
                "aviso": "No se puede comprobar el borrador: se necesita una ficha sin errores."
            }
        else:
            call = check_call(text, call_ficha, modalidad=ficha.get("modalidad", {}).get("seleccion"))
            call["pdf_final"] = check_final_pdf(folder, call_ficha, ficha, call["extension"])
            data["convocatoria"] = call
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
    text, index, allowed = _open(folder)
    data = _load(folder)
    if data.get("borrador_sha256") != draft_fingerprint(text):
        data = _check_document(folder, text, index, allowed, bibliography=True)
    judge = data.setdefault("juez", {})

    def progress(entries: list[dict], done: int, total: int) -> None:
        data["apoyo"] = entries
        judge.update(hechos=done, total=total)
        _save(folder, data)

    judge.update(estado="en_curso", error=None)
    try:
        data["apoyo"] = judge_support(
            text, index, consulted(folder), llm, data.get("apoyo"), progress, allowed
        )
        judge.update(estado="terminado", fin=now())
    except UsageLimitError as error:
        judge.update(estado="limite_de_uso", error=str(error))
    except Exception as error:
        judge.update(estado="error", error=str(error))
        raise
    finally:
        judge["fin"] = now()
        _save(folder, data)
        stats = support_summary(data)
        message = (
            f"El juez de citas ha terminado. Ha juzgado {stats['juzgadas']} de {stats['total']} "
            f"pares de frase y obra. {stats['apoyada']} apoyados y "
            f"{stats['sin_juzgar']} pendientes de juicio. "
        )
        if judge["estado"] != "terminado":
            message = (f"El juez de citas se ha detenido: {judge['estado']}. "
                       "Reanuda con /theaiwriter:comprobar. ")
        add_notice(folder, message + "Detalle en informes/comprobacion.md.")
    return data


def status(folder: Path, *, findings: list[dict] | None = None) -> dict:
    """Read the report and flag interrupted runs and changed verification inputs."""
    data = _load(folder)
    if not data:
        raise LibraryError("Este documento todavía no se ha comprobado.")
    judge = data.get("juez", {})
    if judge.get("estado") == "en_curso" and not process_alive(judge.get("pid")):
        judge["estado"] = "interrumpido"
    if findings is None and ("hallazgos_borrador" in data or "cifras" in data):
        findings = list_findings(folder)
    if findings is not None and findings_changed(data.get("hallazgos_borrador"), findings):
        data["hallazgos_desactualizados"] = True
    if final := data.get("convocatoria", {}).get("pdf_final"):
        if final_pdf_is_stale(folder, final):
            final.update(estado="desactualizado", paginas=None,
                         motivo="El PDF final cambió desde la última comprobación.")
    if budget := data.get("ficha", {}).get("idioma_por_presupuesto"):
        if budget_inputs_changed(folder, budget):
            budget.update(estado="desactualizado", pregunta=None)
    return data


def citation_evidence(
    folder: Path, *, phrase: str = "", section: str = "", offset: int = 0, limit: int = 12
) -> dict:
    """Read saved verdicts and their PDF links for the current manuscript, without a model."""
    if offset < 0 or not 1 <= limit <= 25:
        raise LibraryError("Indica desde ≥ 0 y un límite entre 1 y 25.")
    folder = Path(folder)
    project = Project.load(folder)
    data = status(folder)
    draft = folder / DRAFT
    if not draft.is_file():
        raise LibraryError(f"Todavía no hay borrador en {DRAFT}.")
    text = draft.read_text(encoding="utf-8")
    index = open_index()
    entries, changed = current_support(
        text, _fresh_support(data.get("apoyo", []), index, scope(project, index))
    )
    phrase, section = fold_text(phrase.strip()), fold_text(section.strip())
    filtered = [
        {key: entry[key] for key in (
            "seccion", "frase", "clave", "veredicto", "motivo", "pasaje", "pasajes_consultados"
        ) if key in entry}
        for entry in entries
        if phrase in fold_text(entry["frase"]) and section in fold_text(entry["seccion"])
    ]
    return {
        "total": len(filtered), "desde": offset,
        "siguiente_desde": offset + limit if offset + limit < len(filtered) else None,
        "desactualizado": data.get("borrador_sha256") != draft_fingerprint(text) or (
            changed and data.get("juez", {}).get("estado") == "terminado"
        ),
        "resultados": filtered[offset:offset + limit],
        "informe": REPORT,
    }


def overview(data: dict) -> dict:
    """What a tool returns: counts, and the entries that need the student's attention."""
    citations = data["citas"]
    quotes = data["citas_literales"]
    worst = [
        e
        for e in data.get("apoyo", [])
        if e["veredicto"] in ("tergiversada", "no_apoyada", "parcial")
    ]
    order = {"tergiversada": 0, "no_apoyada": 1, "parcial": 2}
    worst.sort(key=lambda e: order[e["veredicto"]])
    report = {
        "citas": {
            name: (len(value) if isinstance(value, list) else value)
            for name, value in citations.items()
        },
        "claves_con_problemas": {
            name: citations[name]
            for name in ("desconocidas", "fuera_de_las_colecciones", "sin_pdf", "mal_formadas")
            if citations[name]
        },
        "citas_literales": {
            "total": len(quotes),
            "no_encontradas": [q for q in quotes if not q["encontrada_en"]],
        },
        "atribuciones_sin_cita": data.get("atribuciones_sin_cita", []),
        "fuentes_por_revisar": data.get("fuentes_por_revisar", []),
        "juez": data.get("juez", {}),
        "apoyo": support_summary(data),
        "frases_a_revisar": [
            {k: e[k] for k in ("seccion", "frase", "clave", "veredicto", "motivo")}
            for e in worst[:25]
        ],
        "informe": REPORT,
        "bibliografia": data.get("bibliografia"),
    }
    for key in ("cifras", "hallazgos_borrador", "hallazgos_desactualizados", "ficha", "convocatoria"):
        if key in data:
            report[key] = data[key]
    return report


def _passage_location(passage: dict) -> str:
    pages = f"p. {passage['paginas']}"
    if url := passage.get("zotero_url"):
        pages = f"[{pages} en Zotero]({url})"
    location = f"`{passage['id']}` · {passage['seccion']} · {pages}"
    if filename := passage.get("archivo"):
        location += f" · {filename}"
    return location


def markdown(data: dict) -> str:
    """The report for the student, problems first."""
    citations, quotes, entries = data["citas"], data["citas_literales"], data.get("apoyo", [])
    lines = [
        "# Comprobación del borrador",
        "",
        f"Comprobado: {data.get('comprobado', '')}",
        "",
        "## Citas",
        "",
        f"{len(citations['validas'])} obras citadas existen "
        "y están en las colecciones del documento.",
    ]
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
    if citations.get("sin_citar"):
        total = citations["en_coleccion"]
        lines.append(
            f"- **Cobertura:** el borrador cita {total - len(citations['sin_citar'])} de las "
            f"{total} obras de sus colecciones. Sin citar: " + ", ".join(citations["sin_citar"])
            + ". Revisa si alguna aporta algo que falta; no hace falta citarlas todas."
        )

    if uncited := data.get("atribuciones_sin_cita"):
        lines += [
            "", "## Frases que parecen hablar de una obra y no llevan cita", "",
            "Sin cita nadie las comprueba. Si dicen lo que dice una obra, pon su `[@clave]` en "
            "la misma frase; si son tuyas, déjalas. Se buscan por sus palabras: puede haber "
            "avisos de más y faltar alguna.",
        ]
        lines += [f"- ({e['seccion'] or 'sin sección'}) «{e['frase']}»" for e in uncited]

    if gaps := data.get("fuentes_por_revisar"):
        reasons = {
            "fuente_pendiente": "Fuente marcada como pendiente",
            "afirmacion_empirica": "Menciona un hallazgo de la literatura sin citarlo",
            "porcentaje": "Porcentaje sin referencia explícita",
        }
        lines += ["", "## Afirmaciones cuya fuente conviene revisar", ""]
        for entry in gaps:
            reason = reasons[entry["motivo"]]
            lines.append(f"- {reason} ({entry['seccion'] or 'sin sección'}) «{entry['frase']}»")
        lines.append("Revisa estos avisos y confirma si la frase necesita una fuente.")

    lines += ["", "## Citas literales", ""]
    missing = [q for q in quotes if not q["encontrada_en"]]
    lines.append(
        f"{len(quotes) - len(missing)} de {len(quotes)} citas literales están tal cual en el PDF."
        if quotes
        else "El borrador no tiene citas literales de 6 palabras o más."
    )
    for quote in missing:
        lines.append(
            f"- **No está en el PDF** ({', '.join(quote['claves'])}): «{quote['cita_literal']}»"
        )
        near = quote["mas_parecido"]
        if near:
            lines.append(f"  - Lo más parecido, en {near['clave']}: «{near['pasaje']}»")
            for change in near["diferencias"]:
                lines.append(
                    f"  - El borrador dice «{change['cita']}» y el PDF dice «{change['texto']}»"
                )
        else:
            lines.append(
                "  - No hay nada parecido en las obras citadas. Si está traducida, déjala en "
                "el idioma original o quita las comillas."
            )

    if "cifras" in data:
        figures = data["cifras"]
        lines += [
            "", "## Cifras propias", "",
            f"{figures['comprobadas']} cifras comprobadas; {figures['con_origen']} con origen.",
        ]
        if figures.get("aviso"):
            lines.append(figures["aviso"])
        for entry in figures["sin_origen"]:
            lines.append(
                f"- **Sin origen: {entry['cifra']}** "
                f"({entry['seccion'] or 'sin sección'}): «{entry['frase']}»"
            )
        if not figures["sin_origen"]:
            lines.append("Todas las cifras comprobadas tienen origen en los resultados.")
        lines += [
            "", "La comprobación confirma que la cifra existe en los resultados, "
            "no que la frase la describa bien.",
        ]

    if "hallazgos_borrador" in data:
        lines.extend(findings_report_lines(data["hallazgos_borrador"]))

    if "ficha" in data:
        lines.extend(report_lines(data["ficha"], data["convocatoria"]))

    lines += ["", "## Apoyo de las frases citadas", ""]
    judge = data.get("juez", {})
    stats = support_summary(data)
    lines.append(
        f"Cobertura: {stats['juzgadas']} de {stats['total']} pares de frase y obra juzgados. "
        f"{stats['sin_juzgar']} pendientes."
    )
    if not entries:
        lines.append(
            "El juez de apoyo no se ha lanzado todavía."
            if judge.get("estado") == "sin_lanzar"
            else f"Juez: {judge.get('estado')}."
        )
        return "\n".join(lines) + "\n"
    lines += [
        f"De los juzgados: {stats['apoyada']} apoyados, {stats['parcial']} parciales, "
        f"{stats['tergiversada']} tergiversados y {stats['no_apoyada']} sin apoyo. "
        f"Estado del juez: {judge.get('estado')}.",
        "Un juez automático compara cada frase con pasajes de la obra citada. Se equivoca a veces: "
        "revisa también los pasajes de las citas que marca como apoyadas.",
        "",
    ]
    if judge.get("estado") == "desactualizado":
        lines += [
            "**El borrador ha cambiado o hay evidencia nueva desde que pasó el juez.** "
            "Las frases afectadas salen sin juzgar. Usa `/theaiwriter:comprobar` para actualizarlas.", "",
        ]
    names = {
        "tergiversada": "Tergiversada",
        "no_apoyada": "No apoyada",
        "parcial": "Parcial",
        "sin_juzgar": "Sin juzgar",
        "apoyada": "Apoyada",
    }
    for verdict, name in names.items():
        matching = [entry for entry in entries if entry["veredicto"] == verdict]
        if verdict == "apoyada" and matching:
            lines += ["", "### Pasajes de las citas apoyadas", ""]
        for entry in matching:
            lines.append(
                f"- **{name}** [@{entry['clave']}] "
                f"({entry['seccion'] or 'sin sección'}): «{entry['frase']}»"
            )
            if entry["motivo"]:
                lines.append(f"  - Motivo: {entry['motivo']}")
            if entry.get("pasaje"):
                passage = entry["pasaje"]
                lines.append(f"  - Pasaje · {_passage_location(passage)}")
                preview = " ".join(passage["texto"].split())
                if fragment := passage.get("fragmento"):
                    lines.append(f"  - Fragmento señalado · «{fragment}»")
                else:
                    ending = "…" if len(preview) > 420 else ""
                    lines.append(f"  - Inicio del pasaje · «{preview[:420]}{ending}»")
            elif consulted_passages := entry.get("pasajes_consultados"):
                lines.append("  - Pasajes consultados")
                lines.extend(f"    - {_passage_location(p)}" for p in consulted_passages)
    return "\n".join(lines) + "\n"
