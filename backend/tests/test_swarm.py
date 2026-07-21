import pytest
from unittest.mock import MagicMock, patch
from src.domain.swarm.orchestrator import swarm_orchestrator
from src.adapters.llm_adapter import llm_client

@pytest.mark.asyncio
@patch("src.adapters.db.postgres.psycopg2.connect")
async def test_swarm_orchestrator_equation_routing(mock_connect):
    """
    Verifies the SwarmOrchestrator routes equation selections 
    to math, background, visual, and question sub-agents.
    """
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    # Run processor
    res = await swarm_orchestrator.process_selection(
        session_id=123,
        selection_text="F(s,a,s') = gamma * Phi(s') - Phi(s)",
        selection_type="EQUATION",
        obj_id="eq_p1_0"
    )
    
    assert "math" in res
    assert "background" in res
    assert "visual" in res
    assert "questions" in res
    assert "latex_clean" in res["math"]
