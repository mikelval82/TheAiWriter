"""Writes a document one section at a time, the model consulting the library on demand.

It is a ``PerspectiveRun`` that changes only the writing phase. Instead of handing
each paragraph a fixed set of extracted ideas, the model gets a few to start from and
then, section by section, searches the idea space, asks for the full passage of the
paper an idea came from, and writes when it has what it needs. The ideas are an index
into the papers, not the writing material.

Each call answers with one JSON object:

    {"accion": "consultar", "buscar": ["consulta", ...], "leer": ["E3", ...]}
    {"accion": "escribir", "texto": "..."}

Evidence ids (``E1``, ``E2``, ...) are per section and stable across its rounds.
"""

import re

from ai_writer.background import now
from ai_writer.llm import LLMError
from ai_writer.llm.client import extract_json
from ai_writer.perspective_run import PerspectiveRun

MAX_ROUNDS = 4  # calls per section; the last one can only write
MAX_QUERIES = 4  # searches the model may ask for in one round
MAX_PASSAGES = 4  # full passages the model may ask for in one round
RESULTS_PER_QUERY = 6
SEED_RESULTS = 4  # results of each paragraph's own query before the first round
JSON_RETRIES = 2  # extra tries when the answer is not the JSON asked for

SYSTEM = """Eres un autor académico que redacta UNA sección de un documento científico \
consultando una biblioteca de papers. Recibes el abstract, la tesis, el plan completo, el \
texto ya escrito de las secciones anteriores, la sección que toca escribir y la evidencia \
reunida hasta ahora (ideas y hallazgos extraídos de los papers, cada uno con su id Ei).

Las ideas extraídas son un índice de los papers, no el material de escritura. Antes de \
citar un resultado, un método o una cifra concretos, lee el texto completo del apartado \
del que sale; si falta algo, busca de nuevo.

En cada llamada respondes con UN SOLO objeto JSON, sin nada más. Tienes dos acciones:
{"accion": "consultar", "buscar": ["consulta", ...], "leer": ["E3", ...]}
  buscar: consultas a la biblioteca (como máximo %(queries)d por ronda); añaden evidencia nueva.
  leer: ids de evidencia cuyo apartado completo quieres leer (como máximo %(passages)d por ronda).
{"accion": "escribir", "texto": "..."}
  texto: la sección completa, párrafos separados por una línea en blanco.

REGLAS DE ESCRITURA
1. Escribe la sección como prosa académica continua, en el idioma del documento, sin encabezado, listas ni títulos.
2. Cita solo obras que aparezcan en la evidencia mostrada, con el formato [@clave]; nunca inventes claves.
3. Una cita va sobre el hecho concreto que la obra respalda. Tus inferencias, enlaces y conclusiones van en frases aparte SIN cita.
4. Lo marcado «afirmación citada» solo puede usarse tal como lo recoge esa obra («según recoge…»), nunca como hallazgo suyo.
5. Nunca escribas [@?]: si una afirmación no tiene fuente, búscala; si sigue sin haberla, no hagas la afirmación.
6. Prefiere los hallazgos de los propios papers, con las cifras y condiciones tomadas de los textos completos, a las generalidades.
7. No repitas lo que ya dicen las secciones anteriores; remite a ello. No adelantes lo que corresponde a las siguientes.
8. Respeta la extensión objetivo y desarrolla cada párrafo del plan.
9. Varía las obras citadas: no apoyes la sección en una sola.
""" % {"queries": MAX_QUERIES, "passages": MAX_PASSAGES}


