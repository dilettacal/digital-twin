"""Local filesystem-backed memory service."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List

from app.core.config import HISTORY_DIR
from app.core.logging import get_logger

from .base import MemoryService
from .utils import get_memory_path, safe_join, sanitize_session_id


class LocalMemoryService(MemoryService):
    """Store conversation memory on the local filesystem."""

    def __init__(self) -> None:
        self._logger = get_logger(__name__).bind(backend="local")

    def load_conversation(self, session_id: str) -> List[Dict]:
        self._logger.debug("memory_load_attempt", session_id=session_id)
        try:
            file_path = self._resolve_session_path(session_id)
        except ValueError as exc:
            self._logger.warning(
                "memory_load_invalid_session",
                session_id=session_id,
                error=str(exc),
            )
            return []
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as file:
                messages = json.load(file)
            self._logger.debug("memory_load_success", session_id=session_id, message_count=len(messages))
            return messages
        self._logger.debug("memory_load_empty", session_id=session_id)
        return []

    def save_conversation(self, session_id: str, messages: List[Dict]) -> None:
        self._logger.debug("memory_save_attempt", session_id=session_id, message_count=len(messages))
        os.makedirs(HISTORY_DIR, mode=0o700, exist_ok=True)
        try:
            file_path = self._resolve_session_path(session_id)
        except ValueError as exc:
            self._logger.error(
                "memory_save_invalid_session",
                session_id=session_id,
                error=str(exc),
            )
            raise
        try:
            self._write_conversation(file_path, messages)
        except Exception as exc:  # pragma: no cover - defensive branch
            self._logger.error(
                "memory_save_failure",
                session_id=session_id,
                error=str(exc),
            )
            raise
        self._logger.info("memory_save_success", session_id=session_id, message_count=len(messages), path=str(file_path))

    def _resolve_session_path(self, session_id: str) -> Path:
        safe_session_id = sanitize_session_id(session_id)
        return safe_join(HISTORY_DIR, get_memory_path(safe_session_id))

    def _write_conversation(self, file_path: Path, messages: List[Dict]) -> None:
        if not isinstance(messages, list) or not all(isinstance(message, dict) for message in messages):
            raise ValueError("Messages must be a list of dictionaries.")

        fd = None
        tmp_path = None
        try:
            fd, tmp_path_str = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.stem}.",
                suffix=".tmp",
            )
            tmp_path = Path(tmp_path_str)
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                fd = None  # fd now owned by file object
                json.dump(messages, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
        finally:
            if fd is not None:
                os.close(fd)

        if tmp_path is None:  # pragma: no cover - defensive branch
            raise RuntimeError("Failed to create temporary file for conversation save.")

        try:
            os.chmod(tmp_path, 0o600)
        except PermissionError:  # pragma: no cover - best-effort
            self._logger.warning("memory_save_chmod_failed", path=str(tmp_path))

        try:
            os.replace(tmp_path, file_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
