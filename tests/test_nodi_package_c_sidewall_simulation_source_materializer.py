from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from nodi_simulator.sidewall_wet_surface_observation_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS as WET_ROUTE_ACCEPTED_STATUS,
    build_wet_surface_observation_intake,
)
from nodi_simulator.sidewall_wet_surface_observation_manifest_import import (
    build_wet_observation_rows_from_manifest,
)
from nodi_simulator.sidewall_yield_detection_claim_value_manifest_import import (
    build_yield_detection_claim_value_rows_from_manifest,
)
from nodi_simulator.sidewall_yield_detection_claim_value_review import (
    build_yield_detection_claim_value_review,
)
from tools.audits import (
    build_nodi_package_c_sidewall_simulation_source_materializer as builder,
)


def _winner_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "winner_current": "True",
            "JRC_current": "True",
            "route_score_current": "True",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "winner_current": "False",
            "JRC_current": "False",
            "route_score_current": "True",
        },
    ]


def test_simulation_source_materializer_payload_is_ready() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["route_context_rows"] == 2
    assert summary["wet_manifest_rows_to_write"] >= 14
    assert summary["claim_value_manifest_rows_to_write"] == 4
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_materialized_wet_manifest_is_accepted_by_existing_intake(
    tmp_path: Path,
) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_source_dir = builder.SOURCE_DIR
    old_wet_manifest = builder.WET_SOURCE_MANIFEST
    old_claim_manifest = builder.CLAIM_VALUE_SOURCE_MANIFEST
    try:
        builder.OUTPUT_DIR = tmp_path / "reports" / "joint_interface_20260701"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.SOURCE_DIR = (
            builder.OUTPUT_DIR / "sidewall_simulation_assumption_sources"
        )
        builder.WET_SOURCE_MANIFEST = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
        )
        builder.CLAIM_VALUE_SOURCE_MANIFEST = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
        )
        builder.write_outputs(payload)
        wet_manifest_rows = read_csv_rows(builder.WET_SOURCE_MANIFEST)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.SOURCE_DIR = old_source_dir
        builder.WET_SOURCE_MANIFEST = old_wet_manifest
        builder.CLAIM_VALUE_SOURCE_MANIFEST = old_claim_manifest

    imported_rows, audit_rows = build_wet_observation_rows_from_manifest(
        contract_rows=payload["wet_contract_rows"],
        manifest_rows=wet_manifest_rows,
        artifact_root=tmp_path,
    )
    _intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=payload["wet_contract_rows"],
        observation_rows=imported_rows,
        artifact_root=tmp_path,
    )

    assert len(imported_rows) == len(payload["wet_contract_rows"])
    assert {row.import_rejection_reason for row in audit_rows} == {""}
    assert {row.route_wet_observation_matrix_status for row in matrix_rows} == {
        WET_ROUTE_ACCEPTED_STATUS
    }


def test_materialized_claim_value_manifest_is_accepted_by_existing_review(
    tmp_path: Path,
) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_source_dir = builder.SOURCE_DIR
    old_wet_manifest = builder.WET_SOURCE_MANIFEST
    old_claim_manifest = builder.CLAIM_VALUE_SOURCE_MANIFEST
    try:
        builder.OUTPUT_DIR = tmp_path / "reports" / "joint_interface_20260701"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.SOURCE_DIR = (
            builder.OUTPUT_DIR / "sidewall_simulation_assumption_sources"
        )
        builder.WET_SOURCE_MANIFEST = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
        )
        builder.CLAIM_VALUE_SOURCE_MANIFEST = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
        )
        builder.write_outputs(payload)
        claim_manifest_rows = read_csv_rows(builder.CLAIM_VALUE_SOURCE_MANIFEST)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.SOURCE_DIR = old_source_dir
        builder.WET_SOURCE_MANIFEST = old_wet_manifest
        builder.CLAIM_VALUE_SOURCE_MANIFEST = old_claim_manifest

    detection_rows, yield_rows, audit_rows = (
        build_yield_detection_claim_value_rows_from_manifest(
            manifest_rows=claim_manifest_rows,
            artifact_root=tmp_path,
        )
    )
    review_rows, guard_rows = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows(),
        detection_value_rows=detection_rows,
        yield_value_rows=yield_rows,
        artifact_root=tmp_path,
    )

    assert len(detection_rows) == 2
    assert len(yield_rows) == 2
    assert {row.import_rejection_reason for row in audit_rows} == {""}
    assert {row.detection_probability_simulation_candidate_current for row in review_rows} == {
        True
    }
    assert {row.yield_simulation_candidate_current for row in review_rows} == {True}
    assert {row.wet_pass_probability_simulation_candidate_current for row in review_rows} == {
        True
    }
    assert {row.detection_probability_current for row in review_rows} == {False}
    assert {row.yield_current for row in review_rows} == {False}
    assert {row.wet_pass_probability_current for row in review_rows} == {False}
    by_target = {row.promotion_target: row for row in guard_rows}
    assert by_target["simulation_detection_probability_candidate"].activation_allowed_now is True
    assert by_target["simulation_yield_wet_candidate"].activation_allowed_now is True
    assert by_target["production_ingestion"].activation_allowed_now is False


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_simulation_source_materializer.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-simulation-source-materializer is required" in result.stderr
