from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_initial_ui_loads_without_model_download():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "A clearer view of your documents."
    assert app.chat_input[0].disabled
    assert len(app.metric) == 4


def test_sample_index_and_clear(monkeypatch):
    from tests.fakes import HashEmbedder
    monkeypatch.setattr("src.embeddings.get_embedder", lambda _: HashEmbedder())
    app = AppTest.from_file(APP).run(timeout=30)
    next(b for b in app.button if b.label == "Try three sample reports").click().run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "3"
    assert not app.chat_input[0].disabled
    next(b for b in app.button if b.label == "Clear Documents").click().run(timeout=30)
    assert app.metric[0].value == "0" and app.chat_input[0].disabled


def test_chat_followup_clear_and_session_isolation(monkeypatch):
    from tests.fakes import HashEmbedder, FakeLLM
    monkeypatch.setattr("src.embeddings.get_embedder", lambda _: HashEmbedder())
    monkeypatch.setattr("src.llm_service.GeminiService", lambda _: FakeLLM())
    app = AppTest.from_file(APP).run(timeout=30)
    next(b for b in app.button if b.label == "Try three sample reports").click().run(timeout=30)
    app.chat_input[0].set_value("What was Northstar revenue in 2023?").run(timeout=30)
    assert not app.exception and len(app.chat_message) == 2
    app.chat_input[0].set_value("What about 2024?").run(timeout=30)
    assert not app.exception and len(app.chat_message) == 4
    assert "2024" in app.session_state["pipeline"].memory.turns[-1].answer.resolved_question
    independent = AppTest.from_file(APP).run(timeout=30)
    assert independent.metric[0].value == "0" and not independent.chat_message
    next(b for b in app.button if b.label == "Clear Chat").click().run(timeout=30)
    assert not app.chat_message and app.metric[0].value == "3"
