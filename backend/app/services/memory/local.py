"""Local filesystem-backed memory service."""

from __future__ import annotations

import json
import os
from typing import Dict, List

from app.core.config import HISTORY_DIR
from app.core.logging import get_logger

from .base import MemoryService
from .utils import get_memory_path, safe_join


class LocalMemoryService(MemoryService):
    """Store conversation memory on the local filesystem."""

    def __init__(self) -> None:
        self._logger = get_logger(__name__).bind(backend="local")

    def load_conversation(self, session_id: str) -> List[Dict]:
        self._logger.debug("memory_load_attempt", session_id=session_id)
        file_path = safe_join(HISTORY_DIR, get_memory_path(session_id))
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as file:
                messages = json.load(file)
            self._logger.debug("memory_load_success", session_id=session_id, message_count=len(messages))
            return messages
        self._logger.debug("memory_load_empty", session_id=session_id)
        return []

    def save_conversation(self, session_id: str, messages: List[Dict]) -> None:
        self._logger.debug("memory_save_attempt", session_id=session_id, message_count=len(messages))
        os.makedirs(HISTORY_DIR, exist_ok=True)
        file_path = safe_join(HISTORY_DIR, get_memory_path(session_id))
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(messages, file, indent=2)
        self._logger.info("memory_save_success", session_id=session_id, message_count=len(messages), path=str(file_path))
