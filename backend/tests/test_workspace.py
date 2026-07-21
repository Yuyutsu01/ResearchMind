import pytest
from unittest.mock import MagicMock, patch
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.agents.explain_selection import explain_selection

@pytest.fixture
def mock_blackboard():
    blackboard = ResearchBlackboard(session_id=999)
    blackboard.context["query"] = "Compare positional encodings"
    return blackboard

@patch("src.domain.agents.explain_selection.llm_client")
@patch("src.domain.agents.explain_selection.execute_query")
def test_explain_selection_structure(mock_execute_query, mock_llm_client, mock_blackboard):
    # Setup mock LLM return values
    mock_llm_client.get_structured_json.return_value = {
        "level_1": "Core intuition of positional encodings.",
        "level_2": "Detailed summary paragraph.",
        "level_3": "Concept assumptions.",
        "level_4": "Math representations.",
        "level_5": "Historical evolution.",
        "level_6": "PyTorch implementation.",
        "level_7": "Related references.",
        "why_this_matters": {
            "author_intent": "Needed for permutation invariance",
            "problem_solved": "Sequence order mapping.",
            "later_dependents": "Equation 3",
            "prerequisites": "Sine/Cosine functions"
        },
        "critic_warning": "Warning about context length scaling issues."
    }

    # Run explanation service
    explanation = explain_selection(mock_blackboard, "relative positional encoding", "TECHNICAL_TERM")

    # Assertions
    assert "level_1" in explanation
    assert "level_6" in explanation
    assert explanation["why_this_matters"]["author_intent"] == "Needed for permutation invariance"
    assert "critic_warning" in explanation

    # Verify timeline DB logging call was triggered
    assert mock_execute_query.called
