from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_noise_route_sensitivity_uses_relative_rank_not_absolute_snr_or_margin_floor() -> None:
    with root_path("results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["noise_pass_criterion_id"] for row in rows} == {
        "relative_rank_percentile_stability_vs_nominal_v1"
    }
    assert {row["absolute_snr_gate_used"] for row in rows} == {"False"}
    assert {row["fixed_margin_z_floor_used"] for row in rows} == {"False"}
    assert {row["SNR_claim_level"] for row in rows} == {"absolute_blocked"}
    assert "margin_z" not in rows[0]


def test_noise_route_sensitivity_records_nominal_rank_comparison() -> None:
    with root_path("results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "noise_rank_percentile_in_stratum",
        "nominal_rank_percentile_in_stratum",
        "rank_delta_vs_nominal",
        "percentile_delta_vs_nominal",
        "noise_relative_fragility_flag",
    }
    assert required.issubset(rows[0])
