"""Writes a document of the perspective route into its folder, and can resume it.

The run goes through the pipeline's phases (topics → plan → paragraphs → section
review → global review → closing) and records each step in ``borrador/estado.json``
as soon as it is done. Started again after a crash or a stop, it continues from
the last paragraph written. The plan lives in ``borrador/plan.json``: if it is
edited before writing starts, the edited plan is the one written.

Evidence comes only from the document's collections and the writer cites with the
library's stable keys; whatever citation still fails at the end becomes ``[@?]``.
"""

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from ai_writer.background import now, process_alive, spawn_cli
from ai_writer.citations import CitationIndex, check_citations
from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMClient, LLMError, get_llm_client
from ai_writer.profiles import profile_for

BORRADOR = Path("borrador")
STATE = BORRADOR / "estado.json"
PLAN = BORRADOR / "plan.json"
PLAN_MD = BORRADOR / "plan.md"
DRAFT = BORRADOR / "documento.md"
LOG = BORRADOR / "registro.log"
STOP = BORRADOR / "detener"
ABSTRACT = Path("materiales") / "abstract.md"
CORRECTIONS = Path("revision") / "citas_corregidas.md"
CRITICAL_REVIEW = Path("revision") / "revision_critica.md"

IDEAS_PER_SECTION = 16
CONTEXT_LIMITS = (20, 3)  # evidence items offered per paragraph, and at most per work
OVERCITED = 6  # a work cited this often is pointed out to the writer
_SPANISH = {"es", "español", "espanol", "castellano", "spanish"}
_CITED_KEY = re.compile(r"Citar: \[@([^\]]+)\]")


class StopRequested(Exception):
    """The student asked the run to stop (``borrador/detener`` exists)."""


class LanguageClient:
    """An LLMClient whose every request asks for output in the document's language.

    The agents' prompts are in Spanish and say so; the note overrides that.
    """

    def __init__(self, client: LLMClient, language: str) -> None:
        self._client = client
        self._note = (
            f"\n\nIDIOMA DE SALIDA: redacta todo el texto que produzcas en {language}, "
            "aunque estas instrucciones estén en español. Esta indicación prevalece sobre "
            "cualquier otra sobre el idioma. No traduzcas ni cambies los marcadores de cita [@...]."
        )

    def complete(self, system: str, user: str, **kwargs) -> str:
        return self._client.complete(system + self._note, user, **kwargs)

    def complete_json(self, system: str, user: str, **kwargs):
        return self._client.complete_json(system + self._note, user, **kwargs)

    def __getattr__(self, name):
        return getattr(self._client, name)


def client_for(language: str):
    client = get_llm_client()
    if language.strip().lower() in _SPANISH:
        return client
    return LanguageClient(client, language)


