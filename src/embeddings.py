from functools import lru_cache
from pathlib import Path
from threading import RLock
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceEmbedder:
    """Only public model weights are cached globally, never document embeddings."""
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        cache = Path(__file__).resolve().parents[1] / ".cache" / "models"
        self.model = SentenceTransformer(model_name, device="cpu", trust_remote_code=False,
                                         cache_folder=str(cache))
        self.lock = RLock()

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        # MiniLM truncates long inputs. Average token-bounded windows so no tail is lost.
        tokenizer = self.model.tokenizer
        limit = self.model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
        windows, counts = [], []
        for text in texts:
            ids = tokenizer.encode(text, add_special_tokens=False)
            parts = [ids[i:i + limit] for i in range(0, len(ids), limit)] or [[]]
            windows.extend(tokenizer.decode(part, skip_special_tokens=True) for part in parts)
            counts.append(len(parts))
        with self.lock:
            encoded = self.model.encode(windows, batch_size=32, convert_to_numpy=True,
                                        normalize_embeddings=True, show_progress_bar=False)
        rows, offset = [], 0
        for count in counts:
            rows.append(encoded[offset:offset + count].mean(axis=0))
            offset += count
        return np.asarray(rows, dtype=np.float32)


@lru_cache(maxsize=2)
def get_embedder(model_name: str) -> SentenceEmbedder:
    return SentenceEmbedder(model_name)
