import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.doctor_visit import DoctorVisitPrepRequest, DoctorVisitPrepResponse
from app.schemas.urgency import RecommendedProviderType
from app.skills.doctor_visit_prep_skill import DoctorVisitPrepSkill
from app.services.llm_service import get_llm_service
from app.services.doctor_document_generator import get_doctor_document_generator
from app.models.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.document import UploadedDocument
from app.models.doctor_visit import DoctorVisitSummary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/prepare", response_model=DoctorVisitPrepResponse)
async def prepare_doctor_visit(
    request: DoctorVisitPrepRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a structured doctor visit preparation document from a chat session.
    """
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Aggregate session context
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    conversation = "\n".join(f"{m.role.upper()}: {m.content}" for m in messages)

    document_context = ""
    if request.include_document_findings:
        docs = (
            db.query(UploadedDocument)
            .filter(UploadedDocument.session_id == request.session_id)
            .all()
        )
        if docs:
            document_context = "\n\n".join(
                f"[Document: {d.filename}]\n{(d.extracted_text or '')[:1000]}" for d in docs
            )

    skill = DoctorVisitPrepSkill(llm=get_llm_service())
    visit_doc = await skill.run(
        symptom_summary=conversation,
        document_findings=document_context,
    )

    generator = get_doctor_document_generator()
    provider = RecommendedProviderType()
    markdown = generator.generate_markdown(
        concerns=visit_doc.concerns,
        symptom_timeline=visit_doc.symptom_timeline,
        questions_to_ask=visit_doc.questions_to_ask,
        medications_to_mention=visit_doc.important_details_to_share,
        red_flags_to_watch=[],
        recommended_provider=provider,
        summary=visit_doc.summary,
    )

    # Persist the summary
    summary_record = DoctorVisitSummary(
        session_id=request.session_id,
        summary_markdown=markdown,
    )
    db.add(summary_record)
    db.commit()

    return DoctorVisitPrepResponse(
        visit_summary_markdown=markdown,
        concerns=visit_doc.concerns,
        symptom_timeline=visit_doc.symptom_timeline,
        questions_to_ask=visit_doc.questions_to_ask,
        medications_to_mention=visit_doc.important_details_to_share,
        red_flags_to_watch=[],
        recommended_provider_type=provider,
    )
