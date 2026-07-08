import pytest
from unittest.mock import MagicMock, patch
import networkx as nx

# Mock postgres queries to avoid DB dependency in unit tests
@pytest.fixture(autouse=True)
def mock_db():
    with patch("src.domain.blackboard.blackboard.execute_query") as mock:
        mock.return_value = []
        yield mock

from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.scheduler.scheduler import TaskScheduler, BudgetManager, ResearchStateMachine, BudgetExceededException
from src.domain.agents.registry import AgentRegistry

def test_task_scheduler_priority():
    """Verifies that TaskScheduler correctly prioritizes tasks by score."""
    registry = AgentRegistry()
    scheduler = TaskScheduler(registry)
    blackboard = ResearchBlackboard(session_id=99)
    
    # Schedule three tasks with different priorities
    scheduler.schedule_task(blackboard, "analyze_paper", priority=5, payload={})
    scheduler.schedule_task(blackboard, "verify_claim", priority=10, payload={})
    scheduler.schedule_task(blackboard, "discover_papers", priority=1, payload={})
    
    # Assert sorted order in queue (highest priority first)
    assert blackboard.active_tasks[0]["name"] == "verify_claim"
    assert blackboard.active_tasks[1]["name"] == "analyze_paper"
    assert blackboard.active_tasks[2]["name"] == "discover_papers"

def test_budget_manager_enforcements():
    """Verifies that BudgetManager correctly calculates cost and raises budget limit warnings."""
    blackboard = ResearchBlackboard(session_id=99)
    
    # Verify initial state
    assert blackboard.budget["tokens_used"] == 0
    assert blackboard.budget["cost_usd"] == 0.0
    
    # Record standard LLM call
    BudgetManager.record_llm_call(blackboard, prompt_tokens=1000, completion_tokens=2000)
    assert blackboard.budget["tokens_used"] == 3000
    # prompt cost: (1000/1000)*0.0005 = 0.0005. completion cost: (2000/1000)*0.0015 = 0.003
    assert blackboard.budget["cost_usd"] == 0.0035
    
    # Trigger limit breach
    with pytest.raises(BudgetExceededException):
        # Exceed dollar limit ($10.00 max)
        BudgetManager.record_llm_call(blackboard, prompt_tokens=10000000, completion_tokens=10000000)

def test_state_machine_transitions():
    """Verifies ResearchStateMachine transitions states and adds state transition events."""
    blackboard = ResearchBlackboard(session_id=99)
    assert blackboard.session_state == "IDLE"
    
    # Transition to SEARCHING
    ResearchStateMachine.transition_to(blackboard, "SEARCHING")
    assert blackboard.session_state == "SEARCHING"
    
    # Verify transition event is logged
    transitions = [e for e in blackboard.event_queue if e["type"] == "STATE_TRANSITION"]
    assert len(transitions) == 1
    assert transitions[0]["details"]["to_state"] == "SEARCHING"
