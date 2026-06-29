from __future__ import annotations

import math
from pathlib import Path

import pytest

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate10_sidewall_interface_impact as gate10


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate10_payload_passes_and_keeps_no_auth_boundaries() -> None:
    payload = gate10.build_payload()

    assert gate10.validate_payload(payload) == []
    assert payload["summary"]["gate2d_accepted_ledger_rows"] == 4
    assert payload["summary"]["gate9_rc51_field_count"] == 365
    assert payload["summary"]["inventory_rows"] >= 12
    assert payload["summary"]["positive_fixture_rows"] == 4
    assert payload["summary"]["negative_fixture_rows"] >= 12
    assert payload["summary"]["unexpected_pass_count"] == 0
    assert payload["summary"]["production_ingestion_authorized"] is False
    assert payload["summary"]["runtime_configuration_authorized"] is False
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_descriptor_conversion_formula_and_hash_are_stable() -> None:
    descriptor = gate10.build_descriptor(
        descriptor_id="TEST-SIDEWALL-85",
        sidewall_deg_comsol=85.0,
        w_top_nm=500.0,
        depth_nm=900.0,
    )

    assert float(descriptor["sidewall_taper_angle_deg_nodi"]) == pytest.approx(5.0)
    expected_bottom = 500.0 - 2.0 * 900.0 / math.tan(math.radians(85.0))
    assert float(descriptor["W_bottom_unclipped_nm"]) == pytest.approx(
        expected_bottom,
        abs=1e-9,
    )
    assert descriptor["closure_status"] == "open"
    assert gate10.validate_descriptor(descriptor) == []
    assert descriptor["geometry_descriptor_sha256"] == gate10.descriptor_hash(descriptor)

    repeat = gate10.build_descriptor(
        descriptor_id="TEST-SIDEWALL-85",
        sidewall_deg_comsol=85.0,
        w_top_nm=500.0,
        depth_nm=900.0,
    )
    assert repeat["geometry_descriptor_sha256"] == descriptor["geometry_descriptor_sha256"]


def test_sidewall_positive_examples_include_requested_angle_conversions() -> None:
    rows = gate10.build_positive_fixtures()
    by_angle = {float(row["sidewall_deg_comsol"]): row for row in rows}

    assert float(by_angle[85.0]["sidewall_taper_angle_deg_nodi"]) == pytest.approx(5.0)
    assert float(by_angle[90.0]["sidewall_taper_angle_deg_nodi"]) == pytest.approx(0.0)
    assert float(by_angle[70.0]["sidewall_taper_angle_deg_nodi"]) == pytest.approx(20.0)
    assert all(row["observed_result"] == "PASS" for row in rows)


def test_sidewall_bound_rows_without_descriptor_binding_fail_closed() -> None:
    status, reason = gate10.validate_sidewall_bound_row(
        {
            "source_artifact": "PRS",
            "sidewall_aware": "true",
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
        }
    )

    assert status == "QUARANTINE_MISSING_SIDEWALL_DESCRIPTOR_BINDING"
    assert "geometry_descriptor_id" in reason
    assert "geometry_descriptor_sha256" in reason


def test_negative_fixtures_all_fail_as_expected_with_zero_unexpected_pass() -> None:
    positives = gate10.build_positive_fixtures()
    negatives = gate10.build_negative_fixture_catalog(positives[0])
    results, unexpected = gate10.build_mutation_results(positives, negatives)

    assert len(negatives) >= 12
    assert all(row["observed_result"] == "FAIL_AS_EXPECTED" for row in negatives)
    assert unexpected[0]["unexpected_pass_count"] == "0"
    assert unexpected[0]["forbidden_promotion_count"] == "0"
    assert all(row["authorization_promotion"] == "false" for row in results)


def test_authorization_and_measured_geometry_spoofs_hard_fail() -> None:
    descriptor = gate10.build_descriptor(
        descriptor_id="TEST-SPOOF",
        sidewall_deg_comsol=85.0,
        w_top_nm=500.0,
        depth_nm=900.0,
    )
    for field in (
        "jrc_authorized",
        "qch_weighting_authorized",
        "production_ingestion_authorized",
        "runtime_configuration_authorized",
        "formula_use_authorized",
    ):
        row = dict(descriptor)
        row[field] = "true"
        issues = gate10.validate_descriptor(row)
        assert any(field in issue for issue in issues)

    measured = dict(descriptor)
    measured["geometry_claim_level"] = "measured"
    assert "measured geometry claim without evidence" in gate10.validate_descriptor(measured)


def test_rc51_freeze_impact_requires_review_only_geometry_descriptor_addendum() -> None:
    impact = gate10.build_freeze_impact()
    missing_required = [
        row
        for row in impact
        if row["recommendation"]
        == "ADDENDUM_REQUIRED_FAIL_CLOSED_FOR_SIDEWALL_AWARE_ROWS"
    ]

    assert len(impact) >= 18
    assert {row["field_name"] for row in missing_required} >= {
        "geometry_descriptor_id",
        "geometry_descriptor_sha256",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "W_bottom_unclipped_nm",
    }


def test_gate10_written_outputs_have_expected_shape_after_builder_run() -> None:
    manifest = OUT / "NODI_COMSOL_GATE10_SIDEWALL_MANIFEST_20260629.csv"
    if not manifest.exists():
        pytest.skip("Gate10 builder outputs not written yet")

    manifest_rows = read_csv_rows(manifest)
    mutation_rows = read_csv_rows(
        OUT / "NODI_COMSOL_GATE10_SIDEWALL_MUTATION_RESULTS_20260629.csv"
    )
    freeze_rows = read_csv_rows(
        OUT / "NODI_COMSOL_GATE10_SIDEWALL_RC51_FREEZE_IMPACT_MATRIX_20260629.csv"
    )

    assert len(manifest_rows) >= 19
    assert len(mutation_rows) >= 16
    assert all(row["not_evidence"] == "true" for row in manifest_rows)
    assert any(
        row["compatibility_class"] == "addendum-only"
        for row in freeze_rows
    )
