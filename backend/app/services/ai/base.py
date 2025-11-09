"""Abstract base definitions for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterator, List


class AIService(ABC):
    """Abstract base class for AI completion providers."""

    _history_limit: int = 20

    @staticmethod
    def _truncate_history(conversation: List[Dict], limit: int) -> List[Dict]:
        """Return the most recent `limit` messages from the conversation."""
        if limit <= 0:
            return []
        return conversation[-limit:]

    @property
    def history_limit(self) -> int:
        return self._history_limit

    @history_limit.setter
    def history_limit(self, value: int) -> None:
        self._history_limit = max(0, value)

    @abstractmethod
    def generate_response(self, conversation: List[Dict], user_message: str) -> str:
        """Return the assistant response given the conversation and user message."""

    def stream_response(self, conversation: List[Dict], user_message: str) -> Iterator[str]:
        """
        Yield the assistant response incrementally.

        Providers that do not support native streaming can override this method.
        The default implementation yields the full response returned by `generate_response`.
        """
        yield self.generate_response(conversation, user_message)
