from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def r3a_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("r3a_reduced_grid")
    rv2.run_reduced_grid_R3a(output, write_root_manifest=False)
    return output


def test_R3a_cost_cap_blocks_over_cap_grid():
    cost = rv2.estimate_reduced_grid_R3a_cost(n_routes=rv2.MAX_R3A_ROUTES + 1)

    assert cost["under_R3a_review_cap"] is False
    assert cost["case_row_count"] > rv2.MAX_R3A_CASE_ROWS_BEFORE_REVIEW


def test_R3a_outputs_required_files_and_cap(r3a_output: Path):
    for name in (
        "reduced_grid_summary.csv",
        "route_family_rank_distribution.csv",
        "scenario_rank_distribution.csv",
        "anchor_overlap_correlation.csv",
        "scenario_SNR_spread_by_route_family.csv",
        "optional_660_900x1400_probe_summary.csv",
        "weak_reference_control_summary.csv",
        "thermal_404_gate_summary.csv",
        "detector_connection_state_machine_summary.csv",
        "blank_rare_tail_check.csv",
        "unit_guardrail_summary.csv",
        "reduced_grid_cost_estimate.csv",
        "run_manifest.json",
        "R3a_reduced_grid_report.md",
    ):
        assert (r3a_output / name).exists(), name

    rows = _read_csv(r3a_output / "reduced_grid_summary.csv")
    cost = _read_csv(r3a_output / "reduced_grid_cost_estimate.csv")[0]

    assert len(rows) == rv2.MAX_R3A_CASE_ROWS_BEFORE_REVIEW
    assert int(cost["case_row_count"]) == rv2.MAX_R3A_CASE_ROWS_BEFORE_REVIEW
    assert cost["under_R3a_review_cap"] == "True"


def test_R3a_route_roles_do_not_promote_optional_660_900_silently(
    r3a_output: Path,
):
    rows = _read_csv(r3a_output / "reduced_grid_summary.csv")
    optional_rows = [
        row
        for row in rows
        if row["wavelength_nm"] == "660"
        and row["width_nm"] == "900"
        and row["depth_nm"] == "1400"
    ]
    optional_summary = _read_csv(r3a_output / "optional_660_900x1400_probe_summary.csv")
    longwave_sanity = [
        row
        for row in rows
        if row["wavelength_nm"] == "660"
        and row["width_nm"] == "800"
        and row["depth_nm"] in {"550", "600", "700"}
    ]

    assert optional_rows
    assert all(row["route_role"] == "optional_robustness_probe" for row in optional_rows)
    assert all(row["route_role_locked"] == "True" for row in optional_rows)
    assert all(row["route_role_source"] == rv2.R3A_ROUTE_ROLE_SOURCE for row in rows)
    assert all(
        row["optional_660_900x1400_eligible_for_main_660_redefinition"] == "False"
        for row in optional_rows
    )
    assert optional_summary
    assert all(
        row["promotion_discussion_only_in_optional_summary"] == "True"
        for row in optional_summary
    )
    assert longwave_sanity
    assert all(
        row["route_role"] == "selected_annulus_sanity_overlap_longwave"
        for row in longwave_sanity
    )


def test_R3a_detectability_score_is_not_event_probability(r3a_output: Path):
    rows = _read_csv(r3a_output / "reduced_grid_summary.csv")

    assert rows
    assert all(row["primary_metric"] == "detectability_relative_prior_score" for row in rows)
    assert all(
        row["p_detect_scenario_interpretation"]
        == "legacy_named_relative_prior_score_not_event_probability"
        for row in rows
    )
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(
        row["detected_events_source"]
        == "relative_prior_score_proxy_count_not_observed_events"
        for row in rows
    )
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)


def test_R3a_scenario_snr_spread_watch_triggers_at_1e3(r3a_output: Path):
    triggered = rv2.classify_R3a_scenario_spread_watch(
        min_snr=1.0e-9,
        max_snr=1.1e-6,
    )
    explained = rv2.classify_R3a_scenario_spread_watch(
        min_snr=1.0e-9,
        max_snr=1.1e-6,
        physical_explanation="bounded named-bundle stress test",
    )
    rows = _read_csv(r3a_output / "scenario_SNR_spread_by_route_family.csv")

    assert triggered["scenario_spread_watch_status"] == "stop_requires_physical_explanation"
    assert explained["scenario_spread_watch_status"] == "watch_explained_over_1e3"
    assert rows
    assert all(
        row["stop_if_spread_exceeds_1e3_without_physical_explanation"] == "True"
        for row in rows
    )


def test_R3a_manifest_keeps_R3b_R4_R5_false(r3a_output: Path):
    manifest = json.loads((r3a_output / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["R2_anchor_smoke_run"] is True
    assert manifest["R3_reduced_grid_run"] is True
    assert manifest["R3a_reduced_grid_named_bundle_survey_run"] is True
    assert manifest["R3b_uncertainty_expansion_run"] is False
    assert manifest["R4_representative_full_wave_validation_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["event_budget"]["case_rows"] == rv2.MAX_R3A_CASE_ROWS_BEFORE_REVIEW
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
    assert manifest["base_v1_summary_path_relative"]
    assert manifest["output_directory_relative"]


def test_R3a_outputs_have_required_v2_provenance_and_no_legacy_snr_names(
    r3a_output: Path,
):
    rows = _read_csv(r3a_output / "reduced_grid_summary.csv")

    for row in rows[:100]:
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] in row["scenario_identity"]
        assert row["scenario_id"] not in row["base_route_key"]
        assert row["claim_level"] == "absolute_blocked"
        assert row["module_status"] == "bounded_prior"
    assert all("detector_SNR" not in row for row in rows)
    assert all("calibrated_detector_SNR" not in row for row in rows)


def test_R3a_anchor_overlap_correlation_is_reported(r3a_output: Path):
    rows = _read_csv(r3a_output / "anchor_overlap_correlation.csv")

    assert rows
    assert int(rows[0]["shared_route_particle_cases"]) > 0
    assert rows[0]["rank_correlation_requirement"] == (
        ">0.7_for_shared_R2_anchor_cases_or_explain"
    )
    assert rows[0]["anchor_overlap_rank_correlation_status"] in {
        "pass_rank_correlation_over_0p7",
        "not_available_or_below_threshold",
    }
