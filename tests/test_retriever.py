import numpy as np
import pytest

from src.models import Chunk
from src.vector_store import VectorStore
from tests.fakes import HashEmbedder


def chunk(id, text):
    return Chunk(id, id, f"{id}.pdf", 2, text, 0)


def test_multidocument_retrieval_metadata_and_duplicates():
    store = VectorStore(HashEmbedder())
    a, b = chunk("finance", "revenue annual growth million"), chunk("policy", "encryption security access policy")
    store.add([a, b, a])
    store.add([a])
    assert len(store.chunks) == 2
    hit = store.search("encryption security", 5, 0)[0]
    assert hit.chunk == b and hit.chunk.page == 2
    store.clear()
    assert store.search("revenue", 5, 0) == []


def test_dimension_change_is_atomic():
    class Changing:
        dim = 3
        def encode(self, texts):
            return np.ones((len(texts), self.dim))
    embedder = Changing()
    store = VectorStore(embedder)
    store.add([chunk("a", "hello")])
    embedder.dim = 4
    with pytest.raises(ValueError, match="dimensions"):
        store.add([chunk("b", "world")])
    assert len(store.chunks) == 1 and store.index.ntotal == 1
    with pytest.raises(ValueError, match="dimensions"):
        store.search("hello", 5, 0)


@pytest.mark.parametrize("value", [0, float("nan"), float("inf")])
def test_invalid_embeddings(value):
    class Broken:
        def encode(self, texts):
            return np.full((len(texts), 3), value)
    with pytest.raises(ValueError):
        VectorStore(Broken()).add([chunk("a", "some text")])
