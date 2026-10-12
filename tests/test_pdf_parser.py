import pytest

from src.pdf_parser import PDFExtractionError, extract_pdf_document


def test_empty_pdf_bytes_raise_clear_error():
    with pytest.raises(PDFExtractionError):
        extract_pdf_document(b"", "empty.pdf")
