"""PDF text extraction helpers for underwriting submissions."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from pypdf import PdfReader


class PDFExtractionError(ValueError):
    """Raised when a PDF cannot provide usable text for the prototype."""


def extract_pdf_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract page-level text while preserving the original page number."""

    if not file_bytes:
        raise PDFExtractionError(f"{filename}: empty PDF file")

    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise PDFExtractionError(f"{filename}: PDF를 읽을 수 없습니다.") from exc

    pages: List[Dict[str, Any]] = []
    total_chars = 0

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
        if text:
            total_chars += len(text)
            pages.append({"page": page_number, "text": text})

    if not pages:
        raise PDFExtractionError(
            f"{filename}: 추출 가능한 텍스트가 없습니다. "
            "현재 프로토타입은 스캔 이미지 PDF의 OCR을 지원하지 않습니다."
        )

    return {
        "filename": filename,
        "page_count": len(reader.pages),
        "text_page_count": len(pages),
        "character_count": total_chars,
        "pages": pages,
    }


def build_document_preview(document: Dict[str, Any], max_chars: int = 1600) -> str:
    """Return a compact page-labelled preview for the Streamlit UI."""

    chunks: List[str] = []
    remaining = max_chars

    for page in document.get("pages", []):
        label = f"[p.{page['page']}]\n"
        text = str(page.get("text") or "")
        chunk = label + text
        if len(chunk) > remaining:
            chunks.append(chunk[:remaining] + "...")
            break
        chunks.append(chunk)
        remaining -= len(chunk)
        if remaining <= 0:
            break

    return "\n\n".join(chunks)
