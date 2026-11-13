"""Integration smoke check with real cached MiniLM weights and Streamlit AppTest.

Download/cache the model with run_evaluation.py first. This check makes no LLM calls.
"""
import json
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HF_HUB_OFFLINE"] = "1"

from streamlit.testing.v1 import AppTest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Exercise real Gemini responses through the UI; uses API quota")
    args = parser.parse_args()
    if args.live:
        os.environ["LLM_MIN_INTERVAL_SECONDS"] = "6"
    app = AppTest.from_file(ROOT / "app.py").run(timeout=60)
    assert not app.exception, "Initial UI failed"
    next(button for button in app.button if button.label == "Try three sample reports").click().run(timeout=120)
    assert not app.exception, "UI indexing failed"
    engine = app.session_state["pipeline"]
    assert len(engine.documents) == 3 and len(engine.store.chunks) == 9
    hits = engine.store.search("Northstar revenue in 2023", 5, 0.30)
    assert hits and hits[0].chunk.filename == "Northstar_Annual_Report.pdf" and hits[0].chunk.page == 1
    assert not app.chat_input[0].disabled
    summary = {"ui": "passed", "embedding": "real cached MiniLM, CPU", "documents": 3,
               "pages": 9, "chunks": 9, "query_top_source": f"{hits[0].chunk.filename}:p{hits[0].chunk.page}",
               "live_llm": "not executed", "browser_visual_review": "not executed"}
    if args.live:
        cases = [
            ("What was Northstar Analytics revenue in 2023?", "answered", "12"),
            ("What about 2024?", "answered", "15"),
            ("What funding did Aurora receive, and how many pilot customers did it have?", "answered", "30"),
            ("Do the reports agree on the 2024 on-time delivery rate?", "answered", "94"),
            ("What encryption protects customer data at rest and in transit?", "answered", "AES"),
            ("What is the CEO's salary?", "insufficient", ""),
        ]
        transcripts = []
        for question, status, text in cases:
            app.chat_input[0].set_value(question).run(timeout=240)
            if app.exception or app.error or app.session_state["pipeline"].memory.turns[-1].question != question:
                transcripts.append({"question": question, "status": "ui_or_provider_error", "passed": False})
                print(f"Live UI case {len(transcripts)}: ui_or_provider_error", flush=True)
                continue
            answer = app.session_state["pipeline"].memory.turns[-1].answer
            passed = (answer.status == status and text.lower() in answer.text.lower()
                      and (status != "answered" or bool(answer.citations)))
            transcripts.append({"question": question, "answer": answer.text, "status": answer.status,
                                "passed": passed,
                                "resolved_question": answer.resolved_question,
                                "citations": [{"filename": c.chunk.filename, "page": c.chunk.page, "quote": c.quote}
                                              for c in answer.citations]})
            print(f"Live UI case {len(transcripts)}: {answer.status}", flush=True)
        next(button for button in app.button if button.label == "Clear Chat").click().run(timeout=30)
        assert not app.chat_message and app.metric[0].value == "3"
        summary.update(live_llm="passed" if all(t["passed"] for t in transcripts) else "failed",
                       live_cases=len(transcripts), live_cases_passed=sum(t["passed"] for t in transcripts),
                       clear_chat="passed")
        (ROOT / "evaluation/ui_live_transcript.json").write_text(json.dumps(transcripts, indent=2), encoding="utf-8")
    next(button for button in app.button if button.label == "Clear Documents").click().run(timeout=30)
    assert app.metric[0].value == "0" and app.chat_input[0].disabled
    summary["clear_documents"] = "passed"
    suffix = "runtime_verification_live.json" if args.live else "runtime_verification.json"
    (ROOT / "evaluation" / suffix).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if args.live and summary["live_llm"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
