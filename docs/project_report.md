# DocuMind AI — Intelligent Multi-Document RAG System

## 1. Title page

**Assignment 3: Generative AI / Data Science Case Study**
Project: DocuMind AI
Submission date: 13 November 2026
Implementation: Python, Streamlit, Sentence Transformers, FAISS and Google Gemini
Verification status: see [validation record](validation.md) for executed checks and remaining limitations.

## 2. Abstract

DocuMind AI addresses natural-language information retrieval across multiple PDF reports. The implementation separates document ingestion, semantic retrieval, conversational interpretation, answer generation and citation verification. It preserves original extracted text and physical PDF page numbers, uses CPU embeddings and an in-memory FAISS index, and asks Gemini for structured claims supported by retrieved quotations. Three original synthetic reports and 25 evaluation questions make the system reproducible without confidential data. Offline tests evaluate deterministic behavior; real semantic retrieval is measured separately from live answer quality. Provenance verification reduces fabricated references but does not prove semantic faithfulness.

## 3. Introduction

Organizational facts often span annual reports, operational summaries and policies. Keyword search can miss paraphrases, while a general chatbot may produce plausible unsupported answers. A document-grounded workflow must first identify evidence, then produce an answer with enough traceability for a reader to inspect it. Conversational follow-ups introduce an additional requirement: interpret references without treating earlier model statements as independent evidence.

## 4. Problem statement

Develop a local application that accepts multiple PDFs, extracts and retrieves relevant information, answers natural-language questions using an LLM, cites actual documents and pages, abstains when information is unavailable, and maintains conversational context. Demonstration must use multiple sample reports and include reproducible evaluation.

## 5. Project objectives

The principal objectives are accurate provenance, dependable ingestion, bounded conversational state, modular provider integration, transparent failure behavior and an interface that makes evidence easy to inspect. Measured performance must distinguish implementation correctness from retrieval effectiveness and model answer quality.

## 6. Scope

The application runs locally on Windows and supports searchable text PDFs. It handles multiple reports within configured file, page and chunk limits. It does not implement OCR, enterprise authentication, durable storage, table-structure reconstruction or an independently validated prompt-injection firewall. Only Gemini is currently implemented; the provider protocol permits later extensions.

## 7. Technology stack

Python 3.11+ supplies the application runtime. Streamlit implements upload, chat, metrics and source inspection. PyMuPDF extracts text. LangChain's recursive text splitter is used without adding a broader agent framework. Sentence Transformers provides MiniLM CPU embeddings and FAISS IndexFlatIP performs exact cosine search. Pydantic validates configuration and structured model output. Google Gen AI SDK integrates Gemini. ReportLab generates original samples; Pytest and Streamlit AppTest support offline verification. Exact installed versions are recorded in `requirements-lock.txt`.

## 8. Proposed system architecture

The [architecture diagram](architecture.md) shows two phases. Ingestion validates PDFs, extracts original page text, normalizes it, creates page-local chunks and indexes normalized embeddings. Question answering validates the query, obtains a standalone interpretation from bounded history, retrieves relevant chunks, generates structured claims and verifies each citation. Each Streamlit session owns its documents, index and history. Only public model weights are shared across sessions.

## 9. Dataset and sample documents

The Northstar collection contains three original, explicitly fictional reports, each three pages long. The annual report covers revenue, profit, research allocation, workforce and targets. The operations report covers delivery, the Aurora pilot and platform reliability. The security policy covers retention, access and incident controls. Tables repeat important quantitative facts in a readable form. Overlapping entities support multi-document and follow-up questions. Deliberate disagreements test conflict reporting, while a training appendix tests handling of embedded malicious instructions. No sample financial figure is a real-world disclosure.

## 10. Document preprocessing

The loader checks extension, PDF signature, byte size, password state and page count before extracting text. A SHA-256 content digest identifies duplicates even after renaming. Unreadable files produce sanitized errors. Empty or image-only PDFs request OCR. Pages with little text produce warnings rather than silent success. Unicode normalization and whitespace cleanup retain punctuation, percentages, dates and monetary figures. Both original and cleaned text remain available in memory.

