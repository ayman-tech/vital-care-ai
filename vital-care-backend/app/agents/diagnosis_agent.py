import asyncio
import logging
from app.services.llm_service import LLMService, get_llm_service
from app.services.location_service import LocationService, get_location_service
from app.services.rag_service import RAGService, get_rag_service
from app.safety.medical_safety_guardrails import MedicalSafetyGuardrails, get_safety_guardrails, STANDARD_DISCLAIMER
from app.skills.symptom_consultation_skill import SymptomConsultationSkill
from app.skills.urgency_classification_skill import UrgencyClassificationSkill
from app.skills.possible_causes_skill import PossibleCausesSkill
from app.skills.temporary_mitigation_skill import TemporaryMitigationSkill
from app.skills.provider_type_skill import ProviderTypeSkill
from app.skills.care_locator_skill import CareLocatorSkill
from app.skills.doctor_visit_prep_skill import DoctorVisitPrepSkill
from app.skills.medical_document_skill import MedicalDocumentSkill
from app.skills.medical_jargon_skill import MedicalJargonSkill
from app.schemas.chat import DiagnosisChatRequest, DiagnosisChatResponse, DoctorVisitDocument
from app.schemas.urgency import UrgencyResult, RecommendedProviderType
from app.prompts.diagnosis_system_prompt import DIAGNOSIS_SYSTEM_PROMPT, INTENT_DETECTION_PROMPT

logger = logging.getLogger(__name__)

# Skills that are always called for symptom intents
_SYMPTOM_SKILLS = {
    "urgency_classification",
    "possible_causes",
    "temporary_mitigation",
    "provider_type",
    "care_locator",
    "doctor_visit_prep",
}


