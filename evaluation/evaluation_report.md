# Evaluation report

Executed on 13 November 2026 using Windows x64, Python 3.12.7, real CPU MiniLM embeddings, FAISS and Google Gemini `gemini-3.5-flash-lite`. Exact installed dependencies are in `requirements-lock.txt`.

## Dataset and procedure

Three original fictional reports contain nine pages and nine default-sized chunks. The 25 questions and gold source/page labels were defined before retrieval. Twenty-one cases have gold retrieval pages; three absent-information questions and one ambiguous reference are excluded from retrieval denominators. The injection case has a gold retrieval page but its expected safe answer is abstention rather than execution of the embedded instruction.

Retrieval uses top-k=5 and a 0.30 cosine threshold. Offline retrieval metrics use gold standalone reformulations for follow-up cases. They therefore do not measure rewriting. Live generation executes actual history turns and resolves follow-ups through the implemented pipeline. Six additional UI cases exercise real Gemini responses through Streamlit AppTest. Requests were paced rather than run concurrently in the final checks.

## Actual measured results

| Check | Result | Denominator / qualification |
|---|---:|---|
| Gemini model access and structured response | Passed | Actual authenticated API check, sanitized record saved |
| Recall@5 | 1.0000 | 21 labeled source/page cases |
| Hit Rate@5 | 1.0000 | 21/21 |
| MRR | 0.9762 | 20 first-ranked relevant hits, one second-ranked |
| Full live run | 24 responses, 1 provider error | 25 cases; the error was a transient HTTP 503 on Q01 |
| Targeted Q01 recheck | Answered correctly | Separate raw run retained, not substituted into full-run CSV |
| Factual answer coverage after documented recheck | 20/20 | Excludes abstention, ambiguity and injection cases |
| Displayed evidence provenance | 29/29 quotes valid | Across the 20 factual answers including Q01 recheck |
| Absent-information handling | 3/3 correct abstentions | Q21-Q23 |
| Follow-up/context retention | 2/2 correct | Q19 and Q20, actual conversation history |
| Ambiguous reference | Clarification requested | Q24 |
| Injection exercise | Abstained | Q25; did not execute the embedded instruction |
| Live Streamlit AppTest | 6/6 passed | Actual MiniLM and Gemini; clear chat/documents also passed |
| Offline Pytest suite | 43 passed | Deterministic tests with fake providers where appropriate |
| Agent-reviewed factual completeness | 39/40 points | Twenty answers, 0-2 rubric; Q15 omitted the effective date |
| Agent-reviewed groundedness | 40/40 points | Twenty answers; every reviewed claim supported by quotes |

Agent review means Codex inspected the saved answers, expected facts and evidence. It is **not an independent human assessment**, blinded evaluation or external model-as-judge benchmark. The original `correctness_0_2` and `groundedness_0_2` CSV columns remain blank for an independent human reviewer. Agent scores and rationales are in a separate `answer_review.csv`, bound to exact answers with SHA-256 hashes.

The raw full run had 19 `answered`, 4 `insufficient`, 1 `clarification` and 1 `provider_or_pipeline_error`. The fourth insufficient case is the injection exercise. Do not report the full run as 25 uninterrupted API successes. The later Q01 recheck recovered the one service error.

## Artifact map

- `provider_verification.json`: actual configured-model lookup and structured generation result; no credential values.
- `evaluation_results_sentence.csv` / `summary_sentence.json`: original real semantic retrieval-only run.
- `evaluation_results_live.csv` / `summary_live.json`: complete final 25-case run, including Q01 failure.
- `evaluation_results.csv`: standard assignment artifact, same full live run.
- `evaluation_results_live_recheck.csv` / `summary_live_recheck.json`: Q01 recovery only.
- `answer_review.csv` / `answer_review_summary.json`: agent inspection, exact-answer hashes, scores and limitations.
- `ui_live_transcript.json` / `runtime_verification_live.json`: six successful real UI cases and source evidence.
- `test_results.txt`: final local Pytest output.
- `baseline/`: completed first live run, preserved before fixes.
- Files labeled `hash`: lexical test-double diagnostic, not semantic performance evidence.

