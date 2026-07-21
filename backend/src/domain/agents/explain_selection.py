import json
from typing import Dict, Any
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.llm_adapter import llm_client
from src.adapters.db.qdrant import semantic_memory
from src.adapters.db.postgres import execute_query

def explain_selection(blackboard: ResearchBlackboard, selection_text: str, selection_type: str, obj_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Orchestrates the dynamic multi-agent analysis for user highlights, compiling progressive
    explanations (levels 1-7), 'Why This Matters' metrics, and logging events to the timeline.
    """
    print(f"[Selection Service] Explaining '{selection_text}' ({selection_type}) for Session #{blackboard.session_id}...")
    
    # 1. Retrieve local context chunks from Qdrant if available
    context_chunks = []
    if semantic_memory:
        context_chunks = semantic_memory.search(blackboard.session_id, selection_text, top_k=3)
        
    context_text = "\n".join([f"Context: {c['text']}" for c in context_chunks])
    
    meta_prompt = ""
    if obj_metadata:
        meta_prompt = f"""
Semantic Object Layout:
- Object ID: {obj_metadata.get('id')}
- Target Type: {obj_metadata.get('type')}
- Page Number: Page {obj_metadata.get('page')}
- Parent Block: {obj_metadata.get('parent_id')}
- Bounding Box Coordinates: {obj_metadata.get('bounding_box')}
- Related Objects Connections: {obj_metadata.get('relationships')}
- Object Attribute Details: {obj_metadata.get('metadata')}
"""
    
    # 2. Build multi-agent critique and explanation prompt
    system_prompt = """You are an elite research mentor and senior scientist.
Analyze the provided scientific context and the specific highlight.
Explain the highlight by generating a structured JSON. 

Format all mathematical equations in clean LaTeX notation (use $ for inline math like $O(d)$ and $$ for block math equations).
If the selection is a method or code segment, write clean Python/PyTorch pseudocode under level_6.

Target JSON Structure:
{
  "level_1": "One sentence intuition summarizing this concept.",
  "level_2": "One paragraph breakdown of its core mechanics.",
  "level_3": "Detailed explanation of meaning, context, and fundamental assumptions.",
  "level_4": "Mathematical explanation, variable definitions, and step-by-step derivations (if applicable).",
  "level_5": "Historical evolution (how the field arrived at this concept and what came before it).",
  "level_6": "Implementation details (algorithmic steps, PyTorch pseudocode, or common software mistakes).",
  "level_7": "List of 2-3 key related papers/citations with titles and brief relevance.",
  "why_this_matters": {
    "author_intent": "Why the authors included this specific concept/equation/design choice in the paper.",
    "problem_solved": "What exact limitation or problem this specific item solves.",
    "later_dependents": "Which later mathematical equations, theorems, or sections in the paper build on this.",
    "prerequisites": "Prerequisite mathematical or conceptual knowledge required to understand this."
  },
  "critic_warning": "Weaknesses, limitations, controversial assumptions, or common misunderstandings surrounding this topic."
}
"""
    user_prompt = f"""
Research Query Context: {blackboard.context.get("query", "")}
Supporting Paper Snippets:
{context_text}
{meta_prompt}
Highlight/Selected Item: "{selection_text}"
Type of Highlight: {selection_type}
"""

    try:
        explanation = llm_client.get_structured_json(blackboard, system_prompt, user_prompt)
    except Exception as e:
        print(f"[Selection Service Error] LLM generation failed: {e}")
        explanation = {
            "level_1": f"Selected {selection_type}: {selection_text}",
            "level_2": "An explanation could not be generated due to an LLM error.",
            "level_3": str(e),
            "level_4": "N/A",
            "level_5": "N/A",
            "level_6": "N/A",
            "level_7": "N/A",
            "why_this_matters": {
                "author_intent": "Error in LLM evaluation.",
                "problem_solved": "N/A",
                "later_dependents": "N/A",
                "prerequisites": "N/A"
            },
            "critic_warning": "N/A"
        }

    # 3. Log highlight selection to Reading Timeline in PostgreSQL
    try:
        execute_query(
            "INSERT INTO reading_timeline (session_id, action_type, details) VALUES (%s, 'TEXT_SELECTED', %s);",
            (
                blackboard.session_id,
                json.dumps({
                    "text": selection_text,
                    "type": selection_type,
                    "summary": explanation.get("level_1", "")
                })
            )
        )
    except Exception as dbe:
        print(f"[Selection Service DB Error] Failed to log selection to timeline: {dbe}")

    # 4. Dynamically update Knowledge Graph if a prominent concept is discovered
    if selection_type in ("TECHNICAL_TERM", "METHOD_SELECTED", "CONCEPT_SELECTED", "CITATION_SELECTED"):
        node_id = selection_text.strip().replace(" ", "_").lower()
        if not blackboard.knowledge_graph.has_node(node_id):
            blackboard.knowledge_graph.add_node(
                node_id,
                label=selection_text,
                type="concept",
                confidence=0.8,
                details=explanation.get("level_1", "")
            )
            blackboard.add_event("GRAPH_UPDATED", {"msg": f"Added selected concept '{selection_text}' to Knowledge Graph."})
            blackboard.save_to_db()

    return explanation
