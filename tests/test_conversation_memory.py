from src.conversation_memory import ConversationMemory
from src.models import Answer


def test_limits_isolation_clear():
    first, second = ConversationMemory(2), ConversationMemory(2)
    for i in range(3):
        first.add(str(i), Answer("x" * 2000, "answered"))
    assert len(first.turns) == 2 and first.turns[0].question == "1"
    assert len(first.context()[0]["answer"]) == 1500
    assert not second.turns
    first.clear()
    assert first.context() == []


def test_abstentions_not_used_as_factual_history():
    memory = ConversationMemory()
    memory.add("Who?", Answer("I cannot answer", "insufficient"))
    assert memory.context() == []
