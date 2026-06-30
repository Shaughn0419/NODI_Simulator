from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from tools.audits import (
    build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate as gate38,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return gate38.build_payload()


def test_gate38_payload_refines_gate37_wall_pileup_without_promotion() -> None:
    payload = _payload()
    failures = gate38.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == gate38.DISPOSITION
    assert summary["gate37_disposition"] == gate38.EXPECTED_GATE37_DISPOSITION
    assert summary["gate37_max_wall_pileup_ratio"] == 9.0
    assert summary["refined_top_pileup_rows"] == gate38.TOP_PILEUP_ROW_COUNT
    assert summary["expanded_sample_count"] == gate38.EXPANDED_SAMPLE_COUNT
    assert summary["algorithmic_pileup_signal_rows"] == 0
    assert summary["sparse_gate37_proxy_artifact_rows"] >= 1
    assert summary["max_expanded_first_vs_adjacent_gap_band_smoothed_ratio"] < 1.5
    assert summary["max_interpretable_expanded_gap_band_smoothed_ratio"] < 1.5
    assert summary["wall_pileup_refinement_status"] == (
        "sparse_gate37_proxy_artifact_no_algorithmic_pileup_signal"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_gate38_refinement_rows_include_counts_and_confidence_intervals() -> None:
    rows = _payload()["wall_pileup_refinement"]
    first = rows[0]

    assert len(rows) == gate38.TOP_PILEUP_ROW_COUNT
    assert first["scenario_id"] == "theta90_D1200_r20"
    assert first["gate37_wall_pileup_ratio"] == "9.0"
    assert int(first["gate37_adjacent_band_count"]) == 0
    assert first["gate37_ratio_denominator_zero"] == "true"
    assert first["gate37_sparse_denominator_status"] == "sparse_proxy_uninterpretable"
    assert int(first["expanded_sample_count"]) == gate38.EXPANDED_SAMPLE_COUNT
    assert first["band_edges_nm_json"].startswith("[")
    assert first["expanded_band_counts_json"].startswith("[")
    assert first["expanded_sparse_denominator_status"] == "expanded_count_supported_proxy"
    assert first["dt_consistency_status"] == "high_ratio_only_in_sparse_proxy_rows"
    assert float(first["expanded_first_vs_adjacent_gap_band_smoothed_ratio"]) < 1.0
    assert first["algorithmic_pileup_signal"] == "false"
    assert first["refinement_status"] == "sparse_gate37_proxy_artifact_no_algorithmic_signal"
    assert all(row["claim_boundary"] == gate38.CLAIM_BOUNDARY for row in rows)


def test_gate38_algorithmic_signal_rule_is_stricter_than_ratio_alone() -> None:
    rows = _payload()["wall_pileup_refinement"]

    assert max(
        float(row["expanded_first_vs_adjacent_gap_band_smoothed_ratio"]) for row in rows
    ) < gate38.ALGORITHM_PILEUP_RATIO_HARD_LINE
    assert max(
        float(row["expanded_first_vs_adjacent_gap_band_ratio_ci95_low"]) for row in rows
    ) < gate38.ALGORITHM_PILEUP_LOWER_CI_HARD_LINE
    assert all(row["algorithmic_pileup_signal"] == "false" for row in rows)


def test_gate38_firewall_keeps_authorization_false() -> None:
    firewall = gate38.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == "PASS_GATE38_WALL_PILEUP_REFINEMENT_NO_PROOF_REGISTRATION"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_gate38_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = gate38.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = gate38.read_csv(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_20260701.csv" in artifacts
    assert "NODI_COMSOL_GATE38_SIDEWALL_SOURCE_LOCK_20260701.csv" in artifacts
    assert "NODI_COMSOL_GATE38_SIDEWALL_NO_PROOF_FIREWALL_20260701.csv" in artifacts
    assert "NODI_COMSOL_GATE38_SIDEWALL_STATUS_20260701.json" in artifacts
    assert "500_NODI_COMSOL_GATE38A_WALL_PILEUP_REFINEMENT_COUNTS_20260701.md" in artifacts
    assert "503_NODI_COMSOL_GATE38_WALL_PILEUP_REFINEMENT_CANDIDATE_MASTER_REPORT_20260701.md" in artifacts
    assert by_artifact["NODI_COMSOL_GATE38_SIDEWALL_MANIFEST_20260701.csv"][
        "sha256"
    ] == gate38.SELF_MANIFEST_SHA256


def test_gate38_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate38-wall-pileup-refinement-candidate is required" in result.stderr
