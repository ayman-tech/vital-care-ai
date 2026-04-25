from pydantic import BaseModel
from typing import Literal, Optional


SeverityLevel = Literal["LOW", "MODERATE", "CRITICAL"]


class MoodPoint(BaseModel):
    timestamp: str
    score: int
    note: str = ""


class StressPoint(BaseModel):
    timestamp: str
    score: int


class TagEntry(BaseModel):
    tag: str
    count: int
    severity: Literal["low", "moderate", "critical"]


class AgentData(BaseModel):
    """Parsed from the <!--AGENT_DATA ... AGENT_DATA--> block in LLM responses."""
    tags: list[str] = []
    severity: SeverityLevel = "LOW"
    mood_score: int = 5
    stress_score: int = 5
    timestamp: str = ""


class WellbeingChatRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    message: str
    consent_given: Optional[bool] = None  # client sends this after consent is obtained


class WellbeingChatResponse(BaseModel):
    response: str
    session_id: str
    severity: SeverityLevel = "LOW"
    agent_data: Optional[AgentData] = None
    escalated: bool = False
    escalation_payload: Optional[dict] = None
    status: str = "active"


class PanicRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    location: Optional[dict] = None


class EscalationSummary(BaseModel):
    session_id: str
    duration_minutes: int
    mood_timeline: list[MoodPoint] = []
    stress_timeline: list[StressPoint] = []
    severity_progression: list[str] = []
    top_tags: list[TagEntry] = []
    key_moments: list[str] = []
    recommended_specialties: list[str] = [
        "mental health", "counseling", "psychiatry", "therapy"
    ]
    immediate_resources: list[str] = [
        "988 Suicide & Crisis Lifeline: call or text 988",
        "Crisis Text Line: Text HOME to 741741",
        "SAMHSA Helpline: 1-800-662-4357",
    ]
    nearby_providers: list[dict] = []


class PanicResponse(BaseModel):
    message: str
    escalation_summary: EscalationSummary
    pdf_available: bool = True
    status: str = "escalated"


class WellbeingReportRequest(BaseModel):
    session_id: str


class ConsentRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    consent_given: bool
