from abc import ABC, abstractmethod
from src.domain.blackboard.blackboard import ResearchBlackboard

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        """Runs the main cognitive routine of the agent using the shared Blackboard."""
        pass
