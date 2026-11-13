# GitHub submission guide

Repository name: **DocuMind-AI-Multi-Document-RAG**

The submission uses the existing project root. It includes application source, bounded dependencies, a Windows verification lock file, an example configuration, tests, CI, three original fictional reports, measured evaluation artifacts, architecture and the complete case study. No separate institutional GitHub rubric was supplied; the checklist below covers the assignment prompt and normal public-repository hygiene.

## Reviewer entry points

- `README.md`: installation, configuration, features and verified results.
- `docs/project_report.md`: 24-section Assignment 3 case study and requirement traceability.
- `docs/architecture.md`: Mermaid diagram and component boundaries.
- `evaluation/evaluation_report.md`: measured results, failures and scoring limitations.
- `evaluation/provider_verification.json`: sanitized real model-access verification.
- `evaluation/evaluation_results_live.csv`: full live response records and citation evidence.
- `tests/`: deterministic core and Streamlit tests; no API key is required.
- `.github/workflows/tests.yml`: automated offline tests on push and pull requests.

## Public data and exclusions

All included reports and their generated answers are fictional demonstration data. `.env`, environment variants, private uploads, model caches, virtual environments, test caches, logs, private-key files and ZIPs are ignored. `.env.example` deliberately has no credential value. Never place a real API key in source, screenshots, commit messages, issues, workflow variables or README examples. GitHub Actions does not need Gemini credentials.

Before each publication:

```powershell
git add .
.\.venv\Scripts\python.exe scripts\package_submission.py
.\.venv\Scripts\python.exe scripts\audit_publication.py
git diff --cached --stat
```

The audit checks exact staged file bytes and the ZIP against the configured local credential, common token signatures, excluded paths and oversized files. It reports filenames only, never secret values. This is a focused check, not a guarantee against every possible kind of sensitive data; review staged content as well.

## Publish or reproduce the publication

If authentication is unavailable, sign in locally without sharing credentials in chat:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth status
```

For a new repository, after tests and the publication audit pass:

```powershell
git init -b main
git add .
git commit -m "Complete Assignment 3 multi-document RAG submission"
gh repo create DocuMind-AI-Multi-Document-RAG --public --source . --remote origin --push
```

If the repository already exists and `origin` is configured, use `git push -u origin main` instead of creating it again. Do not overwrite an unrelated repository or force-push. Use `gh run list` and `gh run view <run-id>` to inspect CI.

For the assignment, submit the repository URL and the locally generated `DocuMind_AI_RAG_Assignment.zip` if a ZIP is requested. The ZIP is intentionally not committed. It excludes the environment and model weights, so a reviewer must install dependencies and download MiniLM once. A reviewer supplies their own Gemini key in a local `.env` file.

## Remaining scope limits

This is a local assignment application, not an authenticated hosted service. Citation validation proves provenance and verbatim quote membership, not complete semantic entailment. The small synthetic evaluation is a demonstration benchmark. Browser visual review, if unavailable, is explicitly distinguished from Streamlit AppTest verification in the validation record.
