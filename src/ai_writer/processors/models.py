"""Data models for PDF processing output."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    """Metadata extracted from a paper."""
    
    paper_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None  # Journal or conference
    source_file: str = ""
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_pages: int = 0
    sections_found: list[str] = Field(default_factory=list)
    # metodo, llamadas, segundos, tramos, motor, modelo
    procesado: dict[str, int | float | str] = Field(default_factory=dict)


class SectionData(BaseModel):
    """Data for a single section of a paper."""
    
    section_id: str = Field(default_factory=lambda: str(uuid4()))
    paper_id: str
    section_name: str
    section_number: int
    content: str
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    word_count: int = 0


class Idea(BaseModel):
    """A main idea extracted from a section."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    paper_id: str
    paper_title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    section: str
    idea: str
    context: str = ""  # Surrounding text for reference
    importance: str = "medium"  # high, medium, low
    kind: Optional[str] = None  # finding, concept, method, limitation, proposal, background
    keywords: list[str] = Field(default_factory=list)
    related_references: list[str] = Field(default_factory=list)
    quote: str = ""  # Sentence copied verbatim from the paper that states the idea
    quote_verified: Optional[bool] = None  # None until checked against the paper's text


class Claim(BaseModel):
    """A claim with evidence extracted from the paper."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    paper_id: str
    paper_title: str
    section: str
    claim: str  # The assertion being made
    evidence: str  # Supporting evidence or data
    evidence_type: str = "citation"  # citation, data, experiment, observation
    cited_references: list[str] = Field(default_factory=list)
    confidence: str = "medium"  # high, medium, low
    origin: str = "propio"  # "citado" if the evidence is another work, else "propio"
    quote: str = ""  # Sentence copied verbatim from the paper that states the claim
    quote_verified: Optional[bool] = None  # None until checked against the paper's text


class ProcessedPaper(BaseModel):
    """Complete processed paper data."""
    
    metadata: PaperMetadata
    sections: list[SectionData] = Field(default_factory=list)
    ideas: list[Idea] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)

    @property
    def usable_ideas(self) -> list[Idea]:
        """Ideas whose quote was not found in the paper are kept out of the indices."""
        return [idea for idea in self.ideas if idea.quote_verified is not False]

    @property
    def usable_claims(self) -> list[Claim]:
        return [claim for claim in self.claims if claim.quote_verified is not False]
