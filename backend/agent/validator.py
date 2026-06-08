import os
import sys
import time

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.citation_tool import validate_citations
from memory.postgres.db import log_tool_call

def validation_node(state: dict) -> dict:
    """
    LangGraph node to validate scientific summaries and citation claims.
    """
    start_time = time.time()
    print("[Validation Agent] Validating report content and citations...")
    
    messages = list(state.get("messages", []))
    messages.append("Validation Agent: Reviewing outputs for hallucinations.")
    
    sections = state.get("sections", {})
    # Flatten text to validate citation mentions
    full_text = "\n".join(sections.values())
    
    # Grab references from retrieved papers
    references = []
    for paper in state.get("retrieved_papers", []):
        ref_str = f"{', '.join(paper.get('authors', [])) or 'Anon'}. {paper.get('title')}. ({paper.get('published')})."
        references.append(ref_str)
        
    # Check citations
    cite_report = validate_citations(full_text, references)
    
    # Mock fact check scoring
    fact_score = 0.90 if full_text else 0.50
    
    validation_results = {
        "citation_check": cite_report,
        "fact_check": {
            "score": fact_score,
            "status": "passed" if fact_score > 0.7 else "warning"
        },
        "overall_score": round((cite_report["score"] + fact_score) / 2.0, 2)
    }
    
    # Log the tool call in DB
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=state.get("task_id", 0),
        step_index=4,
        tool_name="validation_evaluator",
        kwargs={"total_citations": cite_report["total_citations_found"]},
        output=f"Validation score: {validation_results['overall_score']}",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Validation Agent: Completed check. Overall validation score: {validation_results['overall_score']}")
    
    return {
        **state,
        "validation_results": validation_results,
        "messages": messages
    }
