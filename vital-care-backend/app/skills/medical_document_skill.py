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

        summary = raw.get("plain_language_summary", "")
        if not summary:
            logger.error("MedicalDocumentSkill: empty summary from LLM, raw=%s", raw)
            return DocumentExplainResponse(
                plain_language_summary="I was unable to interpret this document. Please try again or paste the text directly.",
            )

        _VALID_STATUS = {"normal", "high", "low", "unclear", "not_applicable"}

        key_findings = []
        for f in raw.get("key_findings", []):
            if not isinstance(f, dict):
                continue
            status = f.get("normal_or_abnormal", "unclear")
            if status not in _VALID_STATUS:
                f["normal_or_abnormal"] = "unclear"
            try:
                key_findings.append(KeyFinding(**f))
            except Exception as e:
                logger.warning("Skipping invalid key_finding %s: %s", f, e)

        medical_terms = []
        for t in raw.get("medical_terms", []):
            if not isinstance(t, dict):
                continue
            try:
                medical_terms.append(MedicalTerm(**t))
            except Exception as e:
                logger.warning("Skipping invalid medical_term %s: %s", t, e)

        return DocumentExplainResponse(
            plain_language_summary=summary,
            key_findings=key_findings,
            medical_terms=medical_terms,
            questions_for_doctor=raw.get("questions_for_doctor", []),
            urgency_flags=raw.get("urgency_flags", []),
            disclaimer=raw.get(
                "disclaimer",
                "This explanation is for educational purposes only. Your healthcare provider should interpret your results."
            ),
        )
