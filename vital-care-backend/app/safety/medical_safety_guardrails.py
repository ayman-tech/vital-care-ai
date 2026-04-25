import re
import logging
from app.prompts.safety_prompt import EMERGENCY_OVERRIDE_MESSAGE

logger = logging.getLogger(__name__)

STANDARD_DISCLAIMER = (
    "I am not a doctor and cannot diagnose you. This information is for educational "
    "purposes only. Always consult a qualified healthcare professional for medical advice, "
    "diagnosis, or treatment."
)

# Keyword patterns that indicate emergency situations
_EMERGENCY_PATTERNS = [
    r"\bchest\s+pain\b",
    r"\bcan'?t\s+breathe\b",
    r"\bdifficult(y)?\s+breathing\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bstroke\b",
    r"\bface\s+drop(ping)?\b",
    r"\barm\s+weak(ness)?\b",
    r"\bspeech\s+(slurred|difficulty|problem)\b",
    r"\bsevere\s+bleed(ing)?\b",
    r"\bblood\s+everywhere\b",
    r"\boverdose\b",
    r"\bpoisoning\b",
    r"\bsuicid(e|al)\b",
    r"\bself.?harm\b",
    r"\bkill\s+(myself|me)\b",
    r"\bsevere\s+abdominal\s+pain\b",
    r"\bpregnancy\s+(complication|bleed|danger)\b",
    r"\bsudden\s+vision\s+loss\b",
    r"\bloss\s+of\s+consciousness\b",
    r"\bpassed?\s+out\b",
    r"\bseizure\b",
    r"\bconvulsion\b",
    r"\binfant\s+fever\b",
    r"\bbaby\s+fever\b",
    r"\bsevere\s+dehydration\b",
    r"\bhead\s+injury\b",
    r"\bfainting\b",
    r"\bfainted\b",
    r"\ballergic\s+reaction\b",
    r"\bthroat\s+(closing|swelling)\b",
    r"\banaphyl\b",
]

# Phrases that constitute unsafe diagnosis claims
_DIAGNOSIS_CLAIM_PATTERNS = [
    r"\byou\s+have\s+[a-z\s]+disease\b",
    r"\byou\s+have\s+[a-z\s]+disorder\b",
    r"\byou\s+are\s+diagnosed\s+with\b",
    r"\byou\s+definitely\s+have\b",
    r"\bI\s+diagnose\s+you\s+with\b",
    r"\byour\s+diagnosis\s+is\b",
]

# Patterns for unsafe medication advice
_UNSAFE_MEDICATION_PATTERNS = [
    r"\bstop\s+(taking|your)\s+medication\b",
    r"\bdiscontinue\s+your\s+(medication|prescription)\b",
    r"\bdo\s+not\s+take\s+your\s+(medication|pills)\b",
    r"\btake\s+\d+\s*mg\s+of\s+[a-z]+\b",
    r"\bprescribe\s+you\b",
]


def _matches_any(text: str, patterns: list[str]) -> list[str]:
    text_lower = text.lower()
    return [p for p in patterns if re.search(p, text_lower)]


class MedicalSafetyGuardrails:
    """
    Inspects user messages and AI responses for safety violations.
    Can override responses when emergency red flags are detected.
    """

    def check_user_message_for_emergency(self, message: str) -> tuple[bool, list[str]]:
        """Return (is_emergency, list_of_matched_red_flags)."""
        matched = _matches_any(message, _EMERGENCY_PATTERNS)
        return bool(matched), matched

    def check_response_safety(self, response_text: str) -> dict:
        """
        Audit an AI response for safety issues.
        Returns a dict with: is_safe, issues_found, requires_emergency_override.
        """
        issues = []
        requires_emergency_override = False

        diagnosis_matches = _matches_any(response_text, _DIAGNOSIS_CLAIM_PATTERNS)
        if diagnosis_matches:
            issues.append(f"Diagnosis claim detected: {diagnosis_matches}")

        med_matches = _matches_any(response_text, _UNSAFE_MEDICATION_PATTERNS)
        if med_matches:
            issues.append(f"Unsafe medication advice detected: {med_matches}")

        emergency_matches = _matches_any(response_text, _EMERGENCY_PATTERNS)
        if emergency_matches and "emergency" not in response_text.lower():
            issues.append("Emergency symptoms mentioned but no escalation found")
            requires_emergency_override = True

        return {
            "is_safe": len(issues) == 0,
            "issues_found": issues,
            "requires_emergency_override": requires_emergency_override,
        }

    def build_emergency_response(self, red_flags: list[str]) -> str:
        flags_text = ""
        if red_flags:
            flags_text = f" (concerning symptoms: {', '.join(red_flags[:3])})"
        return (
            f"{EMERGENCY_OVERRIDE_MESSAGE}{flags_text}\n\n"
            "**What to do right now:**\n"
            "- Call 911 (or your local emergency number) or have someone take you to the ER\n"
            "- Do not drive yourself if you are feeling very unwell\n"
            "- Stay calm and describe your symptoms clearly to emergency services\n\n"
            f"{STANDARD_DISCLAIMER}"
        )

    def ensure_disclaimer(self, response_text: str) -> str:
        """Append disclaimer if it is missing from the response."""
        disclaimer_keywords = ["not a doctor", "cannot diagnose", "consult a", "healthcare professional"]
        if not any(kw in response_text.lower() for kw in disclaimer_keywords):
            return f"{response_text}\n\n---\n*{STANDARD_DISCLAIMER}*"
        return response_text


def get_safety_guardrails() -> MedicalSafetyGuardrails:
    return MedicalSafetyGuardrails()
