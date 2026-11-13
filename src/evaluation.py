from src.models import Hit


def retrieval_metrics(hits: list[Hit], expected: set[tuple[str, int]]) -> dict[str, float]:
    """Gold relevance unit is (filename, page); duplicate chunks count once for recall."""
    if not expected:
        return {}
    found = {(hit.chunk.filename, hit.chunk.page) for hit in hits}
    ranks = [i for i, hit in enumerate(hits, 1) if (hit.chunk.filename, hit.chunk.page) in expected]
    return {"recall_at_k": len(found & expected) / len(expected),
            "hit_at_k": float(bool(ranks)), "reciprocal_rank": 1 / min(ranks) if ranks else 0.0}
