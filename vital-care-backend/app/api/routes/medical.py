from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.skills.medical_jargon_skill import MedicalJargonSkill
from app.services.llm_service import get_llm_service

router = APIRouter()


class ExplainTermRequest(BaseModel):
    term: str
    context: Optional[str] = None


class ExplainTermResponse(BaseModel):
    term: str
    simple_explanation: str
    deeper_explanation: str
    example: str
    when_to_ask_a_doctor: str


@router.post("/explain-term", response_model=ExplainTermResponse)
async def explain_medical_term(request: ExplainTermRequest):
    """Explain a medical term in plain, accessible language."""
    skill = MedicalJargonSkill(llm=get_llm_service())
    result = await skill.run(request.term, request.context or "")
    return ExplainTermResponse(
        term=result.get("term", request.term),
        simple_explanation=result.get("simple_explanation", ""),
        deeper_explanation=result.get("deeper_explanation", ""),
        example=result.get("example", ""),
        when_to_ask_a_doctor=result.get("when_to_ask_a_doctor", ""),
    )
