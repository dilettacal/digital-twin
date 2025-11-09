"""Business logic services."""

from __future__ import annotations

import importlib
import sys


def _ensure_memory_module() -> None:
    """Expose ``app.services.memory`` regardless of layout."""
    module_name = f"{__name__}.memory"
    if module_name in sys.modules:
        return

    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError:
        legacy_name = f"{__name__}.memory_service"
        legacy_module = importlib.import_module(legacy_name)
        sys.modules[module_name] = legacy_module


_ensure_memory_module()
