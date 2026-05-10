from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import write_pairwise_rank_inversion

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv")
    if not path.exists():
        write_pairwise_rank_inversion(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_pairwise_rank_inversion_schema_and_required_comparisons_exist() -> None:
    rows = _rows()
    required = {
        "candidate_a",
        "candidate_b",
        "comparison_stratum",
        "scalar_order",
        "bfp_order",
        "tsuyama_order",
        "noise_robustness_order",
        "ev_uncertainty_order",
        "selected_annulus_order",
        "pairwise_inversion_flag",
        "pairwise_inversion_reason",
    }
    strata = {row["comparison_stratum"] for row in rows}

    assert rows
    assert required.issubset(rows[0])
    assert {
        "main_vs_control",
        "main_vs_optional_probe",
        "historical_vs_current_main",
        "shortwave_probe_vs_current_main",
    }.issubset(strata)
    assert len(rows) >= 10
