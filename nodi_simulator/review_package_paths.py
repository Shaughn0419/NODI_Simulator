"""Path normalization helpers for review-package artifacts."""

from __future__ import annotations

import unicodedata
from pathlib import Path


def normalize_relpath(path: str | Path) -> str:
    return unicodedata.normalize("NFC", Path(path).as_posix())
