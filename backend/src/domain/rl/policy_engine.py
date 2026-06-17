import os
import json
import random

Q_TABLE_FILE = "q_table.json"

class PolicyEngine:
    def __init__(self):
        self.q_table = {}
        self.load_policy()
        
    def load_policy(self):
        if os.path.exists(Q_TABLE_FILE):
            try:
                with open(Q_TABLE_FILE, 'r', encoding='utf-8') as f:
                    self.q_table = json.load(f)
                print("[Policy Engine] Loaded existing Q-table.")
            except Exception:
                self.q_table = {}
        else:
            self.q_table = {}
            
    def save_policy(self):
        try:
            with open(Q_TABLE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.q_table, f, indent=4)
        except Exception as e:
            print(f"[Policy Engine Error] Failed to save Q-table: {e}")

    def get_state_key(self, query: str, has_pdf: bool) -> str:
        """
        Derives a discrete state representation from query text and context.
        """
        # Feature 1: Query type classification
        q_lower = query.lower()
        if "compare" in q_lower or "comparison" in q_lower or "difference" in q_lower:
            q_type = "compare"
        elif "methodology" in q_lower or "method" in q_lower or "how did they" in q_lower:
            q_type = "methodology"
        elif "gap" in q_lower or "future" in q_lower or "underexplored" in q_lower:
            q_type = "gap_analysis"
        else:
            q_type = "general"
            
        # Feature 2: Uploaded PDF present
        pdf_state = "has_pdf" if has_pdf else "no_pdf"
        
        return f"state_{q_type}_{pdf_state}"

    def get_action_space(self, action_type: str) -> list:
        if action_type == "source_selection":
            # 0: arxiv, 1: semantic_scholar, 2: web_search
            return [0, 1, 2]
        elif action_type == "retrieval_strategy":
            # 0: semantic, 1: bm25, 2: hybrid
            return [0, 1, 2]
        elif action_type == "expansion_depth":
            # 0: none, 1: shallow, 2: deep
            return [0, 1, 2]
        return [0]

    def choose_action(self, state_key: str, action_type: str, epsilon: float = 0.15) -> int:
        """
        Chooses an action using Epsilon-Greedy strategy.
        """
        actions = self.get_action_space(action_type)
        
        # Initialize state action values if not present
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if action_type not in self.q_table[state_key]:
            self.q_table[state_key][action_type] = {str(a): 0.0 for a in actions}
            
        # Epsilon-greedy selection
        if random.random() < epsilon:
            return random.choice(actions)
            
        # Select action with maximum Q-value
        q_vals = self.q_table[state_key][action_type]
        max_q = max(q_vals.values())
        best_actions = [int(a) for a, q in q_vals.items() if q == max_q]
        return random.choice(best_actions)

    def update_q_value(self, state_key: str, action_type: str, action: int, reward: float, next_state_key: str, alpha: float = 0.1, gamma: float = 0.9):
        """
        Updates Q-value using standard Temporal Difference update:
        Q(s,a) = Q(s,a) + alpha * [reward + gamma * max(Q(s', a')) - Q(s,a)]
        """
        actions = self.get_action_space(action_type)
        
        # Ensure state and action keys exist
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if action_type not in self.q_table[state_key]:
            self.q_table[state_key][action_type] = {str(a): 0.0 for a in actions}
            
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {}
        if action_type not in self.q_table[next_state_key]:
            self.q_table[next_state_key][action_type] = {str(a): 0.0 for a in actions}
            
        # Get current Q-value
        curr_q = self.q_table[state_key][action_type][str(action)]
        
        # Get maximum Q-value of next state
        next_q_vals = self.q_table[next_state_key][action_type]
        max_next_q = max(next_q_vals.values())
        
        # Compute new Q-value
        new_q = curr_q + alpha * (reward + (gamma * max_next_q) - curr_q)
        self.q_table[state_key][action_type][str(action)] = round(new_q, 4)
        
        # Save policy to file
        self.save_policy()

# Global Singleton
policy_engine = PolicyEngine()
