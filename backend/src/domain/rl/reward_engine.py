def calculate_reward(validation_score: float, citation_score: float, duration_ms: float, user_feedback: float = 0.5) -> float:
    """
    Computes a reward signal bounded between -1.0 and +1.0.
    
    Parameters:
    - validation_score: float [0, 1] (agent's output validity)
    - citation_score: float [0, 1] (accuracy of bibliography matches)
    - duration_ms: float (time spent executing search/RAG)
    - user_feedback: float [0, 1] (optional rating)
    """
    # 1. Base accuracy rewards
    accuracy_weight = 0.5
    citation_weight = 0.25
    feedback_weight = 0.15
    
    weighted_score = (
        (validation_score * accuracy_weight) +
        (citation_score * citation_weight) +
        (user_feedback * feedback_weight)
    )
    
    # Scale base score to [-0.5, +0.8] range
    reward = (weighted_score * 1.3) - 0.5
    
    # 2. Efficiency Penalties (cost/latency)
    # Give a penalty for taking too long (e.g. over 15 seconds is slow)
    duration_sec = duration_ms / 1000.0
    latency_penalty = 0.0
    if duration_sec > 15.0:
        latency_penalty = -0.15
    elif duration_sec > 5.0:
        latency_penalty = -0.05
        
    reward += latency_penalty
    
    # Clamp final reward between -1.0 and 1.0
    return max(-1.0, min(1.0, reward))
