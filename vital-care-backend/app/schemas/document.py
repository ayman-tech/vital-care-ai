from pydantic import BaseModel
from typing import Literal, Optional
from app.schemas.common import UserContext


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    extracted_text_preview: str
    status: Literal["processed", "failed"]


class DocumentExplainRequest(BaseModel):
    document_id: Optional[str] = None
    raw_text: Optional[str] = None
    user_context: Optional[UserContext] = None


class KeyFinding(BaseModel):
    finding: str
    simple_explanation: str
    normal_or_abnormal: Literal["normal", "high", "low", "unclear", "not_applicable"]
    why_it_matters: str


class MedicalTerm(BaseModel):
    term: str
    meaning: str


class DocumentExplainResponse(BaseModel):
    plain_language_summary: str
    key_findings: list[KeyFinding] = []
    medical_terms: list[MedicalTerm] = []
    questions_for_doctor: list[str] = []
    urgency_flags: list[str] = []
    disclaimer: str = (
        "This explanation is for educational purposes only and does not constitute "
        "medical advice. Consult your healthcare provider for interpretation."
    )
