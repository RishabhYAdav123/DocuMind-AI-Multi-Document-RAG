"""Run with: python -m streamlit run app.py"""
import logging
from pathlib import Path

import streamlit as st

from config.settings import Settings
from src.document_loader import DocumentError
from src.embeddings import get_embedder
from src.llm_service import GeminiService, ProviderError
from src.rag_pipeline import RAGPipeline

ROOT = Path(__file__).parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# Third-party request logs may contain document text or query parameters.
for name in ("httpx", "httpcore", "google_genai"):
    logging.getLogger(name).setLevel(logging.ERROR)

st.set_page_config(page_title="DocuMind AI", page_icon="📚", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets/custom.css').read_text()}</style>", unsafe_allow_html=True)
try:
    settings = Settings()
except Exception:
    st.error("Invalid configuration. Check numeric limits and CHUNK_OVERLAP < CHUNK_SIZE in .env.")
    st.stop()

if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0


def pipeline() -> RAGPipeline:
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = RAGPipeline(settings, get_embedder(settings.embedding_model), GeminiService(settings))
    return st.session_state.pipeline


def process(files: list[tuple[str, bytes]]) -> None:
    progress = st.progress(0, text="Loading the embedding model…")
    try:
        engine = pipeline()
    except Exception:
        progress.empty()
        st.error("Embedding model could not load. Check internet access for the first download and available memory.")
        return
    for i, (filename, data) in enumerate(files):
        progress.progress(i / len(files), text=f"Processing {filename}")
        try:
            doc, added = engine.ingest(filename, data)
            st.success(f"{doc.filename}: {'indexed' if added else 'already indexed (duplicate skipped)'}")
            for warning in doc.warnings:
                st.warning(warning)
        except DocumentError as error:
            st.error(f"{filename}: {error}")
        except Exception:
            st.error(f"{filename}: indexing failed. Check the embedding model and available memory, then retry.")
    progress.progress(1.0, text="Processing complete. Indexed documents are listed below.")


with st.sidebar:
    st.markdown("## ◈ DocuMind AI")
    st.caption("YOUR DOCUMENT WORKSPACE")
    uploaded = st.file_uploader("Add PDF reports", type=["pdf"], accept_multiple_files=True,
                               key=f"uploads_{st.session_state.uploader_version}",
                               help=f"Up to {settings.max_file_mb} MB per PDF. Text-based PDFs; OCR is not included.")
    if uploaded:
        for upload in uploaded:
            st.caption(f"{upload.name} · {upload.size / 1024:.1f} KB · awaiting processing")
    if st.button("Process Documents", type="primary", disabled=not uploaded, use_container_width=True):
        process([(upload.name, upload.getvalue()) for upload in uploaded])
    if st.button("Try three sample reports", use_container_width=True):
        process([(p.name, p.read_bytes()) for p in sorted((ROOT / "sample_documents").glob("*.pdf"))])
    engine = st.session_state.get("pipeline")
    st.divider()
    st.markdown("**Indexed documents**")
    if engine and engine.documents:
        for doc in engine.documents.values():
            with st.expander(f"✓ {doc.filename}"):
                st.caption(f"{doc.page_count} pages · {doc.size_bytes / 1024:.1f} KB · ID {doc.document_id[:8]}")
                st.caption(f"{len(doc.pages)} pages with extracted text")
                for warning in doc.warnings:
                    st.warning(warning)
    else:
        st.caption("Your collection is empty.")
    left, right = st.columns(2)
    if left.button("Clear Chat", use_container_width=True):
        if engine:
            engine.memory.clear()
        st.rerun()
    if right.button("Clear Documents", use_container_width=True):
        if engine:
            engine.clear_documents()
        st.session_state.uploader_version += 1
        st.rerun()
    with st.expander("Retrieval settings"):
        top_k = st.slider("Sources to retrieve", 1, 20, settings.top_k)
        minimum = st.slider("Minimum similarity", -1.0, 1.0, settings.min_similarity, 0.05)
        st.caption("Similarity is a retrieval signal, not a confidence probability. Defaults are starting values.")
        st.caption(f"Provider: Gemini · Model: {settings.llm_model}")
        if engine:
            engine.settings.top_k, engine.settings.min_similarity = top_k, minimum
    st.caption("Only retrieved passages and questions go to Gemini. Recent chat is sent for question interpretation.")

st.caption("DOCUMENT INTELLIGENCE / LOCAL WORKSPACE")
st.title("A clearer view of your documents.")
st.markdown("### DocuMind AI")
st.write("Ask intelligent questions across your documents.")
engine = st.session_state.get("pipeline")
ready = bool(engine and engine.store.chunks)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Documents", len(engine.documents) if engine else 0)
col2.metric("Indexed pages", len({(c.document_id, c.page) for c in engine.store.chunks}) if engine else 0)
col3.metric("Text chunks", len(engine.store.chunks) if engine else 0)
col4.metric("Collection", "Ready" if ready else "Empty")
if not settings.google_api_key.get_secret_value():
    st.info("You can index and inspect PDFs now. To chat, set GOOGLE_API_KEY in .env and restart Streamlit.")

chat_tab, sources_tab = st.tabs(["Conversation", "Document explorer"])
with chat_tab:
    if not engine or not engine.memory.turns:
        with st.container(border=True):
            st.markdown("#### Start with a question. Follow the evidence.")
            st.write("Upload your reports or load the fictional Northstar sample collection from the sidebar.")
            st.caption("TRY WITH THE SAMPLE REPORTS")
            st.write("• What was Northstar's revenue in 2023?\n\n• What about 2024?\n\n• Do the reports agree on the 2024 on-time delivery rate?")
    if engine:
        for turn in engine.memory.turns:
            with st.chat_message("user"):
                st.write(turn.question)
            with st.chat_message("assistant"):
                st.write(turn.answer.text)
                if turn.answer.resolved_question and turn.answer.resolved_question != turn.question:
                    st.caption(f"Interpreted question: {turn.answer.resolved_question}")
                for citation in turn.answer.citations:
                    with st.expander(f"[{citation.source_id}] {citation.chunk.filename} · Page {citation.chunk.page}"):
                        st.text(citation.quote)
                        st.caption(f"Chunk {citation.chunk.chunk_id} · cosine similarity {citation.score:.3f}")
                        st.text(citation.chunk.text)
    if question := st.chat_input("Ask about your documents…", disabled=not ready):
        try:
            with st.spinner("Resolving the question, retrieving evidence and checking citations…"):
                engine.ask(question)
            st.rerun()
        except (ProviderError, ValueError) as error:
            st.error(str(error))
        except Exception:
            st.error("The request could not be completed. Your documents are still available; please retry.")

with sources_tab:
    if ready:
        selected = st.selectbox("Document", list(engine.documents),
                                format_func=lambda key: f"{engine.documents[key].filename} · {key[:8]}")
        doc = engine.documents[selected]
        page_num = st.selectbox("Extracted page", [p.number for p in doc.pages])
        page = next(p for p in doc.pages if p.number == page_num)
        st.caption("Original extracted text, before whitespace normalization.")
        st.text(page.original_text)
    else:
        st.info("Process documents to inspect page-level source text.")
st.divider()
st.caption("Answers are generated from retrieved document context. Verify claims against cited passages. "
           "Citation checks verify provenance, not factual entailment. Documents and chat stay in this session's memory.")
