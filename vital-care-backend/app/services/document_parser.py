import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentParser:
    """Extracts text from PDF, image, and plain text files."""

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Route to correct parser based on file extension."""
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return self._extract_from_pdf(file_bytes)
        elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp"):
            return self._extract_from_image(file_bytes)
        elif ext in (".txt", ".text"):
            return self._extract_from_text(file_bytes)
        else:
            # Attempt plain text fallback
            return self._extract_from_text(file_bytes)

    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n\n".join(p for p in pages if p.strip())
        except Exception as e:
            logger.warning("pdfplumber failed (%s), trying pypdf", e)
            return self._extract_from_pdf_fallback(file_bytes)

    def _extract_from_pdf_fallback(self, file_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            return ""

    def _extract_from_image(self, file_bytes: bytes) -> str:
        try:
            from PIL import Image
            import pytesseract
            image = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.error("OCR extraction failed: %s", e)
            # TODO: integrate alternative OCR provider if pytesseract unavailable
            return ""

    def _extract_from_text(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception as e:
                logger.error("Text extraction failed: %s", e)
                return ""


def get_document_parser() -> DocumentParser:
    return DocumentParser()
