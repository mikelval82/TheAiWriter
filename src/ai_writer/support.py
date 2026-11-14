"""Does each cited work say what the sentence claims?

Compares every cited sentence of the draft with the evidence the library holds from
the cited work, using an LLM as a strict judge (one call per paragraph).
"""

import json
import re
from pathlib import Path

from ai_writer.citations import find_citations
from ai_writer.evidence import EvidenceEngine
from ai_writer.library import Project
from ai_writer.llm import LLMError, UsageLimitError, get_llm_client
from ai_writer.validation import DRAFT, RETRIEVED, SUPPORT, seen_evidence

VERDICTS = ("apoyada", "parcial", "no_apoyada")
MAX_EVIDENCE = 12  # items shown to the judge per (sentence, work)
NO_EVIDENCE = "La biblioteca no tiene evidencia de esta obra para esta frase"

_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_CITE_MARKUP = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\[PENDIENTE[^\]]*\]\]")
_ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|et al|cf|vs|pp?|fig|figs|no|dr|dra|sr|sra)\.", re.I)
_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_DOT = "\x01"

JUDGE_SYSTEM = """Eres un revisor estricto de citas en un documento científico. Para cada \
afirmación recibes la frase del documento, la obra citada y la evidencia que la biblioteca \
guarda de esa obra. Decides si la evidencia respalda la frase.

Reglas:
- Juzga SOLO con la evidencia mostrada. No uses tu conocimiento propio del tema ni de la obra, \
aunque sepas que la frase es cierta.
- No evalúas el estilo, la redacción ni la calidad de la frase: solo si la obra dice lo que la frase le atribuye.
- «apoyada»: la evidencia afirma esto, con el mismo alcance, magnitud y sentido.
- «parcial»: la evidencia está relacionada pero la frase va más allá: generaliza, cambia la \
magnitud o el sentido, añade condiciones, o presenta como hallazgo propio de la obra algo que la \
evidencia marca como «citado» (afirmación de segunda mano que la obra recoge de otra).
- «no_apoyada»: la evidencia no dice esto.
- Ante la duda entre dos veredictos, elige el más severo.
- Las citas literales son frases copiadas del texto de la obra y pesan más que los resúmenes.

Responde solo con JSON: {"veredictos": [{"n": <número>, "veredicto": "apoyada|parcial|no_apoyada", \
"motivo": "una frase en español"}]}, con un veredicto por cada número recibido."""


def split_sentences(paragraph: str) -> list[str]:
    """Sentences of a paragraph; never splits inside ``[...]`` or on common abbreviations."""
    groups: list[str] = []

    def hide(match: re.Match) -> str:
        groups.append(match.group(0))
        return f"\x00{len(groups) - 1}\x00"

    masked = re.sub(r"\[[^\[\]]*\]", hide, " ".join(paragraph.split()))
    masked = _ABBREVIATION.sub(lambda m: m.group(0).replace(".", _DOT), masked)
    masked = _DECIMAL.sub(_DOT, masked)
    pieces = [p for p in _SENTENCE_END.split(masked) if p.strip()]
    merged: list[str] = []
    for piece in pieces:  # citation markup right after a full stop belongs to the previous sentence
        lead = re.match(r"((?:\x00\d+\x00[\s.,;]*)+)(.*)", piece)
        if merged and lead:
            merged[-1] += " " + lead.group(1).strip()
            piece = lead.group(2)
        if piece.strip():
            merged.append(piece)
    restore = lambda text: re.sub(r"\x00(\d+)\x00", lambda m: groups[int(m.group(1))], text).replace(_DOT, ".")
    return [restore(p).strip() for p in merged]


def cited_paragraphs(text: str) -> list[dict]:
    """Paragraphs with cited sentences: ``{"seccion", "frases": [(sentence, [keys])]}``."""
    blocks: list[tuple[str, str]] = []
    section, lines = "", []

    def flush() -> None:
        if lines:
            blocks.append((section, " ".join(lines)))
            lines.clear()

    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            flush()
            section = heading.group(1)
        elif not line.strip():
            flush()
        else:
            lines.append(line.strip())
    flush()

    paragraphs = []
    for section, block in blocks:
        cited = []
        for sentence in split_sentences(block):
            keys = list(dict.fromkeys(find_citations(sentence)[0]))
            if keys:
                cited.append((sentence, keys))
        if cited:
            paragraphs.append({"seccion": section, "frases": cited})
    return paragraphs


def _query(sentence: str) -> str:
    return " ".join(_CITE_MARKUP.sub("", sentence).split()) or sentence


