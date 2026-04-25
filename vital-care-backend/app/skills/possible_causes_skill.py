import logging
from app.services.llm_service import LLMService
from app.prompts.possible_causes_prompt import POSSIBLE_CAUSES_PROMPT
from app.schemas.urgency import PossibleCause

logger = logging.getLogger(__name__)


class PossibleCausesSkill:
    """Suggests possible (non-diagnostic) causes for described symptoms."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, symptom_summary: str, user_context_notes: str = "") -> list[PossibleCause]:
        prompt_input = f"Symptoms: {symptom_summary}"
        if user_context_notes:
            prompt_input += f"\nUser context: {user_context_notes}"

        raw = await self.llm.chat_completion_json(
            system_prompt=POSSIBLE_CAUSES_PROMPT,
            user_message=prompt_input,
        )
        causes = []
        for item in raw.get("possible_causes", []):
            try:
                causes.append(PossibleCause(
                    name=item.get("name", "Unknown"),
                    likelihood=item.get("likelihood", "possible"),
                    reasoning=item.get("reasoning", ""),
                    disclaimer=item.get(
                        "disclaimer",
                        "This is not a diagnosis. Please consult a healthcare professional."
                    ),
                ))
            except Exception as e:
                logger.warning("Skipping malformed possible cause: %s", e)
        return causes