## 11. Chunking methodology

Recursive splitting uses paragraph, line, sentence and word boundaries before falling back to characters. Default size is 1,000 characters with a maximum 200-character overlap. Processing each page independently guarantees correct single-page citations. Chunk metadata includes content digest, filename, page, unique ordinal and normalized-text start offset. Page boundaries can separate related material; this is a documented precision/continuity tradeoff. The defaults have not been proven optimal.

## 12. Embedding generation

The production encoder is `sentence-transformers/all-MiniLM-L6-v2`, loaded once on CPU per model name. Text is embedded in batches. Inputs exceeding the model token limit are divided into windows whose vectors are averaged, preventing silent loss of the tail. All final vectors are normalized. A lock protects concurrent access to the shared encoder; private document vectors are never placed in a global cache. Tests inject deterministic lexical vectors to avoid network dependencies, and those results are not presented as semantic performance.

## 13. Vector database and retrieval

FAISS exact inner-product search over normalized vectors implements cosine retrieval. The store rejects non-finite, zero or dimensionally inconsistent embeddings. New chunks are deduplicated and added to a candidate index before committing the change. Default top-k is five with a 0.30 cosine cutoff. An empty store returns no hits. The cutoff controls obvious irrelevance but is not a probability of correctness. Retrieving every necessary page remains especially important for cross-document calculations and disagreements.

## 14. LLM integration

Google Gemini is accessed through the official `google-genai` SDK. Configuration includes the provider, model, key and per-attempt timeout. Account-specific access to `gemini-3.5-flash-lite` and structured generation were verified on 13 November 2026. Credentials are read from environment and never logged. Generation uses temperature 0.1, a bounded output and a structured schema. Transient API failures receive one retry; rate limits respect bounded structured retry delays and evaluation requests are paced. Provider errors are replaced with actionable messages without exposing request content or secrets.

## 15. Conversational memory

Every successful interaction stores the user question and the resulting assistant answer. At most six turns are retained by default. Rewrite context includes bounded text from answered turns and their resolved questions. The model is instructed to preserve explicit constraints, resolve unambiguous references and request clarification otherwise. A question can change topic without inheriting unrelated facts. Generation receives documentary evidence, not prior assistant answers as evidence. Clearing documents also clears history to prevent references to a removed collection.

## 16. Source citation mechanism

Retrieved chunks receive request-local source IDs. Each generated claim must include evidence objects containing a source ID and a verbatim quote. The validator checks that the ID exists in the actual retrieval set and that the quote is present after whitespace normalization. Any invalid evidence rejects the entire response. Only cited passages are displayed, with filenames and page numbers from application metadata. This prevents invented citation identifiers from reaching the source list. It does not independently detect a misleading inference from a genuine quote; human review remains necessary.

## 17. User interface

The Streamlit layout uses dark navy surfaces, restrained accent colors, readable spacing and rounded panels. The sidebar contains multi-file upload, process controls, sample loading, indexed-document statuses, clear actions and retrieval settings. Four collection metrics expose documents, indexed pages, chunks and readiness. Conversation messages provide evidence expanders. A separate explorer shows original extracted page text. The chat input is disabled until an index exists. Missing credentials are explained before a user attempts an answer. The UI avoids a decorative chart because the collection metrics already communicate the relevant state.

## 18. Evaluation methodology

The 25-case dataset specifies expected answers, filenames and physical page numbers before executing retrieval. Categories include factual, numerical, multi-document, multi-hop, comparison, conflict, policy, follow-up, context retention, unanswerable, ambiguous and injection cases. Recall@K uses expected source/page pairs as the denominator; hit rate counts any relevant hit; MRR uses the first relevant chunk rank. Cases without relevant pages are excluded from these denominators. Offline follow-ups use gold standalone queries, so they do not evaluate model rewriting. Live mode records real answers and conversation behavior for subsequent rubric scoring.

## 19. Experimental results