def _evidence_text(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        extra = item.get("contexto") or item.get("evidencia") or ""  # stored items have neither
        origin = " [CITADO: la obra lo recoge de otra]" if item.get("origen") == "citado" else ""
        line = f"  {i}. ({item.get('tipo', '')}){origin} {item.get('texto', '')}"
        if extra:
            line += f" | {extra}"
        lines.append(line)
        if item.get("cita_literal"):
            lines.append(f"     CITA LITERAL: «{item['cita_literal']}»")
    return "\n".join(lines)


def _evidence_for(engine, query: str, key: str, section: str, seen: dict, queries: dict) -> list[dict]:
    """What the judge sees of ``key``: the items closest to the sentence, those the writer saw
    in the section (or, for older drafts, those its paragraph queries retrieve), no repeated text."""
    items = engine.search(query, n=5, keys={key}, max_per_paper=5)
    stored = seen.get(section, {}).get(key)
    if stored is None:
        for q in queries.get(key, []):
            items += engine.search(q, n=4, keys={key}, max_per_paper=4)
    else:
        items += stored
    unique = {}
    for item in items:
        unique.setdefault(item.get("texto", ""), item)
    return list(unique.values())[:MAX_EVIDENCE]


def _judge_prompt(pairs: list[dict]) -> str:
    blocks = [
        f"[{p['n']}] Frase: {p['frase']}\nObra citada: {p['clave']}\nEvidencia de la obra:\n{_evidence_text(p['items'])}"
        for p in pairs
    ]
    return "Juzga cada una de estas afirmaciones.\n\n" + "\n\n".join(blocks)


def _parse(answer, count: int) -> dict[int, tuple[str, str]]:
    """Verdicts by number; items that are malformed or missing are left out."""
    rows = answer.get("veredictos") if isinstance(answer, dict) else answer
    found = {}
    for row in rows if isinstance(rows, list) else []:
        try:
            n = int(row["n"])
            verdict = str(row["veredicto"]).strip().lower()
        except (KeyError, TypeError, ValueError):
            continue
        if verdict in VERDICTS and 1 <= n <= count:
            found[n] = (verdict, str(row.get("motivo", "")).strip())
    return found


def judge_document(folder: Path, llm=None) -> list[dict]:
    """Judge every (sentence, cited work) of the draft against the work's evidence.

    One LLM call per paragraph with cited sentences. Pairs the library has no evidence
    for are ``no_apoyada`` without a call; a paragraph the judge answers badly is
    ``sin_juzgar``, never counted as support. ``UsageLimitError`` propagates.
    """
    folder = Path(folder)
    text = (folder / DRAFT).read_text(encoding="utf-8")
    paragraphs = cited_paragraphs(text)
    if not paragraphs:
        return []
    project = Project.load(folder)
    engine = EvidenceEngine(project.library(), project.paper_ids())
    llm = llm or get_llm_client()
    seen = seen_evidence(folder)
    retrieved = folder / RETRIEVED
    queries = json.loads(retrieved.read_text(encoding="utf-8")) if retrieved.exists() else {}

    entries = []
    for paragraph in paragraphs:
        to_judge, rows = [], []
        for sentence, keys in paragraph["frases"]:
            for key in keys:
                row = {"seccion": paragraph["seccion"], "frase": sentence, "clave": key,
                       "veredicto": "sin_juzgar", "motivo": "", "cita_literal": None}
                rows.append(row)
                items = _evidence_for(engine, _query(sentence), key, paragraph["seccion"], seen, queries)
                if not items:
                    row.update(veredicto="no_apoyada", motivo=NO_EVIDENCE)
                    continue
                row["cita_literal"] = next((i["cita_literal"] for i in items if i.get("cita_literal")), None)
                to_judge.append({"n": len(to_judge) + 1, "frase": sentence, "clave": key,
                                 "items": items, "row": row})
        if to_judge:
            _apply_verdicts(llm, to_judge)
        entries.extend(rows)
    return entries


def _apply_verdicts(llm, pairs: list[dict]) -> None:
    try:
        answer = llm.complete_json(JUDGE_SYSTEM, _judge_prompt(pairs))
    except UsageLimitError:
        raise
    except LLMError as error:
        answer, failure = None, f"El juez no devolvió una respuesta legible ({error})"
    else:
        failure = "El juez no dio veredicto para esta frase"
    verdicts = _parse(answer, len(pairs))
    for pair in pairs:
        if pair["n"] in verdicts:
            pair["row"]["veredicto"], pair["row"]["motivo"] = verdicts[pair["n"]]
        else:
            pair["row"]["motivo"] = failure


def summary(entries: list[dict]) -> dict:
    """Entries per verdict and ``apoyo``: share of judged entries that are ``apoyada``."""
    counts = {v: sum(e["veredicto"] == v for e in entries) for v in (*VERDICTS, "sin_juzgar")}
    judged = sum(counts[v] for v in VERDICTS)
    counts["apoyo"] = round(counts["apoyada"] / judged, 3) if judged else None
    return counts


def markdown(entries: list[dict]) -> str:
    """The «Apoyo de las citas» section, worst entries first."""
    stats = summary(entries)
    apoyo = "sin datos" if stats["apoyo"] is None else f"{stats['apoyo']:.0%}"
    lines = [
        "## Apoyo de las citas", "",
        f"Apoyo: {apoyo} ({stats['apoyada']} apoyadas, {stats['parcial']} parciales, "
        f"{stats['no_apoyada']} no apoyadas, {stats['sin_juzgar']} sin juzgar).",
        "Un juez automático compara cada frase con lo que la biblioteca guarda de la obra citada: "
        "revisa a mano las peores.", "",
    ]
    labels = {"no_apoyada": "No apoyada", "parcial": "Parcial", "sin_juzgar": "Sin juzgar"}
    for verdict, label in labels.items():
        for entry in (e for e in entries if e["veredicto"] == verdict):
            lines.append(f"- **{label}** [@{entry['clave']}] ({entry['seccion'] or 'sin sección'}): «{entry['frase']}»")
            if entry["motivo"]:
                lines.append(f"  - Motivo: {entry['motivo']}")
            if entry.get("cita_literal"):
                lines.append(f"  - Cita literal de la obra: «{entry['cita_literal']}»")
    if stats["apoyada"]:
        lines += ["", f"Además, {stats['apoyada']} citas están apoyadas por la evidencia."]
    return "\n".join(lines) + "\n"


def save(folder: Path, entries: list[dict]) -> Path:
    """Write ``revision/apoyo.json`` (entries and summary)."""
    path = Path(folder) / SUPPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"resumen": summary(entries), "entradas": entries}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
