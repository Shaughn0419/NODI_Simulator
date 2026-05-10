from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import write_top_candidate_mandatory_audit

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv")
    if not path.exists():
        write_top_candidate_mandatory_audit(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_top_candidate_audit_consumes_required_relative_evidence_layers() -> None:
    rows = _rows()
    required = {
        "bfp_roi_score",
        "audit_bfp_jacobian_applied",
        "tsuyama_tolerance_profile_id",
        "noise_pass_criterion_id",
        "ev_pass_criterion_id",
        "selected_annulus_primary_gate_switch_blocked",
        "coincidence_event_overlap_proxy_definition",
        "ev_polydispersity_pass_fraction_proxy",
        "contaminant_pass_fraction",
    }

    assert rows
    assert required.issubset(rows[0])
    assert {row["audit_bfp_jacobian_applied"] for row in rows} == {"True"}
    assert {row["selected_annulus_primary_gate_switch_blocked"] for row in rows} == {"True"}


def test_top_candidate_audit_blocks_calibrated_absolute_biological_claims() -> None:
    rows = _rows()

    for field in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "main_660_redefinition_authorized",
    ):
        assert {row[field] for row in rows} == {"False"}
