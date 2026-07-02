from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_comsol_v4_upper_assumption_alignment as builder


def test_v4_upper_assumption_alignment_builds_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["comsol_v4_assumption_set_id"] == builder.EXPECTED_V4_ID
    assert summary["comsol_v4_assumption_set_version"] == builder.EXPECTED_V4_VERSION
    assert summary["comsol_v4_sha_match"] is True
    assert summary["v4_scenario_rows"] == 4
    assert summary["v4_low_mid_high_rows"] == 3
    assert summary["v4_extreme_preflight_rows"] == 1
    assert summary["route_binding_rows"] == 2
    assert summary["route_binding_aligned_rows"] == 2
    assert summary["simulation_release_candidate_rows"] == 1
    assert summary["top_route_candidate_id"] == "ROUTE-CAND-001"
    assert summary["top_route_geometry_family"] == "ideal_rectangle"
    assert summary["failed_alignment_check_rows"] == 0


def test_v4_scenario_rows_preserve_extreme_preflight_and_v4_identity() -> None:
    payload = builder.build_payload()
    rows = {row["scenario_id"]: row for row in payload["v4_scenario_rows"]}

    assert set(rows) == builder.EXPECTED_V4_SCENARIOS
    for scenario_id, row in rows.items():
        assert row["assumption_set_id"] == builder.EXPECTED_V4_ID
        assert row["assumption_set_version"] == builder.EXPECTED_V4_VERSION
        assert row["assumption_set_sha256"] == builder.EXPECTED_V4_SHA256
        assert row["geometry_root_requirement"] == "required_external_binding"
        assert row["hydraulic_anchor_requirement"] == "required_external_binding"
        assert row["surface_binding_policy"] == "must_resolve_before_wet_model_execution"
        if scenario_id == "EXTREV-SCEN-EXTREME":
            assert row["nodi_alignment_status"] == (
                "aligned_extreme_branch_preflight_required"
            )
            assert row["compute_authorized_now"] == "false_preflight_required"
        else:
            assert row["nodi_alignment_status"] == "aligned_to_nodi_simulation_overlay"
            assert row["compute_authorized_now"] == "local_python_scenario_only"


def test_route_bindings_cover_rectangle_and_trapezoid_with_simulation_claims() -> None:
    payload = builder.build_payload()
    rows = {row["route_candidate_id"]: row for row in payload["route_binding_rows"]}

    assert set(rows) == {"ROUTE-CAND-001", "ROUTE-CAND-002"}
    assert rows["ROUTE-CAND-001"]["route_geometry_family"] == "ideal_rectangle"
    assert rows["ROUTE-CAND-002"]["route_geometry_family"] == (
        "trapezoid_tapered_sidewalls"
    )
    for row in rows.values():
        assert row["comsol_v4_assumption_set_id"] == builder.EXPECTED_V4_ID
        assert row["comsol_v4_assumption_set_sha256"] == builder.EXPECTED_V4_SHA256
        assert row["simulation_claims_authorized_by_alignment"] is True
        assert row["actual_measurement_or_calibration_claim"] is False
        assert row["actual_fabrication_release_current"] is False
        assert row["actual_production_ingestion_current"] is False
        assert row["alignment_status"] == "aligned_to_comsol_v4_upper_assumptions"


def test_alignment_checks_are_all_hard_pass() -> None:
    payload = builder.build_payload()
    rows = payload["alignment_check_rows"]

    assert rows
    assert all(row["check_pass"] is True for row in rows)
    assert all(row["hard_fail_if_false"] is True for row in rows)
    assert any(
        row["check_name"] == "v4_contract_sha_matches_agents_lock" for row in rows
    )
    assert any(
        row["check_name"] == "simulation_claims_allowed_under_alignment"
        for row in rows
    )


def test_v4_upper_assumption_alignment_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        paths = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir

    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_V4_SCENARIO_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_BINDING_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ALIGNMENT_CHECK_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"586_{builder.PREFIX}_20260702.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260702.csv" in names


def test_v4_upper_assumption_alignment_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_v4_upper_assumption_alignment.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-nodi-comsol-v4-upper-assumption-alignment is required" in (
        result.stderr + result.stdout
    )
