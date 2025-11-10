"""Shared utilities for memory services."""

from __future__ import annotations

import re
from pathlib import Path
from werkzeug.utils import secure_filename

_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def sanitize_session_id(session_id: str) -> str:
    """Validate and sanitize session IDs before using them in storage."""
    if not session_id:
        raise ValueError("Session ID must be provided.")
    if not _SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Session ID contains invalid characters.")
    return session_id


def get_memory_path(session_id: str) -> str:
    """Return the storage path for a session (guaranteed safe basename)."""
    safe_session_id = sanitize_session_id(session_id)
    filename = secure_filename(f"{safe_session_id}.json")
    if filename != f"{safe_session_id}.json":
        # Defensive: refuse if secure_filename mangles output (should never happen!)
        raise ValueError("Session ID results in unsafe filename.")
    return filename


def safe_join(base_dir: str, filename: str) -> Path:
    """
    Safely join paths ensuring the final path stays within base_dir.
    Rejects attempts to traverse outside the base directory.
    """
    base_path = Path(base_dir).resolve()

    filename_path = Path(filename)
    if filename_path.is_absolute() or ".." in filename_path.parts:
        raise ValueError("Invalid filename: path traversal detected.")

    candidate_path = (base_path / filename_path).resolve()

    try:
        candidate_path.relative_to(base_path)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError("Invalid path: outside base directory.") from exc

    return candidate_path
