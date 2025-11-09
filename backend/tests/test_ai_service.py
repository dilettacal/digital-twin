"""Unit tests for AI service implementations."""

from __future__ import annotations

import importlib
import os
from typing import Any, Dict

import requests

pytest = importlib.import_module("pytest")


def _load_ai_modules():
    from app.services import ai as ai_pkg  # local import to allow env setup first
    from app.services.ai import AIService, BedrockAIService, OllamaAIService, OpenAIAIService, get_ai_service

    return ai_pkg, AIService, BedrockAIService, OllamaAIService, OpenAIAIService, get_ai_service


os.environ.setdefault("AI_PROVIDER", "bedrock")
os.environ.setdefault("RATE_LIMIT_MAX_REQUESTS", "5")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "10")
os.environ.setdefault("RATE_LIMIT_COOLDOWN_SECONDS", "1.0")

(  # unpack imports after environment configuration
    ai_pkg,
    AIServiceBase,
    BedrockAIService,
    OllamaAIService,
    OpenAIAIService,
    get_ai_service,
) = _load_ai_modules()


def test_truncate_history_limits_messages():
    class DummyService(AIServiceBase):
        def generate_response(self, conversation, user_message):
            return ""

    conversation = [{"role": "user", "content": str(i)} for i in range(5)]

    truncated = DummyService._truncate_history(conversation, 2)
    assert len(truncated) == 2
    assert truncated[0]["content"] == "3"
    assert truncated[1]["content"] == "4"

    assert DummyService._truncate_history(conversation, 0) == []


