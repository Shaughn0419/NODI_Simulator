from __future__ import annotations

import csv
from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_fourth_bounded_solver_lane_execution import (
    P12_SOLVER_OUTPUT_CSV,
    build_artifact_manifest,
    build_p11_authorization_binding_manifest,
    build_solver_output_manifest,
    build_solver_rows,
    validate_artifact_manifest,
    validate_execution_registry,
    validate_p11_authorization_binding_manifest,
    validate_solver_output_manifest,
    validate_solver_rows,
)
from nodi_simulator.post_v2_p10_closure_p11_authorization_design import (
    P11_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/fourth_bounded_solver_lane_execution_registry.yaml"
PLAN_PATH = "reports/111_EV_NODI_P12_fourth_bounded_solver_lane_execution_plan.md"
README_PATH = "results/post_v2_fourth_bounded_solver_lane_execution/README.md"
P11_BINDING_PATH = (
    "results/post_v2_fourth_bounded_solver_lane_execution/"
    "fourth_bounded_solver_lane_execution_p11_authorization_binding_manifest.json"
)
SOLVER_OUTPUT_MANIFEST_PATH = (
    "results/post_v2_fourth_bounded_solver_lane_execution/"
    "fourth_bounded_solver_lane_trace_output_manifest.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_fourth_bounded_solver_lane_execution/"
    "fourth_bounded_solver_lane_execution_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/fourth_bounded_solver_lane_execution_p11_authorization_binding_manifest_schema.md",
    "docs/schemas/fourth_bounded_solver_lane_execution_output_manifest_schema.md",
    "docs/schemas/fourth_bounded_solver_lane_execution_artifact_manifest_schema.md",
)


def _registry() -> dict:
    return rv2.load_json_yaml("fourth_bounded_solver_lane_execution_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def _csv_rows() -> list[dict[str, str]]:
    with root_path(P12_SOLVER_OUTPUT_CSV.as_posix()).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p12_registry_authorizes_only_fourth_bounded_trace_execution() -> None:
    registry = validate_execution_registry(_registry())

    assert registry["stage"] == "P12_fourth_bounded_solver_lane_execution_complete"
    assert registry["execution_role"] == "fourth_bounded_solver_lane_execution_trace_only"
    assert registry["physical_solver_execution_authorized"] is True
    assert registry["fourth_bounded_solver_lane_execution_authorized"] is True
    assert registry["solver_output_generated"] is True
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    for key in (
        "full_wave_solver_execution_authorized",
        "vector_solver_execution_authorized",
        "roughness_leakage_simulation_authorized",
        "transport_residence_time_simulation_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "route_promotion_authorized",
        "raw_magnitude_final_gate_allowed",
        "solver_native_raw_magnitude_final_gate_allowed",
    ):
        assert registry[key] is False


def test_p12_generated_artifacts_are_current() -> None:
    assert _load_json(P11_BINDING_PATH) == build_p11_authorization_binding_manifest(root_path("."))
    assert _load_json(SOLVER_OUTPUT_MANIFEST_PATH) == build_solver_output_manifest(root_path("."))
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p12_fourth_lane_output_is_rank_pairwise_trace_only() -> None:
    rows = validate_solver_rows(build_solver_rows(root_path(".")))
    csv_rows = _csv_rows()

    assert len(rows) == 3
    assert [row["fourth_lane_response_rank"] for row in rows] == [1, 2, 3]
    assert [row["fourth_lane_pairwise_order_signature"] for row in rows] == [
        "1_of_3",
        "2_of_3",
        "3_of_3",
    ]
    assert [row["fourth_lane_vs_p10_rank_delta"] for row in rows] == [0, 0, 0]
    assert {row["solver_output_generated"] for row in rows} == {True}
    assert {row["raw_magnitude_final_gate_allowed"] for row in rows} == {False}
    assert {row["solver_native_raw_magnitude_final_gate_allowed"] for row in rows} == {False}
    assert {row["route_promotion_authorized"] for row in rows} == {False}
    assert len(csv_rows) == 3
    assert "solver_native_fourth_lane_response_trace_only" in csv_rows[0]


def test_p12_binding_and_output_manifests_preserve_boundaries() -> None:
    binding = validate_p11_authorization_binding_manifest(
        build_p11_authorization_binding_manifest(root_path("."))
    )
    output = validate_solver_output_manifest(build_solver_output_manifest(root_path(".")))
    artifact = validate_artifact_manifest(build_artifact_manifest(root_path(".")), root_path("."))

    for manifest in (binding, output, artifact):
        assert manifest["calibrated_claim_allowed"] is False
        assert manifest["p0_release_conclusion_changed"] is False
        assert manifest["physical_solver_execution_authorized"] is True
        assert manifest["fourth_bounded_solver_lane_execution_authorized"] is True
        assert manifest["solver_output_generated"] is True
        assert manifest["measured_data_ingest_authorized"] is False
        assert manifest["calibration_data_ingest_authorized"] is False
        assert manifest["new_mesh_generation_authorized"] is False
        assert manifest["operator_export_generation_authorized"] is False
        assert manifest["full_wave_solver_execution_authorized"] is False
        assert manifest["vector_solver_execution_authorized"] is False
        assert manifest["route_promotion_authorized"] is False


def test_p12_records_required_phrase_and_binds_p11_gate() -> None:
    binding = validate_p11_authorization_binding_manifest(
        build_p11_authorization_binding_manifest(root_path("."))
    )

    assert binding["required_future_authorization_phrase"] == P11_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert binding["user_authorization_phrase_received"] == P11_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert binding["p11_gate_prior_decision"] == "not_authorized_pending_explicit_future_request"
    assert binding["bound_route_count"] == 3


def test_p12_registry_and_manifests_reject_scope_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["full_wave_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="implementation authority drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["authorization_evidence"]["user_authorization_phrase_received"] = "authorize everything"
    with pytest.raises(ValueError, match="user authorization phrase drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["solver_contract"]["selected_route_count"] = 4
    with pytest.raises(ValueError, match="selected route count drifted"):
        validate_execution_registry(registry)

    binding = build_p11_authorization_binding_manifest(root_path("."))
    binding["p10_trace_context_path"] = "results/other.csv"
    with pytest.raises(ValueError, match="P10 trace context path drifted"):
        validate_p11_authorization_binding_manifest(binding)

    output = build_solver_output_manifest(root_path("."))
    output["raw_solver_native_fields_role"] = "final_gate"
    with pytest.raises(ValueError, match="raw solver-native role drifted"):
        validate_solver_output_manifest(output)

    rows = build_solver_rows(root_path("."))
    rows[0]["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_solver_rows(rows)


def test_p12_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH, *SCHEMA_DOCS):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p12_report_and_readme_are_in_claim_scan() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert PLAN_PATH in paths
    assert README_PATH in paths


def test_p12_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths


def test_p12_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_fourth_bounded_solver_lane_execution.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS fourth_bounded_solver_lane_execution_registry" in result.stdout
    assert "PASS fourth_bounded_solver_lane_execution_output_csv_current" in result.stdout
    assert "PASS fourth_bounded_solver_lane_execution_claim_boundaries" in result.stdout
