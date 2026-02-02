"""Translator agent for academic paper translation with style guide."""

import json
from pathlib import Path

from ai_writer.agents.base_agent import BaseAgent
from config.settings import settings


class TranslatorAgent(BaseAgent):
    """Agent specialized in academic translation with style guide compliance."""

    def __init__(
        self,
        model: str | None = None,
        style_guide_path: Path | str | None = None,
        glossary_path: Path | str | None = None,
    ) -> None:
        """Initialize the translator agent.

        Args:
            model: The model to use. Defaults to settings default.
            style_guide_path: Path to the style guide markdown file.
            glossary_path: Path to the terminology glossary JSON file.
        """
        super().__init__(model=model)
        
        # Load style guide
        self.style_guide_path = Path(style_guide_path) if style_guide_path else (
            settings.paths.base_dir / "config" / "style_guides" / "mikel_val_calvo_uk_english.md"
        )
        self.style_guide = self._load_style_guide()
        
        # Load glossary
        self.glossary_path = Path(glossary_path) if glossary_path else (
            settings.paths.base_dir / "config" / "terminology" / "hri_glossary.json"
        )
        self.glossary = self._load_glossary()
        
        # Accumulator for new terms discovered during translation
        self.new_terms: dict[str, str] = {}

    def _load_style_guide(self) -> str:
        """Load the style guide from file."""
        if not self.style_guide_path.exists():
            raise FileNotFoundError(f"Style guide not found: {self.style_guide_path}")
        return self.style_guide_path.read_text(encoding="utf-8")

    def _load_glossary(self) -> dict:
        """Load the terminology glossary from file."""
        if not self.glossary_path.exists():
            return {"metadata": {}, "terms": {}, "abbreviations": {}}
        return json.loads(self.glossary_path.read_text(encoding="utf-8"))

    def save_glossary(self) -> None:
        """Save the updated glossary with any new terms."""
        if self.new_terms:
            self.glossary["terms"].update(self.new_terms)
            # Update metadata
            from datetime import datetime
            self.glossary["metadata"]["updated"] = datetime.now().strftime("%Y-%m-%d")
            
            self.glossary_path.parent.mkdir(parents=True, exist_ok=True)
            self.glossary_path.write_text(
                json.dumps(self.glossary, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def _format_glossary_for_prompt(self) -> str:
        """Format the glossary as a reference table for the prompt."""
        lines = ["## Terminology Glossary (Use these exact translations):\n"]
        lines.append("| Spanish | English |")
        lines.append("|---------|---------|")
        for es, en in self.glossary.get("terms", {}).items():
            lines.append(f"| {es} | {en} |")
        
        if self.glossary.get("abbreviations"):
            lines.append("\n## Abbreviations:")
            for abbr, full in self.glossary["abbreviations"].items():
                lines.append(f"- {abbr}: {full}")
        
        return "\n".join(lines)

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for the translator agent."""
        glossary_section = self._format_glossary_for_prompt()
        
        return f"""You are an expert academic translator specializing in scientific papers. 
Your task is to translate Spanish academic texts to British English (UK) following a specific style guide.

CRITICAL INSTRUCTIONS:
1. Translate ONLY the content - do not add, remove, or modify the meaning
2. Maintain all Markdown formatting exactly (headers, lists, emphasis, links)
3. Keep all citations in their original format: (Author et al., 2023)
4. Do NOT translate author names or paper titles in citations
5. Use British English spelling consistently (behaviour, centre, optimise, etc.)
6. Preserve all technical terms according to the glossary provided
7. Maintain the academic register and formal tone throughout

STYLE GUIDE:
{self.style_guide}

{glossary_section}

OUTPUT FORMAT:
- Return ONLY the translated text in Markdown
- Do not include any explanations or comments
- Preserve the exact structure of the original
"""

    def translate_section(
        self,
        section_content: str,
        section_name: str,
        abstract_context: str = "",
    ) -> str:
        """Translate a single section of the paper.

        Args:
            section_content: The Spanish content to translate.
            section_name: Name of the section (for context).
            abstract_context: Previously translated abstract for consistency.

        Returns:
            The translated section in British English.
        """
        context_block = ""
        if abstract_context:
            context_block = f"""
CONTEXT - Previously translated Abstract (for terminology consistency):
---
{abstract_context}
---

"""

        user_prompt = f"""{context_block}Translate the following "{section_name}" section from Spanish to British English:

---
{section_content}
---

Remember:
- Follow the style guide strictly
- Use British English spelling
- Maintain all formatting and citations
- Use the glossary terms consistently
"""

        return self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=settings.ai.max_tokens,
        )

    def translate_abstract(self, abstract_content: str) -> str:
        """Translate the abstract section.
        
        This is handled separately as it sets the tone for the entire translation.

        Args:
            abstract_content: The Spanish abstract to translate.

        Returns:
            The translated abstract in British English.
        """
        user_prompt = f"""Translate the following Abstract from Spanish to British English.

This Abstract sets the tone and terminology for the entire paper, so ensure:
- Precise academic language
- Consistent terminology that will be used throughout
- Clear, impactful opening and closing sentences

---
{abstract_content}
---
"""

        return self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=settings.ai.max_tokens,
        )
