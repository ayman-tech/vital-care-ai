import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.chat import DiagnosisChatRequest, DiagnosisChatResponse
from app.agents.diagnosis_agent import DiagnosisChatAgent, get_diagnosis_agent
from app.models.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.document import UploadedDocument
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

        # Load any documents uploaded in this session and prepend as context
        docs = (
            db.query(UploadedDocument)
            .filter(UploadedDocument.session_id == session_id)
            .order_by(UploadedDocument.created_at)
            .all()
        )
        doc_messages: list[dict] = []
        for d in docs:
            if d.extracted_text:
                doc_messages.append({
                    "role": "user",
                    "content": f"[Uploaded document: {d.filename}]\n\n{d.extracted_text[:4000]}",
                })
                doc_messages.append({
                    "role": "assistant",
                    "content": f"I've received your document '{d.filename}'. I can explain it or answer questions about it.",
                })

        # Load prior messages for context (last 20 = 10 turns)
        prior = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )
        chat_messages = [{"role": m.role, "content": m.content} for m in prior][-20:]
        request.history = doc_messages + chat_messages

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
        response.session_id = session_id

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
