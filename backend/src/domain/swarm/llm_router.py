"""
LLM Router Module for ResearchMind Swarm Architecture (Phase 8)

Routes agent requests to specific model tiers based on task complexity:
- FAST: Instant model for basic summaries, intent routing, terminology (e.g. llama-3.1-8b-instant, gpt-4o-mini).
- REASONING: High-capability model for math derivations, proofs, synthesis (e.g. llama-3.3-70b-versatile, gpt-4o).
- VISION: Multimodal vision model for figure/diagram interpretation.
"""

import os
from typing import Dict, Any

class LLMRouter:
    """
    Selects optimal model tier for agent tasks to balance speed and capability.
    """
    
    TIER_MODELS: Dict[str, str] = {
        "FAST": os.environ.get("MODEL_FAST", "llama-3.1-8b-instant"),
        "REASONING": os.environ.get("MODEL_REASONING", "llama-3.3-70b-versatile"),
        "VISION": os.environ.get("MODEL_VISION", "llama-3.2-11b-vision-instruct")
    }

    AGENT_TIER_MAPPING: Dict[str, str] = {
        "explanation": "REASONING",
        "math": "REASONING",
        "background": "FAST",
        "visual": "FAST",
        "figure": "VISION",
        "table": "REASONING",
        "citation": "FAST",
        "terminology": "FAST",
        "questions": "FAST"
    }

    def get_model_for_agent(self, agent_name: str) -> str:
        """
        Returns model string for a given agent name based on task complexity.
        """
        tier = self.AGENT_TIER_MAPPING.get(agent_name.lower(), "REASONING")
        model = self.TIER_MODELS.get(tier, self.TIER_MODELS["REASONING"])
        print(f"[LLMRouter] Agent '{agent_name}' mapped to Tier '{tier}' -> Model '{model}'")
        return model

llm_router = LLMRouter()
