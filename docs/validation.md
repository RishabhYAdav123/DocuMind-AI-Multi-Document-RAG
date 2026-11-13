# Final verification record

Date: 13 November 2026. Environment: Windows x64, Python 3.12.7. The existing working implementation was preserved and improved after live testing.

**Readiness: READY for the Assignment 3 source-code submission, with documented limitations.** Actual Gemini access, multi-PDF retrieval, live answers, conversation follow-ups, citations, abstention, Streamlit widget behavior and local automated tests were executed. This is not a production-readiness or universal answer-accuracy claim. Browser visual review remains unavailable.

## Executed checks

| Check | Observed result |
|---|---|
| Fresh environment installation from earlier phase | Completed; exact versions retained in requirements-lock.txt |
| Dependency compatibility | `pip check`: no broken requirements |
| Final local Pytest suite | **43 passed in 5.53 seconds** |
| Clean GitHub Linux runner | **43 passed in 2.57 seconds** with updated actions (initial run: 2.18 seconds); both dependency checks passed |
| Gemini model lookup | `models/gemini-3.5-flash-lite` accessible |
| Structured Gemini generation | Passed with the locally configured key |
| Real semantic retrieval | Recall@5 1.0000, Hit Rate@5 1.0000, MRR 0.9762 over 21 cases |
| Full live evaluation | 25 cases; one transient 503 error, passed on a separately recorded recheck |
| Final live UI test | **6/6 passed** through Streamlit AppTest using real MiniLM and Gemini |
| UI document processing | Three PDFs, nine indexed pages, nine chunks |
| UI conversation | Factual response, year follow-up, multi-document answer, conflict comparison, security-policy answer and abstention passed |
| UI clear controls | Clear Chat preserved documents; Clear Documents cleared the collection and disabled chat |
| Session isolation | Passed in deterministic Streamlit tests |
| Server | Restarted with API network access at `http://127.0.0.1:8501`; health endpoint returned `ok` |
| Sample reports | Three original PDFs, three pages each; all pages extracted |
| PDF visual review from earlier phase | All nine pages rendered with PyMuPDF and inspected; no clipping/overlap observed |
| Secret handling | Credential remains only in local ignored configuration; publication audit checks staging and ZIP |

Final raw records are in `evaluation/`. The full live run is not rewritten to hide its provider error. A separate Q01 recheck recovered it. Agent inspection of twenty factual answers awarded 39/40 completeness points and 40/40 grounding points; this is not an independent human review. One policy comparison omitted its effective-date caveat. See the evaluation report for exact denominators and failed exploratory runs.

## Changes made during live verification

- Standalone questions now bypass unnecessary rewriting; dependent references still use bounded conversational reformulation.
- Quote instructions require exact contiguous source text; strict citation rejection is retained.
- Rate-limit handling reads the installed SDK's structured retry details, bounds waits to sixty seconds and supports optional request pacing.
- Evaluation records now include resolved questions, actual citations, statuses, timestamps and model IDs; isolated rechecks preserve main-run results.
- Live UI verification retains diagnostics and checks both clear controls.
- Git ignore patterns cover environment variants, caches, logs, private-key files and build output. Public CI uses no Gemini secrets.

## Remaining limits

- Browser automation could not reliably determine the active Windows URL in the earlier inspection attempt. No application screenshot, responsive-browser visual review or native file-picker test is claimed. AppTest checks the actual Streamlit execution/widget path, not screen appearance.
- Gemini is nondeterministic and subject to quota/service failures; one 503 was observed even after a bounded retry.
- Q15 omitted the effective date of the newer security policy. Correct citations do not guarantee a complete answer.
- The nine-page synthetic corpus is small. Performance on long, scanned, multi-column or complex-table PDFs is not established. OCR is not included.
- Follow-up detection is heuristic. Independent human faithfulness review and adversarial testing remain desirable.
- Citation validation checks provenance and verbatim quotations, not formal entailment or enterprise-grade security.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_provider.py
.\.venv\Scripts\python.exe scripts\run_evaluation.py --live
.\.venv\Scripts\python.exe scripts\verify_runtime.py --live
```

Run live commands sequentially and configure your own key locally. `verify_runtime.py` uses cached MiniLM weights, so run the evaluator first to download them. Live runs use Gemini quota. The offline test suite needs no key or model download.

## Submission and GitHub

The public source repository is named `DocuMind-AI-Multi-Document-RAG`. Publication details are recorded separately in `docs/publication.md`. The ZIP is created from an explicit allowlist and contains source, CI configuration, documentation, evaluation evidence and the three permitted sample PDFs. Virtual environments, keys, model weights, private uploads and temporary rendering files are excluded. See `docs/github_submission.md` for exact publishing steps and requirement entry points.
