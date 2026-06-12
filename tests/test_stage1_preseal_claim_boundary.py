from __future__ import annotations

import csv
import json

from ._review_package_test_helpers import root_path


def test_stage1_preseal_artifacts_expose_narrowed_gate_without_full_closure() -> None:
    manifest_path = root_path(
        "results/audits/report148_stage1_preseal_review_20260612/"
        "report148_stage1_preseal_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["narrowed_no_data_gate_met"] is True
    assert manifest["full_route_readout_gauge_closure_met"] is False
    assert (
        manifest["full_route_readout_gauge_closure_status"]
        == "not_met_r1_and_c_d_v2_deferred_out_of_no_data_scope"
    )
    scope = manifest["point_estimate_winner_wavelength_scope"]
    assert "candidate-family" in scope
    assert "not detector-resolved" in scope
    assert "not an absolute wavelength winner" in scope

    coverage_path = root_path(
        "results/audits/report148_stage1_preseal_review_20260612/"
        "report148_stage1_coverage_matrix.csv"
    )
    with coverage_path.open(newline="", encoding="utf-8") as handle:
        coverage_rows = list(csv.DictReader(handle))

    assert {row["gauge_mode"] for row in coverage_rows} == {
        "V1_gauge_locked",
        "V2_raw_angular_explicit_norm_sample",
    }
    assert sum(
        row["gate_classification"].startswith("in_narrowed_gate")
        for row in coverage_rows
    ) == 6
    assert sum(
        row["gate_classification"].startswith("out_of_narrowed_gate")
        for row in coverage_rows
    ) == 10
