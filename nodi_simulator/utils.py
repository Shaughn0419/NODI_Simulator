"""
Package-local utility functions for NODI interferometric simulation.

Shared utilities used across multiple modules:
    - interpolate_at_theta: angle interpolation (shared by baseline and runtime)
    - interpolate_complex_at_theta: complex-valued angle interpolation
    - validate_simulation_config: configuration checks
    - sample_initial_position: random particle starting position
    - min_max_normalize: normalization for scoring
    - compute_detected_scattering_field: angular collection proxy
    - compute_baseline_normalization: global E_sca_ref computation
    - compute_baseline_normalization_per_wavelength: per-λ E_sca_ref
"""

import math
from typing import Any, cast

import numpy as np
from copy import copy, deepcopy

from .calibration_models import (
    build_bfp_roi_mask_contract,
    build_raw_blank_trace_bootstrap_boundary,
    calibration_contract_summary,
    load_calibration_rows,
    optional_calibration_float,
    optional_calibration_string,
    resolve_calibration_state_machine,
)
from .data_objects import (
    Particle, Medium, Channel, OpticalSystem, SimulationConfig,
    READOUT_PRESET_CONFIG_OVERRIDES,
    READOUT_PRESET_PROVENANCE,
)
from .detector_units import build_detector_unit_chain_boundary
from .intrinsic_scattering import compute_intrinsic_scattering
from .readout_transfer_model import build_nodi_readout_transfer_diagnostics
from .trajectory import axial_transport_velocity_m_s, estimate_max_axial_velocity
from .uncertainty import build_uncertainty_propagation_boundary


def interpolate_at_theta(
    theta_grid_rad: np.ndarray,
    values: np.ndarray,
    theta_target_rad: float,
) -> float:
    """
    Linearly interpolate values at a specific angle on the theta grid.

    Both compute_baseline_normalization and run_single_case_batch call this
    function to ensure identical interpolation logic.

    Args:
        theta_grid_rad: Angle grid in radians (monotonically increasing).
        values: Values corresponding to theta_grid_rad.
        theta_target_rad: Target angle for interpolation.

    Returns:
        Interpolated value at theta_target_rad.

    Raises:
        ValueError: If theta_target is outside the grid range.
    """
    if theta_target_rad < theta_grid_rad[0] or theta_target_rad > theta_grid_rad[-1]:
        raise ValueError(
            f"theta_target {theta_target_rad:.4f} outside grid range "
            f"[{theta_grid_rad[0]:.4f}, {theta_grid_rad[-1]:.4f}]"
        )
    result = np.interp(theta_target_rad, theta_grid_rad, values)
    return float(result)


def interpolate_complex_at_theta(
    theta_grid_rad: np.ndarray,
    values: np.ndarray,
    theta_target_rad: float,
) -> complex:
    """
    Linearly interpolate complex values at a specific angle.

    Real and imaginary parts are interpolated separately so the same target-angle
    logic can be shared between single-angle collection and weighted collection.
    """
    real = interpolate_at_theta(theta_grid_rad, np.real(values), theta_target_rad)
    imag = interpolate_at_theta(theta_grid_rad, np.imag(values), theta_target_rad)
    return complex(real, imag)


def resolve_collection_theta_rad(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float | None = None,
) -> float:
    """
    Resolve the effective collection angle used by the simulator.

    Modes:
        - "fixed": use optical.collection_theta_rad directly
        - "channel_diffraction": use a weak diffraction-inspired center-angle proxy

    Notes:
        - This is a geometry surrogate rather than a full diffraction solution.
        - Uses an effective wavelength lambda_eff = lambda0 / n_medium.
        - When calibrated blank-channel reference data already drives E_ref,
          the collection center is kept near forward collection (0 rad) to
          reduce geometry double counting.
    """
    if sim_cfg.collection_angle_model == "fixed":
        return float(optical.collection_theta_rad)
    if sim_cfg.collection_angle_model == "channel_diffraction":
        if sim_cfg.reference_model == "calibrated_lookup":
            return 0.0

        n_medium = max(float(medium_refractive_index or 1.0), 1e-9)
        lambda_eff = float(optical.wavelength_m) / n_medium
        ratio = (
            float(sim_cfg.diffraction_order)
            * lambda_eff
            / float(channel.width_m)
        )
        ratio = min(max(ratio, 0.0), 1.0 - 1e-9)
        base_theta = float(np.arcsin(ratio))
        aspect_factor = float(channel.width_m / (channel.width_m + channel.depth_m))
        center_scale = 0.35 + 0.15 * aspect_factor
        return float(center_scale * base_theta)
    raise ValueError(
        "collection_angle_model must be 'fixed' or 'channel_diffraction', "
        f"got {sim_cfg.collection_angle_model}"
    )


def _collection_kernel(
    theta_grid_rad: np.ndarray,
    theta_center_rad: float,
    sigma_rad: float,
) -> np.ndarray:
    """
    Build a normalized Gaussian angular collection kernel on theta.

    The kernel is weighted by sin(theta) so that a 1D theta integral remains a
    better proxy for a solid-angle collection average inside one scattering plane.
    """
    kernel = np.exp(-0.5 * ((theta_grid_rad - theta_center_rad) / sigma_rad) ** 2)
    kernel = kernel * np.maximum(np.sin(theta_grid_rad), 0.0)
    norm = np.trapezoid(kernel, theta_grid_rad)
    if norm <= 0:
        idx = int(np.argmin(np.abs(theta_grid_rad - theta_center_rad)))
        kernel = np.zeros_like(theta_grid_rad, dtype=float)
        kernel[idx] = 1.0
        return kernel
    return kernel / norm


def _pupil_theta_factor(theta_grid_rad: np.ndarray) -> np.ndarray:
    """Weak apodization surrogate for finite-NA collection."""
    return np.sqrt(np.clip(np.cos(theta_grid_rad), 0.0, None))


def _theta_pinhole_factor(
    theta_grid_rad: np.ndarray,
    theta_center_rad: float,
    sigma_rad: float,
) -> np.ndarray:
    """
    Additional theta-domain narrowing as a pinhole surrogate.

    The pinhole is modeled as a second Gaussian centered at the collection
    angle, slightly narrower than the main pupil kernel so that the 2D
    `pupil_slit_surrogate` becomes more than a simple separable theta Gaussian.
    """
    sigma_pin = max(0.65 * float(sigma_rad), np.deg2rad(2.0))
    return np.exp(-0.5 * ((theta_grid_rad - theta_center_rad) / sigma_pin) ** 2)


def _phi_vector_projection(
    theta_grid_rad: np.ndarray,
    phi_grid_rad: np.ndarray,
    scattering_projection_mode: str,
) -> np.ndarray:
    """
    Minimal 2D vector/polarization projection surrogate.

    This keeps the collection stage explicitly theta/phi dependent:
      - amplitude varies with azimuthal projection
      - phase carries a weak angular coupling term
    """
    theta = theta_grid_rad[:, None]
    phi = phi_grid_rad[None, :]
    if scattering_projection_mode == "parallel":
        amplitude = np.cos(phi) * np.clip(np.sqrt((1.0 + np.cos(theta)) / 2.0), 0.0, None)
    elif scattering_projection_mode == "perpendicular":
        amplitude = np.sin(phi) * np.clip(np.sqrt((1.0 + np.cos(theta)) / 2.0), 0.0, None)
    else:
        amplitude = np.ones((len(theta_grid_rad), len(phi_grid_rad)), dtype=float)

    phase = np.exp(1j * 0.5 * np.sin(theta) * np.sin(phi))
    return amplitude * phase


def _optional_calibration_float(
    row: dict[str, Any],
    *keys: str,
    default: float | None = None,
) -> float | None:
    """Return the first finite float found in a calibration row."""
    return optional_calibration_float(row, *keys, default=default)


def _optional_calibration_string(
    row: dict[str, Any],
    *keys: str,
    default: str | None = None,
) -> str | None:
    """Return the first non-empty string found in a calibration row."""
    return optional_calibration_string(row, *keys, default=default)


def _load_collection_operator_calibration(path: str) -> list[dict[str, Any]]:
    """Load a calibrated collection-operator table from CSV or JSON."""
    return load_calibration_rows(path)


def _relative_distance(value: float | None, target: float) -> float:
    """Dimensionless distance for nearest calibration-row lookup."""
    if value is None:
        return 0.0
    scale = max(abs(target), abs(value), 1e-30)
    return abs(value - target) / scale


def _manifest_kind_mismatched(calibration: dict[str, Any]) -> bool:
    """Return True when a loaded calibration manifest belongs to another lane."""
    return str(calibration.get("manifest_validation_status")) == "manifest_kind_mismatch"


