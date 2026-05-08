#!/usr/bin/env python3
"""Execute the capped R4.2 main-660 near-wall mesh adjudication only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARENT = PROJECT_ROOT.parent
for candidate in (PROJECT_ROOT, PARENT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

try:
    from nodi_simulator import realism_v2 as rv2
except ModuleNotFoundError:  # pragma: no cover - direct bundle fallback
    import realism_v2 as rv2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=str(rv2.DEFAULT_R4_2_ADJUDICATION_DIR),
        help="Directory for R4.2 adjudication outputs.",
    )
    parser.add_argument(
        "--write-root-manifest",
        action="store_true",
        help="Also update the repository-root run_manifest.json.",
    )
    args = parser.parse_args()

    result = rv2.run_R4_2_main660_nearwall_mesh_adjudication(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "solver_case_rows": result["solver_case_rows"],
                "under_R4_2_review_cap": result["under_R4_2_review_cap"],
                "fine_confirm_main660_fraction": result[
                    "fine_confirm_main660_fraction"
                ],
                "fine_confirm_sign_reliable_subset_fraction": result[
                    "fine_confirm_sign_reliable_subset_fraction"
                ],
                "review_refined_main660_fraction": result[
                    "review_refined_main660_fraction"
                ],
                "fine_confirm_agrees_with_review_refined": result[
                    "fine_confirm_agrees_with_review_refined"
                ],
                "coarse_screen_sign_fraction": result["coarse_screen_sign_fraction"],
                "R4_2_gate_met": result["R4_2_gate_met"],
                "R4_2_recovery_decision": result["R4_2_recovery_decision"],
                "R5_plan_preparation_authorized": result[
                    "R5_plan_preparation_authorized"
                ],
                "R5_full_grid_v2_run": result["R5_full_grid_v2_run"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
