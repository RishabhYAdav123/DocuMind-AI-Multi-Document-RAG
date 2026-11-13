from types import SimpleNamespace

import pytest
import httpx
from google.genai import errors

from src.llm_service import GeminiService, ProviderError


def mock_client(monkeypatch, action):
    class Client:
        def __init__(self, **kwargs):
            self.models = SimpleNamespace(generate_content=action)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr("google.genai.Client", Client)
    monkeypatch.setattr("src.llm_service.time.sleep", lambda _: None)


def test_schema_config_and_success(monkeypatch, settings):
    settings.google_api_key = __import__("pydantic").SecretStr("test-not-real")
    seen = {}
    def action(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(text='{"question":"Northstar revenue in 2024?","needs_clarification":false}')
    mock_client(monkeypatch, action)
    result = GeminiService(settings).rewrite("What about 2024?", [])
    assert result.question == "Northstar revenue in 2024?"
    assert seen["config"].temperature == 0.1
    assert seen["config"].response_mime_type == "application/json"


def test_rate_limit_retry_and_secret_redaction(monkeypatch, settings):
    settings.google_api_key = __import__("pydantic").SecretStr("SENSITIVE_TEST_KEY")
    calls = []
    def action(**kwargs):
        calls.append(1)
        raise errors.ClientError(429, {"error": {"message": "SENSITIVE_TEST_KEY", "code": 429}})
    mock_client(monkeypatch, action)
    with pytest.raises(ProviderError) as caught:
        GeminiService(settings).rewrite("Revenue?", [])
    assert len(calls) == 2
    assert "SENSITIVE_TEST_KEY" not in str(caught.value)


def test_bad_json_rejected(monkeypatch, settings):
    settings.google_api_key = __import__("pydantic").SecretStr("test-not-real")
    mock_client(monkeypatch, lambda **kwargs: SimpleNamespace(text="not valid JSON"))
    with pytest.raises(ProviderError, match="unusable"):
        GeminiService(settings).rewrite("Revenue?", [])


def test_timeout_retries_once(monkeypatch, settings):
    settings.google_api_key = __import__("pydantic").SecretStr("test-not-real")
    calls = []
    def action(**kwargs):
        calls.append(1)
        raise httpx.ReadTimeout("private request content")
    mock_client(monkeypatch, action)
    with pytest.raises(ProviderError, match="timed out") as caught:
        GeminiService(settings).rewrite("Revenue?", [])
    assert len(calls) == 2 and "private" not in str(caught.value)


def test_retry_delay_respects_provider_hint_and_bounds():
    def error(delay):
        return errors.ClientError(429, {"error": {"code": 429, "details": [
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}]}})
    assert GeminiService.retry_delay(error("12s")) == 13
    assert GeminiService.retry_delay(error("999s")) == 60
    assert GeminiService.retry_delay(error("invalid")) == 20
