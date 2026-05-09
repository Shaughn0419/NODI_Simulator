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
        default_output_dir=rv2.DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR,
        output_help="Directory for v2 no-measured-data closure outputs.",
    )
    result = rv2.run_v2_no_measured_data_closure(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(
        json.dumps(
            {
                "output_dir": result["output_dir"],
                "v2_no_measured_data_closure_run": result[
                    "v2_no_measured_data_closure_run"
                ],
                "closure_decision": result["closure_decision"],
                "selected_future_recommendation_class": result[
                    "selected_future_recommendation_class"
                ],
                "new_case_rows_added": result["new_case_rows_added"],
                "new_experiments_started": result["new_experiments_started"],
                "operator_artifact_acquisition_started": result[
                    "operator_artifact_acquisition_started"
                ],
                "R8_plan_preparation_authorized": result[
                    "R8_plan_preparation_authorized"
                ],
                "R8_execution_authorized": result["R8_execution_authorized"],
                "context_route_promotion_authorized": result[
                    "context_route_promotion_authorized"
                ],
                "main_660_redefinition_authorized": result[
                    "main_660_redefinition_authorized"
                ],
                "calibrated_event_probability_claim_emitted": result[
                    "calibrated_event_probability_claim_emitted"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
