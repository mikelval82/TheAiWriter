"""Advanced orchestrator with 3-phase architecture for perspective papers.

Phase 1: Cluster Analysis - Extract main topics from embedding space
Phase 2: Planning - Generate detailed outline with paragraph-level ideas
Phase 3: Writing - Write paragraph-by-paragraph with idea-specific queries
"""

from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_writer.agents.writer_agent import WriterAgent
from ai_writer.agents.reviewer_agent import ReviewerAgent
from ai_writer.agents.planner_agent import PlannerAgent
from ai_writer.models.paper import Paper, Section
from ai_writer.models.outline import PaperOutline, SectionOutline, ParagraphOutline
from ai_writer.readers.markdown_reader import MarkdownReader
from ai_writer.writers.markdown_writer import MarkdownWriter
from ai_writer.utils.cluster_analyzer import ClusterAnalyzer
from ai_writer.utils.enhanced_context_manager import EnhancedContextManager
from ai_writer.utils.pipeline_logger import PipelineLogger
from config.settings import settings

console = Console()


class AdvancedPerspectiveOrchestrator:
    """Advanced orchestrator with cluster analysis, planning, and targeted writing."""

    def __init__(
        self,
        abstract_path: Path | str | None = None,
        review_iterations: int = 1,
        n_clusters: int = 25,  # Increased from 12 for better embedding space coverage
        outline_review_iterations: int = 1,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the advanced orchestrator.

        Args:
            abstract_path: Path to the abstract markdown file.
            review_iterations: Number of review iterations per section.
            n_clusters: Number of clusters for topic extraction.
            outline_review_iterations: Iterations for refining the outline.
            enable_logging: Whether to enable pipeline logging.
        """
        self.abstract_path = Path(abstract_path) if abstract_path else (
            settings.paths.references_markdown_dir / "ABSTRACT.md"
        )
        self.review_iterations = max(1, review_iterations)
        self.n_clusters = n_clusters
        self.outline_review_iterations = outline_review_iterations
        self.enable_logging = enable_logging
        
        # Initialize components
        self.markdown_reader = MarkdownReader()
        self.markdown_writer = MarkdownWriter()
        
        # Load abstract
        self.abstract_context = self._load_abstract()
        
        # Initialize cluster analyzer
        self.cluster_analyzer = ClusterAnalyzer(n_clusters=n_clusters)
        
        # Initialize context manager
        self.context_manager = EnhancedContextManager(
            abstract_context=self.abstract_context,
        )
        
        # Initialize agents
        self.planner_agent = PlannerAgent()
        self.writer_agent = WriterAgent(abstract_context=self.abstract_context)
        self.reviewer_agent = ReviewerAgent(
            abstract_context=self.abstract_context,
            context_manager=self.context_manager,
        )
        
        # State
        self.current_outline: PaperOutline | None = None
        self.topic_centroids: dict = {}
        self.output_file_path: Path | None = None
        self.logger: PipelineLogger | None = None
        
        # Short-term memory: resúmenes de secciones escritas (manejado por orquestador)
        self.section_memory: dict[str, str] = {}

    def _load_abstract(self) -> str:
        """Load the abstract from the configured path."""
        if not self.abstract_path.exists():
            raise FileNotFoundError(
                f"Abstract file not found: {self.abstract_path}"
            )
        
        content = self.markdown_reader.read(self.abstract_path)
        console.print(Panel(
            content[:500] + "..." if len(content) > 500 else content,
            title="📄 Abstract Cargado",
            border_style="green",
        ))
        return content

    # =========================================================================
    # Section Memory Management
    # =========================================================================
    
    def _reset_section_memory(self) -> None:
        """Reset the section memory for a new paper."""
        self.section_memory = {}
    
    def _generate_section_summary(self, section: Section) -> str:
        """Generate a concise summary of a section for memory.
        
        Args:
            section: The section to summarize.
            
        Returns:
            A concise summary capturing key points.
        """
        from ai_writer.agents.base_agent import BaseAgent
        
        # Use a lightweight call to generate summary
        client = self.writer_agent.client
        model = self.writer_agent.model
        
        user_prompt = f"""Genera un resumen conciso de la siguiente sección de un paper académico.

SECCIÓN: {section.title}

CONTENIDO:
{section.content}

INSTRUCCIONES:
- Resume en 3-5 oraciones los puntos clave y argumentos principales
- Incluye la tesis o idea central de la sección
- Menciona conceptos o términos importantes introducidos
- Sé preciso y conciso (máximo 150 palabras)

RESUMEN:"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres un asistente experto en síntesis de textos académicos."},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=300,
        )
        
        return response.choices[0].message.content.strip()
    
    def _update_section_memory(self, section: Section) -> None:
        """Update memory with a completed section.
        
        Args:
            section: The completed section to add to memory.
        """
        console.print(f"  [dim]💭 Generando resumen para memoria...[/dim]")
        summary = self._generate_section_summary(section)
        self.section_memory[section.title] = summary
    
    def _get_memory_context(self) -> str:
        """Get formatted memory context for agents.
        
        Returns:
            Formatted string with section summaries.
        """
        if not self.section_memory:
            return ""
        
        context = "\n\nMEMORIA DEL PAPER (resúmenes de secciones anteriores):\n"
        for title, summary in self.section_memory.items():
            context += f"\n### {title}\n{summary}\n"
        
        return context

    # =========================================================================
    # PHASE 1: Cluster Analysis
    # =========================================================================
    
    def phase1_analyze_topics(self, title: str = "paper") -> list:
        """Phase 1: Analyze embedding space and extract main topics.
        
        Args:
            title: Paper title for logging.
        
        Returns:
            List of ClusterTopic objects.
        """
        # Initialize logger if enabled
        if self.enable_logging and not self.logger:
            safe_title = title.replace(" ", "_").replace(":", "")
            self.logger = PipelineLogger(run_name=safe_title)
        
        console.print(Panel(
            "[bold]FASE 1: Análisis de Clusters[/bold]\n\n"
            "Analizando el espacio de embeddings para extraer\n"
            "los temas principales de la literatura...",
            title="🔬 Phase 1",
            border_style="cyan",
        ))
        
        # Analyze ideas (main conceptual content)
        topics = self.cluster_analyzer.analyze(embed_type="ideas")
        
        # Display results
        self.cluster_analyzer.display_topics(topics)
        
        # Store centroids for later targeted searches
        self.topic_centroids = self.cluster_analyzer.get_topic_centroids(topics)
        
        # Log topics
        if self.logger:
            self.logger.log_topics(topics)
        
        return topics

    # =========================================================================
    # PHASE 2: Planning
    # =========================================================================
    
    def _create_section_topic_mapping(
        self,
        topics: list,
    ) -> dict[str, list[str]]:
        """Create a mapping of sections to relevant topics.
        
        Args:
            topics: List of ClusterTopic objects.
            
        Returns:
            Dict mapping section names to list of topic labels.
        """
        from ai_writer.agents.planner_agent import PERSPECTIVE_SECTIONS
        
        topic_labels = [t.label for t in topics]
        n_topics = len(topic_labels)
        
        # Define which topics are most relevant for each section type
        # With more clusters (25+), we assign more topics per section for diversity
        section_mapping = {}
        
        for section_name, purpose, _, _ in PERSPECTIVE_SECTIONS:
            # Assign topics based on section purpose
            if "introducción" in section_name.lower():
                # Introduction: broad overview, use largest 6 clusters
                section_mapping[section_name] = topic_labels[:6]
            elif "estado" in section_name.lower() or "arte" in section_name.lower():
                # State of the art: use ALL topics for maximum coverage
                section_mapping[section_name] = topic_labels
            elif "problema" in section_name.lower() or "brecha" in section_name.lower():
                # Problem identification: focus on smaller/niche topics (second half)
                section_mapping[section_name] = topic_labels[n_topics//2:]
            elif "perspectiva" in section_name.lower() or "nueva" in section_name.lower():
                # New perspective: use topics related to main concepts (first 8)
                section_mapping[section_name] = topic_labels[:8]
            elif "discusión" in section_name.lower():
                # Discussion: broad analysis, all topics
                section_mapping[section_name] = topic_labels
            elif "implicaciones" in section_name.lower() or "futuras" in section_name.lower():
                # Future implications: focus on emerging topics (varied selection)
                section_mapping[section_name] = topic_labels[:10]
            elif "desafíos" in section_name.lower() or "limitaciones" in section_name.lower():
                # Challenges: use diverse topics from different regions
                section_mapping[section_name] = topic_labels[::2] + topic_labels[1::4]  # More varied
            elif "conclusiones" in section_name.lower():
                # Conclusions: main themes (first 5)
                section_mapping[section_name] = topic_labels[:5]
            else:
                # Default: use top 5 topics
                section_mapping[section_name] = topic_labels[:5]
        
        return section_mapping
    
    def phase2_generate_outline(
        self,
        title: str,
        topics: list,
    ) -> PaperOutline:
        """Phase 2: Generate detailed paper outline based on topics.
        
        Args:
            title: Paper title.
            topics: Topics from cluster analysis.
            
        Returns:
            Complete PaperOutline object.
        """
        console.print(Panel(
            "[bold]FASE 2: Planificación[/bold]\n\n"
            "Generando esquema detallado del paper\n"
            "con ideas clave por párrafo...",
            title="📋 Phase 2",
            border_style="yellow",
        ))
        
        # Get topics summary for planner
        topics_summary = self.cluster_analyzer.get_topics_summary(topics)
        
        # Create section-to-topic mapping
        section_topic_mapping = self._create_section_topic_mapping(topics)
        
        # Search for relevant ideas for each section using topic centroids
        console.print("[cyan]🔍 Buscando ideas relevantes por sección...[/cyan]")
        section_ideas = self.cluster_analyzer.get_ideas_for_sections(
            topics=topics,
            section_topic_mapping=section_topic_mapping,
            ideas_per_section=16,  # Increased from 8 for better context
        )
        
        # Display how many ideas were found per section
        for section_name, ideas in section_ideas.items():
            console.print(f"[dim]  {section_name}: {len(ideas)} ideas[/dim]")
        
        # Log section ideas
        if self.logger:
            self.logger.log_section_ideas(section_ideas, section_topic_mapping)
        
        # Generate initial outline with literature-grounded ideas
        outline = self.planner_agent.generate_outline(
            abstract=self.abstract_context,
            topics_summary=topics_summary,
            title=title,
            section_ideas=section_ideas,
            logger=self.logger,
        )
        outline.available_topics = [t.label for t in topics]
        
        # Log outline
        if self.logger:
            self.logger.log_outline(outline)
        
        # Iterative refinement with reviewer
        for i in range(self.outline_review_iterations):
            console.print(f"[yellow]🔄 Refinamiento {i + 1}/{self.outline_review_iterations}[/yellow]")
            
            # Get feedback from reviewer
            feedback = self.reviewer_agent.review_outline(outline)
            
            # Log the feedback
            if self.logger and feedback:
                self.logger.log_data(f"outline_feedback_{i+1}", {
                    "iteration": i + 1,
                    "feedback": feedback,
                    "requires_changes": "sin cambios" not in feedback.lower()
                })
                console.print(f"  💾 Feedback guardado → outline_feedback_{i+1}.json")
            
            if feedback and "sin cambios" not in feedback.lower():
                outline = self.planner_agent.refine_outline(outline, feedback)
                
                # Log the refined outline
                if self.logger:
                    self.logger.log_data(f"outline_refined_{i+1}", outline.to_dict())
                    console.print(f"  💾 Outline refinado → outline_refined_{i+1}.json")
            else:
                console.print(f"  ✓ Reviewer: Sin cambios necesarios")
        
        # Save outline to disk
        self._save_outline(outline, title)
        
        # Display final outline
        self.planner_agent.display_outline(outline)
        
        self.current_outline = outline
        return outline

    # =========================================================================
    # PHASE 3: Writing
    # =========================================================================
    
    def phase3_write_paper(
        self,
        outline: PaperOutline,
    ) -> Paper:
        """Phase 3: Write the paper paragraph by paragraph.
        
        Args:
            outline: The paper outline to follow.
            
        Returns:
            Complete Paper object.
        """
        console.print(Panel(
            "[bold]FASE 3: Escritura[/bold]\n\n"
            "Escribiendo el paper párrafo por párrafo\n"
            "con queries específicas por idea...",
            title="✍️ Phase 3",
            border_style="green",
        ))
        
        # Reset exploration state for this new paper
        self.context_manager.reset_exploration_state()
        
        # Reset section memory for fresh paper
        self._reset_section_memory()
        
        # Initialize output file
        self._initialize_output_file(outline.title)
        
        # Create paper with abstract
        paper = Paper(
            title=outline.title,
            sections=[Section(title="Abstract", content=self.abstract_context)],
        )
        
        generated_sections = []
        
        for section_outline in outline.sections:
            section = self._write_section_from_outline(
                section_outline=section_outline,
                previous_sections=paper.sections + generated_sections,
                thesis=outline.thesis_statement,
            )
            generated_sections.append(section)
            
            # Append to output file
            self._append_section_to_file(section)
        
        paper.sections.extend(generated_sections)
        
        # Log exploration statistics
        exploration_stats = self.context_manager.get_exploration_stats()
        console.print(Panel(
            f"[bold]Estadísticas de Exploración RAG:[/bold]\n"
            f"• Ideas únicas usadas: {exploration_stats['unique_ideas_used']}\n"
            f"• Claims únicos usados: {exploration_stats['unique_claims_used']}\n"
            f"• Cobertura ideas: {exploration_stats['ideas_coverage_percent']:.1f}%\n"
            f"• Clusters explorados: {exploration_stats['clusters_explored']}/{exploration_stats['total_clusters']} "
            f"({exploration_stats['clusters_coverage_percent']:.0f}%)",
            title="📊 Exploration Stats",
            border_style="cyan",
        ))
        
        # Add bibliography
        citations = self.context_manager.get_all_citations()
        if citations:
            bib_content = "\n".join(f"- {cite}" for cite in citations)
            paper.sections.append(Section(
                title="Referencias Utilizadas",
                content=bib_content,
            ))
        
        return paper

    def _write_section_from_outline(
        self,
        section_outline: SectionOutline,
        previous_sections: list[Section],
        thesis: str,
    ) -> Section:
        """Write a section following the outline paragraph by paragraph.
        
        Args:
            section_outline: The section outline to follow.
            previous_sections: Already written sections.
            thesis: Paper's thesis statement.
            
        Returns:
            Completed Section object.
        """
        section_name = section_outline.section_name
        console.print(f"\n[bold cyan]📝 Escribiendo: {section_name}[/bold cyan]")
        
        # Get memory context (summaries of previous sections)
        memory_context = self._get_memory_context()
        
        paragraphs_content = []
        
        for para_outline in section_outline.paragraphs:
            console.print(f"  [dim]Párrafo {para_outline.paragraph_number}: {para_outline.key_idea[:50]}...[/dim]")
            
            # Get targeted context using paragraph's key idea (NOT the abstract)
            context = self._get_context_for_paragraph(para_outline, section_name)
            
            # Write paragraph with memory context
            para_text = self._write_paragraph(
                paragraph_outline=para_outline,
                section_name=section_name,
                section_purpose=section_outline.section_purpose,
                previous_paragraphs=paragraphs_content,
                reference_context=context,
                thesis=thesis,
                memory_context=memory_context,
            )
            
            paragraphs_content.append(para_text)
        
        # Combine paragraphs into section
        section_content = "\n\n".join(paragraphs_content)
        
        section = Section(title=section_name, content=section_content)
        
        # Review iterations - pass memory to reviewer
        for iteration in range(self.review_iterations):
            console.print(
                f"  [yellow]🔄 Revisión {iteration + 1}/{self.review_iterations}[/yellow]"
            )
            # Share orchestrator's memory with reviewer
            self.reviewer_agent.section_summaries = self.section_memory.copy()
            section = self.reviewer_agent.review_section(
                section=section,
                previous_sections=None,  # No longer needed, using memory
                update_memory=False,  # Orchestrator manages memory
            )
        
        # Update orchestrator's memory with the completed section
        self._update_section_memory(section)
        
        console.print(f"  [green]✓ {section_name} completado[/green]")
        return section

    def _save_outline(self, outline: PaperOutline, title: str) -> Path:
        """Save the outline to disk in both markdown and JSON formats.
        
        Args:
            outline: The paper outline to save.
            title: Paper title for filename.
            
        Returns:
            Path to the saved markdown file.
        """
        output_dir = settings.paths.drafts_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        
        # Save as markdown
        md_path = output_dir / f"{safe_title}_outline.md"
        md_path.write_text(outline.to_markdown(), encoding="utf-8")
        console.print(f"[dim]📋 Outline guardado: {md_path}[/dim]")
        
        # Save as JSON for potential reuse
        json_path = output_dir / f"{safe_title}_outline.json"
        json_path.write_text(outline.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]📋 Outline JSON: {json_path}[/dim]")
        
        return md_path

    def _get_context_for_paragraph(
        self,
        paragraph_outline: ParagraphOutline,
        section_name: str,
    ) -> str:
        """Get targeted context for a specific paragraph using its key idea.
        
        This is the KEY DIFFERENCE from the original orchestrator:
        Instead of querying with the abstract, we query with the
        paragraph's specific key idea.
        
        Args:
            paragraph_outline: The paragraph outline with key idea.
            section_name: Name of the section.
            
        Returns:
            Formatted context string.
        """
        # Build query from paragraph's key idea and supporting points
        query = paragraph_outline.to_query()
        
        # Use the enhanced context manager's idea-specific search
        return self.context_manager.get_context_for_idea(
            idea_query=query,
            section_name=section_name,
            suggested_topics=paragraph_outline.suggested_sources,
        )

    def _write_paragraph(
        self,
        paragraph_outline: ParagraphOutline,
        section_name: str,
        section_purpose: str,
        previous_paragraphs: list[str],
        reference_context: str,
        thesis: str,
        memory_context: str = "",
    ) -> str:
        """Write a single paragraph based on outline and context.
        
        Args:
            paragraph_outline: The paragraph outline to follow.
            section_name: Name of the section.
            section_purpose: Purpose of the section.
            previous_paragraphs: Already written paragraphs in this section.
            reference_context: Context from embeddings search.
            thesis: Paper's thesis statement.
            memory_context: Summary of previous sections for coherence.
            
        Returns:
            Written paragraph text.
        """
        return self.writer_agent.write_paragraph(
            key_idea=paragraph_outline.key_idea,
            supporting_points=paragraph_outline.supporting_points,
            section_name=section_name,
            section_purpose=section_purpose,
            previous_paragraphs=previous_paragraphs,
            reference_context=reference_context,
            thesis=thesis,
            memory_context=memory_context,
        )

    def _initialize_output_file(self, title: str) -> Path:
        """Initialize the output file."""
        output_dir = settings.paths.final_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        
        self.output_file_path = output_dir / f"{safe_title}.md"
        
        initial_content = f"# {title}\n\n## Abstract\n\n{self.abstract_context}\n\n"
        self.output_file_path.write_text(initial_content, encoding="utf-8")
        
        console.print(f"[dim]📄 Archivo de salida: {self.output_file_path}[/dim]")
        return self.output_file_path

    def _append_section_to_file(self, section: Section) -> None:
        """Append a section to the output file."""
        if self.output_file_path is None:
            return
        
        section_content = f"## {section.title}\n\n{section.content}\n\n"
        
        with open(self.output_file_path, "a", encoding="utf-8") as f:
            f.write(section_content)
        
        console.print(f"  [dim]💾 Sección guardada[/dim]")

    # =========================================================================
    # Main Run Method
    # =========================================================================
    
    def run(
        self,
        title: str,
        output_dir: Path | str | None = None,
    ) -> tuple[Path, Path]:
        """Run the complete 3-phase pipeline.
        
        Args:
            title: Paper title.
            output_dir: Output directory.
            
        Returns:
            Tuple of (paper path, critical review path).
        """
        console.print(Panel(
            f"[bold]Generando Paper de Perspectivas[/bold]\n\n"
            f"📌 Título: {title}\n"
            f"🔬 Clusters: {self.n_clusters}\n"
            f"🔄 Revisiones/sección: {self.review_iterations}\n\n"
            "[cyan]Arquitectura de 3 Fases:[/cyan]\n"
            "  1. Análisis de Clusters\n"
            "  2. Planificación con Ideas Clave\n"
            "  3. Escritura Párrafo por Párrafo",
            title="🚀 Advanced Perspective Paper Orchestrator",
            border_style="blue",
        ))
        
        output_dir = Path(output_dir) if output_dir else settings.paths.final_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # PHASE 1: Cluster Analysis
        topics = self.phase1_analyze_topics()
        
        # PHASE 2: Planning
        outline = self.phase2_generate_outline(title, topics)
        
        # PHASE 3: Writing
        paper = self.phase3_write_paper(outline)
        
        # Paper path
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        paper_path = self.output_file_path or (output_dir / f"{safe_title}.md")

        # Final review
        reviewed_paper = paper
        critical_review = ""
        try:
            reviewed_paper, critical_review = self.reviewer_agent.review_full_paper(paper), ""
            critical_review = self.reviewer_agent.generate_critical_review(paper)
            self.markdown_writer.write(reviewed_paper, paper_path)
            console.print(f"[green]📄 Paper final guardado: {paper_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Error en revisión final: {e}[/yellow]")
            console.print(f"[yellow]  Paper guardado sin revisión final[/yellow]")

        # Save critical review
        review_path = output_dir / f"{safe_title}_critical_review.md"
        if critical_review:
            review_path.write_text(critical_review, encoding="utf-8")
        else:
            review_path.write_text("# Revisión Crítica\n\nNo disponible.", encoding="utf-8")

        console.print("\n[bold green]✓ Pipeline completado exitosamente![/bold green]")
        return paper_path, review_path
