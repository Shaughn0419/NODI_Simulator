from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_tsuyama_summary_records_tolerance_and_extrapolation_policy() -> None:
    with root_path("results/post_v2_mandatory_audit/tsuyama_bfp_reference_summary.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["tsuyama_tolerance_profile_id"] for row in rows} == {
        "tsuyama_signed_phase_relative_v1_tight_no_measured_data"
    }
    assert {row["tsuyama_geometry_relation"] for row in rows}.issubset(
        {"paper_geometry", "extrapolated_geometry"}
    )
    extrapolated = [row for row in rows if row["tsuyama_geometry_relation"] == "extrapolated_geometry"]
    assert extrapolated
    assert {row["tsuyama_extrapolation_reason_code"] for row in extrapolated} == {
        "TSUYAMA.EXTRAPOLATED_GEOMETRY"
    }
    assert {row["tsuyama_paper_reproduction_claim_allowed"] for row in rows} == {"False"}
    assert {row["clean_relative_main_supported_by_tsuyama_alone"] for row in rows} == {"False"}


def test_roadmap_declares_generated_tsuyama_tolerance_profile() -> None:
    roadmap = root_path(
        "reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md"
    ).read_text(encoding="utf-8")

    assert "tsuyama_signed_phase_relative_v1_tight_no_measured_data" in roadmap
    assert "not a calibrated Tsuyama tolerance" in roadmap
