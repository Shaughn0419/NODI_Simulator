"""Compatibility wrapper for ``tools.audits.tsuyama_paper_target_audit``."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._legacy_entrypoint import run_legacy_tool


if __name__ == "__main__":
    run_legacy_tool("tools.audits.tsuyama_paper_target_audit")
