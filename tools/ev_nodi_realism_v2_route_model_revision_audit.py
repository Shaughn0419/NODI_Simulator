from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator.realism_v2 import (  # noqa: E402
    DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
    run_R4_route_model_revision_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run EV/NODI realism v2 R4 route-model revision audit only."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
        help="Output directory for route-model revision audit artifacts.",
    )
    args = parser.parse_args(argv)
    result = run_R4_route_model_revision_audit(args.output_dir)
    printable = {
        "output_dir": result["output_dir"],
        "source_observable_rows": result["source_observable_rows"],
        "source_route_rows": result["source_route_rows"],
        "best_allowed_convention_id": result["best_allowed_convention_id"],
        "best_main_660_nonblank_sign_preserved_fraction": result[
            "best_main_660_nonblank_sign_preserved_fraction"
        ],
        "main_660_recovery_gate_met": result["main_660_recovery_gate_met"],
        "route_model_revision_audit_decision": result[
            "route_model_revision_audit_decision"
        ],
        "R5_plan_preparation_authorized": result["R5_plan_preparation_authorized"],
        "R5_full_grid_v2_run": result["R5_full_grid_v2_run"],
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
