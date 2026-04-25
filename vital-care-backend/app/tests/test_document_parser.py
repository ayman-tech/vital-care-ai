import pytest
from app.services.document_parser import DocumentParser


@pytest.fixture
def parser():
    return DocumentParser()


def test_extract_plain_text(parser):
    content = "This is a lab result. WBC: 5.5, RBC: 4.2"
    result = parser.extract_text(content.encode("utf-8"), "report.txt")
    assert "WBC" in result
    assert "RBC" in result


def test_extract_utf8_text(parser):
    content = "Patient: John Doe\nHemoglobin A1c: 6.5%"
    result = parser.extract_text(content.encode("utf-8"), "result.txt")
    assert "Hemoglobin" in result


def test_extract_latin1_text(parser):
    content = "Diagnosis: ánemia leve"
    result = parser.extract_text(content.encode("latin-1"), "diag.txt")
    assert len(result) > 0


def test_unknown_extension_fallback(parser):
    content = "Some medical text content"
    result = parser.extract_text(content.encode("utf-8"), "file.xyz")
    assert "medical text" in result
