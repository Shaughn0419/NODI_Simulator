from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import realism_v2 as rv2  # noqa: E402


def main() -> int:
    result = rv2.run_R7_1_operator_artifact_validation_protocol_generation()
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "R7_1_operator_artifact_validation_protocol_generation_run": result[
                    "R7_1_operator_artifact_validation_protocol_generation_run"
                ],
                "evidence_module_count": result["evidence_module_count"],
                "required_artifact_field_count": result[
                    "required_artifact_field_count"
                ],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "protocol_decision": result["protocol_decision"],
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
    raise SystemExit(main())
