from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_physical_ceiling import (
    CONTRACT_CONFIG_PATHS,
    PHYSICAL_CEILING_CONTRACT_MANIFEST,
    PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST,
    PHYSICAL_CEILING_INPUT_BINDING_MANIFEST,
    PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST,
    build_physical_ceiling_diagnostic_outputs,
    build_physical_ceiling_contract_manifest,
    build_physical_ceiling_diagnostic_schema_manifest,
    build_physical_ceiling_input_binding_manifest,
    build_physical_ceiling_route_coverage_manifest,
    validate_physical_ceiling_contract,
    validate_physical_ceiling_contract_manifest,
    validate_physical_ceiling_diagnostic_schema_manifest,
    validate_physical_ceiling_diagnostic_rows,
    validate_physical_ceiling_input_binding_manifest,
    validate_physical_ceiling_route_coverage_manifest,
    verify_physical_ceiling_contract_package,
    write_physical_ceiling_contract_manifest,
    write_physical_ceiling_manifests,
)
from nodi_simulator.review_package import (
    P1_PHYSICAL_CEILING_P0_PACKAGE_EXCLUDED_CONFIGS,
    _config_entries,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_physical_ceiling_contract_manifest_records_generated_no_solver_outputs() -> None:
    manifest = validate_physical_ceiling_contract_manifest(
        build_physical_ceiling_contract_manifest(root_path("."))
    )

    assert manifest["stage"] == "P1_no_solver_rank_diagnostics_complete"
    assert manifest["manifest_role"] == "contract_registry_and_generated_no_solver_output_guard"
    assert manifest["contract_count"] == 4
    assert manifest["contract_paths"] == list(CONTRACT_CONFIG_PATHS)
    assert manifest["diagnostic_outputs_generated"] is True
    assert manifest["solver_or_simulation_execution_authorized"] is False
    assert manifest["diagnostic_output_existing_count"] == manifest["diagnostic_output_count"]
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["physical_ceiling_role"] == "surrogate_risk_reduction_only"


def test_physical_ceiling_contract_manifest_contract_rows_fail_closed() -> None:
    manifest = build_physical_ceiling_contract_manifest(root_path("."))

    assert {row["lane_id"] for row in manifest["contracts"]} == {
        "full_wave_green_tensor_physical_ceiling_diagnostic",
        "vector_jones_polarization_diagnostic",
        "roughness_leakage_diagnostic",
        "transport_residence_time_diagnostic",
    }
    for row in manifest["contracts"]:
        assert row["planned_output_exists"] is True
        assert row["artifact_status"] == "generated_no_solver_rank_diagnostic"
        assert row["calibrated_claim_allowed"] is False
        assert row["p0_release_conclusion_changed"] is False
        assert row["physical_ceiling_role"] == "surrogate_risk_reduction_only"
        assert row["raw_magnitude_final_gate_allowed"] is False
        assert row["decision_authority"] == "diagnostic_flag_only_no_route_promotion"
        assert row["contract_sha256"]


def test_write_physical_ceiling_contract_manifest_writes_manifest_after_outputs() -> None:
    path = write_physical_ceiling_contract_manifest(root_path("."))
    manifest = json.loads(path.read_text(encoding="utf-8"))

    assert path.relative_to(root_path(".")).as_posix() == (
        PHYSICAL_CEILING_CONTRACT_MANIFEST.as_posix()
    )
    validate_physical_ceiling_contract_manifest(manifest)
    for output in manifest["diagnostic_output_paths"]:
        assert root_path(output).exists(), output


def test_physical_ceiling_contract_manifest_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/generate_post_v2_physical_ceiling_contract_manifest.py")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert PHYSICAL_CEILING_CONTRACT_MANIFEST.as_posix() in result.stdout
    assert PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST.as_posix() in result.stdout
    assert PHYSICAL_CEILING_INPUT_BINDING_MANIFEST.as_posix() in result.stdout
    assert PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST.as_posix() in result.stdout


def test_physical_ceiling_diagnostic_schema_manifest_records_outputs() -> None:
    manifest = validate_physical_ceiling_diagnostic_schema_manifest(
        build_physical_ceiling_diagnostic_schema_manifest(root_path("."))
    )

    assert manifest["stage"] == "P1_diagnostic_schema_manifest_generated_no_solver_outputs"
    assert manifest["schema_count"] == 4
    assert manifest["diagnostic_outputs_generated"] is True
    assert manifest["solver_or_simulation_execution_authorized"] is False
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    for schema in manifest["schemas"]:
        assert schema["planned_output_exists"] is True
        assert schema["artifact_status"] == "generated_no_solver_rank_diagnostic"
        assert schema["raw_magnitude_final_gate_allowed"] is False
        assert schema["decision_authority"] == "diagnostic_flag_only_no_route_promotion"
        assert "raw_magnitude_final_gate_allowed" in schema["required_false_columns"]
        assert "calibrated_claim_allowed" in schema["required_false_columns"]
        assert "p0_release_conclusion_changed" in schema["required_false_columns"]
        assert schema["required_role_column_value"] == "surrogate_risk_reduction_only"
        assert any("rank_percentile" in metric for metric in schema["primary_gate_metrics"])
        assert any("pairwise_inversion" in metric for metric in schema["primary_gate_metrics"])


def test_write_physical_ceiling_manifests_preserves_generated_diagnostic_csvs() -> None:
    paths = write_physical_ceiling_manifests(root_path("."))
    relpaths = {path.relative_to(root_path(".")).as_posix() for path in paths}

    assert relpaths == {
        PHYSICAL_CEILING_CONTRACT_MANIFEST.as_posix(),
        PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST.as_posix(),
        PHYSICAL_CEILING_INPUT_BINDING_MANIFEST.as_posix(),
        PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST.as_posix(),
    }

    schema_manifest = build_physical_ceiling_diagnostic_schema_manifest(root_path("."))
    for schema in schema_manifest["schemas"]:
        assert root_path(schema["planned_output_path"]).exists(), schema[
            "planned_output_path"
        ]


def test_physical_ceiling_input_binding_manifest_binds_declared_p0_sources() -> None:
    manifest = validate_physical_ceiling_input_binding_manifest(
        build_physical_ceiling_input_binding_manifest(root_path("."))
    )

    assert manifest["stage"] == "P1_input_binding_manifest_generated_no_solver_outputs"
    assert manifest["binding_count"] > 0
    assert manifest["diagnostic_outputs_generated"] is True
    assert manifest["solver_or_simulation_execution_authorized"] is False
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    for binding in manifest["bindings"]:
        assert binding["source_exists"] is True
        assert binding["source_sha256"]
        assert binding["required_fields_present"] is True
        assert binding["missing_required_fields"] == []
        assert binding["calibrated_claim_allowed"] is False
        assert binding["p0_release_conclusion_changed"] is False
        assert binding["diagnostic_output_generated"] is True
        assert binding["physical_ceiling_role"] == "surrogate_risk_reduction_only"


def test_physical_ceiling_route_coverage_manifest_covers_primary_routes() -> None:
    manifest = validate_physical_ceiling_route_coverage_manifest(
        build_physical_ceiling_route_coverage_manifest(root_path("."))
    )

    assert manifest["stage"] == "P1_route_coverage_manifest_generated_no_solver_outputs"
    assert manifest["lane_count"] == 4
    assert manifest["primary_route_key_count"] > 0
    assert manifest["diagnostic_outputs_generated"] is True
    assert manifest["solver_or_simulation_execution_authorized"] is False
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    for lane in manifest["lanes"]:
        assert lane["planned_output_exists"] is True
        assert lane["route_key_source_count"] > 0
        assert lane["route_key_sources_with_full_primary_coverage"] > 0
        assert lane["diagnostic_output_generated"] is True
        assert lane["physical_ceiling_role"] == "surrogate_risk_reduction_only"
    for source in manifest["source_bindings"]:
        if source["source_has_route_key_field"]:
            assert source["missing_primary_route_key_count"] == 0
            assert source["missing_primary_route_keys"] == []


def test_physical_ceiling_contracts_are_not_p0_review_package_configs() -> None:
    config_paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert set(P1_PHYSICAL_CEILING_P0_PACKAGE_EXCLUDED_CONFIGS).isdisjoint(config_paths)
    assert "configs/realism_v2/r5_scenario_bundle_manifest.yaml" in config_paths


def test_physical_ceiling_results_readme_keeps_no_solver_output_boundary() -> None:
    text = root_path("results/post_v2_physical_ceiling/README.md").read_text(
        encoding="utf-8"
    )

    assert "generated no-solver rank diagnostics" in text
    assert "surrogate_risk_reduction_only" in text
    assert "does not change the P0 release conclusion" in text
    for filename in (
        "full_wave_green_tensor_diagnostic.csv",
        "vector_jones_polarization_diagnostic.csv",
        "roughness_leakage_diagnostic.csv",
        "transport_residence_time_diagnostic.csv",
    ):
        assert filename in text
        assert root_path(f"results/post_v2_physical_ceiling/{filename}").exists()


def test_physical_ceiling_generated_outputs_preserve_guard_columns() -> None:
    outputs = build_physical_ceiling_diagnostic_outputs(root_path("."))

    assert {len(rows) for rows in outputs.values()} == {572}
    for rows in outputs.values():
        validate_physical_ceiling_diagnostic_rows(rows, "unit-test generated rows")
        for row in rows:
            assert row["calibrated_claim_allowed"] is False
            assert row["p0_release_conclusion_changed"] is False
            assert row["raw_magnitude_final_gate_allowed"] is False
            assert row["physical_ceiling_role"] == "surrogate_risk_reduction_only"


def test_physical_ceiling_diagnostic_row_validation_rejects_claim_drift() -> None:
    rows = build_physical_ceiling_diagnostic_outputs(root_path("."))[
        PHYSICAL_CEILING_CONTRACT_MANIFEST.parent / "full_wave_green_tensor_diagnostic.csv"
    ]
    tampered = [dict(row) for row in rows]
    tampered[0]["calibrated_claim_allowed"] = True

    with pytest.raises(ValueError, match="calibrated_claim_allowed"):
        validate_physical_ceiling_diagnostic_rows(tampered, "tampered full-wave rows")


def test_physical_ceiling_contract_validation_rejects_solver_authority_drift() -> None:
    contract = rv2.load_json_yaml(root_path(CONTRACT_CONFIG_PATHS[0]))
    tampered = deepcopy(contract)
    tampered["execution_authority"]["solver_execution_authorized"] = True

    with pytest.raises(ValueError, match="solver_execution_authorized"):
        validate_physical_ceiling_contract(tampered)


def test_physical_ceiling_contract_validation_rejects_role_drift() -> None:
    contract = rv2.load_json_yaml(root_path(CONTRACT_CONFIG_PATHS[0]))
    tampered = deepcopy(contract)
    tampered["physical_ceiling_role"] = "calibrated_physical_prediction"

    with pytest.raises(ValueError, match="role drifted"):
        validate_physical_ceiling_contract(tampered)


def test_verify_physical_ceiling_contract_package_passes_with_no_solver_outputs() -> None:
    result = verify_physical_ceiling_contract_package(root_path("."))

    assert result == [
        "PASS physical_ceiling_no_solver_diagnostics_current",
        "PASS physical_ceiling_contract_manifest_current",
        "PASS physical_ceiling_diagnostic_schema_manifest_current",
        "PASS physical_ceiling_input_binding_manifest_current",
        "PASS physical_ceiling_route_coverage_manifest_current",
        "PASS physical_ceiling_solver_or_simulation_execution_blocked",
        "PASS physical_ceiling_claim_boundaries",
        "PASS physical_ceiling_readme_boundary",
    ]


def test_verify_physical_ceiling_contract_package_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_physical_ceiling_contracts.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS physical_ceiling_input_binding_manifest_current" in result.stdout
    assert "PASS physical_ceiling_route_coverage_manifest_current" in result.stdout
    assert "PASS physical_ceiling_no_solver_diagnostics_current" in result.stdout
    assert "PASS physical_ceiling_solver_or_simulation_execution_blocked" in result.stdout
    assert "PASS physical_ceiling_claim_boundaries" in result.stdout


def test_physical_ceiling_manifest_schema_docs_preserve_boundaries() -> None:
    manifest_docs = [
        (
            root_path("docs/schemas/physical_ceiling_contract_manifest_schema.md"),
            build_physical_ceiling_contract_manifest(root_path(".")),
            ["planned_output_exists = true"],
        ),
        (
            root_path("docs/schemas/physical_ceiling_diagnostic_schema_manifest_schema.md"),
            build_physical_ceiling_diagnostic_schema_manifest(root_path(".")),
            ["planned_output_exists = true"],
        ),
        (
            root_path("docs/schemas/physical_ceiling_input_binding_manifest_schema.md"),
            build_physical_ceiling_input_binding_manifest(root_path(".")),
            ["diagnostic_output_generated = true"],
        ),
        (
            root_path("docs/schemas/physical_ceiling_route_coverage_manifest_schema.md"),
            build_physical_ceiling_route_coverage_manifest(root_path(".")),
            ["planned_output_exists = true", "diagnostic_output_generated = true"],
        ),
    ]

    for path, manifest, expected_snippets in manifest_docs:
        text = path.read_text(encoding="utf-8")
        assert manifest["manifest_role"] in text
        assert "calibrated_claim_allowed = false" in text
        assert "p0_release_conclusion_changed = false" in text
        assert "physical_ceiling_role = surrogate_risk_reduction_only" in text
        assert "diagnostic_outputs_generated = true" in text
        assert "solver_or_simulation_execution_authorized = false" in text
        for snippet in expected_snippets:
            assert snippet in text
        assert "empty_output_guard" not in text
        assert "does not generate" not in text


def test_physical_ceiling_completion_note_preserves_boundaries() -> None:
    text = root_path(
        "reports/97_EV_NODI_P1_physical_ceiling_contract_manifest_completion_note.md"
    ).read_text(encoding="utf-8")

    assert "does not change the P0 release conclusion" in text
    assert "no-measured-data relative audit" in text
    assert "calibrated_claim_allowed = false" in text
    assert "p0_release_conclusion_changed = false" in text
    assert "physical_ceiling_role = surrogate_risk_reduction_only" in text
    assert "Generated no-solver rank diagnostic CSVs" in text
    assert "P1 physical-ceiling config artifacts are excluded from P0" in text
    assert "empty-output" not in text
