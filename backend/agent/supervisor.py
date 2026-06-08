import os
import sys
import time
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.rl.policy_engine import policy_engine
from agent.rl.reward_engine import calculate_reward
from agent.rl.experience_store import save_transition

# Define the shared Graph State
class AgentState(TypedDict):
    query: str
    has_pdf: bool
    pdf_path: str
    paper_metadata: Dict[str, Any]
    retrieved_papers: List[Dict[str, Any]]
    external_context: List[str]
    sections: Dict[str, str]
    validation_results: Dict[str, Any]
    reports: Dict[str, str]
    errors: List[str]
    messages: List[str]
    rl_actions: Dict[str, int]
    task_id: int
    duration_ms: float

# Let's import agent nodes
# To prevent circular imports, we will import them dynamically or write their nodes directly in supervisor.py or their respective modules.
# We will write the supervisor graph structure here.

def create_supervisor_graph():
    workflow = StateGraph(AgentState)
    
    # 1. Define nodes
    from agent.document_agent import document_node
    from agent.retrieval_agent import retrieval_node
    from agent.expansion_agent import expansion_node
    from agent.validator import validation_node
    from agent.report_agent import report_node
    from agent.concept_explorer import concept_node
    from agent.gap_detector import gap_detector_node
    
    workflow.add_node("document_analysis", document_node)
    workflow.add_node("concept_extraction", concept_node)
    workflow.add_node("research_retrieval", retrieval_node)
    workflow.add_node("knowledge_expansion", expansion_node)
    workflow.add_node("gap_detection", gap_detector_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("report_generation", report_node)
    
    # 2. Define routing logic
    def route_start(state: AgentState):
        if state.get("pdf_path") and os.path.exists(state.get("pdf_path")):
            return "document_analysis"
        else:
            return "research_retrieval"
            
    def route_after_document(state: AgentState):
        return "concept_extraction"
        
    def route_after_concept(state: AgentState):
        return "research_retrieval"
        
    def route_after_retrieval(state: AgentState):
        return "knowledge_expansion"
        
    def route_after_expansion(state: AgentState):
        return "gap_detection"
        
    def route_after_gap(state: AgentState):
        return "validation"
        
    def route_after_validation(state: AgentState):
        return "report_generation"
        
    # Set conditional entry point
    workflow.set_conditional_entry_point(
        route_start,
        {
            "document_analysis": "document_analysis",
            "research_retrieval": "research_retrieval"
        }
    )
    
    # Add regular connections
    workflow.add_conditional_edges(
        "document_analysis",
        route_after_document,
        {"concept_extraction": "concept_extraction"}
    )
    
    workflow.add_conditional_edges(
        "concept_extraction",
        route_after_concept,
        {"research_retrieval": "research_retrieval"}
    )
    
    workflow.add_conditional_edges(
        "research_retrieval",
        route_after_retrieval,
        {"knowledge_expansion": "knowledge_expansion"}
    )
    
    workflow.add_conditional_edges(
        "knowledge_expansion",
        route_after_expansion,
        {"gap_detection": "gap_detection"}
    )
    
    workflow.add_conditional_edges(
        "gap_detection",
        route_after_gap,
        {"validation": "validation"}
    )
    
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {"report_generation": "report_generation"}
    )
    
    workflow.add_edge("report_generation", END)
    
    return workflow.compile()

# Helper to run the graph and record experience
def run_research_workflow(query: str, pdf_path: str = None, task_id: int = 0) -> dict:
    start_time = time.time()
    
    # Initialize state
    has_pdf = pdf_path is not None and os.path.exists(pdf_path)
    state_key = policy_engine.get_state_key(query, has_pdf)
    
    # Select RL actions
    source_action = policy_engine.choose_action(state_key, "source_selection")
    retrieval_action = policy_engine.choose_action(state_key, "retrieval_strategy")
    expansion_action = policy_engine.choose_action(state_key, "expansion_depth")
    
    rl_actions = {
        "source_selection": source_action,
        "retrieval_strategy": retrieval_action,
        "expansion_depth": expansion_action
    }
    
    initial_state: AgentState = {
        "query": query,
        "has_pdf": has_pdf,
        "pdf_path": pdf_path or "",
        "paper_metadata": {},
        "retrieved_papers": [],
        "external_context": [],
        "sections": {},
        "validation_results": {},
        "reports": {},
        "errors": [],
        "messages": [f"Starting workflow with RL actions: {rl_actions}"],
        "rl_actions": rl_actions,
        "task_id": task_id,
        "duration_ms": 0.0
    }
    
    app_graph = create_supervisor_graph()
    print("[Supervisor] Executing Research State Graph...")
    
    final_state = app_graph.invoke(initial_state)
    
    # Calculate rewards and log transition
    duration_ms = (time.time() - start_time) * 1000.0
    final_state["duration_ms"] = duration_ms
    
    val_score = final_state.get("validation_results", {}).get("citation_check", {}).get("score", 0.8)
    cit_score = final_state.get("validation_results", {}).get("citation_check", {}).get("score", 0.8)
    
    reward = calculate_reward(
        validation_score=val_score,
        citation_score=cit_score,
        duration_ms=duration_ms,
        user_feedback=0.9  # Simulated/standard feedback
    )
    
    # Transition states for RL Replay
    state_repr = {"query": query, "has_pdf": has_pdf}
    next_state_repr = {"query": query, "has_pdf": has_pdf, "success": val_score > 0.6}
    
    save_transition(state_repr, rl_actions, reward, next_state_repr)
    
    return final_state