class PerspectiveRun:
    """One document's writing run, read from and saved to its folder."""

    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)
        self.project = Project.load(self.folder)
        self.library = self.project.library()
        self.profile = profile_for(self.project.perfil, self.project.tipo)
        path = self.folder / STATE
        self.state: dict = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.llm = client_for(self.project.idioma)
        self._engine = None
        self._context_manager = None

    # State

    def save(self, **fields) -> None:
        self.state.update(fields, actualizado=now())
        path = self.folder / STATE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def status(self) -> dict:
        """What the run is doing, for the student: phase, progress and last error."""
        state = dict(self.state)
        if state.get("estado") == "en_curso" and not process_alive(state.get("pid")):
            state["estado"] = "interrumpido"
        plan = self._load_plan() if (self.folder / PLAN).exists() else None
        total = sum(len(s.paragraphs) for s in plan.sections) if plan else None
        written = sum(len(s.get("parrafos", [])) for s in state.get("secciones", []))
        return {
            "estado": state.get("estado", "sin_empezar"),
            "fase": state.get("fase"),
            "parrafos": f"{written}/{total}" if total else None,
            "secciones_terminadas": [
                s["titulo"] for s in state.get("secciones", []) if s.get("contenido")
            ],
            "inicio": state.get("inicio"),
            "actualizado": state.get("actualizado"),
            "error": state.get("error"),
            "llamadas_llm": state.get("llamadas_llm", 0),
            "coste_estimado_usd": state.get("coste_usd"),
        }

    def _check_stop(self) -> None:
        if (self.folder / STOP).exists():
            raise StopRequested()

    def _track_usage(self) -> None:
        usage = getattr(self.llm, "usage", None)
        if usage is not None:
            base = self.state.get("_uso_base", {"llamadas": 0, "coste": 0.0})
            self.state["llamadas_llm"] = base["llamadas"] + usage.calls
            self.state["coste_usd"] = round(base["coste"] + usage.cost_usd, 4)

    # Run

    def run(self, pause_after_plan: bool = False) -> dict:
        """Run from wherever the document is. Returns the final status."""
        import os

        (self.folder / STOP).unlink(missing_ok=True)
        if "pausar_tras_plan" not in self.state:
            self.state["pausar_tras_plan"] = pause_after_plan
        self.state["_uso_base"] = {
            "llamadas": self.state.get("llamadas_llm", 0), "coste": self.state.get("coste_usd") or 0.0
        }
        self.save(estado="en_curso", pid=os.getpid(), error=None,
                  inicio=self.state.get("inicio") or now())
        try:
            abstract = self._abstract()
            if "ideas_por_seccion" not in self.state:
                self._topics()
            if not (self.folder / PLAN).exists():
                self._plan(abstract)
            if self.state.get("pausar_tras_plan") and not self.state.get("plan_aprobado"):
                self.save(estado="esperando_aprobacion", fase="plan")
                return self.status()
            self._write(abstract)
            if not self.state.get("revision_global_hecha"):
                self._global_review(abstract)
            self._close(abstract)
        except StopRequested:
            self._track_usage()
            self.save(estado="detenido")
        except BaseException as error:
            self._track_usage()
            self.save(estado="error", error=str(error) or type(error).__name__)
            raise
        return self.status()

    def _abstract(self) -> str:
        path = self.folder / ABSTRACT
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            raise LibraryError(
                f"Falta el abstract en {ABSTRACT}: escribe ahí la idea y la tesis del documento."
            )
        return path.read_text(encoding="utf-8").strip()

    def engine(self):
        if self._engine is None:
            from ai_writer.evidence import EvidenceEngine

            self._engine = EvidenceEngine(self.library, self.project.paper_ids())
        return self._engine

    # Phase 1: topics and the literature ideas each section is planned from

    def _topics(self) -> None:
        self.save(fase="temas")
        engine = self.engine()
        topics = engine.topics()
        ordered = [topic.id for topic in topics]
        used_rows: set[int] = set()
        section_ideas = {}
        for section in self.profile.sections:
            ideas = []
            for topic_id in self.profile.topic_ids(section, ordered):
                if len(ideas) >= IDEAS_PER_SECTION:
                    break
                ideas += engine.topic_ideas(topic_id, 2, used_rows)
            section_ideas[section.name] = ideas[:IDEAS_PER_SECTION]
        self.save(temas=[asdict(topic) for topic in topics], ideas_por_seccion=section_ideas)

    def _topics_summary(self) -> str:
        lines = ["# Temas Principales Identificados en la Literatura\n"]
        for i, topic in enumerate(self.state["temas"], 1):
            lines.append(f"## {i}. {', '.join(topic['keywords'][:4])}")
            lines.append(f"- **Cantidad de ideas:** {topic['ideas']} ({topic['papers']} obras)")
            for example in topic["examples"][:2]:
                lines.append(f"- **Idea representativa:** \"{example['idea'][:200]}\"")
            lines.append("")
        return "\n".join(lines)

    # Phase 2: plan

    def _plan(self, abstract: str) -> None:
        from ai_writer.agents.planner_agent import PlannerAgent
        from ai_writer.agents.reviewer_agent import ReviewerAgent

        self.save(fase="plan")
        planner = PlannerAgent(llm=self.llm)
        outline = planner.generate_outline(
            abstract=abstract,
            topics_summary=self._topics_summary(),
            title=self.project.titulo,
            sections=[section.as_planner_tuple() for section in self.profile.sections],
            section_ideas=self.state["ideas_por_seccion"],
        )
        reviewer = ReviewerAgent(abstract_context=abstract)
        reviewer.llm = self.llm
        feedback = reviewer.review_outline(outline)
        if feedback and "sin cambios" not in feedback.lower():
            outline = planner.refine_outline(outline, feedback)
        outline = fit_plan(outline, self.profile)
        self._check_stop()
        (self.folder / PLAN).write_text(outline.model_dump_json(indent=2), encoding="utf-8")
        (self.folder / PLAN_MD).write_text(outline.to_markdown(), encoding="utf-8")
        self._track_usage()
        self.save(fase="plan", plan_hecho=now())

    def _load_plan(self):
        from ai_writer.models.outline import PaperOutline

        return PaperOutline.model_validate_json((self.folder / PLAN).read_text(encoding="utf-8"))

    # Phase 3: paragraphs and section reviews

    def context_manager(self, abstract: str):
        if self._context_manager is None:
            from ai_writer.utils.enhanced_context_manager import EnhancedContextManager

            citations = CitationIndex.load(self.library)
            keys = {paper.id: citations.key_for(paper.id) for paper in self.library.papers()}
            manager = EnhancedContextManager(
                abstract_context=abstract,
                indices_dir=self.library.indices_dir,
                embeddings_dir=self.library.embeddings_dir,
                paper_ids=self.project.paper_ids(),
                citation_keys=keys,
            )
            used = self.state.get("usados", {})
            manager._used_idea_fingerprints = set(used.get("ideas", []))
            manager._used_claim_fingerprints = set(used.get("claims", []))
            manager._idea_retrieval_counts = dict(used.get("cuentas_ideas", {}))
            manager._claim_retrieval_counts = dict(used.get("cuentas_claims", {}))
            self._context_manager = manager
        return self._context_manager

    def _save_used(self) -> None:
        manager = self._context_manager
        self.state["usados"] = {
            "ideas": sorted(manager._used_idea_fingerprints),
            "claims": sorted(manager._used_claim_fingerprints),
            "cuentas_ideas": manager._idea_retrieval_counts,
            "cuentas_claims": manager._claim_retrieval_counts,
        }

    def _write(self, abstract: str) -> None:
        from ai_writer.agents.reviewer_agent import ReviewerAgent
        from ai_writer.agents.writer_agent import WriterAgent
        from ai_writer.models.paper import Section
        from ai_writer.validation import record_retrieved, record_seen

        outline = self._load_plan()
        words = self.profile.paragraph_words(outline.total_paragraphs)
        manager = self.context_manager(abstract)
        manager.limits = CONTEXT_LIMITS
        writer = WriterAgent(abstract_context=abstract)
        writer.llm = self.llm
        reviewer = ReviewerAgent(abstract_context=abstract, context_manager=manager)
        reviewer.llm = self.llm
        sections = self.state.setdefault("secciones", [])
        self.save(fase="escritura")

        for i, section_outline in enumerate(outline.sections):
            if i == len(sections):
                sections.append({"titulo": section_outline.section_name, "parrafos": []})
            state = sections[i]
            memory = self._memory_context(sections[:i], outline.sections[i + 1:])
            spec = self.profile.section(section_outline.section_name)

            for j, paragraph in enumerate(section_outline.paragraphs):
                if j < len(state["parrafos"]):
                    continue
                self._check_stop()
                query = paragraph.to_query()
                cited = self._cited_so_far()
                manager.citation_counts = dict(cited)
                context = manager.get_context_for_idea(
                    idea_query=query,
                    section_name=section_outline.section_name,
                    suggested_topics=paragraph.suggested_sources,
                    config=spec.search if spec else None,
                )
                plan_text, plan_results = self._plan_sources(paragraph, query)
                context = plan_text + context
                record_retrieved(self.folder, query, _CITED_KEY.findall(context))
                record_seen(self.folder, section_outline.section_name,
                            _seen_items(manager, plan_results))
                context += _overcited_note(cited)
                text = writer.write_paragraph(
                    key_idea=paragraph.key_idea,
                    supporting_points=paragraph.supporting_points,
                    section_name=section_outline.section_name,
                    section_purpose=section_outline.section_purpose,
                    previous_paragraphs=state["parrafos"],
                    reference_context=context,
                    thesis=outline.thesis_statement,
                    memory_context=memory,
                    words=words,
                )
                state["parrafos"].append(text)
                self._save_used()
                self._track_usage()
                self.save()
                self.render(abstract)

            if state.get("contenido") is None:
                self._check_stop()
                section = Section(title=state["titulo"], content="\n\n".join(state["parrafos"]))
                section = reviewer.review_section(
                    section=section, previous_sections=None, update_memory=False,
                    other_sections={s["titulo"]: s["contenido"] for s in sections[:i]},
                )
                state["contenido"] = section.content
                self._track_usage()
                self.save()
                self.render(abstract)

    def _plan_sources(self, paragraph, query: str) -> tuple[str, list[dict]]:
        """The evidence of the works the plan built this paragraph on, offered first.

        The general search may leave those works out (limits per work, works
        already cited often); without them the writer knows a claim from the plan
        but not its source, and leaves a ``[@?]``.
        """
        keys = set(paragraph.source_keys) & self.engine().allowed_keys()
        if not keys:
            return "", []
        results = self.engine().search(query, n=2 * len(keys), keys=keys)
        lines = ["\n📌 FUENTES DE LAS IDEAS DEL PLAN PARA ESTE PÁRRAFO "
                 "(cítalas cuando uses sus ideas):"]
        for result in results:
            lines.append(f"• [{result['paper'][:50]}] → Citar: {result['cita']}\n   {result['texto']}")
        return "\n".join(lines) + "\n", results

    def _cited_so_far(self) -> Counter:
        """How many times the document written so far cites each work."""
        text = "\n".join(
            section.get("contenido") or "\n".join(section.get("parrafos", []))
            for section in self.state.get("secciones", [])
        )
        return Counter(re.findall(r"@([\w:-]+)", text))

    def _memory_context(self, sections: list[dict], upcoming: list) -> str:
        """The full text of the sections already written and the plan of those still to write."""
        lines = []
        if sections:
            lines.append("\n\nTEXTO YA ESCRITO DEL DOCUMENTO (secciones anteriores, completas). "
                         "No repitas lo ya dicho: remite a ello.")
            lines += [f"\n### {s['titulo']}\n{s['contenido']}" for s in sections]
        if upcoming:
            lines.append("\n\nPLAN DE LAS SECCIONES QUE FALTAN POR ESCRIBIR "
                         "(no adelantes lo que les corresponde):")
            for section in upcoming:
                lines.append(f"\n### {section.section_name}\nPropósito: {section.section_purpose}")
                lines += [f"- {paragraph.key_idea}" for paragraph in section.paragraphs]
        return "\n".join(lines) + "\n" if lines else ""

    # Phase 4: global review, one section at a time

    def _global_review(self, abstract: str) -> None:
        """Revise each section for the coherence of the whole, saving after each one.

        A revision that adds citations or changes the length a lot is discarded and
        the section keeps its text.
        """
        from ai_writer.agents.reviewer_agent import ReviewerAgent
        from ai_writer.models.paper import Section

        self.save(fase="revision_global")
        sections = self.state["secciones"]
        reviewer = ReviewerAgent(abstract_context=abstract)
        reviewer.llm = self.llm
        kept = self.state.setdefault("revision_global_descartada", [])
        for i, section in enumerate(sections):
            if "revisada_global" in section:
                continue
            self._check_stop()
            previous = sections[i - 1]["contenido"].split("\n\n")[-1] if i > 0 else ""
            following = sections[i + 1]["contenido"].split("\n\n")[0] if i + 1 < len(sections) else ""
            whole = {s["titulo"]: s.get("revisada_global") or s["contenido"] for s in sections}
            try:
                revised = reviewer.review_section_coherence(
                    Section(title=section["titulo"], content=section["contenido"]),
                    whole, previous, following,
                )
            except LLMError:
                revised = ""
            if revision_is_safe(section["contenido"], revised):
                section["revisada_global"] = revised
            else:
                section["revisada_global"] = None
                kept.append(section["titulo"])
            self._track_usage()
            self.save()
            self.render(abstract)
        self.save(revision_global_hecha=now())

    # Phase 5: closing

    def _close(self, abstract: str) -> None:
        from ai_writer.validation import validate_document

        self.save(fase="cierre")
        text = self.document_text(abstract)
        citations = CitationIndex.load(self.library)
        allowed = citations.keys_for_papers(self.project.paper_ids())
        text, corrections = replace_invalid_citations(text, citations, allowed)
        (self.folder / DRAFT).write_text(text, encoding="utf-8")
        corrections_path = self.folder / CORRECTIONS
        corrections_path.parent.mkdir(parents=True, exist_ok=True)
        if corrections:
            corrections_path.write_text(
                "# Citas sustituidas por [@?]\n\nEl texto citaba estas claves, que no se pueden "
                "aceptar; quedan como huecos para completar.\n\n"
                + "\n".join(f"- `{c}`" for c in corrections) + "\n",
                encoding="utf-8",
            )
        if not self.state.get("apoyo"):
            from ai_writer import support

            self._check_stop()
            entries = support.judge_document(self.folder, self.llm)
            support.save(self.folder, entries)
            self.state["apoyo"] = support.summary(entries)
            self._track_usage()
            self.save()
        report = validate_document(self.folder, suggest=True)

        if not self.state.get("revision_critica_hecha"):
            from ai_writer.agents.reviewer_agent import ReviewerAgent
            from ai_writer.models.paper import Paper, Section

            reviewer = ReviewerAgent(abstract_context=abstract)
            reviewer.llm = self.llm
            paper = Paper(title=self.project.titulo, sections=[
                Section(title=title, content=content) for title, content in _split_sections(text)
            ])
            try:
                review = reviewer.generate_critical_review(paper)
            except LLMError as error:
                review = f"# Revisión crítica\n\nNo disponible: {error}"
            (self.folder / CRITICAL_REVIEW).write_text(review, encoding="utf-8")
            self.state["revision_critica_hecha"] = now()

        self._track_usage()
        self.save(
            estado="terminado", fase="terminado", fin=now(),
            citas_validas=report.citations.ok, citas_sustituidas=len(corrections),
        )

    # Rendering

    def document_text(self, abstract: str) -> str:
        """The document as far as it is written, best version of each section."""
        parts = [f"# {self.project.titulo}", "", "## Abstract", "", abstract, ""]
        for section in self.state.get("secciones", []):
            content = (
                section.get("revisada_global")
                or section.get("contenido")
                or "\n\n".join(section.get("parrafos", []))
            )
            parts += [f"## {section['titulo']}", "", content.strip(), ""]
        return "\n".join(parts).rstrip() + "\n"

    def render(self, abstract: str) -> None:
        (self.folder / DRAFT).write_text(self.document_text(abstract), encoding="utf-8")


