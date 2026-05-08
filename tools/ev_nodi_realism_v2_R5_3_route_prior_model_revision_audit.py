from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import realism_v2 as rv2  # noqa: E402


def main() -> int:
    result = rv2.run_R5_3_route_prior_model_revision_audit()
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "R5_3_route_prior_model_revision_audit_run": result[
                    "R5_3_route_prior_model_revision_audit_run"
                ],
                "existing_R5_rows_audited": result["existing_R5_rows_audited"],
                "audit_route_id_count": result["audit_route_id_count"],
                "scenario_bundle_count": result["scenario_bundle_count"],
                "new_case_rows_added": result["new_case_rows_added"],
                "selected_candidate_prior_id": result["selected_candidate_prior_id"],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "audit_decision": result["audit_decision"],
                "weak_reference_delta_explained_fraction": result[
                    "weak_reference_delta_explained_fraction"
                ],
                "context_family_delta_explained_fraction": result[
                    "context_family_delta_explained_fraction"
                ],
                "context_routes_above_main_after_candidate": result[
                    "context_routes_above_main_after_candidate"
                ],
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
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
