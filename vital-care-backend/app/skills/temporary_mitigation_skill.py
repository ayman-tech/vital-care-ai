import logging
from app.services.llm_service import LLMService
from app.prompts.temporary_mitigation_prompt import TEMPORARY_MITIGATION_PROMPT
from app.schemas.urgency import TemporaryMitigation

logger = logging.getLogger(__name__)


class TemporaryMitigationSkill:
    """Suggests safe temporary steps while the user awaits professional care."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, symptom_summary: str, urgency_level: str = "unknown") -> list[TemporaryMitigation]:
        # Don't suggest home care for emergencies
        if urgency_level == "emergency":
            return [
                TemporaryMitigation(
                    title="Seek emergency care immediately",
                    description="Call 911 or go to the nearest emergency room right away.",
                    safety_note="Do not attempt home management for emergency symptoms.",
                )
            ]

        raw = await self.llm.chat_completion_json(
            system_prompt=TEMPORARY_MITIGATION_PROMPT,
            user_message=f"Symptom description: {symptom_summary}\nUrgency level: {urgency_level}",
        )
        steps = []
        for item in raw.get("temporary_mitigation", []):
            try:
                steps.append(TemporaryMitigation(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    safety_note=item.get("safety_note", ""),
                ))
            except Exception as e:
                logger.warning("Skipping malformed mitigation step: %s", e)
        return steps
