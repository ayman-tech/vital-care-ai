import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas.document import DocumentUploadResponse, DocumentExplainRequest, DocumentExplainResponse
from app.services.document_parser import get_document_parser
from app.skills.medical_document_skill import MedicalDocumentSkill
from app.services.llm_service import get_llm_service
from app.models.database import get_db
from app.models.document import UploadedDocument

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png", "image/jpeg", "image/jpg",
    "image/tiff", "image/bmp", "image/gif", "image/webp",
    "text/plain",
}
PREVIEW_LENGTH = 500


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a medical document (PDF, image, or text).
    Extracts text and stores metadata for later use in chat sessions.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, images, plain text.",
        )

    file_bytes = await file.read()
    parser = get_document_parser()
    extracted = parser.extract_text(file_bytes, file.filename or "document")

    doc = UploadedDocument(
        id=str(uuid.uuid4()),
        filename=file.filename or "document",
        file_type=file.content_type or "unknown",
        extracted_text=extracted,
    )
    db.add(doc)
    db.commit()

    status = "processed" if extracted else "failed"
    preview = extracted[:PREVIEW_LENGTH] + ("..." if len(extracted) > PREVIEW_LENGTH else "")

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        extracted_text_preview=preview,
        status=status,
    )


@router.post("/explain", response_model=DocumentExplainResponse)
async def explain_document(request: DocumentExplainRequest, db: Session = Depends(get_db)):
    """
    Explain a medical document in plain language.
    Supply either a document_id (previously uploaded) or raw_text directly.
    """
    document_text = request.raw_text or ""

    if request.document_id and not document_text:
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        document_text = doc.extracted_text or ""

    if not document_text.strip():
        raise HTTPException(status_code=400, detail="No document text provided or extracted.")

    skill = MedicalDocumentSkill(llm=get_llm_service())
    return await skill.run(document_text, request.user_context)
