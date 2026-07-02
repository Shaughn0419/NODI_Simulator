from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows, write_csv_rows
from tools.audits import (
    build_nodi_package_c_sidewall_wet_surface_observation_manifest_import as builder,
)
from tests.test_sidewall_wet_surface_observation_manifest_import import (
    _contract_rows,
    _manifest_rows,
)


def test_manifest_import_builder_defaults_to_manifest_required(tmp_path: Path) -> None:
    missing_manifest = tmp_path / "missing_source_manifest.csv"
    payload = builder.build_payload(
        source_manifest=missing_manifest,
        artifact_root=builder.PROJECT_ROOT,
    )
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.MANIFEST_REQUIRED_DISPOSITION
    assert summary["source_manifest_present"] is False
    assert summary["imported_observation_rows"] == 0
    assert summary["canonical_wet_input_written"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert payload["import_audit_rows"][0]["import_rejection_reason"] == (
        "source_manifest_missing"
    )


def test_manifest_import_builder_treats_header_only_manifest_as_required(
    tmp_path: Path,
) -> None:
    source_manifest = tmp_path / "source_manifest.csv"
    source_manifest.write_text(
        "route_candidate_id,endpoint_id,observation_artifact_id,observation_artifact_class,source_kind,model_or_solver_id,assumption_manifest_id,validity_domain,uncertainty_semantics,claim_level,observation_source_artifact,source_geometry_match_level,provided_fields,controls_status,replicate_count,uncertainty_interval_status,pre_registered_rule_status\n",
        encoding="utf-8",
    )

    payload = builder.build_payload(
        source_manifest=source_manifest,
        artifact_root=tmp_path,
    )
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.MANIFEST_REQUIRED_DISPOSITION
    assert summary["source_manifest_present"] is True
    assert summary["imported_observation_rows"] == 0
    assert summary["canonical_wet_input_written"] is False
    assert payload["import_audit_rows"][0]["import_rejection_reason"] == (
        "source_manifest_rows_missing"
    )


def test_manifest_import_builder_writes_hash_bound_canonical_rows(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.csv"
    source_manifest = tmp_path / "source_manifest.csv"
    write_csv_rows(contract_path, _contract_rows())
    write_csv_rows(source_manifest, _manifest_rows(tmp_path))

    old_contract = builder.WET_CONTRACT_ROWS
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_canonical = builder.CANONICAL_WET_INPUT_ROWS
    try:
        builder.WET_CONTRACT_ROWS = contract_path
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.CANONICAL_WET_INPUT_ROWS = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
        )
        payload = builder.build_payload(
            source_manifest=source_manifest,
            artifact_root=tmp_path,
        )
        failures = builder.validate_payload(payload)
        paths = builder.write_outputs(payload)
        canonical_rows = read_csv_rows(builder.CANONICAL_WET_INPUT_ROWS)
    finally:
        builder.WET_CONTRACT_ROWS = old_contract
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.CANONICAL_WET_INPUT_ROWS = old_canonical

    assert failures == []
    assert payload["summary"]["disposition"] == builder.READY_DISPOSITION
    assert payload["summary"]["imported_observation_rows"] == 7
    assert payload["summary"]["canonical_wet_input_written"] is True
    assert len(canonical_rows) == 7
    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_IMPORTED_OBSERVATION_ROWS_20260701.csv" in names
    assert f"578_{builder.PREFIX}_20260701.md" in names


def test_manifest_import_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-wet-surface-observation-manifest-import is required" in (
        result.stderr + result.stdout
    )
