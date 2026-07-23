import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200

@patch("src.adapters.api.routes.execute_query")
def test_create_session(mock_execute):
    mock_execute.side_effect = [
        [{"id": 1}], # user_exists
        [{"id": 101}] # session_id
    ]
    response = client.post(
        "/api/v1/sessions",
        json={"user_id": 1, "prompt": "Test Prompt"}
    )
    assert response.status_code == 201
    assert response.json()["session_id"] == 101
