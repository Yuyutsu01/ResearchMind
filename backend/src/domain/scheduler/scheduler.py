import time
from typing import Dict, Any, List
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.config.app_config import Config

class BudgetExceededException(Exception):
    pass

class BudgetManager:
    @staticmethod
    def record_llm_call(blackboard: ResearchBlackboard, prompt_tokens: int, completion_tokens: int):
        """Records token usage and calculates estimated USD cost."""
        # Standard pricing: Llama3 equivalent pricing ($0.0005 / 1k input, $0.0015 / 1k output)
        input_cost = (prompt_tokens / 1000) * 0.0005
        output_cost = (completion_tokens / 1000) * 0.0015
        total_cost = input_cost + output_cost
        
        blackboard.budget["tokens_used"] += (prompt_tokens + completion_tokens)
        blackboard.budget["cost_usd"] += total_cost
        blackboard.budget["api_calls"] += 1
        
        # Enforce budget limits
        if blackboard.budget["tokens_used"] > Config.MAX_TOKENS_PER_SESSION:
            raise BudgetExceededException("Token usage limit exceeded for this session.")
        if blackboard.budget["cost_usd"] > Config.MAX_DOLLARS_PER_SESSION:
            raise BudgetExceededException("Dollar cost limit exceeded for this session.")
        if blackboard.budget["api_calls"] > Config.MAX_API_CALLS_PER_SESSION:
            raise BudgetExceededException("API call count limit exceeded for this session.")

    @staticmethod
    def check_budget(blackboard: ResearchBlackboard) -> bool:
        """Returns True if session is within budget limits, False otherwise."""
        return (
            blackboard.budget["tokens_used"] <= Config.MAX_TOKENS_PER_SESSION and
            blackboard.budget["cost_usd"] <= Config.MAX_DOLLARS_PER_SESSION and
            blackboard.budget["api_calls"] <= Config.MAX_API_CALLS_PER_SESSION
        )


class ResearchStateMachine:
    VALID_STATES = {"IDLE", "SEARCHING", "READING", "VERIFYING", "SYNTHESIZING", "QUESTIONING_USER", "COMPLETE"}

    @staticmethod
    def transition_to(blackboard: ResearchBlackboard, new_state: str, event_bus_stream=None):
        """Manages transitions of the State Machine and notifies the active event stream."""
        if new_state not in ResearchStateMachine.VALID_STATES:
            print(f"[State Machine Error] Invalid state: {new_state}")
            return
            
        old_state = blackboard.session_state
        if old_state == new_state:
            return
            
        blackboard.session_state = new_state
        print(f"[State Machine] Session #{blackboard.session_id}: {old_state} ──> {new_state}")
        
        # Log to blackboard event log
        blackboard.add_event("STATE_TRANSITION", {
            "from_state": old_state,
            "to_state": new_state,
            "msg": f"Platform state changed to {new_state}"
        })
        
        # If active WebSocket is attached, stream transition
        if event_bus_stream:
            event_bus_stream(new_state)


class TaskScheduler:
    def __init__(self, agent_registry):
        self.agent_registry = agent_registry

    def schedule_task(self, blackboard: ResearchBlackboard, task_name: str, priority: int, payload: Dict[str, Any]):
        """Pushes a task into the Blackboard's active task queue, keeping it sorted by priority."""
        task = {
            "name": task_name,
            "priority": priority,
            "payload": payload,
            "created_at": time.time(),
            "status": "PENDING"
        }
        blackboard.active_tasks.append(task)
        # Sort task queue by priority (highest priority first)
        blackboard.active_tasks.sort(key=lambda x: x["priority"], reverse=True)
        print(f"[Scheduler] Scheduled task '{task_name}' with priority {priority}.")

    def execute_next_task(self, blackboard: ResearchBlackboard) -> bool:
        """Pops and executes the highest-priority pending task from the queue."""
        pending = [t for t in blackboard.active_tasks if t["status"] == "PENDING"]
        if not pending:
            return False
            
        task = pending[0]
        task["status"] = "RUNNING"
        
        task_name = task["name"]
        payload = task["payload"]
        print(f"[Scheduler] Executing task '{task_name}'...")
        
        # Resolve task_name to registered agents via Agent Registry
        # Example mapping: "search_literature" -> Explorer Agent
        agent = self.agent_registry.get_agent_for_task(task_name)
        if not agent:
            print(f"[Scheduler Error] No registered agent for task: {task_name}")
            task["status"] = "FAILED"
            return False
            
        try:
            # Enforce budget before executing
            if not BudgetManager.check_budget(blackboard):
                raise BudgetExceededException("Encountered budget block before executing task.")
                
            agent.execute(blackboard, payload)
            task["status"] = "COMPLETED"
            
            # Remove completed task from active_tasks list
            blackboard.active_tasks.remove(task)
            return True
        except BudgetExceededException as be:
            print(f"[Scheduler Budget Warning] {be}")
            task["status"] = "FAILED"
            ResearchStateMachine.transition_to(blackboard, "COMPLETE")
            return False
        except Exception as e:
            print(f"[Scheduler Error] Task '{task_name}' execution failed: {e}")
            task["status"] = "FAILED"
            return False
