#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools import tsuyama_detection_rate_calibration as rate_calib

OUTPUT_DIR = PROJECT_ROOT / "results" / "instrument_hardware_feasibility_v1"
SCHEMA_ID = "instrument_hardware_feasibility_v1"
PRIOR_FILENAME = "instrument_hardware_prior_v1.csv"
FEASIBILITY_FILENAME = "instrument_connection_feasibility_v1.csv"
SUMMARY_JSON_FILENAME = "instrument_hardware_feasibility_summary_v1.json"
REPORT_FILENAME = "instrument_hardware_feasibility_report_v1.md"

E_CHARGE_C = 1.602176634e-19
DEFAULT_WAVELENGTHS_NM = (404, 488, 532, 660)
DEFAULT_TAU_MS = (1.0, 2.0, 3.0)
DEFAULT_FILTER_ORDERS = (1, 2, 4)
DEFAULT_REFERENCE_POWERS_W = (1.0e-9, 1.0e-8, 1.0e-7)
TARGET_SNR_ANCHORS = (
    ("Au20_paper_normalized", 12.0),
    ("Au30_paper_normalized", 33.0),
)


@dataclass(frozen=True)
class ET2030Prior:
    active_area_diameter_m: float = 0.4e-3
    bandwidth_hz: float = 1.2e9
    dark_current_A: float = 0.1e-9
    nep_W_per_sqrtHz: float = 1.0e-14
    max_linear_current_A: float = 3.0e-3
    responsivity_A_per_W_404: float = 0.12
    responsivity_A_per_W_488: float = 0.25
    responsivity_A_per_W_532: float = 0.32
    responsivity_A_per_W_660: float = 0.42
    responsivity_source: str = "estimated_silicon_curve_not_measured"

    def responsivity(self, wavelength_nm: int) -> float:
        table = {
            404: self.responsivity_A_per_W_404,
            488: self.responsivity_A_per_W_488,
            532: self.responsivity_A_per_W_532,
            660: self.responsivity_A_per_W_660,
        }
        if int(wavelength_nm) in table:
            return float(table[int(wavelength_nm)])
        known = sorted(table)
        lower = max([value for value in known if value <= wavelength_nm], default=known[0])
        upper = min([value for value in known if value >= wavelength_nm], default=known[-1])
        if lower == upper:
            return float(table[lower])
        frac = (float(wavelength_nm) - lower) / (upper - lower)
        return float(table[lower] + frac * (table[upper] - table[lower]))


@dataclass(frozen=True)
class LI5640Prior:
    frequency_min_hz: float = 1.0e-3
    frequency_max_hz: float = 1.0e5
    time_constant_min_s: float = 10.0e-6
    time_constant_max_s: float = 30.0e3
    dynamic_reserve_dB: float = 100.0
    current_fullscale_min_A: float = 5.0e-15
    current_fullscale_max_A: float = 1.0e-6
    voltage_fullscale_min_V: float = 2.0e-9
    voltage_fullscale_max_V: float = 1.0
    current_input_noise_density_A_per_sqrtHz: float = 5.0e-15
    input_termination_ohm: float = 50.0
    voltage_sensitivity_source: str = "datasheet_fullscale_not_noise_density"
    current_noise_source: str = "estimated_floor_for_feasibility_not_calibration"


def lockin_enbw_hz(tau_s: float, filter_order: int) -> float:
    """Equivalent noise bandwidth for cascaded equal-pole low-pass surrogate."""
    if tau_s <= 0:
        raise ValueError("tau_s must be positive")
    if filter_order < 1:
        raise ValueError("filter_order must be >= 1")
    numerator = math.sqrt(math.pi) * math.gamma(filter_order - 0.5)
    denominator = 4.0 * math.pi * tau_s * math.gamma(filter_order)
    return float(numerator / denominator)


