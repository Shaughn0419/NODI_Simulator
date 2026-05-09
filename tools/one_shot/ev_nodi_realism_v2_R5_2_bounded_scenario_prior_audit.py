#!/usr/bin/env python3
"""Run the EV/NODI realism v2 R5.2 bounded scenario-prior audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections.abc import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator import realism_v2 as rv2  # noqa: E402
from tools._common import parse_realism_v2_writer_args  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_realism_v2_writer_args(
        argv,
        description=__doc__,
        default_output_dir=rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
        output_help="Directory for R5.2 bounded scenario-prior audit outputs.",
    )
    result = rv2.run_R5_2_bounded_scenario_prior_audit(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "R5_2_bounded_scenario_prior_audit_run": result[
                    "R5_2_bounded_scenario_prior_audit_run"
                ],
                "existing_R5_rows_audited": result["existing_R5_rows_audited"],
                "audit_route_id_count": result["audit_route_id_count"],
                "scenario_bundle_count": result["scenario_bundle_count"],
                "new_case_rows_added": result["new_case_rows_added"],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "audit_decision": result["audit_decision"],
                "R6_plan_preparation_authorized": result[
                    "R6_plan_preparation_authorized"
                ],
                "R6_execution_authorized": result["R6_execution_authorized"],
                "R5_followup_expansion_authorized": result[
                    "R5_followup_expansion_authorized"
                ],
                "context_route_promotion_authorized": result[
                    "context_route_promotion_authorized"
                ],
                "main_660_redefinition_authorized": result[
                    "main_660_redefinition_authorized"
                ],
                "weak_reference_exceeds_main_660_scenario_count": result[
                    "weak_reference_exceeds_main_660_scenario_count"
                ],
                "context_routes_above_main_under_all_scenarios": result[
                    "context_routes_above_main_under_all_scenarios"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
