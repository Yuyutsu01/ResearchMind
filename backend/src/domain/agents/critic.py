from typing import Dict, Any, List
from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.llm_adapter import llm_client
from src.domain.agents.registry import agent_registry

class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("Critic")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        claim_text = payload.get("claim_text")
        
        # Collate all gathered papers/methods context
        papers = blackboard.working_memory.get("retrieved_papers", [])
        context_text = "\n".join([
            f"Paper: {p['title']}\nAbstract: {p['abstract']}"
            for p in papers
        ])
        
        if not claim_text:
            # Check a default claim or formulate one from queries
            claim_text = f"Main assertion regarding: {blackboard.context.get('query', '')}"
            
        print(f"[Critic] Evaluating validity of claim: '{claim_text}'...")
        
        system_prompt = """You are a highly critical academic reviewer. Analyze the claim and the supporting literature context provided.
Identify if the claim is fully supported, has contradictory evidence, or is a potential hallucination (not present in source documents).
Rate the claim confidence from 0.0 to 1.0. If there are contradictions, explain them in detail.
Output ONLY a JSON object in the target structure. Do not wrap in markdown or output text other than JSON.

Target Structure:
{
  "confidence_score": 0.45,
  "status": "CONTRADICTED", // SUPPORTED, CONTRADICTED, WEAK_EVIDENCE, HALLUCINATION
  "critique": "Paper A claims 15x speedup, but Paper B lists a speedup of only 2.4x under similar setups.",
  "unresolved_contradiction": true
}
"""
        
        user_prompt = f"Claim to evaluate: {claim_text}\n\nLiterature Context:\n{context_text}"
        
        try:
            review = llm_client.get_structured_json(blackboard, system_prompt, user_prompt)
            
            # Find and update or add the claim in the blackboard
            claim_entry = None
            for c in blackboard.claims:
                if c["claim_text"] == claim_text:
                    claim_entry = c
                    break
                    
            if not claim_entry:
                claim_entry = {
                    "claim_text": claim_text,
                    "confidence_score": 0.5,
                    "evidence": [],
                    "status": "PROVISIONAL"
                }
                blackboard.claims.append(claim_entry)
                
            # Update fields based on Critic analysis
            old_score = claim_entry["confidence_score"]
            claim_entry["confidence_score"] = review.get("confidence_score", 0.5)
            claim_entry["status"] = review.get("status", "PROVISIONAL")
            claim_entry["evidence"].append({
                "critic_remark": review.get("critique", ""),
                "timestamp": review.get("timestamp", 0.0)
            })
            
            print(f"[Critic] Claim confidence adjusted: {old_score} ──> {claim_entry['confidence_score']} (Status: {claim_entry['status']})")
            
            # Publish critique events
            if review.get("unresolved_contradiction"):
                blackboard.add_event("CONTRADICTION_FOUND", {
                    "claim": claim_text,
                    "critique": review.get("critique"),
                    "msg": f"Critic found unresolved contradiction: {review.get('critique')}"
                })
                
            if claim_entry["confidence_score"] < 0.5:
                blackboard.add_event("LOW_CONFIDENCE", {
                    "claim": claim_text,
                    "score": claim_entry["confidence_score"],
                    "msg": f"Claim confidence fell to {claim_entry['confidence_score']}"
                })
                
        except Exception as e:
            print(f"[Critic Error] Critique failed: {e}")
            blackboard.add_event("CRITIQUE_FAILED", {
                "claim": claim_text,
                "error": str(e),
                "msg": f"Failed critique check: {str(e)}"
            })

# Register to Registry
critic_agent = CriticAgent()
agent_registry.register_agent(
    "Critic",
    critic_agent,
    tasks=["verify_claim"],
    event_subs=["PAPER_ANALYZED", "GRAPH_UPDATED"]
)
