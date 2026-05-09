from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator import realism_v2 as rv2  # noqa: E402
from tools._common import parse_realism_v2_writer_args  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_realism_v2_writer_args(
        argv,
        description=__doc__,
        default_output_dir=rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
        output_help="Directory for R7 mechanistic decomposition audit outputs.",
    )
    result = rv2.run_R7_route_prior_mechanistic_decomposition_audit(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "R7_route_prior_mechanistic_decomposition_audit_run": result[
                    "R7_route_prior_mechanistic_decomposition_audit_run"
                ],
                "existing_R5_rows_interpreted": result[
                    "existing_R5_rows_interpreted"
                ],
                "mechanistic_candidate_count": result[
                    "mechanistic_candidate_count"
                ],
                "executable_existing_artifact_mechanistic_candidate_count": result[
                    "executable_existing_artifact_mechanistic_candidate_count"
                ],
                "physical_operator_artifact_gap_count": result[
                    "physical_operator_artifact_gap_count"
                ],
                "particle_stratum_residual_warning_count": result[
                    "particle_stratum_residual_warning_count"
                ],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "audit_decision": result["audit_decision"],
                "R8_plan_preparation_authorized": result[
                    "R8_plan_preparation_authorized"
                ],
                "R8_execution_authorized": result["R8_execution_authorized"],
                "new_experiment_authorized": result["new_experiment_authorized"],
                "context_route_promotion_authorized": result[
                    "context_route_promotion_authorized"
                ],
                "main_660_redefinition_authorized": result[
                    "main_660_redefinition_authorized"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
