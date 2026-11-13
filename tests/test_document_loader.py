import pymupdf
import pytest

from src.document_loader import DocumentError, load_pdf
from src.preprocessing import normalize_text
from tests.conftest import pdf_bytes


def test_valid_multipage_and_original(data, settings):
    doc = load_pdf("report.pdf", data, settings)
    assert doc.page_count == 2
    assert [p.number for p in doc.pages] == [1, 2]
    assert "12 million" in doc.pages[0].original_text
    assert doc.pages[1].document_id == doc.document_id


@pytest.mark.parametrize("name,payload", [("bad.pdf", b"%PDF-broken"), ("x.txt", b"%PDF-1.7"), ("empty.pdf", b"")])
def test_invalid_uploads(name, payload, settings):
    with pytest.raises(DocumentError):
        load_pdf(name, payload, settings)


def test_empty_scanned_pdf(settings):
    with pytest.raises(DocumentError, match="OCR"):
        load_pdf("empty.pdf", pdf_bytes(""), settings)


def test_partial_blank_warns(settings):
    doc = load_pdf("partial.pdf", pdf_bytes("", "Meaningful report with enough extractable information to index."), settings)
    assert len(doc.warnings) == 1 and doc.pages[0].number == 2


def test_encrypted(settings):
    with pymupdf.open() as doc:
        doc.new_page()
        raw = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="reader")
    with pytest.raises(DocumentError, match="Password"):
        load_pdf("secret.pdf", raw, settings)


def test_size_and_page_limits(data, settings):
    settings.max_pages = 1
    with pytest.raises(DocumentError, match="pages"):
        load_pdf("long.pdf", data, settings)
    settings.max_file_mb = 1
    with pytest.raises(DocumentError, match="MB"):
        load_pdf("big.pdf", b"%PDF-" + b"x" * 1048576, settings)


def test_normalization_preserves_figures():
    assert normalize_text("  USD 1,200.50\t 25%\r\n\r\n2024-01-02\x00") == "USD 1,200.50 25%\n\n2024-01-02"
