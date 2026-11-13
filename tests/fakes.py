import hashlib
import re

import numpy as np

from src.models import Claim, Evidence, GeneratedAnswer, Rewrite


class HashEmbedder:
    """Lexical test double. NOT a Sentence Transformer or production quality metric."""
    def encode(self, texts: list[str]) -> np.ndarray:
        rows = np.zeros((len(texts), 1024), dtype=np.float32)
        for row, text in zip(rows, texts):
            for word in re.findall(r"\w+", text.lower()):
                bucket = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 1024
                row[bucket] += 1
            if not row.any():
                row[0] = 1
        return rows


class FakeLLM:
    def __init__(self):
        self.histories = []
        self.answer_calls = 0

    def rewrite(self, question, history):
        self.histories.append(history)
        if question.lower().startswith("what about"):
            if not history:
                return Rewrite(question=question, needs_clarification=True)
            previous = history[-1]["resolved_question"] or history[-1]["question"]
            years = re.findall(r"\b20\d{2}\b", question)
            return Rewrite(question=re.sub(r"\b20\d{2}\b", years[0], previous) if years else previous)
        return Rewrite(question=question)

    def answer(self, question, hits):
        self.answer_calls += 1
        return GeneratedAnswer(status="answered", claims=[Claim(
            text="Test fixture evidence", evidence=[Evidence(source_id="S1", quote=hits[0].chunk.text[:100])])])
