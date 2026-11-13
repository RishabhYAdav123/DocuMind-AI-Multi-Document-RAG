import logging
import re

from config.settings import Settings
from src.chunking import chunk_document
from src.conversation_memory import ConversationMemory
from src.document_loader import DocumentError, load_pdf
from src.embeddings import Embedder
from src.llm_service import LLM
from src.models import Answer, Citation, Document, GeneratedAnswer, Hit, Rewrite
from src.vector_store import VectorStore

LOGGER = logging.getLogger(__name__)
ABSTENTION = "The uploaded documents do not contain enough information to answer this question reliably."


def needs_reformulation(question: str) -> bool:
    """Only dependent references need LLM rewriting; clear standalone queries go straight to search."""
    return bool(re.search(r"\b(it|its|they|their|them|this|that|these|those|same|previous|former|latter|he|she|his|her)\b",
                          question, re.IGNORECASE)
                or re.match(r"\s*(what about|how about|and\b|also\b|compared to\b)", question, re.IGNORECASE))


def canonical(text: str) -> str:
    return " ".join(text.split())


def validate_answer(result: GeneratedAnswer, hits: list[Hit], query: str) -> Answer:
    """Validate provenance and exact evidence, not semantic entailment."""
    if result.status != "answered" or not result.claims:
        return Answer(ABSTENTION, "insufficient", resolved_question=query)
    sources = {f"S{i}": hit for i, hit in enumerate(hits, 1)}
    citations, lines, seen = [], [], set()
    for claim in result.claims:
        labels = []
        for evidence in claim.evidence:
            hit = sources.get(evidence.source_id)
            quote = canonical(evidence.quote)
            if hit is None or quote not in canonical(hit.chunk.text):
                return Answer("I could not verify the answer's source evidence. Please rephrase or retry.",
                              "invalid_citation", resolved_question=query)
            key = (evidence.source_id, quote)
            if key not in seen:
                citations.append(Citation(evidence.source_id, hit.chunk, quote, hit.score))
                seen.add(key)
            if evidence.source_id not in labels:
                labels.append(evidence.source_id)
        lines.append(claim.text + " " + " ".join(f"[{label}]" for label in labels))
    return Answer("\n\n".join(lines), "answered", citations, query)


class RAGPipeline:
    def __init__(self, settings: Settings, embedder: Embedder, llm: LLM):
        self.settings, self.llm = settings, llm
        self.store = VectorStore(embedder)
        self.documents: dict[str, Document] = {}
        self.memory = ConversationMemory(settings.history_turns)

    def ingest(self, filename: str, data: bytes) -> tuple[Document, bool]:
        doc = load_pdf(filename, data, self.settings)
        if doc.document_id in self.documents:
            return self.documents[doc.document_id], False
        if len(self.documents) >= self.settings.max_documents:
            raise DocumentError("Document limit reached. Clear documents to start a new collection.")
        chunks = chunk_document(doc, self.settings.chunk_size, self.settings.chunk_overlap)
        if len(self.store.chunks) + len(chunks) > self.settings.max_chunks:
            raise DocumentError("Collection chunk limit reached. Upload fewer or shorter PDFs.")
        self.store.add(chunks)
        self.documents[doc.document_id] = doc
        LOGGER.info("Indexed document: pages=%d chunks=%d", doc.page_count, len(chunks))
        return doc, True

    def ask(self, question: str) -> Answer:
        question = question.strip()
        if not question or len(question) > 2000:
            raise ValueError("Enter a question between 1 and 2,000 characters.")
        if not self.store.chunks:
            return Answer("Upload and process PDFs before asking a question.", "no_documents")
        history = self.memory.context()
        # Standalone topics are already valid retrieval queries; rewriting them can
        # introduce unnecessary ambiguity and consumes extra quota.
        rewrite = (self.llm.rewrite(question, history) if needs_reformulation(question)
                   else Rewrite(question=question))
        if rewrite.needs_clarification:
            answer = Answer("Please specify the company, topic or period you mean.", "clarification")
        else:
            hits = self.store.search(rewrite.question, self.settings.top_k, self.settings.min_similarity)
            answer = (validate_answer(self.llm.answer(rewrite.question, hits), hits, rewrite.question)
                      if hits else Answer(ABSTENTION, "insufficient", resolved_question=rewrite.question))
        self.memory.add(question, answer)
        return answer

    def clear_documents(self) -> None:
        self.store.clear()
        self.documents.clear()
        self.memory.clear()
