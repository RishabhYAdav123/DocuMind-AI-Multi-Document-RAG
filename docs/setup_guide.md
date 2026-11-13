# Windows setup and troubleshooting

1. Install Python 3.11+ x64. Verification used Python 3.12.7. Open the project directory in VS Code and use its PowerShell terminal.
2. Run `python -m venv .venv` then `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Run `Copy-Item .env.example .env`. Edit `.env` locally, set `GOOGLE_API_KEY`, and select an available Gemini text model via `LLM_MODEL`.
4. Run `.\.venv\Scripts\python.exe -m streamlit run app.py`. Open `http://localhost:8501`.
5. Click **Try three sample reports** or upload your own text PDFs. Processing requires the first model-weight download. Wait until the collection says Ready.
6. Ask a question, inspect citations, then try a follow-up. Clear chat to start a new topic; clear documents to start a new collection.

No activation script is required. If you prefer activation, `.\.venv\Scripts\Activate.ps1` works where execution policy permits it. Avoid changing system-wide policy merely for this project. Select `.venv\Scripts\python.exe` as the VS Code interpreter.

## Common issues

| Symptom | Action |
|---|---|
| Model cannot load | Allow Hugging Face network access for the first run; ensure disk/RAM availability. Check a local proxy if applicable. |
| Missing API key | Set `GOOGLE_API_KEY` in `.env` in the project directory, then restart the server. Never paste keys into chat. |
| Provider failure | Check model access in your account, key validity, quota and connectivity. One retry is automatic for transient API errors. |
| No usable text | Run OCR externally, export a searchable PDF, and upload again. |
| Password protected | Upload an unlocked copy you are authorized to use. |
| Empty or irrelevant answer | Check source text, narrow the question, or adjust top-k/cutoff. A lower cutoff can introduce irrelevant evidence. |
| Wrong table reading order | Inspect the original PDF; extraction is text-based and does not reconstruct complex table geometry. |
| Port already used | Add `--server.port 8502` to the launch command. |
| Changed embedding configuration | Restart, clear documents and re-index. Do not mix embedding models. |

The app binds only to localhost. An internet-facing deployment would require authentication, resource isolation and additional security work. The UI can index and inspect PDFs without a Gemini key, but chat reformulation and answers require it. Tests inject fakes; the default evaluation uses real embeddings and no LLM calls.
