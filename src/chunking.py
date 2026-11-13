from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.models import Chunk, Document


def chunk_document(document: Document, size: int = 1000, overlap: int = 200) -> list[Chunk]:
    if size < 1 or not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap, add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""], strip_whitespace=True,
    )
    chunks = []
    for page in document.pages:
        for i, part in enumerate(splitter.create_documents([page.text])):
            if part.page_content.strip():
                chunks.append(Chunk(
                    f"{document.document_id}:p{page.number}:c{i}", document.document_id,
                    document.filename, page.number, part.page_content, part.metadata["start_index"],
                ))
    return chunks