def _lookup_collection_operator_calibration(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> dict[str, Any]:
    """
    Resolve optional collection-operator calibration for one geometry.

    The table may contain any of:
      width_nm/depth_nm/wavelength_nm, theta_center_rad/theta_sigma_rad,
      phi_sigma_rad/slit_phi_limit_rad, throughput_scale, operator_id.
    Missing geometric columns are treated as generic rows; missing operator
    parameters fall back to the configured surrogate values.
    """
    path = getattr(sim_cfg, "collection_operator_calibration_path", None)
    requested_id = getattr(sim_cfg, "collection_operator_id", None)
    if not path:
        return {
            "configured": False,
            "status": "not_configured_surrogate",
            "coverage_status": "not_applicable",
            "row": {},
            "source": None,
            "operator_id": requested_id,
            "row_id": None,
            "row_index": None,
            "row_count": 0,
            "calibration_data_role": "not_configured",
            "synthetic_fixture_active": False,
            "table_validation_status": "not_configured",
            "manifest_status": "not_configured",
            "manifest_validation_status": "not_configured",
            "manifest_path": None,
        }

    rows = _load_collection_operator_calibration(str(path))
    contract = calibration_contract_summary(
        table_path=str(path),
        kind="collection_operator",
    )
    if requested_id is not None:
        filtered = [
            (idx, row)
            for idx, row in enumerate(rows)
            if _optional_calibration_string(
                row,
                "operator_id",
                "collection_operator_id",
                "id",
            )
            == str(requested_id)
        ]
        if not filtered:
            return {
                "configured": True,
                "status": "missing_requested_operator_id_using_surrogate",
                "coverage_status": "missing_operator_id",
                "row": {},
                "source": str(path),
                "operator_id": str(requested_id),
                "row_id": None,
                "row_index": None,
                "row_count": len(rows),
                "calibration_data_role": contract["calibration_data_role"],
                "synthetic_fixture_active": bool(contract["synthetic_fixture_active"]),
                "table_validation_status": contract["calibration_table_validation_status"],
                "manifest_status": contract["calibration_manifest_status"],
                "manifest_validation_status": contract[
                    "calibration_manifest_validation_status"
                ],
                "manifest_path": contract["calibration_manifest_path"],
            }
        indexed_rows = filtered
    else:
        indexed_rows = list(enumerate(rows))

    width_nm = float(channel.width_m) * 1e9
    depth_nm = float(channel.depth_m) * 1e9
    wavelength_nm = float(optical.wavelength_m) * 1e9
    n_medium = float(medium_refractive_index)

    scored_rows: list[tuple[float, float, int, dict[str, Any]]] = []
    for idx, row in indexed_rows:
        row_width_nm = _optional_calibration_float(row, "width_nm", "W_nm")
        row_depth_nm = _optional_calibration_float(row, "depth_nm", "H_nm")
        row_wavelength_nm = _optional_calibration_float(
            row,
            "wavelength_nm",
            "lambda_nm",
            "wavelength0_nm",
        )
        row_n_medium = _optional_calibration_float(
            row,
            "medium_refractive_index",
            "n_medium",
        )
        distances = (
            _relative_distance(row_width_nm, width_nm),
            _relative_distance(row_depth_nm, depth_nm),
            _relative_distance(row_wavelength_nm, wavelength_nm),
            _relative_distance(row_n_medium, n_medium),
        )
        max_distance = max(distances)
        score = sum(distance * distance for distance in distances)
        scored_rows.append((score, max_distance, idx, row))

    scored_rows.sort(key=lambda item: item[0])
    _, max_distance, selected_index, selected = scored_rows[0]
    selected_contract = calibration_contract_summary(
        table_path=str(path),
        kind="collection_operator",
        row=selected,
    )
    synthetic_fixture = bool(selected_contract["synthetic_fixture_active"])
    manifest_kind_mismatch = _manifest_kind_mismatched(
        {
            "manifest_validation_status": selected_contract[
                "calibration_manifest_validation_status"
            ]
        }
    )
    selected_id = _optional_calibration_string(
        selected,
        "operator_id",
        "collection_operator_id",
        "id",
        default=str(requested_id) if requested_id is not None else None,
    )
    selected_row_id = _optional_calibration_string(
        selected,
        "calibration_row_id",
        "row_id",
        default=selected_id,
    )
    if max_distance <= 1e-9:
        coverage_status = "covered_exact"
    elif max_distance <= 0.05:
        coverage_status = "covered_nearest_within_5pct"
    else:
        coverage_status = "extrapolated_nearest_row"

    return {
        "configured": True,
        "status": (
            "collection_operator_manifest_kind_mismatch_not_applied"
            if manifest_kind_mismatch
            else (
                "synthetic_operator_fixture_selected_not_applied"
                if synthetic_fixture
                else "calibrated_operator_table_selected"
            )
        ),
        "coverage_status": coverage_status,
        "row": selected,
        "source": str(path),
        "operator_id": selected_id,
        "row_id": selected_row_id,
        "row_index": int(selected_index),
        "row_count": len(rows),
        "max_relative_geometry_distance": float(max_distance),
        "calibration_data_role": selected_contract["calibration_data_role"],
        "synthetic_fixture_active": synthetic_fixture,
        "table_validation_status": selected_contract["calibration_table_validation_status"],
        "manifest_status": selected_contract["calibration_manifest_status"],
        "manifest_validation_status": selected_contract[
            "calibration_manifest_validation_status"
        ],
        "manifest_path": selected_contract["calibration_manifest_path"],
    }


def _lookup_standard_particle_calibration(
    optical: OpticalSystem | None,
    sim_cfg: SimulationConfig,
    collection_operator: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve an optional standard-particle K_sca / phase calibration row."""
    path = getattr(sim_cfg, "standard_particle_calibration_path", None)
    requested_id = getattr(sim_cfg, "standard_particle_calibration_id", None)
    if not path:
        return {
            "configured": False,
            "status": "not_configured",
            "coverage_status": "not_applicable",
            "row": {},
            "source": None,
            "calibration_id": requested_id,
            "row_id": None,
            "row_index": None,
            "row_count": 0,
            "wavelength_count": 0,
            "operator_count": 0,
            "calibration_data_role": "not_configured",
            "synthetic_fixture_active": False,
            "table_validation_status": "not_configured",
            "manifest_status": "not_configured",
            "manifest_validation_status": "not_configured",
            "manifest_path": None,
        }

    rows = _load_collection_operator_calibration(str(path))
    contract = calibration_contract_summary(
        table_path=str(path),
        kind="standard_particle",
    )
    if requested_id is not None:
        filtered = [
            (idx, row)
            for idx, row in enumerate(rows)
            if _optional_calibration_string(
                row,
                "calibration_id",
                "standard_particle_calibration_id",
                "id",
            )
            == str(requested_id)
        ]
        if not filtered:
            return {
                "configured": True,
                "status": "missing_requested_standard_calibration_id",
                "coverage_status": "missing_calibration_id",
                "row": {},
                "source": str(path),
                "calibration_id": str(requested_id),
                "row_id": None,
                "row_index": None,
                "row_count": len(rows),
                "wavelength_count": 0,
                "operator_count": 0,
                "calibration_data_role": contract["calibration_data_role"],
                "synthetic_fixture_active": bool(contract["synthetic_fixture_active"]),
                "table_validation_status": contract["calibration_table_validation_status"],
                "manifest_status": contract["calibration_manifest_status"],
                "manifest_validation_status": contract[
                    "calibration_manifest_validation_status"
                ],
                "manifest_path": contract["calibration_manifest_path"],
            }
        indexed_rows = filtered
    else:
        indexed_rows = list(enumerate(rows))

    target_wavelength_nm = (
        float(optical.wavelength_m) * 1e9 if optical is not None else None
    )
    target_operator_id = (
        str(collection_operator.get("collection_operator_id"))
        if collection_operator
        and collection_operator.get("collection_operator_id") is not None
        else None
    )
    unique_wavelengths = {
        _optional_calibration_float(row, "wavelength_nm", "lambda_nm")
        for row in rows
    }
    unique_operators = {
        _optional_calibration_string(row, "operator_id", "collection_operator_id")
        for row in rows
    }
    unique_wavelengths.discard(None)
    unique_operators.discard(None)

    scored_rows: list[tuple[float, float, int, dict[str, Any]]] = []
    for idx, row in indexed_rows:
        wavelength_nm = _optional_calibration_float(
            row,
            "wavelength_nm",
            "lambda_nm",
        )
        wavelength_distance = (
            _relative_distance(wavelength_nm, target_wavelength_nm)
            if target_wavelength_nm is not None
            else 0.0
        )
        row_operator_id = _optional_calibration_string(
            row,
            "operator_id",
            "collection_operator_id",
        )
        operator_distance = (
            0.0
            if target_operator_id is None
            or row_operator_id is None
            or row_operator_id == target_operator_id
            else 1.0
        )
        max_distance = max(wavelength_distance, operator_distance)
        score = wavelength_distance * wavelength_distance + operator_distance
        scored_rows.append((score, max_distance, idx, row))

    scored_rows.sort(key=lambda item: item[0])
    _, max_distance, selected_index, selected = scored_rows[0]
    selected_contract = calibration_contract_summary(
        table_path=str(path),
        kind="standard_particle",
        row=selected,
    )
    synthetic_fixture = bool(selected_contract["synthetic_fixture_active"])
    manifest_kind_mismatch = _manifest_kind_mismatched(
        {
            "manifest_validation_status": selected_contract[
                "calibration_manifest_validation_status"
            ]
        }
    )
    if max_distance <= 1e-9:
        coverage_status = "covered_exact"
    elif max_distance <= 0.05:
        coverage_status = "covered_nearest_within_5pct"
    else:
        coverage_status = "extrapolated_nearest_row"

    selected_id = _optional_calibration_string(
        selected,
        "calibration_id",
        "standard_particle_calibration_id",
        "id",
        default=str(requested_id) if requested_id is not None else None,
    )
    selected_row_id = _optional_calibration_string(
        selected,
        "calibration_row_id",
        "row_id",
        default=selected_id,
    )
    return {
        "configured": True,
        "status": (
            "standard_particle_manifest_kind_mismatch_not_applied"
            if manifest_kind_mismatch
            else (
                "synthetic_standard_particle_fixture_selected_not_applied"
                if synthetic_fixture
                else "standard_particle_calibration_table_selected"
            )
        ),
        "coverage_status": coverage_status,
        "row": selected,
        "source": str(path),
        "calibration_id": selected_id,
        "row_id": selected_row_id,
        "row_index": int(selected_index),
        "row_count": len(rows),
        "wavelength_count": len(unique_wavelengths),
        "operator_count": len(unique_operators),
        "max_relative_wavelength_or_operator_distance": float(max_distance),
        "calibration_data_role": selected_contract["calibration_data_role"],
        "synthetic_fixture_active": synthetic_fixture,
        "table_validation_status": selected_contract["calibration_table_validation_status"],
        "manifest_status": selected_contract["calibration_manifest_status"],
        "manifest_validation_status": selected_contract[
            "calibration_manifest_validation_status"
        ],
        "manifest_path": selected_contract["calibration_manifest_path"],
    }


def _lookup_blank_false_positive_calibration(
    sim_cfg: SimulationConfig,
) -> dict[str, Any]:
    """Resolve optional blank-trace false-positive calibration summary."""
    path = getattr(sim_cfg, "blank_false_positive_calibration_path", None)
    requested_id = getattr(sim_cfg, "blank_false_positive_calibration_id", None)
    if not path:
        return {
            "configured": False,
            "status": "not_configured",
            "row": {},
            "source": None,
            "calibration_id": requested_id,
            "row_id": None,
            "row_index": None,
            "row_count": 0,
            "calibration_data_role": "not_configured",
            "synthetic_fixture_active": False,
            "table_validation_status": "not_configured",
            "manifest_status": "not_configured",
            "manifest_validation_status": "not_configured",
            "manifest_path": None,
        }

    rows = _load_collection_operator_calibration(str(path))
    contract = calibration_contract_summary(
        table_path=str(path),
        kind="blank_false_positive",
    )
    if requested_id is not None:
        filtered = [
            (idx, row)
            for idx, row in enumerate(rows)
            if _optional_calibration_string(
                row,
                "blank_calibration_id",
                "false_positive_calibration_id",
                "id",
            )
            == str(requested_id)
        ]
        if not filtered:
            return {
                "configured": True,
                "status": "missing_requested_blank_false_positive_id",
                "row": {},
                "source": str(path),
                "calibration_id": str(requested_id),
                "row_id": None,
                "row_index": None,
                "row_count": len(rows),
                "calibration_data_role": contract["calibration_data_role"],
                "synthetic_fixture_active": bool(contract["synthetic_fixture_active"]),
                "table_validation_status": contract["calibration_table_validation_status"],
                "manifest_status": contract["calibration_manifest_status"],
                "manifest_validation_status": contract[
                    "calibration_manifest_validation_status"
                ],
                "manifest_path": contract["calibration_manifest_path"],
            }
        indexed_rows = filtered
    else:
        indexed_rows = list(enumerate(rows))

    selected_index, selected = indexed_rows[0]
    selected_contract = calibration_contract_summary(
        table_path=str(path),
        kind="blank_false_positive",
        row=selected,
    )
    synthetic_fixture = bool(selected_contract["synthetic_fixture_active"])
    manifest_kind_mismatch = _manifest_kind_mismatched(
        {
            "manifest_validation_status": selected_contract[
                "calibration_manifest_validation_status"
            ]
        }
    )
    selected_id = _optional_calibration_string(
        selected,
        "blank_calibration_id",
        "false_positive_calibration_id",
        "id",
        default=str(requested_id) if requested_id is not None else None,
    )
    selected_row_id = _optional_calibration_string(
        selected,
        "calibration_row_id",
        "row_id",
        default=selected_id,
    )
    return {
        "configured": True,
        "status": (
            "blank_false_positive_manifest_kind_mismatch_not_applied"
            if manifest_kind_mismatch
            else (
                "synthetic_blank_false_positive_fixture_selected_not_applied"
                if synthetic_fixture
                else "blank_false_positive_summary_selected"
            )
        ),
        "row": selected,
        "source": str(path),
        "calibration_id": selected_id,
        "row_id": selected_row_id,
        "row_index": int(selected_index),
        "row_count": len(rows),
        "calibration_data_role": selected_contract["calibration_data_role"],
        "synthetic_fixture_active": synthetic_fixture,
        "table_validation_status": selected_contract["calibration_table_validation_status"],
        "manifest_status": selected_contract["calibration_manifest_status"],
        "manifest_validation_status": selected_contract[
            "calibration_manifest_validation_status"
        ],
        "manifest_path": selected_contract["calibration_manifest_path"],
    }


def resolve_effective_polarization_mode(
    field_mode: str,
    scattering_projection_mode: str,
) -> str:
    """
    Resolve a field-side polarization setting into an effective channel label.

    Effective channel labels intentionally stay minimal:
      - parallel / perpendicular: explicit phase-aware polarization channels
      - unpolarized: equal split into both phase-aware channels
      - intensity_proxy: legacy basisless path with no polarization semantics
    """
    if field_mode == "match_scattering":
        if scattering_projection_mode in {"parallel", "perpendicular"}:
            return scattering_projection_mode
        return "intensity_proxy"
    return field_mode


def resolve_polarization_coupling(
    field_mode: str,
    scattering_projection_mode: str,
    cross_polarization_leakage: float,
) -> dict[str, object]:
    """
    Map field-side polarization semantics onto the active scattering channel.

    This is a deliberately minimal surrogate rather than a full vector model.
    It only answers: how much of the illumination/reference amplitude survives
    when the active scattering projection is interpreted as the detector basis?
    """
    leakage = float(np.clip(cross_polarization_leakage, 0.0, 1.0))
    effective_mode = resolve_effective_polarization_mode(
        field_mode,
        scattering_projection_mode,
    )
    detector_mode = (
        scattering_projection_mode
        if scattering_projection_mode in {"parallel", "perpendicular"}
        else "intensity_proxy"
    )

    if detector_mode == "intensity_proxy" or effective_mode == "intensity_proxy":
        amplitude_factor = 1.0
        alignment_status = "legacy_basisless"
    elif effective_mode == "unpolarized":
        amplitude_factor = float(np.sqrt(0.5))
        alignment_status = "split_unpolarized"
    elif effective_mode == detector_mode:
        amplitude_factor = 1.0
        alignment_status = "matched"
    else:
        amplitude_factor = leakage
        alignment_status = "cross_suppressed"

    return {
        "requested_mode": field_mode,
        "effective_mode": effective_mode,
        "detector_mode": detector_mode,
        "amplitude_factor": float(amplitude_factor),
        "alignment_status": alignment_status,
        "cross_polarization_leakage": leakage,
    }


def resolve_projection_basis(mode: str) -> str:
    """Collapse a polarization label into the detector-basis audit vocabulary."""
    if mode in {"parallel", "perpendicular"}:
        return str(mode)
    return "intensity_proxy"


def build_projection_basis_diagnostics(
    prefix: str,
    polarization: dict[str, object],
    scattering_projection_mode: str,
) -> dict[str, object]:
    """
    Export audit-friendly basis diagnostics for illumination / reference fields.

    The detector basis is the basis after the field has been projected onto the
    active scattering channel surrogate. This lets the dashboard distinguish:
      - same-basis full interference
      - same-basis but cross-suppressed leakage
      - same-basis unpolarized split
      - legacy basisless paths
    """
    scattering_basis = resolve_projection_basis(str(scattering_projection_mode))
    projection_basis = resolve_projection_basis(str(polarization["detector_mode"]))
    effective_basis = resolve_projection_basis(str(polarization["effective_mode"]))
    basis_match = bool(projection_basis == scattering_basis)

    if scattering_basis == "intensity_proxy" or projection_basis == "intensity_proxy":
        coupling_status = "legacy_basisless"
    elif not basis_match:
        coupling_status = "basis_mismatch"
    elif str(polarization["effective_mode"]) == "unpolarized":
        coupling_status = "shared_basis_unpolarized_split"
    elif effective_basis == projection_basis:
        coupling_status = "shared_basis_matched"
    else:
        coupling_status = "shared_basis_cross_suppressed"

    return {
        f"{prefix}_projection_basis": projection_basis,
        f"{prefix}_effective_basis": effective_basis,
        f"{prefix}_projection_basis_match": basis_match,
        f"{prefix}_projection_coupling_status": coupling_status,
        f"{prefix}_phase_aware_shared_basis": bool(
            basis_match
            and scattering_basis in {"parallel", "perpendicular"}
            and projection_basis in {"parallel", "perpendicular"}
        ),
    }


def classify_projection_freeze(
    *,
    scattering_projection_basis: str,
    illumination_projection_coupling_status: str,
    reference_projection_coupling_status: str,
    interference_projection_coupling_status: str,
) -> dict[str, object]:
    """
    Convert end-to-end projection-basis diagnostics into one freeze judgement.

    This stays intentionally lightweight:
      - aligned: all three paths are explicitly same-basis and fully matched
      - caution: same-basis semantics still hold, but at least one path is
        cross-suppressed or unpolarized-split
      - mismatch: any legacy/basis-mismatch path means the phase-aware default
        should not be treated as frozen
    """
    scattering_basis = resolve_projection_basis(str(scattering_projection_basis))
    statuses = [
        str(illumination_projection_coupling_status),
        str(reference_projection_coupling_status),
        str(interference_projection_coupling_status),
    ]
    same_basis_statuses = {
        "shared_basis_matched",
        "shared_basis_cross_suppressed",
        "shared_basis_unpolarized_split",
    }

    if scattering_basis == "intensity_proxy":
        agreement_status = "legacy"
        default_frozen = False
        freeze_status = "legacy_non_phase_aware"
        guidance = (
            "当前散射主通道仍是 intensity_proxy；这条路径只应用于 legacy / dark-field 对照，"
            " 不应被当成已冻结的 phase-aware 干涉主链。"
        )
    elif any(status == "basis_mismatch" for status in statuses):
        agreement_status = "mismatch"
        default_frozen = False
        freeze_status = "review_required_before_freeze"
        guidance = (
            "reference / illumination / scattering 至少有一路没有落在同一 detector basis 上；"
            " 当前不应把偏振语义视为已冻结。"
        )
    elif any(status == "legacy_basisless" for status in statuses):
        agreement_status = "mismatch"
        default_frozen = False
        freeze_status = "review_required_before_freeze"
        guidance = (
            "当前仍存在 legacy basisless 偏振路径；冻结结果库前应先把 phase-aware 与 legacy 语义彻底分开。"
        )
    elif all(status == "shared_basis_matched" for status in statuses):
        agreement_status = "aligned"
        default_frozen = True
        freeze_status = "default_frozen_active"
        guidance = (
            "reference / illumination / scattering 当前都在同一 phase-aware detector basis 上，"
            " 可以把这条偏振主链视为已冻结默认。"
        )
    elif all(status in same_basis_statuses for status in statuses):
        agreement_status = "caution"
        default_frozen = False
        freeze_status = "warning_review_before_freeze"
        guidance = (
            "虽然三条路径仍保持同基底语义，但至少有一路已经进入 cross-suppressed"
            " 或 unpolarized-split；冻结前应先确认默认结果是否仍代表目标实验配置。"
        )
    else:
        agreement_status = "mismatch"
        default_frozen = False
        freeze_status = "review_required_before_freeze"
        guidance = (
            "当前偏振语义无法稳定归入已知的 same-basis phase-aware 主链；"
            " 需要先复核 reference / illumination 的投影路径。"
        )

    return {
        "projection_freeze_agreement_status": agreement_status,
        "projection_default_model": "shared_phase_aware_basis",
        "projection_default_frozen": default_frozen,
        "projection_default_freeze_status": freeze_status,
        "projection_freeze_guidance": guidance,
    }


def classify_interference_overlap_freeze(
    *,
    overlap_factor_abs: float,
    overlap_factor_phase_rad: float,
    collapsed_cross_term_scalar: float,
    joint_cross_term_scalar: float,
    joint_available: bool,
    default_model: str = "joint_overlap_integrated",
    aligned_max_abs_factor_deviation: float = 0.15,
    aligned_max_abs_phase_rad: float = 0.15,
    aligned_max_peak_rel_error: float = 0.15,
    caution_max_abs_factor_deviation: float = 0.75,
    caution_max_abs_phase_rad: float = 0.50,
    caution_max_peak_rel_error: float = 0.75,
) -> dict[str, object]:
    """
    Convert overlap diagnostics into one explicit freeze recommendation.
    """
    default_model = str(default_model)
    if default_model not in {"collapsed_then_multiplied", "joint_overlap_integrated"}:
        raise ValueError(
            "default_model must be 'collapsed_then_multiplied' or "
            f"'joint_overlap_integrated', got {default_model}"
        )

    abs_phase = float(abs(float(overlap_factor_phase_rad)))
    collapsed_scalar = float(collapsed_cross_term_scalar)
    joint_scalar = float(joint_cross_term_scalar)

    if default_model == "joint_overlap_integrated":
        default_scalar = max(abs(joint_scalar), 1e-12)
        alternative_factor = (
            float(abs(collapsed_scalar) / default_scalar)
            if default_scalar > 1e-12
            else 1.0
        )
        abs_factor_deviation = float(abs(alternative_factor - 1.0))
        peak_rel_error = float(abs(collapsed_scalar - joint_scalar) / default_scalar)
        alternative_model = "collapsed_then_multiplied"
    else:
        default_scalar = max(abs(collapsed_scalar), 1e-12)
        alternative_factor = float(overlap_factor_abs)
        abs_factor_deviation = float(abs(alternative_factor - 1.0))
        peak_rel_error = float(abs(joint_scalar - collapsed_scalar) / default_scalar)
        alternative_model = "joint_overlap_integrated"

    aligned = bool(
        joint_available
        and abs_factor_deviation <= aligned_max_abs_factor_deviation
        and abs_phase <= aligned_max_abs_phase_rad
        and peak_rel_error <= aligned_max_peak_rel_error
    )
    caution = bool(
        joint_available
        and not aligned
        and abs_factor_deviation <= caution_max_abs_factor_deviation
        and abs_phase <= caution_max_abs_phase_rad
        and peak_rel_error <= caution_max_peak_rel_error
    )

    if not joint_available:
        agreement_status = "unavailable"
        default_role = "default_pending_unavailable"
        default_freeze_status = "freeze_unavailable"
        default_frozen = False
        alternative_role = "unavailable_alternative_overlap"
        guidance = (
            "当前 case 缺少 joint-overlap 审计所需的 reference/scattering 角谱场，"
            " 暂时无法对默认 overlap 主线做 freeze 判断。"
        )
    elif default_model == "joint_overlap_integrated":
        agreement_status = "aligned" if aligned else "caution" if caution else "mismatch"
        default_role = "default_frozen_mainline"
        default_freeze_status = "default_frozen_active"
        default_frozen = True
        if aligned:
            alternative_role = "diagnostic_alternative_agrees"
            guidance = (
                "joint overlap 与 collapsed 口径足够接近；当前可以把 "
                "`joint_overlap_integrated` 视为已冻结默认主线，"
                "`collapsed_then_multiplied` 保留为低风险诊断对照。"
            )
        elif caution:
            alternative_role = "warning_review_alternative"
            guidance = (
                "joint overlap 已作为默认主线冻结，但 collapsed 近似开始出现可见偏差；"
                "后续结果解释应优先引用 joint-overlap 口径。"
            )
        else:
            alternative_role = "legacy_collapsed_review_only"
            guidance = (
                "joint overlap 与 collapsed 已显著脱钩；当前应继续冻结 "
                "`joint_overlap_integrated` 作为默认主线，并把 "
                "`collapsed_then_multiplied` 降级为 legacy 诊断路径。"
            )
    else:
        if aligned:
            agreement_status = "aligned"
            default_role = "default_frozen_mainline"
            default_freeze_status = "default_frozen_active"
            default_frozen = True
            alternative_role = "diagnostic_review_alternative"
            guidance = (
                "joint overlap 与 collapsed 口径足够接近；当前可以继续接受 "
                "`collapsed_then_multiplied` 作为默认主线，"
                "`joint_overlap_integrated` 保留为审计对照。"
            )
        elif caution:
            agreement_status = "caution"
            default_role = "warning_review_mainline"
            default_freeze_status = "warning_review_before_freeze"
            default_frozen = False
            alternative_role = "preferred_review_cross_check"
            guidance = (
                "joint overlap 与 collapsed 的差异已经进入可见区；当前仍可保留 "
                "`collapsed_then_multiplied` 作为工作主线，但冻结结果前应先检查 "
                "joint-overlap 对 clean signal 的影响。"
            )
        else:
            agreement_status = "mismatch"
            default_role = "review_required_mainline"
            default_freeze_status = "review_required_before_freeze"
            default_frozen = False
            alternative_role = "high_priority_review_cross_check"
            guidance = (
                "joint overlap 与 collapsed 已显著脱钩；当前不应把 "
                "`collapsed_then_multiplied` 视为已冻结默认口径，"
                " 至少需要把 joint-overlap 作为高优先级复核路径。"
            )

    return {
        "interference_overlap_abs_factor_deviation": abs_factor_deviation,
        "interference_overlap_abs_phase_rad": abs_phase,
        "interference_overlap_peak_rel_error": peak_rel_error,
        "interference_overlap_threshold_aligned_max_abs_factor_deviation": float(
            aligned_max_abs_factor_deviation
        ),
        "interference_overlap_threshold_aligned_max_abs_phase_rad": float(
            aligned_max_abs_phase_rad
        ),
        "interference_overlap_threshold_aligned_max_peak_rel_error": float(
            aligned_max_peak_rel_error
        ),
        "interference_overlap_threshold_caution_max_abs_factor_deviation": float(
            caution_max_abs_factor_deviation
        ),
        "interference_overlap_threshold_caution_max_abs_phase_rad": float(
            caution_max_abs_phase_rad
        ),
        "interference_overlap_threshold_caution_max_peak_rel_error": float(
            caution_max_peak_rel_error
        ),
        "interference_overlap_joint_available": bool(joint_available),
        "interference_overlap_agreement_status": agreement_status,
        "interference_overlap_default_model": default_model,
        "interference_overlap_alternative_model": alternative_model,
        "interference_overlap_default_role": default_role,
        "interference_overlap_default_frozen": default_frozen,
        "interference_overlap_default_freeze_status": default_freeze_status,
        "interference_overlap_alternative_role": alternative_role,
        "interference_overlap_joint_role": (
            default_role
            if default_model == "joint_overlap_integrated"
            else alternative_role
        ),
        "interference_overlap_collapsed_role": (
            alternative_role
            if default_model == "joint_overlap_integrated"
            else default_role
        ),
        "interference_overlap_guidance": guidance,
    }


def classify_delta_phi_gouy_geometry_validity(
    *,
    channel: Channel,
    optical: OpticalSystem,
    phase_model: str,
) -> dict[str, object]:
    """
    Minimal geometry-validity check for shared-beam delta_phi_gouy semantics.

    Rule adopted from the current roadmap:
      - if W / w_x > 2 and H / w_z > 2, shared-beam Gouy semantics are acceptable
      - otherwise keep them in caution mode
    """
    illumination_geometry = optical.resolve_illumination_geometry()
    beam_waist_x_m = float(illumination_geometry["illumination_beam_waist_x_m"])
    beam_waist_z_m = float(illumination_geometry["illumination_beam_waist_z_m"])
    geometry_source = str(illumination_geometry["illumination_geometry_source"])
    geometry_decoupled = bool(
        illumination_geometry["illumination_geometry_decoupled_from_legacy_shared_beam"]
    )
    width_ratio = float(channel.width_m / max(beam_waist_x_m, 1e-30))
    depth_ratio = float(channel.depth_m / max(beam_waist_z_m, 1e-30))

    if phase_model != "relative_surrogate":
        validity = "not_applicable_legacy_phase_model"
        guidance = (
            "当前相位主链不是 relative_surrogate；shared-beam delta_phi_gouy 的几何判据只作为"
            " 兼容审计量，不参与主判断。"
        )
    elif geometry_decoupled:
        validity = "shared_beam_acceptable"
        guidance = (
            "illumination x/z 几何已显式从 legacy shared beam 语义中拆分，"
            " delta_phi_gouy 不再依赖 shared-beam 假设；当前可按 acceptable 主线处理。"
        )
    elif width_ratio > 2.0 and depth_ratio > 2.0:
        validity = "shared_beam_acceptable"
        guidance = (
            "通道横截面相对 beam waist 足够大；当前 shared-beam delta_phi_gouy 假设可作为"
            " 冻结判断中的可接受近似。"
        )
    else:
        validity = "shared_beam_caution"
        guidance = (
            "通道横截面仍与 beam waist 同量级；shared-beam delta_phi_gouy 语义保留为 caution，"
            " 冻结结果库前应结合 OPD 对照路径一起复核。"
        )

    return {
        "delta_phi_gouy_geometry_width_to_waist_ratio": width_ratio,
        "delta_phi_gouy_geometry_depth_to_waist_ratio": depth_ratio,
        "delta_phi_gouy_geometry_source": geometry_source,
        "delta_phi_gouy_validity": validity,
        "delta_phi_gouy_geometry_guidance": guidance,
    }


def classify_observation_freeze(
    *,
    path_opd_freeze_status: str,
    interference_overlap_default_freeze_status: str,
    projection_default_freeze_status: str,
    delta_phi_gouy_validity: str,
) -> dict[str, object]:
    """
    Collapse the current freeze diagnostics into one auditable result-freeze status.
    """
    statuses = {
        "path_opd": str(path_opd_freeze_status),
        "overlap": str(interference_overlap_default_freeze_status),
        "projection": str(projection_default_freeze_status),
    }
    validity = str(delta_phi_gouy_validity)

    if all(status == "default_frozen_active" for status in statuses.values()) and validity == "shared_beam_acceptable":
        freeze_status = "default_ready_for_result_freeze"
        guidance = (
            "当前 OPD / overlap / projection 三条默认主线都处于 frozen_active，"
            " 且 shared-beam delta_phi_gouy 几何判据可接受；可以进入结果冻结。"
        )
    elif any(status in {"review_required_before_freeze", "freeze_unavailable"} for status in statuses.values()):
        freeze_status = "review_required_before_result_freeze"
        guidance = (
            "当前至少有一条 freeze judgement 仍处于 review_required / unavailable；"
            " 不应直接冻结结果库。"
        )
    elif any(status == "legacy_non_phase_aware" for status in statuses.values()):
        freeze_status = "legacy_phase_path_not_freezable"
        guidance = (
            "当前观测链仍包含 legacy non-phase-aware 路径；这类配置不应直接作为结果冻结主线。"
        )
    else:
        freeze_status = "caution_probe_before_result_freeze"
        guidance = (
            "当前默认主线没有明显失配，但仍存在 warning/caution 项；建议先跑 coarse probe"
            " 快速回归，再决定是否冻结结果库。"
        )

    return {
        "observation_freeze_status": freeze_status,
        "observation_freeze_guidance": guidance,
    }


def classify_design_recommendation(
    *,
    engineering_gate_passed: bool,
    observation_freeze_status: str,
) -> dict[str, object]:
    """
    Collapse engineering gate + observation freeze into one browsing-friendly
    recommendation tier for result tables and dashboard summaries.
    """
    gate_passed = bool(engineering_gate_passed)
    obs_status = str(observation_freeze_status)

    if gate_passed and obs_status == "default_ready_for_result_freeze":
        status = "recommended_default"
        label = "推荐（默认）"
        rank = 4
        guidance = (
            "已通过 engineering gate，且 observation freeze 已 ready；"
            " 可作为当前默认优先候选。"
        )
    elif gate_passed and obs_status == "caution_probe_before_result_freeze":
        status = "recommended_with_caution"
        label = "推荐（需复核）"
        rank = 3
        guidance = (
            "已通过 engineering gate，但 observation freeze 仍带 caution；"
            " 适合作为候选点，但建议先在 Inspector 中复核 freeze 诊断。"
        )
    elif (not gate_passed) and obs_status == "default_ready_for_result_freeze":
        status = "physics_ready_gate_blocked"
        label = "可研究（门槛未过）"
        rank = 2
        guidance = (
            "物理主链已 ready，但当前未通过 engineering gate；"
            " 更适合作为边界 case 或阈值敏感度分析对象。"
        )
    elif obs_status in {
        "review_required_before_result_freeze",
        "legacy_phase_path_not_freezable",
    }:
        status = "not_recommended_freeze_blocked"
        label = "不推荐（冻结未就绪）"
        rank = 0
        guidance = (
            "当前 observation freeze 仍未就绪；不建议把这类 case 当作当前主链推荐结果。"
        )
    else:
        status = "monitor_only"
        label = "观察（暂不推荐）"
        rank = 1
        guidance = (
            "当前既未通过 engineering gate，也没有达到默认推荐条件；"
            " 可保留作监控或对照，但不建议进入默认推荐集合。"
        )

    return {
        "design_recommendation_status": status,
        "design_recommendation_label": label,
        "design_recommendation_rank": rank,
        "design_recommendation_guidance": guidance,
    }


def classify_engineering_gate_explanation(
    *,
    engineering_gate_passed: bool,
    engineering_gate_reason: str,
    engineering_gate_failed_count: int,
) -> dict[str, object]:
    """
    Convert raw engineering gate failures into a stable explanation layer for
    dashboard browsing and exported result summaries.
    """

    def _classify_token(token: str) -> tuple[str, str, str]:
        token = str(token).strip()
        if token.startswith("n_detected<"):
            return (
                "detected_events",
                "检出事件数不足",
                "优先提升绝对检出事件数，先检查检出率、停留时间和局部 SNR 是否一起偏低。",
            )
        if token.startswith("detection_rate<"):
            return (
                "detection_rate",
                "检出率下界不足",
                "当前保守检出率下界偏低，建议先看阈值边界、signal margin 和 phase-flip 是否共同压低了 detect。",
            )
        if "stable_detection_rate" in token:
            return (
                "stable_detection_rate",
                "稳定检出率不足",
                "当前通过阈值的事件里稳定 pulse 占比仍偏低，优先复核 transit time、局部 SNR 和 freeze 状态。",
            )
        if "phase_flip_fraction" in token:
            return (
                "phase_flip_fraction",
                "相位翻转占比过高",
                "当前正负峰翻转过多，建议回看 OPD / material phase / observation freeze 诊断，确认不是相位链不稳。",
            )
        if "mean_peak_margin_z" in token:
            return (
                "peak_margin",
                "峰高 z-margin 不足",
                "当前峰值离背景噪声边界太近，优先提升局部 SNR 或 reference/scattering 干涉增益，而不只看平均峰高。",
            )
        if "strict_paired_detection_rate" in token:
            return (
                "strict_paired",
                "严格双通道确认不足",
                "当前 paired 链能看到信号，但严格双通道确认还不够稳，更适合作为边界 case 观察。",
            )
        if "paired_channel_detection_rate" in token:
            return (
                "paired_detection_rate",
                "双通道检出率不足",
                "当前 paired 通道口径下的有效检出偏低，建议先核对 paired lane 的 signal/noise 和 gate basis。",
            )
        if "paired_channel_mean_peak_margin_z" in token:
            return (
                "paired_peak_margin",
                "双通道峰值 margin 不足",
                "当前 paired 通道峰高离噪声边界太近，建议优先看 paired trace 的局部 margin 与阈值配置。",
            )
        return (
            "other",
            "其他门槛限制",
            "当前未通过的是未分类 gate 项，建议回看 engineering_gate_reason 原文和 Inspector 详细表。",
        )

    reason = str(engineering_gate_reason or "N/A").strip()
    failed_count = int(engineering_gate_failed_count or 0)
    if bool(engineering_gate_passed):
        return {
            "engineering_gate_status_label": "工程门槛通过",
            "engineering_gate_primary_blocker": "pass",
            "engineering_gate_primary_blocker_label": "已通过",
            "engineering_gate_blocker_summary": "已通过 engineering gate",
            "engineering_gate_guidance": "当前 case 已过工程门槛，可优先结合 freeze 与推荐标签继续筛选。",
        }

    raw_tokens = [token.strip() for token in reason.split("/") if token.strip()]
    tokens = [token for token in raw_tokens if token.casefold() != "pass"]
    if not tokens:
        tokens = ["unclassified_failure"]

    blocker_infos = [_classify_token(token) for token in tokens]
    primary_code, primary_label, primary_guidance = blocker_infos[0]
    unique_labels = []
    for _, label, _ in blocker_infos:
        if label not in unique_labels:
            unique_labels.append(label)
    summary = " / ".join(unique_labels)
    if failed_count > 1:
        summary = f"{summary}（共 {failed_count} 项）"

    return {
        "engineering_gate_status_label": "工程门槛未通过",
        "engineering_gate_primary_blocker": primary_code,
        "engineering_gate_primary_blocker_label": primary_label,
        "engineering_gate_blocker_summary": summary,
        "engineering_gate_guidance": primary_guidance,
    }


def build_case_decision_summary(
    *,
    design_recommendation_label: str | None,
    design_recommendation_status: str | None,
    design_recommendation_guidance: str | None,
    engineering_gate_passed: bool,
    engineering_gate_status_label: str | None,
    engineering_gate_primary_blocker_label: str | None,
    engineering_gate_blocker_summary: str | None,
    engineering_gate_guidance: str | None,
    observation_freeze_status: str | None,
    observation_freeze_guidance: str | None = None,
) -> dict[str, object]:
    """
    Convert recommendation / gate / freeze diagnostics into one reusable summary block.
    """
    recommendation_label = str(design_recommendation_label or "未分类")
    recommendation_status = str(design_recommendation_status or "unclassified")
    gate_label = str(
        engineering_gate_status_label
        or ("工程门槛通过" if bool(engineering_gate_passed) else "工程门槛未通过")
    )
    freeze_status = str(observation_freeze_status or "review_required_before_result_freeze")
    blocker_label = str(engineering_gate_primary_blocker_label or "").strip()
    blocker_summary = str(engineering_gate_blocker_summary or "").strip()
    recommendation_guidance = str(design_recommendation_guidance or "").strip()
    gate_guidance = str(engineering_gate_guidance or "").strip()
    freeze_guidance = str(observation_freeze_guidance or "").strip()

    if recommendation_status == "recommended_default":
        tone = "success"
        headline = f"{recommendation_label} | {gate_label} | freeze ready"
        primary_message = "当前点已经同时满足 engineering gate 与默认 freeze 条件。"
        next_step = recommendation_guidance or "优先看它是否位于稳定平台，再决定是否进入更细局部扫描。"
    elif recommendation_status == "recommended_with_caution":
        tone = "warning"
        headline = f"{recommendation_label} | {gate_label} | freeze caution"
        primary_message = "当前点已过 gate，但 freeze 仍带 caution，更适合作为谨慎候选。"
        next_step = (
            recommendation_guidance
            or freeze_guidance
            or "优先复核 overlap / Gouy / OPD 等 freeze 诊断，再决定是否冻结。"
        )
    elif recommendation_status == "physics_ready_gate_blocked":
        tone = "warning"
        headline = f"{recommendation_label} | {gate_label} | freeze ready"
        primary_message = "当前点的 physics 主链已 ready，但 engineering gate 仍未通过。"
        next_step = gate_guidance or "优先看 blocker，再决定是否保留为边界 case。"
    elif recommendation_status == "not_recommended_freeze_blocked":
        tone = "error"
        headline = f"{recommendation_label} | freeze blocked"
        primary_message = "当前点在结果冻结层仍未就绪，不建议进入默认推荐集合。"
        next_step = freeze_guidance or recommendation_guidance or "先复核 freeze 诊断，再决定是否继续分析。"
    else:
        tone = "info"
        headline = f"{recommendation_label} | {gate_label} | freeze={freeze_status}"
        primary_message = "当前点更适合作为观察或对照对象，而不是默认推荐。"
        next_step = (
            recommendation_guidance
            or gate_guidance
            or freeze_guidance
            or "保留作监控或对照，不建议直接进入默认推荐集合。"
        )

    blocker_text = blocker_summary or blocker_label or (
        "已通过 engineering gate" if bool(engineering_gate_passed) else "暂未归类 blocker"
    )
    badge_parts = [recommendation_label, gate_label]
    if freeze_status == "default_ready_for_result_freeze":
        badge_parts.append("freeze ready")
    elif freeze_status == "caution_probe_before_result_freeze":
        badge_parts.append("freeze caution")
    else:
        badge_parts.append(f"freeze={freeze_status}")

    return {
        "decision_summary_tone": tone,
        "decision_summary_headline": headline,
        "decision_summary_badge": " | ".join(part for part in badge_parts if part),
        "decision_summary_primary_message": primary_message,
        "decision_summary_blocker_text": blocker_text,
        "decision_summary_next_step": next_step,
    }


def _resolve_collection_sigma_rad(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> float:
    """
    Resolve an effective angular-kernel width.

    The configured sigma acts as a baseline. Geometry only modulates it weakly,
    with the width dependence carrying more weight than the depth dependence.
    When reference calibration is used, the geometry mainly broadens/narrows the
    collection kernel rather than shifting its center angle.
    """
    sigma_base = float(sim_cfg.collection_sigma_rad)
    n_medium = max(float(medium_refractive_index), 1e-9)
    lambda_eff = float(optical.wavelength_m) / n_medium
    width_scale = np.clip((lambda_eff / max(channel.width_m, 1e-12)) / 0.6, 0.4, 2.0)
    depth_scale = np.clip((lambda_eff / max(channel.depth_m, 1e-12)) / 0.8, 0.5, 1.6)
    sigma_scale = (width_scale ** 0.45) * (depth_scale ** 0.15)
    return float(np.clip(sigma_base * sigma_scale, np.deg2rad(3.0), np.deg2rad(35.0)))


def build_field_measure_diagnostics(sim_cfg: SimulationConfig) -> dict[str, object]:
    """Export the coordinate-measure contract used by angular-field operators."""
    measure = str(sim_cfg.field_coordinate_measure)
    jacobian_applied = bool(sim_cfg.bfp_to_angle_jacobian_applied)
    if measure == "theta_phi_surrogate" and not jacobian_applied:
        measure_status = "surrogate_theta_phi_weights_not_solid_angle"
        normalization_claim = "ranking_surrogate_not_absolute_throughput"
    elif measure == "solid_angle" and jacobian_applied:
        measure_status = "solid_angle_jacobian_applied"
        normalization_claim = "solid_angle_measure_explicit"
    elif measure == "direction_cosine_uv" and jacobian_applied:
        measure_status = "direction_cosine_jacobian_applied"
        normalization_claim = "direction_cosine_measure_explicit"
    else:
        measure_status = "measure_jacobian_contract_incomplete"
        normalization_claim = "do_not_claim_calibrated_quantitative"

    return {
        "field_coordinate_measure": measure,
        "bfp_to_angle_jacobian_applied": jacobian_applied,
        "field_measure_status": measure_status,
        "field_measure_normalization_claim": normalization_claim,
        "detector_mask_units": str(sim_cfg.detector_mask_units),
    }


def build_coordinate_frame_mapping_diagnostics(sim_cfg: SimulationConfig) -> dict[str, object]:
    """Freeze the chip / optical / BFP frame convention used by this route."""
    return {
        "coordinate_frame_mapping": str(sim_cfg.coordinate_frame_mapping),
        "coordinate_frame_mapping_status": "explicit_surrogate_mapping",
        "chip_frame_axes": "x=channel_width,y=flow_direction,z=channel_depth",
        "optical_frame_axes": (
            "detector_projection_surrogate; optical propagation axis is not "
            "assumed to be y_flow or z_depth"
        ),
        "bfp_frame_axes": "theta=collection_polar_angle,phi=slit_azimuth",
    }


def build_detector_forward_diagnostics(
    sim_cfg: SimulationConfig,
    overlap_diagnostics: dict,
) -> dict[str, object]:
    """Describe the detector forward equation currently represented by the simulator."""
    default_overlap_model = str(
        overlap_diagnostics.get(
            "interference_cross_term_model_default",
            sim_cfg.interference_overlap_mode,
        )
    )
    joint_available = bool(
        overlap_diagnostics.get("interference_cross_term_joint_available", False)
    )
    joint_requested = (
        str(sim_cfg.detector_forward_model) == "joint_overlap_coherent_surrogate"
        and default_overlap_model == "joint_overlap_integrated"
    )
    joint_used = bool(joint_requested and joint_available)

    if str(sim_cfg.detector_forward_model) == "collapsed_scalar_surrogate":
        status = "collapsed_scalar_surrogate_active"
        equation = "2*Re(collapse(E_ref)*conj(collapse(E_sca)))"
    elif str(sim_cfg.detector_forward_model) == "roi_intensity_integral":
        status = "roi_intensity_integral_comparison_lane_active"
        equation = "integral_ROI(|E_ref+E_sca|^2-|E_ref|^2)dA"
    elif str(sim_cfg.detector_forward_model) == "roi_complex_mode_overlap_integral":
        status = "roi_complex_mode_overlap_integral_comparison_lane_active"
        equation = "integral_ROI(|E_sca|^2)dA + 2*Re(integral_ROI(E_ref*conj(E_sca))dA)"
    elif str(sim_cfg.detector_forward_model) == "cross_only_joint_overlap_diagnostic":
        status = "cross_only_joint_overlap_diagnostic_lane_active"
        equation = "2*Re(integral_ROI(E_ref*conj(E_sca))dA)"
    elif joint_used:
        status = "joint_overlap_coherent_surrogate_active"
        equation = "2*Re(integral T(theta,phi)*E_ref(theta,phi)*conj(E_sca(theta,phi)) dtheta dphi)"
    elif joint_requested:
        status = "joint_overlap_requested_scalar_surrogate_fallback"
        equation = "2*Re(E_ref_scalar*conj(E_sca_scalar)); angular joint field unavailable"
    else:
        status = "detector_forward_model_overlap_mismatch"
        equation = "surrogate detector equation unresolved; inspect interference_overlap_mode"

    diagnostics = {
        "detector_forward_model": str(sim_cfg.detector_forward_model),
        "detector_forward_status": status,
        "detector_forward_equation": equation,
        "detector_forward_claim_level": "coherent_surrogate_not_detector_unit",
        "detector_forward_photon_units": False,
        "detector_mode_definition": str(sim_cfg.detector_mode_definition),
        "joint_overlap_used": joint_used,
        "collapsed_scalar_error_estimate_available": bool(
            "interference_overlap_factor_abs" in overlap_diagnostics
        ),
    }
    diagnostics.update(build_field_measure_diagnostics(sim_cfg))
    diagnostics.update(build_coordinate_frame_mapping_diagnostics(sim_cfg))
    return diagnostics


def build_complex_field_convention_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    optical: OpticalSystem | None = None,
    intrinsic: dict | None = None,
) -> dict[str, object]:
    """
    Export the complex-field and basis conventions used by the observable chain.

    This is intentionally diagnostic metadata: it freezes the sign, conjugation,
    and S1/S2 bridge assumptions without upgrading the current scalar surrogate
    into a calibrated Jones/vector-optics detector model.
    """
    projection_mode = str(sim_cfg.scattering_projection_mode)
    if projection_mode == "parallel":
        active_mie_basis_component = "S2_complex"
    elif projection_mode == "perpendicular":
        active_mie_basis_component = "S1_complex"
    else:
        active_mie_basis_component = "legacy_intensity_proxy"

    global_phase_source = str(sim_cfg.global_phase_offset_source)
    absolute_phase_locked = bool(global_phase_source != "unmeasured_zero_reference")
    if absolute_phase_locked:
        absolute_polarity_claim = "phase_zero_defined_by_external_or_blank_reference"
    else:
        absolute_polarity_claim = "not_available_without_measured_global_phase_offset"

    na_collection = (
        float(optical.NA_collection)
        if optical is not None and hasattr(optical, "NA_collection")
        else None
    )
    high_na_warning = bool(
        na_collection is not None
        and na_collection >= 0.7
        and str(sim_cfg.vector_optics_mode) == "scalar_surrogate"
    )
    if str(sim_cfg.vector_optics_mode) == "scalar_surrogate":
        vector_validity_status = (
            "scalar_high_NA_caution"
            if high_na_warning
            else "scalar_low_NA_surrogate"
        )
    elif str(sim_cfg.jones_basis_status) == "jones_basis_applied":
        vector_validity_status = "jones_basis_declared_not_full_vector_debye"
    else:
        vector_validity_status = "vector_mode_declared_review_required"

    diagnostics = {
        "complex_time_harmonic_convention": str(
            sim_cfg.complex_time_harmonic_convention
        ),
        "fourier_transform_sign_convention": str(
            sim_cfg.fourier_transform_sign_convention
        ),
        "mie_amplitude_phase_convention": str(
            sim_cfg.mie_amplitude_phase_convention
        ),
        "interference_conjugation_convention": str(
            sim_cfg.interference_conjugation_convention
        ),
        "interference_cross_term_convention": "2*Re(E_ref*conj(E_sca))",
        "global_phase_offset_source": global_phase_source,
        "complex_reference_absolute_phase_locked": absolute_phase_locked,
        "absolute_polarity_claim": absolute_polarity_claim,
        "complex_convention_status": "frozen_surrogate_convention",
        "complex_field_claim_level": "relative_complex_surrogate_not_absolute_phase",
        "polarization_basis_model": str(sim_cfg.polarization_basis_model),
        "jones_basis_status": str(sim_cfg.jones_basis_status),
        "vector_optics_mode": str(sim_cfg.vector_optics_mode),
        "mie_s1_s2_lab_basis_mapping": "parallel->S2,perpendicular->S1",
        "active_mie_basis_component": active_mie_basis_component,
        "S1S2_to_lab_basis_rotation_applied": False,
        "reference_jones_field_defined": False,
        "detector_analyzer_jones_matrix_defined": False,
        "mie_jones_bridge_status": "scalar_S1S2_projection_no_jones_rotation",
        "NA_collection_for_vector_warning": na_collection,
        "high_NA_collection_warning": high_na_warning,
        "vector_validity_status": vector_validity_status,
    }
    if intrinsic is not None:
        diagnostics["mie_intrinsic_complex_fields_available"] = bool(
            "S1_complex" in intrinsic and "S2_complex" in intrinsic
        )
    diagnostics.update(
        build_mie_incident_field_validity_diagnostics(
            optical=optical,
            intrinsic=intrinsic,
        )
    )
    return diagnostics


def build_mie_incident_field_validity_diagnostics(
    *,
    optical: OpticalSystem | None = None,
    intrinsic: dict | None = None,
) -> dict[str, object]:
    """
    Report whether local-plane-wave Mie is an incident-field approximation.

    The current intrinsic solver remains standard Mie / coated-sphere Mie. This
    diagnostic makes focused-beam gradient limits visible without changing the
    numerical scattering result.
    """
    if optical is None or intrinsic is None:
        return {
            "incident_field_model_for_mie": "local_plane_wave",
            "local_plane_wave_validity": "unknown_missing_optical_or_intrinsic_payload",
            "mie_particle_radius_m": None,
            "mie_size_parameter": None,
            "mie_incident_beam_waist_min_m": None,
            "mie_radius_to_beam_waist_ratio": None,
            "mie_field_gradient_across_particle_status": "unknown",
            "mie_incident_field_GLMT_required": False,
            "mie_incident_field_fullwave_required": False,
            "mie_incident_field_claim_level": "local_plane_wave_status_unresolved",
            "mie_illumination_geometry_source": None,
            "mie_illumination_NA": None,
            "mie_incident_field_blocker_summary": "missing_optical_or_intrinsic_payload",
        }

    size_parameter = float(intrinsic.get("size_parameter", 0.0) or 0.0)
    k_m = float(intrinsic["k_m"])
    particle_radius_m = size_parameter / k_m if k_m > 0.0 else None
    geometry = optical.resolve_illumination_geometry()
    beam_waist_min_m = min(
        float(geometry["illumination_beam_waist_x_m"]),
        float(geometry["illumination_beam_waist_y_m"]),
        float(geometry["illumination_beam_waist_z_m"]),
    )
    radius_to_beam = (
        float(particle_radius_m) / beam_waist_min_m
        if particle_radius_m is not None and beam_waist_min_m > 0.0
        else None
    )
    illumination_na = (
        float(optical.illumination_NA) if optical.illumination_NA is not None else None
    )
    ratio = float(radius_to_beam or 0.0)
    na_value = float(illumination_na or 0.0)

    if ratio >= 0.25 or na_value >= 1.0:
        incident_model = "fullwave_required"
        validity = "fullwave_required"
        gradient_status = "field_gradient_or_high_NA_requires_fullwave"
        glmt_required = True
        fullwave_required = True
        claim_level = "local_plane_wave_invalid_for_quantitative_phase"
    elif ratio >= 0.10 or na_value >= 0.70:
        incident_model = "focused_gaussian_GLMT_required"
        validity = "GLMT_required"
        gradient_status = "focused_beam_gradient_requires_GLMT"
        glmt_required = True
        fullwave_required = False
        claim_level = "local_plane_wave_mie_material_only_GLMT_needed"
    elif ratio >= 0.05 or na_value >= 0.50:
        incident_model = "local_plane_wave"
        validity = "caution_for_phase"
        gradient_status = "caution_gradient_across_particle"
        glmt_required = False
        fullwave_required = False
        claim_level = "local_plane_wave_ok_for_ranking_caution_for_phase"
    else:
        incident_model = "local_plane_wave"
        validity = "valid_for_ranking"
        gradient_status = "negligible_for_engineering_ranking"
        glmt_required = False
        fullwave_required = False
        claim_level = "local_plane_wave_mie_for_engineering_ranking"

    blockers: list[str] = []
    if glmt_required:
        blockers.append("GLMT_not_implemented")
    if fullwave_required:
        blockers.append("fullwave_incident_field_not_implemented")
    if validity == "caution_for_phase":
        blockers.append("local_plane_wave_caution_for_phase_or_polarity")

    return {
        "incident_field_model_for_mie": incident_model,
        "local_plane_wave_validity": validity,
        "mie_particle_radius_m": particle_radius_m,
        "mie_size_parameter": size_parameter,
        "mie_incident_beam_waist_min_m": beam_waist_min_m,
        "mie_radius_to_beam_waist_ratio": radius_to_beam,
        "mie_field_gradient_across_particle_status": gradient_status,
        "mie_incident_field_GLMT_required": glmt_required,
        "mie_incident_field_fullwave_required": fullwave_required,
        "mie_incident_field_claim_level": claim_level,
        "mie_illumination_geometry_source": geometry["illumination_geometry_source"],
        "mie_illumination_NA": illumination_na,
        "mie_incident_field_blocker_summary": (
            "none" if not blockers else "; ".join(blockers)
        ),
    }


def build_calibration_state_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    reference: dict,
    optical: OpticalSystem | None = None,
    collection_operator: dict | None = None,
    E_sca_ref: float | None = None,
) -> dict[str, object]:
    """
    Resolve route-level calibration and output-claim metadata.

    This does not alter the runtime signal. It prevents the current
    baseline-particle-normalized scattering field from being mistaken for a
    photon-unit or detector-unit absolute field.
    """
    reference_claim_level = str(reference.get("reference_claim_level", "unknown"))
    amplitude_status = str(
        reference.get("reference_calibration_amplitude_status", "not_calibrated")
    )
    phase_claim = str(
        reference.get("reference_phase_absolute_claim", "not_measured_absolute_phase")
    )

    if amplitude_status == "absolute_calibrated":
        reference_calibration_level = "reference_amplitude_absolute"
    elif amplitude_status == "calibrated_scale_only":
        reference_calibration_level = "reference_scale_only_rho_dependent"
    else:
        reference_calibration_level = "reference_not_calibrated_or_surrogate"

    if phase_claim == "measured_or_fitted_absolute_phase":
        reference_phase_calibration_level = "phase_measured_or_fitted"
    else:
        reference_phase_calibration_level = "phase_unmeasured_zero_or_model_assigned"

    route = str(sim_cfg.scattering_normalization_route)
    standard_calibration = _lookup_standard_particle_calibration(
        optical,
        sim_cfg,
        collection_operator,
    )
    standard_synthetic = bool(standard_calibration.get("synthetic_fixture_active", False))
    standard_manifest_invalid = _manifest_kind_mismatched(standard_calibration)
    standard_row = standard_calibration.get("row", {})
    if (
        not isinstance(standard_row, dict)
        or standard_synthetic
        or standard_manifest_invalid
    ):
        standard_row = {}
    k_sca_value = _optional_calibration_float(
        standard_row,
        "K_sca",
        "K_sca_scale",
        "K_sca_detector_scale",
    )
    global_phase_offset_rad = _optional_calibration_float(
        standard_row,
        "global_phase_offset_rad",
        "phase_offset_rad",
    )
    k_sca_available = (
        k_sca_value is not None
        and float(k_sca_value) > 0.0
        and not standard_synthetic
        and not standard_manifest_invalid
    )
    standard_phase_offset_available = (
        global_phase_offset_rad is not None
        and not standard_synthetic
        and not standard_manifest_invalid
    )
    if standard_synthetic:
        k_status = "synthetic_standard_particle_fixture_not_experimental"
    elif standard_manifest_invalid:
        k_status = "standard_particle_manifest_kind_mismatch_not_applied"
    elif k_sca_available:
        k_status = "standard_particle_table_available"
    else:
        k_status = str(sim_cfg.K_sca_calibration_status)
    if route == "baseline_particle_relative":
        scattering_status = "baseline_particle_relative_active"
        scattering_level = "relative_baseline_particle_normalized"
        baseline_role = "relative_scattering_scale_anchor_not_absolute_detector_unit"
        baseline_abs_restored = False
        photon_allowed = False
        detector_allowed = False
        normalization_claim = "relative_field_units_not_photon_or_detector_units"
    else:
        scattering_status = "unsupported_absolute_route_blocked"
        scattering_level = "absolute_route_requested_but_unavailable"
        baseline_role = "absolute_route_requires_explicit_K_sca_or_power_chain"
        baseline_abs_restored = False
        photon_allowed = False
        detector_allowed = False
        normalization_claim = "do_not_use_for_quantitative_output"

    if reference_claim_level in {
        "reference_calibrated_relative",
        "paper_aligned_comparison",
        "engineering_ranking",
        "legacy_debug",
    }:
        output_claim_level = reference_claim_level
    elif reference_calibration_level == "reference_amplitude_absolute":
        output_claim_level = "reference_calibrated_relative"
    else:
        output_claim_level = "engineering_ranking"

    max_lockin_frequency_hz = max(
        float(sim_cfg.pod_lockin_frequency_Hz),
        float(sim_cfg.nodi_lockin_frequency_Hz),
    )
    readout_sampled_carrier_route = (
        str(sim_cfg.readout_internal_demod_route) == "sampled_carrier_demod_on_event_grid"
    )
    readout_sampling_required_rate_hz = 10.0 * max_lockin_frequency_hz
    readout_sampling_hard_gate_passed = bool(
        (not readout_sampled_carrier_route)
        or float(sim_cfg.sampling_rate_Hz) >= readout_sampling_required_rate_hz
    )
    readout_sampling_claim_blocker_active = bool(
        readout_sampled_carrier_route and not readout_sampling_hard_gate_passed
    )
    if readout_sampling_claim_blocker_active and str(sim_cfg.readout_preset).startswith(
        "tsuyama_2024_paired_"
    ):
        output_claim_level = "engineering_diagnostic"

    blockers = [
        "missing_detector_unit_noise_model",
        "missing_readout_electronics_calibration",
        "missing_concentration_to_count_model",
    ]
    if not k_sca_available:
        blockers.insert(0, "missing_K_sca_standard_calibration")
    if standard_synthetic:
        blockers.insert(0, "synthetic_calibration_fixture_not_experimental")
    if readout_sampling_claim_blocker_active:
        blockers.insert(0, "sampled_carrier_readout_underresolved")
    if (
        reference_phase_calibration_level != "phase_measured_or_fitted"
        and not standard_phase_offset_available
    ):
        blockers.append("missing_global_phase_offset_calibration")

    k_uncertainty_required_inputs = (
        "standard_particle_size_distribution",
        "standard_particle_shape_uncertainty",
        "standard_particle_ligand_shell",
        "standard_particle_batch_metadata",
        "standard_particle_concentration_uncertainty",
        "standard_particle_material_dataset_uncertainty",
    )
    k_uncertainty_blockers = [
        "missing_standard_particle_size_distribution",
        "missing_standard_particle_shape_uncertainty",
        "missing_standard_particle_ligand_shell",
        "missing_standard_particle_batch_metadata",
        "missing_standard_particle_concentration_uncertainty",
        "missing_standard_particle_material_dataset_uncertainty",
        "K_sca_not_calibrated",
        "K_sca_uncertainty_not_propagated",
    ]
    mie_to_power_blockers = [
        "incident_power_density_not_applied",
        "dCsca_dOmega_not_converted_to_dP_sca_dOmega",
        "detector_etendue_not_calibrated",
        "detector_field_voltage_conversion_not_calibrated",
    ]
    if not k_sca_available:
        mie_to_power_blockers.append("K_sca_not_available_as_residual_calibration")
    else:
        mie_to_power_blockers.append(
            "K_sca_available_only_as_lumped_residual_not_power_chain"
        )
    operator = collection_operator or {}
    absolute_throughput_calibrated = bool(
        operator.get(
            "absolute_throughput_calibrated",
            reference.get("absolute_throughput_calibrated", False),
        )
    )
    if not absolute_throughput_calibrated:
        mie_to_power_blockers.insert(3, "absolute_optical_throughput_not_calibrated")
    detector_unit_boundary = build_detector_unit_chain_boundary(
        sim_cfg,
        optical=optical,
        collection_operator=operator,
        calibration_state={
            "K_sca_calibration_status": k_status,
            "absolute_throughput_calibrated": absolute_throughput_calibrated,
        },
    )
    state_machine_boundary = resolve_calibration_state_machine(
        lanes={
            "reference": reference_calibration_level,
            "reference_phase": reference_phase_calibration_level,
            "scattering": scattering_level,
            "detector_units": detector_unit_boundary["detector_unit_chain_status"],
            "readout": "lockin_surrogate_not_physical_electronics",
            "count": "conditional_event_detection_not_count_rate",
        },
        output_claim_level=output_claim_level,
        synthetic_fixture_active=standard_synthetic
        or bool(operator.get("collection_operator_synthetic_fixture_active", False)),
    )
    identifiability_blockers = [
        "no_standard_particle_measurements",
        "no_multi_wavelength_calibration",
        "no_multi_geometry_calibration",
        "no_held_out_validation",
        "A_ref_K_sca_phase_throughput_gain_not_jointly_identifiable",
    ]

    return {
        "calibration_state_machine_version": str(
            sim_cfg.calibration_state_machine_version
        ),
        "calibration_state_machine_status": "partial_lane_calibration_only",
        "output_claim_level": output_claim_level,
        "calibrated_quantitative_unlocked": False,
        "output_claim_blocker_summary": " / ".join(blockers),
        "readout_sampling_output_claim_blocker_active": (
            readout_sampling_claim_blocker_active
        ),
        "readout_sampling_hard_gate_required_rate_Hz": readout_sampling_required_rate_hz,
        "readout_sampling_hard_gate_passed": readout_sampling_hard_gate_passed,
        "reference_calibration_level": reference_calibration_level,
        "reference_phase_calibration_level": reference_phase_calibration_level,
        "scattering_normalization_route": route,
        "scattering_normalization_status": scattering_status,
        "scattering_normalization_claim": normalization_claim,
        "scattering_calibration_level": scattering_level,
        "baseline_normalization_role": baseline_role,
        "baseline_particle_absolute_scale_restored": baseline_abs_restored,
        "baseline_normalized_E_sca_allowed_in_photon_unit_route": photon_allowed,
        "baseline_normalized_E_sca_allowed_in_detector_unit_route": detector_allowed,
        "baseline_normalized_absolute_route_blocker_active": bool(route == "baseline_particle_relative"),
        "detector_unit_claim_allowed": detector_allowed,
        "photon_unit_claim_allowed": photon_allowed,
        "absolute_route_claim_blocker": (
            "baseline_normalized_E_sca_cannot_unlock_detector_or_photon_units"
            if route == "baseline_particle_relative"
            else "absolute_scattering_route_not_implemented"
        ),
        "E_sca_ref_normalization_role": (
            "divides_detected_scattering_field_for_relative_ranking"
        ),
        "E_sca_ref_for_relative_normalization": (
            float(E_sca_ref) if E_sca_ref is not None else None
        ),
        "K_sca_calibration_status": k_status,
        "K_sca_value": (
            float(k_sca_value)
            if k_sca_available and k_sca_value is not None
            else None
        ),
        "K_sca_scope": (
            str(
                _optional_calibration_string(
                    standard_row,
                    "K_sca_scope",
                    "scope",
                    default="standard_particle_lumped_detector_scale",
                )
            )
            if k_sca_available
            else "none"
        ),
        "K_sca_role": (
            "lumped_residual_scale_available_not_mie_to_power_chain"
            if k_sca_available
            else "not_applied"
        ),
        "mie_to_power_chain_status": (
            "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
        ),
        "mie_differential_cross_section_source": "mie_dCsca_dOmega_nominal",
        "scattered_power_conversion_status": (
            "not_applied_no_incident_power_density_or_detector_etendue"
        ),
        "detector_field_units": "arbitrary_relative_field_units",
        "detector_voltage_units": "not_calibrated",
        "power_chain_absolute_units_available": False,
        "K_sca_power_chain_role": (
            "available_as_lumped_residual_cannot_replace_mie_to_power_chain"
            if k_sca_available
            else "not_available_cannot_replace_mie_to_power_chain"
        ),
        "mie_to_power_chain_blocker_summary": " / ".join(mie_to_power_blockers),
        "standard_particle_calibration_status": k_status,
        "standard_particle_calibration_path_configured": bool(
            standard_calibration.get("configured")
        ),
        "standard_particle_calibration_source": standard_calibration.get("source"),
        "standard_particle_calibration_id": standard_calibration.get("calibration_id"),
        "standard_particle_calibration_row_id": standard_calibration.get("row_id"),
        "standard_particle_calibration_row_index": standard_calibration.get(
            "row_index"
        ),
        "standard_particle_calibration_row_count": standard_calibration.get(
            "row_count"
        ),
        "standard_particle_calibration_coverage_status": standard_calibration.get(
            "coverage_status"
        ),
        "standard_particle_calibration_table_status": standard_calibration.get(
            "status"
        ),
        "standard_particle_calibration_max_relative_distance": standard_calibration.get(
            "max_relative_wavelength_or_operator_distance"
        ),
        "standard_particle_calibration_data_role": standard_calibration.get(
            "calibration_data_role"
        ),
        "standard_particle_synthetic_fixture_active": standard_synthetic,
        "standard_particle_table_validation_status": standard_calibration.get(
            "table_validation_status"
        ),
        "standard_particle_manifest_status": standard_calibration.get(
            "manifest_status"
        ),
        "standard_particle_manifest_validation_status": standard_calibration.get(
            "manifest_validation_status"
        ),
        "standard_particle_manifest_path": standard_calibration.get("manifest_path"),
        "global_phase_offset_rad": (
            float(global_phase_offset_rad)
            if global_phase_offset_rad is not None
            else None
        ),
        "global_phase_offset_calibration_status": (
            "standard_particle_table_phase_offset_available"
            if standard_phase_offset_available
            else "not_available_no_standard_particle_phase_offset"
        ),
        "K_sca_uncertainty_status": (
            "not_propagated_standard_particle_table_without_uncertainty_budget"
            if k_sca_available
            else "not_propagated_no_standard_particle_uncertainty_budget"
        ),
        "K_sca_uncertainty_required_inputs": "; ".join(
            k_uncertainty_required_inputs
        ),
        "K_sca_uncertainty_propagated_to_outputs": False,
        "standard_particle_uncertainty_budget_status": (
            "missing_standard_particle_uncertainty_budget"
        ),
        "standard_particle_size_distribution_status": "not_provided",
        "standard_particle_shape_uncertainty_status": "not_provided",
        "standard_particle_ligand_shell_status": "not_provided",
        "standard_particle_batch_status": "not_provided",
        "standard_particle_concentration_uncertainty_status": "not_provided",
        "standard_particle_material_dataset_uncertainty_status": (
            "not_uncertainty_quantified"
        ),
        "K_sca_uncertainty_blocker_summary": " / ".join(k_uncertainty_blockers),
        "calibration_design_rank": (
            "single_table_dimension_unvalidated"
            if k_sca_available
            else "none"
        ),
        "calibration_design_rank_reason": (
            "standard_particle_table_available_without_held_out_validation"
            if k_sca_available
            else "no_standard_particle_calibration"
        ),
        "calibration_standard_count": (
            int(standard_calibration.get("row_count", 0)) if k_sca_available else 0
        ),
        "calibration_wavelength_count": (
            int(standard_calibration.get("wavelength_count", 0))
            if k_sca_available
            else 0
        ),
        "calibration_geometry_count": (
            int(standard_calibration.get("operator_count", 0))
            if k_sca_available
            else 0
        ),
        "calibration_held_out_validation_status": (
            "not_available_no_standard_particle_design"
        ),
        "calibration_held_out_error": None,
        "calibration_identifiability_blocker_summary": " / ".join(
            identifiability_blockers
        ),
        "calibration_fit_parameter_coupling_status": (
            "A_ref_K_sca_phase_throughput_detector_gain_coupled"
        ),
        "calibration_design_minimum_requirement_status": (
            "not_met_requires_standard_particle_and_held_out_dimension"
        ),
        "fit_parameters_identifiable": False,
        "detector_calibration_level": "surrogate_not_detector_unit",
        "readout_calibration_level": "lockin_surrogate_not_physical_electronics",
        "count_calibration_level": "conditional_event_detection_not_count_rate",
        **detector_unit_boundary,
        **state_machine_boundary,
    }


def build_detector_noise_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    collection_operator: dict | None = None,
    mean_shot_noise_std: float | None = None,
    mean_intensity_proxy: float | None = None,
    mean_baseline_proxy: float | None = None,
    reference_enhancement_gain: float | None = None,
) -> dict[str, object]:
    """
    Describe detector/noise/dynamic-range semantics without changing signals.

    The current runtime keeps arbitrary signal units and an engineering
    intensity-proxy noise surrogate. Photon-unit, RIN, speckle, saturation, and
    ADC routes are explicitly marked unavailable until calibrated inputs exist.
    """
    shot_status = (
        "intensity_proxy_shot_noise_surrogate"
        if float(sim_cfg.shot_noise_scale) > 0.0
        else "disabled"
    )
    electronics_status = (
        "gaussian_additive_surrogate"
        if float(sim_cfg.noise_std) > 0.0
        else "disabled"
    )
    drift_status = (
        "linear_drift_surrogate"
        if str(sim_cfg.noise_model) == "gaussian_plus_drift"
        and float(sim_cfg.drift_slope) > 0.0
        else "disabled"
    )
    post_readout_status = (
        "post_readout_gaussian_or_drift_surrogate"
        if float(sim_cfg.post_readout_noise_std) > 0.0
        or float(sim_cfg.post_readout_drift_slope) > 0.0
        else "disabled"
    )
    lockin_enbw_hz = (
        1.0 / (4.0 * float(sim_cfg.lockin_time_constant_s))
        if float(sim_cfg.lockin_time_constant_s) > 0.0
        else None
    )
    operator = collection_operator or {}
    absolute_throughput_route = str(
        operator.get("absolute_throughput_route", sim_cfg.absolute_throughput_route)
    )
    absolute_throughput_calibrated = bool(
        operator.get("absolute_throughput_calibrated", False)
    )

    return {
        "noise_model_route": str(sim_cfg.detector_noise_model_route),
        "detector_noise_claim_level": "engineering_noise_surrogate_not_detector_unit",
        "detector_signal_unit_convention": "arbitrary_relative_signal_units",
        "absolute_throughput_route": absolute_throughput_route,
        "absolute_throughput_calibrated": absolute_throughput_calibrated,
        "photon_unit_noise_model": str(sim_cfg.photon_unit_noise_model),
        "photon_unit_noise_model_status": str(sim_cfg.photon_unit_noise_model),
        "photon_count_route_active": False,
        "photodiode_responsivity_A_per_W": None,
        "transimpedance_gain_V_per_A": None,
        "lockin_ENBW_Hz": lockin_enbw_hz,
        "lockin_ENBW_status": "first_order_lockin_surrogate",
        "lockin_ENBW_claim_level": (
            "first_order_surrogate_not_measured_lockin_electronics"
        ),
        "shot_noise_model_status": shot_status,
        "photon_shot_noise_term_status": shot_status,
        "shot_noise_scale": float(sim_cfg.shot_noise_scale),
        "mean_shot_noise_std": mean_shot_noise_std,
        "mean_shot_noise_intensity_proxy": mean_intensity_proxy,
        "mean_shot_noise_baseline_proxy": mean_baseline_proxy,
        "shot_noise_limited_snr": None,
        "electronics_noise_model_status": electronics_status,
        "electronics_noise_term_status": electronics_status,
        "electronics_noise_std": float(sim_cfg.noise_std),
        "electronics_noise_limited_snr": None,
        "rin_noise_model_status": str(sim_cfg.rin_noise_model),
        "rin_noise_term_status": str(sim_cfg.rin_noise_model),
        "rin_limited_snr": None,
        "speckle_background_noise_model_status": str(
            sim_cfg.speckle_background_noise_model
        ),
        "speckle_like_noise_term_status": str(sim_cfg.speckle_background_noise_model),
        "drift_noise_model_status": drift_status,
        "drift_noise_term_status": drift_status,
        "post_readout_noise_model_status": post_readout_status,
        "lockin_output_noise_term_status": post_readout_status,
        "noise_terms_schema_version": "noise_terms_v1",
        "noise_term_quantitative_contribution_status": (
            "not_available_arbitrary_units"
        ),
        "noise_terms": {
            "photon_shot": shot_status,
            "electronics": electronics_status,
            "RIN": str(sim_cfg.rin_noise_model),
            "speckle_like": str(sim_cfg.speckle_background_noise_model),
            "drift": drift_status,
            "lockin_output_noise": post_readout_status,
        },
        "detector_dynamic_range_model": str(sim_cfg.detector_dynamic_range_model),
        "detector_saturation_status": "not_evaluated_no_detector_range",
        "detector_saturation_margin": None,
        "adc_dynamic_range_model": str(sim_cfg.adc_dynamic_range_model),
        "ADC_dynamic_range_status": "not_evaluated_no_adc_range",
        "ADC_dynamic_range_margin": None,
        "dynamic_range_margin": None,
        "blank_trace_noise_model_fit_quality": None,
        "reference_enhancement_gain": reference_enhancement_gain,
        "reference_enhancement_snr_claim": (
            "not_monotonic_without_photon_unit_noise_model"
        ),
    }


def build_background_field_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    e_sca_to_ref_amplitude_ratio_estimate: float | None = None,
    extinction_to_beam_area_estimate: float | None = None,
    reference_depletion_fraction_estimate: float | None = None,
) -> dict[str, object]:
    """
    Export residual-background and weak-superposition provenance.

    The simulator currently subtracts the reference baseline but does not model
    residual transmitted leakage, stray fields, speckle-like blank fields, or
    particle-induced perturbations of the channel reference field as independent
    complex fields.
    """
    subtraction_status = "active" if bool(sim_cfg.background_subtraction_on) else "disabled"
    e_ratio = (
        float(e_sca_to_ref_amplitude_ratio_estimate)
        if e_sca_to_ref_amplitude_ratio_estimate is not None
        and np.isfinite(e_sca_to_ref_amplitude_ratio_estimate)
        else None
    )
    extinction_ratio = (
        float(extinction_to_beam_area_estimate)
        if extinction_to_beam_area_estimate is not None
        and np.isfinite(extinction_to_beam_area_estimate)
        else None
    )
    depletion_fraction = (
        float(reference_depletion_fraction_estimate)
        if reference_depletion_fraction_estimate is not None
        and np.isfinite(reference_depletion_fraction_estimate)
        else None
    )
    if e_ratio is None and extinction_ratio is None:
        superposition_validity = "not_evaluated_missing_reference_or_beam_area"
    elif (
        (e_ratio is not None and e_ratio >= 0.5)
        or (extinction_ratio is not None and extinction_ratio >= 0.1)
        or (depletion_fraction is not None and depletion_fraction >= 0.1)
    ):
        superposition_validity = "requires_joint_fullwave"
    elif (
        (e_ratio is not None and e_ratio >= 0.1)
        or (extinction_ratio is not None and extinction_ratio >= 0.01)
        or (depletion_fraction is not None and depletion_fraction >= 0.01)
    ):
        superposition_validity = "caution_reference_perturbation"
    else:
        superposition_validity = "weak_scatterer_valid"

    superposition_blockers = [
        "joint_fullwave_channel_particle_solution_not_implemented",
        "reference_depletion_not_computed_from_field_solution",
    ]
    if e_ratio is None:
        superposition_blockers.append("E_sca_to_E_ref_ratio_unavailable")
    if extinction_ratio is None:
        superposition_blockers.append("extinction_to_beam_area_unavailable")
    if superposition_validity != "weak_scatterer_valid":
        superposition_blockers.append("superposition_not_validated_for_quantitative_claim")

    return {
        "background_field_model": str(sim_cfg.background_field_model),
        "background_field_status": (
            "baseline_subtraction_only_no_explicit_leakage_field"
        ),
        "background_claim_level": "engineering_background_surrogate_not_measured_blank",
        "background_subtraction_on": bool(sim_cfg.background_subtraction_on),
        "background_subtraction_status": subtraction_status,
        "residual_transmitted_leakage_model": str(sim_cfg.transmitted_leakage_model),
        "residual_transmitted_leakage_status": "not_modeled",
        "transmitted_leakage_model": str(sim_cfg.transmitted_leakage_model),
        "stray_light_model": str(sim_cfg.stray_light_model),
        "stray_light_status": "not_modeled",
        "speckle_like_background_status": str(sim_cfg.speckle_background_noise_model),
        "blank_trace_provenance": "synthetic_event_background_segment",
        "blank_trace_empirical_available": False,
        "blank_trace_noise_model_fit_quality": None,
        "particle_induced_channel_perturbation_model": str(
            sim_cfg.particle_induced_channel_perturbation_model
        ),
        "particle_induced_channel_phase_perturbation_status": (
            "not_modeled_weak_superposition_assumed"
        ),
        "independent_superposition_status": "E_ref_plus_E_sca_independent_surrogate",
        "weak_superposition_validity_status": "not_a_fullwave_channel_perturbation_model",
        "superposition_validity_status": superposition_validity,
        "E_sca_to_E_ref_amplitude_ratio_estimate": e_ratio,
        "extinction_to_beam_area_estimate": extinction_ratio,
        "reference_depletion_fraction_estimate": depletion_fraction,
        "reference_depletion_estimate_status": (
            "not_computed_requires_joint_field_solution"
            if depletion_fraction is None
            else "proxy_estimate_not_fullwave_validated"
        ),
        "channel_particle_coupling_model": "independent_superposition",
        "joint_fullwave_required_for_quantitative_phase": (
            superposition_validity != "weak_scatterer_valid"
        ),
        "superposition_validity_claim_level": (
            "engineering_weak_superposition_diagnostic_not_fullwave_validated"
        ),
        "superposition_validity_blocker_summary": " / ".join(
            superposition_blockers
        ),
        "nodi_signal_component_model": "scattering_interference_only_surrogate",
        "nodi_signal_component_status": (
            "no_forward_extinction_or_channel_perturbation_component"
        ),
        "nodi_forward_extinction_leakage_status": "not_modeled",
        "nodi_transmitted_leakage_component_status": "not_modeled",
        "nodi_particle_induced_channel_coupling_status": (
            "not_modeled_weak_superposition_assumed"
        ),
        "nodi_signal_component_claim_level": (
            "engineering_scattering_interference_surrogate_not_full_signal_decomposition"
        ),
        "nodi_component_escalation_route": (
            "measured_blank_or_fullwave_required_for_extinction_leakage"
        ),
        "measured_blank_trace_required_for_calibrated_noise": True,
    }


def _readout_preset_mismatch_fields(sim_cfg: SimulationConfig) -> list[str]:
    """Return fields whose current value no longer matches the named preset."""
    expected = READOUT_PRESET_CONFIG_OVERRIDES.get(str(sim_cfg.readout_preset), {})
    mismatches: list[str] = []
    for field_name, expected_value in expected.items():
        actual_value = getattr(sim_cfg, field_name)
        if isinstance(expected_value, float):
            if not np.isclose(float(actual_value), expected_value, rtol=1e-12, atol=1e-15):
                mismatches.append(field_name)
        elif actual_value != expected_value:
            mismatches.append(field_name)
    return mismatches


def build_readout_convention_diagnostics(
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """
    Export readout preset, phase, sampling, and unit-convention provenance.

    This is a metadata layer around the current lock-in surrogate. It does not
    upgrade the simulator to calibrated photodiode / lock-in voltage units.
    """
    readout_preset = str(sim_cfg.readout_preset)
    preset_provenance = dict(
        cast(dict[str, object], READOUT_PRESET_PROVENANCE.get(readout_preset, {}))
    )
    mismatch_fields = _readout_preset_mismatch_fields(sim_cfg)
    observable = str(sim_cfg.readout_observable_mode)
    if observable == "magnitude":
        effective_phase_policy = "magnitude_only"
        readout_polarity = "magnitude_nonnegative"
        polarity_source = "magnitude_erased"
        reported_channel = "R"
    else:
        effective_phase_policy = str(sim_cfg.electronics_demod_phase_policy)
        readout_polarity = "sign(lockin_output_I)"
        polarity_source = "optical_and_electronics_phase_mixed"
        reported_channel = "X"

    max_lockin_frequency_hz = max(
        float(sim_cfg.pod_lockin_frequency_Hz),
        float(sim_cfg.nodi_lockin_frequency_Hz),
    )
    sampling_rate_hz = float(sim_cfg.sampling_rate_Hz)
    nyquist_hz = sampling_rate_hz / 2.0
    oversampling_ratio = (
        sampling_rate_hz / max_lockin_frequency_hz
        if max_lockin_frequency_hz > 0.0
        else float("inf")
    )
    declared_route = str(sim_cfg.readout_internal_demod_route)
    raw_readout_route = str(sim_cfg.readout_model) == "raw"
    analytic_envelope_route_used = bool(
        declared_route == "analytic_lockin_surrogate"
        and str(sim_cfg.nodi_readout_semantics) == "bandpass_envelope_surrogate"
        and observable == "magnitude"
    )
    # A measured transfer-function route is part of the schema, but no measured
    # table is wired into the runtime yet. Treat it as declared, not active.
    measured_transfer_used = False
    sampled_carrier_route_used = bool(
        not raw_readout_route
        and not analytic_envelope_route_used
        and not measured_transfer_used
    )
    carrier_nyquist_resolved = bool(
        sampled_carrier_route_used and nyquist_hz > max_lockin_frequency_hz
    )
    carrier_resolved_with_margin = bool(
        sampled_carrier_route_used
        and sampling_rate_hz >= 10.0 * max_lockin_frequency_hz
    )
    if raw_readout_route:
        sampling_validity = "raw_detector_trace"
    elif analytic_envelope_route_used:
        sampling_validity = "analytic_demod"
    elif measured_transfer_used:
        sampling_validity = "measured_transfer_function"
    elif sampled_carrier_route_used and carrier_resolved_with_margin:
        sampling_validity = "carrier_resolved"
    elif sampled_carrier_route_used:
        sampling_validity = "carrier_underresolved"
    else:
        sampling_validity = "aliased_invalid"
    sampling_hard_gate_passed = bool(
        raw_readout_route
        or analytic_envelope_route_used
        or measured_transfer_used
        or carrier_resolved_with_margin
    )

    readout_transfer = build_nodi_readout_transfer_diagnostics(
        sim_cfg,
        observable_mode=observable,
        sampling_hard_gate_passed=sampling_hard_gate_passed,
    )

    if readout_preset == "exploratory_default":
        preset_status = (
            "exploratory_default_active"
            if not mismatch_fields
            else "exploratory_default_modified"
        )
    elif readout_preset == "EV_NODI_only_design":
        preset_status = (
            "ev_design_preset_contract_active"
            if not mismatch_fields
            else "ev_design_preset_modified"
        )
    elif mismatch_fields:
        preset_status = "paper_preset_modified"
    else:
        preset_status = "paper_preset_contract_active"

    return {
        "readout_preset": readout_preset,
        "readout_preset_status": preset_status,
        "readout_preset_claim_level": preset_provenance.get(
            "claim_level",
            "unknown_readout_preset_claim",
        ),
        "readout_preset_mismatch_fields": mismatch_fields,
        "readout_preset_threshold_scope": preset_provenance.get("threshold_scope"),
        "readout_shared_threshold_profile": True,
        "readout_lane_specific_thresholds_available": False,
        "readout_preset_frequency_leakage_note": preset_provenance.get(
            "frequency_leakage_note"
        ),
        "readout_paper_time_constant_range_s": preset_provenance.get(
            "paper_time_constant_range_s"
        ),
        **readout_transfer,
        "electronics_demod_phase_policy": str(sim_cfg.electronics_demod_phase_policy),
        "effective_electronics_demod_phase_policy": effective_phase_policy,
        "readout_reference_phase_source": "configured_constant_phase",
        "readout_polarity": readout_polarity,
        "polarity_source": polarity_source,
        "arrival_phase_distribution": (
            "not_modeled_fixed_time_grid"
            if effective_phase_policy == "locked_to_event_center"
            else "not_sampled_by_current_event_generator"
        ),
        "readout_internal_sampling_rate_Hz": sampling_rate_hz,
        "readout_output_sampling_rate_Hz": sampling_rate_hz,
        "readout_max_lockin_frequency_Hz": max_lockin_frequency_hz,
        "readout_sampling_required_rate_Hz": 10.0 * max_lockin_frequency_hz,
        "readout_sampling_hard_gate_passed": sampling_hard_gate_passed,
        "readout_frequency_dependent_paper_conclusion_allowed": (
            sampling_hard_gate_passed
        ),
        "readout_sampling_claim_level": (
            "raw_detector_trace_no_carrier_sampling"
            if raw_readout_route
            else "carrier_sampling_not_required"
            if analytic_envelope_route_used or measured_transfer_used
            else (
                "sampled_carrier_frequency_resolved"
                if carrier_resolved_with_margin
                else "engineering_diagnostic"
            )
        ),
        "readout_sampling_oversampling_ratio": oversampling_ratio,
        "readout_carrier_nyquist_resolved": carrier_nyquist_resolved,
        "readout_carrier_resolved": carrier_resolved_with_margin,
        "readout_carrier_resolved_with_margin": carrier_resolved_with_margin,
        "readout_analytic_demod_used": analytic_envelope_route_used,
        "readout_internal_demod_route": declared_route,
        "readout_anti_alias_policy": str(sim_cfg.readout_anti_alias_policy),
        "readout_anti_alias_filter_before_downsample": False,
        "lockin_output_grid_matches_data_logger": (
            sampling_validity
            in {"analytic_demod", "measured_transfer_function", "raw_detector_trace"}
        ),
        "readout_sampling_validity": sampling_validity,
        "lockin_output_unit_convention": str(sim_cfg.lockin_output_unit_convention),
        "lockin_gain_chain": str(sim_cfg.lockin_gain_chain),
        "lockin_reported_channel": reported_channel,
        "lockin_reported_channel_source": "configured_readout_observable_mode",
        "lockin_measured_voltage_comparable": (
            str(sim_cfg.lockin_output_unit_convention)
            in {"rms_voltage", "peak_voltage", "peak_to_peak_voltage"}
        ),
        "readout_model_claim_level": "lockin_surrogate_not_physical_electronics",
        "pod_source_model_status": "frequency_lane_surrogate_not_thermal_pod_source",
        "nodi_source_model_status": "transient_scattering_surrogate_not_carrier_modulated_source",
    }


def build_threshold_false_alarm_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    n_background_samples: int | None = None,
    mean_threshold_robust_std: float | None = None,
    mean_pod_threshold_robust_std: float | None = None,
) -> dict[str, object]:
    """
    Export threshold-tail and false-alarm provenance for pulse extraction.

    Runtime thresholds are estimated from synthetic event background samples
    unless an empirical blank summary is configured. When a blank-style source
    is requested without a raw blank file, the runtime falls back to a
    pre/post-event edge-background surrogate rather than silently relabeling the
    original first-segment threshold.
    """
    detection_mode = str(sim_cfg.pulse_detection_mode)
    configured_tail = str(sim_cfg.threshold_tail)
    if configured_tail == "auto_by_detection_mode":
        threshold_tail = "two_sided" if detection_mode == "absolute" else "one_sided"
    else:
        threshold_tail = configured_tail

    tail_count = 2 if threshold_tail == "two_sided" else 1
    if detection_mode == "absolute":
        threshold_sign = "absolute_magnitude"
        polarity_mode = "positive_or_negative_peak"
    else:
        threshold_sign = "positive_only"
        polarity_mode = "positive_peak_only"

    sigma = float(sim_cfg.threshold_sigma)
    single_sample_far = (
        math.erfc(sigma / math.sqrt(2.0))
        if threshold_tail == "two_sided"
        else 0.5 * math.erfc(sigma / math.sqrt(2.0))
    )
    n_bg = (
        max(1, int(n_background_samples))
        if n_background_samples is not None
        else max(1, int(0.2 * int(sim_cfg.n_samples)))
    )
    iid_trace_far = 1.0 - (1.0 - single_sample_far) ** max(n_bg, 1)
    blank_calibration = _lookup_blank_false_positive_calibration(sim_cfg)
    blank_synthetic = bool(blank_calibration.get("synthetic_fixture_active", False))
    blank_manifest_invalid = _manifest_kind_mismatched(blank_calibration)
    blank_row = blank_calibration.get("row", {})
    if (
        not isinstance(blank_row, dict)
        or blank_synthetic
        or blank_manifest_invalid
    ):
        blank_row = {}
    blank_summary_selected = (
        blank_calibration.get("status") == "blank_false_positive_summary_selected"
        and not blank_synthetic
        and not blank_manifest_invalid
    )
    empirical_peak_far = _optional_calibration_float(
        blank_row,
        "empirical_peak_false_alarm_rate_per_minute",
        "peak_false_alarm_rate_per_minute",
    )
    empirical_pair_far = _optional_calibration_float(
        blank_row,
        "empirical_pair_false_alarm_rate_per_minute",
        "pair_false_alarm_rate_per_minute",
    )
    blank_autocorr_s = _optional_calibration_float(
        blank_row,
        "blank_trace_autocorrelation_time_s",
        "autocorrelation_time_s",
    )
    effective_samples = _optional_calibration_float(
        blank_row,
        "effective_independent_samples_per_trace",
        "n_eff",
    )
    lane_noise_corr = _optional_calibration_float(
        blank_row,
        "lane_noise_correlation_coefficient",
        "lane_correlation",
    )
    blank_lockin_order = _optional_calibration_float(
        blank_row,
        "lockin_filter_order",
    )
    threshold_sigma_nodi = _optional_calibration_float(
        blank_row,
        "threshold_sigma_nodi",
        default=sigma,
    )
    threshold_sigma_pod = _optional_calibration_float(
        blank_row,
        "threshold_sigma_pod",
        default=sigma,
    )

    if blank_summary_selected and str(sim_cfg.threshold_calibration_source) in {
        "blank_trace_empirical",
        "block_bootstrap",
    }:
        calibration_status = (
            "blank_trace_empirical_summary_applied"
            if str(sim_cfg.threshold_calibration_source) == "blank_trace_empirical"
            else "blank_trace_block_bootstrap_summary_applied"
        )
    elif str(sim_cfg.threshold_calibration_source) == "gaussian_iid":
        calibration_status = "gaussian_iid_surrogate_not_empirical_blank"
    elif str(sim_cfg.threshold_calibration_source) in {
        "blank_trace_empirical",
        "block_bootstrap",
    }:
        calibration_status = "blank_source_unavailable_using_event_edge_background_surrogate"
    else:
        calibration_status = "configured_source_unavailable_without_blank_trace"

    colored_model = str(sim_cfg.colored_noise_false_alarm_model)
    colored_components: tuple[str, ...] = ()
    colored_threshold_bias: float | None = None
    colored_threshold_bias_status = "not_evaluated"
    if blank_summary_selected and colored_model in {"empirical_blank", "block_bootstrap"}:
        colored_status = (
            "empirical_blank_colored_noise_summary_applied"
            if colored_model == "empirical_blank"
            else "block_bootstrap_colored_noise_summary_applied"
        )
    elif colored_model == "not_applied":
        colored_status = "not_evaluated_iid_surrogate_only"
    elif colored_model == "iid_gaussian_surrogate":
        colored_status = "iid_gaussian_ar1_1overf_speckle_surrogate_active"
        colored_components = (
            "gaussian_iid",
            "ar1_correlation_proxy",
            "one_over_f_low_frequency_proxy",
            "slow_multiplicative_speckle_proxy",
        )
        surrogate_effective_samples = max(1.0, 0.35 * float(n_bg))
        if effective_samples is None:
            effective_samples = surrogate_effective_samples
        if blank_autocorr_s is None and float(sim_cfg.sampling_rate_Hz) > 0.0:
            blank_autocorr_s = max(
                float(sim_cfg.lockin_time_constant_s),
                1.0 / float(sim_cfg.sampling_rate_Hz),
            )
        iid_to_colored_inflation = float(n_bg) / surrogate_effective_samples
        colored_threshold_bias = float(
            min(1.0, iid_trace_far * max(0.0, iid_to_colored_inflation - 1.0))
        )
        colored_threshold_bias_status = "surrogate_bias_estimate_not_empirical_blank"
    else:
        colored_status = "configured_but_unavailable_without_empirical_blank_trace"

    raw_blank_boundary = build_raw_blank_trace_bootstrap_boundary(
        raw_blank_trace_path=getattr(sim_cfg, "raw_blank_trace_path", None),
    )

    return {
        "threshold_sigma": sigma,
        "threshold_sigma_nodi": threshold_sigma_nodi,
        "threshold_sigma_pod": threshold_sigma_pod,
        "threshold_lane_specific_model": (
            "blank_summary_lane_specific_thresholds"
            if blank_summary_selected
            and (
                not np.isclose(float(threshold_sigma_nodi or sigma), sigma)
                or not np.isclose(float(threshold_sigma_pod or sigma), sigma)
            )
            else "shared_threshold"
        ),
        "threshold_tail": threshold_tail,
        "threshold_tail_configured": configured_tail,
        "threshold_tail_status": (
            "matches_detection_mode"
            if (
                (detection_mode == "absolute" and threshold_tail == "two_sided")
                or (detection_mode == "positive" and threshold_tail == "one_sided")
            )
            else "review_tail_vs_detection_mode"
        ),
        "threshold_false_alarm_tail_count": tail_count,
        "threshold_sign": threshold_sign,
        "threshold_polarity_mode": polarity_mode,
        "target_false_alarm_rate": float(sim_cfg.evaluation_false_alarm_rate),
        "fixed_false_alarm_rate_used": float(sim_cfg.evaluation_false_alarm_rate),
        "threshold_from_blank_trace": blank_summary_selected,
        "threshold_from_event_background_segment": not blank_summary_selected,
        "threshold_background_source": (
            "empirical_blank_trace_summary"
            if blank_summary_selected
            else (
                "synthetic_event_edge_background_surrogate"
                if str(sim_cfg.threshold_calibration_source)
                in {"blank_trace_empirical", "block_bootstrap"}
                else "synthetic_event_background_segment"
            )
        ),
        "threshold_background_segment_fraction": 0.2,
        "threshold_background_segment_samples": n_bg,
        "threshold_calibration_source": str(sim_cfg.threshold_calibration_source),
        "threshold_calibration_status": calibration_status,
        "blank_false_positive_calibration_status": blank_calibration.get("status"),
        "blank_false_positive_calibration_source": blank_calibration.get("source"),
        "blank_false_positive_calibration_id": blank_calibration.get(
            "calibration_id"
        ),
        "blank_false_positive_calibration_row_id": blank_calibration.get("row_id"),
        "blank_false_positive_calibration_row_index": blank_calibration.get(
            "row_index"
        ),
        "blank_false_positive_calibration_row_count": blank_calibration.get(
            "row_count"
        ),
        "blank_false_positive_calibration_data_role": blank_calibration.get(
            "calibration_data_role"
        ),
        "blank_false_positive_synthetic_fixture_active": blank_synthetic,
        "blank_false_positive_table_validation_status": blank_calibration.get(
            "table_validation_status"
        ),
        "blank_false_positive_manifest_status": blank_calibration.get(
            "manifest_status"
        ),
        "blank_false_positive_manifest_validation_status": blank_calibration.get(
            "manifest_validation_status"
        ),
        "blank_false_positive_manifest_path": blank_calibration.get("manifest_path"),
        "absolute_threshold_sigma_equivalent": (
            sigma if threshold_tail == "two_sided" else None
        ),
        "positive_threshold_sigma_equivalent": (
            sigma if threshold_tail == "one_sided" else None
        ),
        "gaussian_iid_single_sample_false_alarm_probability": float(
            single_sample_far
        ),
        "gaussian_iid_background_segment_false_alarm_probability": float(
            iid_trace_far
        ),
        "mean_threshold_robust_std": mean_threshold_robust_std,
        "mean_pod_threshold_robust_std": mean_pod_threshold_robust_std,
        "blank_trace_autocorrelation_time_s": blank_autocorr_s,
        "effective_independent_samples_per_trace": effective_samples,
        "lockin_filter_order": (
            int(blank_lockin_order)
            if blank_lockin_order is not None
            else 1 if str(sim_cfg.readout_model) == "lockin_surrogate" else None
        ),
        "empirical_peak_false_alarm_rate_per_minute": empirical_peak_far,
        "empirical_pair_false_alarm_rate_per_minute": empirical_pair_far,
        "lane_noise_correlation_coefficient": lane_noise_corr,
        "colored_noise_false_alarm_model": colored_model,
        "colored_noise_false_alarm_status": colored_status,
        "colored_noise_surrogate_components": colored_components,
        "colored_noise_threshold_bias": colored_threshold_bias,
        "colored_noise_threshold_bias_status": colored_threshold_bias_status,
        "paired_false_alarm_status": (
            "empirical_pair_summary_available"
            if empirical_pair_far is not None and lane_noise_corr is not None
            else "not_evaluated_no_joint_blank_trace"
        ),
        **raw_blank_boundary,
    }


def build_particle_model_diagnostics(
    particle: Particle,
    sim_cfg: SimulationConfig,
    *,
    intrinsic: dict | None = None,
) -> dict[str, object]:
    """
    Export particle-family, EV/sEV claim, and material-uncertainty provenance.

    The current particle models remain deterministic nominal cases. Ensemble
    uncertainty is represented only when the precompute profile explicitly
    enumerates separate particles / presets.
    """
    particle_name = str(particle.name)
    material_key = getattr(particle, "material_key", None)
    structure_key = getattr(particle, "structure_key", None)
    structure_params = particle.structure_params or {}
    structured_spec = (
        intrinsic.get("structured_particle_spec")
        if intrinsic is not None and "structured_particle_spec" in intrinsic
        else None
    )
    is_ev_like = bool(
        structure_key == "exosome_biomimetic"
        or particle_name.startswith("exosome_")
        or material_key == "exosome_uniform"
    )
    if structure_key == "exosome_biomimetic":
        particle_family = "EV_sEV"
        ev_label = "exosome_like"
        particle_optical_model = "core_shell_EV_sEV_surrogate"
        structured_status = "biomimetic_core_shell_nominal_preset"
        material_dataset = "literature_bounded_EV_core_shell_preset"
        preset_name = (
            str(structured_spec.get("preset_name"))
            if isinstance(structured_spec, dict)
            else str((particle.structure_params or {}).get("preset_name", "unknown"))
        )
        core_ri = (
            float(np.real(structured_spec["core_n_complex"]))
            if isinstance(structured_spec, dict) and "core_n_complex" in structured_spec
            else None
        )
        shell_ri = (
            float(np.real(structured_spec["shell_n_complex"]))
            if isinstance(structured_spec, dict) and "shell_n_complex" in structured_spec
            else None
        )
        shell_thickness_m = (
            float(structured_spec["shell_thickness_m"])
            if isinstance(structured_spec, dict) and "shell_thickness_m" in structured_spec
            else None
        )
    elif is_ev_like:
        particle_family = "EV_sEV"
        ev_label = "exosome_like"
        particle_optical_model = "homogeneous_EV_sEV_surrogate"
        structured_status = "legacy_uniform_nominal_sphere"
        material_dataset = "fixed_uniform_EV_refractive_index"
        preset_name = None
        core_ri = float(np.real(particle.n_complex))
        shell_ri = None
        shell_thickness_m = None
    elif str(material_key or "").startswith("gold") or particle_name.startswith("gold_"):
        particle_family = "gold"
        ev_label = None
        particle_optical_model = "homogeneous_mie_sphere"
        structured_status = "not_structured"
        material_dataset = (
            "materials_db:gold"
            if bool(getattr(particle, "use_material_model", False))
            else "fixed_gold_index"
        )
        preset_name = None
        core_ri = None
        shell_ri = None
        shell_thickness_m = None
    else:
        particle_family = str(material_key or "unknown")
        ev_label = None
        particle_optical_model = "homogeneous_mie_sphere"
        structured_status = "not_structured"
        material_dataset = (
            f"materials_db:{material_key}"
            if bool(getattr(particle, "use_material_model", False))
            else "fixed_complex_index"
        )
        preset_name = None
        core_ri = None
        shell_ri = None
        shell_thickness_m = None

    uncertainty_mode = str(sim_cfg.particle_uncertainty_propagation_mode)
    uncertainty_budget_model = str(sim_cfg.particle_uncertainty_budget_model)
    if uncertainty_mode == "none":
        uncertainty_status = "nominal_only_uncertainty_not_propagated"
        output_confidence_status = "no_particle_uncertainty_CI"
    else:
        uncertainty_status = "configured_uncertainty_route_requires_explicit_ensemble_outputs"
        output_confidence_status = "uncertainty_route_configured_no_CI_in_current_outputs"

    if is_ev_like:
        ev_claim_level = "optical_EV_like_particle"
        biogenesis_claim = "none"
        anisotropic_shell_model = "unmodeled"
        shape_uncertainty_status = "spherical_surrogate_shape_uncertainty_unresolved"
        orientation_average_status = "not_applicable_spherical_surrogate"
        sample_prep_status = "not_specified"
        isolation_method = None
        aggregation_status = "unmodeled"
        uncertainty_inputs = [
            "size_distribution",
            "core_RI",
            "shell_RI",
            "shell_thickness",
            "shape",
            "orientation",
            "corona_or_coisolate",
            "isolation_batch",
        ]
    else:
        ev_claim_level = "not_applicable"
        biogenesis_claim = "not_applicable"
        anisotropic_shell_model = "not_applicable"
        shape_uncertainty_status = "homogeneous_sphere_nominal"
        orientation_average_status = "not_applicable_spherical_particle"
        sample_prep_status = "not_applicable"
        isolation_method = None
        aggregation_status = "not_modeled"
        uncertainty_inputs = ["size", "material_RI"]

    use_material_model = bool(getattr(particle, "use_material_model", False))
    material_type = "fixed_complex_index"
    material_source = "particle_fixed_complex_index"
    if structure_key == "exosome_biomimetic":
        material_model_mode = "structured_particle_nominal_preset"
        material_wavelength_status = (
            "structured_preset_nominal_no_wavelength_uncertainty"
        )
        material_source = str(preset_name or "structured_particle_preset")
        material_type = "structured_preset"
    elif use_material_model and material_key is not None:
        from .materials import MATERIAL_DB

        entry = MATERIAL_DB.get(str(material_key), {})
        material_type = str(entry.get("type", "unknown"))
        material_source = str(entry.get("source", "unknown_material_source"))
        if material_type == "tabulated":
            material_model_mode = "materials_db_tabulated_interpolation"
            material_wavelength_status = "materials_db_interpolation_range_checked"
        elif material_type == "constant":
            material_model_mode = "materials_db_constant_visible_approximation"
            material_wavelength_status = (
                "constant_visible_approximation_no_dispersion_uncertainty"
            )
        elif material_type in {"cauchy", "sellmeier"}:
            material_model_mode = "materials_db_visible_dispersion_nominal"
            material_wavelength_status = (
                "materials_db_visible_dispersion_range_checked_no_uncertainty"
            )
        else:
            material_model_mode = "materials_db_unknown_type"
            material_wavelength_status = "unknown_material_wavelength_validity"
    else:
        material_model_mode = "fixed_complex_index"
        material_wavelength_status = "fixed_index_no_wavelength_validity_check"

    from .materials import material_db_coverage_diagnostics

    material_coverage = material_db_coverage_diagnostics()

    return {
        "particle_family": particle_family,
        "particle_family_status": "explicit_particle_family_diagnostic",
        "particle_optical_model": particle_optical_model,
        "structured_particle_model_status": structured_status,
        "structured_particle_key": structure_key,
        "structured_particle_preset_name": preset_name,
        "EV_label": ev_label,
        "EV_claim_level": ev_claim_level,
        "exosome_biogenesis_claim": biogenesis_claim,
        "biogenesis_claim": biogenesis_claim,
        "material_dataset": material_dataset,
        "particle_material_model_mode": material_model_mode,
        "particle_material_dataset_key": material_key,
        "particle_material_dataset_source": material_source,
        "particle_material_dataset_type": material_type,
        "particle_material_wavelength_status": material_wavelength_status,
        "particle_material_temperature_correction_status": (
            "not_applied_room_temperature_nominal"
        ),
        "particle_material_uncertainty_status": (
            "not_quantified_material_dataset_nominal"
        ),
        "metal_size_damping": "off",
        "metal_size_damping_status": "not_applied",
        "ligand_shell": "none",
        "ligand_shell_status": "not_modeled",
        "medium_dispersion": "materials_db_or_constant_runtime",
        "medium_dispersion_status": str(material_coverage["medium_wall_dispersion_status"]),
        "wall_dispersion": "materials_db_or_constant_runtime",
        "wall_dispersion_status": str(material_coverage["medium_wall_dispersion_status"]),
        **material_coverage,
        "shape_model": "sphere",
        "anisotropic_shell_model": anisotropic_shell_model,
        "orientation_average_status": orientation_average_status,
        "shape_uncertainty_status": shape_uncertainty_status,
        "EV_sample_preparation_status": sample_prep_status,
        "EV_isolation_method": isolation_method,
        "EV_aggregation_or_coisolate_status": aggregation_status,
        "EV_ensemble_mode": str(sim_cfg.EV_ensemble_mode),
        "EV_ensemble_name": structure_params.get("EV_ensemble_name"),
        "EV_ensemble_member_index": structure_params.get("EV_ensemble_member_index"),
        "EV_ensemble_member_count": structure_params.get("EV_ensemble_member_count"),
        "EV_ensemble_member_preset": structure_params.get("EV_ensemble_member_preset"),
        "EV_ensemble_status": (
            "nominal_single_preset_no_hidden_sampling"
            if str(sim_cfg.EV_ensemble_mode) == "nominal_single_preset"
            else "explicit_cases_required_for_reproducible_ensemble"
        ),
        "EV_core_RI_nominal": core_ri,
        "EV_shell_RI_nominal": shell_ri,
        "EV_shell_thickness_m": shell_thickness_m,
        "EV_uncertainty_inputs": list(uncertainty_inputs),
        "size_distribution_uncertainty": "not_propagated",
        "core_RI_uncertainty": "not_propagated" if is_ev_like else None,
        "shell_RI_uncertainty": "not_propagated" if is_ev_like else None,
        "shell_thickness_uncertainty": "not_propagated" if is_ev_like else None,
        "anisotropy_uncertainty": "unresolved" if is_ev_like else None,
        "shape_uncertainty": "unresolved" if is_ev_like else "sphere_assumed",
        "corona_coisolate_uncertainty": "unresolved" if is_ev_like else None,
        "isolation_batch_uncertainty": "unresolved" if is_ev_like else None,
        "particle_uncertainty_budget_model": uncertainty_budget_model,
        "particle_uncertainty_budget_status": uncertainty_status,
        "uncertainty_propagation_mode": uncertainty_mode,
        "uncertainty_inputs": list(uncertainty_inputs),
        "uncertainty_outputs": "not_propagated_to_peak_or_detection_confidence",
        "uncertainty_output_confidence_status": output_confidence_status,
        "peak_height_CI_available": False,
        "detection_rate_CI_available": False,
        "count_rate_CI_available": False,
        "classification_probability_CI_available": False,
        **build_uncertainty_propagation_boundary(sim_cfg, particle=particle),
    }


def build_collection_operator(
    theta_grid_rad: np.ndarray,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> dict:
    """
    Build the shared angular collection operator used by both E_sca and E_ref.

    Returns normalized theta/phi weights plus an audit-friendly signature so the
    same detection operator can be verified across runtime collection and
    baseline/reference normalization.
    """
    surrogate_theta_center = resolve_collection_theta_rad(
        channel,
        optical,
        sim_cfg,
        medium_refractive_index=medium_refractive_index,
    )
    surrogate_sigma_rad = _resolve_collection_sigma_rad(
        channel,
        optical,
        sim_cfg,
        medium_refractive_index=medium_refractive_index,
    )
    calibration = _lookup_collection_operator_calibration(
        channel,
        optical,
        sim_cfg,
        medium_refractive_index,
    )
    calibration_synthetic = bool(calibration.get("synthetic_fixture_active", False))
    calibration_manifest_invalid = _manifest_kind_mismatched(calibration)
    calibration_row = calibration.get("row", {})
    if (
        not isinstance(calibration_row, dict)
        or calibration_synthetic
        or calibration_manifest_invalid
    ):
        calibration_row = {}

    theta_center = _optional_calibration_float(
        calibration_row,
        "theta_center_rad",
        "theta_rad",
        default=surrogate_theta_center,
    )
    sigma_rad = _optional_calibration_float(
        calibration_row,
        "theta_sigma_rad",
        "sigma_effective_rad",
        "collection_sigma_rad",
        default=surrogate_sigma_rad,
    )
    phi_sigma_rad = _optional_calibration_float(
        calibration_row,
        "phi_sigma_rad",
        "collection_phi_sigma_rad",
        default=float(sim_cfg.collection_phi_sigma_rad),
    )
    slit_phi_limit_rad = _optional_calibration_float(
        calibration_row,
        "slit_phi_limit_rad",
        "slit_phi_rad",
        default=float(sim_cfg.slit_phi_limit_rad),
    )
    calibrated_throughput = _optional_calibration_float(
        calibration_row,
        "throughput_scale",
        "absolute_throughput",
        "optical_throughput",
    )
    theta_center = float(theta_center if theta_center is not None else surrogate_theta_center)
    sigma_rad = float(max(sigma_rad if sigma_rad is not None else surrogate_sigma_rad, 1e-9))
    phi_sigma_rad = float(
        max(phi_sigma_rad if phi_sigma_rad is not None else sim_cfg.collection_phi_sigma_rad, 1e-9)
    )
    slit_phi_limit_rad = float(
        np.clip(
            slit_phi_limit_rad
            if slit_phi_limit_rad is not None
            else sim_cfg.slit_phi_limit_rad,
            1e-9,
            math.pi / 2,
        )
    )
    calibration_selected = bool(
        calibration.get("configured")
        and calibration.get("status") == "calibrated_operator_table_selected"
        and not calibration_synthetic
    )

    if sim_cfg.collection_integration_mode == "single_angle":
        theta_weights = np.zeros_like(theta_grid_rad, dtype=float)
        theta_weights[int(np.argmin(np.abs(theta_grid_rad - theta_center)))] = 1.0
        phi_grid = np.array([0.0], dtype=float)
        phi_weights = np.array([1.0], dtype=float)
        theta_effective = float(theta_center)
        throughput_scale = 1.0
    elif sim_cfg.collection_integration_mode == "gaussian_weighted":
        theta_weights = _collection_kernel(theta_grid_rad, theta_center, sigma_rad)
        phi_grid = np.array([0.0], dtype=float)
        phi_weights = np.array([1.0], dtype=float)
        theta_effective = float(np.trapezoid(theta_weights * theta_grid_rad, theta_grid_rad))
        throughput_scale = 1.0
    elif sim_cfg.collection_integration_mode == "pupil_slit_surrogate":
        theta_base = _collection_kernel(theta_grid_rad, theta_center, sigma_rad)
        theta_weights = (
            theta_base
            * _pupil_theta_factor(theta_grid_rad)
            * _theta_pinhole_factor(theta_grid_rad, theta_center, sigma_rad)
        )
        theta_norm = np.trapezoid(theta_weights, theta_grid_rad)
        if theta_norm > 0:
            theta_weights = theta_weights / theta_norm
        phi_grid = np.linspace(-slit_phi_limit_rad, slit_phi_limit_rad, 31)
        raw_phi_sigma = float(max(phi_sigma_rad, 1e-6))
        raw_slit_limit = float(max(slit_phi_limit_rad, 1e-6))
        raw_phi = (
            (np.abs(phi_grid) <= raw_slit_limit).astype(float)
            * np.exp(-0.5 * (phi_grid / raw_phi_sigma) ** 2)
            * np.exp(-0.5 * (phi_grid / max(0.6 * raw_slit_limit, 1e-6)) ** 2)
        )
        phi_norm = np.trapezoid(raw_phi, phi_grid)
        if phi_norm > 0:
            phi_weights = raw_phi / phi_norm
        else:
            phi_weights = np.zeros_like(phi_grid, dtype=float)
            phi_weights[len(phi_weights) // 2] = 1.0
        phi_throughput = float(np.trapezoid(raw_phi, phi_grid))
        theta_throughput = float(theta_norm)
        throughput_scale = max(theta_throughput * phi_throughput, 1e-12)
        theta_effective = float(np.trapezoid(theta_weights * theta_grid_rad, theta_grid_rad))
    else:
        raise ValueError(
            "collection_integration_mode must be 'single_angle', "
            "'gaussian_weighted', or 'pupil_slit_surrogate', got "
            f"{sim_cfg.collection_integration_mode}"
        )

    surrogate_throughput_scale = float(throughput_scale)
    absolute_throughput_calibrated = (
        calibrated_throughput is not None and float(calibrated_throughput) > 0.0
    )
    calibrated_throughput_float = (
        float(calibrated_throughput)
        if calibrated_throughput is not None
        else None
    )
    if absolute_throughput_calibrated:
        throughput_scale = float(cast(float, calibrated_throughput_float))

    if calibration_selected:
        operator_route = "calibrated_operator_table"
    else:
        operator_route = str(sim_cfg.collection_integration_mode)
    if operator_route == "calibrated_operator_table" and absolute_throughput_calibrated:
        operator_normalization = "absolute_throughput_calibrated_operator_table"
        absolute_throughput_route = "calibrated_operator_table"
    elif operator_route == "calibrated_operator_table":
        operator_normalization = "unit_normalized_calibrated_operator_geometry"
        absolute_throughput_route = str(sim_cfg.absolute_throughput_route)
    elif operator_route in {"gaussian_weighted", "pupil_slit_surrogate"}:
        operator_normalization = "unit_normalized_weights_with_throughput_surrogate"
        absolute_throughput_route = str(sim_cfg.absolute_throughput_route)
    else:
        operator_normalization = "single_angle_sample"
        absolute_throughput_route = str(sim_cfg.absolute_throughput_route)

    operator_signature = (
        f"angle={sim_cfg.collection_angle_model}"
        f"|integration={sim_cfg.collection_integration_mode}"
        f"|operator_route={operator_route}"
        f"|operator_calibration_status={calibration.get('status')}"
        f"|operator_coverage={calibration.get('coverage_status')}"
        f"|projection={sim_cfg.scattering_projection_mode}"
        f"|measure={sim_cfg.field_coordinate_measure}"
        f"|jacobian={bool(sim_cfg.bfp_to_angle_jacobian_applied)}"
        f"|theta_center={theta_center:.9e}"
        f"|theta_sigma={sigma_rad:.9e}"
        f"|phi_sigma={phi_sigma_rad:.9e}"
        f"|slit_phi={slit_phi_limit_rad:.9e}"
        f"|throughput={throughput_scale:.9e}"
    )
    field_measure_diagnostics = build_field_measure_diagnostics(sim_cfg)
    bfp_roi_contract = build_bfp_roi_mask_contract(
        bfp_roi_mask_path=getattr(sim_cfg, "bfp_roi_mask_path", None),
        bfp_to_angle_jacobian_applied=bool(sim_cfg.bfp_to_angle_jacobian_applied),
    )
    return {
        "theta_center_rad": float(theta_center),
        "theta_effective_rad": float(theta_effective),
        "sigma_effective_rad": float(sigma_rad),
        "theta_grid_rad": np.asarray(theta_grid_rad, dtype=float).copy(),
        "theta_weights": theta_weights,
        "phi_grid_rad": phi_grid,
        "phi_weights": phi_weights,
        "throughput_scale": float(throughput_scale),
        "operator_route": operator_route,
        "operator_normalization": operator_normalization,
        "operator_signature": operator_signature,
        "surrogate_theta_center_rad": float(surrogate_theta_center),
        "surrogate_sigma_effective_rad": float(surrogate_sigma_rad),
        "surrogate_phi_sigma_rad": float(sim_cfg.collection_phi_sigma_rad),
        "surrogate_slit_phi_limit_rad": float(sim_cfg.slit_phi_limit_rad),
        "surrogate_throughput_scale": surrogate_throughput_scale,
        "collection_operator_calibration_status": str(calibration.get("status")),
        "collection_operator_coverage_status": str(calibration.get("coverage_status")),
        "collection_operator_calibration_source": calibration.get("source"),
        "collection_operator_id": calibration.get("operator_id"),
        "collection_operator_calibration_row_id": calibration.get("row_id"),
        "collection_operator_calibration_row_index": calibration.get("row_index"),
        "collection_operator_calibration_row_count": calibration.get("row_count"),
        "collection_operator_calibrated_geometry": calibration_selected,
        "collection_operator_max_relative_geometry_distance": calibration.get(
            "max_relative_geometry_distance"
        ),
        "collection_operator_geometry_distance_report": (
            f"max_relative_geometry_distance={calibration.get('max_relative_geometry_distance')}"
            if calibration.get("max_relative_geometry_distance") is not None
            else None
        ),
        "collection_operator_calibration_data_role": calibration.get(
            "calibration_data_role"
        ),
        "collection_operator_synthetic_fixture_active": calibration_synthetic,
        "collection_operator_table_validation_status": calibration.get(
            "table_validation_status"
        ),
        "collection_operator_manifest_status": calibration.get("manifest_status"),
        "collection_operator_manifest_validation_status": calibration.get(
            "manifest_validation_status"
        ),
        "collection_operator_manifest_path": calibration.get("manifest_path"),
        "absolute_throughput_route": absolute_throughput_route,
        "absolute_throughput_calibrated": absolute_throughput_calibrated,
        **field_measure_diagnostics,
        **bfp_roi_contract,
    }


def collapse_angular_field_with_operator(
    theta_grid_rad: np.ndarray,
    field_theta_or_2d: np.ndarray,
    operator: dict,
    sim_cfg: SimulationConfig,
    *,
    phi_grid_rad: np.ndarray | None = None,
) -> complex:
    """
    Collapse a theta-only or theta/phi complex angular field with one operator.

    This helper is used so that E_sca and E_ref can share the same detection
    operator semantics instead of only sharing partial weights.
    """
    field = np.asarray(field_theta_or_2d)
    theta_center = float(operator["theta_center_rad"])
    theta_weights = np.asarray(operator["theta_weights"], dtype=float)
    throughput = float(operator.get("throughput_scale", 1.0))

    if sim_cfg.collection_integration_mode == "single_angle":
        if field.ndim == 1:
            return complex(
                interpolate_complex_at_theta(theta_grid_rad, field, theta_center) * throughput
            )
        if phi_grid_rad is None:
            raise ValueError("phi_grid_rad is required when collapsing a 2D field")
        theta_idx = int(np.argmin(np.abs(theta_grid_rad - theta_center)))
        phi_vals = np.asarray(phi_grid_rad, dtype=float)
        phi_weights = np.interp(
            phi_vals,
            operator["phi_grid_rad"],
            operator["phi_weights"],
            left=0.0,
            right=0.0,
        )
        theta_slice = field[theta_idx]
        return complex(np.trapezoid(theta_slice * phi_weights, phi_vals) * throughput)

    if sim_cfg.collection_integration_mode == "gaussian_weighted":
        if field.ndim == 1:
            return complex(np.trapezoid(theta_weights * field, theta_grid_rad) * throughput)
        if phi_grid_rad is None:
            raise ValueError("phi_grid_rad is required when collapsing a 2D field")
        phi_vals = np.asarray(phi_grid_rad, dtype=float)
        phi_weights = np.interp(
            phi_vals,
            operator["phi_grid_rad"],
            operator["phi_weights"],
            left=0.0,
            right=0.0,
        )
        detected_theta = np.trapezoid(field * phi_weights[None, :], phi_vals, axis=1)
        return complex(np.trapezoid(theta_weights * detected_theta, theta_grid_rad) * throughput)

    if sim_cfg.collection_integration_mode == "pupil_slit_surrogate":
        if phi_grid_rad is None:
            raise ValueError("phi_grid_rad is required for pupil_slit_surrogate")
        phi_vals = np.asarray(phi_grid_rad, dtype=float)
        phi_weights = np.interp(
            phi_vals,
            operator["phi_grid_rad"],
            operator["phi_weights"],
            left=0.0,
            right=0.0,
        )
        projection_2d = _phi_vector_projection(
            theta_grid_rad,
            phi_vals,
            sim_cfg.scattering_projection_mode,
        )
        # Phenomenological pupil-slit phase shear. This dimensionless factor is
        # an auditable surrogate assumption, not a first-principles derivation
        # of BFP propagation phase.
        theta_phase = np.exp(
            1j * (theta_grid_rad[:, None] - theta_center) * np.sin(phi_vals[None, :])
        )
        if field.ndim == 1:
            field_2d = field[:, None] * projection_2d * theta_phase
        else:
            field_2d = field * projection_2d * theta_phase
        detected_theta = np.trapezoid(field_2d * phi_weights[None, :], phi_vals, axis=1)
        return complex(np.trapezoid(theta_weights * detected_theta, theta_grid_rad) * throughput)

    raise ValueError(
        "collection_integration_mode must be 'single_angle', "
        "'gaussian_weighted', or 'pupil_slit_surrogate', got "
        f"{sim_cfg.collection_integration_mode}"
    )


def _resample_complex_theta_field(
    source_theta_grid_rad: np.ndarray,
    field_theta_or_2d: np.ndarray,
    target_theta_grid_rad: np.ndarray,
) -> np.ndarray:
    """Interpolate a 1D or 2D complex theta field onto a target theta grid."""
    source_theta = np.asarray(source_theta_grid_rad, dtype=float)
    target_theta = np.asarray(target_theta_grid_rad, dtype=float)
    field = np.asarray(field_theta_or_2d, dtype=complex)
    if field.ndim == 1:
        real = np.interp(target_theta, source_theta, np.real(field))
        imag = np.interp(target_theta, source_theta, np.imag(field))
        return real + 1j * imag

    cols = []
    for col_idx in range(field.shape[1]):
        real = np.interp(target_theta, source_theta, np.real(field[:, col_idx]))
        imag = np.interp(target_theta, source_theta, np.imag(field[:, col_idx]))
        cols.append(real + 1j * imag)
    return np.stack(cols, axis=1)




def _collapse_and_joint_overlap_with_operator(
    theta_grid_rad: np.ndarray,
    reference_field_theta_or_2d: np.ndarray,
    scattering_field_theta_or_2d: np.ndarray,
    operator: dict,
    sim_cfg: SimulationConfig,
    *,
    phi_grid_rad: np.ndarray | None = None,
) -> tuple[complex, complex, complex]:
    """Compute collapsed reference/scattering fields and their joint overlap together."""
    ref_field = np.asarray(reference_field_theta_or_2d, dtype=complex)
    sca_field = np.asarray(scattering_field_theta_or_2d, dtype=complex)
    theta_center = float(operator["theta_center_rad"])
    theta_weights = np.asarray(operator["theta_weights"], dtype=float)
    throughput = float(operator.get("throughput_scale", 1.0))

    if sim_cfg.collection_integration_mode == "single_angle":
        ref_collapsed = collapse_angular_field_with_operator(
            theta_grid_rad,
            ref_field,
            operator,
            sim_cfg,
            phi_grid_rad=phi_grid_rad,
        )
        sca_collapsed = collapse_angular_field_with_operator(
            theta_grid_rad,
            sca_field,
            operator,
            sim_cfg,
            phi_grid_rad=phi_grid_rad,
        )
        joint_overlap = complex(ref_collapsed * np.conj(sca_collapsed))
        return complex(ref_collapsed), complex(sca_collapsed), joint_overlap

    if sim_cfg.collection_integration_mode == "gaussian_weighted":
        if ref_field.ndim == 1 and sca_field.ndim == 1:
            ref_collapsed = complex(
                np.trapezoid(theta_weights * ref_field, theta_grid_rad) * throughput
            )
            sca_collapsed = complex(
                np.trapezoid(theta_weights * sca_field, theta_grid_rad) * throughput
            )
            joint_overlap = complex(
                np.trapezoid(theta_weights * ref_field * np.conj(sca_field), theta_grid_rad)
                * throughput
            )
            return ref_collapsed, sca_collapsed, joint_overlap

        if phi_grid_rad is None:
            raise ValueError("phi_grid_rad is required when joint-overlap uses a 2D field")
        phi_vals = np.asarray(phi_grid_rad, dtype=float)
        phi_weights = np.interp(
            phi_vals,
            operator["phi_grid_rad"],
            operator["phi_weights"],
            left=0.0,
            right=0.0,
        )
        ref_2d = ref_field if ref_field.ndim == 2 else np.repeat(ref_field[:, None], len(phi_vals), axis=1)
        sca_2d = sca_field if sca_field.ndim == 2 else np.repeat(sca_field[:, None], len(phi_vals), axis=1)
        ref_theta = np.trapezoid(ref_2d * phi_weights[None, :], phi_vals, axis=1)
        sca_theta = np.trapezoid(sca_2d * phi_weights[None, :], phi_vals, axis=1)
        joint_theta = np.trapezoid(
            ref_2d * np.conj(sca_2d) * phi_weights[None, :],
            phi_vals,
            axis=1,
        )
        ref_collapsed = complex(np.trapezoid(theta_weights * ref_theta, theta_grid_rad) * throughput)
        sca_collapsed = complex(np.trapezoid(theta_weights * sca_theta, theta_grid_rad) * throughput)
        joint_overlap = complex(np.trapezoid(theta_weights * joint_theta, theta_grid_rad) * throughput)
        return ref_collapsed, sca_collapsed, joint_overlap

    if sim_cfg.collection_integration_mode == "pupil_slit_surrogate":
        if phi_grid_rad is None:
            raise ValueError("phi_grid_rad is required for pupil_slit_surrogate joint overlap")
        phi_vals = np.asarray(phi_grid_rad, dtype=float)
        phi_weights = np.interp(
            phi_vals,
            operator["phi_grid_rad"],
            operator["phi_weights"],
            left=0.0,
            right=0.0,
        )
        projection_2d = _phi_vector_projection(
            theta_grid_rad,
            phi_vals,
            sim_cfg.scattering_projection_mode,
        )
        # Phenomenological pupil-slit phase shear. This dimensionless factor is
        # an auditable surrogate assumption, not a first-principles derivation
        # of BFP propagation phase.
        theta_phase = np.exp(
            1j * (theta_grid_rad[:, None] - theta_center) * np.sin(phi_vals[None, :])
        )
        ref_2d = ref_field if ref_field.ndim == 2 else ref_field[:, None]
        sca_2d = sca_field if sca_field.ndim == 2 else sca_field[:, None]
        ref_projected = ref_2d * projection_2d * theta_phase
        sca_projected = sca_2d * projection_2d * theta_phase
        ref_theta = np.trapezoid(ref_projected * phi_weights[None, :], phi_vals, axis=1)
        sca_theta = np.trapezoid(sca_projected * phi_weights[None, :], phi_vals, axis=1)
        joint_theta = np.trapezoid(
            ref_projected * np.conj(sca_projected) * phi_weights[None, :],
            phi_vals,
            axis=1,
        )
        ref_collapsed = complex(np.trapezoid(theta_weights * ref_theta, theta_grid_rad) * throughput)
        sca_collapsed = complex(np.trapezoid(theta_weights * sca_theta, theta_grid_rad) * throughput)
        joint_overlap = complex(np.trapezoid(theta_weights * joint_theta, theta_grid_rad) * throughput)
        return ref_collapsed, sca_collapsed, joint_overlap

    raise ValueError(
        "collection_integration_mode must be 'single_angle', "
        "'gaussian_weighted', or 'pupil_slit_surrogate', got "
        f"{sim_cfg.collection_integration_mode}"
    )


def build_interference_overlap_diagnostics(
    theta_grid_rad: np.ndarray,
    reference_field_theta_or_2d: np.ndarray,
    scattering_field_theta_or_2d: np.ndarray,
    operator: dict,
    sim_cfg: SimulationConfig,
    *,
    phi_grid_rad: np.ndarray | None = None,
    scattering_theta_grid_rad: np.ndarray | None = None,
) -> dict[str, object]:
    """Compare scalar collapsed interference against the joint angular-overlap form."""
    evaluation_theta_grid = np.asarray(
        operator.get("theta_grid_rad", theta_grid_rad),
        dtype=float,
    )
    reference_field_eval = _resample_complex_theta_field(
        theta_grid_rad,
        reference_field_theta_or_2d,
        evaluation_theta_grid,
    )
    if scattering_theta_grid_rad is None:
        scattering_field_eval = _resample_complex_theta_field(
            theta_grid_rad,
            scattering_field_theta_or_2d,
            evaluation_theta_grid,
        )
    else:
        scattering_field_eval = _resample_complex_theta_field(
            scattering_theta_grid_rad,
            scattering_field_theta_or_2d,
            evaluation_theta_grid,
        )
    ref_collapsed, sca_collapsed, joint_overlap = _collapse_and_joint_overlap_with_operator(
        evaluation_theta_grid,
        reference_field_eval,
        scattering_field_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    collapsed_product = complex(ref_collapsed * np.conj(sca_collapsed))
    if abs(collapsed_product) > 1e-30:
        overlap_factor = joint_overlap / collapsed_product
    else:
        overlap_factor = 1.0 + 0.0j

    return {
        "interference_overlap_mode": str(sim_cfg.interference_overlap_mode),
        "interference_cross_term_model_default": str(sim_cfg.interference_overlap_mode),
        "interference_cross_term_joint_available": True,
        "interference_collapsed_product_complex": collapsed_product,
        "interference_joint_overlap_complex": complex(joint_overlap),
        "interference_overlap_factor_complex": complex(overlap_factor),
        "interference_overlap_factor_abs": float(abs(overlap_factor)),
        "interference_overlap_factor_phase_rad": float(np.angle(overlap_factor)),
        "interference_overlap_status": (
            "aligned"
            if np.isclose(abs(overlap_factor - 1.0), 0.0, atol=1e-3)
            else "mismatch_auditable"
        ),
    }


def _copy_collection_operator_payload(operator: dict) -> dict:
    """Return a caller-owned collection-operator payload."""
    copied = {}
    for key, value in operator.items():
        if isinstance(value, np.ndarray):
            copied[key] = value.copy()
        else:
            copied[key] = deepcopy(value)
    return copied


def compute_detected_scattering_field(
    intrinsic: dict,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    *,
    collection_operator: dict | None = None,
) -> dict:
    """
    Collapse the intrinsic angular response into one detected field proxy.

    Three collection modes are supported:
        - single_angle: recover the old point-sampling logic
        - gaussian_weighted: integrate over a finite angular kernel
        - pupil_slit_surrogate: 2D theta/phi surrogate with pupil + slit weighting

    Two field proxies are supported:
        - intensity_proxy: legacy sqrt(dCsca/dΩ) amplitude, positive-real
        - parallel / perpendicular: complex polarization-channel proxies based
          on S2 or S1 respectively, preserving Mie-material phase information

    Returns:
        dict with:
            E_sca_detected_complex: complex detected-field proxy
            E_sca_detected_abs: absolute magnitude of that proxy
            theta_center_rad: collection-kernel center angle
            theta_effective_rad: weighted effective angle
            collection_weights: normalized marginal theta kernel
    """
    theta_grid = intrinsic["theta_grid_rad"]
    k_m = float(intrinsic["k_m"])
    medium_refractive_index = k_m * float(optical.wavelength_m) / (2.0 * np.pi)
    operator = (
        collection_operator
        if collection_operator is not None
        else build_collection_operator(
            theta_grid,
            channel,
            optical,
            sim_cfg,
            medium_refractive_index=medium_refractive_index,
        )
    )
    theta_center = operator["theta_center_rad"]
    sigma_rad = operator["sigma_effective_rad"]

    if sim_cfg.scattering_projection_mode == "intensity_proxy":
        field_theta = intrinsic["Esca_unit_amp"].astype(complex)
    elif sim_cfg.scattering_projection_mode == "parallel":
        field_theta = intrinsic["S2_complex"] / k_m
    elif sim_cfg.scattering_projection_mode == "perpendicular":
        field_theta = intrinsic["S1_complex"] / k_m
    else:
        raise ValueError(
            f"Unsupported scattering_projection_mode: {sim_cfg.scattering_projection_mode}"
        )

    if sim_cfg.collection_integration_mode == "single_angle":
        detected = collapse_angular_field_with_operator(
            theta_grid,
            field_theta,
            operator,
            sim_cfg,
        )
        theta_effective = float(theta_center)
        weights = operator["theta_weights"]
    elif sim_cfg.collection_integration_mode == "gaussian_weighted":
        weights = operator["theta_weights"]
        detected = collapse_angular_field_with_operator(
            theta_grid,
            field_theta,
            operator,
            sim_cfg,
        )
        theta_effective = float(operator["theta_effective_rad"])
    elif sim_cfg.collection_integration_mode == "pupil_slit_surrogate":
        detected = collapse_angular_field_with_operator(
            theta_grid,
            field_theta,
            operator,
            sim_cfg,
            phi_grid_rad=operator["phi_grid_rad"],
        )
        weights = operator["theta_weights"]
        theta_effective = float(operator["theta_effective_rad"])
    else:
        raise ValueError(
            "collection_integration_mode must be 'single_angle', "
            "'gaussian_weighted', or 'pupil_slit_surrogate', got "
            f"{sim_cfg.collection_integration_mode}"
        )

    s1_eff = interpolate_complex_at_theta(
        theta_grid,
        intrinsic["S1_complex"] / k_m,
        theta_effective,
    )
    s2_eff = interpolate_complex_at_theta(
        theta_grid,
        intrinsic["S2_complex"] / k_m,
        theta_effective,
    )
    if sim_cfg.scattering_projection_mode == "parallel":
        material_phase_selected = float(np.angle(s2_eff))
    elif sim_cfg.scattering_projection_mode == "perpendicular":
        material_phase_selected = float(np.angle(s1_eff))
    else:
        material_phase_selected = 0.0

    return {
        "E_sca_detected_complex": detected,
        "E_sca_detected_abs": float(abs(detected)),
        "phi_projection_rad": float(np.angle(detected)),
        "phi_sca_material_rad": material_phase_selected,
        "phi_sca_material_parallel_rad": float(np.angle(s2_eff)),
        "phi_sca_material_perpendicular_rad": float(np.angle(s1_eff)),
        "theta_center_rad": float(theta_center),
        "theta_effective_rad": float(theta_effective),
        "sigma_effective_rad": float(sigma_rad),
        "collection_weights": np.asarray(weights, dtype=float).copy(),
        "operator_signature": operator["operator_signature"],
        "operator_route": operator.get("operator_route"),
        "operator_normalization": operator.get("operator_normalization"),
        "collection_operator_calibration_status": operator.get(
            "collection_operator_calibration_status"
        ),
        "collection_operator_coverage_status": operator.get(
            "collection_operator_coverage_status"
        ),
        "collection_operator_calibration_source": operator.get(
            "collection_operator_calibration_source"
        ),
        "collection_operator_id": operator.get("collection_operator_id"),
        "collection_operator_calibrated_geometry": operator.get(
            "collection_operator_calibrated_geometry"
        ),
        "collection_operator_max_relative_geometry_distance": operator.get(
            "collection_operator_max_relative_geometry_distance"
        ),
        "surrogate_throughput_scale": operator.get("surrogate_throughput_scale"),
        "absolute_throughput_route": operator.get("absolute_throughput_route"),
        "absolute_throughput_calibrated": operator.get(
            "absolute_throughput_calibrated"
        ),
        "field_coordinate_measure": operator.get("field_coordinate_measure"),
        "field_measure_status": operator.get("field_measure_status"),
        "bfp_to_angle_jacobian_applied": operator.get("bfp_to_angle_jacobian_applied"),
        "detector_mask_units": operator.get("detector_mask_units"),
        "bfp_roi_mask_schema": operator.get("bfp_roi_mask_schema"),
        "bfp_roi_mask_path_configured": operator.get("bfp_roi_mask_path_configured"),
        "bfp_roi_mask_calibrated": operator.get("bfp_roi_mask_calibrated"),
        "bfp_roi_mask_source": operator.get("bfp_roi_mask_source"),
        "bfp_roi_mask_status": operator.get("bfp_roi_mask_status"),
        "bfp_roi_mask_claim_level": operator.get("bfp_roi_mask_claim_level"),
        "bfp_roi_mask_data_role": operator.get("bfp_roi_mask_data_role"),
        "bfp_roi_mask_synthetic_fixture_active": operator.get(
            "bfp_roi_mask_synthetic_fixture_active"
        ),
        "bfp_roi_mask_table_validation_status": operator.get(
            "bfp_roi_mask_table_validation_status"
        ),
        "bfp_roi_mask_manifest_status": operator.get(
            "bfp_roi_mask_manifest_status"
        ),
        "bfp_roi_mask_manifest_validation_status": operator.get(
            "bfp_roi_mask_manifest_validation_status"
        ),
        "bfp_roi_mask_manifest_path": operator.get("bfp_roi_mask_manifest_path"),
        "bfp_roi_mask_row_count": operator.get("bfp_roi_mask_row_count"),
        "bfp_roi_mask_required_field_groups_missing": operator.get(
            "bfp_roi_mask_required_field_groups_missing"
        ),
        "bfp_roi_mask_gate_passed": operator.get("bfp_roi_mask_gate_passed"),
        "bfp_pixel_to_angle_status": operator.get("bfp_pixel_to_angle_status"),
        "slit_position_mapping_status": operator.get("slit_position_mapping_status"),
        "pinhole_projection_status": operator.get("pinhole_projection_status"),
        "bfp_roi_required_inputs": operator.get("bfp_roi_required_inputs"),
        "collection_operator": (
            _copy_collection_operator_payload(operator)
            if collection_operator is not None
            else operator
        ),
        "theta_grid_rad": theta_grid.copy(),
        "phi_grid_rad": np.asarray(operator["phi_grid_rad"], dtype=float).copy(),
        "angular_field_theta": np.asarray(field_theta, dtype=complex).copy(),
    }


def validate_simulation_config(
    sim_cfg: SimulationConfig,
    optical: OpticalSystem,
) -> None:
    """
    Validate that simulation configuration is physically consistent.

    Checks:
        1. total_time >= 10 × transit_duration (background dominates)
        2. First 20% time segment is pulse-free (for robust threshold estimation)
        3. Sufficient number of samples

    Raises:
        ValueError: If any check fails.
    """
    max_velocity = estimate_max_axial_velocity(sim_cfg)
    illumination_geometry = optical.resolve_illumination_geometry()
    illumination_beam_waist_y_m = float(
        illumination_geometry["illumination_beam_waist_y_m"]
    )
    transit_duration = illumination_beam_waist_y_m / max_velocity

    # Check 1: total time >> transit
    if sim_cfg.total_time_s < 10 * transit_duration:
        raise ValueError(
            f"total_time ({sim_cfg.total_time_s:.4f}s) must be >= 10× "
            f"transit_duration ({transit_duration:.4f}s). "
            f"Increase total_time or reduce beam_waist_y."
        )

    # Check 2: first 20% background segment doesn't overlap illumination zone
    # Particle reaches focus at ~50% of total_time.
    # At end of bg segment (20%), particle is at 30% of travel before focus.
    # Distance from focus at 20% mark:
    #   y_at_20pct = focus_y - velocity * total_time * 0.3
    # This should be >> beam_waist_y (several waists away from focus)
    y_distance_at_bg_end = max_velocity * sim_cfg.total_time_s * 0.3
    if y_distance_at_bg_end < 5 * illumination_beam_waist_y_m:
        raise ValueError(
            f"Background segment (first 20%) too close to illumination zone. "
            f"Distance from focus at bg end: {y_distance_at_bg_end:.2e}m, "
            f"need >= 5×beam_waist_y = {5*illumination_beam_waist_y_m:.2e}m. "
            f"Increase total_time or reduce velocity."
        )

    # Check 3: minimum samples
    if sim_cfg.n_samples < 10:
        raise ValueError(
            f"Too few samples ({sim_cfg.n_samples}). "
            f"Increase total_time or sampling_rate."
        )


def sample_initial_position(
    channel: Channel,
    rng: np.random.Generator,
    particle_radius_m: float = 0.0,
    sim_cfg: SimulationConfig | None = None,
    unit_position_sample: tuple[float, float, float] | None = None,
) -> tuple[float, float, dict[str, float | str | bool]]:
    """
    Sample a particle initial position within the channel cross-section.

    Args:
        channel: Channel geometry.
        rng: NumPy random number generator.

    Returns:
        `(x0, z0, diagnostics)` where diagnostics makes the sampling surrogate
        explicit and auditable.
    """
    if unit_position_sample is not None and len(unit_position_sample) != 3:
        raise ValueError("unit_position_sample must contain exactly three values")

    def _unit(index: int) -> float:
        if unit_position_sample is None:
            return float(rng.uniform(0.0, 1.0))
        return float(np.clip(unit_position_sample[index], 0.0, np.nextafter(1.0, 0.0)))

    half_w = channel.width_m / 2.0 - particle_radius_m
    half_h = channel.depth_m / 2.0 - particle_radius_m
    if half_w <= 0 or half_h <= 0:
        raise ValueError(
            "particle_radius_m is too large for the channel cross-section: "
            f"radius={particle_radius_m:.2e}m, width={channel.width_m:.2e}m, "
            f"depth={channel.depth_m:.2e}m"
        )
    if sim_cfg is None:
        mode = "uniform"
        strength = 0.0
        min_conf_ratio = 0.0
        flux_mixture_fraction = 0.0
    else:
        mode = str(sim_cfg.initial_position_distribution_mode)
        strength = float(sim_cfg.initial_position_center_bias_strength)
        min_conf_ratio = float(sim_cfg.initial_position_center_bias_min_confinement_ratio)
        flux_mixture_fraction = float(
            sim_cfg.initial_position_flux_weighted_mixture_fraction
        )

    min_half_extent = max(min(half_w, half_h), 1e-18)
    confinement_ratio = float(np.clip(particle_radius_m / min_half_extent, 0.0, 1.0))
    confinement_activation = float(
        np.clip(
            (confinement_ratio - min_conf_ratio) / max(0.25 - min_conf_ratio, 1e-12),
            0.0,
            1.0,
        )
    )
    aspect_depth_focus = float(np.clip(channel.width_m / max(channel.depth_m, 1e-18), 1.0, 4.0))

    flux_attempts = 1
    flux_acceptance_rate = 1.0
    mixture_component = "not_applicable"
    use_flux_weighted_sampler = mode == "flux_weighted"
    if mode == "flux_uniform_mixture_surrogate":
        use_flux_weighted_sampler = _unit(2) < flux_mixture_fraction
        mixture_component = (
            "flux_weighted"
            if use_flux_weighted_sampler
            else "uniform_accessible_area"
        )

    if use_flux_weighted_sampler:
        assert sim_cfg is not None
        max_velocity = max(estimate_max_axial_velocity(sim_cfg), 1e-18)
        x0 = 0.0
        z0 = 0.0
        accepted = False
        max_attempts = 128
        for attempt in range(1, max_attempts + 1):
            if attempt == 1 and unit_position_sample is not None:
                candidate_x = float(-half_w + 2.0 * half_w * _unit(0))
                candidate_z = float(-half_h + 2.0 * half_h * _unit(1))
                accept_draw = (
                    _unit(2)
                    if mode == "flux_weighted"
                    else float(rng.uniform(0.0, 1.0))
                )
            else:
                candidate_x = float(rng.uniform(-half_w, half_w))
                candidate_z = float(rng.uniform(-half_h, half_h))
                accept_draw = float(rng.uniform(0.0, 1.0))
            local_velocity = float(
                axial_transport_velocity_m_s(
                    candidate_x,
                    candidate_z,
                    channel,
                    sim_cfg,
                    particle_radius_m=particle_radius_m,
                )
            )
            accept_probability = float(np.clip(local_velocity / max_velocity, 0.0, 1.0))
            if accept_draw <= accept_probability:
                x0 = candidate_x
                z0 = candidate_z
                accepted = True
                flux_attempts = attempt
                break
        if not accepted:
            flux_attempts = max_attempts
        flux_acceptance_rate = 1.0 / float(flux_attempts)
        x_exponent = 1.0
        z_exponent = 1.0
        active = True
    elif mode == "center_biased_surrogate" and strength > 0 and confinement_activation > 0:
        x_exponent = float(1.0 + 0.6 * strength * confinement_activation)
        z_exponent = float(1.0 + 1.2 * strength * confinement_activation * np.sqrt(aspect_depth_focus))

        def _sample_centered_coordinate(
            half_extent: float,
            exponent: float,
            unit_index: int,
        ) -> float:
            unit = _unit(unit_index)
            u = float(-1.0 + 2.0 * unit)
            return float(half_extent * np.sign(u) * (abs(u) ** exponent))

        x0 = _sample_centered_coordinate(half_w, x_exponent, 0)
        z0 = _sample_centered_coordinate(half_h, z_exponent, 1)
        active = True
    else:
        x0 = float(-half_w + 2.0 * half_w * _unit(0))
        z0 = float(-half_h + 2.0 * half_h * _unit(1))
        x_exponent = 1.0
        z_exponent = 1.0
        active = False

    if mode == "flux_weighted":
        cross_section_event_bias_status = "flux_weighted_by_axial_transport_velocity"
    elif mode == "flux_uniform_mixture_surrogate":
        cross_section_event_bias_status = (
            "flux_uniform_mixture_flux_weighted_component"
            if active
            else "flux_uniform_mixture_uniform_component"
        )
    elif mode == "uniform_accessible_area":
        cross_section_event_bias_status = "uniform_over_accessible_particle_center_area"
    elif mode == "center_biased_surrogate":
        cross_section_event_bias_status = (
            "center_biased_surrogate_active"
            if active
            else "center_biased_surrogate_inactive"
        )
    else:
        cross_section_event_bias_status = "legacy_uniform_over_accessible_particle_center_area"

    diagnostics: dict[str, float | str | bool] = {
        "initial_position_distribution_mode": mode,
        "initial_position_distribution_active": bool(active),
        "initial_position_unit_sample_supplied": bool(
            unit_position_sample is not None
        ),
        "cross_section_event_bias_status": cross_section_event_bias_status,
        "flux_weighted_sampling_acceptance_rate": flux_acceptance_rate,
        "flux_weighted_sampling_attempts": int(flux_attempts),
        "initial_position_center_bias_strength": strength,
        "initial_position_center_bias_min_confinement_ratio": min_conf_ratio,
        "initial_position_flux_weighted_mixture_fraction": flux_mixture_fraction,
        "initial_position_mixture_component": mixture_component,
        "initial_position_confinement_ratio": confinement_ratio,
        "initial_position_confinement_activation": confinement_activation,
        "initial_position_center_bias_x_exponent": x_exponent,
        "initial_position_center_bias_z_exponent": z_exponent,
        "initial_position_x_norm": float(x0 / max(half_w, 1e-18)),
        "initial_position_z_norm": float(z0 / max(half_h, 1e-18)),
    }
    return float(x0), float(z0), diagnostics


def min_max_normalize(value: float, all_values: list[float]) -> float:
    """
    Min-max normalize a value to [0, 1] range within a batch.

    Args:
        value: Value to normalize.
        all_values: All values in the batch for reference.

    Returns:
        Normalized value in [0, 1]. Returns 0.0 if all values are identical.
    """
    mn = min(all_values)
    mx = max(all_values)
    if mx == mn:
        return 0.0
    return (value - mn) / (mx - mn)


def compute_baseline_normalization(
    particle: Particle,
    medium: Medium,
    optical_baseline: OpticalSystem,
    theta_grid_rad: np.ndarray,
    channel: Channel | None = None,
    sim_cfg: SimulationConfig | None = None,
) -> dict:
    """
    Compute the global E_sca_ref normalization constant.

    Must be called ONCE before the parameter sweep. The returned E_sca_ref
    is used to normalize all subsequent scattering amplitude calculations.

    Uses the SAME interpolate_at_theta function as runtime code to ensure
    consistent interpolation between baseline and all sweep cases.

    Args:
        particle: Baseline particle (gold, radius=20nm).
        medium: Baseline medium (water).
        optical_baseline: Baseline optical system (λ=660nm).
        theta_grid_rad: Global angle grid.

    Returns:
        dict with:
            E_sca_ref: float — the normalization constant (> 0)
            wavelength_m: float — the baseline wavelength used

    All wavelengths share this single E_sca_ref (global normalization mode).
    For per-wavelength normalization, use compute_baseline_normalization_per_wavelength.
    """
    intrinsic = compute_intrinsic_scattering(
        particle, medium, optical_baseline.wavelength_m, theta_grid_rad
    )

    if channel is not None and sim_cfg is not None:
        collection = compute_detected_scattering_field(
            intrinsic, channel, optical_baseline, sim_cfg
        )
        theta_det = collection["theta_effective_rad"]
        E_sca_ref = collection["E_sca_detected_abs"]
        E_sca_ref_complex = collection["E_sca_detected_complex"]
    else:
        theta_det = optical_baseline.collection_theta_rad
        E_sca_ref_complex = interpolate_complex_at_theta(
            intrinsic["theta_grid_rad"],
            intrinsic["Esca_unit_amp"].astype(complex),
            theta_det,
        )
        E_sca_ref = float(abs(E_sca_ref_complex))

    if E_sca_ref <= 0:
        raise ValueError(
            f"E_sca_ref must be positive, got {E_sca_ref}. "
            f"Check baseline particle/medium/wavelength parameters."
        )

    return {
        "E_sca_ref": E_sca_ref,
        "E_sca_ref_complex": complex(E_sca_ref_complex),
        "wavelength_m": optical_baseline.wavelength_m,
        "theta_det_rad": float(theta_det),
        "operator_signature": (
            collection["operator_signature"]
            if channel is not None and sim_cfg is not None
            else (
                f"angle=fixed"
                f"|integration=single_angle"
                f"|projection=intensity_proxy"
                f"|theta_center={float(theta_det):.9e}"
                f"|theta_sigma=0.000000000e+00"
                f"|phi_sigma=0.000000000e+00"
                f"|slit_phi=0.000000000e+00"
            )
        ),
    }


def compute_baseline_normalization_per_wavelength(
    particle: Particle,
    medium: Medium,
    optical_template: OpticalSystem,
    wavelength_list_m: np.ndarray,
    theta_grid_rad: np.ndarray,
    channel: Channel | None = None,
    sim_cfg: SimulationConfig | None = None,
) -> dict[float, float]:
    """
    Compute per-wavelength E_sca_ref normalization constants.

    Each wavelength gets its own baseline, computed with that wavelength's
    material optical constants. This eliminates the bias from anchoring
    all wavelengths to a single baseline wavelength.

    Args:
        particle: Baseline particle (should have use_material_model=True for
            wavelength-dependent optical constants).
        medium: Baseline medium.
        optical_template: Template optical system (wavelength will be replaced).
        wavelength_list_m: Array of wavelengths to compute baselines for.
        theta_grid_rad: Global angle grid.

    Returns:
        Dict mapping wavelength (float) -> E_sca_ref (float).
    """
    result = {}
    for wl in wavelength_list_m:
        optical = copy(optical_template)
        optical.wavelength_m = float(wl)
        bl = compute_baseline_normalization(
            particle,
            medium,
            optical,
            theta_grid_rad,
            channel=channel,
            sim_cfg=sim_cfg,
        )
        result[float(wl)] = bl["E_sca_ref"]
    return result
