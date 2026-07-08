from typing import Dict, Any, List
from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.llm_adapter import llm_client
from src.domain.agents.registry import agent_registry

class SynthesizerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Synthesizer")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        print("[Synthesizer] Synthesizing literature and consolidating Knowledge Graph...")
        
        # 1. Clean and merge graph node representations
        self._consolidate_graph(blackboard)
        
        # 2. Formulate hypothesis or synthesis report via LLM
        query = blackboard.context.get("query", "")
        papers = blackboard.working_memory.get("retrieved_papers", [])
        
        # Collate paper details
        papers_context = ""
        for p in papers:
            papers_context += f"\nTitle: {p['title']}\nAbstract: {p['abstract']}\n"
            
        system_prompt = """You are a senior research scientist. Review the literature contexts below.
Synthesize a unified research narrative for the query, listing the problem context, common methods, experimental achievements, and future directions.
Output ONLY a JSON object matching the target structure. Do not wrap in markdown or output text other than JSON.

Target Structure:
{
  "narrative": "A complete, detailed markdown analysis of the literature (3-5 paragraphs)...",
  "comparison_table": [
    {
      "method": "FlashAttention",
      "speedup": "2-4x",
      "memory_efficiency": "O(N) instead of O(N^2)"
    }
  ],
  "proposed_hypothesis": "A novel hypothesis generated from combining these works..."
}
"""
        
        user_prompt = f"Query: {query}\n\nRetrieved Papers:\n{papers_context}"
        
        try:
            synthesis = llm_client.get_structured_json(blackboard, system_prompt, user_prompt)
            
            # Write results back to Working Memory
            blackboard.working_memory["report_synthesis"] = synthesis.get("narrative", "")
            blackboard.working_memory["comparison_table"] = synthesis.get("comparison_table", [])
            
            # Save proposed hypothesis
            hyp_text = synthesis.get("proposed_hypothesis", "")
            if hyp_text:
                hyp_entry = {
                    "hypothesis_text": hyp_text,
                    "status": "ACTIVE",
                    "evidence": []
                }
                blackboard.hypotheses.append(hyp_entry)
                print(f"[Synthesizer] Formulated new hypothesis: '{hyp_text}'")
                
            # Publish connection/synthesis events
            blackboard.add_event("GRAPH_UPDATED", {
                "nodes_count": len(blackboard.knowledge_graph),
                "edges_count": blackboard.knowledge_graph.number_of_edges(),
                "msg": f"Knowledge Graph consolidated: {len(blackboard.knowledge_graph)} nodes, {blackboard.knowledge_graph.number_of_edges()} edges."
            })
            
            blackboard.add_event("NEW_CONNECTION", {
                "hypothesis": hyp_text,
                "msg": "Synthesizer established novel concept connection."
            })
            
        except Exception as e:
            print(f"[Synthesizer Error] Synthesis failed: {e}")
            blackboard.add_event("SYNTHESIS_FAILED", {
                "error": str(e),
                "msg": f"Failed synthesis pipeline: {str(e)}"
            })

    def _consolidate_graph(self, blackboard: ResearchBlackboard):
        """Simplifies the NetworkX graph in RAM by removing duplicate nodes and isolated concepts."""
        # For simplicity in this v1 prototype, we remove duplicate labels
        # and ensure every node has basic styling properties for cytoscape visualization
        nodes = list(blackboard.knowledge_graph.nodes)
        for node in nodes:
            attrs = blackboard.knowledge_graph.nodes[node]
            if "label" not in attrs:
                blackboard.knowledge_graph.nodes[node]["label"] = node
            if "type" not in attrs:
                blackboard.knowledge_graph.nodes[node]["type"] = "concept"
                
        print(f"[Synthesizer Graph Clean] NetworkX size: {len(blackboard.knowledge_graph.nodes)} nodes.")

# Register to Registry
synthesizer_agent = SynthesizerAgent()
agent_registry.register_agent(
    "Synthesizer",
    synthesizer_agent,
    tasks=["synthesize_knowledge", "consolidate_graph"],
    event_subs=["PAPER_ANALYZED", "CONTRADICTION_FOUND"]
)
