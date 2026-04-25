import logging
from app.services.llm_service import LLMService
from app.prompts.medical_document_prompt import MEDICAL_DOCUMENT_PROMPT
from app.schemas.document import DocumentExplainResponse, KeyFinding, MedicalTerm
from app.schemas.common import UserContext

logger = logging.getLogger(__name__)


class MedicalDocumentSkill:
    """Explains medical documents in plain language."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(
        self,
        document_text: str,
        user_context: UserContext | None = None,
    ) -> DocumentExplainResponse:
        context_str = ""
        if user_context:
            parts = []
            if user_context.age:
                parts.append(f"Age: {user_context.age}")
            if user_context.sex:
                parts.append(f"Sex: {user_context.sex}")
            if user_context.known_conditions:
                parts.append(f"Known conditions: {', '.join(user_context.known_conditions)}")
            if user_context.medications:
                parts.append(f"Medications: {', '.join(user_context.medications)}")
            if parts:
                context_str = f"\n\nPatient context: {'; '.join(parts)}"

        raw = await self.llm.chat_completion_json(
            system_prompt=MEDICAL_DOCUMENT_PROMPT,
            user_message=f"Medical document text:\n\n{document_text}{context_str}",
            max_tokens=3000,
        )

        try:
            return DocumentExplainResponse(
                plain_language_summary=raw.get("plain_language_summary", ""),
                key_findings=[
                    KeyFinding(**f) for f in raw.get("key_findings", [])
                    if isinstance(f, dict)
                ],
                medical_terms=[
                    MedicalTerm(**t) for t in raw.get("medical_terms", [])
                    if isinstance(t, dict)
                ],
                questions_for_doctor=raw.get("questions_for_doctor", []),
                urgency_flags=raw.get("urgency_flags", []),
                disclaimer=raw.get(
                    "disclaimer",
                    "This explanation is for educational purposes only. Your healthcare provider should interpret your results."
                ),
            )
        except Exception as e:
            logger.error("MedicalDocumentSkill parse error: %s", e)
            return DocumentExplainResponse(
                plain_language_summary="Unable to process document at this time.",
            )