def fit_plan(outline, profile):
    """Keep each section within its profile's paragraph count.

    The planner sometimes adds paragraphs beyond the profile's maximum; the extra
    ones become supporting points of the section's last paragraph.
    """
    for section in outline.sections:
        spec = profile.section(section.section_name)
        if spec is None or len(section.paragraphs) <= spec.max_paragraphs:
            continue
        kept, extra = section.paragraphs[: spec.max_paragraphs], section.paragraphs[spec.max_paragraphs:]
        kept[-1].supporting_points += [paragraph.key_idea for paragraph in extra]
        section.paragraphs = kept
    return outline


def revision_is_safe(original: str, revised: str) -> bool:
    """Whether a coherence revision can replace the text: no new citations, similar length."""
    if not revised.strip():
        return False
    keys = lambda text: set(re.findall(r"@([\w:-]+)", text))  # noqa: E731
    ratio = len(revised.split()) / max(1, len(original.split()))
    return keys(revised) <= keys(original) and 0.75 <= ratio <= 1.2


def _seen_items(manager, plan_results: list[dict]) -> list[dict]:
    """The evidence the writer got for a paragraph, as ``{clave, tipo, texto, cita_literal, origen}``."""
    from ai_writer.utils.enhanced_context_manager import is_cited_claim

    items = []
    for result in plan_results:
        verified = result.get("cita_verificada")
        items.append({"clave": result["clave"], "tipo": result["tipo"], "texto": result["texto"],
                      "cita_literal": result.get("cita_literal") if verified else None,
                      "origen": result.get("origen") if result["tipo"] == "claim" else None})
    for item, _score, kind in manager.last_items:
        key = manager._citation_key_for(item)
        if not key:
            continue
        verified = item.get("quote") if item.get("quote_verified") else None
        items.append({"clave": key, "tipo": kind, "texto": item.get(kind, ""), "cita_literal": verified,
                      "origen": ("citado" if is_cited_claim(item) else "propio") if kind == "claim" else None})
    return items


def _overcited_note(cited: Counter) -> str:
    frequent = [(key, n) for key, n in cited.most_common(4) if n >= OVERCITED and key != "?"]
    if not frequent:
        return ""
    works = ", ".join(f"[@{key}] ({n} veces)" for key, n in frequent)
    return (
        f"\n\nOBRAS YA MUY CITADAS EN EL DOCUMENTO: {works}. Cítalas solo si ninguna otra "
        "fuente del contexto sirve para la afirmación; prefiere las que aún no se citan."
    )


def replace_invalid_citations(text: str, index: CitationIndex, allowed: set[str]) -> tuple[str, list[str]]:
    """Replace citations that fail the checks by ``[@?]``; return the text and what was replaced."""
    known = set(index.citables())
    replaced = []

    def fix(match: re.Match) -> str:
        group = match.group(1)
        if group.strip() == "@?":
            return match.group(0)
        report = check_citations(match.group(0), index, allowed)
        if report.ok:
            return match.group(0)
        if report.malformed:
            replaced.append(match.group(0))
            return "[@?]"
        parts = [part.strip() for part in group.split(";")]
        kept = []
        for part in parts:
            key = part.lstrip("-@").split(",")[0].strip()
            if key in known and key in allowed:
                kept.append(part)
            else:
                replaced.append(key)
        return f"[{'; '.join(kept)}]" if kept else "[@?]"

    return re.sub(r"\[([^\[\]]*@[^\[\]]*)\]", fix, text), replaced