def test_bedrock_build_messages_includes_system_and_user(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.ai.bedrock.bedrock_client", object(), raising=False)
    monkeypatch.setattr("app.services.ai.bedrock.prompt", lambda: "System prompt", raising=False)

    conversation = [{"role": "assistant", "content": "Hi!"}]
    service = BedrockAIService()
    messages = service._build_messages(conversation, "Hello")

    assert messages[0]["content"][0]["text"].startswith("System:")
    assert messages[-1]["content"][0]["text"] == "Hello"
    assert len(messages) == 3


def test_openai_build_messages_includes_system_and_user(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.ai.openai.openai_client", object(), raising=False)
    monkeypatch.setattr("app.services.ai.openai.prompt", lambda: "System prompt", raising=False)

    conversation = [{"role": "assistant", "content": "Hi!"}]
    service = OpenAIAIService()
    messages = service._build_messages(conversation, "Hello")

    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "Hello"
    assert len(messages) == 3


def test_ollama_build_messages_includes_system_and_user(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.ai.ollama.prompt", lambda: "System prompt", raising=False)

    conversation = [{"role": "assistant", "content": "Hi!"}]
    service = OllamaAIService()
    messages = service._build_messages(conversation, "Hello")

    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "Hello"
    assert len(messages) == 3


def test_bedrock_ai_service_success(monkeypatch: pytest.MonkeyPatch):
    class FakeBedrockClient:
        def __init__(self) -> None:
            self.called_with: Dict[str, Any] | None = None

        def converse(self, **kwargs: Any) -> Dict[str, Any]:
            self.called_with = kwargs
            return {
                "output": {
                    "message": {"content": [{"text": "Bedrock reply"}]},
                }
            }

    fake_client = FakeBedrockClient()
    monkeypatch.setattr("app.services.ai.bedrock.bedrock_client", fake_client, raising=False)
    monkeypatch.setattr("app.services.ai.bedrock.prompt", lambda: "System prompt", raising=False)

    service = BedrockAIService()
    result = service.generate_response([], "Hello")

    assert result == "Bedrock reply"
    assert fake_client.called_with is not None
    assert fake_client.called_with["modelId"]


def test_bedrock_ai_service_handles_client_error(monkeypatch: pytest.MonkeyPatch):
    class FakeError(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)
            self.response = {"Error": {"Code": "ValidationException"}}

    class FakeBedrockClient:
        def converse(self, **kwargs: Any) -> Dict[str, Any]:
            raise FakeError("bad request")

    monkeypatch.setattr("app.services.ai.bedrock.bedrock_client", FakeBedrockClient(), raising=False)
    monkeypatch.setattr("app.services.ai.bedrock.ClientError", FakeError, raising=False)
    monkeypatch.setattr("app.services.ai.bedrock.prompt", lambda: "System prompt", raising=False)

    service = BedrockAIService()
    with pytest.raises(Exception) as exc_info:
        service.generate_response([], "Hello")

    assert type(exc_info.value).__name__ == "HTTPException"
    assert getattr(exc_info.value, "status_code", None) == 400


def test_openai_ai_service_success(monkeypatch: pytest.MonkeyPatch):
    class Choice:
        def __init__(self, content: str) -> None:
            self.message = type("Message", (), {"content": content})

    class FakeResponse:
        def __init__(self) -> None:
            self.choices = [Choice("OpenAI reply")]

    class FakeCompletions:
        def __init__(self) -> None:
            self.called_with: Dict[str, Any] | None = None

        def create(self, **kwargs: Any) -> FakeResponse:
            self.called_with = kwargs
            return FakeResponse()

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeOpenAIClient:
        def __init__(self) -> None:
            self.chat = FakeChat()

    fake_client = FakeOpenAIClient()
    monkeypatch.setattr("app.services.ai.openai.openai_client", fake_client, raising=False)
    monkeypatch.setattr("app.services.ai.openai.prompt", lambda: "System prompt", raising=False)

    service = OpenAIAIService()
    result = service.generate_response([], "Hello")

    assert result == "OpenAI reply"


def test_openai_ai_service_handles_errors(monkeypatch: pytest.MonkeyPatch):
    class FakeCompletions:
        def create(self, **kwargs: Any) -> None:
            raise RuntimeError("API down")

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeOpenAIClient:
        def __init__(self) -> None:
            self.chat = FakeChat()

    fake_client = FakeOpenAIClient()
    monkeypatch.setattr("app.services.ai.openai.openai_client", fake_client, raising=False)
    monkeypatch.setattr("app.services.ai.openai.prompt", lambda: "System prompt", raising=False)

    service = OpenAIAIService()
    with pytest.raises(Exception) as exc_info:
        service.generate_response([], "Hello")

    assert type(exc_info.value).__name__ == "HTTPException"
    assert getattr(exc_info.value, "status_code", None) == 500


def test_ollama_ai_service_success(monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        def __init__(self, payload: Dict[str, Any]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> Dict[str, Any]:
            return self._payload

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        return FakeResponse({"message": {"content": "Ollama reply"}})

    monkeypatch.setattr("app.services.ai.ollama.requests.post", fake_post, raising=False)
    monkeypatch.setattr("app.services.ai.ollama.prompt", lambda: "System prompt", raising=False)

    service = OllamaAIService()
    result = service.generate_response([], "Hello")

    assert result == "Ollama reply"


def test_ollama_ai_service_handles_errors(monkeypatch: pytest.MonkeyPatch):
    def fake_post(*args: Any, **kwargs: Any) -> None:
        raise requests.RequestException("connection error")

    monkeypatch.setattr("app.services.ai.ollama.requests.post", fake_post, raising=False)
    monkeypatch.setattr("app.services.ai.ollama.prompt", lambda: "System prompt", raising=False)

    service = OllamaAIService()
    with pytest.raises(Exception) as exc_info:
        service.generate_response([], "Hello")

    assert type(exc_info.value).__name__ == "HTTPException"
    assert getattr(exc_info.value, "status_code", None) == 502


def test_get_ai_service_respects_provider(monkeypatch: pytest.MonkeyPatch):
    ai_pkg.get_ai_service.cache_clear()
    monkeypatch.setattr("app.services.ai.AI_PROVIDER", "openai", raising=False)

    class _FakeOpenAICompletions:
        def create(self, **kwargs: Any) -> Dict[str, Any]:
            return {"choices": [{"message": {"content": ""}}]}

    class _FakeOpenAIChat:
        def __init__(self) -> None:
            self.completions = _FakeOpenAICompletions()

    class _FakeOpenAIClient:
        def __init__(self) -> None:
            self.chat = _FakeOpenAIChat()

    monkeypatch.setattr("app.services.ai.openai.openai_client", _FakeOpenAIClient(), raising=False)

    service = get_ai_service()
    assert isinstance(service, OpenAIAIService)

    ai_pkg.get_ai_service.cache_clear()
    monkeypatch.setattr("app.services.ai.AI_PROVIDER", "ollama", raising=False)
    monkeypatch.setattr("app.services.ai.ollama.prompt", lambda: "System prompt", raising=False)
    monkeypatch.setattr("app.services.ai.ollama.requests.post", lambda *args, **kwargs: type("R", (), {"raise_for_status": lambda self: None, "json": lambda self: {"message": {"content": ""}}})(), raising=False)

    service = get_ai_service()
    assert isinstance(service, OllamaAIService)

    ai_pkg.get_ai_service.cache_clear()
    monkeypatch.setattr("app.services.ai.AI_PROVIDER", "bedrock", raising=False)

    class _FakeBedrockClient:
        def converse(self, **kwargs: Any) -> Dict[str, Any]:
            return {"output": {"message": {"content": [{"text": ""}]}}}

    monkeypatch.setattr("app.services.ai.bedrock.bedrock_client", _FakeBedrockClient(), raising=False)

    service = get_ai_service()
    assert isinstance(service, BedrockAIService)

    ai_pkg.get_ai_service.cache_clear()
