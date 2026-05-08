from __future__ import annotations

import csv
import json
from pathlib import Path

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_anchor_smoke_uses_capped_route_particle_scenario_seed_panel(tmp_path):
    summary = rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)

    assert summary["route_count"] == 14
    assert summary["particle_count"] == 8
    assert summary["scenario_bundle_count"] == 8
    assert summary["seed_count"] == 3
    assert summary["anchor_smoke_rows"] == rv2.MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW
    assert summary["smoke_cost_under_cap"] is True
    assert summary["all_snr_claims_absolute_blocked"] is True
    assert summary["legacy_snr_output_names_absent"] is True
    assert summary["R3_reduced_grid_run"] is False
    assert summary["R5_full_grid_v2_run"] is False


def test_anchor_smoke_outputs_required_files_and_manifest_gates(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)

    for name in (
        "anchor_smoke_summary.csv",
        "anchor_smoke_route_particle_summary.csv",
        "anchor_smoke_scenarios.csv",
        "detector_connection_state_machine_summary.csv",
        "mie_to_power_unit_check.csv",
        "blank_rare_tail_check.csv",
        "unit_guardrail_summary.csv",
        "smoke_run_cost_estimate.csv",
        "run_manifest.json",
        "anchor_smoke_report.md",
    ):
        assert (tmp_path / name).exists(), name

    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["R2_anchor_smoke_run"] is True
    assert manifest["R3_reduced_grid_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["event_budget"]["event_level_runs"] == rv2.MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW
    assert manifest["scenario_budget"]["smoke_cost_under_cap"] is True


def test_anchor_smoke_output_guardrails(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)

    summary_rows = _read_csv(tmp_path / "anchor_smoke_summary.csv")
    state_rows = _read_csv(tmp_path / "detector_connection_state_machine_summary.csv")
    blank_rows = _read_csv(tmp_path / "blank_rare_tail_check.csv")
    cost_rows = _read_csv(tmp_path / "smoke_run_cost_estimate.csv")

    assert len(summary_rows) == rv2.MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW
    assert all(row["P_ref_ROI_W_unit"] == "W" for row in summary_rows)
    assert all(row["P_sca_ROI_W_unit"] == "W" for row in summary_rows)
    assert all(row["P_cross_ROI_W_unit"] == "W" for row in summary_rows)
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in summary_rows)
    assert all("detector_SNR" not in row for row in summary_rows)
    assert all("calibrated_detector_SNR" not in row for row in summary_rows)
    assert all(row["scenario_detector_SNR"] for row in summary_rows)
    assert all(
        row["finite_monte_carlo_zero_event_inferred"] == "False" for row in blank_rows
    )
    assert any(
        row["connection_state_id"] == "ET2030_BNC_direct_to_LI5640_current_input"
        and row["connection_physical_validity"] == "forbidden"
        for row in state_rows
    )
    assert cost_rows[0]["under_review_cap"] == "True"
    assert int(cost_rows[0]["max_event_level_runs_before_review"]) == 2688


def test_anchor_smoke_rows_keep_route_and_scenario_identities_separate(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)
    for row in _read_csv(tmp_path / "anchor_smoke_summary.csv")[:25]:
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] in row["scenario_identity"]
        assert row["scenario_id"] not in row["base_route_key"]
        assert row["claim_level"] == "absolute_blocked"
        assert row["module_status"] == "bounded_prior"


def test_reference_power_independent_of_particle_for_fixed_route_scenario(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)
    rows = _read_csv(tmp_path / "anchor_smoke_summary.csv")
    subset = [
        row
        for row in rows
        if row["wavelength_nm"] == "660"
        and row["width_nm"] == "800"
        and row["depth_nm"] == "1400"
        and row["scenario_bundle"] == "nominal_instrument_clean_blank"
        and row["seed"] == "42"
    ]

    assert len({row["particle_id"] for row in subset}) == 8
    assert len({row["P_ref_ROI_W"] for row in subset}) == 1
    assert all(row["P_ref_scale_independent_of_particle"] == "True" for row in subset)


def test_10k_rerun_not_recommended_when_only_low_p_gate_is_active(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)
    rows = _read_csv(tmp_path / "anchor_smoke_summary.csv")
    low_only_rows = [
        row
        for row in rows
        if row["low_detectability_prior"] == "True"
        and row["statistical_precision_rerun_recommended"] == "False"
    ]

    assert low_only_rows
    assert all(row["adaptive_rerun_recommended"] == "False" for row in low_only_rows)
    assert all(
        row["adaptive_event_count_will_not_clear_gate"] == "True" for row in low_only_rows
    )


def test_p_detect_mapping_claim_level_is_not_calibrated_probability(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)
    rows = _read_csv(tmp_path / "anchor_smoke_summary.csv")

    assert rows
    assert all(
        row["p_detect_mapping_mode"]
        == "relative_prior_score_from_absolute_blocked_snr_not_event_probability"
        for row in rows
    )
    assert all(
        row["p_detect_scenario_interpretation"]
        == "legacy_named_relative_prior_score_not_event_probability"
        for row in rows
    )
    assert all(
        row["detected_events_source"]
        == "relative_prior_score_proxy_count_not_observed_events"
        for row in rows
    )
    assert all(
        row["statistical_precision_rerun_basis"]
        == "relative_prior_score_proxy_wilson_half_width"
        for row in rows
    )
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["detected_events_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)


def test_adaptive_precision_gate_separate_from_low_detectability_gate(tmp_path):
    rv2.run_anchor_smoke(tmp_path, write_root_manifest=False)
    rows = _read_csv(tmp_path / "anchor_smoke_summary.csv")

    assert all("statistical_precision_rerun_recommended" in row for row in rows)
    assert all("low_detectability_prior" in row for row in rows)
    assert all("adaptive_event_count_will_not_clear_gate" in row for row in rows)
    assert any(row["low_detectability_prior"] == "False" for row in rows)
    assert all(
        row["adaptive_rerun_recommended"]
        == row["statistical_precision_rerun_recommended"]
        for row in rows
    )
