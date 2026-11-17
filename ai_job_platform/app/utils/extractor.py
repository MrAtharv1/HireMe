"""
Document text extraction utility.

Supported formats: PDF, DOCX, PNG, JPG/JPEG.
Strategy:
  1. Try native text extraction (PyMuPDF for PDF, python-docx for DOCX).
  2. If extracted text is empty or too short (< 50 chars), fall back to EasyOCR.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Tuple

import fitz  # PyMuPDF
import numpy as np
from docx import Document as DocxDocument
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy-loaded EasyOCR reader (heavyweight — loaded only when needed).
_ocr_reader = None

MIN_TEXT_LENGTH = 50  # below this we consider extraction "failed"


def _get_ocr_reader():
    """Lazy-init the EasyOCR reader so startup stays fast."""
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr

        _ocr_reader = easyocr.Reader(["en"], gpu=False)
        logger.info("EasyOCR reader initialised (CPU mode).")
    return _ocr_reader


# ─────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────


async def extract_text(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """
    Extract text from a document.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content.
    filename : str
        Original filename (used to determine type).

    Returns
    -------
    tuple[str, str]
        (extracted_text, extraction_method)
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_docx(file_bytes)
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
        return _extract_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ─────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────


def _extract_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """Try PyMuPDF text extraction; fall back to OCR on scanned pages."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text: list[str] = []

    for page in doc:
        pages_text.append(page.get_text("text"))

    full_text = "\n".join(pages_text).strip()
    doc.close()

    if len(full_text) >= MIN_TEXT_LENGTH:
        return full_text, "pymupdf"

    # Scanned PDF — render pages to images and OCR them.
    logger.info("PDF text too short (%d chars); falling back to OCR.", len(full_text))
    return _ocr_pdf(file_bytes)


def _ocr_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """Render each PDF page as an image, then run EasyOCR (memory-safe)."""
    reader = _get_ocr_reader()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_text: list[str] = []

    # Limit to first 3 pages to prevent memory spikes on free cloud hosts
    for page_idx in range(min(len(doc), 3)):
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=150)  # 150 DPI is optimal for OCR while using 75% less RAM than 300 DPI
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        img_np = np.array(img)
        results = reader.readtext(img_np, detail=0)
        all_text.append(" ".join(results))

    doc.close()
    return "\n".join(all_text).strip(), "easyocr"


def _extract_docx(file_bytes: bytes) -> Tuple[str, str]:
    """Extract text from a DOCX file using python-docx."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(paragraphs).strip()

    if len(full_text) >= MIN_TEXT_LENGTH:
        return full_text, "python-docx"

    # Very rare: DOCX with embedded images only → OCR the images.
    logger.info("DOCX text too short (%d chars); attempting image OCR.", len(full_text))
    return _ocr_docx_images(doc, full_text)


def _ocr_docx_images(doc: DocxDocument, existing_text: str) -> Tuple[str, str]:
    """Pull inline images from a DOCX and OCR them."""
    reader = _get_ocr_reader()
    ocr_parts: list[str] = [existing_text] if existing_text else []

    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            img_bytes = rel.target_part.blob
            img = Image.open(io.BytesIO(img_bytes))
            img_np = np.array(img.convert("RGB"))
            results = reader.readtext(img_np, detail=0)
            ocr_parts.append(" ".join(results))

    return "\n".join(ocr_parts).strip(), "easyocr"


def _extract_image(file_bytes: bytes) -> Tuple[str, str]:
    """Straight OCR on an image file."""
    reader = _get_ocr_reader()
    img = Image.open(io.BytesIO(file_bytes))
    img_np = np.array(img.convert("RGB"))
    results = reader.readtext(img_np, detail=0)
    return " ".join(results).strip(), "easyocr"
