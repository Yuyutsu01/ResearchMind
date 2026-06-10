import os
import sys

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from memory.postgres.db import store_experience, get_experiences

def save_transition(state: dict, action: dict, reward: float, next_state: dict):
    """
    Saves an RL experience tuple in the database.
    """
    try:
        store_experience(state, action, reward, next_state)
        print(f"[RL Experience Store] Saved transition with reward: {reward:.3f}")
    except Exception as e:
        print(f"[RL Experience Store Error] {e}")

def get_replay_buffer(limit: int = 100) -> list[dict]:
    """
    Retrieves the latest transition tuples for policy updates.
    """
    try:
        return get_experiences(limit)
    except Exception as e:
        print(f"[RL Experience Store Error] Failed to read replay buffer: {e}")
        return []
