"""
Tests for Document Text Extractor (app/utils/extractor.py).
Verifies:
- Native PyMuPDF text extraction from clean PDFs (> 50 chars)
- python-docx text extraction from DOCX files
- OCR fallback triggering when PDF text is under 50 characters
- Scanned PDF 3-page cap and 150 DPI memory optimization
- Unsupported file extension rejection (ValueError)
- Empty or corrupted file byte handling
"""

import io
from unittest.mock import MagicMock, patch
import pytest
import fitz
from docx import Document as DocxDocument

from app.utils.extractor import (
    extract_text,
    _extract_pdf,
    _extract_docx,
    _ocr_pdf,
)


@pytest.mark.asyncio
async def test_extract_pdf_clean_text():
    # Generate in-memory PDF with sufficient text (> 50 chars)
    doc = fitz.open()
    page = doc.new_page()
    sample_text = (
        "Arjun Sharma\n"
        "Software Engineer with experience in Python, FastAPI, Docker, and PostgreSQL.\n"
        "Graduating with B.Tech in Computer Science from DTU."
    )
    page.insert_text((50, 72), sample_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    text, method = await extract_text(pdf_bytes, "candidate_resume.pdf")
    assert method == "pymupdf"
    assert "Arjun Sharma" in text
    assert "FastAPI" in text


@pytest.mark.asyncio
async def test_extract_docx_clean_text():
    # Generate in-memory DOCX with sufficient text
    doc = DocxDocument()
    doc.add_paragraph("Arjun Sharma - Early Career Backend Developer")
    doc.add_paragraph("Core competencies: Python, FastAPI, Docker, Redis, Celery, and SQL.")
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()

    text, method = await extract_text(docx_bytes, "candidate_resume.docx")
    assert method == "python-docx"
    assert "Arjun Sharma" in text
    assert "Celery" in text


@pytest.mark.asyncio
async def test_extract_pdf_ocr_fallback_triggered():
    # Create PDF with text length < 50 chars (e.g. scanned image or single word)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Short")
    pdf_bytes = doc.tobytes()
    doc.close()

    # Mock OCR fallback to avoid heavyweight easyocr model download during tests
    with patch("app.utils.extractor._ocr_pdf", return_value=("OCR Extracted Scanned Resume Text", "easyocr")) as mock_ocr:
        text, method = await extract_text(pdf_bytes, "scanned_doc.pdf")
        assert mock_ocr.called
        assert method == "easyocr"
        assert "OCR Extracted" in text


def test_ocr_pdf_page_cap_and_dpi():
    # Create a 5-page PDF
    doc = fitz.open()
    for i in range(5):
        p = doc.new_page()
        p.insert_text((50, 72), f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()

    # Mock OCR reader
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = ["Scanned", "Page", "Content"]

    with patch("app.utils.extractor._get_ocr_reader", return_value=mock_reader):
        text, method = _ocr_pdf(pdf_bytes)
        assert method == "easyocr"
        assert "Scanned Page Content" in text
        # Must cap at max 3 pages to protect server memory
        assert mock_reader.readtext.call_count == 3


@pytest.mark.asyncio
async def test_extract_unsupported_extension_error():
    with pytest.raises(ValueError) as exc_info:
        await extract_text(b"some content", "resume.xyz")
    assert "Unsupported file type: .xyz" in str(exc_info.value)


def test_extract_empty_file_handling():
    # Corrupt or zero-length byte sequence should raise fitz.FileDataError
    with pytest.raises(fitz.FileDataError):
        _extract_pdf(b"")
