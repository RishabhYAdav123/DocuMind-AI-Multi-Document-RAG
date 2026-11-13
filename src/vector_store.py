import faiss
import numpy as np

from src.embeddings import Embedder
from src.models import Chunk, Hit


def normalized(vectors: np.ndarray) -> np.ndarray:
    values = np.array(vectors, dtype=np.float32, copy=True, order="C")
    if values.ndim != 2 or not values.shape[1] or not np.isfinite(values).all():
        raise ValueError("Embeddings must be a finite two-dimensional matrix")
    if np.any(np.linalg.norm(values, axis=1) == 0):
        raise ValueError("Embedding model returned a zero vector")
    faiss.normalize_L2(values)
    return values


class VectorStore:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.index = None
        self.chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk]) -> None:
        existing = {c.chunk_id for c in self.chunks}
        fresh = []
        for chunk in chunks:
            if chunk.chunk_id not in existing:
                fresh.append(chunk)
                existing.add(chunk.chunk_id)
        if not fresh:
            return
        vectors = normalized(self.embedder.encode([c.text for c in fresh]))
        if vectors.shape[0] != len(fresh):
            raise ValueError("Embedding row count mismatch")
        if self.index is not None and vectors.shape[1] != self.index.d:
            raise ValueError("Embedding dimensions changed; rebuild the index")
        # Copy-on-write: a failed add cannot partially corrupt the active session index.
        candidate = faiss.clone_index(self.index) if self.index is not None else faiss.IndexFlatIP(vectors.shape[1])
        candidate.add(vectors)
        self.index = candidate
        self.chunks.extend(fresh)

    def search(self, question: str, top_k: int, minimum: float) -> list[Hit]:
        if self.index is None or not self.chunks:
            return []
        query = normalized(self.embedder.encode([question]))
        if query.shape != (1, self.index.d):
            raise ValueError("Query embedding dimensions do not match the index")
        scores, indices = self.index.search(query, min(top_k, len(self.chunks)))
        return [Hit(self.chunks[i], float(score)) for score, i in zip(scores[0], indices[0])
                if i >= 0 and float(score) >= minimum]

    def clear(self) -> None:
        self.index, self.chunks = None, []
