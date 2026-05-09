from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_DIR = rv2.DEFAULT_R5_FULL_GRID_V2_DIR
R5_EXECUTION_MANIFEST_FROZEN_CHECKSUMS = {
    "R5_plan_yaml_checksum": "5fe1be0da5f072335e4e520e11a5f1f5fb310cb23d0d3b75f658869536614964",
    "R5_plan_report_checksum": "76abc52a35d172187cf0839b173d6d856d92ae0334e5c608e097d128ec2230d7",
    "R5_scenario_bundle_manifest_checksum": (
        "770eb4f59a2fe842c9cd014b50bd1a4a91f116266df49a10100738de3c452373"
    ),
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_headers(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return set(next(csv.reader(handle)))


def _row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in handle) - 1


def _truthy(value: str) -> bool:
    return value == "True"


def test_R5_execution_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R5_full_grid_v2(
            tmp_path,
            external_authorization="PASS_TO_R5_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R5_source_schema_helpers_report_missing_or_bad_columns():
    with pytest.raises(ValueError, match="source row 7 missing all required columns"):
        rv2._r5_required_text({}, "particle_name", "particle_preset_id", row_index=7)

    with pytest.raises(ValueError, match="source row 8 has non-numeric value 'wide'"):
        rv2._r5_required_float({"width_nm": "wide"}, "width_nm", "W_nm", row_index=8)

    with pytest.raises(ValueError, match="source row 9 has non-finite value 'nan'"):
        rv2._r5_required_float({"width_nm": "nan"}, "width_nm", "W_nm", row_index=9)


def test_R5_outputs_required_files_only_and_respect_cap():
    assert R5_DIR.exists()
    files = {p.name for p in R5_DIR.iterdir() if p.is_file() and not p.name.startswith("._")}

    assert files == rv2.R5_REQUIRED_OUTPUTS_IF_EXECUTED_AFTER_REVIEW
    assert _row_count(R5_DIR / "full_grid_v2_case_manifest.csv") == 256256
    assert _row_count(R5_DIR / "full_grid_v2_summary.csv") == 256256

    cost = _csv_rows(R5_DIR / "full_grid_v2_cost_estimate.csv")[0]
    assert cost["case_row_count"] == "256256"
    assert cost["actual_case_rows"] == "256256"
    assert _truthy(cost["under_R5_review_cap"])
    assert cost["external_authorization"] == "PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY"
    assert _truthy(cost["R5_full_grid_v2_run"])
    assert not _truthy(cost["R5_followup_expansion_authorized"])


def test_R5_case_manifest_uses_reviewed_source_rows_scenarios_and_no_seeds():
    scenarios: set[str] = set()
    seeds: set[str] = set()
    source_rows: set[str] = set()
    route_ids: set[str] = set()
    role_counts: Counter[str] = Counter()

    with (R5_DIR / "full_grid_v2_case_manifest.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        for row in csv.DictReader(handle):
            scenarios.add(row["scenario_bundle"])
            seeds.add(row["stochastic_seed"])
            source_rows.add(row["source_v1_row_index"])
            route_ids.add(row["route_id"])
            role_counts[row["route_role"]] += 1
            assert row["R5_full_grid_v2_run"] == "True"
            assert row["R5_followup_expansion_authorized"] == "False"
            assert row["context_route_promotion_authorized"] == "False"
            assert row["main_660_redefinition_authorized"] == "False"
            assert row["route_specific_manual_sign_flip_applied"] == "False"

    assert scenarios == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert seeds == {""}
    assert len(source_rows) == rv2.R5_V1_SOURCE_ROW_COUNT == 32032
    assert len(route_ids) == rv2.R5_V1_SOURCE_ROUTE_COUNT == 572
    assert sum(role_counts.values()) == 256256
    assert role_counts["main_660"] == 896


def test_R5_summary_claim_boundaries_are_blocked_for_all_rows():
    counters = {
        "SNR_claim_level": Counter(),
        "event_probability_claim_level": Counter(),
        "p_detect_mapping_claim_level": Counter(),
        "R5_full_grid_v2_run": Counter(),
        "context_route_promotion_authorized": Counter(),
        "main_660_redefinition_authorized": Counter(),
        "route_specific_manual_sign_flip_applied": Counter(),
        "R5_followup_expansion_authorized": Counter(),
    }

    with (R5_DIR / "full_grid_v2_summary.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for key in counters:
                counters[key][row[key]] += 1
            assert row["primary_metric"] == "detectability_relative_prior_score"
            assert row["detected_events_source"] == (
                "relative_prior_score_proxy_count_not_observed_events"
            )

    assert counters["SNR_claim_level"] == Counter({"absolute_blocked": 256256})
    assert counters["event_probability_claim_level"] == Counter({"absolute_blocked": 256256})
    assert counters["p_detect_mapping_claim_level"] == Counter({"relative_with_priors": 256256})
    assert counters["R5_full_grid_v2_run"] == Counter({"True": 256256})
    assert counters["context_route_promotion_authorized"] == Counter({"False": 256256})
    assert counters["main_660_redefinition_authorized"] == Counter({"False": 256256})
    assert counters["route_specific_manual_sign_flip_applied"] == Counter({"False": 256256})
    assert counters["R5_followup_expansion_authorized"] == Counter({"False": 256256})


def test_R5_aggregate_outputs_preserve_route_governance_and_R4_2_carryforward():
    r4_2 = _csv_rows(R5_DIR / "R4_2_validation_grade_carryforward_summary.csv")[0]
    assert r4_2["accepted_gate"] == "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    assert r4_2["fine_confirm_main660_fraction"] == "1.0"
    assert r4_2["fine_confirm_sign_reliable_subset_fraction"] == "1.0"
    assert r4_2["review_refined_main660_fraction"] == "1.0"
    assert r4_2["fine_confirm_agrees_with_review_refined"] == "1.0"
    assert _truthy(r4_2["R4_2_gate_met"])

    coarse = _csv_rows(R5_DIR / "coarse_screen_warning_carryforward_summary.csv")[0]
    assert coarse["coarse_screen_role"] == "screening_only_warning"
    assert coarse["coarse_screen_can_confirm_or_demote_routes"] == "False"
    assert coarse["coarse_screen_ranking_role"] == "warning_only_not_rank_gate"
    assert coarse["R5_ranking_gate_uses_coarse_screen"] == "False"

    main_rows = _csv_rows(R5_DIR / "main_660_full_grid_v2_stability_summary.csv")
    assert {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in main_rows
    } == rv2.R5_MAIN_660_LOCKED_ROUTES
    assert all(row["route_role"] == "main_660" for row in main_rows)
    assert all(row["main_660_route_role_locked"] == "True" for row in main_rows)
    assert all(row["R4_2_validation_grade_carryforward"] == "True" for row in main_rows)

    context_rows = _csv_rows(R5_DIR / "context_route_no_promotion_summary.csv")
    assert context_rows
    assert all(row["context_route_promotion_authorized"] == "False" for row in context_rows)
    assert all(row["route_promotion_eligible"] == "False" for row in context_rows)

    optional = _csv_rows(R5_DIR / "optional_660_governance_summary.csv")[0]
    assert optional["route_id"] == "660_900x1400"
    assert optional["optional_660_900x1400_can_redefine_main_660"] == "False"

    selected_rows = _csv_rows(R5_DIR / "selected_annulus_parallel_lens_summary.csv")
    assert selected_rows
    assert all(
        row["selected_annulus_boundary_policy"]
        == "unchanged_v1_0p5_0p8_parallel_lens_only"
        for row in selected_rows
    )
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in selected_rows
    )


def test_R5_guardrail_summaries_and_manifest_fail_closed():
    detector = _csv_rows(R5_DIR / "detector_blank_claim_guardrail_summary.csv")[0]
    assert detector["ET2030_BNC_direct_to_LI5640_current_input"] == "forbidden"
    assert detector["finite_monte_carlo_zero_event_inferred"] == "False"
    assert detector["false_positive_per_min_claim"] == "analytic_prior_only"
    assert detector["legacy_detector_SNR_output_header_emitted"] == "False"
    assert detector["legacy_calibrated_detector_SNR_output_header_emitted"] == "False"
    assert detector["calibrated_SNR_or_event_probability_claim_emitted"] == "False"

    thermal = _csv_rows(R5_DIR / "thermal_404_sidecar_summary.csv")[0]
    assert thermal["thermal_sidecar_does_not_increase_nodi_score"] == "True"
    assert float(thermal["max_thermal_404_log_multiplier"]) <= 0.0
    assert thermal["thermal_sidecar_used_to_increase_NODI_score"] == "False"

    unit_rows = _csv_rows(R5_DIR / "unit_guardrail_summary.csv")
    assert unit_rows
    assert all(row["status"] == "pass" for row in unit_rows)

    manifest = json.loads((R5_DIR / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["R5_full_grid_v2_run"] is True
    assert manifest["R5_case_rows_before_next_review"] == 256256
    assert manifest["R5_followup_expansion_authorized"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["route_specific_manual_sign_flips_authorized"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["calibrated_event_probability_claim_emitted"] is False
    assert manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False
    assert manifest["biological_specificity_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False


def test_R5_headers_do_not_emit_legacy_SNR_output_names():
    for path in R5_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        headers = _csv_headers(path)
        assert "detector_SNR" not in headers
        assert "calibrated_detector_SNR" not in headers


def test_R5_execution_manifest_freezes_plan_and_scenario_checksums():
    manifest = json.loads((R5_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    for key, value in R5_EXECUTION_MANIFEST_FROZEN_CHECKSUMS.items():
        assert manifest[key] == value

    scenario_manifest = rv2.validate_R5_scenario_bundle_manifest()
    assert {
        row["scenario_id"] for row in scenario_manifest["scenario_bundles"]
    } == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
