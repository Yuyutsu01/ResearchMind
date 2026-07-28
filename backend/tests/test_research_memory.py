"""
Unit Tests for Research Memory System (Phase 2)
"""

import pytest
from src.runtime.memory.research_memory import research_memory

def test_record_and_retrieve_learned_concept():
    """Verifies concepts are recorded and retrieved from Research Memory."""
    session_id = 999
    
    # Record concept
    mem = research_memory.record_learned_concept(session_id, "Transformers")
    assert "Transformers" in mem.learned_concepts
    
    # Retrieve memory
    fetched = research_memory.get_user_memory(session_id)
    assert "Transformers" in fetched.learned_concepts

def test_build_memory_prompt_context():
    """Verifies memory prompt context is generated for concept suppression."""
    session_id = 999
    research_memory.record_learned_concept(session_id, "Self-Attention")
    
    prompt_ctx = research_memory.build_memory_prompt_context(session_id)
    assert "USER KNOWLEDGE STATE" in prompt_ctx
    assert "Self-Attention" in prompt_ctx
    assert "Do NOT explain basic definitions" in prompt_ctx
