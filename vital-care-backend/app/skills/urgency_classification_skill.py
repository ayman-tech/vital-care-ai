import logging
from app.services.llm_service import LLMService
from app.prompts.urgency_prompt import URGENCY_PROMPT
from app.schemas.urgency import UrgencyResult

logger = logging.getLogger(__name__)


class UrgencyClassificationSkill:
    """Classifies the medical urgency of a symptom description."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, symptom_summary: str) -> UrgencyResult:
        raw = await self.llm.chat_completion_json(
            system_prompt=URGENCY_PROMPT,
            user_message=f"Symptom description: {symptom_summary}",
        )
        try:
            return UrgencyResult(
                level=raw.get("level", "unknown"),
                reason=raw.get("reason", ""),
                red_flags=raw.get("red_flags", []),
                recommended_timeframe=raw.get("recommended_timeframe", ""),
            )
        except Exception as e:
            logger.error("UrgencyClassificationSkill parse error: %s", e)
            return UrgencyResult()
