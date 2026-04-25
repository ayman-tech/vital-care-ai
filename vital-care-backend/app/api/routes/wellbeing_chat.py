import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.schemas.wellbeing import (
    WellbeingChatRequest, WellbeingChatResponse,
    PanicRequest, PanicResponse,
    WellbeingReportRequest, ConsentRequest,
    EscalationSummary,
)
from app.agents.wellbeing_agent import WellbeingAgent, get_wellbeing_agent
from app.services.pdf_generator import get_pdf_generator
from app.models.database import get_db
from app.models.wellbeing import WellbeingSession, WellbeingMessage

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_or_create_session(
    session_id: str | None,
    user_id: str | None,
    db: Session,
) -> WellbeingSession:
    sid = session_id or str(uuid.uuid4())
    session = db.query(WellbeingSession).filter(WellbeingSession.id == sid).first()
    if not session:
        session = WellbeingSession(id=sid, user_id=user_id)
        db.add(session)
        db.flush()
    return session


@router.post("/chat", response_model=WellbeingChatResponse)
async def wellbeing_chat(
    request: WellbeingChatRequest,
    agent: WellbeingAgent = Depends(get_wellbeing_agent),
    db: Session = Depends(get_db),
):
    """
    Main wellbeing chat endpoint.
    Handles consent protocol, mood/stress tracking, severity assessment,
    and automatic escalation when CRITICAL severity is detected.
    """
    session = _get_or_create_session(request.session_id, request.user_id, db)

    # Client may pass consent_given explicitly (e.g. after UI consent screen)
    if request.consent_given is not None and not session.consent_given:
        session.consent_given = request.consent_given

    messages = (
        db.query(WellbeingMessage)
        .filter(WellbeingMessage.session_id == session.id)
        .order_by(WellbeingMessage.created_at)
        .all()
    )

    # Store user message
    user_msg = WellbeingMessage(
        session_id=session.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    db.flush()
    messages_with_new = list(messages) + [user_msg]

    response = await agent.run(request, session, messages_with_new)

    # Store assistant response
    assistant_msg = WellbeingMessage(
        session_id=session.id,
        role="assistant",
        content=response.response,
        severity_at_time=response.severity,
        mood_score=str(response.agent_data.mood_score) if response.agent_data else None,
        stress_score=str(response.agent_data.stress_score) if response.agent_data else None,
    )
    db.add(assistant_msg)

    # Persist updated session state
    db.add(session)
    db.commit()

    response.session_id = session.id
    return response


@router.post("/consent")
async def update_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db),
):
    """Update session consent status explicitly."""
    session = _get_or_create_session(request.session_id, request.user_id, db)
    session.consent_given = request.consent_given
    db.add(session)
    db.commit()
    return {
        "session_id": session.id,
        "consent_given": session.consent_given,
        "message": "Consent recorded. Let's talk 💙" if request.consent_given
                   else "Understood. Operating without tracking this session.",
    }


@router.post("/panic", response_model=PanicResponse)
async def panic_button(
    request: PanicRequest,
    agent: WellbeingAgent = Depends(get_wellbeing_agent),
    db: Session = Depends(get_db),
):
    """
    Panic button endpoint — immediate escalation.
    Triggered when the user presses 'I'm Not Okay'.
    """
    session = db.query(WellbeingSession).filter(WellbeingSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    messages = (
        db.query(WellbeingMessage)
        .filter(WellbeingMessage.session_id == request.session_id)
        .order_by(WellbeingMessage.created_at)
        .all()
    )

    escalation = await agent.handle_panic(
        session=session,
        messages=messages,
        location=request.location,
    )

    db.add(session)
    db.commit()

    return PanicResponse(
        message=(
            "I hear you, and I'm really glad you told me. You don't have to figure this out alone. "
            "I've pulled together everything we've talked about and found support options for you. "
            "Please reach out to one of these resources right now — you matter. 💙\n\n"
            "**988 Suicide & Crisis Lifeline: call or text 988**\n"
            "**Crisis Text Line: Text HOME to 741741**"
        ),
        escalation_summary=escalation,
        pdf_available=True,
    )


@router.post("/report")
async def generate_report(
    request: WellbeingReportRequest,
    db: Session = Depends(get_db),
):
    """
    Generate and return a 1-page PDF well-being summary report.
    Returns the PDF as a downloadable file.
    """
    from app.schemas.wellbeing import MoodPoint, StressPoint

    session = db.query(WellbeingSession).filter(WellbeingSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    messages = (
        db.query(WellbeingMessage)
        .filter(WellbeingMessage.session_id == request.session_id)
        .order_by(WellbeingMessage.created_at)
        .all()
    )

    from app.agents.wellbeing_agent import _get_top_tags, _extract_key_moments
    from datetime import datetime, timezone

    mood_timeline = [MoodPoint(**p) for p in session.mood_history]
    stress_timeline = [StressPoint(**p) for p in session.stress_history]

    if messages:
        start = messages[0].created_at
        duration = int((datetime.now(timezone.utc) - start.replace(tzinfo=timezone.utc)).total_seconds() / 60)
    else:
        duration = 0

    summary = EscalationSummary(
        session_id=session.id,
        duration_minutes=duration,
        mood_timeline=mood_timeline,
        stress_timeline=stress_timeline,
        severity_progression=session.severity_log or [session.severity],
        top_tags=_get_top_tags(session.tags),
        key_moments=_extract_key_moments(messages),
    )

    generator = get_pdf_generator()
    pdf_bytes = generator.generate(summary, session.id)

    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=wellbeing_report_{session.id[:8]}.pdf"},
    )
