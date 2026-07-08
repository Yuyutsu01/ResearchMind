from typing import Dict, Any, List

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        # Maps task name -> agent instance
        self._task_mappings: Dict[str, Any] = {}
        # Maps event type -> list of agent instances subscribed
        self._event_subscriptions: Dict[str, List[Any]] = {}

    def register_agent(self, name: str, agent_instance: Any, tasks: List[str], event_subs: List[str]):
        """Dynamically registers an agent, its task capabilities, and event subscriptions."""
        self._agents[name] = agent_instance
        
        for task in tasks:
            self._task_mappings[task] = agent_instance
            print(f"[Agent Registry] Registered task '{task}' to Agent '{name}'")
            
        for event in event_subs:
            if event not in self._event_subscriptions:
                self._event_subscriptions[event] = []
            self._event_subscriptions[event].append(agent_instance)
            print(f"[Agent Registry] Subscribed Agent '{name}' to Event '{event}'")

    def get_agent_for_task(self, task_name: str) -> Any:
        """Returns the agent instance configured for the specified task."""
        return self._task_mappings.get(task_name)

    def get_agents_for_event(self, event_type: str) -> List[Any]:
        """Returns a list of agents subscribed to the specified event."""
        return self._event_subscriptions.get(event_type, [])

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

# Global Instance
agent_registry = AgentRegistry()
