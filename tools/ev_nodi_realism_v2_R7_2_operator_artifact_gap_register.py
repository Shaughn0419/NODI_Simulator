"""Compatibility wrapper for ``tools.one_shot.ev_nodi_realism_v2_R7_2_operator_artifact_gap_register``."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._legacy_entrypoint import run_legacy_tool


if __name__ == "__main__":
    run_legacy_tool(
        "tools.one_shot.ev_nodi_realism_v2_R7_2_operator_artifact_gap_register",
        safe_help=True,
        require_execute=True,
        pass_execute_to_module=True,
    )
