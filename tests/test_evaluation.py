from src.evaluation import retrieval_metrics
from src.models import Chunk, Hit


def test_metrics_have_gold_page_denominator():
    hits = [Hit(Chunk(str(i), "d", name, page, "text", 0), 1.0)
            for i, (name, page) in enumerate([("wrong.pdf", 1), ("a.pdf", 2), ("a.pdf", 2)])]
    assert retrieval_metrics(hits, {("a.pdf", 2), ("b.pdf", 3)}) == {
        "recall_at_k": 0.5, "hit_at_k": 1.0, "reciprocal_rank": 0.5}
    assert retrieval_metrics(hits, set()) == {}
