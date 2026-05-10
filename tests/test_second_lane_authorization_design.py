from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_second_lane_authorization_design import (
    P6_REQUIRED_EVIDENCE_PATHS,
    P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    build_artifact_manifest,
    build_authorization_gate_record,
    build_candidate_lane_contract_manifest,
    build_p6_evidence_binding_manifest,
    validate_artifact_manifest,
    validate_authorization_gate_record,
    validate_candidate_lane_contract_manifest,
    validate_design_registry,
    validate_p6_evidence_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/second_lane_authorization_design_registry.yaml"
PLAN_PATH = "reports/104_EV_NODI_P7_second_lane_authorization_design_plan.md"
README_PATH = "results/post_v2_second_lane_authorization_design/README.md"
P6_EVIDENCE_BINDING_PATH = (
    "results/post_v2_second_lane_authorization_design/"
    "second_lane_authorization_design_p6_evidence_binding_manifest.json"
)
AUTHORIZATION_GATE_RECORD_PATH = (
    "results/post_v2_second_lane_authorization_design/"
    "second_lane_authorization_design_authorization_gate_record.json"
)
CANDIDATE_LANE_CONTRACT_PATH = (
    "results/post_v2_second_lane_authorization_design/"
    "second_lane_authorization_design_candidate_lane_contract_manifest.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_second_lane_authorization_design/"
    "second_lane_authorization_design_artifact_manifest.json"
)
SCHEMA_DOC_PATHS = (
    "docs/schemas/second_lane_authorization_design_p6_evidence_binding_manifest_schema.md",
    "docs/schemas/second_lane_authorization_design_authorization_gate_record_schema.md",
    "docs/schemas/second_lane_authorization_design_candidate_lane_contract_schema.md",
    "docs/schemas/second_lane_authorization_design_artifact_manifest_schema.md",
)


def _registry() -> dict:
    return rv2.load_json_yaml("second_lane_authorization_design_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p7_registry_is_design_only_and_blocks_execution() -> None:
    registry = validate_design_registry(_registry())

    assert registry["stage"] == "P7_second_lane_authorization_design_complete"
    assert registry["design_role"] == "authorization_design_only_no_solver_execution"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["p6_minimal_execution_scope_preserved"] is True
    for key in (
        "physical_solver_execution_authorized",
        "second_bounded_solver_lane_execution_authorized",
        "solver_output_generated",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "full_wave_solver_execution_authorized",
        "vector_solver_execution_authorized",
        "roughness_leakage_simulation_authorized",
        "transport_residence_time_simulation_authorized",
        "route_promotion_authorized",
        "raw_magnitude_final_gate_allowed",
        "solver_native_raw_magnitude_final_gate_allowed",
    ):
        assert registry[key] is False


def test_p7_generated_manifests_are_current() -> None:
    assert _load_json(P6_EVIDENCE_BINDING_PATH) == build_p6_evidence_binding_manifest(root_path("."))
    assert _load_json(AUTHORIZATION_GATE_RECORD_PATH) == build_authorization_gate_record(
        root_path(".")
    )
    assert _load_json(CANDIDATE_LANE_CONTRACT_PATH) == build_candidate_lane_contract_manifest(
        root_path(".")
    )
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p7_binds_p6_artifacts_without_promotion_or_calibration() -> None:
    manifest = validate_p6_evidence_binding_manifest(
        build_p6_evidence_binding_manifest(root_path("."))
    )

    assert tuple(entry["path"] for entry in manifest["evidence"]) == P6_REQUIRED_EVIDENCE_PATHS
    assert manifest["p6_trace_output_role"] == (
        "prior_trace_only_rank_pairwise_order_evidence_not_calibration_or_promotion"
    )
    assert manifest["p6_trace_used_as_calibrated_prediction"] is False
    assert manifest["p6_trace_used_as_physical_calibration"] is False
    assert manifest["p6_trace_used_as_route_promotion_evidence"] is False
    assert manifest["p6_trace_used_as_snr_lod_concentration_specificity_evidence"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["route_promotion_authorized"] is False


def test_p7_future_gate_records_phrase_as_not_received() -> None:
    record = validate_authorization_gate_record(build_authorization_gate_record(root_path(".")))
    lane = validate_candidate_lane_contract_manifest(
        build_candidate_lane_contract_manifest(root_path("."))
    )

    for manifest in (record, lane):
        assert manifest["required_future_authorization_phrase"] == (
            P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
        )
        assert manifest["future_authorization_phrase_already_received"] is False
        assert manifest["current_prompt_authorizes_second_lane_execution"] is False
        assert manifest["second_bounded_solver_lane_execution_authorized"] is False
        assert manifest["solver_output_generated"] is False


def test_p7_artifact_manifest_preserves_claim_and_execution_boundaries() -> None:
    manifest = validate_artifact_manifest(build_artifact_manifest(root_path(".")), root_path("."))

    assert manifest["claim_boundary"]["allowed_claim_level"] == (
        "second_lane_authorization_design_only"
    )
    assert manifest["claim_boundary"]["calibrated_snr_claim_allowed"] is False
    assert manifest["claim_boundary"]["absolute_lod_claim_allowed"] is False
    assert manifest["claim_boundary"]["true_ev_concentration_claim_allowed"] is False
    assert manifest["claim_boundary"]["biological_specificity_claim_allowed"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["physical_solver_execution_authorized"] is False


def test_p7_registry_and_manifests_reject_tampering() -> None:
    registry = deepcopy(_registry())
    registry["physical_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="physical_solver_execution_authorized=false"):
        validate_design_registry(registry)

    registry = deepcopy(_registry())
    registry["future_authorization_gate_contract"][
        "future_authorization_phrase_already_received"
    ] = True
    with pytest.raises(ValueError, match="future_authorization_phrase_already_received=false"):
        validate_design_registry(registry)

    registry = deepcopy(_registry())
    registry["p6_evidence_binding_contract"]["required_p6_artifact_paths"][0] = "results/drift.json"
    with pytest.raises(ValueError, match="P6 evidence path set drifted"):
        validate_design_registry(registry)

    manifest = build_p6_evidence_binding_manifest(root_path("."))
    manifest["p6_trace_output_role"] = "calibrated_prediction"
    with pytest.raises(ValueError, match="P6 trace output role drifted"):
        validate_p6_evidence_binding_manifest(manifest)

    record = build_authorization_gate_record(root_path("."))
    record["solver_output_generated"] = True
    with pytest.raises(ValueError, match="solver_output_generated=false"):
        validate_authorization_gate_record(record)

    artifact = build_artifact_manifest(root_path("."))
    artifact["raw_magnitude_final_gate_allowed"] = True
    with pytest.raises(ValueError, match="raw_magnitude_final_gate_allowed=false"):
        validate_artifact_manifest(artifact, root_path("."))


def test_p7_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH, *SCHEMA_DOC_PATHS):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p7_report_and_readme_are_in_claim_scan() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert PLAN_PATH in paths
    assert README_PATH in paths


def test_p7_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths


def test_p7_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_second_lane_authorization_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS second_lane_authorization_design_registry" in result.stdout
    assert "PASS second_lane_authorization_design_future_gate_not_authorized" in result.stdout
    assert "PASS second_lane_authorization_design_no_solver_execution_or_output" in result.stdout
