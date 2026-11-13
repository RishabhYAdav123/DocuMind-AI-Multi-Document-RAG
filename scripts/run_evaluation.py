"""Offline real semantic retrieval by default; --live enables paid Gemini calls."""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import Settings
from src.embeddings import get_embedder
from src.evaluation import retrieval_metrics
from src.llm_service import GeminiService
from src.rag_pipeline import RAGPipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", choices=["sentence", "hash"], default="sentence")
    parser.add_argument("--live", action="store_true", help="Calls Gemini; incurs provider usage")
    parser.add_argument("--request-interval", type=float, default=6.0,
                        help="Minimum seconds between live requests (default 6, to reduce quota bursts)")
    parser.add_argument("--case-ids", default="", help="Optional comma-separated case IDs for a targeted recheck")
    parser.add_argument("--output-tag", default="", help="Alphanumeric/underscore suffix to preserve earlier runs")
    args = parser.parse_args()
    if args.output_tag and not args.output_tag.replace("_", "").isalnum():
        parser.error("--output-tag must contain only letters, digits and underscores")
    settings = Settings()
    if args.live:
        if not 0 <= args.request_interval <= 60:
            parser.error("--request-interval must be between 0 and 60")
        settings.llm_min_interval_seconds = args.request_interval
    if args.live and not settings.google_api_key.get_secret_value():
        parser.error("--live needs GOOGLE_API_KEY; no API calls were made")
    if args.embedding == "hash":
        from tests.fakes import HashEmbedder
        embedder = HashEmbedder()
    else:
        embedder = get_embedder(settings.embedding_model)
    pipeline = RAGPipeline(settings, embedder, GeminiService(settings))
    for path in sorted((ROOT / "sample_documents").glob("*.pdf")):
        pipeline.ingest(path.name, path.read_bytes())
    questions = json.loads((ROOT / "evaluation/evaluation_questions.json").read_text())
    if args.case_ids:
        selected = set(args.case_ids.split(","))
        if selected - {case["id"] for case in questions}:
            parser.error("Unknown case ID")
        questions = [case for case in questions if case["id"] in selected]
    rows = []
    for case in questions:
        gold = set(zip(case["expected_source"], case["expected_page"]))
        hits = pipeline.store.search(case["retrieval_question"], settings.top_k, settings.min_similarity)
        row = dict(id=case["id"], category=case["category"], question=case["question"],
                   embedding=args.embedding, top_k=settings.top_k, threshold=settings.min_similarity,
                   retrieved="; ".join(f"{h.chunk.filename}:p{h.chunk.page}" for h in hits),
                   recall_at_k="", hit_at_k="", reciprocal_rank="", answer_status="not_run",
                   answer="", citation_validity="", unanswerable_correct="",
                   correctness_0_2="", groundedness_0_2="", resolved_question="", citations_json="")
        row.update(retrieval_metrics(hits, gold))
        if args.live:
            pipeline.memory.clear()
            try:
                for previous in case["history"]:
                    pipeline.ask(previous)
                answer = pipeline.ask(case["question"])
                row.update(answer_status=answer.status, answer=answer.text,
                           resolved_question=answer.resolved_question,
                           citations_json=json.dumps([{"source_id": c.source_id, "filename": c.chunk.filename,
                                                       "page": c.chunk.page, "quote": c.quote}
                                                      for c in answer.citations], ensure_ascii=False))
                if answer.citations:
                    row["citation_validity"] = float(all(c.quote in " ".join(c.chunk.text.split()) for c in answer.citations))
                if case["category"] == "unanswerable":
                    row["unanswerable_correct"] = float(answer.status == "insufficient")
            except Exception:
                row["answer_status"] = "provider_or_pipeline_error"
            print(f"{case['id']}: {row['answer_status']}", flush=True)
        rows.append(row)
    out = ROOT / "evaluation"
    suffix = args.output_tag or ("live" if args.live else args.embedding)
    path = out / f"evaluation_results_{suffix}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    # Standard assignment artifact follows the most recent real semantic run only.
    if args.embedding == "sentence" and not args.output_tag:
        (out / "evaluation_results.csv").write_bytes(path.read_bytes())
    summary = {metric: (mean(r[metric] for r in rows if r[metric] != "")
                       if any(r[metric] != "" for r in rows) else None)
               for metric in ("recall_at_k", "hit_at_k", "reciprocal_rank")}
    summary.update(embedding=args.embedding, live=args.live, questions=len(rows),
                   retrieval_cases=sum(bool(c["expected_source"]) for c in questions),
                   chunks=len(pipeline.store.chunks), top_k=settings.top_k, threshold=settings.min_similarity)
    summary.update(executed_at=datetime.now(timezone.utc).isoformat(), model=settings.llm_model)
    if args.live:
        summary["answer_status_counts"] = {status: sum(r["answer_status"] == status for r in rows)
                                          for status in sorted({r["answer_status"] for r in rows})}
        for field in ("citation_validity", "unanswerable_correct"):
            values = [r[field] for r in rows if r[field] != ""]
            summary[field] = mean(values) if values else None
            summary[f"{field}_cases"] = len(values)
    (out / f"summary_{suffix}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
