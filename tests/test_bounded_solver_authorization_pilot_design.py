from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_bounded_solver_authorization_pilot_design import (
    P3_PILOT_LANE_ID,
    build_artifact_manifest,
    build_p2_route_binding_manifest,
    build_route_subset_manifest,
    build_schema_manifest,
    validate_p2_route_binding_manifest,
    validate_pilot_registry,
    validate_route_subset_manifest,
    validate_schema_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml"
PLAN_PATH = "reports/100_EV_NODI_P3_bounded_solver_authorization_pilot_design_plan.md"
README_PATH = "results/post_v2_bounded_solver_authorization_pilot_design/README.md"
P2_BINDING_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_p2_route_binding_manifest.json"
)
ROUTE_SUBSET_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_route_subset_manifest.json"
)
SCHEMA_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_schema_manifest.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_artifact_manifest.json"
)
P2_ROUTE_UNIVERSE_PATH = (
    "results/post_v2_bounded_physical_solver_readiness/"
    "bounded_physical_solver_readiness_route_universe_manifest.json"
)
SCHEMA_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/bounded_solver_authorization_pilot_design_schema_manifest_schema.md"
)
ROUTE_SUBSET_SCHEMA_DOC = (
    "docs/schemas/bounded_solver_authorization_pilot_design_route_subset_manifest_schema.md"
)
P2_BINDING_SCHEMA_DOC = (
    "docs/schemas/bounded_solver_authorization_pilot_design_p2_route_binding_manifest_schema.md"
)
ARTIFACT_SCHEMA_DOC = (
    "docs/schemas/bounded_solver_authorization_pilot_design_artifact_manifest_schema.md"
)


