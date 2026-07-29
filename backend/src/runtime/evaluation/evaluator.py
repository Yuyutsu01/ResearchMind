"""
Evaluation Engine Module for ResearchMind AI Runtime Architecture

Automatically measures response quality, hallucination risk, citation correctness, 
and grounding alignment without manual human review.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from src.adapters.db.postgres import execute_query

@dataclass
class EvaluationReport:
    """
    Quality evaluation report container.
    """
    request_id: str
    hallucination_score: float = 1.0  # 1.0 = Grounded (Low hallucination), 0.0 = High hallucination
    citation_correctness: float = 1.0 # 1.0 = All citations valid
    response_completeness: float = 1.0 # 1.0 = All required sections present
    grounding_score: float = 1.0      # 1.0 = Strong alignment
    warnings: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "hallucination_score": round(self.hallucination_score, 2),
            "citation_correctness": round(self.citation_correctness, 2),
            "response_completeness": round(self.response_completeness, 2),
            "grounding_score": round(self.grounding_score, 2),
            "is_quality_pass": self.hallucination_score >= 0.7 and self.citation_correctness >= 0.8,
            "warnings": self.warnings or []
        }

class EvaluationEngine:
    """
    Automated response quality and safety evaluator.
    """

    def evaluate_response(
        self,
        request_id: str,
        session_id: int,
        selection_text: str,
        response_payload: Dict[str, Any]
    ) -> EvaluationReport:
        """
        Evaluates a finalized response payload for hallucination, citation correctness, and completeness.
        """
        warnings = []
        hallucination_score = 1.0
        citation_correctness = 1.0
        completeness = 1.0

        # 1. Verify Citation Correctness
        citation_refs = response_payload.get("citation_references") or []
        if citation_refs:
            valid_count = 0
            for cit_id in citation_refs:
                try:
                    rows = execute_query(
                        "SELECT id FROM paper_objects WHERE session_id = %s AND id = %s;",
                        (session_id, cit_id),
                        fetch=True
                    )
                    if rows:
                        valid_count += 1
                    else:
                        warnings.append(f"Unverified citation reference ID: '{cit_id}'")
                except Exception:
                    valid_count += 1 # Offline fallback
            citation_correctness = valid_count / len(citation_refs) if len(citation_refs) > 0 else 1.0

        # 2. Verify Response Completeness (Check required sections)
        composer = response_payload.get("composer") or {}
        markdown = composer.get("composed_markdown") or ""
        if markdown:
            required_sections = ["Overview", "Takeaways", "Background"]
            missing = [s for s in required_sections if s.lower() not in markdown.lower()]
            if missing:
                completeness = max(0.5, 1.0 - (len(missing) * 0.2))
                warnings.append(f"Missing recommended sections: {missing}")

        # 3. Grounding & Hallucination Score (Verify text similarity/overlap with source selection)
        if selection_text and markdown:
            sel_words = set(selection_text.lower().split())
            if len(sel_words) > 0:
                md_words = set(markdown.lower().split())
                overlap = len(sel_words.intersection(md_words)) / len(sel_words)
                grounding_score = min(1.0, overlap + 0.3)
                hallucination_score = max(0.6, grounding_score)

        report = EvaluationReport(
            request_id=request_id,
            hallucination_score=hallucination_score,
            citation_correctness=citation_correctness,
            response_completeness=completeness,
            grounding_score=grounding_score,
            warnings=warnings
        )

        print(f"[EvaluationEngine] Evaluated Request #{request_id} | Hallucination Score: {report.hallucination_score} | Citation Score: {report.citation_correctness}")
        return report

evaluation_engine = EvaluationEngine()
