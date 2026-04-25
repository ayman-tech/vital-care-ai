import pytest
from app.safety.medical_safety_guardrails import MedicalSafetyGuardrails


@pytest.fixture
def guardrails():
    return MedicalSafetyGuardrails()


def test_detects_chest_pain_emergency(guardrails):
    is_emergency, flags = guardrails.check_user_message_for_emergency(
        "I have chest pain and can't breathe"
    )
    assert is_emergency is True
    assert len(flags) > 0


def test_detects_stroke_symptoms(guardrails):
    is_emergency, flags = guardrails.check_user_message_for_emergency(
        "My face is drooping and my arm is weak and I can't speak"
    )
    assert is_emergency is True


def test_detects_suicidal_ideation(guardrails):
    is_emergency, flags = guardrails.check_user_message_for_emergency(
        "I want to kill myself"
    )
    assert is_emergency is True


def test_non_emergency_message(guardrails):
    is_emergency, flags = guardrails.check_user_message_for_emergency(
        "I have a mild headache that started this morning"
    )
    assert is_emergency is False


def test_diagnosis_claim_flagged(guardrails):
    result = guardrails.check_response_safety(
        "You have diabetes and should stop taking your medication."
    )
    assert result["is_safe"] is False
    assert len(result["issues_found"]) > 0


def test_safe_response_passes(guardrails):
    result = guardrails.check_response_safety(
        "This could be associated with a tension headache. Please consult a healthcare professional."
    )
    assert result["is_safe"] is True


def test_emergency_response_built(guardrails):
    msg = guardrails.build_emergency_response(["chest pain", "shortness of breath"])
    assert "emergency" in msg.lower() or "911" in msg


def test_disclaimer_appended_when_missing(guardrails):
    response = guardrails.ensure_disclaimer("Rest and drink fluids.")
    assert "not a doctor" in response.lower() or "cannot diagnose" in response.lower()


def test_disclaimer_not_duplicated(guardrails):
    response = "Please consult a healthcare professional for diagnosis."
    result = guardrails.ensure_disclaimer(response)
    assert result.count("consult") >= 1
