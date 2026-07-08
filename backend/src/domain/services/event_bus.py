import asyncio
from typing import Dict, Any
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.agents.registry import agent_registry
from src.domain.scheduler.scheduler import TaskScheduler

class EventBus:
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler

    async def publish_event(self, blackboard: ResearchBlackboard, event_type: str, details: Dict[str, Any]):
        """Publishes an event and schedules task activations for registered subscriber agents."""
        # 1. Log event on Blackboard
        blackboard.add_event(event_type, details)
        
        # 2. Get interested agents
        subscribers = agent_registry.get_agents_for_event(event_type)
        
        # 3. Schedule agent execution tasks via priority queue
        for agent in subscribers:
            # Map events to concrete agent tasks
            task_name = self._map_event_to_task(event_type, agent.name)
            if task_name:
                self.scheduler.schedule_task(
                    blackboard=blackboard,
                    task_name=task_name,
                    priority=5, # Event-triggered actions have baseline priority
                    payload={
                        "event_type": event_type,
                        "details": details,
                        "paper_title": details.get("paper_title")
                    }
                )

    def _map_event_to_task(self, event_type: str, agent_name: str) -> str:
        """Determines the mapped task name based on event trigger and agent capability."""
        mappings = {
            ("NEW_PAPER_FOUND", "Analyst"): "analyze_paper",
            ("PAPER_ANALYZED", "Critic"): "verify_claim",
            ("PAPER_ANALYZED", "Synthesizer"): "synthesize_knowledge",
            ("GRAPH_UPDATED", "MemoryKeeper"): "checkpoint_session",
            ("STATE_TRANSITION", "MemoryKeeper"): "checkpoint_session"
        }
        return mappings.get((event_type, agent_name))
