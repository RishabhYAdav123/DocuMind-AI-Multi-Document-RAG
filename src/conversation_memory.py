from dataclasses import dataclass

from src.models import Answer


@dataclass
class Turn:
    question: str
    answer: Answer


class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.turns: list[Turn] = []

    def add(self, question: str, answer: Answer) -> None:
        self.turns.append(Turn(question, answer))
        self.turns = self.turns[-self.max_turns:]

    def context(self) -> list[dict[str, str]]:
        return [{"question": t.question[:2000], "resolved_question": t.answer.resolved_question[:2000],
                 "answer": t.answer.text[:1500]} for t in self.turns if t.answer.status == "answered"]

    def clear(self) -> None:
        self.turns.clear()
