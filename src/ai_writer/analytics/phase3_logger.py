"""Logger for Phase 3 (Writing) to track RAG retrieval during paragraph writing.

This module logs every context retrieval during the writing phase,
enabling post-hoc analysis of exploration vs exploitation.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RetrievalRecord:
    """Record of a single context retrieval."""
    
    timestamp: str
    section_name: str
    paragraph_number: int
    query: str
    
    # Retrieved items
    ideas_retrieved: list[dict] = field(default_factory=list)
    claims_retrieved: list[dict] = field(default_factory=list)
    
    # Metadata
    ideas_count: int = 0
    claims_count: int = 0
    unique_papers: int = 0
    avg_similarity: float = 0.0


class Phase3Logger:
    """Logger for tracking context retrieval during writing phase."""
    
    def __init__(self, log_dir: Path | str):
        """Initialize logger.
        
        Args:
            log_dir: Directory to store phase3 logs.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.retrievals: list[RetrievalRecord] = []
        self.all_idea_indices: list[int] = []  # Track which ideas were retrieved
        self.all_claim_indices: list[int] = []  # Track which claims were retrieved
    
    def log_retrieval(
        self,
        section_name: str,
        paragraph_number: int,
        query: str,
        ideas: list[dict],
        claims: list[dict],
    ) -> None:
        """Log a context retrieval.
        
        Args:
            section_name: Name of the section being written.
            paragraph_number: Paragraph number within section.
            query: The query used for retrieval.
            ideas: List of retrieved ideas with metadata.
            claims: List of retrieved claims with metadata.
        """
        # Track indices
        for idea in ideas:
            if "index" in idea:
                self.all_idea_indices.append(idea["index"])
        
        for claim in claims:
            if "index" in claim:
                self.all_claim_indices.append(claim["index"])
        
        # Calculate unique papers
        papers = set()
        for item in ideas + claims:
            if "source" in item and item["source"]:
                papers.add(item["source"])
        
        # Calculate average similarity
        similarities = []
        for item in ideas + claims:
            if "similarity" in item:
                similarities.append(item["similarity"])
        
        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
        
        record = RetrievalRecord(
            timestamp=datetime.now().isoformat(),
            section_name=section_name,
            paragraph_number=paragraph_number,
            query=query[:200],  # Truncate query for readability
            ideas_retrieved=ideas,
            claims_retrieved=claims,
            ideas_count=len(ideas),
            claims_count=len(claims),
            unique_papers=len(papers),
            avg_similarity=avg_sim,
        )
        
        self.retrievals.append(record)
    
    def save(self) -> Path:
        """Save logs to file.
        
        Returns:
            Path to saved log file.
        """
        log_path = self.log_dir / "phase3_retrievals.json"
        
        # Compute summary statistics
        summary = {
            "total_retrievals": len(self.retrievals),
            "total_ideas_retrieved": sum(r.ideas_count for r in self.retrievals),
            "total_claims_retrieved": sum(r.claims_count for r in self.retrievals),
            "unique_idea_indices": len(set(self.all_idea_indices)),
            "unique_claim_indices": len(set(self.all_claim_indices)),
            "idea_reuse_ratio": self._compute_reuse_ratio(self.all_idea_indices),
            "claim_reuse_ratio": self._compute_reuse_ratio(self.all_claim_indices),
        }
        
        data = {
            "summary": summary,
            "retrievals": [asdict(r) for r in self.retrievals],
        }
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return log_path
    
    def _compute_reuse_ratio(self, indices: list[int]) -> float:
        """Compute how often items are reused.
        
        Returns:
            Ratio of total retrievals to unique items. 
            1.0 = no reuse, higher = more reuse.
        """
        if not indices:
            return 0.0
        unique = len(set(indices))
        return len(indices) / unique


def integrate_with_context_manager():
    """Code snippet showing how to integrate with EnhancedContextManager."""
    
    code = '''
# In enhanced_context_manager.py, add to __init__:
self.phase3_logger: Phase3Logger | None = None

def set_phase3_logger(self, logger: Phase3Logger) -> None:
    """Set logger for phase 3 retrieval tracking."""
    self.phase3_logger = logger

# In get_context_for_idea(), after combining results:
if self.phase3_logger:
    self.phase3_logger.log_retrieval(
        section_name=section_name,
        paragraph_number=getattr(self, '_current_paragraph', 0),
        query=query,
        ideas=ideas_results,
        claims=claims_results,
    )
'''
    return code