## Failures, fixes and remaining limitations

The first live run returned 11 answers, 5 clarifications, 3 abstentions, 1 citation rejection and 5 provider errors. Concurrent evaluation/UI calls caused HTTP 429 responses. Rewriting every query also caused unnecessary clarification on standalone questions. One multi-hop response failed exact-quote validation and was correctly withheld.

Fixes preserve the implementation: standalone questions now go directly to retrieval; dependent references still use bounded-history rewriting. Quote instructions explicitly require a contiguous verbatim substring. The provider reads the SDK's `details` field for structured RetryInfo and honors a bounded delay, with a 20-second rate-limit fallback. Evaluation calls are paced at six seconds minimum. A regression test caught and corrected an initially wrong SDK attribute name. Citation validation was not weakened.

A second rewrite-prompt-only run was stopped after the same unnecessary clarification recurred. It is not counted as a completed benchmark. After the routing change, all previously over-clarified standalone questions produced answers. The final full run had one HTTP 503 despite its bounded retry; a later isolated recheck succeeded. Provider availability is still an external dependency.

An initial live UI attempt stopped on a 429 after two cases. A later attempt stopped on a follow-up assertion without retaining the answer, so its cause is unknown. The verifier was improved to record per-case outcomes instead of losing diagnostics. The final diagnostic UI run passed all six cases, with full transcripts retained. These exploratory failures are not represented as successful checks.

Q15 correctly compared 30-day operations retention with 90-day security retention and cited both reports, but omitted the security policy's effective date of 1 February 2025. It receives 1/2 completeness points. All its stated facts were supported. This is a remaining answer-completeness limitation, not a fabricated reference.

Q03 ranked the 2025 target page first and the correct historical revenue page second. Top-k recovered the evidence; rank-one search would have failed. Q21 and Q23 retrieved related pages despite absent answers, demonstrating why similarity alone cannot establish answerability. The actual model abstained on both in the final run.

The corpus is very small and synthetic; k=5 covers much of the collection. Settings are not calibrated on an independent held-out corpus. Prompt changes were informed by this demonstration set, so the final scores are not out-of-sample estimates. Citation provenance does not prove semantic entailment. One successful injection example is not a general security guarantee. The heuristic follow-up detector may miss subtler elliptical references. Browser visual review and a native browser file-picker test remain unverified; AppTest verifies the Streamlit execution/widget path.

## Metric definitions and review rubric

Gold relevance is a set of `(filename, physical page)` pairs. Recall@K is the fraction of gold pairs retrieved, counting duplicate page chunks once. Hit Rate@K is one if any gold pair is retrieved. Reciprocal rank is the inverse rank of the first relevant chunk, or zero without a hit. MRR averages across the 21 labeled cases after the similarity gate.

Completeness rubric: 0 = wrong or required answer absent; 1 = partially correct or omits a required caveat; 2 = all required facts, units and periods present. Groundedness: 0 = major unsupported claim; 1 = partly supported or misleading interpretation; 2 = every factual claim supported and calculations justified. Only the twenty factual answers were scored; abstention/clarification/injection outcomes are reported separately. Quote membership is automated, whereas claim meaning was inspected by the agent. Independent human review is still recommended.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_provider.py
.\.venv\Scripts\python.exe scripts\run_evaluation.py
.\.venv\Scripts\python.exe scripts\run_evaluation.py --live
.\.venv\Scripts\python.exe scripts\verify_runtime.py --live
# Optional isolated recheck; preserves the main run:
.\.venv\Scripts\python.exe scripts\run_evaluation.py --live --case-ids Q01 --output-tag live_recheck
```

Live commands use API quota. Run them sequentially. `--request-interval` adjusts evaluator pacing; `LLM_MIN_INTERVAL_SECONDS` controls normal service pacing. Use your own account-supported model and key. Retain raw failures and do not overwrite them with aggregate success claims. The default evaluator still works without an LLM key, using real cached/downloadable embeddings.
