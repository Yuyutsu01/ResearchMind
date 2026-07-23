import pytest
from unittest.mock import MagicMock, patch
from src.adapters.llm_providers import OpenAIProvider, GroqProvider, retry_with_backoff, track_tokens_and_cost
from src.adapters.llm_adapter import LLMAdapter

def test_llm_adapter_provider_selection():
    with patch.dict("os.environ", {"LLM_PROVIDER": "groq", "LLM_API_KEY": "gsk_test"}):
        adapter = LLMAdapter()
        assert adapter.provider_name == "groq"
        assert isinstance(adapter.provider, GroqProvider)

def test_llm_adapter_mock_fallback():
    with patch.dict("os.environ", {"LLM_PROVIDER": "mock"}):
        adapter = LLMAdapter()
        assert adapter.provider_name == "mock"
        res = adapter.get_structured_json("test_key", "system", "user")
        assert isinstance(res, dict)

import httpx

def test_retry_with_backoff_decorator():
    mock_func = MagicMock()
    mock_func.side_effect = [httpx.RequestError("Temporary Error", request=MagicMock()), "Success"]

    decorated = retry_with_backoff(max_retries=2, initial_delay=0.01)(mock_func)
    res = decorated()

    assert res == "Success"
    assert mock_func.call_count == 2
