from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from tools.audits import (
    build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate as gate37,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return gate37.build_payload()


def test_gate37_payload_is_metric_hardening_candidate_only() -> None:
    payload = _payload()
    failures = gate37.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == gate37.DISPOSITION
    assert summary["gate33_36_disposition"] == gate37.EXPECTED_GATE33_36_DISPOSITION
    assert summary["scenario_metric_rows_inherited"] >= 200
    assert summary["boundary_atom_split_rows"] >= 100
    assert summary["histogram_rows"] >= 300
    assert summary["ess_proxy_rows"] >= 100
    assert summary["one_wall_suite_rows"] == 18
    assert summary["worst_case_dt_refinement_rows"] == gate37.WORST_CASE_COUNT
    assert summary["corner_heatmap_rows"] == gate37.WORST_CASE_COUNT * 4
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_gate37_boundary_split_separates_exact_and_near_band() -> None:
    rows = _payload()["boundary_atom_split"]
    first = rows[0]

    assert "exact_boundary_atom_fraction" in first
    assert "near_boundary_band_fraction" in first
    assert "wall_pileup_ratio" in first
    assert first["exact_boundary_atom_eps_nm"] == str(gate37.EXACT_ATOM_EPS_NM)
    assert first["near_boundary_band_eps_nm"] == str(gate37.NEAR_BAND_EPS_NM)
    assert all(
        row["candidate_interpretation"]
        == "exact_atom_split_checked_no_exact_atoms_observed_not_proof_registered"
        for row in rows
    )
    assert all(row["claim_boundary"] == gate37.CLAIM_BOUNDARY for row in rows)


def test_gate37_histograms_and_ess_are_reviewer_friendly() -> None:
    histogram_rows = _payload()["raw_histograms"]
    ess_rows = _payload()["ess_proxy"]
    bases = {row["histogram_basis"] for row in histogram_rows}

    assert bases == {"x_local_norm", "u_accessible_cdf"}
    assert all(row["bin_edges_json"].startswith("[") for row in histogram_rows)
    assert all(row["bin_probability_json"].startswith("[") for row in histogram_rows)
    assert all(row["ess_method"] == "independent_one_step_samples_no_timeseries_autocorrelation_available" for row in ess_rows)
    assert all(row["autocorrelation_status"] == "not_a_timeseries_proof_artifact" for row in ess_rows)


def test_gate37_one_wall_suite_has_positive_and_negative_controls() -> None:
    rows = _payload()["one_wall_suite"]
    methods = {row["method"] for row in rows}

    assert methods == {
        "folded_normal_mirror_positive_control",
        "projection_clamp_negative_control",
        "rejection_resampling_negative_control",
    }
    assert {row["d_over_sigma"] for row in rows} == {"0.0", "0.25", "0.5", "1.0", "2.0", "4.0"}
    positive = [
        row
        for row in rows
        if row["method"] == "folded_normal_mirror_positive_control"
    ]
    projection = [
        row
        for row in rows
        if row["method"] == "projection_clamp_negative_control"
    ]
    assert max(float(row["ks_distance_to_reflecting_kernel"]) for row in positive) <= 0.02
    assert max(float(row["exact_boundary_atom_fraction"]) for row in projection) > 0.0


def test_gate37_worst_case_dt_and_corner_rows_are_bounded() -> None:
    dt_rows = _payload()["worst_case_dt_refinement"]
    corner_rows = _payload()["corner_heatmap"]

    assert len(dt_rows) == gate37.WORST_CASE_COUNT
    assert all(row["extra_dt_s"] == str(gate37.EXTRA_DT_S) for row in dt_rows)
    assert all(row["extra_dt_support_violation_count"] == "0" for row in dt_rows)
    assert len(corner_rows) == gate37.WORST_CASE_COUNT * 4
    assert {row["corner_id"] for row in corner_rows} == {
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
    }


def test_gate37_firewall_keeps_all_authorization_false() -> None:
    firewall = gate37.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == "PASS_GATE37_METRIC_HARDENING_CANDIDATE_NO_PROOF_REGISTRATION"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_gate37_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = gate37.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = gate37.read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_GATE37_SIDEWALL_BOUNDARY_ATOM_SPLIT_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE37_SIDEWALL_RAW_HISTOGRAMS_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE37_SIDEWALL_ONE_WALL_FOLDED_NORMAL_SUITE_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE37_SIDEWALL_WORST_CASE_DT_REFINEMENT_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE37_SIDEWALL_CORNER_HEATMAP_20260630.csv" in artifacts
    assert "496_NODI_COMSOL_GATE37A_BOUNDARY_ATOM_AND_HISTOGRAM_HARDENING_20260630.md" in artifacts
    assert "499_NODI_COMSOL_GATE37_REFLECTION_METRIC_HARDENING_CANDIDATE_MASTER_REPORT_20260630.md" in artifacts
    assert by_artifact["NODI_COMSOL_GATE37_SIDEWALL_MANIFEST_20260630.csv"][
        "sha256"
    ] == gate37.SELF_MANIFEST_SHA256


def test_gate37_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate37-package-c-metric-hardening-candidate is required" in result.stderr
