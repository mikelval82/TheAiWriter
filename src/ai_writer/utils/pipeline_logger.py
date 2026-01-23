"""Logging utilities for tracking intermediate steps in paper generation."""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from rich.console import Console

from config.settings import settings

console = Console()


class PipelineLogger:
    """Logger for tracking intermediate steps in the paper generation pipeline."""
    
    def __init__(
        self,
        run_name: str | None = None,
        logs_dir: Path | None = None,
    ) -> None:
        """Initialize the pipeline logger.
        
        Args:
            run_name: Name for this run. Defaults to timestamp.
            logs_dir: Directory for logs. Defaults to data/logs.
        """
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_name = run_name or self.timestamp
        
        # Create logs directory
        self.logs_dir = logs_dir or (settings.paths.data_dir / "logs")
        self.run_dir = self.logs_dir / f"run_{self.run_name}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log files
        self._init_run_log()
        
        console.print(f"[dim]📁 Logs: {self.run_dir}[/dim]")
    
    def _init_run_log(self) -> None:
        """Initialize the main run log file."""
        self.run_log_path = self.run_dir / "run_log.json"
        self.run_log = {
            "run_name": self.run_name,
            "started_at": datetime.now().isoformat(),
            "steps": [],
        }
        self._save_run_log()
    
    def _save_run_log(self) -> None:
        """Save the run log to disk."""
        with open(self.run_log_path, "w", encoding="utf-8") as f:
            json.dump(self.run_log, f, indent=2, ensure_ascii=False)
    
    def log_step(
        self,
        step_name: str,
        data: dict[str, Any],
        save_separate: bool = True,
    ) -> None:
        """Log a pipeline step.
        
        Args:
            step_name: Name of the step (e.g., "phase1_clusters").
            data: Data to log for this step.
            save_separate: Whether to save data in a separate file.
        """
        step_entry = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "summary": self._create_summary(data),
        }
        
        self.run_log["steps"].append(step_entry)
        self._save_run_log()
        
        if save_separate:
            step_file = self.run_dir / f"{step_name}.json"
            with open(step_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            console.print(f"[dim]  💾 {step_name} → {step_file.name}[/dim]")
    
    def _create_summary(self, data: dict) -> dict:
        """Create a summary of the data for the run log."""
        summary = {}
        for key, value in data.items():
            if isinstance(value, list):
                summary[key] = f"{len(value)} items"
            elif isinstance(value, dict):
                summary[key] = f"{len(value)} keys"
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = f"{len(value)} chars"
            else:
                summary[key] = value
        return summary
    
    def log_topics(self, topics: list) -> None:
        """Log extracted topics from cluster analysis.
        
        Args:
            topics: List of ClusterTopic objects.
        """
        topics_data = {
            "n_clusters": len(topics),
            "topics": [
                {
                    "cluster_id": t.cluster_id,
                    "label": t.label,
                    "keywords": t.keywords,
                    "size": t.size,
                    "representative_ideas": t.representative_ideas[:3],
                }
                for t in topics
            ],
        }
        self.log_step("phase1_topics", topics_data)
    
    def log_section_ideas(
        self,
        section_ideas: dict[str, list[dict]],
        section_topic_mapping: dict[str, list[str]],
    ) -> None:
        """Log ideas found for each section.
        
        Args:
            section_ideas: Dict mapping section names to lists of ideas.
            section_topic_mapping: Dict mapping sections to topics used.
        """
        ideas_data = {
            "total_ideas": sum(len(ideas) for ideas in section_ideas.values()),
            "sections": {},
        }
        
        for section_name, ideas in section_ideas.items():
            ideas_data["sections"][section_name] = {
                "n_ideas": len(ideas),
                "topics_used": section_topic_mapping.get(section_name, []),
                "ideas": [
                    {
                        "text": (idea.get("idea") or idea.get("statement") or idea.get("text", ""))[:300],
                        "source": idea.get("source", "Unknown"),
                        "similarity": idea.get("similarity", 0),
                    }
                    for idea in ideas
                ],
            }
        
        self.log_step("phase2_section_ideas", ideas_data)
    
    def log_outline(self, outline) -> None:
        """Log the generated outline.
        
        Args:
            outline: PaperOutline object.
        """
        outline_data = {
            "title": outline.title,
            "thesis_statement": outline.thesis_statement,
            "n_sections": outline.total_sections,
            "n_paragraphs": outline.total_paragraphs,
            "sections": [
                {
                    "name": s.section_name,
                    "purpose": s.section_purpose,
                    "paragraphs": [
                        {
                            "key_idea": p.key_idea,
                            "supporting_points": p.supporting_points,
                            "suggested_sources": p.suggested_sources,
                        }
                        for p in s.paragraphs
                    ],
                }
                for s in outline.sections
            ],
        }
        self.log_step("phase2_outline", outline_data)
    
    def log_prompt(self, prompt: str, prompt_name: str = "planner_prompt") -> None:
        """Log a prompt sent to the LLM.
        
        Args:
            prompt: The full prompt text.
            prompt_name: Name for the prompt file.
        """
        prompt_file = self.run_dir / f"{prompt_name}.md"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        
        self.log_step(prompt_name, {
            "length": len(prompt),
            "file": prompt_file.name,
        }, save_separate=False)
        
        console.print(f"[dim]  💾 {prompt_name} → {prompt_file.name}[/dim]")
    
    def log_llm_response(
        self,
        response: str,
        model: str,
        response_name: str = "llm_response",
    ) -> None:
        """Log an LLM response.
        
        Args:
            response: The raw response text.
            model: Model used.
            response_name: Name for the response file.
        """
        response_file = self.run_dir / f"{response_name}.json"
        with open(response_file, "w", encoding="utf-8") as f:
            json.dump({
                "model": model,
                "response_length": len(response),
                "response": response,
            }, f, indent=2, ensure_ascii=False)
        
        self.log_step(response_name, {
            "model": model,
            "length": len(response),
        }, save_separate=False)
    
    def finalize(self, success: bool = True, error: str | None = None) -> Path:
        """Finalize the run log.
        
        Args:
            success: Whether the run completed successfully.
            error: Error message if failed.
            
        Returns:
            Path to the run directory.
        """
        self.run_log["completed_at"] = datetime.now().isoformat()
        self.run_log["success"] = success
        if error:
            self.run_log["error"] = error
        
        self._save_run_log()
        
        status = "✅" if success else "❌"
        console.print(f"[dim]{status} Run log: {self.run_log_path}[/dim]")
        
        return self.run_dir
