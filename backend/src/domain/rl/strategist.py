import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.scheduler.scheduler import ResearchStateMachine, TaskScheduler
from src.domain.agents.registry import agent_registry

MODEL_PATH = "ppo_strategist_model"

class ResearchMindEnv(gym.Env):
    """
    Custom Gym Environment simulating research transitions.
    Allows Stable-Baselines3 PPO to learn optimal agent execution scheduling.
    """
    def __init__(self):
        super().__init__()
        # State: [Concepts/20, Papers/10, Contradictions/5, Avg_Confidence, Budget_Spent]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(5,), dtype=np.float32
        )
        # Action space:
        # 0: SEARCH_PAPERS, 1: ANALYZE_PAPER, 2: VERIFY_CLAIM, 3: CONNECT_CONCEPTS, 4: CLARIFY_USER, 5: TERMINATE
        self.action_space = spaces.Discrete(6)
        
        self.state = np.zeros(5, dtype=np.float32)
        self.steps = 0
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([0.0, 0.0, 0.0, 0.5, 0.0], dtype=np.float32)
        self.steps = 0
        return self.state, {}
        
    def step(self, action):
        self.steps += 1
        
        # Heuristic state updates simulating environment response to actions
        if action == 0:  # Search papers
            self.state[1] = min(1.0, self.state[1] + 0.3)  # found papers
            self.state[4] = min(1.0, self.state[4] + 0.1)  # spent budget
        elif action == 1:  # Analyze
            self.state[0] = min(1.0, self.state[0] + 0.25) # found concepts
            self.state[4] = min(1.0, self.state[4] + 0.08)
        elif action == 2:  # Verify
            self.state[2] = max(0.0, self.state[2] - 0.2)  # resolved contradictions
            self.state[3] = min(1.0, self.state[3] + 0.15) # higher confidence
            self.state[4] = min(1.0, self.state[4] + 0.05)
        elif action == 3:  # Connect
            self.state[0] = min(1.0, self.state[0] + 0.1)
            self.state[4] = min(1.0, self.state[4] + 0.05)
        elif action == 4:  # Clarification
            self.state[3] = min(1.0, self.state[3] + 0.1)
            
        # Calculate Reward
        # High confidence, high concept count, low contradictions, within budget
        reward = (self.state[0] * 0.4) + (self.state[3] * 0.4) - (self.state[2] * 0.3) - (self.state[4] * 0.2)
        
        terminated = action == 5 or self.steps >= 15
        truncated = False
        
        return self.state, float(reward), terminated, truncated, {}


class RLStrategist:
    def __init__(self):
        self.env = ResearchMindEnv()
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads existing PPO strategist model or trains a new one if not found."""
        if os.path.exists(f"{MODEL_PATH}.zip"):
            try:
                self.model = PPO.load(MODEL_PATH)
                print("[RL Strategist] Loaded existing PPO model successfully.")
            except Exception as e:
                print(f"[RL Strategist Warning] Failed to load model: {e}. Falling back to training.")
                self.train_and_save()
        else:
            print("[RL Strategist] PPO model not found. Starting initial model training...")
            self.train_and_save()

    def train_and_save(self):
        """Trains PPO agent on Gym environment and saves weights."""
        try:
            self.model = PPO("MlpPolicy", self.env, verbose=0, learning_rate=0.001)
            self.model.learn(total_timesteps=5000)
            self.model.save(MODEL_PATH)
            print(f"[RL Strategist] Successfully trained PPO model and saved to '{MODEL_PATH}'.")
        except Exception as e:
            print(f"[RL Strategist Error] Training failed: {e}")

    def get_observation(self, blackboard: ResearchBlackboard) -> np.ndarray:
        """Derives a normalized Gym observation vector from current blackboard state."""
        # 1. Concept count
        concepts = [node for node in blackboard.knowledge_graph.nodes if blackboard.knowledge_graph.nodes[node].get("type") == "concept"]
        concept_ratio = min(1.0, len(concepts) / 20.0)
        
        # 2. Paper count
        papers = blackboard.working_memory.get("retrieved_papers", [])
        paper_ratio = min(1.0, len(papers) / 10.0)
        
        # 3. Contradiction count
        contradictions = [e for e in blackboard.event_queue if e["type"] == "CONTRADICTION_FOUND"]
        contradiction_ratio = min(1.0, len(contradictions) / 5.0)
        
        # 4. Avg confidence
        avg_confidence = 0.5
        if blackboard.claims:
            avg_confidence = sum(c["confidence_score"] for c in blackboard.claims) / len(blackboard.claims)
            
        # 5. Budget spent
        cost = blackboard.budget.get("cost_usd", 0.0)
        budget_ratio = min(1.0, cost / 10.0)
        
        return np.array([concept_ratio, paper_ratio, contradiction_ratio, avg_confidence, budget_ratio], dtype=np.float32)

    def select_action(self, blackboard: ResearchBlackboard) -> int:
        """Predicts the next high-value action using the PPO policy, with heuristic fallback."""
        obs = self.get_observation(blackboard)
        
        # Heuristic safety override: if no papers found, search literature first!
        papers = blackboard.working_memory.get("retrieved_papers", [])
        if not papers:
            print("[RL Strategist Override] No papers found in memory. Recommending SEARCH_PAPERS.")
            return 0  # SEARCH_PAPERS
            
        if self.model:
            action, _ = self.model.predict(obs, deterministic=True)
            action_val = int(action)
        else:
            # Heuristic default
            action_val = 1  # ANALYZE_PAPER
            
        return action_val

    def execute_action(self, blackboard: ResearchBlackboard, action: int, scheduler: TaskScheduler):
        """Translates the selected action into a scheduled agent task."""
        action_mapping = {
            0: ("discover_papers", "SEARCHING"),
            1: ("analyze_paper", "READING"),
            2: ("verify_claim", "VERIFYING"),
            3: ("synthesize_knowledge", "SYNTHESIZING"),
            4: ("explain_findings", "QUESTIONING_USER"),
            5: ("checkpoint_session", "COMPLETE")
        }
        
        task_name, state_name = action_mapping.get(action, ("checkpoint_session", "COMPLETE"))
        
        # Transition State Machine
        ResearchStateMachine.transition_to(blackboard, state_name)
        
        # Determine payload
        payload = {}
        if action == 0:
            payload["query"] = blackboard.context.get("query", "")
            payload["source_selection"] = "arxiv"
        elif action == 1:
            # Find next unanalyzed paper
            papers = blackboard.working_memory.get("retrieved_papers", [])
            analyzed = [node for node in blackboard.knowledge_graph.nodes if blackboard.knowledge_graph.nodes[node].get("type") == "paper"]
            unprocessed = [p for p in papers if p["title"] not in analyzed]
            
            if unprocessed:
                payload["paper_title"] = unprocessed[0]["title"]
            else:
                # Re-synthesize or terminate if nothing left to analyze
                task_name, state_name = "synthesize_knowledge", "SYNTHESIZING"
                ResearchStateMachine.transition_to(blackboard, state_name)
        elif action == 2:
            # Select claims to verify
            if blackboard.claims:
                payload["claim_text"] = blackboard.claims[-1]["claim_text"]
                
        # Schedule the task
        scheduler.schedule_task(blackboard, task_name, priority=10, payload=payload)

# Global Instance
rl_strategist = RLStrategist()
