import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.chat import DiagnosisChatResponse
from app.schemas.urgency import UrgencyResult, RecommendedProviderType

client = TestClient(app)


def _mock_agent_response():
    return DiagnosisChatResponse(
        response="Based on your symptoms, this could be related to a common tension headache. Please see a doctor if it persists.",
        intent="symptoms",
        urgency=UrgencyResult(
            level="routine",
            reason="Mild headache, no red flags.",
            red_flags=[],
            recommended_timeframe="See a doctor within a few days if it persists.",
        ),
        recommended_provider_type=RecommendedProviderType(
            specialty="primary_care",
            reason="Routine headache evaluation.",
        ),
    )


def test_diagnosis_chat_returns_valid_schema():
    """Test that the diagnosis endpoint returns a valid DiagnosisChatResponse schema."""
    with patch("app.api.routes.diagnosis_chat.get_diagnosis_agent") as mock_get_agent:
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=_mock_agent_response())
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/api/diagnosis/chat",
            json={"message": "I have a mild headache", "user_id": "test-user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "urgency" in data
        assert "intent" in data
        assert "safety_disclaimer" in data
        assert data["urgency"]["level"] in [
            "emergency", "urgent", "soon", "routine", "self_care", "unknown"
        ]


def test_diagnosis_chat_emergency_triggers_override():
    """Test that emergency messages short-circuit to the emergency response."""
    response = client.post(
        "/api/diagnosis/chat",
        json={"message": "I have severe chest pain and can't breathe"},
    )
    assert response.status_code == 200
    data = response.json()
    # Emergency override fires before LLM — no mock needed
    assert data["urgency"]["level"] == "emergency"
    assert "ER" in data["recommended_provider_type"]["specialty"]


def test_diagnosis_chat_missing_message_fails():
    response = client.post("/api/diagnosis/chat", json={})
    assert response.status_code == 422


def test_diagnosis_chat_has_disclaimer():
    with patch("app.api.routes.diagnosis_chat.get_diagnosis_agent") as mock_get_agent:
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=_mock_agent_response())
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/api/diagnosis/chat",
            json={"message": "I have a sore throat"},
        )
        data = response.json()
        assert len(data["safety_disclaimer"]) > 10
