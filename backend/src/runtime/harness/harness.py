"""
AI Harness Foundation Module for ResearchMind AI Runtime Architecture (Phase 1)

Centralized wrapper managing all LLM execution, prompt construction, context injection, 
token budgeting, cost tracking, and execution resilience. All LLM calls pass through the Harness.
"""

import time
import json
from typing import Dict, Any, Optional, Callable
from src.adapters.llm_adapter import llm_client
from src.adapters.telemetry import telemetry

class AIHarness:
    """
    Central execution harness surrounding LLM calls.
    Enforces token budgeting, prompt construction, context injection, and cost tracking.
    """
    
    # Token cost pricing table per 1,000 tokens (USD)
    COST_TABLE: Dict[str, Dict[str, float]] = {
        "groq": {"prompt": 0.0005, "completion": 0.0008},
        "openai": {"prompt": 0.0025, "completion": 0.0100},
        "mock": {"prompt": 0.0, "completion": 0.0}
    }

    def __init__(self):
        self.total_tokens_used: int = 0
        self.total_cost_usd: float = 0.0

    def execute(
        self,
        cache_key: str,
        system_prompt: str,
        user_prompt: str,
        session_id: int = 0,
        context_data: Optional[Dict[str, Any]] = None,
        max_token_budget: int = 4000
    ) -> Dict[str, Any]:
        """
        Executes an LLM call wrapped inside the Harness.
        Injects context data, tracks token budgets, and logs telemetry metrics.
        """
        t_start = time.time()

        # 1. Context Injection: Enrich prompt with SharedContext if provided
        enriched_user_prompt = user_prompt
        if context_data:
            ctx_str = json.dumps(context_data, indent=2)
            enriched_user_prompt = f"SHARED CONTEXT:\n{ctx_str}\n\nUSER PROMPT:\n{user_prompt}"

        # 2. Enforce Token Budgeting (Truncate prompt if exceeding token safety threshold)
        if len(enriched_user_prompt) > max_token_budget * 4:
            print(f"[AIHarness Warning] Prompt length ({len(enriched_user_prompt)}) exceeds budget limit ({max_token_budget * 4}). Truncating...")
            enriched_user_prompt = enriched_user_prompt[:max_token_budget * 4]

        # 3. LLM Execution via provider adapter
        result = llm_client.get_structured_json(
            cache_key=cache_key,
            system_prompt=system_prompt,
            user_prompt=enriched_user_prompt,
            session_id=session_id
        )

        # 4. Telemetry & Cost Tracking
        duration = time.time() - t_start
        est_prompt_tokens = len(enriched_user_prompt) // 4
        est_completion_tokens = len(json.dumps(result)) // 4
        
        self.total_tokens_used += (est_prompt_tokens + est_completion_tokens)
        pricing = self.COST_TABLE.get(llm_client.provider_name.lower(), self.COST_TABLE["mock"])
        call_cost = (est_prompt_tokens * pricing["prompt"] + est_completion_tokens * pricing["completion"]) / 1000.0
        self.total_cost_usd += call_cost

        print(f"[AIHarness] Execution successful ({duration:.3f}s) | Tokens: {est_prompt_tokens + est_completion_tokens} | Call Cost: ${call_cost:.6f}")
        return result

ai_harness = AIHarness()
