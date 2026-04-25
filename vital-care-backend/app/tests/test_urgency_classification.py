import pytest
from unittest.mock import AsyncMock, MagicMock
from app.skills.urgency_classification_skill import UrgencyClassificationSkill
from app.schemas.urgency import UrgencyResult


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    return llm


@pytest.mark.asyncio
async def test_urgency_emergency_level(mock_llm):
    mock_llm.chat_completion_json = AsyncMock(return_value={
        "level": "emergency",
        "reason": "Chest pain with shortness of breath are emergency symptoms.",
        "red_flags": ["chest pain", "shortness of breath"],
        "recommended_timeframe": "Go to the ER now."
    })
    skill = UrgencyClassificationSkill(mock_llm)
    result = await skill.run("I have chest pain and I can't breathe")
    assert result.level == "emergency"
    assert len(result.red_flags) > 0


@pytest.mark.asyncio
async def test_urgency_routine_level(mock_llm):
    mock_llm.chat_completion_json = AsyncMock(return_value={
        "level": "routine",
        "reason": "Mild intermittent headache, no red flags.",
        "red_flags": [],
        "recommended_timeframe": "Schedule an appointment with your doctor."
    })
    skill = UrgencyClassificationSkill(mock_llm)
    result = await skill.run("I get mild headaches occasionally")
    assert result.level == "routine"
    assert result.red_flags == []


@pytest.mark.asyncio
async def test_urgency_returns_default_on_empty_response(mock_llm):
    mock_llm.chat_completion_json = AsyncMock(return_value={})
    skill = UrgencyClassificationSkill(mock_llm)
    result = await skill.run("some symptoms")
    assert isinstance(result, UrgencyResult)
    assert result.level == "unknown"
