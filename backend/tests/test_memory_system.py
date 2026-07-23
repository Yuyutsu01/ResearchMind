import pytest
from unittest.mock import patch, MagicMock
from src.domain.swarm.memory import AgentMemorySystem

@patch("src.domain.swarm.memory.execute_query")
@patch("src.adapters.db.redis_session.redis_session.get_stream_history")
def test_agent_memory_retrieval(mock_stream, mock_db):
    mock_stream.return_value = [
        {"text": "Attention is all you need", "summary": "Introduces Transformer architecture"}
    ]
    mock_db.return_value = [
        {"selection_text": "Self-attention", "user_note": "Key mechanism"}
    ]
    
    memory_system = AgentMemorySystem()
    context = memory_system.retrieve_context(session_id=1, query_text="Transformers")

    assert "Attention is all you need" in context
    assert "Self-attention" in context
