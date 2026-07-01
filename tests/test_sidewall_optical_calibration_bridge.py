from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

import pytest

from nodi_simulator._exports import (
    DEFAULT_SIM_CFG,
    Channel,
    OpticalSystem,
    compute_reference_field,
)
from nodi_simulator.calibration_models import (
    calibration_contract_summary,
    validate_calibration_table,
)
from nodi_simulator.sidewall_optical_calibration_bridge import (
    SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
    build_calibration_seed_manifest,
    build_sidewall_optical_calibration_readiness_rows,
    build_sidewall_optical_calibration_seed_rows,
)


def test_sidewall_optical_calibration_seed_rows_are_synthetic_not_claims() -> None:
    rows = build_sidewall_optical_calibration_seed_rows()

    assert len(rows) == 4
    assert {row.reference_model_source for row in rows} == {
        "trapezoid_effective_aperture_surrogate"
    }
    assert {row.wavelength_nm for row in rows} == {404, 660}
    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    theta85_404 = next(
        row
        for row in rows
        if row.sidewall_deg_comsol == 85.0 and row.wavelength_nm == 404
    )
    assert 0.0 < theta85_404.g_ref < 1.0
    for row in rows:
        assert row.not_experimental_blank_channel_calibration is True
        assert row.not_full_wave_optical_solver is True
        assert row.not_true_W_eff is True
        assert row.not_detector_response_validation is True
        assert row.not_detection_probability is True
        assert row.claim_boundary == SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY


def test_sidewall_optical_calibration_readiness_rows_cover_required_lanes() -> None:
    rows = build_sidewall_optical_calibration_readiness_rows()
    lanes = {row.evidence_lane for row in rows}

    assert "blank_channel_reference_amplitude_phase" in lanes
    assert "sidewall_geometry_coverage" in lanes
    assert "detector_response_bridge" in lanes
    assert "blank_false_positive_trace" in lanes
    assert "wet_wall_interaction" in lanes
    assert "integrated_route_ledger" in lanes
    for row in rows:
        assert row.target_claim_current is False
        assert row.hard_fail_if_promoted_without
        assert row.claim_boundary == SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY


def test_sidewall_calibration_seed_table_validates_but_cannot_unlock_lookup(
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "sidewall_reference_seed.csv"
    manifest_path = Path(f"{seed_path}.manifest.json")
    rows = [row.to_dict() for row in build_sidewall_optical_calibration_seed_rows()]
    _write_csv(seed_path, rows)
    manifest_path.write_text(
        json.dumps(build_calibration_seed_manifest(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    table_validation = validate_calibration_table(
        str(seed_path),
        "reference_blank_channel",
    )
    contract = calibration_contract_summary(
        table_path=str(seed_path),
        kind="reference_blank_channel",
    )
    assert table_validation["validation_status"] == "valid_minimal_schema"
    assert contract["calibration_manifest_validation_status"] == "valid_minimal_manifest"
    assert contract["synthetic_fixture_active"] is True

    cfg = replace(
        DEFAULT_SIM_CFG,
        reference_model="calibrated_lookup",
        reference_calibration_path=str(seed_path),
    )
    channel = Channel(width_m=500e-9, depth_m=900e-9)
    optical = OpticalSystem(
        wavelength_m=404e-9,
        peak_irradiance_W_m2=1.0,
        beam_waist_x_m=300e-9,
        beam_waist_y_m=700e-9,
        beam_waist_z_m=300e-9,
    )
    with pytest.raises(ValueError, match="synthetic/template fixture"):
        compute_reference_field(channel, optical, cfg)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
