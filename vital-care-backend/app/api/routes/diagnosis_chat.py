import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.chat import DiagnosisChatRequest, DiagnosisChatResponse
from app.agents.diagnosis_agent import DiagnosisChatAgent, get_diagnosis_agent
from app.models.database import get_db
from app.models.chat import ChatSession, ChatMessage
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=DiagnosisChatResponse)
async def diagnosis_chat(
    request: DiagnosisChatRequest,
    agent: DiagnosisChatAgent = Depends(get_diagnosis_agent),
    db: Session = Depends(get_db),
):
    """
    Main diagnosis chat endpoint. Receives a user message and returns a
    structured medical navigation response from the DiagnosisChatAgent.
    """
    try:
        # Ensure session exists
        session_id = request.session_id or str(uuid.uuid4())
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id, user_id=request.user_id, mode="diagnosis")
            db.add(session)

        # Store user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message,
        )
        db.add(user_msg)
        db.commit()

        # Run agent
        response = await agent.run(request)

        # Store assistant response
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response.response,
        )
        db.add(assistant_msg)
        db.commit()

        return response

    except Exception as e:
        logger.error("Diagnosis chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request.")
