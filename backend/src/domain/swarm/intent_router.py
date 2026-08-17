"""
Intent Router Module for ResearchMind Swarm Architecture (Phase 1)

Analyzes user selection metadata and target type to determine the minimal 
set of specialized agents required for processing, eliminating redundant LLM calls.
"""

from typing import List, Dict, Any

class IntentRouter:
    """
    Selectively routes selection payloads to required sub-agents based on content type.
    """
    
    # Pre-defined required agent mappings by selection category
    ROUTE_MAP: Dict[str, List[str]] = {
        "text": ["explanation", "background", "questions"],
        "paragraph": ["explanation", "background", "questions"],
        "equation": ["math", "background", "questions"],
        "math": ["math", "background", "questions"],
        "figure": ["figure", "visual", "background"],
        "table": ["table", "questions", "background"],
        "citation": ["citation", "terminology"],
        "reference": ["citation", "terminology"]
    }

    def route_intent(self, selection_type: str, selection_text: str, custom_prompt: str = None) -> List[str]:
        """
        Determines minimal set of agent names required for processing.
        """
        s_type = (selection_type or "text").lower().strip()
        
        # Check if custom prompt requests specific analysis (e.g. math or visual)
        if custom_prompt:
            lower_prompt = custom_prompt.lower()
            if "math" in lower_prompt or "equation" in lower_prompt or "derive" in lower_prompt:
                return ["math", "background", "questions"]
            if "figure" in lower_prompt or "diagram" in lower_prompt or "visual" in lower_prompt:
                return ["figure", "visual", "background"]
            if "cite" in lower_prompt or "reference" in lower_prompt:
                return ["citation", "terminology"]

        # Default mapping lookup
        agents = self.ROUTE_MAP.get(s_type, ["explanation", "background", "questions"])
        
        print(f"[IntentRouter] Selection type '{selection_type}' routed to minimal agent set: {agents}")
        return agents

    def route_followup_intent(self, question: str) -> List[str]:
        """
        Classifies user follow-up questions to activate only required sub-agents.
        """
        q = (question or "").lower()
        if "math" in q or "equation" in q or "derive" in q or "formula" in q:
            return ["math"]
        elif "background" in q or "prereq" in q or "concept" in q or "history" in q:
            return ["background"]
        elif "diagram" in q or "visual" in q or "flowchart" in q:
            return ["visual"]
        elif "cite" in q or "reference" in q or "paper" in q:
            return ["citation"]
        elif "term" in q or "definition" in q or "meaning" in q:
            return ["terminology"]
        else:
            return ["explanation"]

intent_router = IntentRouter()