def _registry() -> dict:
    return rv2.load_json_yaml("bounded_solver_authorization_pilot_design_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p3_registry_is_authorization_planning_only() -> None:
    registry = validate_pilot_registry(_registry())

    assert (
        registry["schema_version"]
        == "ev_nodi_p3_bounded_solver_authorization_pilot_design_registry_v1"
    )
    assert registry["stage"] == "P3_bounded_solver_authorization_pilot_design_phase1"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["p1_surrogate_risk_role_preserved"] is True
    assert registry["p2_readiness_scope_preserved"] is True
    assert registry["physical_solver_execution_authorized"] is False
    assert registry["measured_data_ingest_authorized"] is False
    assert registry["solver_output_generated"] is False

    authority = registry["implementation_authority"]
    for key in (
        "physical_solver_execution_authorized",
        "full_wave_solver_execution_authorized",
        "green_tensor_solver_execution_authorized",
        "new_solver_case_generation_authorized",
        "new_mesh_generation_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "solver_output_generation_authorized",
        "route_promotion_authorized",
    ):
        assert authority[key] is False


def test_p3_claim_families_and_raw_gates_are_blocked() -> None:
    registry = _registry()
    claims = registry["claim_governance"]
    score = registry["score_governance"]

    for key in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "sample_count_claim_allowed",
        "measured_blank_safety_claim_allowed",
        "route_promotion_authorized",
    ):
        assert claims[key] is False
    assert claims["allowed_claim_level"] == "bounded_solver_authorization_pilot_design_only"
    assert set(score["allowed_gate_metric_families"]) == {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }
    assert score["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert score["solver_native_raw_magnitude_final_gate_allowed"] is False


def test_p3_single_lane_binds_p2_route_universe() -> None:
    registry = validate_pilot_registry(_registry())

    assert registry["p2_route_universe_binding"]["source_manifest_path"] == P2_ROUTE_UNIVERSE_PATH
    lanes = registry["pilot_design_lanes"]
    assert [lane["lane_id"] for lane in lanes] == [P3_PILOT_LANE_ID]

    lane = lanes[0]
    assert lane["lane_status"] == "phase1_pilot_design_only_not_executable"
    assert lane["physical_solver_execution_authorized"] is False
    assert lane["measured_data_ingest_authorized"] is False
    assert lane["solver_output_generated"] is False
    assert all(value is False for value in lane["execution_authority"].values())
    assert lane["route_subset_selection_rule"]["source_manifest_path"] == P2_ROUTE_UNIVERSE_PATH
    assert lane["route_subset_selection_rule"]["raw_proxy_fields_allowed"] is False
    assert lane["route_subset_selection_rule"]["route_promotion_evidence_allowed"] is False
    assert (
        lane["route_subset_selection_rule"]["optional_660_W900_D1400_redefines_main_660"]
        is False
    )


def test_p3_generated_manifests_are_current() -> None:
    assert _load_json(P2_BINDING_MANIFEST_PATH) == build_p2_route_binding_manifest(
        root_path(".")
    )
    assert _load_json(ROUTE_SUBSET_MANIFEST_PATH) == build_route_subset_manifest(
        root_path(".")
    )
    assert _load_json(SCHEMA_MANIFEST_PATH) == build_schema_manifest(root_path("."))
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p3_p2_route_binding_manifest_is_preflight_scope_only() -> None:
    manifest = validate_p2_route_binding_manifest(
        build_p2_route_binding_manifest(root_path("."))
    )

    assert manifest["bound_source_manifest_path"] == P2_ROUTE_UNIVERSE_PATH
    assert manifest["bound_route_universe_row_count"] == 572
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["p1_surrogate_risk_role_preserved"] is True
    assert manifest["p2_readiness_scope_preserved"] is True
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["measured_data_ingest_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["route_promotion_authorized"] is False


def test_p3_route_subset_manifest_uses_only_p2_bounded_rows() -> None:
    manifest = validate_route_subset_manifest(build_route_subset_manifest(root_path(".")))
    p2_routes = {
        row["candidate_id"]: row for row in _load_json(P2_ROUTE_UNIVERSE_PATH)["routes"]
    }

    assert manifest["source_manifest_path"] == P2_ROUTE_UNIVERSE_PATH
    assert manifest["selected_route_count"] == 3
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["measured_data_ingest_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["raw_magnitude_final_gate_allowed"] is False
    assert manifest["route_promotion_authorized"] is False

    selected_ids = {row["candidate_id"] for row in manifest["selected_routes"]}
    assert selected_ids.issubset(p2_routes)
    assert {"main_660_W800_D1400", "main_660_W800_D1500"}.issubset(selected_ids)
    assert any(
        row["full_wave_green_tensor_pairwise_inversion_flag"] is True
        for row in manifest["selected_routes"]
    )
    for row in manifest["selected_routes"]:
        assert row["calibrated_claim_allowed"] is False
        assert row["p0_release_conclusion_changed"] is False
        assert row["p1_surrogate_risk_role_preserved"] is True
        assert row["p2_readiness_scope_preserved"] is True
        assert row["physical_solver_execution_authorized"] is False
        assert row["measured_data_ingest_authorized"] is False
        assert row["solver_output_generated"] is False
        assert row["raw_magnitude_final_gate_allowed"] is False
        assert row["route_promotion_authorized"] is False
        assert not any(
            key.startswith("raw_") and key != "raw_magnitude_final_gate_allowed"
            for key in row
        )


def test_p3_schema_manifest_preserves_input_preflight_output_guards() -> None:
    manifest = validate_schema_manifest(build_schema_manifest(root_path(".")))

    assert manifest["lane_id"] == P3_PILOT_LANE_ID
    input_schema = manifest["solver_input_manifest_schema"]
    assert input_schema["source_manifest_path_required"] == P2_ROUTE_UNIVERSE_PATH
    assert input_schema["physical_solver_execution_authorized"] is False
    assert input_schema["measured_data_ingest_authorized"] is False
    assert input_schema["solver_output_generated"] is False
    assert input_schema["raw_magnitude_final_gate_allowed"] is False

    preflight = manifest["mesh_boundary_unit_preflight_schema"]
    assert all(value is False for value in preflight["execution_authority"].values())
    assert preflight["v1_bfp_to_angle_jacobian_applied"] is False
    assert preflight["audit_bfp_jacobian_applied"] is True

    output = manifest["output_schema_placeholder"]
    assert output["artifact_status"] == "output_schema_placeholder_no_solver_output"
    assert output["allowed_claim_level"] == "pilot_design_output_schema_placeholder_only"
    assert output["calibrated_claim_allowed"] is False
    assert output["physical_solver_execution_authorized"] is False
    assert output["measured_data_ingest_authorized"] is False
    assert output["solver_output_generated"] is False
    assert output["raw_magnitude_final_gate_allowed"] is False
    assert set(output["allowed_interpretability_families"]) == {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }


def test_p3_registry_rejects_execution_measured_and_route_promotion_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["physical_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_pilot_registry(registry)

    registry = deepcopy(_registry())
    registry["implementation_authority"]["measured_data_ingest_authorized"] = True
    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_pilot_registry(registry)

    registry = deepcopy(_registry())
    registry["claim_governance"]["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="must keep route_promotion_authorized=false"):
        validate_pilot_registry(registry)


def test_p3_registry_rejects_missing_p2_binding_and_scope_drift() -> None:
    registry = deepcopy(_registry())
    registry["p2_route_universe_binding"]["source_manifest_path"] = "results/other.json"
    with pytest.raises(ValueError, match="must reference the P2 route-universe"):
        validate_pilot_registry(registry)

    registry = deepcopy(_registry())
    registry["p2_route_universe_binding"][
        "source_manifest_schema_version_required"
    ] = "ev_nodi_p2_wrong_schema_v9"
    with pytest.raises(ValueError, match="schema-version requirement drifted"):
        validate_pilot_registry(registry)

    registry = deepcopy(_registry())
    registry["p2_readiness_scope_preserved"] = False
    with pytest.raises(ValueError, match="p2_readiness_scope_preserved=true"):
        validate_pilot_registry(registry)


def test_p3_schema_rejects_calibrated_output_and_raw_final_gate_tampering() -> None:
    manifest = build_schema_manifest(root_path("."))
    manifest["output_schema_placeholder"]["calibrated_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_claim_allowed=false"):
        validate_schema_manifest(manifest)

    manifest = build_schema_manifest(root_path("."))
    manifest["output_schema_placeholder"][
        "allowed_claim_level"
    ] = "calibrated_physical_prediction"
    with pytest.raises(ValueError, match="output claim level drifted"):
        validate_schema_manifest(manifest)

    manifest = build_schema_manifest(root_path("."))
    manifest["output_schema_placeholder"]["raw_magnitude_final_gate_allowed"] = True
    with pytest.raises(ValueError, match="output raw final gate drifted"):
        validate_schema_manifest(manifest)


def test_p3_route_subset_rejects_raw_proxy_and_route_promotion_tampering() -> None:
    manifest = build_route_subset_manifest(root_path("."))
    manifest["selected_routes"][0]["raw_complex_field_proxy_diagnostic_only"] = "0.1"
    with pytest.raises(ValueError, match="must not carry raw proxy fields"):
        validate_route_subset_manifest(manifest)

    manifest = build_route_subset_manifest(root_path("."))
    manifest["selected_routes"][0]["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route promotion drifted"):
        validate_route_subset_manifest(manifest)


def test_p3_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p3_manifest_schema_docs_preserve_boundaries() -> None:
    for path in (
        SCHEMA_MANIFEST_SCHEMA_DOC,
        ROUTE_SUBSET_SCHEMA_DOC,
        P2_BINDING_SCHEMA_DOC,
        ARTIFACT_SCHEMA_DOC,
    ):
        text = root_path(path).read_text(encoding="utf-8")
        assert "calibrated_claim_allowed = false" in text
        assert "p0_release_conclusion_changed = false" in text
        assert "p1_surrogate_risk_role_preserved = true" in text
        assert "p2_readiness_scope_preserved = true" in text
        assert "physical_solver_execution_authorized = false" in text
        assert "measured_data_ingest_authorized = false" in text
        assert "solver_output_generated = false" in text


def test_p3_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_bounded_solver_authorization_pilot_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS bounded_solver_authorization_pilot_design_registry" in result.stdout
    assert (
        "PASS bounded_solver_authorization_pilot_design_p2_route_binding_manifest_current"
        in result.stdout
    )
    assert (
        "PASS bounded_solver_authorization_pilot_design_route_subset_manifest_current"
        in result.stdout
    )
    assert "PASS bounded_solver_authorization_pilot_design_execution_blocked" in result.stdout
    assert (
        "PASS bounded_solver_authorization_pilot_design_measured_data_ingest_blocked"
        in result.stdout
    )
    assert "PASS bounded_solver_authorization_pilot_design_solver_output_absent" in result.stdout


def test_p3_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths
