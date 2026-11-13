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
from dataclasses import asdict
from pathlib import Path

from ai_writer.background import now, process_alive, spawn_cli
from ai_writer.citations import CitationIndex, check_citations
from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMClient, LLMError, get_llm_client
from ai_writer.profiles import profile_for
from config.settings import settings

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
                s["titulo"] for s in state.get("secciones", []) if s.get("resumen")
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
        from ai_writer.validation import record_retrieved

        outline = self._load_plan()
        manager = self.context_manager(abstract)
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
            memory = self._memory_context(sections[:i])

            for j, paragraph in enumerate(section_outline.paragraphs):
                if j < len(state["parrafos"]):
                    continue
                self._check_stop()
                query = paragraph.to_query()
                context = manager.get_context_for_idea(
                    idea_query=query,
                    section_name=section_outline.section_name,
                    suggested_topics=paragraph.suggested_sources,
                )
                record_retrieved(self.folder, query, _CITED_KEY.findall(context))
                text = writer.write_paragraph(
                    key_idea=paragraph.key_idea,
                    supporting_points=paragraph.supporting_points,
                    section_name=section_outline.section_name,
                    section_purpose=section_outline.section_purpose,
                    previous_paragraphs=state["parrafos"],
                    reference_context=context,
                    thesis=outline.thesis_statement,
                    memory_context=memory,
                )
                state["parrafos"].append(text)
                self._save_used()
                self._track_usage()
                self.save()
                self.render(abstract)

            if state.get("contenido") is None:
                self._check_stop()
                section = Section(title=state["titulo"], content="\n\n".join(state["parrafos"]))
                reviewer.section_summaries = self._summaries(sections[:i])
                section = reviewer.review_section(
                    section=section, previous_sections=None, update_memory=False
                )
                state["contenido"] = section.content
                self._track_usage()
                self.save()
                self.render(abstract)
            if state.get("resumen") is None:
                state["resumen"] = self._summarize(state["titulo"], state["contenido"])
                self._track_usage()
                self.save()

    def _summaries(self, sections: list[dict]) -> dict[str, str]:
        return {s["titulo"]: s["resumen"] for s in sections if s.get("resumen")}

    def _memory_context(self, sections: list[dict]) -> str:
        summaries = self._summaries(sections)
        if not summaries:
            return ""
        lines = ["\n\nMEMORIA DEL PAPER (resúmenes de secciones anteriores):"]
        lines += [f"\n### {title}\n{summary}" for title, summary in summaries.items()]
        return "\n".join(lines) + "\n"

    def _summarize(self, title: str, content: str) -> str:
        prompt = f"""Genera un resumen conciso de la siguiente sección de un paper académico.

SECCIÓN: {title}

CONTENIDO:
{content}

INSTRUCCIONES:
- Resume en 3-5 oraciones los puntos clave y argumentos principales
- Incluye la tesis o idea central de la sección
- Menciona conceptos o términos importantes introducidos
- Sé preciso y conciso (máximo 150 palabras)

RESUMEN:"""
        return self.llm.complete(
            "Eres un asistente experto en síntesis de textos académicos.",
            prompt,
            model=settings.ai.fast_model,
            max_tokens=300,
        ).strip()

    # Phase 4: global review

    def _global_review(self, abstract: str) -> None:
        from ai_writer.agents.reviewer_agent import ReviewerAgent
        from ai_writer.models.paper import Paper, Section

        self._check_stop()
        self.save(fase="revision_global")
        sections = self.state["secciones"]
        paper = Paper(
            title=self.project.titulo,
            sections=[Section(title="Abstract", content=abstract)]
            + [Section(title=s["titulo"], content=s["contenido"]) for s in sections],
        )
        reviewer = ReviewerAgent(abstract_context=abstract)
        reviewer.llm = self.llm
        reviewed = {}
        try:
            result = reviewer.review_full_paper(paper)
            reviewed = {s.title: s.content for s in result.sections[1:]}
        except LLMError as error:
            self.state["aviso_revision_global"] = str(error)
        # Only a complete answer replaces the sections: a partial one would drop text
        if set(reviewed) == {s["titulo"] for s in sections} and all(reviewed.values()):
            for s in sections:
                s["revisada_global"] = reviewed[s["titulo"]]
        else:
            self.state["aviso_revision_global"] = self.state.get(
                "aviso_revision_global",
                "La revisión global no devolvió todas las secciones; se conserva el texto revisado por sección.",
            )
        self._track_usage()
        self.save(revision_global_hecha=now())
        self.render(abstract)

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
        report = validate_document(self.folder)

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