def _status_from_margin(margin: float, *, warning: float = 1.0, comfortable: float = 10.0) -> str:
    if not math.isfinite(margin):
        return "not_evaluated"
    if margin < warning:
        return "below_minimum_sensitivity"
    if margin < comfortable:
        return "near_minimum_sensitivity"
    return "comfortable_margin"


def _upper_limit_status(margin: float) -> str:
    if not math.isfinite(margin):
        return "not_evaluated"
    if margin < 1.0:
        return "over_upper_limit"
    if margin < 10.0:
        return "near_upper_limit"
    return "comfortable_margin"


def _detector_linear_status(linear_margin: float) -> str:
    if not math.isfinite(linear_margin):
        return "not_evaluated"
    if linear_margin < 1.0:
        return "over_detector_linear_current_limit"
    if linear_margin < 10.0:
        return "near_detector_linear_current_limit"
    return "comfortable_margin"


def _connection_recommendation(
    *,
    detector_linear_margin: float,
    current_min_margin: float,
    current_max_margin: float,
    voltage_min_margin: float,
    voltage_max_margin: float,
) -> str:
    current_feasible = current_min_margin >= 1.0 and current_max_margin >= 1.0
    voltage_feasible = voltage_min_margin >= 1.0 and voltage_max_margin >= 1.0
    if detector_linear_margin < 1.0:
        return "reduce_reference_power_detector_over_linear_limit"
    if current_feasible and not voltage_feasible:
        return "prefer_current_input_or_low_noise_TIA"
    if current_feasible and voltage_feasible:
        return "either_connection_has_sensitivity_and_range_margin"
    if not current_feasible and not voltage_feasible:
        return "increase_gain_or_reduce_signal_to_enter_instrument_range"
    return "check_connection_mode_range_tradeoff"


def _reference_shot_noise_current_A(
    *,
    responsivity_A_per_W: float,
    reference_power_W: float,
    dark_current_A: float,
    enbw_hz: float,
) -> float:
    reference_current_A = max(0.0, responsivity_A_per_W * reference_power_W)
    shot_current_density_A2_per_Hz = 2.0 * E_CHARGE_C * (
        reference_current_A + max(0.0, dark_current_A)
    )
    return float(math.sqrt(max(0.0, shot_current_density_A2_per_Hz * enbw_hz)))