class DiagnosisChatAgent:
    """
    Skill-based agent for medical navigation and diagnosis support.

    Flow:
    1. Run safety check on user message
    2. Detect intent
    3. Call required skills (in parallel where possible)
    4. Run safety check on outputs
    5. Compose final structured response
    """

    def __init__(
        self,
        llm: LLMService,
        location_service: LocationService,
        rag_service: RAGService,
        guardrails: MedicalSafetyGuardrails,
    ):
        self.llm = llm
        self.location_service = location_service
        self.rag_service = rag_service
        self.guardrails = guardrails

        # Instantiate skills
        self.symptom_skill = SymptomConsultationSkill(llm)
        self.urgency_skill = UrgencyClassificationSkill(llm)
        self.causes_skill = PossibleCausesSkill(llm)
        self.mitigation_skill = TemporaryMitigationSkill(llm)
        self.provider_skill = ProviderTypeSkill(llm)
        self.care_locator_skill = CareLocatorSkill(location_service)
        self.visit_prep_skill = DoctorVisitPrepSkill(llm)
        self.document_skill = MedicalDocumentSkill(llm)
        self.jargon_skill = MedicalJargonSkill(llm)

    async def run(self, request: DiagnosisChatRequest) -> DiagnosisChatResponse:
        message = request.message
        user_context = request.user_context
        location = request.location.model_dump() if request.location else None

        # Step 1: Check for emergency red flags before any LLM calls
        is_emergency, red_flags = self.guardrails.check_user_message_for_emergency(message)
        if is_emergency:
            emergency_response = self.guardrails.build_emergency_response(red_flags)
            return DiagnosisChatResponse(
                response=emergency_response,
                intent="symptoms",
                urgency=UrgencyResult(
                    level="emergency",
                    reason="Emergency red flags detected in user message.",
                    red_flags=red_flags,
                    recommended_timeframe="Go to the ER now or call 911.",
                ),
                recommended_provider_type=RecommendedProviderType(
                    specialty="ER",
                    reason="Emergency symptoms require immediate emergency care.",
                ),
                safety_disclaimer=STANDARD_DISCLAIMER,
            )

        # Step 2: Detect intent
        intent_data = await self._detect_intent(message)
        intent = intent_data.get("intent", "unknown")
        required_skills: list[str] = intent_data.get("requires_skills", [])

        # Step 3: Route to appropriate skill pipeline
        response = DiagnosisChatResponse(intent=intent)  # type: ignore

        if intent in ("symptoms", "care_navigation", "general_health", "unknown"):
            response = await self._run_symptom_pipeline(
                message, user_context, location, intent
            )
        elif intent == "document_explanation":
            response = await self._run_document_pipeline(message, user_context)
        elif intent == "jargon_explanation":
            response = await self._run_jargon_pipeline(message)
        elif intent == "doctor_visit_prep":
            response = await self._run_visit_prep_pipeline(message, user_context)
        else:
            response = await self._run_symptom_pipeline(
                message, user_context, location, intent
            )

        response.intent = intent  # type: ignore
        response.safety_disclaimer = STANDARD_DISCLAIMER
        return response

    async def _detect_intent(self, message: str) -> dict:
        result = await self.llm.chat_completion_json(
            system_prompt=INTENT_DETECTION_PROMPT,
            user_message=message,
        )
        return result or {"intent": "unknown", "requires_skills": []}

    async def _run_symptom_pipeline(
        self,
        message: str,
        user_context,
        location: dict | None,
        intent: str,
    ) -> DiagnosisChatResponse:
        # Step 1: Extract symptom details
        symptom_data = await self.symptom_skill.run(message, user_context)
        symptom_summary = symptom_data.get("symptom_summary", message)
        user_context_notes = symptom_data.get("user_context_notes", "")
        follow_up_questions = symptom_data.get("follow_up_questions", [])

        # Step 2: Run parallel skill calls
        urgency_task = self.urgency_skill.run(symptom_summary)
        causes_task = self.causes_skill.run(symptom_summary, user_context_notes)
        provider_task = self.provider_skill.run(symptom_summary)

        urgency, causes, provider = await asyncio.gather(
            urgency_task, causes_task, provider_task
        )

        # Step 3: Now run skills that depend on urgency/provider
        mitigation_task = self.mitigation_skill.run(symptom_summary, urgency.level)
        care_task = self.care_locator_skill.run(provider, location)
        visit_task = self.visit_prep_skill.run(symptom_summary, user_context, provider)

        mitigation, care_suggestions, visit_doc = await asyncio.gather(
            mitigation_task, care_task, visit_task
        )

        # Step 4: Compose conversational response
        response_text = await self._compose_symptom_response(
            symptom_summary=symptom_summary,
            follow_up_questions=follow_up_questions,
            urgency=urgency,
            provider=provider,
        )

        return DiagnosisChatResponse(
            response=response_text,
            intent=intent,  # type: ignore
            urgency=urgency,
            possible_causes=causes,
            temporary_mitigation=mitigation,
            recommended_provider_type=provider,
            doctor_visit_document=visit_doc,
            nearest_care_suggestions=care_suggestions,
        )

    async def _compose_symptom_response(
        self,
        symptom_summary: str,
        follow_up_questions: list[str],
        urgency: UrgencyResult,
        provider: RecommendedProviderType,
    ) -> str:
        urgency_map = {
            "emergency": "This sounds potentially serious.",
            "urgent": "You should seek care today.",
            "soon": "I'd recommend seeing a doctor within the next day or two.",
            "routine": "This doesn't seem urgent, but a doctor visit would be helpful.",
            "self_care": "This may be manageable at home, but watch for any worsening.",
            "unknown": "Based on what you've described,",
        }
        opener = urgency_map.get(urgency.level, "Based on what you've described,")

        lines = [
            f"{opener} {urgency.reason}" if urgency.reason else opener,
            "",
            f"I'd suggest seeing a **{provider.specialty.replace('_', ' ')}** — {provider.reason}" if provider.reason else "",
        ]

        if follow_up_questions:
            lines += ["", "To better understand your situation, it would help to know:"]
            for q in follow_up_questions[:2]:
                lines.append(f"- {q}")

        lines += [
            "",
            f"*Recommended timeframe: {urgency.recommended_timeframe}*" if urgency.recommended_timeframe else "",
        ]

        return "\n".join(l for l in lines if l is not None)

    async def _run_document_pipeline(self, message: str, user_context) -> DiagnosisChatResponse:
        result = await self.document_skill.run(message, user_context)
        return DiagnosisChatResponse(
            response=result.plain_language_summary or "I wasn't able to process that document.",
            intent="document_explanation",
        )

    async def _run_jargon_pipeline(self, message: str) -> DiagnosisChatResponse:
        result = await self.jargon_skill.run(message)
        term = result.get("term", "")
        simple = result.get("simple_explanation", "")
        deeper = result.get("deeper_explanation", "")
        response_text = f"**{term}**: {simple}"
        if deeper:
            response_text += f"\n\n{deeper}"
        return DiagnosisChatResponse(
            response=response_text,
            intent="jargon_explanation",
        )

    async def _run_visit_prep_pipeline(self, message: str, user_context) -> DiagnosisChatResponse:
        visit_doc = await self.visit_prep_skill.run(message, user_context)
        return DiagnosisChatResponse(
            response=visit_doc.summary or "I've prepared a doctor visit summary for you.",
            intent="doctor_visit_prep",
            doctor_visit_document=visit_doc,
        )


def get_diagnosis_agent() -> DiagnosisChatAgent:
    return DiagnosisChatAgent(
        llm=get_llm_service(),
        location_service=get_location_service(),
        rag_service=get_rag_service(),
        guardrails=get_safety_guardrails(),
    )
