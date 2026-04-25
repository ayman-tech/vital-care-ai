import logging
from app.services.llm_service import LLMService
from app.prompts.medical_jargon_prompt import MEDICAL_JARGON_PROMPT

logger = logging.getLogger(__name__)


class MedicalJargonSkill:
    """Explains medical terminology in plain, accessible language."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, term: str, context: str = "") -> dict:
        user_input = f"Medical term to explain: {term}"
        if context:
            user_input += f"\nContext where this term appeared: {context}"

        raw = await self.llm.chat_completion_json(
            system_prompt=MEDICAL_JARGON_PROMPT,
            user_message=user_input,
        )
        return raw or {
            "term": term,
            "simple_explanation": "Unable to explain this term at this time.",
            "deeper_explanation": "",
            "example": "",
            "when_to_ask_a_doctor": "If this term appears in your medical records, ask your doctor to explain it.",
        }
