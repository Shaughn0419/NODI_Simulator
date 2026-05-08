from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


_RESULT_DEPENDENCIES_BY_FILE: dict[str, tuple[Path, ...]] = {
    "test_realism_v2_R4_2_adjudication.py": (rv2.DEFAULT_R4_2_ADJUDICATION_DIR,),
    "test_realism_v2_R4_2_adjudication_plan.py": (rv2.DEFAULT_REVISED_R4_RERUN_DIR,),
    "test_realism_v2_R5_full_grid_v2.py": (rv2.DEFAULT_R5_FULL_GRID_V2_DIR,),
    "test_realism_v2_R5_plan.py": (rv2.DEFAULT_R4_2_ADJUDICATION_DIR,),
    "test_realism_v2_R5_1_interpretation.py": (rv2.DEFAULT_R5_1_INTERPRETATION_DIR,),
    "test_realism_v2_R5_1_next_stage_plan.py": (rv2.DEFAULT_R5_FULL_GRID_V2_DIR,),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit.py": (
        rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
    ),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py": (
        rv2.DEFAULT_R5_FULL_GRID_V2_DIR,
        rv2.DEFAULT_R5_1_INTERPRETATION_DIR,
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_audit.py": (
        rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_plan.py": (
        rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
    ),
    "test_realism_v2_R6_plan.py": (
        rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_R6_route_prior_sensitivity_audit.py": (
        rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR,
    ),
    "test_realism_v2_R7_plan.py": (rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR,),
    "test_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py": (
        rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_plan.py": (
        rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_protocol.py": (
        rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR,
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_generation.py": (
        rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR,
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_plan.py": (
        rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR,
    ),
    "test_realism_v2_no_measured_data_closure.py": (
        rv2.DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR,
        rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR,
    ),
    "test_realism_v2_reduced_grid_R3a.py": (rv2.DEFAULT_REDUCED_GRID_R3A_DIR,),
    "test_realism_v2_representative_full_wave_R4.py": (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
    ),
    "test_realism_v2_revised_R4_rerun.py": (rv2.DEFAULT_REVISED_R4_RERUN_DIR,),
    "test_realism_v2_revised_R4_rerun_plan.py": (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
        rv2.DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_route_model_revision_audit.py": (
        rv2.DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_route_model_revision_plan.py": (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
    ),
    "test_realism_v2_uncertainty_R3b.py": (rv2.DEFAULT_UNCERTAINTY_R3B_DIR,),
}


def _missing_paths(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if not path.exists()]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        path = Path(str(item.path))
        dependencies = _RESULT_DEPENDENCIES_BY_FILE.get(path.name)
        if not dependencies:
            continue
        missing = _missing_paths(dependencies)
        if not missing:
            continue
        missing_text = ", ".join(str(path) for path in missing)
        item.add_marker(
            pytest.mark.skip(
                reason=(
                    "requires precomputed realism_v2 result artifacts not present in "
                    f"this checkout: {missing_text}"
                )
            )
        )
