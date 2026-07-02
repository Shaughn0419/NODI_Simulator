from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.nodi_comsol_next_artifacts import PRS_SIDEWALL_V2_REQUIRED_FIELDS
from tools.audits import build_nodi_sidewall_prs_v2_candidate_from_bounded_shards as builder


def test_prs_v2_candidate_rows_preserve_executed_shard_count() -> None:
    rows = builder.prs_candidate_rows()

    assert len(rows) == 24
    assert {row["sidewall_deg_comsol"] for row in rows} == {90.0, 85.0}
    assert {row["diameter_nm"] for row in rows} == {100, 220, 300}
    assert all(row["source_shard_case_id"].startswith("SHARD-") for row in rows)
    assert all(row["decision_use_allowed"] is False for row in rows)


def test_prs_v2_candidate_rows_include_required_sidewall_fields() -> None:
    row = builder.prs_candidate_rows()[0]

    missing = [field for field in PRS_SIDEWALL_V2_REQUIRED_FIELDS if field not in row]
    assert missing == []
    assert row["artifact_version"] == "NODI_POSITION_RESPONSE_SIDEWALL_V2"
    assert row["roadmap_status"] == "surrogate_sensitivity_only"
    assert row["not_accepted_for_production"] is True


def test_prs_v2_candidate_rows_keep_sparse_event_context_boundary() -> None:
    rows = builder.prs_candidate_rows()

    assert all(row["bin_sample_status"] in {"sparse", "empty"} for row in rows)
    assert all(row["sparse_bin_flag"] is True for row in rows)
    assert all(row["not_detection_probability"] is True for row in rows)
    assert all(row["not_yield"] is True for row in rows)
    assert all(row["not_qch_weighted"] is True for row in rows)
    assert all(row["not_selection_metric_claim"] is True for row in rows)
    assert all(row["not_winner"] is True for row in rows)
    assert all(row["not_true_W_eff"] is True for row in rows)
    assert all(row["not_production_prs"] is True for row in rows)


def test_prs_v2_candidate_preserves_sidewall_formula_and_semantics() -> None:
    row = next(
        row
        for row in builder.prs_candidate_rows()
        if row["route_id_nodi"] == "404/W500/D900"
        and row["sidewall_deg_comsol"] == 85.0
        and row["diameter_nm"] == 100
    )

    assert abs(row["W_bottom_unclipped_nm"] - 342.52) < 0.03
    assert row["W_top_semantics"] == "runtime_top_aperture"
    assert row["source_W_top_semantics"] == "runtime_top_aperture_surrogate"
    assert row["sidewall_angle_convention"] == "comsol_from_horizontal_90deg_vertical"
    assert row["sidewall_taper_angle_deg_nodi"] == 5.0


def test_prs_v2_candidate_source_grain_does_not_borrow_depth() -> None:
    rows = builder.prs_candidate_rows()

    assert all(row["source_route_id_nodi"] == row["route_id_nodi"] for row in rows)
    assert all(row["source_D_nm"] == row["D_nm"] for row in rows)
    assert all(row["source_distribution_type"] == row["distribution_type"] for row in rows)
    assert all(row["source_bin_basis"] == row["bin_basis"] for row in rows)
    assert all(row["source_bin_id"] == row["bin_id"] for row in rows)


def test_prs_v2_candidate_does_not_trigger_wall_distance_bin_proof() -> None:
    rows = builder.prs_candidate_rows()

    assert all("wall_distance" not in row["bin_basis"] for row in rows)
    assert all("wall_distance" not in row["source_bin_basis"] for row in rows)
    assert all(row["includes_trajectory_near_wall_metrics"] is False for row in rows)
    assert all(row["package_C_validation_status"] == "not_applicable_for_this_artifact" for row in rows)


def test_blocked_bins_carry_no_numeric_response_values() -> None:
    rows = builder.prs_candidate_rows()
    blocked_rows = [
        row
        for row in rows
        if row["bin_particle_center_support_status"] == "blocked"
        or row["bin_accessible"] is False
    ]

    for row in blocked_rows:
        assert row["blocked_reason"]
        assert row["response_value"] == "blocked"
        assert row["response_proxy_value"] == ""
        assert row["detector_response_proxy"] == ""
        assert row["signal_response_proxy"] == ""
        assert row["response_rate_bin"] == ""
        assert row["neighbor_fill_used"] is False


def test_no_forbidden_primary_columns_in_candidate_outputs() -> None:
    payload = builder.build_payload()
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "detection_probability",
        "yield",
        "W_eff",
        "q_ch_eta",
        "rank_under_surrogate",
        "not_route_score",
    }
    columns = set().union(*(set(row) for row in payload["prs_candidate_rows"]))
    assert forbidden_exact.isdisjoint(columns)
    assert builder.validate_payload(payload) == []


def test_delta_context_rows_preserve_pairing_without_probability_claims() -> None:
    rows = builder.delta_context_rows()

    assert len(rows) == 12
    assert {row["baseline_sidewall_deg_comsol"] for row in rows} == {90.0}
    assert {row["sidewall_deg_comsol"] for row in rows} == {85.0}
    assert all(row["not_detection_probability"] is True for row in rows)
    assert all(row["not_selection_metric_claim"] is True for row in rows)


def test_prs_v2_candidate_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"{builder.PREFIX}_CANDIDATE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_DELTA_CONTEXT_ROWS_20260702.csv" in names
    assert f"592_{builder.PREFIX}_20260702.md" in names


def test_prs_v2_candidate_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_prs_v2_candidate_from_bounded_shards.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-prs-v2-candidate-from-bounded-shards is required" in (
        result.stderr + result.stdout
    )