def feasibility_rows(
    *,
    detector: ET2030Prior,
    lockin: LI5640Prior,
    wavelengths_nm: tuple[int, ...] = DEFAULT_WAVELENGTHS_NM,
    tau_ms_values: tuple[float, ...] = DEFAULT_TAU_MS,
    filter_orders: tuple[int, ...] = DEFAULT_FILTER_ORDERS,
    reference_powers_W: tuple[float, ...] = DEFAULT_REFERENCE_POWERS_W,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wavelength_nm in wavelengths_nm:
        responsivity = detector.responsivity(wavelength_nm)
        detector_nep_current_density = responsivity * detector.nep_W_per_sqrtHz
        for tau_ms in tau_ms_values:
            tau_s = float(tau_ms) * 1.0e-3
            for filter_order in filter_orders:
                enbw = lockin_enbw_hz(tau_s, int(filter_order))
                detector_nep_current_rms = detector_nep_current_density * math.sqrt(enbw)
                lockin_current_noise_rms = (
                    lockin.current_input_noise_density_A_per_sqrtHz * math.sqrt(enbw)
                )
                for reference_power_W in reference_powers_W:
                    reference_current_A = responsivity * reference_power_W
                    reference_shot_noise_A = _reference_shot_noise_current_A(
                        responsivity_A_per_W=responsivity,
                        reference_power_W=reference_power_W,
                        dark_current_A=detector.dark_current_A,
                        enbw_hz=enbw,
                    )
                    total_current_noise_A = math.sqrt(
                        detector_nep_current_rms**2
                        + lockin_current_noise_rms**2
                        + reference_shot_noise_A**2
                    )
                    total_power_noise_W = total_current_noise_A / max(
                        responsivity,
                        1e-30,
                    )
                    for target_label, target_snr in TARGET_SNR_ANCHORS:
                        required_modulation_power_W = target_snr * total_power_noise_W
                        required_photocurrent_A = (
                            responsivity * required_modulation_power_W
                        )
                        equivalent_50ohm_voltage_V = (
                            required_photocurrent_A * lockin.input_termination_ohm
                        )
                        current_margin = (
                            required_photocurrent_A / lockin.current_fullscale_min_A
                        )
                        voltage_margin = (
                            equivalent_50ohm_voltage_V / lockin.voltage_fullscale_min_V
                        )
                        current_max_margin = lockin.current_fullscale_max_A / max(
                            required_photocurrent_A,
                            1e-30,
                        )
                        voltage_max_margin = lockin.voltage_fullscale_max_V / max(
                            equivalent_50ohm_voltage_V,
                            1e-30,
                        )
                        linear_margin = detector.max_linear_current_A / max(
                            reference_current_A + required_photocurrent_A,
                            1e-30,
                        )
                        required_fraction = required_modulation_power_W / max(
                            reference_power_W,
                            1e-30,
                        )
                        rows.append(
                            {
                                "schema_id": SCHEMA_ID,
                                "hardware_profile_id": "ET2030_LI5640_estimated_v1",
                                "claim_level": (
                                    "instrument_feasibility_estimate_not_calibration"
                                ),
                                "wavelength_nm": int(wavelength_nm),
                                "target_snr_label": target_label,
                                "target_snr": float(target_snr),
                                "connection_mode": "current_input_or_external_TIA",
                                "reference_power_W": float(reference_power_W),
                                "photodiode_responsivity_A_per_W": responsivity,
                                "lockin_tau_ms": float(tau_ms),
                                "lockin_filter_order": int(filter_order),
                                "lockin_enbw_hz": enbw,
                                "detector_nep_current_noise_A_rms": (
                                    detector_nep_current_rms
                                ),
                                "lockin_current_noise_A_rms": lockin_current_noise_rms,
                                "reference_shot_noise_A_rms": reference_shot_noise_A,
                                "total_current_noise_A_rms": total_current_noise_A,
                                "total_power_noise_W_rms": total_power_noise_W,
                                "required_modulation_power_W": (
                                    required_modulation_power_W
                                ),
                                "required_modulation_fraction_of_reference": (
                                    required_fraction
                                ),
                                "required_photocurrent_A": required_photocurrent_A,
                                "equivalent_50ohm_voltage_V": equivalent_50ohm_voltage_V,
                                "current_input_margin_vs_min_fullscale": current_margin,
                                "current_input_margin_vs_max_fullscale": (
                                    current_max_margin
                                ),
                                "voltage_input_margin_vs_min_sensitivity": voltage_margin,
                                "voltage_input_margin_vs_max_fullscale": (
                                    voltage_max_margin
                                ),
                                "detector_linear_current_margin": linear_margin,
                                "current_input_status": _status_from_margin(
                                    current_margin,
                                ),
                                "current_input_max_range_status": _upper_limit_status(
                                    current_max_margin,
                                ),
                                "voltage_50ohm_status": _status_from_margin(
                                    voltage_margin,
                                ),
                                "voltage_50ohm_max_range_status": _upper_limit_status(
                                    voltage_max_margin,
                                ),
                                "detector_saturation_status": _detector_linear_status(
                                    linear_margin
                                ),
                                "connection_recommendation": _connection_recommendation(
                                    detector_linear_margin=linear_margin,
                                    current_min_margin=current_margin,
                                    current_max_margin=current_max_margin,
                                    voltage_min_margin=voltage_margin,
                                    voltage_max_margin=voltage_max_margin,
                                ),
                            }
                        )
    return rows


def prior_frame(detector: ET2030Prior, lockin: LI5640Prior) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, value in asdict(detector).items():
        rows.append(
            {
                "component": "ET-2030",
                "field": key,
                "value": value,
                "source_level": (
                    "public_spec_or_estimated_prior"
                    if "responsivity" not in key
                    else "estimated_prior_not_measured"
                ),
            }
        )
    for key, value in asdict(lockin).items():
        rows.append(
            {
                "component": "LI5640",
                "field": key,
                "value": value,
                "source_level": "public_spec_or_estimated_prior",
            }
        )
    return pd.DataFrame(rows)


def summarize_feasibility(frame: pd.DataFrame) -> dict[str, Any]:
    current_status_counts = frame["current_input_status"].value_counts().to_dict()
    voltage_status_counts = frame["voltage_50ohm_status"].value_counts().to_dict()
    recommendation_counts = frame["connection_recommendation"].value_counts().to_dict()
    detector_saturation_counts = (
        frame["detector_saturation_status"].value_counts().to_dict()
    )
    current_max_status_counts = (
        frame["current_input_max_range_status"].value_counts().to_dict()
    )
    voltage_max_status_counts = (
        frame["voltage_50ohm_max_range_status"].value_counts().to_dict()
    )
    min_rows = (
        frame.sort_values(
            ["target_snr", "required_modulation_power_W", "wavelength_nm"],
            ignore_index=True,
        )
        .groupby(["target_snr_label", "wavelength_nm"], as_index=False)
        .first()
    )
    return {
        "schema_id": SCHEMA_ID,
        "generated_at_unix": time.time(),
        "claim_level": "instrument_feasibility_estimate_not_calibration",
        "phase2_paper_fit_search_status": "stopped_negative_or_diagnostic_only",
        "ev_full_grid_writeback": False,
        "selected_annulus_changed": False,
        "global_material_defaults_changed": False,
        "detector_unit_chain_unlocked": False,
        "current_input_status_counts": current_status_counts,
        "voltage_50ohm_status_counts": voltage_status_counts,
        "connection_recommendation_counts": recommendation_counts,
        "detector_saturation_status_counts": detector_saturation_counts,
        "current_input_max_range_status_counts": current_max_status_counts,
        "voltage_50ohm_max_range_status_counts": voltage_max_status_counts,
        "minimum_required_modulation_power_by_target": min_rows[
            [
                "target_snr_label",
                "wavelength_nm",
                "lockin_tau_ms",
                "lockin_filter_order",
                "reference_power_W",
                "required_modulation_power_W",
                "required_modulation_fraction_of_reference",
                "current_input_status",
                "current_input_max_range_status",
                "voltage_50ohm_status",
                "voltage_50ohm_max_range_status",
                "detector_saturation_status",
            ]
        ].to_dict(orient="records"),
        "summary": (
            "ET-2030/LI5640 estimated priors support current-input/TIA feasibility "
            "checks; 50-ohm voltage mode is expected to be weak for pA/fA-scale "
            "photocurrent. This does not calibrate absolute NODI SNR."
        ),
    }


def write_outputs(
    *,
    output_dir: Path,
    detector: ET2030Prior,
    lockin: LI5640Prior,
    wavelengths_nm: tuple[int, ...] = DEFAULT_WAVELENGTHS_NM,
    tau_ms_values: tuple[float, ...] = DEFAULT_TAU_MS,
    filter_orders: tuple[int, ...] = DEFAULT_FILTER_ORDERS,
    reference_powers_W: tuple[float, ...] = DEFAULT_REFERENCE_POWERS_W,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prior = prior_frame(detector, lockin)
    feasibility = pd.DataFrame(
        feasibility_rows(
            detector=detector,
            lockin=lockin,
            wavelengths_nm=wavelengths_nm,
            tau_ms_values=tau_ms_values,
            filter_orders=filter_orders,
            reference_powers_W=reference_powers_W,
        )
    )
    summary = summarize_feasibility(feasibility)
    prior_path = output_dir / PRIOR_FILENAME
    feasibility_path = output_dir / FEASIBILITY_FILENAME
    summary_path = output_dir / SUMMARY_JSON_FILENAME
    report_path = output_dir / REPORT_FILENAME
    prior.to_csv(prior_path, index=False)
    feasibility.to_csv(feasibility_path, index=False)
    rate_calib.write_json(summary_path, summary)

    compact_cols = [
        "wavelength_nm",
        "target_snr_label",
        "connection_mode",
        "reference_power_W",
        "lockin_tau_ms",
        "lockin_filter_order",
        "lockin_enbw_hz",
        "required_modulation_power_W",
        "required_modulation_fraction_of_reference",
        "required_photocurrent_A",
        "equivalent_50ohm_voltage_V",
        "current_input_status",
        "current_input_max_range_status",
        "voltage_50ohm_status",
        "voltage_50ohm_max_range_status",
        "detector_saturation_status",
        "connection_recommendation",
    ]
    best_by_target = (
        feasibility.sort_values(
            ["target_snr", "required_modulation_power_W", "wavelength_nm"],
            ignore_index=True,
        )
        .groupby(["target_snr_label", "wavelength_nm"], as_index=False)
        .first()
    )
    lines = [
        "# Instrument Hardware Feasibility Report",
        "",
        "## Boundary",
        "",
        "- This is an estimated hardware feasibility layer, not Tsuyama paper-fit search.",
        "- It does not unlock detector-unit calibration, absolute SNR, LOD, or concentration claims.",
        "- It does not modify EV full-grid, selected-annulus bounds, or global material defaults.",
        "- Connection-mode comparison is intended to flag current-input/TIA versus 50-ohm voltage-readout risk.",
        "",
        "## Summary",
        "",
        f"- Current-input status counts: `{json.dumps(summary['current_input_status_counts'], ensure_ascii=False)}`.",
        f"- 50-ohm voltage status counts: `{json.dumps(summary['voltage_50ohm_status_counts'], ensure_ascii=False)}`.",
        f"- Recommendation counts: `{json.dumps(summary['connection_recommendation_counts'], ensure_ascii=False)}`.",
        f"- Detector saturation counts: `{json.dumps(summary['detector_saturation_status_counts'], ensure_ascii=False)}`.",
        "",
        "## Best-Case Required Modulation Power",
        "",
        rate_calib.dataframe_to_markdown(best_by_target.loc[:, compact_cols]),
        "",
        "## Hardware Prior",
        "",
        rate_calib.dataframe_to_markdown(prior),
        "",
        "## Output Files",
        "",
        f"- `{prior_path}`",
        f"- `{feasibility_path}`",
        f"- `{summary_path}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return feasibility, summary


def _float_tuple(values: list[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _int_tuple(values: list[int]) -> tuple[int, ...]:
    return tuple(int(value) for value in values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate ET-2030 + LI5640 connection-mode feasibility."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--wavelengths-nm",
        type=int,
        nargs="+",
        default=list(DEFAULT_WAVELENGTHS_NM),
    )
    parser.add_argument(
        "--tau-ms",
        type=float,
        nargs="+",
        default=list(DEFAULT_TAU_MS),
    )
    parser.add_argument(
        "--filter-orders",
        type=int,
        nargs="+",
        default=list(DEFAULT_FILTER_ORDERS),
    )
    parser.add_argument(
        "--reference-powers-W",
        type=float,
        nargs="+",
        default=list(DEFAULT_REFERENCE_POWERS_W),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    feasibility, summary = write_outputs(
        output_dir=args.output_dir,
        detector=ET2030Prior(),
        lockin=LI5640Prior(),
        wavelengths_nm=_int_tuple(args.wavelengths_nm),
        tau_ms_values=_float_tuple(args.tau_ms),
        filter_orders=_int_tuple(args.filter_orders),
        reference_powers_W=_float_tuple(args.reference_powers_W),
    )
    print(
        f"Wrote {len(feasibility)} hardware feasibility rows to {args.output_dir} "
        f"({summary['claim_level']})"
    )


if __name__ == "__main__":
    main()
