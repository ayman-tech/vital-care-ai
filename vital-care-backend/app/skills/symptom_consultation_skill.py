import logging
from app.services.llm_service import LLMService
from app.prompts.symptom_consultation_prompt import SYMPTOM_CONSULTATION_PROMPT
from app.schemas.common import UserContext

logger = logging.getLogger(__name__)


class SymptomConsultationSkill:
    """Extracts and structures symptom information from user messages."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(
        self,
        message: str,
        user_context: UserContext | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        context_str = ""
        if user_context:
            context_str = f"\n\nUser context: {user_context.model_dump_json()}"

        current = f"User message: {message}{context_str}"

        if history:
            # Replace last user turn with the enriched message so context_str is included
            messages = history[:-1] if history and history[-1]["role"] == "user" else history
            messages = messages + [{"role": "user", "content": current}]
            result = await self.llm.chat_with_history_json(
                system_prompt=SYMPTOM_CONSULTATION_PROMPT,
                messages=messages,
            )
        else:
            result = await self.llm.chat_completion_json(
                system_prompt=SYMPTOM_CONSULTATION_PROMPT,
                user_message=current,
            )

        return result or {
            "symptoms_extracted": [],
            "symptom_details": {},
            "follow_up_questions": [],
            "symptom_summary": message,
            "user_context_notes": "",
        }
