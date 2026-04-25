"""
Tests for the wellbeing chat module.
These tests run without an OpenAI API key (agent calls are mocked).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_new_session_returns_consent_prompt():
    """First message to a new session should return the consent prompt."""
    response = client.post(
        "/api/wellbeing/chat",
        json={"message": "Hello", "session_id": "test-wb-new-session-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "awaiting_consent"
    assert "consent" in data["response"].lower()
    assert "ai" in data["response"].lower()


def test_consent_yes_moves_to_active():
    """After consent 'yes', session should become active."""
    # First call creates the session and shows consent prompt
    session_id = "test-wb-consent-yes-001"
    client.post("/api/wellbeing/chat", json={"message": "Hi", "session_id": session_id})
    # Second call: user says yes
    response = client.post(
        "/api/wellbeing/chat",
        json={"message": "yes", "session_id": session_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("active", "escalated")


def test_consent_no_returns_stateless():
    """Declining consent should result in stateless mode."""
    session_id = "test-wb-consent-no-001"
    client.post("/api/wellbeing/chat", json={"message": "Hi", "session_id": session_id})
    response = client.post(
        "/api/wellbeing/chat",
        json={"message": "no", "session_id": session_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stateless"
    assert "988" in data["response"] or "crisis" in data["response"].lower()


def test_wellbeing_chat_returns_session_id():
    response = client.post(
        "/api/wellbeing/chat",
        json={"message": "I'm feeling stressed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


def test_consent_endpoint():
    session_id = "test-wb-consent-endpoint-001"
    response = client.post(
        "/api/wellbeing/consent",
        json={"session_id": session_id, "consent_given": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["consent_given"] is True


def test_panic_button_returns_404_for_unknown_session():
    response = client.post(
        "/api/wellbeing/panic",
        json={"session_id": "nonexistent-session-xyz"},
    )
    assert response.status_code == 404


def test_panic_button_escalates_known_session():
    """Panic button on a real session should trigger escalation."""
    session_id = "test-wb-panic-001"
    client.post("/api/wellbeing/chat", json={"message": "Hi", "session_id": session_id})

    with patch("app.api.routes.wellbeing_chat.get_wellbeing_agent") as mock_agent_factory:
        from app.schemas.wellbeing import EscalationSummary
        mock_agent = MagicMock()
        mock_agent.handle_panic = AsyncMock(return_value=EscalationSummary(
            session_id=session_id,
            duration_minutes=5,
        ))
        mock_agent_factory.return_value = mock_agent

        response = client.post(
            "/api/wellbeing/panic",
            json={"session_id": session_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "escalated"
        assert "988" in data["message"]
