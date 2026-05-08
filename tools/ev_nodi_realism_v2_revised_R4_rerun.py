#!/usr/bin/env python3
"""Execute the capped revised R4 rerun only."""

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
        default=str(rv2.DEFAULT_REVISED_R4_RERUN_DIR),
        help="Directory for revised R4 rerun outputs.",
    )
    parser.add_argument(
        "--no-root-manifest",
        action="store_true",
        help="Do not update the repository-root run_manifest.json.",
    )
    args = parser.parse_args()

    result = rv2.run_revised_R4_rerun(
        args.output_dir,
        write_root_manifest=not args.no_root_manifest,
    )
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "solver_case_rows": result["solver_case_rows"],
                "under_R4_revised_rerun_review_cap": result[
                    "under_R4_revised_rerun_review_cap"
                ],
                "best_allowed_convention_id": result["best_allowed_convention_id"],
                "all_nonblank_sign_preserved_after_global_flip": result[
                    "all_nonblank_sign_preserved_after_global_flip"
                ],
                "main_660_nonblank_sign_preserved_after_global_flip": result[
                    "main_660_nonblank_sign_preserved_after_global_flip"
                ],
                "main_660_sign_reliable_subset_fraction": result[
                    "main_660_sign_reliable_subset_fraction"
                ],
                "main_660_review_refined_mesh_fraction": result[
                    "main_660_review_refined_mesh_fraction"
                ],
                "main_660_recovery_gate_met": result[
                    "main_660_recovery_gate_met"
                ],
                "revised_R4_recovery_decision": result[
                    "revised_R4_recovery_decision"
                ],
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
