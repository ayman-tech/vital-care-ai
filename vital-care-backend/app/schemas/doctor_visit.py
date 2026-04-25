from pydantic import BaseModel
from app.schemas.urgency import RecommendedProviderType


class DoctorVisitPrepRequest(BaseModel):
    session_id: str
    include_document_findings: bool = True


class DoctorVisitPrepResponse(BaseModel):
    visit_summary_markdown: str
    concerns: list[str] = []
    symptom_timeline: list[str] = []
    questions_to_ask: list[str] = []
    medications_to_mention: list[str] = []
    red_flags_to_watch: list[str] = []
    recommended_provider_type: RecommendedProviderType = RecommendedProviderType()
