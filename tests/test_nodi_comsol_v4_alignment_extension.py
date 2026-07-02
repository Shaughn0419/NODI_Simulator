from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_comsol_v4_alignment_extension as builder


def test_v4_alignment_extension_builds_dirty_source_aware_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_alignment_disposition"] == (
        "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_READY"
    )
    assert summary["source_missing_rows"] == 0
    assert summary["dirty_source_dependency_rows"] > 0
    assert summary["route_universe_crosswalk_rows"] == 4
    assert summary["readout_noise_binding_rows"] == 2
    assert summary["wet_surface_v4_binding_rows"] == 8
    assert summary["state_machine_rows"] == 4
    assert summary["quarantine_guard_rows"] == 1
    assert summary["failed_alignment_check_rows"] == 0


def test_route_universe_crosswalk_keeps_comsol_nodi_and_sidewall_grains_distinct() -> None:
    rows = {
        row["crosswalk_row_id"]: row
        for row in builder.build_payload()["route_universe_crosswalk_rows"]
    }

    assert rows["ROUTE-XWALK-COMSOL-V4-STAGE1-36"]["route_count"] == 36
    assert rows["ROUTE-XWALK-COMSOL-V4-FIELD-12"]["route_count"] == 12
    assert rows["ROUTE-XWALK-NODI-POST-V2-572"]["route_count"] == 572
    assert rows["ROUTE-XWALK-NODI-PACKAGE-C-2"]["route_count"] == 2
    assert rows["ROUTE-XWALK-COMSOL-V4-STAGE1-36"][
        "maps_to_nodi_sidewall_candidate"
    ] == "unmapped_by_design"
    assert rows["ROUTE-XWALK-NODI-POST-V2-572"][
        "mapping_policy"
    ] == "do_not_collapse_572_routes_into_two_sidewall_candidates"


def test_readout_noise_binding_requires_eight_noise_scenarios_and_four_physical_lanes() -> None:
    rows = builder.build_payload()["readout_noise_binding_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["noise_readout_scenario_count"] == 8
        assert row["physical_ceiling_lane_count"] == 4
        assert row["physical_ceiling_role"] == "surrogate_risk_reduction_only"
        assert row["calibrated_claim_allowed"] is False
        assert row["solver_or_simulation_execution_authorized"] is False


def test_wet_surface_v4_binding_is_route_by_scenario_matrix() -> None:
    rows = builder.build_payload()["wet_surface_v4_binding_rows"]
    keys = {
        (row["route_candidate_id"], row["scenario_id"])
        for row in rows
    }

    assert len(rows) == 8
    assert len(keys) == 8
    assert ("ROUTE-CAND-001", "EXTREV-SCEN-LOW") in keys
    assert ("ROUTE-CAND-002", "EXTREV-SCEN-EXTREME") in keys
    for row in rows:
        assert row["surface_chemistry_contract_binding"] == (
            "PEG_silane_unverified_project_QC_contract_v4"
        )
        assert row["binding_status"] == (
            "v4_wet_surface_assumption_bound_to_sidewall_route"
        )


def test_state_machine_stays_simulation_only_and_hash_bound() -> None:
    rows = builder.build_payload()["state_machine_rows"]
    states = [row["state_id"] for row in rows]

    assert states == [
        "simulation_source_hash_locked",
        "simulation_candidate_metric",
        "simulation_release_candidate",
        "solver_supported_candidate",
    ]
    for row in rows:
        assert row["final_or_production_state"] is False
        assert row["requires_v4_identity"] is True
        assert row["requires_source_hash"] is True


def test_quarantine_guard_is_negative_guard_not_active_source() -> None:
    rows = builder.build_payload()["quarantine_guard_rows"]

    assert len(rows) == 1
    assert rows[0]["active_source_allowed"] is False
    assert rows[0]["negative_guard_allowed"] is True
    assert rows[0]["guard_status"] == (
        "quarantine_artifact_retained_as_negative_guard_only"
    )


def test_v4_alignment_extension_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_SOURCE_DEPENDENCY_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_UNIVERSE_CROSSWALK_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_READOUT_NOISE_BINDING_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_WET_SURFACE_V4_BINDING_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_SIMULATION_STATE_MACHINE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"587_{builder.PREFIX}_20260702.md" in names


def test_v4_alignment_extension_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_v4_alignment_extension.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-nodi-comsol-v4-alignment-extension is required" in (
        result.stderr + result.stdout
    )
