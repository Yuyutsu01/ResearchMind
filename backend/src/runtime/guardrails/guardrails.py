"""
Guardrail Layer Module for ResearchMind AI Runtime Architecture (Phase 1)

Executes multi-stage safety and validation checks:
- Pre-LLM: Detects prompt injection in PDFs, sanitizes system prompts.
- Post-LLM: Verifies citations against database metadata, flags hallucinations.
- Pre-UI: Validates JSON schema integrity.
"""

import re
from typing import Dict, Any, List, Optional
from src.adapters.db.postgres import execute_query

class GuardrailEngine:
    """
    Multi-stage Guardrail Engine running safety and grounding checks.
    """

    PROMPT_INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"disregard (the )?above",
        r"system prompt",
        r"you are now an? unrestricted",
        r"print (the )?api key",
        r"reveal secret"
    ]

    def validate_pre_llm(self, text: str) -> Dict[str, Any]:
        """
        Pre-LLM Guard: Detects prompt injection patterns inside PDF text selections.
        """
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[Guardrail Warning] Pre-LLM prompt injection pattern detected: '{pattern}'")
                return {
                    "is_safe": False,
                    "reason": f"Prompt injection attempt detected: '{pattern}'",
                    "sanitized_text": "[Content removed by Guardrail Engine for safety]"
                }
        return {"is_safe": True, "reason": None, "sanitized_text": text}

    def validate_post_llm(self, session_id: int, agent_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-LLM Guard: Verifies citation references and checks grounding integrity.
        """
        is_grounded = True
        warnings = []

        # Check citations if present in output
        citations = agent_output.get("citation_references") or []
        for cit_id in citations:
            try:
                rows = execute_query(
                    "SELECT id FROM paper_objects WHERE session_id = %s AND id = %s;",
                    (session_id, cit_id),
                    fetch=True
                )
                if not rows:
                    is_grounded = False
                    warnings.append(f"Unverified citation ID detected: '{cit_id}'")
            except Exception:
                pass

        return {
            "is_grounded": is_grounded,
            "warnings": warnings,
            "validated_output": agent_output
        }

    def validate_pre_ui(self, response_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-UI Guard: Enforces response payload structural schema integrity before UI render.
        """
        if not isinstance(response_payload, dict):
            return {"valid": False, "error": "Response payload must be a JSON object"}
        if "composer" not in response_payload and "explanation" not in response_payload:
            return {"valid": False, "error": "Response payload missing composer/explanation block"}
        return {"valid": True, "error": None}

guardrails = GuardrailEngine()