class DemandRun(PerspectiveRun):
    """A document's run whose sections are written with on-demand consultation."""

    def _write(self, abstract: str) -> None:
        outline = self._load_plan()
        words = self.profile.paragraph_words(outline.total_paragraphs)
        sections = self.state.setdefault("secciones", [])
        self.save(fase="escritura")

        for i, section_outline in enumerate(outline.sections):
            if i == len(sections):
                sections.append({"titulo": section_outline.section_name, "parrafos": []})
            state = sections[i]
            if state.get("contenido"):
                continue
            text = self._write_section(abstract, outline, i, words, sections[:i])
            state["contenido"] = text
            state["parrafos"] = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            self._track_usage()
            self.save()
            self.render(abstract)
        # every section was written with the whole document in view: nothing to review globally
        self.save(revision_global_hecha=now())

    def _write_section(self, abstract: str, outline, i: int, words: tuple[int, int], written: list[dict]) -> str:
        from ai_writer.validation import record_retrieved, record_seen

        section = outline.sections[i]
        engine = self.engine()
        items: list[dict] = []  # evidence of this section, ids E1, E2, ...
        passages: dict[tuple[str, str], str] = {}
        texts: set[str] = set()

        def search(query: str, **kwargs) -> None:
            results = engine.search(query, **kwargs)
            record_retrieved(self.folder, query, [r["clave"] for r in results])
            fresh = []
            for result in results:
                if result["texto"] in texts:
                    continue
                texts.add(result["texto"])
                items.append({"id": f"E{len(items) + 1}", **result})
                fresh.append(_seen_item(result))
            record_seen(self.folder, section.section_name, fresh)

        allowed = engine.allowed_keys()
        for paragraph in section.paragraphs:
            query = paragraph.to_query()
            search(query, n=SEED_RESULTS)
            if keys := set(paragraph.source_keys) & allowed:
                search(query, n=2 * len(keys), keys=keys)

        low, high = words
        target = (low * len(section.paragraphs), high * len(section.paragraphs))
        notes: list[str] = []
        for round_number in range(1, MAX_ROUNDS + 2):
            final = round_number >= MAX_ROUNDS
            prompt = self._prompt(abstract, outline, i, written, target, items, passages, notes,
                                  round_number, final)
            answer = self._ask(prompt, section.section_name)
            if answer["accion"] == "escribir":
                return answer["texto"].strip()
            if final:
                notes = ["Respondiste «consultar», pero ya no se puede consultar: responde con «escribir»."]
                continue
            notes = []
            for query in answer["buscar"][:MAX_QUERIES]:
                search(str(query), n=RESULTS_PER_QUERY)
            by_id = {item["id"]: item for item in items}
            for item_id in answer["leer"][:MAX_PASSAGES]:
                item = by_id.get(str(item_id).strip())
                if item is None:
                    notes.append(f"No existe la evidencia {item_id}.")
                    continue
                at = (item["clave"], item.get("seccion") or "")
                if at in passages:
                    continue
                passage = engine.passage(*at)
                if passage is None:
                    notes.append(f"No hay texto completo de {item['id']} ({item['cita']}, apartado «{at[1]}»).")
                else:
                    passages[at] = passage
        raise LLMError(f"El modelo no escribió la sección «{section.section_name}» tras {MAX_ROUNDS} rondas.")

    def _ask(self, prompt: str, title: str) -> dict:
        """One call whose answer must be a valid action; unreadable answers are asked again."""
        for _ in range(1 + JSON_RETRIES):
            self._check_stop()
            try:
                answer = extract_json(self.llm.complete(SYSTEM, prompt, json_mode=True))
            except ValueError:
                continue
            if not isinstance(answer, dict):
                continue
            if answer.get("accion") == "escribir" and str(answer.get("texto") or "").strip():
                answer["texto"] = str(answer["texto"])
                return answer
            if answer.get("accion") == "consultar":
                lists = {name: answer.get(name) if isinstance(answer.get(name), list) else [] for name in ("buscar", "leer")}
                return {"accion": "consultar", **lists}
        raise LLMError(f"Respuesta ilegible del modelo en la sección «{title}».")

    def _prompt(self, abstract, outline, i, written, target, items, passages, notes, round_number, final) -> str:
        section = outline.sections[i]
        plan = []
        for other in outline.sections:
            plan.append(f"## {other.section_name}\nPropósito: {other.section_purpose}")
            plan += [f"- {paragraph.key_idea}" for paragraph in other.paragraphs]
        parts = [
            f"# ABSTRACT\n{abstract}",
            f"# TESIS\n{outline.thesis_statement}",
            "# PLAN DEL DOCUMENTO\n" + "\n".join(plan),
        ]
        if written:
            parts.append("# TEXTO YA ESCRITO (secciones anteriores, completas)\n"
                         + "\n\n".join(f"### {s['titulo']}\n{s['contenido']}" for s in written))
        paragraphs = []
        for n, paragraph in enumerate(section.paragraphs, 1):
            paragraphs.append(f"Párrafo {n}: {paragraph.key_idea}")
            paragraphs += [f"  - {point}" for point in paragraph.supporting_points]
        parts.append(
            f"# SECCIÓN QUE TOCA ESCRIBIR: {section.section_name}\nPropósito: {section.section_purpose}\n"
            + "\n".join(paragraphs)
            + f"\nExtensión objetivo: entre {target[0]} y {target[1]} palabras "
              f"({len(section.paragraphs)} párrafos)."
        )
        parts.append("# EVIDENCIA REUNIDA (cita con el formato indicado en cada línea)\n"
                     + ("\n".join(_evidence_line(item) for item in items) or "(ninguna todavía)"))
        if passages:
            parts.append("# TEXTOS COMPLETOS LEÍDOS\n" + "\n\n".join(
                f"## [@{key}], apartado «{name}»\n{text}" for (key, name), text in passages.items()))
        if notes:
            parts.append("# AVISOS DE LA ÚLTIMA CONSULTA\n" + "\n".join(notes))
        if final:
            parts.append(f"# RONDA {round_number}: YA NO SE PUEDE CONSULTAR\n"
                         'Responde solo con {"accion": "escribir", "texto": "..."}; '
                         "la acción «consultar» no se acepta.")
        else:
            parts.append(f"# RONDA {round_number} DE {MAX_ROUNDS}\n"
                         "Consulta si te falta evidencia o necesitas leer el texto completo de algo que vas a citar; "
                         "si no, escribe la sección.")
        return "\n\n".join(parts)


def _evidence_line(item: dict) -> str:
    if item["tipo"] == "idea":
        kind = "idea"
    else:
        kind = "afirmación citada" if item.get("origen") == "citado" else "hallazgo propio"
    line = f"{item['id']} · {item['cita']} · apartado «{item.get('seccion') or '?'}» · {kind} · {item['texto']}"
    if item.get("cita_verificada") and item.get("cita_literal"):
        line += f" · cita literal: «{item['cita_literal']}»"
    return line


def _seen_item(result: dict) -> dict:
    """An evidence result as the validator stores what the writer saw."""
    return {"clave": result["clave"], "tipo": result["tipo"], "texto": result["texto"],
            "cita_literal": result.get("cita_literal") if result.get("cita_verificada") else None,
            "origen": result.get("origen") if result["tipo"] == "claim" else None}
