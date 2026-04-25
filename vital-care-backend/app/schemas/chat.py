from pydantic import BaseModel
from typing import Literal, Optional
from app.schemas.common import LocationContext, UserContext
from app.schemas.urgency import UrgencyResult, PossibleCause, TemporaryMitigation, RecommendedProviderType


ChatIntent = Literal[
    "symptoms", "document_explanation", "jargon_explanation",
    "doctor_visit_prep", "care_navigation", "general_health", "unknown"
]


class NearestCareSuggestion(BaseModel):
    name: str
    type: str
    address: str
    distance: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None


class DoctorVisitDocument(BaseModel):
    summary: str = ""
    concerns: list[str] = []
    symptom_timeline: list[str] = []
    questions_to_ask: list[str] = []
    important_details_to_share: list[str] = []


class DiagnosisChatRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    message: str
    location: Optional[LocationContext] = None
    user_context: Optional[UserContext] = None
    history: list[dict] = []


class DiagnosisChatResponse(BaseModel):
    session_id: Optional[str] = None
    response: str
    intent: ChatIntent = "unknown"
    urgency: UrgencyResult = UrgencyResult()
    possible_causes: list[PossibleCause] = []
    temporary_mitigation: list[TemporaryMitigation] = []
    recommended_provider_type: RecommendedProviderType = RecommendedProviderType()
    doctor_visit_document: DoctorVisitDocument = DoctorVisitDocument()
    nearest_care_suggestions: list[NearestCareSuggestion] = []
    safety_disclaimer: str = (
        "I am not a doctor and cannot diagnose you. This information is for educational "
        "purposes only. Always consult a qualified healthcare professional for medical advice."
    )


class WellbeingChatRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    message: str


class WellbeingChatResponse(BaseModel):
    response: str = "Wellbeing chat module is not configured yet."
    status: str = "placeholder"
