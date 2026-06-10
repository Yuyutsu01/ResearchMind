import os
import sys
import argparse

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.rl.experience_store import get_replay_buffer
from agent.rl.policy_engine import policy_engine

def train_policy(epochs: int = 1, alpha: float = 0.1, gamma: float = 0.9) -> int:
    """
    Loads transitions from experience replay buffer and updates Q-table policy.
    Returns the count of updated steps.
    """
    buffer = get_replay_buffer(limit=250)
    if not buffer:
        print("[RL Trainer] No experiences found in database. Skipping training.")
        return 0
        
    print(f"[RL Trainer] Replaying {len(buffer)} transitions from database...")
    updates_count = 0
    
    for _ in range(epochs):
        for exp in buffer:
            state = exp["state"]
            action_dict = exp["action"]
            reward = exp["reward"]
            next_state = exp["next_state"]
            
            # Extract state keys
            state_key = policy_engine.get_state_key(state.get("query", ""), state.get("has_pdf", False))
            next_state_key = policy_engine.get_state_key(next_state.get("query", ""), next_state.get("has_pdf", False))
            
            # Update Q-values for each action category
            for action_type, val in action_dict.items():
                policy_engine.update_q_value(
                    state_key=state_key,
                    action_type=action_type,
                    action=int(val),
                    reward=reward,
                    next_state_key=next_state_key,
                    alpha=alpha,
                    gamma=gamma
                )
                updates_count += 1
                
    policy_engine.save_policy()
    print(f"[RL Trainer] Training complete. Performed {updates_count} Q-value updates.")
    return updates_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-run", action="store_true", help="Run a dry-run test of the trainer")
    args = parser.parse_args()
    
    if args.test_run:
        print("[RL Trainer] Testing policy choosing...")
        sk = policy_engine.get_state_key("transformer paper summary", True)
        a_src = policy_engine.choose_action(sk, "source_selection", epsilon=0.5)
        print(f"Chosen state key: {sk}")
        print(f"Chosen action for source_selection: {a_src}")
        
        # Test update
        policy_engine.update_q_value(sk, "source_selection", a_src, 0.75, sk)
        print("Successfully updated Q-table policy.")
