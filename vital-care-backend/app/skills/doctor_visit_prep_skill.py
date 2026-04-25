import logging
from app.services.llm_service import LLMService
from app.prompts.doctor_visit_prompt import DOCTOR_VISIT_PROMPT, DOCTOR_VISIT_MARKDOWN_PROMPT
from app.schemas.chat import DoctorVisitDocument
from app.schemas.urgency import RecommendedProviderType
from app.schemas.common import UserContext

logger = logging.getLogger(__name__)


class DoctorVisitPrepSkill:
    """Generates structured doctor visit preparation documents."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(
        self,
        symptom_summary: str,
        user_context: UserContext | None = None,
        provider_type: RecommendedProviderType | None = None,
        document_findings: str = "",
    ) -> DoctorVisitDocument:
        context_parts = [f"Symptom summary: {symptom_summary}"]
        if user_context:
            if user_context.medications:
                context_parts.append(f"Current medications: {', '.join(user_context.medications)}")
            if user_context.allergies:
                context_parts.append(f"Known allergies: {', '.join(user_context.allergies)}")
            if user_context.known_conditions:
                context_parts.append(f"Known conditions: {', '.join(user_context.known_conditions)}")
        if provider_type:
            context_parts.append(f"Recommended provider: {provider_type.specialty}")
        if document_findings:
            context_parts.append(f"Document findings: {document_findings}")

        raw = await self.llm.chat_completion_json(
            system_prompt=DOCTOR_VISIT_PROMPT,
            user_message="\n".join(context_parts),
        )
        try:
            return DoctorVisitDocument(
                summary=raw.get("summary", ""),
                concerns=raw.get("concerns", []),
                symptom_timeline=raw.get("symptom_timeline", []),
                questions_to_ask=raw.get("questions_to_ask", []),
                important_details_to_share=raw.get("important_details_to_share", []),
            )
        except Exception as e:
            logger.error("DoctorVisitPrepSkill parse error: %s", e)
            return DoctorVisitDocument()

    async def generate_markdown(
        self,
        symptom_summary: str,
        user_context: UserContext | None = None,
        provider_type: RecommendedProviderType | None = None,
    ) -> str:
        context_parts = [f"Symptom summary: {symptom_summary}"]
        if user_context:
            if user_context.medications:
                context_parts.append(f"Medications: {', '.join(user_context.medications)}")
            if user_context.allergies:
                context_parts.append(f"Allergies: {', '.join(user_context.allergies)}")
        if provider_type:
            context_parts.append(f"Recommended provider: {provider_type.specialty} — {provider_type.reason}")

        return await self.llm.chat_completion(
            system_prompt=DOCTOR_VISIT_MARKDOWN_PROMPT,
            user_message="\n".join(context_parts),
            json_mode=False,
        )
