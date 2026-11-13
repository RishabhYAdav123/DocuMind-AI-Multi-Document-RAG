import pytest

from src.chunking import chunk_document
from src.models import Document, Page


def document(text):
    return Document("id", "test.pdf", 100, 1, [Page("id", "test.pdf", 1, text, text)])


def test_empty_and_short():
    assert chunk_document(document("")) == []
    chunks = chunk_document(document("Revenue is USD 12 million."))
    assert len(chunks) == 1 and chunks[0].page == 1 and chunks[0].filename == "test.pdf"


def test_long_overlap_traceability():
    text = "".join(chr(0x400 + i) for i in range(500))
    chunks = chunk_document(document(text), 100, 20)
    assert len(chunks) > 1
    assert chunks[0].text[-20:] == chunks[1].text[:20]
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    for chunk in chunks:
        assert len(chunk.text) <= 100
        assert text[chunk.start:chunk.start + len(chunk.text)] == chunk.text


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_document(document("x"), 10, 10)
