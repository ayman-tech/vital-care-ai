import logging
from app.services.llm_service import LLMService
from app.prompts.provider_type_prompt import PROVIDER_TYPE_PROMPT
from app.schemas.urgency import RecommendedProviderType

logger = logging.getLogger(__name__)


class ProviderTypeSkill:
    """Recommends the most appropriate healthcare provider type."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, symptom_summary: str, urgency_level: str = "unknown") -> RecommendedProviderType:
        raw = await self.llm.chat_completion_json(
            system_prompt=PROVIDER_TYPE_PROMPT,
            user_message=f"Symptom description: {symptom_summary}\nUrgency level: {urgency_level}",
        )
        try:
            return RecommendedProviderType(
                specialty=raw.get("specialty", "unknown"),
                reason=raw.get("reason", ""),
            )
        except Exception as e:
            logger.error("ProviderTypeSkill parse error: %s", e)
            return RecommendedProviderType()
