from pydantic import BaseModel
from typing import Literal, Optional


UrgencyLevel = Literal["emergency", "urgent", "soon", "routine", "self_care", "unknown"]
LikelihoodCategory = Literal["more_likely", "possible", "less_likely", "cannot_rule_out"]


class UrgencyResult(BaseModel):
    level: UrgencyLevel = "unknown"
    reason: str = ""
    red_flags: list[str] = []
    recommended_timeframe: str = ""


class PossibleCause(BaseModel):
    name: str
    likelihood: LikelihoodCategory
    reasoning: str
    disclaimer: str = "This is not a diagnosis. Please consult a healthcare professional."


class TemporaryMitigation(BaseModel):
    title: str
    description: str
    safety_note: str


class RecommendedProviderType(BaseModel):
    specialty: Literal[
        "ER", "urgent_care", "primary_care", "pediatrician", "ophthalmologist",
        "orthopedist", "gynecologist", "dermatologist", "cardiologist",
        "neurologist", "gastroenterologist", "ENT", "dentist",
        "psychiatrist", "therapist", "other", "unknown"
    ] = "unknown"
    reason: str = ""
