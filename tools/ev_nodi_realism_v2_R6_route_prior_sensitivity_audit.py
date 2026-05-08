from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import realism_v2 as rv2  # noqa: E402


def main() -> int:
    result = rv2.run_R6_route_prior_sensitivity_audit()
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "R6_route_prior_sensitivity_audit_run": result[
                    "R6_route_prior_sensitivity_audit_run"
                ],
                "existing_R5_rows_audited": result["existing_R5_rows_audited"],
                "candidate_prior_count": result["candidate_prior_count"],
                "derived_candidate_rows_evaluated": result[
                    "derived_candidate_rows_evaluated"
                ],
                "nearby_warning_resolved_candidate_count": result[
                    "nearby_warning_resolved_candidate_count"
                ],
                "main660_retention_warning_candidate_count": result[
                    "main660_retention_warning_candidate_count"
                ],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "audit_decision": result["audit_decision"],
                "R7_plan_preparation_authorized": result[
                    "R7_plan_preparation_authorized"
                ],
                "R7_execution_authorized": result["R7_execution_authorized"],
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
