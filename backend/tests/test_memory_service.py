"""Unit tests for memory service implementations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.memory import LocalMemoryService, S3MemoryService
from app.services.memory.utils import get_memory_path, safe_join, sanitize_session_id


def test_sanitize_session_id_accepts_valid_values():
    assert sanitize_session_id("session-123") == "session-123"
    assert sanitize_session_id("abc_123") == "abc_123"


@pytest.mark.parametrize("invalid", ["", "bad/session", "with spaces", "!" * 65])
def test_sanitize_session_id_rejects_invalid_values(invalid: str):
    with pytest.raises(ValueError):
        sanitize_session_id(invalid)


def test_safe_join_prevents_traversal(tmp_path: Path):
    base_dir = tmp_path.as_posix()
    with pytest.raises(ValueError):
        safe_join(base_dir, "../escape.json")


def test_local_memory_service_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    memory_dir = tmp_path / "memory"
    monkeypatch.setattr("app.services.memory.local.MEMORY_DIR", memory_dir.as_posix(), raising=False)

    service = LocalMemoryService()
    session_id = "test-session"

    # Initially empty
    assert service.load_conversation(session_id) == []

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    service.save_conversation(session_id, messages)

    assert service.load_conversation(session_id) == messages
    saved_file = safe_join(memory_dir.as_posix(), get_memory_path(session_id))
    assert Path(saved_file).exists()
    assert json.loads(Path(saved_file).read_text(encoding="utf-8")) == messages


def test_get_memory_service_selects_local(monkeypatch: pytest.MonkeyPatch):
    from app.services import memory as memory_pkg

    memory_pkg.get_memory_service.cache_clear()
    monkeypatch.setattr(memory_pkg, "USE_S3", False, raising=False)

    service = memory_pkg.get_memory_service()
    assert isinstance(service, LocalMemoryService)

    memory_pkg.get_memory_service.cache_clear()


def test_get_memory_service_selects_s3(monkeypatch: pytest.MonkeyPatch):
    from app.services import memory as memory_pkg

    class _FakeS3Client:
        def get_object(self, *args, **kwargs):
            raise NotImplementedError

        def put_object(self, *args, **kwargs):
            raise NotImplementedError

    fake_client = _FakeS3Client()

    memory_pkg.get_memory_service.cache_clear()
    monkeypatch.setattr(memory_pkg, "USE_S3", True, raising=False)
    monkeypatch.setattr("app.services.memory.s3.s3_client", fake_client, raising=False)
    monkeypatch.setattr("app.services.memory.s3.S3_BUCKET", "test-bucket", raising=False)

    service = memory_pkg.get_memory_service()
    assert isinstance(service, S3MemoryService)

    memory_pkg.get_memory_service.cache_clear()
