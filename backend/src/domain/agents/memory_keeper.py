from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.agents.registry import agent_registry

class MemoryKeeperAgent(BaseAgent):
    def __init__(self):
        super().__init__("MemoryKeeper")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        print(f"[Memory Keeper] Archiving session state and checkpoints to PostgreSQL database...")
        # Trigger autosave to postgres
        blackboard.save_to_db()
        
        blackboard.add_event("STATE_CHECKPOINTED", {
            "msg": "Research Blackboard checkpoint committed to PostgreSQL."
        })

# Register to Registry
memory_keeper_agent = MemoryKeeperAgent()
agent_registry.register_agent(
    "MemoryKeeper",
    memory_keeper_agent,
    tasks=["checkpoint_session", "archive_session"],
    event_subs=["PAPER_ANALYZED", "GRAPH_UPDATED", "STATE_TRANSITION"]
)