def _split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^## (.+)$", text, re.M))
    return [
        (m.group(1).strip(), text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip())
        for i, m in enumerate(matches)
    ]


def start_in_background(folder: Path, pause_after_plan: bool = False) -> dict:
    """Launch ``ai-writer documento escribir`` detached for this document.

    Raises:
        LibraryError: If a run is already going on, or the abstract is missing.
    """
    run = PerspectiveRun(folder)
    if run.status()["estado"] == "en_curso":
        raise LibraryError("Ya hay una escritura en curso para este documento.")
    if run.status()["estado"] == "terminado":
        raise LibraryError("El documento ya está escrito. Para empezar de cero, borra borrador/estado.json.")
    run._abstract()
    args = ["documento", "escribir", str(Path(folder).resolve())]
    if pause_after_plan:
        args.append("--pausar")
    pid = spawn_cli(args, Path(folder) / LOG)
    run.save(estado="en_curso", pid=pid, error=None)
    return run.status()


def approve_plan(folder: Path) -> dict:
    """Mark the plan as approved and continue writing in the background."""
    run = PerspectiveRun(folder)
    if not (Path(folder) / PLAN).exists():
        raise LibraryError("Todavía no hay plan que aprobar.")
    run._load_plan()  # an edited plan must still be valid
    run.save(plan_aprobado=now())
    return start_in_background(folder)


def request_stop(folder: Path) -> None:
    """Ask a running write to stop after the paragraph in progress."""
    (Path(folder) / STOP).touch()
