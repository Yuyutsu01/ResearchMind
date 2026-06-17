import os
import sys

# Ensure backend directory is in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir and os.path.basename(current_dir) != "backend":
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

if current_dir and current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.adapters.db.postgres_db import store_experience, get_experiences

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