Actual measured values, command details and failure cases are in [evaluation_report.md](../evaluation/evaluation_report.md), with row-level CSV outputs. The real live evaluation covered 25 cases. One provider 503 failure passed a separate recheck; the full-run failure remains recorded. Twenty factual answers then had 29 valid evidence quotes. All three absent-information cases abstained, both follow-ups retained context, the ambiguous case requested clarification and the injection request abstained. Agent inspection assigned 39/40 completeness points and 40/40 grounding points across the 20 factual answers, with the effective date missing from one policy comparison. This is not an independent human review. Retrieval recall and hit rate were 1.0000; MRR was 0.9762 on 21 labeled cases. The automated suite passed 43 tests. UI details and remaining verification limits are recorded in [validation.md](validation.md).

## 20. Challenges and solutions

Page fidelity is preserved by page-local splitting and metadata-derived source displays. Duplicate uploads are resolved by content hashes rather than filenames. A partially failed embedding operation cannot mutate the active index because the store uses copy-on-write. Empty and scanned PDFs are distinguished from successful extraction through text checks and warnings. Token-limit truncation is addressed through bounded window pooling. Potentially malicious PDF instructions remain in a data payload separated from the system instruction. These controls reduce common failure modes without claiming to eliminate every adversarial risk.

## 21. Limitations

The sample collection is small, synthetic and text-oriented. Its results cannot be generalized to complex enterprise PDFs. Table extraction and reading order may be imperfect. Window pooling can dilute meaning; page-local chunks can separate context. The relevance cutoff is uncalibrated. Gemini may misresolve a reference, overlook a conflict or misinterpret a valid quotation. API account access, network reliability and model availability affect the online path. Citation provenance is not entailment validation. Session memory is not guaranteed secure erasure, and the application is not an enterprise-hardened service.

## 22. Future enhancements

Priorities are a larger independently labeled corpus, threshold calibration, live answer scoring with human adjudication, and targeted retrieval improvements for missed evidence. Hybrid search and reranking should be justified by measured gains. OCR and layout-aware extraction could extend coverage to scanned or complex reports. Claim-level entailment checks could supplement provenance validation. Authentication, stronger resource isolation and retention controls would be required before broader deployment.

## 23. Conclusion

DocuMind implements the assignment's complete ingestion-to-answer architecture with traceable retrieval, bounded conversational interpretation and inspectable citations. Its evaluation design separates deterministic correctness, semantic retrieval and live generation quality. The submission includes reproducible source code, permitted sample PDFs, tests, documentation and an allowlisted ZIP. Final readiness is bounded by the verification record rather than by unexecuted claims.

## 24. References

- [Google Gemini model catalog](https://ai.google.dev/gemini-api/docs/models) — model selection reference, checked 13 November 2026.
- [Google Gen AI SDK](https://googleapis.github.io/python-genai/) — client, configuration and structured outputs.
- [Sentence Transformers documentation](https://www.sbert.net/) — embedding APIs and CPU inference.
- [FAISS documentation](https://faiss.ai/) — vector indexing and inner-product search.
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/) — PDF extraction and rendering.
- [Streamlit documentation](https://docs.streamlit.io/) — application widgets, session state and AppTest.
- [LangChain text splitters](https://docs.langchain.com/oss/python/integrations/splitters/index) — recursive splitting.

## Assignment requirement traceability

| Mandatory requirement | Implementation / evidence |
|---|---|
| Upload multiple PDFs | Sidebar uploader; `RAGPipeline.ingest`; three-sample integration test |
| Extract and process PDF information | Loader, preprocessing, page-local chunker and PDF tests |
| Retrieve relevant information | MiniLM encoder and FAISS search; labeled retrieval CSV |
| Generate context-aware LLM responses | Gemini structured generation; live evaluation command |
| Ground answers in documents | Evidence-only system instruction and per-claim quotes |
| Relevant source references | Source-ID/quote checks, metadata filenames/pages, source explorer |
| Handle unavailable information | Relevance gate, insufficient status and abstention cases |
| Maintain conversational context | Bounded per-session conversation memory |
| Interpret follow-ups | Standalone query reformulation and clarification status |
| Multiple demonstration reports | Three original PDFs, nine pages and 25 labeled cases |
