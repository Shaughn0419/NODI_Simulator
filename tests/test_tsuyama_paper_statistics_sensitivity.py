from __future__ import annotations

import json
import math

import pandas as pd

from tools import tsuyama_paper_statistics_sensitivity as stats


def _decomposition_row(*, slope: float = 3.2532795199816804) -> dict[str, object]:
    return {
        "candidate_id": "tau_2ms_global_refphi_plus_collection_narrow",
        "family_id": "D2_operator_phase_bfp_raw",
        "observable": "peak_height",
        "wavelength_nm": 488,
        "geometry": "800x550",
        "limiting_pair": "40-60",
        "limiting_pair_slope": slope,
        "au40_value": 0.6769247923580757,
        "au60_value": 2.5317132069267583,
    }


def test_required_suppression_matches_pair_slope_formula():
    frame = pd.DataFrame([_decomposition_row()])
    rows = stats.sensitivity_rows(frame)
    row = rows.iloc[0]

    expected_multiplier = math.exp(
        (stats.TARGET_EXPONENT - 3.2532795199816804) * math.log(60.0 / 40.0)
    )

    assert math.isclose(
        row["required_high_signal_multiplier"],
        expected_multiplier,
        rel_tol=1.0e-12,
    )
    assert row["required_high_signal_suppression_fraction"] > 0.30
    assert row["paper_statistics_status"] == "paper_statistics_unlikely_alone"


def test_status_classification_keeps_sub_30_percent_as_borderline():
    rows = stats.sensitivity_rows(
        pd.DataFrame(
            [
                _decomposition_row(slope=stats.TARGET_EXPONENT),
                _decomposition_row(slope=2.0),
                _decomposition_row(slope=3.0),
                _decomposition_row(slope=3.3),
            ]
        )
    )

    assert rows.iloc[0]["paper_statistics_status"] == (
        "paper_statistics_plausible_small_effect"
    )
    assert rows.iloc[1]["paper_statistics_status"] == (
        "already_flatter_than_target_or_requires_amplification"
    )
    assert rows.iloc[1]["required_high_signal_multiplier"] > 1.0
    assert rows.iloc[1]["required_high_signal_amplification_fraction"] > 0.0
    assert rows.iloc[1]["interpretation"] == (
        "raw_pair_is_already_flatter_than_target_or_needs_high_signal_amplification"
    )
    assert rows.iloc[2]["paper_statistics_status"] == "paper_statistics_borderline"
    assert rows.iloc[2]["interpretation"] == (
        "finite_count_iqr_or_vendor_size_distribution_could_contribute"
    )
    assert rows.iloc[3]["paper_statistics_status"] == "paper_statistics_unlikely_alone"
    assert rows.iloc[3]["interpretation"] == (
        "would_require_large_high_diameter_signal_suppression"
    )


def test_summarize_rows_marks_any_unlikely_case_as_unlikely_overall():
    raw_rows = stats.sensitivity_rows(
        pd.DataFrame(
            [
                _decomposition_row(slope=3.0),
                _decomposition_row(slope=3.3),
            ]
        )
    )
    summary = stats.summarize_rows(raw_rows)

    assert summary.iloc[0]["case_count"] == 2
    assert summary.iloc[0]["cases_unlikely_alone"] == 1
    assert summary.iloc[0]["paper_statistics_overall_status"] == "unlikely_alone"


def test_write_outputs_preserves_read_only_boundaries(tmp_path):
    input_path = tmp_path / "decomposition.csv"
    pd.DataFrame([_decomposition_row()]).to_csv(input_path, index=False)

    rows, summary, payload = stats.write_outputs(
        input_path=input_path,
        output_dir=tmp_path / "out",
    )

    assert not rows.empty
    assert not summary.empty
    assert payload["event_level_distribution_available"] is False
    assert payload["ev_full_grid_writeback"] is False
    assert payload["selected_annulus_changed"] is False
    assert payload["global_material_defaults_changed"] is False
    saved_payload = json.loads(
        (tmp_path / "out" / stats.JSON_FILENAME).read_text(encoding="utf-8")
    )
    assert saved_payload["claim_level"] == (
        "read_only_paper_statistics_boundary_not_event_resample"
    )
    assert (tmp_path / "out" / stats.RAW_FILENAME).exists()
    assert (tmp_path / "out" / stats.SUMMARY_FILENAME).exists()
    assert (tmp_path / "out" / stats.REPORT_FILENAME).exists()
