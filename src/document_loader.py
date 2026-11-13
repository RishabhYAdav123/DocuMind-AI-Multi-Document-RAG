import hashlib
from pathlib import PurePath

import pymupdf

from config.settings import Settings
from src.models import Document, Page
from src.preprocessing import normalize_text


class DocumentError(ValueError):
    """Safe, actionable upload error."""


def load_pdf(filename: str, data: bytes, settings: Settings) -> Document:
    filename = PurePath(filename.replace("\\", "/")).name
    if not filename.lower().endswith(".pdf") or not data.lstrip().startswith(b"%PDF-"):
        raise DocumentError("Choose a valid PDF file; renaming another format will not work.")
    if len(data) > settings.max_file_mb * 1024 * 1024:
        raise DocumentError(f"File exceeds the {settings.max_file_mb} MB limit. Split or compress it.")
    document_id = hashlib.sha256(data).hexdigest()
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise DocumentError("Password-protected PDF: upload an unlocked copy.")
            if not pdf.page_count:
                raise DocumentError("This PDF contains no pages.")
            if pdf.page_count > settings.max_pages:
                raise DocumentError(f"PDF exceeds {settings.max_pages} pages. Split it first.")
            pages, warnings = [], []
            for number, page in enumerate(pdf, 1):
                original = page.get_text("text", sort=True)
                cleaned = normalize_text(original)
                if len(cleaned) < 30:
                    warnings.append(f"Page {number} has little or no text; OCR or manual review may be needed.")
                if cleaned:
                    pages.append(Page(document_id, filename, number, original, cleaned))
            if sum(len(p.text) for p in pages) < 30:
                raise DocumentError("No usable text found. Empty or scanned PDF: run OCR, then upload again.")
            return Document(document_id, filename, len(data), pdf.page_count, pages, warnings)
    except DocumentError:
        raise
    except Exception:
        raise DocumentError("PDF cannot be read. Export a new, uncorrupted PDF and try again.") from None
