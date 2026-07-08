from typing import Dict, Any
from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.llm_adapter import llm_client
from src.domain.agents.registry import agent_registry

class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analyst")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        paper_title = payload.get("paper_title")
        
        # Find paper abstract or text in working memory
        papers = blackboard.working_memory.get("retrieved_papers", [])
        selected_paper = None
        for p in papers:
            if p["title"] == paper_title:
                selected_paper = p
                break
                
        if not selected_paper:
            # Fallback to general context
            text_to_analyze = blackboard.context.get("query", "")
            paper_title = "User Input Context"
        else:
            text_to_analyze = f"Title: {selected_paper['title']}\nAbstract: {selected_paper['abstract']}"
            
        print(f"[Analyst] Parsing paper '{paper_title}' for technical details...")
        
        system_prompt = """You are an expert scientific analyst. Extract the top core concepts, methods, equations, and experiments from the research paper text.
Generate a valid JSON object matching the target structure. Do not wrap in markdown or output text other than JSON.

Target Structure:
{
  "concepts": [
    {
      "name": "Self-Attention",
      "definition": "Relates different positions of a single sequence to compute a representation.",
      "formula": "Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V"
    }
  ],
  "methods": [
    {
      "name": "Transformer Encoder",
      "description": "Stack of encoder layers that map inputs to high-dimensional vectors.",
      "implements_concept": "Self-Attention"
    }
  ],
  "experiments": [
    {
      "dataset": "WMT 2014 English-German",
      "metric": "BLEU score",
      "performance": "28.4"
    }
  ]
}
"""
        
        user_prompt = f"Paper Text:\n{text_to_analyze}"
        
        try:
            extracted = llm_client.get_structured_json(blackboard, system_prompt, user_prompt)
            
            # Populate NetworkX Knowledge Graph in Working Memory
            # Add paper node
            blackboard.knowledge_graph.add_node(paper_title, type="paper", label=paper_title)
            
            # Process extracted concepts
            for concept in extracted.get("concepts", []):
                name = concept.get("name", "").strip()
                if not name:
                    continue
                blackboard.knowledge_graph.add_node(
                    name,
                    type="concept",
                    label=name,
                    definition=concept.get("definition", ""),
                    math_formula=concept.get("formula", "")
                )
                blackboard.knowledge_graph.add_edge(paper_title, name, relationship="defines")
                
            # Process extracted methods
            for method in extracted.get("methods", []):
                name = method.get("name", "").strip()
                if not name:
                    continue
                blackboard.knowledge_graph.add_node(
                    name,
                    type="method",
                    label=name,
                    description=method.get("description", "")
                )
                blackboard.knowledge_graph.add_edge(paper_title, name, relationship="introduces")
                
                # Link to concept if implements
                imp_concept = method.get("implements_concept", "").strip()
                if imp_concept and blackboard.knowledge_graph.has_node(imp_concept):
                    blackboard.knowledge_graph.add_edge(name, imp_concept, relationship="implements")

            # Process extracted experiments
            for exp in extracted.get("experiments", []):
                dataset = exp.get("dataset", "").strip()
                if not dataset:
                    continue
                blackboard.knowledge_graph.add_node(
                    dataset,
                    type="dataset",
                    label=dataset
                )
                blackboard.knowledge_graph.add_edge(
                    paper_title, 
                    dataset, 
                    relationship="evaluates_on",
                    metric=exp.get("metric", ""),
                    performance=exp.get("performance", "")
                )
                
            # Publish event
            blackboard.add_event("PAPER_ANALYZED", {
                "paper_title": paper_title,
                "extracted_concepts": [c.get("name") for c in extracted.get("concepts", [])],
                "msg": f"Analyzed paper '{paper_title}' successfully."
            })
            
        except Exception as e:
            print(f"[Analyst Error] Analysis of '{paper_title}' failed: {e}")
            blackboard.add_event("ANALYSIS_FAILED", {
                "paper_title": paper_title,
                "error": str(e),
                "msg": f"Failed to analyze '{paper_title}': {str(e)}"
            })

# Register to Registry
analyst_agent = AnalystAgent()
agent_registry.register_agent(
    "Analyst",
    analyst_agent,
    tasks=["analyze_paper"],
    event_subs=["NEW_PAPER_FOUND"]
)
