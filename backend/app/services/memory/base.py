"""Abstract base definitions for memory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class MemoryService(ABC):
    """Abstract base class for storing and retrieving conversation memory."""

    @abstractmethod
    def load_conversation(self, session_id: str) -> List[Dict]:
        """Load the conversation for a given session."""

    @abstractmethod
    def save_conversation(self, session_id: str, messages: List[Dict]) -> None:
        """Persist the conversation for a given session."""
