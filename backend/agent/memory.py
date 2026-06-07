import os
import json
import numpy as np
from datetime import datetime
from rag.embed import get_embedding
from agent.telemetry import telemetry

MEMORY_FILE = "memory.json"

def load_memory() -> list:
    """Load memory from file."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_memory(memories: list):
    """Save memory to file."""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memories, f, indent=4)

def store_task(task: str, output: str):
    """Store the given task and its final output in memory."""
    memories = load_memory()
    
    # Optional: We could store the embedding directly, but for simplicity
    # we can compute it on the fly next time or store it if we wanted to avoid re-embedding.
    # We will just embed it when searching to keep the JSON clean and small, 
    # but storing it would be more efficient for larger memories.
    
    new_mem = {
        "task": task,
        "output": output,
        "timestamp": datetime.now().isoformat()
    }
    memories.append(new_mem)
    save_memory(memories)
    print(f"[Memory] Stored task: '{task}'")

def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def retrieve_similar_task(new_task: str, threshold: float = 0.85):
    """Check if a similar task exists in memory, using embedding similarity."""
    memories = load_memory()
    if not memories:
        telemetry.record_cache_miss()
        return None
        
    query_emb = get_embedding(new_task)
    
    best_match = None
    highest_score = 0.0
    
    for mem in memories:
        mem_idx = get_embedding(mem["task"])
        score = cosine_similarity(query_emb, mem_idx)
        if score > highest_score:
            highest_score = score
            best_match = mem
            
    if highest_score >= threshold:
        print(f"[Memory] Found similar past task (Score: {highest_score:.2f}): '{best_match['task']}'")
        telemetry.record_cache_hit()
        return best_match["output"]
        
    telemetry.record_cache_miss()
    return None
