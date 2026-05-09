#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from tools.audits import tsuyama_paper_target_audit as target_audit
from tools.audits import tsuyama_selected_annulus_joint_fit as joint_fit
from nodi_simulator.type_coerce import finite_float_or_nan as _safe_float

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_phase2_acceptance_baseline_v1"
SCHEMA_ID = "tsuyama_phase2_acceptance_report_v1"
DEFAULT_JOINT_SUMMARY = (
    PROJECT_ROOT
    / "results"
    / "tsuyama_selected_annulus_joint_fit_v2_size_response_10000e_20260501"
    / joint_fit.SUMMARY_FILENAME
)
DEFAULT_CLASSIFICATION_SUMMARY = (
    PROJECT_ROOT
    / "results"
    / "tsuyama_2022_classification_lane_v2_400e_20260501"
    / "tsuyama_2022_classification_summary_v2.csv"
)
DEFAULT_ROUTE_SUMMARY = PROJECT_ROOT / "results" / "ev_size_weighted_route_analysis.csv"
SUMMARY_FILENAME = "phase2_acceptance_summary_v1.csv"
JSON_FILENAME = "phase2_acceptance_v1.json"
REPORT_FILENAME = "phase2_acceptance_report_v1.md"
GUARDRAIL_FILENAME = "phase2_guardrail_failures_v1.csv"
SHADOW_FILENAME = "phase2_shadow_all_crossing_dashboard_v1.csv"
REPRODUCTION_SUMMARY_FILENAME = "paper_reproduction_fit_summary_v1.csv"
REPRODUCTION_BEST_FILENAME = "paper_reproduction_fit_best_candidates_v1.csv"
REPRODUCTION_JSON_FILENAME = "paper_reproduction_fit_acceptance_v1.json"
REPRODUCTION_REPORT_FILENAME = "paper_reproduction_fit_report_v1.md"
REPRODUCTION_DECOMPOSITION_FILENAME = "paper_reproduction_score_decomposition_v1.csv"
SIZE_RESPONSE_CASE_DECOMPOSITION_FILENAME = (
    "paper_reproduction_size_response_case_decomposition_v1.csv"
)
SIZE_RESPONSE_CANDIDATE_SUMMARY_FILENAME = (
    "paper_reproduction_size_response_candidate_summary_v1.csv"
)
SIZE_RESPONSE_REPORT_FILENAME = "paper_reproduction_size_response_report_v1.md"
DETECTION_BAND_EPS = 0.01
DETECTION_BAND_SEVERE_EPS = 0.03
MAX_HASH_BYTES = 50 * 1024 * 1024
PAPER_AU20_SNR_TARGET = 12.0
PAPER_AU30_SNR_TARGET = 33.0
REPRODUCTION_SIZE_DELTA_PREFERRED_MIN = -1.0
REPRODUCTION_SIZE_DELTA_PREFERRED_MAX = 0.0
REPRODUCTION_SIZE_DELTA_HARD_MIN = -1.2
REPRODUCTION_SIZE_DELTA_HARD_MAX = 0.2
REPRODUCTION_SNR_RESPONSE_EXPONENT_PREFERRED_MIN = 0.75
REPRODUCTION_SNR_RESPONSE_EXPONENT_PREFERRED_MAX = 1.05
REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MIN = 0.5
REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MAX = 1.2
REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_PREFERRED_MIN = 0.70
REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_PREFERRED_MAX = 0.95
REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MIN = 0.55
REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MAX = 1.05

def _safe_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        result = float(value)
        return result if np.isfinite(result) else None
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    return value


def _normalized_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    return str(value).strip()


def _mode_is_active(value: Any) -> bool:
    text = _normalized_text(value).lower()
    return text not in {"", "none", "nan", "null"}


def _bounded_log_ratio(value: float, target: float) -> float:
    if np.isfinite(value) and value > 0 and np.isfinite(target) and target > 0:
        return float(math.log(value / target))
    return float("nan")


def _numeric_column(frame: pd.DataFrame, column: str, default: float = float("nan")) -> pd.Series:
    if column in frame.columns:
        return pd.to_numeric(frame[column], errors="coerce")
    return pd.Series(default, index=frame.index, dtype="float64")


def _status_row(metric: str, status: str, value: Any, notes: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "status": status,
        "value": value,
        "notes": notes,
    }


def _file_sha256(path: Path, *, max_bytes: int = MAX_HASH_BYTES) -> str:
    """Return a full-file sha256, or an explicitly marked prefix hash for large files.

    Values ending in ``:first_N_bytes`` are not full-file integrity hashes.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        remaining = max_bytes
        while remaining > 0:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            hasher.update(chunk)
            remaining -= len(chunk)
    suffix = "" if path.stat().st_size <= max_bytes else f":first_{max_bytes}_bytes"
    return hasher.hexdigest() + suffix


def _target_frame(path: Path | None) -> pd.DataFrame:
    if path is None:
        return target_audit.build_target_frame()
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return pd.DataFrame(payload.get("targets", []))
    return pd.read_csv(path)


PRIMARY_SCORE_COLUMNS = {
    "strict": "joint_fit_score",
    "formula": "joint_fit_score_formula",
    "recomputed_mie": "joint_fit_score_recomputed_mie",
    "paper_reproduction_formula": "paper_reproduction_score_formula",
    "paper_reproduction_strict_upper": "paper_reproduction_score_strict_upper",
    "paper_reproduction_snr_response": "paper_reproduction_score_formula_snr_response",
    "paper_reproduction_reviewed": "paper_reproduction_score_reviewed_snr_response",
    "paper_reproduction_maximal_upper": "paper_reproduction_score_maximal_upper",
    "paper_reproduction_response_compression": (
        "paper_reproduction_score_response_compression"
    ),
}


def _primary_score_column(primary_score_mode: str) -> str:
    return PRIMARY_SCORE_COLUMNS.get(primary_score_mode, "joint_fit_score")


def _effective_score_column(frame: pd.DataFrame, primary_score_mode: str) -> str:
    requested = _primary_score_column(primary_score_mode)
    if requested in frame and pd.to_numeric(frame[requested], errors="coerce").notna().any():
        return requested
    if "joint_fit_score" in frame and pd.to_numeric(frame["joint_fit_score"], errors="coerce").notna().any():
        return "joint_fit_score"
    return requested


PRIMARY_REPRODUCTION_FIELD_KEYS = {
    "paper_reproduction_formula": {
        "status": "paper_reproduction_status",
        "score": "paper_reproduction_score_formula",
        "candidate_class": "paper_reproduction_candidate_class",
    },
    "paper_reproduction_strict_upper": {
        "status": "paper_reproduction_status",
        "score": "paper_reproduction_score_strict_upper",
        "candidate_class": "paper_reproduction_candidate_class",
    },
    "paper_reproduction_snr_response": {
        "status": "paper_reproduction_status_snr_response",
        "score": "paper_reproduction_score_formula_snr_response",
        "candidate_class": "paper_reproduction_candidate_class_snr_response",
    },
    "paper_reproduction_reviewed": {
        "status": "paper_reproduction_status_reviewed",
        "score": "paper_reproduction_score_reviewed_snr_response",
        "candidate_class": "paper_reproduction_candidate_class_reviewed",
    },
    "paper_reproduction_maximal_upper": {
        "status": "paper_reproduction_status_maximal_upper",
        "score": "paper_reproduction_score_maximal_upper",
        "candidate_class": "paper_reproduction_candidate_class_maximal_upper",
    },
    "paper_reproduction_response_compression": {
        "status": "paper_reproduction_status_response_compression",
        "score": "paper_reproduction_score_response_compression",
        "candidate_class": "paper_reproduction_candidate_class_response_compression",
    },
}


def _primary_paper_reproduction_fields(
    best: pd.Series,
    primary_score_mode: str,
) -> dict[str, Any]:
    keys = PRIMARY_REPRODUCTION_FIELD_KEYS.get(primary_score_mode)
    if keys is None:
        return {
            "primary_paper_reproduction_status": "",
            "primary_paper_reproduction_score": float("nan"),
            "primary_paper_reproduction_candidate_class": "",
            "primary_paper_reproduction_status_key": "",
            "primary_paper_reproduction_score_key": "",
            "primary_paper_reproduction_candidate_class_key": "",
        }
    status_key = keys["status"]
    score_key = keys["score"]
    class_key = keys["candidate_class"]
    return {
        "primary_paper_reproduction_status": best.get(status_key),
        "primary_paper_reproduction_score": _safe_float(best.get(score_key)),
        "primary_paper_reproduction_candidate_class": best.get(class_key),
        "primary_paper_reproduction_status_key": status_key,
        "primary_paper_reproduction_score_key": score_key,
        "primary_paper_reproduction_candidate_class_key": class_key,
    }


def _row_signal_score(row: pd.Series, target_mode: str) -> float:
    score_column = f"raw_signal_ratio_score_{target_mode}"
    score = _safe_float(row.get(score_column))
    if np.isfinite(score):
        return score
    penalties: list[float] = []
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        observed = _safe_float(row.get(f"ag40_to_au40_peak_ratio_{wavelength_nm}"))
        target = _safe_float(
            row.get(f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}")
        )
        if not np.isfinite(target) or target <= 0:
            target = joint_fit.table_s1_signal_ratio_target(wavelength_nm, target_mode)
        residual = _bounded_log_ratio(observed, target)
        if np.isfinite(residual):
            penalties.append(float(residual**2))
    return float(np.mean(penalties)) if penalties else float("nan")


def _row_signal_score_with_exponent(
    row: pd.Series,
    target_mode: str,
    exponent: float,
) -> float:
    if not (np.isfinite(exponent) and exponent > 0):
        return float("nan")
    penalties: list[float] = []
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        observed = _safe_float(row.get(f"ag40_to_au40_peak_ratio_{wavelength_nm}"))
        target = _safe_float(
            row.get(f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}")
        )
        if not np.isfinite(target) or target <= 0:
            target = joint_fit.table_s1_signal_ratio_target(wavelength_nm, target_mode)
        if np.isfinite(observed) and observed > 0 and np.isfinite(target) and target > 0:
            compressed_observed = float(observed**exponent)
            penalties.append(float(math.log(compressed_observed / target) ** 2))
    return float(np.mean(penalties)) if penalties else float("nan")


def _row_strict_upper_signal_score(row: pd.Series) -> float:
    calibrated_score = _safe_float(row.get("signal_ratio_score"))
    if np.isfinite(calibrated_score):
        return calibrated_score
    return _row_signal_score(row, "interferometric_column_ratio")


def _snr_anchor_metrics(row: pd.Series) -> dict[str, float]:
    raw_values: list[float] = []
    target_values: list[float] = []
    au20_values: list[float] = []
    au30_values: list[float] = []
    for wavelength_nm, width_nm, depth_nm in joint_fit.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        snr20 = _safe_float(row.get(f"au20_{case_key}_mean_local_snr"))
        snr30 = _safe_float(row.get(f"au30_{case_key}_mean_local_snr"))
        if np.isfinite(snr20) and snr20 > 0:
            au20_values.append(snr20)
            raw_values.append(snr20)
            target_values.append(PAPER_AU20_SNR_TARGET)
        if np.isfinite(snr30) and snr30 > 0:
            au30_values.append(snr30)
            raw_values.append(snr30)
            target_values.append(PAPER_AU30_SNR_TARGET)
    if not raw_values:
        return {
            "raw_au20_snr_median": float("nan"),
            "raw_au30_snr_median": float("nan"),
            "fitted_global_snr_scale": float("nan"),
            "scaled_au20_snr_median": float("nan"),
            "scaled_au30_snr_median": float("nan"),
            "snr_anchor_loss": float("nan"),
        }
    log_scale = float(
        np.mean([math.log(target / raw) for raw, target in zip(raw_values, target_values)])
    )
    scale = float(math.exp(log_scale))
    residuals = [
        float(math.log(scale * raw / target) ** 2)
        for raw, target in zip(raw_values, target_values)
    ]
    raw_au20 = float(np.median(au20_values)) if au20_values else float("nan")
    raw_au30 = float(np.median(au30_values)) if au30_values else float("nan")
    return {
        "raw_au20_snr_median": raw_au20,
        "raw_au30_snr_median": raw_au30,
        "fitted_global_snr_scale": scale,
        "scaled_au20_snr_median": float(raw_au20 * scale)
        if np.isfinite(raw_au20)
        else float("nan"),
        "scaled_au30_snr_median": float(raw_au30 * scale)
        if np.isfinite(raw_au30)
        else float("nan"),
        "snr_anchor_loss": float(np.mean(residuals)),
    }


def _snr_response_metrics(row: pd.Series) -> dict[str, float | str]:
    raw_values: list[float] = []
    target_values: list[float] = []
    au20_values: list[float] = []
    au30_values: list[float] = []
    for wavelength_nm, width_nm, depth_nm in joint_fit.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        snr20 = _safe_float(row.get(f"au20_{case_key}_mean_local_snr"))
        snr30 = _safe_float(row.get(f"au30_{case_key}_mean_local_snr"))
        if np.isfinite(snr20) and snr20 > 0:
            au20_values.append(snr20)
            raw_values.append(snr20)
            target_values.append(PAPER_AU20_SNR_TARGET)
        if np.isfinite(snr30) and snr30 > 0:
            au30_values.append(snr30)
            raw_values.append(snr30)
            target_values.append(PAPER_AU30_SNR_TARGET)
    if len(raw_values) < 2:
        return {
            "snr_response_exponent": float("nan"),
            "snr_response_status": "missing",
            "snr_response_scale": float("nan"),
            "snr_response_anchor_loss": float("nan"),
            "snr_response_ratio": float("nan"),
            "snr_response_ratio_loss": float("nan"),
            "snr_response_scaled_au20_snr_median": float("nan"),
            "snr_response_scaled_au30_snr_median": float("nan"),
        }

    x_values = np.log(np.asarray(raw_values, dtype="float64"))
    y_values = np.log(np.asarray(target_values, dtype="float64"))
    x_mean = float(np.mean(x_values))
    y_mean = float(np.mean(y_values))
    x_var = float(np.mean((x_values - x_mean) ** 2))
    fitted_exponent = (
        float(np.mean((x_values - x_mean) * (y_values - y_mean)) / x_var)
        if x_var > 0
        else 1.0
    )
    applied_exponent = float(
        np.clip(
            fitted_exponent,
            REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MIN,
            REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MAX,
        )
    )
    log_scale = float(np.mean(y_values - applied_exponent * x_values))
    scale = float(math.exp(log_scale))
    residuals = y_values - (log_scale + applied_exponent * x_values)
    raw_au20 = float(np.median(au20_values)) if au20_values else float("nan")
    raw_au30 = float(np.median(au30_values)) if au30_values else float("nan")
    scaled_au20 = (
        float(scale * (raw_au20 ** applied_exponent))
        if np.isfinite(raw_au20) and raw_au20 > 0
        else float("nan")
    )
    scaled_au30 = (
        float(scale * (raw_au30 ** applied_exponent))
        if np.isfinite(raw_au30) and raw_au30 > 0
        else float("nan")
    )
    response_ratio = (
        float(scaled_au30 / scaled_au20)
        if np.isfinite(scaled_au20)
        and scaled_au20 > 0
        and np.isfinite(scaled_au30)
        else float("nan")
    )
    response_residual = _bounded_log_ratio(
        response_ratio,
        joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET,
    )
    response_ratio_loss = (
        float((response_residual / 0.20) ** 2)
        if np.isfinite(response_residual)
        else 10.0
    )
    hard_fail = not (
        REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MIN
        <= fitted_exponent
        <= REPRODUCTION_SNR_RESPONSE_EXPONENT_HARD_MAX
    )
    preferred = (
        REPRODUCTION_SNR_RESPONSE_EXPONENT_PREFERRED_MIN
        <= fitted_exponent
        <= REPRODUCTION_SNR_RESPONSE_EXPONENT_PREFERRED_MAX
    )
    return {
        "snr_response_exponent": applied_exponent,
        "snr_response_unclipped_exponent": fitted_exponent,
        "snr_response_status": (
            "hard_fail"
            if hard_fail
            else "bounded_preferred"
            if preferred
            else "maximal_boundary"
        ),
        "snr_response_scale": scale,
        "snr_response_anchor_loss": float(np.mean(residuals**2)),
        "snr_response_ratio": response_ratio,
        "snr_response_ratio_loss": response_ratio_loss,
        "snr_response_scaled_au20_snr_median": scaled_au20,
        "snr_response_scaled_au30_snr_median": scaled_au30,
    }


def _response_compression_snr_metrics(
    row: pd.Series,
    *,
    gamma: float,
) -> dict[str, float]:
    raw_values: list[float] = []
    target_values: list[float] = []
    au20_values: list[float] = []
    au30_values: list[float] = []
    if not (np.isfinite(gamma) and gamma > 0):
        return {
            "response_compression_snr_scale": float("nan"),
            "response_compression_snr_anchor_loss": float("nan"),
            "response_compression_snr_ratio": float("nan"),
            "response_compression_snr_ratio_loss": float("nan"),
            "response_compression_scaled_au20_snr_median": float("nan"),
            "response_compression_scaled_au30_snr_median": float("nan"),
        }
    for wavelength_nm, width_nm, depth_nm in joint_fit.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        snr20 = _safe_float(row.get(f"au20_{case_key}_mean_local_snr"))
        snr30 = _safe_float(row.get(f"au30_{case_key}_mean_local_snr"))
        if np.isfinite(snr20) and snr20 > 0:
            au20_values.append(snr20)
            raw_values.append(snr20)
            target_values.append(PAPER_AU20_SNR_TARGET)
        if np.isfinite(snr30) and snr30 > 0:
            au30_values.append(snr30)
            raw_values.append(snr30)
            target_values.append(PAPER_AU30_SNR_TARGET)
    if len(raw_values) < 2:
        return {
            "response_compression_snr_scale": float("nan"),
            "response_compression_snr_anchor_loss": float("nan"),
            "response_compression_snr_ratio": float("nan"),
            "response_compression_snr_ratio_loss": float("nan"),
            "response_compression_scaled_au20_snr_median": float("nan"),
            "response_compression_scaled_au30_snr_median": float("nan"),
        }

    raw_logs = np.log(np.asarray(raw_values, dtype="float64"))
    target_logs = np.log(np.asarray(target_values, dtype="float64"))
    log_scale = float(np.mean(target_logs - gamma * raw_logs))
    scale = float(math.exp(log_scale))
    residuals = target_logs - (log_scale + gamma * raw_logs)
    raw_au20 = float(np.median(au20_values)) if au20_values else float("nan")
    raw_au30 = float(np.median(au30_values)) if au30_values else float("nan")
    scaled_au20 = (
        float(scale * (raw_au20**gamma))
        if np.isfinite(raw_au20) and raw_au20 > 0
        else float("nan")
    )
    scaled_au30 = (
        float(scale * (raw_au30**gamma))
        if np.isfinite(raw_au30) and raw_au30 > 0
        else float("nan")
    )
    response_ratio = (
        float(scaled_au30 / scaled_au20)
        if np.isfinite(scaled_au20)
        and scaled_au20 > 0
        and np.isfinite(scaled_au30)
        else float("nan")
    )
    response_residual = _bounded_log_ratio(
        response_ratio,
        joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET,
    )
    response_ratio_loss = (
        float((response_residual / 0.20) ** 2)
        if np.isfinite(response_residual)
        else 10.0
    )
    return {
        "response_compression_snr_scale": scale,
        "response_compression_snr_anchor_loss": float(np.mean(residuals**2)),
        "response_compression_snr_ratio": response_ratio,
        "response_compression_snr_ratio_loss": response_ratio_loss,
        "response_compression_scaled_au20_snr_median": scaled_au20,
        "response_compression_scaled_au30_snr_median": scaled_au30,
    }


def _detection_reproduction_loss(detection: dict[str, Any]) -> float:
    if detection.get("release_blocker"):
        return 5.0
    loss = 0.0
    au20_status = str(detection.get("au20_detection_status", ""))
    if au20_status == "Au20_high_outlier_warning":
        loss += 0.5
    for row in detection.get("rows", []):
        if int(row.get("diameter_nm", 0)) == 20:
            continue
        loss += 0.5 * float(row.get("severe_miss_count", 0))
        loss += 0.15 * float(row.get("minor_miss_count", 0))
        loss += 0.05 * float(row.get("borderline_miss_count", 0))
    return float(loss)


def _ag_transfer_complexity(row: pd.Series) -> tuple[float, int]:
    if not _mode_is_active(row.get("joint_signal_transfer_mode")):
        return 0.0, 0
    gains: list[float] = []
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        gain = _safe_float(row.get(f"applied_silver_transfer_gain_{wavelength_nm}"))
        if np.isfinite(gain) and gain > 0:
            gains.append(gain)
    if not gains:
        return 0.0, 0
    return float(0.5 * np.mean([math.log(gain) ** 2 for gain in gains])), len(gains)


def _strict_signal_transfer_upper_metrics(row: pd.Series) -> dict[str, Any]:
    gains: dict[int, float] = {}
    residuals: list[float] = []
    gain_penalties: list[float] = []
    guardrail_penalty = 0.0
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        observed = _safe_float(row.get(f"ag40_to_au40_peak_ratio_{wavelength_nm}"))
        target = _safe_float(
            row.get(
                "ag40_to_au40_target_ratio_interferometric_column_ratio_"
                f"{wavelength_nm}"
            )
        )
        if not np.isfinite(target) or target <= 0:
            target = joint_fit.table_s1_signal_ratio_target(
                wavelength_nm,
                "interferometric_column_ratio",
            )
        if not (
            np.isfinite(observed)
            and observed > 0
            and np.isfinite(target)
            and target > 0
        ):
            return {
                "signal_loss": float("nan"),
                "gain_penalty": 10.0,
                "guardrail_penalty": 100.0,
                "gain_dof": 0,
                "status": "missing",
            }
        gain = float(target / observed)
        gains[wavelength_nm] = gain
        residuals.append(0.0)
        gain_penalties.append(float(math.log(gain) ** 2))
        if gain < joint_fit.MIN_SIGNAL_TRANSFER_GAIN:
            guardrail_penalty += (joint_fit.MIN_SIGNAL_TRANSFER_GAIN / gain - 1.0) ** 2
        if gain > joint_fit.MAX_SIGNAL_TRANSFER_GAIN:
            guardrail_penalty += (gain / joint_fit.MAX_SIGNAL_TRANSFER_GAIN - 1.0) ** 2
    out: dict[str, Any] = {
        "signal_loss": float(np.mean(residuals)) if residuals else float("nan"),
        "gain_penalty": float(0.5 * np.mean(gain_penalties))
        if gain_penalties
        else 10.0,
        "guardrail_penalty": float(guardrail_penalty),
        "gain_dof": len(gains),
        "gain_min": float(min(gains.values())) if gains else float("nan"),
        "gain_max": float(max(gains.values())) if gains else float("nan"),
        "status": "bounded"
        if guardrail_penalty <= 1e-12
        else "gain_guardrail_violation",
    }
    for wavelength_nm, gain in gains.items():
        out[f"gain_{wavelength_nm}"] = gain
    return out


def _paper_reproduction_metrics_for_row(row: pd.Series) -> dict[str, Any]:
    raw_exponent = _safe_float(row.get("au_size_exponent_raw_median"))
    if not np.isfinite(raw_exponent):
        raw_exponent = _safe_float(row.get("au_size_exponent_median"))
    required_delta = (
        joint_fit.AU_SIZE_EXPONENT_TARGET - raw_exponent
        if np.isfinite(raw_exponent)
        else float("nan")
    )
    applied_delta = (
        float(
            np.clip(
                required_delta,
                REPRODUCTION_SIZE_DELTA_HARD_MIN,
                REPRODUCTION_SIZE_DELTA_HARD_MAX,
            )
        )
        if np.isfinite(required_delta)
        else float("nan")
    )
    corrected_exponent = (
        float(raw_exponent + applied_delta)
        if np.isfinite(raw_exponent) and np.isfinite(applied_delta)
        else float("nan")
    )
    size_loss = (
        float(((corrected_exponent - joint_fit.AU_SIZE_EXPONENT_TARGET) / 0.35) ** 2)
        if np.isfinite(corrected_exponent)
        else 10.0
    )
    size_delta_hard_fail = not (
        np.isfinite(required_delta)
        and REPRODUCTION_SIZE_DELTA_HARD_MIN
        <= required_delta
        <= REPRODUCTION_SIZE_DELTA_HARD_MAX
    )
    size_delta_preferred = bool(
        np.isfinite(required_delta)
        and REPRODUCTION_SIZE_DELTA_PREFERRED_MIN
        <= required_delta
        <= REPRODUCTION_SIZE_DELTA_PREFERRED_MAX
    )
    size_delta_status = (
        "hard_fail"
        if size_delta_hard_fail
        else "bounded_preferred"
        if size_delta_preferred
        else "maximal_boundary"
    )

    snr_ratio = _safe_float(row.get("au30_to_au20_snr_ratio_median"))
    snr_residual = _bounded_log_ratio(snr_ratio, joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET)
    snr_ratio_loss = float((snr_residual / 0.20) ** 2) if np.isfinite(snr_residual) else 10.0
    snr_anchor = _snr_anchor_metrics(row)
    snr_anchor_loss = _safe_float(snr_anchor["snr_anchor_loss"])
    if not np.isfinite(snr_anchor_loss):
        snr_anchor_loss = 10.0
    snr_response = _snr_response_metrics(row)
    snr_response_ratio_loss = _safe_float(snr_response["snr_response_ratio_loss"])
    if not np.isfinite(snr_response_ratio_loss):
        snr_response_ratio_loss = 10.0
    snr_response_anchor_loss = _safe_float(snr_response["snr_response_anchor_loss"])
    if not np.isfinite(snr_response_anchor_loss):
        snr_response_anchor_loss = 10.0
    response_compression_gamma_required = (
        joint_fit.AU_SIZE_EXPONENT_TARGET / raw_exponent
        if np.isfinite(raw_exponent) and raw_exponent > 0
        else float("nan")
    )
    response_compression_gamma = (
        float(
            np.clip(
                response_compression_gamma_required,
                REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MIN,
                REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MAX,
            )
        )
        if np.isfinite(response_compression_gamma_required)
        else float("nan")
    )
    response_compression_corrected_exponent = (
        float(raw_exponent * response_compression_gamma)
        if np.isfinite(raw_exponent) and np.isfinite(response_compression_gamma)
        else float("nan")
    )
    response_compression_size_loss = (
        float(
            (
                (
                    response_compression_corrected_exponent
                    - joint_fit.AU_SIZE_EXPONENT_TARGET
                )
                / 0.35
            )
            ** 2
        )
        if np.isfinite(response_compression_corrected_exponent)
        else 10.0
    )
    response_compression_hard_fail = not (
        np.isfinite(response_compression_gamma_required)
        and REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MIN
        <= response_compression_gamma_required
        <= REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_HARD_MAX
    )
    response_compression_preferred = (
        np.isfinite(response_compression_gamma_required)
        and REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_PREFERRED_MIN
        <= response_compression_gamma_required
        <= REPRODUCTION_RESPONSE_COMPRESSION_GAMMA_PREFERRED_MAX
    )
    response_compression_status = (
        "hard_fail"
        if response_compression_hard_fail
        else "bounded_preferred"
        if response_compression_preferred
        else "maximal_boundary"
    )
    response_compression_snr = _response_compression_snr_metrics(
        row,
        gamma=response_compression_gamma,
    )
    response_compression_snr_ratio_loss = _safe_float(
        response_compression_snr["response_compression_snr_ratio_loss"]
    )
    if not np.isfinite(response_compression_snr_ratio_loss):
        response_compression_snr_ratio_loss = 10.0
    response_compression_snr_anchor_loss = _safe_float(
        response_compression_snr["response_compression_snr_anchor_loss"]
    )
    if not np.isfinite(response_compression_snr_anchor_loss):
        response_compression_snr_anchor_loss = 10.0

    formula_signal_loss = _row_signal_score(row, "sqrt_scattering_column_ratio")
    if not np.isfinite(formula_signal_loss):
        formula_signal_loss = 10.0
    strict_signal_loss = _row_signal_score(row, "interferometric_column_ratio")
    if not np.isfinite(strict_signal_loss):
        strict_signal_loss = 10.0
    recomputed_signal_loss = _row_signal_score(row, "recomputed_mie_sqrt_csca_ratio")
    if not np.isfinite(recomputed_signal_loss):
        recomputed_signal_loss = 10.0
    response_compression_formula_signal_loss = _row_signal_score_with_exponent(
        row,
        "sqrt_scattering_column_ratio",
        response_compression_gamma,
    )
    if not np.isfinite(response_compression_formula_signal_loss):
        response_compression_formula_signal_loss = 10.0
    response_compression_strict_signal_loss = _row_signal_score_with_exponent(
        row,
        "interferometric_column_ratio",
        response_compression_gamma,
    )
    if not np.isfinite(response_compression_strict_signal_loss):
        response_compression_strict_signal_loss = 10.0
    response_compression_recomputed_signal_loss = _row_signal_score_with_exponent(
        row,
        "recomputed_mie_sqrt_csca_ratio",
        response_compression_gamma,
    )
    if not np.isfinite(response_compression_recomputed_signal_loss):
        response_compression_recomputed_signal_loss = 10.0
    strict_upper_signal_loss = _row_strict_upper_signal_score(row)
    if not np.isfinite(strict_upper_signal_loss):
        strict_upper_signal_loss = strict_signal_loss

    detection = detection_band_status(row)
    detection_loss = _detection_reproduction_loss(detection)
    ag_transfer_penalty, ag_transfer_dof = _ag_transfer_complexity(row)
    strict_transfer_upper = _strict_signal_transfer_upper_metrics(row)
    strict_transfer_upper_signal_loss = _safe_float(
        strict_transfer_upper["signal_loss"]
    )
    if not np.isfinite(strict_transfer_upper_signal_loss):
        strict_transfer_upper_signal_loss = strict_signal_loss
    strict_transfer_upper_penalty = _safe_float(
        strict_transfer_upper["gain_penalty"]
    )
    if not np.isfinite(strict_transfer_upper_penalty):
        strict_transfer_upper_penalty = 10.0
    strict_transfer_upper_guardrail_penalty = _safe_float(
        strict_transfer_upper["guardrail_penalty"]
    )
    if not np.isfinite(strict_transfer_upper_guardrail_penalty):
        strict_transfer_upper_guardrail_penalty = 100.0
    snr_scale = _safe_float(snr_anchor["fitted_global_snr_scale"])
    snr_scale_penalty = (
        float(0.2 * math.log(snr_scale) ** 2)
        if np.isfinite(snr_scale) and snr_scale > 0
        else 0.0
    )
    snr_response_scale = _safe_float(snr_response["snr_response_scale"])
    snr_response_scale_penalty = (
        float(0.2 * math.log(snr_response_scale) ** 2)
        if np.isfinite(snr_response_scale) and snr_response_scale > 0
        else 0.0
    )
    snr_response_exponent = _safe_float(snr_response["snr_response_exponent"])
    snr_response_exponent_penalty = (
        float(0.6 * ((snr_response_exponent - 1.0) / 0.20) ** 2)
        if np.isfinite(snr_response_exponent)
        else 10.0
    )
    response_compression_scale = _safe_float(
        response_compression_snr["response_compression_snr_scale"]
    )
    response_compression_scale_penalty = (
        float(0.2 * math.log(response_compression_scale) ** 2)
        if np.isfinite(response_compression_scale)
        and response_compression_scale > 0
        else 0.0
    )
    response_compression_gamma_penalty = (
        float(0.8 * ((1.0 - response_compression_gamma) / 0.25) ** 2)
        if np.isfinite(response_compression_gamma)
        else 10.0
    )
    size_complexity_penalty = (
        float(0.8 * (applied_delta / 0.75) ** 2)
        if np.isfinite(applied_delta)
        else 10.0
    )
    fit_complexity_penalty = (
        size_complexity_penalty + snr_scale_penalty + ag_transfer_penalty
    )
    fit_complexity_penalty_snr_response = (
        size_complexity_penalty
        + snr_response_scale_penalty
        + snr_response_exponent_penalty
        + ag_transfer_penalty
    )
    fit_complexity_penalty_response_compression = (
        response_compression_gamma_penalty
        + response_compression_scale_penalty
        + ag_transfer_penalty
    )
    hard_guardrail_penalty = _safe_float(row.get("hard_guardrail_penalty"))
    if not np.isfinite(hard_guardrail_penalty):
        hard_guardrail_penalty = 0.0
    existing_size_guardrail_penalty = _safe_float(row.get("size_response_guardrail_penalty"))
    if not np.isfinite(existing_size_guardrail_penalty):
        existing_size_guardrail_penalty = 0.0
    transfer_guardrail_penalty = _safe_float(row.get("transfer_gain_guardrail_penalty"))
    if not np.isfinite(transfer_guardrail_penalty):
        transfer_guardrail_penalty = 0.0
    reproduction_guardrail_penalty = (
        100.0 * float(size_delta_hard_fail)
        + hard_guardrail_penalty
        + transfer_guardrail_penalty
        + max(0.0, existing_size_guardrail_penalty)
        + 5.0 * float(bool(detection.get("release_blocker")))
    )
    snr_response_hard_fail = (
        str(snr_response["snr_response_status"]) == "hard_fail"
    )
    reproduction_guardrail_penalty_snr_response = (
        reproduction_guardrail_penalty + 100.0 * float(snr_response_hard_fail)
    )
    reproduction_guardrail_penalty_maximal_upper = (
        reproduction_guardrail_penalty_snr_response
        + strict_transfer_upper_guardrail_penalty
    )
    reproduction_guardrail_penalty_response_compression = (
        reproduction_guardrail_penalty
        + 100.0 * float(response_compression_hard_fail)
    )

    paper_reproduction_score_formula = float(
        4.0 * size_loss
        + 3.0 * snr_ratio_loss
        + 1.0 * snr_anchor_loss
        + 1.5 * detection_loss
        + 1.0 * formula_signal_loss
        + 0.2 * strict_signal_loss
        + 1.2 * fit_complexity_penalty
        + reproduction_guardrail_penalty
    )
    paper_reproduction_score_strict_upper = float(
        4.0 * size_loss
        + 3.0 * snr_ratio_loss
        + 1.0 * snr_anchor_loss
        + 1.5 * detection_loss
        + 0.2 * formula_signal_loss
        + 1.0 * strict_upper_signal_loss
        + 1.2 * fit_complexity_penalty
        + reproduction_guardrail_penalty
    )
    paper_reproduction_score_formula_snr_response = float(
        4.0 * size_loss
        + 3.0 * snr_response_ratio_loss
        + 1.0 * snr_response_anchor_loss
        + 1.5 * detection_loss
        + 1.0 * formula_signal_loss
        + 0.2 * strict_signal_loss
        + 1.2 * fit_complexity_penalty_snr_response
        + reproduction_guardrail_penalty_snr_response
    )
    paper_reproduction_score_reviewed_snr_response = float(
        4.0 * size_loss
        + 3.0 * snr_response_ratio_loss
        + 1.0 * snr_response_anchor_loss
        + 0.5 * detection_loss
        + 1.0 * formula_signal_loss
        + 0.6 * fit_complexity_penalty_snr_response
        + reproduction_guardrail_penalty_snr_response
    )
    paper_reproduction_fit_complexity_penalty_maximal_upper = (
        fit_complexity_penalty_snr_response + strict_transfer_upper_penalty
    )
    paper_reproduction_score_maximal_upper = float(
        4.0 * size_loss
        + 3.0 * snr_response_ratio_loss
        + 1.0 * snr_response_anchor_loss
        + 0.2 * detection_loss
        + 0.2 * formula_signal_loss
        + 1.0 * strict_transfer_upper_signal_loss
        + 0.3 * paper_reproduction_fit_complexity_penalty_maximal_upper
        + reproduction_guardrail_penalty_maximal_upper
    )
    paper_reproduction_score_response_compression = float(
        4.0 * response_compression_size_loss
        + 3.0 * response_compression_snr_ratio_loss
        + 1.0 * response_compression_snr_anchor_loss
        + 0.5 * detection_loss
        + 1.0 * response_compression_formula_signal_loss
        + 0.6 * fit_complexity_penalty_response_compression
        + reproduction_guardrail_penalty_response_compression
    )

    fit_dof_count = 1 + 1 + ag_transfer_dof
    fit_dof_count_snr_response = 1 + 1 + 1 + ag_transfer_dof
    fit_dof_count_maximal_upper = (
        fit_dof_count_snr_response + int(strict_transfer_upper.get("gain_dof", 0))
    )
    fit_dof_count_response_compression = 1 + 1 + ag_transfer_dof
    uses_signal_transfer = _mode_is_active(row.get("joint_signal_transfer_mode"))
    if size_delta_hard_fail or uses_signal_transfer:
        candidate_class = "maximal_paper_fit"
    elif size_delta_preferred:
        candidate_class = "bounded_reproduction_fit"
    else:
        candidate_class = "maximal_paper_fit"
    snr_response_preferred = (
        str(snr_response["snr_response_status"]) == "bounded_preferred"
    )
    if size_delta_hard_fail or snr_response_hard_fail or uses_signal_transfer:
        candidate_class_snr_response = "maximal_paper_fit"
    elif size_delta_preferred and snr_response_preferred:
        candidate_class_snr_response = "bounded_reproduction_fit"
    else:
        candidate_class_snr_response = "maximal_paper_fit"
    if response_compression_hard_fail or uses_signal_transfer:
        candidate_class_response_compression = "maximal_paper_fit"
    elif response_compression_preferred:
        candidate_class_response_compression = "bounded_reproduction_fit"
    else:
        candidate_class_response_compression = "maximal_paper_fit"
    if reproduction_guardrail_penalty >= 100.0:
        status = "fail_guardrail"
    elif candidate_class == "bounded_reproduction_fit" and paper_reproduction_score_formula <= 1.0:
        status = "bounded_reproduction_pass"
    elif candidate_class == "bounded_reproduction_fit" and paper_reproduction_score_formula <= 2.0:
        status = "bounded_reproduction_partial"
    elif paper_reproduction_score_formula <= 1.0:
        status = "maximal_paper_fit_upper_bound"
    else:
        status = "reproduction_fit_not_met"
    if reproduction_guardrail_penalty_snr_response >= 100.0:
        status_snr_response = "fail_guardrail"
    elif (
        candidate_class_snr_response == "bounded_reproduction_fit"
        and paper_reproduction_score_formula_snr_response <= 1.0
    ):
        status_snr_response = "bounded_reproduction_pass"
    elif (
        candidate_class_snr_response == "bounded_reproduction_fit"
        and paper_reproduction_score_formula_snr_response <= 2.0
    ):
        status_snr_response = "bounded_reproduction_partial"
    elif paper_reproduction_score_formula_snr_response <= 1.0:
        status_snr_response = "maximal_paper_fit_upper_bound"
    else:
        status_snr_response = "reproduction_fit_not_met"
    if reproduction_guardrail_penalty_snr_response >= 100.0:
        status_reviewed = "fail_guardrail_descriptive"
    elif (
        candidate_class_snr_response == "bounded_reproduction_fit"
        and paper_reproduction_score_reviewed_snr_response <= 1.0
    ):
        status_reviewed = "bounded_reproduction_pass_descriptive"
    elif (
        candidate_class_snr_response == "bounded_reproduction_fit"
        and paper_reproduction_score_reviewed_snr_response <= 2.0
    ):
        status_reviewed = "bounded_reproduction_partial_descriptive"
    elif paper_reproduction_score_reviewed_snr_response <= 1.0:
        status_reviewed = "maximal_paper_fit_upper_bound_descriptive"
    else:
        status_reviewed = "reproduction_fit_not_met_descriptive"
    if reproduction_guardrail_penalty_maximal_upper >= 100.0:
        status_maximal_upper = "fail_guardrail_upper_bound"
    elif paper_reproduction_score_maximal_upper <= 1.0:
        status_maximal_upper = "maximal_paper_fit_upper_bound"
    elif paper_reproduction_score_maximal_upper <= 2.0:
        status_maximal_upper = "maximal_paper_fit_partial_upper_bound"
    else:
        status_maximal_upper = "maximal_paper_fit_not_met"
    if reproduction_guardrail_penalty_response_compression >= 100.0:
        status_response_compression = "fail_guardrail_response_compression"
    elif (
        candidate_class_response_compression == "bounded_reproduction_fit"
        and paper_reproduction_score_response_compression <= 1.0
    ):
        status_response_compression = "bounded_response_compression_pass_descriptive"
    elif (
        candidate_class_response_compression == "bounded_reproduction_fit"
        and paper_reproduction_score_response_compression <= 2.0
    ):
        status_response_compression = "bounded_response_compression_partial_descriptive"
    elif paper_reproduction_score_response_compression <= 1.0:
        status_response_compression = "maximal_response_compression_upper_bound"
    else:
        status_response_compression = "response_compression_fit_not_met"

    out: dict[str, Any] = {
        "paper_reproduction_candidate_class": candidate_class,
        "paper_reproduction_status": status,
        "paper_reproduction_claim_level": "paper_reproduction_fit_only",
        "paper_reproduction_accepted_raw_calibration": False,
        "paper_reproduction_ev_full_grid_writeback": False,
        "paper_reproduction_selected_annulus_changed": False,
        "paper_reproduction_global_material_defaults_changed": False,
        "paper_reproduction_score_formula": paper_reproduction_score_formula,
        "paper_reproduction_score_strict_upper": paper_reproduction_score_strict_upper,
        "paper_reproduction_score_formula_snr_response": (
            paper_reproduction_score_formula_snr_response
        ),
        "paper_reproduction_score_reviewed_snr_response": (
            paper_reproduction_score_reviewed_snr_response
        ),
        "paper_reproduction_score_maximal_upper": (
            paper_reproduction_score_maximal_upper
        ),
        "paper_reproduction_score_response_compression": (
            paper_reproduction_score_response_compression
        ),
        "paper_reproduction_candidate_class_snr_response": (
            candidate_class_snr_response
        ),
        "paper_reproduction_status_snr_response": status_snr_response,
        "paper_reproduction_candidate_class_reviewed": (
            candidate_class_snr_response
        ),
        "paper_reproduction_status_reviewed": status_reviewed,
        "paper_reproduction_candidate_class_maximal_upper": "maximal_paper_fit",
        "paper_reproduction_status_maximal_upper": status_maximal_upper,
        "paper_reproduction_candidate_class_response_compression": (
            candidate_class_response_compression
        ),
        "paper_reproduction_status_response_compression": status_response_compression,
        "paper_reproduction_reviewed_score_interpretation": (
            "descriptive_rescore_only_strict_table_s1_reported_not_scored"
        ),
        "paper_reproduction_maximal_upper_score_interpretation": (
            "strict_table_s1_upper_bound_with_hypothetical_per_wavelength_ag_transfer"
        ),
        "paper_reproduction_response_compression_score_interpretation": (
            "single_global_pulse_height_readout_compression_reproduction_only"
        ),
        "paper_reproduction_response_compression_size_fit_note": (
            "gamma_is_solved_from_target_over_raw_exponent;"
            "residual_test_is_snr_signal_detection_complexity"
        ),
        "paper_reproduction_size_exponent_loss": size_loss,
        "paper_reproduction_snr_ratio_loss": snr_ratio_loss,
        "paper_reproduction_snr_anchor_loss": snr_anchor_loss,
        "paper_reproduction_snr_response_ratio_loss": snr_response_ratio_loss,
        "paper_reproduction_snr_response_anchor_loss": snr_response_anchor_loss,
        "paper_reproduction_response_compression_size_loss": (
            response_compression_size_loss
        ),
        "paper_reproduction_response_compression_snr_ratio_loss": (
            response_compression_snr_ratio_loss
        ),
        "paper_reproduction_response_compression_snr_anchor_loss": (
            response_compression_snr_anchor_loss
        ),
        "paper_reproduction_response_compression_formula_signal_loss": (
            response_compression_formula_signal_loss
        ),
        "paper_reproduction_response_compression_strict_signal_loss": (
            response_compression_strict_signal_loss
        ),
        "paper_reproduction_response_compression_recomputed_mie_signal_loss": (
            response_compression_recomputed_signal_loss
        ),
        "paper_reproduction_detection_loss": detection_loss,
        "paper_reproduction_formula_signal_loss": formula_signal_loss,
        "paper_reproduction_strict_signal_diagnostic_loss": strict_signal_loss,
        "paper_reproduction_recomputed_mie_signal_loss": recomputed_signal_loss,
        "paper_reproduction_strict_upper_signal_loss": strict_upper_signal_loss,
        "paper_reproduction_fit_complexity_penalty": fit_complexity_penalty,
        "paper_reproduction_fit_complexity_penalty_snr_response": (
            fit_complexity_penalty_snr_response
        ),
        "paper_reproduction_fit_complexity_penalty_maximal_upper": (
            paper_reproduction_fit_complexity_penalty_maximal_upper
        ),
        "paper_reproduction_fit_complexity_penalty_response_compression": (
            fit_complexity_penalty_response_compression
        ),
        "paper_reproduction_size_complexity_penalty": size_complexity_penalty,
        "paper_reproduction_snr_response_exponent_complexity_penalty": (
            snr_response_exponent_penalty
        ),
        "paper_reproduction_response_compression_gamma_complexity_penalty": (
            response_compression_gamma_penalty
        ),
        "paper_reproduction_ag_transfer_complexity_penalty": ag_transfer_penalty,
        "paper_reproduction_strict_upper_ag_transfer_complexity_penalty": (
            strict_transfer_upper_penalty
        ),
        "paper_reproduction_guardrail_penalty": reproduction_guardrail_penalty,
        "paper_reproduction_guardrail_penalty_snr_response": (
            reproduction_guardrail_penalty_snr_response
        ),
        "paper_reproduction_guardrail_penalty_maximal_upper": (
            reproduction_guardrail_penalty_maximal_upper
        ),
        "paper_reproduction_guardrail_penalty_response_compression": (
            reproduction_guardrail_penalty_response_compression
        ),
        "paper_reproduction_fit_dof_count": fit_dof_count,
        "paper_reproduction_fit_dof_count_snr_response": fit_dof_count_snr_response,
        "paper_reproduction_fit_dof_count_maximal_upper": (
            fit_dof_count_maximal_upper
        ),
        "paper_reproduction_fit_dof_count_response_compression": (
            fit_dof_count_response_compression
        ),
        "paper_reproduction_size_delta_status": size_delta_status,
        "paper_reproduction_required_au_size_response_exponent_delta": required_delta,
        "paper_reproduction_applied_au_size_response_exponent_delta": applied_delta,
        "paper_reproduction_corrected_au_size_exponent": corrected_exponent,
        "paper_reproduction_size_delta_scope": (
            "global_all_wavelengths_all_geometries_all_Au_sizes"
        ),
        "paper_reproduction_snr_scale_mode": "single_global_scale",
        "paper_reproduction_snr_response_mode": (
            "single_global_power_law_exponent_plus_scale"
        ),
        "paper_reproduction_response_compression_mode": (
            "single_global_pulse_height_readout_power_law_exponent_plus_scale"
        ),
        "paper_reproduction_response_compression_gamma_status": (
            response_compression_status
        ),
        "paper_reproduction_required_response_compression_gamma": (
            response_compression_gamma_required
        ),
        "paper_reproduction_applied_response_compression_gamma": (
            response_compression_gamma
        ),
        "paper_reproduction_response_compression_corrected_au_size_exponent": (
            response_compression_corrected_exponent
        ),
        "paper_reproduction_target_signal_primary_mode": (
            "sqrt_scattering_column_ratio"
        ),
        "paper_reproduction_strict_table_s1_status": (
            "diagnostic_warning"
            if strict_signal_loss > 0.05 and formula_signal_loss <= 0.05
            else "aligned_or_not_evaluated"
            if strict_signal_loss <= 0.05
            else "diagnostic_fail"
        ),
        "paper_reproduction_strict_upper_ag_transfer_status": (
            strict_transfer_upper["status"]
        ),
        "paper_reproduction_strict_upper_signal_loss_after_transfer": (
            strict_transfer_upper_signal_loss
        ),
        "paper_reproduction_strict_upper_ag_transfer_gain_min": (
            strict_transfer_upper.get("gain_min")
        ),
        "paper_reproduction_strict_upper_ag_transfer_gain_max": (
            strict_transfer_upper.get("gain_max")
        ),
    }
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        out[
            f"paper_reproduction_strict_upper_ag_transfer_gain_{wavelength_nm}"
        ] = strict_transfer_upper.get(f"gain_{wavelength_nm}")
    out.update({f"paper_reproduction_{key}": value for key, value in snr_anchor.items()})
    out.update({f"paper_reproduction_{key}": value for key, value in snr_response.items()})
    out.update(
        {
            f"paper_reproduction_{key}": value
            for key, value in response_compression_snr.items()
        }
    )
    return out


def add_paper_reproduction_metrics(joint_summary: pd.DataFrame) -> pd.DataFrame:
    if joint_summary.empty:
        return joint_summary.copy()
    out = joint_summary.copy()
    metric_rows = [
        _paper_reproduction_metrics_for_row(row)
        for _, row in out.iterrows()
    ]
    metric_frame = pd.DataFrame(metric_rows, index=out.index)
    for column in metric_frame.columns:
        out[column] = metric_frame[column]
    return out


def _best_joint_candidate(
    joint_summary: pd.DataFrame,
    *,
    primary_score_mode: str = "strict",
) -> pd.Series:
    if joint_summary.empty:
        raise ValueError("joint summary is empty")
    score_column = _effective_score_column(joint_summary, primary_score_mode)
    if score_column in joint_summary:
        sort_columns = [score_column]
        if "candidate_id" in joint_summary:
            sort_columns.append("candidate_id")
        ranked = joint_summary.sort_values(sort_columns)
        return ranked.iloc[0]
    if "joint_fit_score" in joint_summary:
        sort_columns = ["joint_fit_score"]
        if "candidate_id" in joint_summary:
            sort_columns.append("candidate_id")
        ranked = joint_summary.sort_values(sort_columns)
        return ranked.iloc[0]
    return joint_summary.iloc[0]


def _unique_status(values: pd.Series) -> Any:
    present = sorted(
        {
            str(value)
            for value in values.dropna().tolist()
            if _normalized_text(value) != ""
        }
    )
    if not present:
        return ""
    if len(present) == 1:
        return present[0]
    return "mixed:" + "|".join(present)


def _aggregate_candidate_group(group: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in group.columns:
        series = group[column]
        if column in {"candidate_id", "family_id", "family_description"}:
            out[column] = _unique_status(series)
            continue
        if column in {"source_seed_count", "source_row_count", "seed_aggregation_status"}:
            continue
        if column in {
            "reference_bad",
            "rho_bad",
            "na_cutoff_active",
            "paper_reproduction_accepted_raw_calibration",
            "paper_reproduction_ev_full_grid_writeback",
            "paper_reproduction_selected_annulus_changed",
            "paper_reproduction_global_material_defaults_changed",
        }:
            out[column] = bool(series.apply(_safe_bool).any())
            continue
        if column == "selected_rate_all_bands_hit":
            out[column] = bool(series.apply(_safe_bool).all())
            continue
        if column in {
            "paper_fit_status",
            "joint_signal_transfer_mode",
            "joint_size_response_mode",
            "signal_ratio_target_mode",
            "base_candidate_id",
            "scenario_config_id",
            "target_schema_id",
            "joint_candidate_rationale",
            "joint_fit_score_interpretation",
            "au_size_exponent_scored_observable",
            "au_size_exponent_best_observable",
            "au_size_exponent_diagnostic_status",
            "joint_cfg_overrides_json",
            "paper_reproduction_candidate_class",
            "paper_reproduction_status",
            "paper_reproduction_claim_level",
            "paper_reproduction_size_delta_status",
            "paper_reproduction_size_delta_scope",
            "paper_reproduction_snr_scale_mode",
            "paper_reproduction_target_signal_primary_mode",
            "paper_reproduction_strict_table_s1_status",
        }:
            out[column] = _unique_status(series)
            continue
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            if column == "annulus_fraction_min":
                out[column] = float(numeric.min())
            elif column.endswith("_guardrail_penalty") or column in {
                "hard_guardrail_penalty",
                "transfer_gain_guardrail_penalty",
                "size_response_guardrail_penalty",
            }:
                out[column] = float(numeric.max())
            elif column == "random_seed":
                out[column] = "seed_median"
            elif column.endswith("_count") or column.endswith("_rows"):
                out[column] = int(numeric.max())
            else:
                out[column] = float(numeric.median())
            continue
        out[column] = _unique_status(series)
    if "candidate_id" not in out and "candidate_id" in group:
        out["candidate_id"] = str(group["candidate_id"].iloc[0])
    if "family_id" not in out and "family_id" in group:
        out["family_id"] = str(group["family_id"].iloc[0])
    out["source_seed_count"] = int(
        pd.to_numeric(group.get("random_seed"), errors="coerce").dropna().nunique()
    ) if "random_seed" in group else 0
    out["source_row_count"] = int(len(group))
    out["seed_aggregation_status"] = "candidate_seed_median"
    return out


def seed_median_acceptance_frame(
    joint_summary: pd.DataFrame,
    *,
    primary_score_mode: str = "strict",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    has_seed_candidates = {"candidate_id", "random_seed"}.issubset(joint_summary.columns)
    if not has_seed_candidates:
        return joint_summary.copy(), {
            "acceptance_aggregation_mode": "single_row_or_baseline",
            "source_rows": int(len(joint_summary)),
            "aggregated_rows": int(len(joint_summary)),
        }
    group_cols = ["candidate_id"]
    if "family_id" in joint_summary.columns:
        group_cols.insert(0, "family_id")
    rows = [
        _aggregate_candidate_group(group)
        for _, group in joint_summary.groupby(group_cols, dropna=False)
    ]
    aggregated = pd.DataFrame(rows)
    score_column = _effective_score_column(aggregated, primary_score_mode)
    if score_column in aggregated:
        sort_columns = [score_column]
        if "candidate_id" in aggregated:
            sort_columns.append("candidate_id")
        aggregated = aggregated.sort_values(
            sort_columns,
            ignore_index=True,
        )
    elif "joint_fit_score" in aggregated:
        sort_columns = ["joint_fit_score"]
        if "candidate_id" in aggregated:
            sort_columns.append("candidate_id")
        aggregated = aggregated.sort_values(
            sort_columns,
            ignore_index=True,
        )
    return aggregated, {
        "acceptance_aggregation_mode": "candidate_seed_median",
        "source_rows": int(len(joint_summary)),
        "aggregated_rows": int(len(aggregated)),
        "candidate_count": int(joint_summary["candidate_id"].nunique()),
        "seed_count": int(
            pd.to_numeric(joint_summary["random_seed"], errors="coerce").dropna().nunique()
        ),
    }


def _uses_local_paper_fit(row: pd.Series) -> bool:
    return (
        _mode_is_active(row.get("joint_signal_transfer_mode"))
        or _mode_is_active(row.get("joint_size_response_mode"))
        or "signal_size_transfer_fit" in _normalized_text(row.get("candidate_id"))
    )


def inverse_context_status(joint_summary: pd.DataFrame, best: pd.Series) -> dict[str, Any]:
    has_family_ladder = "family_id" in joint_summary.columns
    seed_count = 0
    if "random_seed" in joint_summary.columns:
        seed_count = int(pd.to_numeric(joint_summary["random_seed"], errors="coerce").dropna().nunique())
    candidate_count = (
        int(joint_summary["candidate_id"].nunique())
        if "candidate_id" in joint_summary.columns
        else int(len(joint_summary))
    )
    best_candidate_rows = joint_summary
    if "candidate_id" in joint_summary.columns:
        best_candidate_rows = joint_summary[
            joint_summary["candidate_id"].astype(str) == str(best.get("candidate_id"))
        ]
    best_seed_count = 0
    if "random_seed" in best_candidate_rows.columns:
        best_seed_count = int(
            pd.to_numeric(best_candidate_rows["random_seed"], errors="coerce").dropna().nunique()
        )
    status_values = (
        sorted(best_candidate_rows["paper_fit_status"].dropna().astype(str).unique().tolist())
        if "paper_fit_status" in best_candidate_rows.columns
        else []
    )
    mode_values: dict[str, list[str]] = {}
    for column in ("joint_signal_transfer_mode", "joint_size_response_mode"):
        if column in best_candidate_rows.columns:
            mode_values[column] = sorted(
                best_candidate_rows[column].dropna().astype(str).unique().tolist()
            )
    return {
        "status": "available" if has_family_ladder else "baseline_only",
        "has_family_ladder": bool(has_family_ladder),
        "candidate_count": candidate_count,
        "seed_count": seed_count,
        "best_candidate_seed_count": best_seed_count,
        "best_candidate_status_values": status_values,
        "best_candidate_mode_values": mode_values,
        "best_candidate_multi_seed_stable": bool(
            (not has_family_ladder)
            or (
                best_seed_count >= 3
                and len(status_values) <= 1
                and all(len(values) <= 1 for values in mode_values.values())
            )
        ),
    }


def raw_family_alignment_status(joint_summary: pd.DataFrame) -> dict[str, Any]:
    if "family_id" not in joint_summary.columns:
        return {
            "status": "not_evaluated",
            "notes": "family-ladder inverse summary not provided",
        }
    local_fit_mask = joint_summary.apply(_uses_local_paper_fit, axis=1)
    raw = joint_summary[~local_fit_mask].copy()
    if raw.empty:
        return {
            "status": "fail",
            "raw_candidate_count": 0,
            "notes": "no raw/non-transfer family candidates available",
        }
    hard_penalty = _numeric_column(raw, "hard_guardrail_penalty", 0.0).fillna(0.0)
    raw = raw[hard_penalty <= 1e-12]
    if raw.empty:
        return {
            "status": "fail",
            "raw_candidate_count": 0,
            "notes": "all raw/non-transfer family candidates violate hard guardrails",
        }

    def row_signal_score(row: pd.Series, target_mode: str) -> float:
        penalties: list[float] = []
        for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
            observed = _safe_float(row.get(f"ag40_to_au40_peak_ratio_{wavelength_nm}"))
            target = _safe_float(
                row.get(f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}")
            )
            if not np.isfinite(target) or target <= 0:
                target = joint_fit.table_s1_signal_ratio_target(wavelength_nm, target_mode)
            if np.isfinite(observed) and observed > 0 and np.isfinite(target) and target > 0:
                penalties.append(float(math.log(observed / target) ** 2))
        return float(np.mean(penalties)) if penalties else float("nan")

    strict_signal_score = _numeric_column(raw, "signal_ratio_score")
    formula_signal_score = raw.apply(
        lambda row: row_signal_score(row, "sqrt_scattering_column_ratio"),
        axis=1,
    )
    raw_size_exponent = _numeric_column(raw, "au_size_exponent_raw_median")
    size_score = _numeric_column(raw, "size_exponent_score")
    strict_signal_aligned = strict_signal_score <= 0.05
    formula_signal_aligned = formula_signal_score <= 0.05
    source_audited_signal_aligned = strict_signal_aligned | formula_signal_aligned
    size_aligned = (
        raw_size_exponent.sub(joint_fit.AU_SIZE_EXPONENT_TARGET).abs() <= 0.4
    ) | (size_score <= 0.16)
    strict_joint_aligned = strict_signal_aligned & size_aligned
    formula_joint_aligned = formula_signal_aligned & size_aligned
    joint_aligned = source_audited_signal_aligned & size_aligned

    if bool(strict_signal_aligned.any()):
        signal_status = "pass_strict_interferometric_column_target"
    elif bool(formula_signal_aligned.any()):
        signal_status = "pass_formula_consistent_table_s1_target_only"
    else:
        signal_status = "fail_strict_and_formula_consistent_targets"

    return {
        "status": "pass" if bool(joint_aligned.any()) else "fail",
        "raw_candidate_count": int(len(raw)),
        "raw_signal_ratio_alignment_status": signal_status,
        "raw_size_response_alignment_status": "pass" if bool(size_aligned.any()) else "fail",
        "raw_strict_signal_aligned_count": int(strict_signal_aligned.fillna(False).sum()),
        "raw_formula_signal_aligned_count": int(formula_signal_aligned.fillna(False).sum()),
        "raw_size_aligned_count": int(size_aligned.fillna(False).sum()),
        "raw_joint_strict_signal_size_aligned_count": int(
            strict_joint_aligned.fillna(False).sum()
        ),
        "raw_joint_formula_signal_size_aligned_count": int(
            formula_joint_aligned.fillna(False).sum()
        ),
        "raw_joint_signal_size_aligned_count": int(joint_aligned.fillna(False).sum()),
        "best_raw_joint_fit_score": float(_numeric_column(raw, "joint_fit_score").min())
        if "joint_fit_score" in raw
        else float("nan"),
        "best_raw_strict_signal_ratio_score": float(strict_signal_score.min()),
        "best_raw_formula_signal_ratio_score": float(formula_signal_score.min()),
        "best_raw_signal_ratio_score": float(strict_signal_score.min()),
        "best_raw_size_exponent_score": float(size_score.min()),
        "notes": "raw families must show signal/size alignment before local paper-fit transfer can be signed",
    }


def classify_detection_band_value(value: float, low: float, high: float) -> str:
    if not np.isfinite(value):
        return "missing"
    if value < low - DETECTION_BAND_SEVERE_EPS:
        return "severe_low_miss"
    if value < low - DETECTION_BAND_EPS:
        return "minor_low_miss"
    if value < low:
        return "borderline_low_miss"
    if value > high + DETECTION_BAND_SEVERE_EPS:
        return "severe_high_miss"
    if value > high + DETECTION_BAND_EPS:
        return "minor_high_miss"
    if value > high:
        return "borderline_high_miss"
    return "in_band"


def detection_band_status(best: pd.Series) -> dict[str, Any]:
    def diameter_row(diameter_nm: int) -> dict[str, Any]:
        target = joint_fit.DETECTION_RATE_TARGETS[diameter_nm]
        values: list[float] = []
        labels: list[str] = []
        case_hits = 0
        case_total = 0
        low_miss_count = 0
        high_miss_count = 0
        for wavelength_nm, width_nm, depth_nm in joint_fit.JOINT_CASES:
            column = (
                f"au{diameter_nm}_{wavelength_nm}_{width_nm}x{depth_nm}"
                "_selected_annulus_rate"
            )
            value = _safe_float(best.get(column))
            if np.isfinite(value):
                values.append(value)
                label = classify_detection_band_value(value, target["low"], target["high"])
                labels.append(label)
                case_total += 1
                if label == "in_band":
                    case_hits += 1
                if value < target["low"]:
                    low_miss_count += 1
                if value > target["high"]:
                    high_miss_count += 1
        median_value = float(np.median(values)) if values else float("nan")
        median_label = classify_detection_band_value(
            median_value,
            target["low"],
            target["high"],
        )
        severe_miss_count = sum(label.startswith("severe") for label in labels)
        minor_miss_count = sum(label.startswith("minor") for label in labels)
        borderline_miss_count = sum(label.startswith("borderline") for label in labels)
        severe_high_miss_count = sum(label == "severe_high_miss" for label in labels)
        minor_high_miss_count = sum(label == "minor_high_miss" for label in labels)
        borderline_high_miss_count = sum(
            label == "borderline_high_miss" for label in labels
        )
        return {
            "diameter_nm": diameter_nm,
            "median_selected_annulus_rate": median_value,
            "band_low": target["low"],
            "band_high": target["high"],
            "target": target["target"],
            "case_hits": case_hits,
            "case_total": case_total,
            "low_miss_count": low_miss_count,
            "high_miss_count": high_miss_count,
            "median_band_label": median_label,
            "severe_miss_count": severe_miss_count,
            "minor_miss_count": minor_miss_count,
            "borderline_miss_count": borderline_miss_count,
            "severe_high_miss_count": severe_high_miss_count,
            "minor_high_miss_count": minor_high_miss_count,
            "borderline_high_miss_count": borderline_high_miss_count,
        }

    rows: list[dict[str, Any]] = []
    for diameter_nm, target in joint_fit.DETECTION_RATE_TARGETS.items():
        row = diameter_row(diameter_nm)
        median_label = str(row["median_band_label"])
        if diameter_nm == 20:
            high_hard = (
                row["case_total"] == 0
                or median_label in {"minor_high_miss", "severe_high_miss"}
                or int(row["high_miss_count"]) >= 2
            )
            low_warning = (
                not high_hard
                and (
                    median_label in {
                        "borderline_low_miss",
                        "minor_low_miss",
                        "severe_low_miss",
                    }
                    or int(row["low_miss_count"]) >= 2
                )
            )
            high_warning = (
                not high_hard
                and not low_warning
                and int(row["high_miss_count"]) == 1
            )
            row["status"] = (
                "hard_fail_Au20_over_detected"
                if high_hard
                else "warning_Au20_high_outlier"
                if high_warning
                else "warning_Au20_low_sensitivity"
                if low_warning
                else "pass_or_neutral"
            )
        else:
            hard_fail = (
                row["case_total"] == 0
                or median_label.startswith("severe")
                or median_label.startswith("minor")
                or int(row["severe_miss_count"]) >= 2
            )
            warning = (
                not hard_fail
                and (
                    int(row["minor_miss_count"]) > 0
                    or int(row["borderline_miss_count"]) >= 2
                    or median_label.startswith("borderline")
                )
            )
            row["status"] = (
                "hard_fail"
                if hard_fail
                else "warning_borderline_or_minor_miss"
                if warning
                else "pass"
            )
        rows.append(row)

    by_diameter = {int(row["diameter_nm"]): row for row in rows}
    au20 = by_diameter[20]
    au30 = by_diameter[30]
    au20_median = _safe_float(au20["median_selected_annulus_rate"])
    au30_median = _safe_float(au30["median_selected_annulus_rate"])
    au20_high = float(joint_fit.DETECTION_RATE_TARGETS[20]["high"])
    au20_low = float(joint_fit.DETECTION_RATE_TARGETS[20]["low"])
    au20_over_detected = (
        (np.isfinite(au20_median) and au20_median > au20_high + DETECTION_BAND_EPS)
        or int(au20["high_miss_count"]) >= 2
    )
    au20_inversion = (
        np.isfinite(au20_median)
        and np.isfinite(au30_median)
        and au20_median > au30_median + 1e-12
    )
    au20_low_warning = (
        (np.isfinite(au20_median) and au20_median < au20_low)
        or int(au20["low_miss_count"]) >= 2
    )
    if au20_over_detected:
        au20_status = "hard_fail_Au20_over_detected"
    elif au20_inversion:
        au20_status = "hard_fail_Au20_Au30_inversion"
    elif str(au20["status"]) == "warning_Au20_high_outlier":
        au20_status = "Au20_high_outlier_warning"
    elif au20_low_warning:
        au20_status = "Au20_low_sensitivity_warning"
    else:
        au20_status = "pass_or_neutral"

    au30_60_rows = [by_diameter[diameter_nm] for diameter_nm in (30, 40, 60)]
    au30_60_failures = [
        row
        for row in au30_60_rows
        if row["status"] == "hard_fail"
    ]
    au30_60_warnings = [
        row
        for row in au30_60_rows
        if row["status"] == "warning_borderline_or_minor_miss"
    ]
    medians = {
        diameter_nm: _safe_float(by_diameter[diameter_nm]["median_selected_annulus_rate"])
        for diameter_nm in (30, 40, 60)
    }
    size_trend_inversion = (
        np.isfinite(medians[30])
        and np.isfinite(medians[40])
        and medians[30] > medians[40] + 1e-12
    ) or (
        np.isfinite(medians[40])
        and np.isfinite(medians[60])
        and medians[40] > medians[60] + 1e-12
    )
    if au30_60_failures:
        au30_60_status = "hard_fail_Au30_60_practical_gate"
    elif size_trend_inversion:
        au30_60_status = "hard_fail_Au30_60_size_trend_inversion"
    elif au30_60_warnings:
        au30_60_status = "warning_Au30_60_borderline_or_minor_miss"
    else:
        au30_60_status = "pass"

    release_blocker = au20_status.startswith("hard_fail") or au30_60_status.startswith(
        "hard_fail"
    )
    if release_blocker:
        alignment_status = "fail_release_blocker"
    elif au20_status == "Au20_low_sensitivity_warning":
        alignment_status = "partial_pass_with_Au20_low_warning"
    else:
        alignment_status = "pass"
    return {
        "status": alignment_status,
        "detection_alignment_status": alignment_status,
        "au20_detection_status": au20_status,
        "au30_60_detection_status": au30_60_status,
        "release_blocker": bool(release_blocker),
        "rows": rows,
    }


def signal_ratio_status(best: pd.Series) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    target_mode_rows: list[dict[str, Any]] = []
    pass_all = True
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        observed = _safe_float(best.get(f"ag40_to_au40_calibrated_peak_ratio_{wavelength_nm}"))
        target = _safe_float(best.get(f"ag40_to_au40_target_ratio_{wavelength_nm}"))
        residual = (
            abs(math.log(observed / target))
            if np.isfinite(observed) and observed > 0 and np.isfinite(target) and target > 0
            else float("nan")
        )
        wavelength_pass = np.isfinite(residual) and residual <= 0.25
        pass_all = pass_all and bool(wavelength_pass)
        rows.append(
            {
                "wavelength_nm": wavelength_nm,
                "calibrated_ratio": observed,
                "target_ratio": target,
                "abs_log_residual": residual,
                "status": "pass" if wavelength_pass else "fail",
            }
        )
    for target_mode in joint_fit.SIGNAL_RATIO_TARGET_MODES:
        penalties: list[float] = []
        for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
            raw_observed = _safe_float(best.get(f"ag40_to_au40_peak_ratio_{wavelength_nm}"))
            target = _safe_float(
                best.get(f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}")
            )
            if not np.isfinite(target) or target <= 0:
                target = joint_fit.table_s1_signal_ratio_target(wavelength_nm, target_mode)
            if (
                np.isfinite(raw_observed)
                and raw_observed > 0
                and np.isfinite(target)
                and target > 0
            ):
                penalties.append(float(math.log(raw_observed / target) ** 2))
        target_mode_score = float(np.mean(penalties)) if penalties else float("nan")
        target_mode_rows.append(
            {
                "target_mode": target_mode,
                "raw_peak_ratio_score": target_mode_score,
                "status": "pass"
                if np.isfinite(target_mode_score) and target_mode_score <= 0.05
                else "fail",
            }
        )
    score = _safe_float(best.get("signal_ratio_score"))
    score_pass = np.isfinite(score) and score <= 0.05
    target_mode_by_name = {
        str(row["target_mode"]): row for row in target_mode_rows
    }
    strict_mode = "interferometric_column_ratio"
    formula_mode = "sqrt_scattering_column_ratio"
    recomputed_mode = "recomputed_mie_sqrt_csca_ratio"
    return {
        "status": "pass" if pass_all and score_pass else "partial_or_fail",
        "score": score,
        "strict_status": str(
            target_mode_by_name.get(strict_mode, {}).get("status", "not_evaluated")
        ),
        "strict_score": _safe_float(
            target_mode_by_name.get(strict_mode, {}).get("raw_peak_ratio_score")
        ),
        "formula_status": str(
            target_mode_by_name.get(formula_mode, {}).get("status", "not_evaluated")
        ),
        "formula_score": _safe_float(
            target_mode_by_name.get(formula_mode, {}).get("raw_peak_ratio_score")
        ),
        "recomputed_mie_status": str(
            target_mode_by_name.get(recomputed_mode, {}).get(
                "status",
                "not_evaluated",
            )
        ),
        "recomputed_mie_score": _safe_float(
            target_mode_by_name.get(recomputed_mode, {}).get("raw_peak_ratio_score")
        ),
        "rows": rows,
        "target_mode_rows": target_mode_rows,
    }


def size_snr_status(best: pd.Series) -> dict[str, Any]:
    calibrated = _safe_float(best.get("au_size_exponent_calibrated_median"))
    raw = _safe_float(best.get("au_size_exponent_raw_median"))
    delta = _safe_float(best.get("applied_au_size_response_exponent_delta"))
    guard_penalty = _safe_float(best.get("size_response_guardrail_penalty"))
    size_pass = (
        np.isfinite(calibrated)
        and abs(calibrated - joint_fit.AU_SIZE_EXPONENT_TARGET) <= 0.4
        and np.isfinite(delta)
        and joint_fit.MIN_SIZE_RESPONSE_EXPONENT_DELTA <= delta <= joint_fit.MAX_SIZE_RESPONSE_EXPONENT_DELTA
        and (not np.isfinite(guard_penalty) or guard_penalty <= 1e-12)
    )
    snr_ratio = _safe_float(best.get("au30_to_au20_snr_ratio_median"))
    snr_residual = (
        abs(math.log(snr_ratio / joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET))
        if np.isfinite(snr_ratio) and snr_ratio > 0
        else float("nan")
    )
    snr_pass = np.isfinite(snr_residual) and snr_residual <= 0.35
    return {
        "size_status": "pass" if size_pass else "fail",
        "snr_status": "pass" if snr_pass else "fail",
        "raw_size_exponent": raw,
        "calibrated_size_exponent": calibrated,
        "applied_size_delta": delta,
        "snr_ratio": snr_ratio,
        "snr_abs_log_residual": snr_residual,
    }


def classification_status(classification_summary: pd.DataFrame | None) -> dict[str, Any]:
    if classification_summary is None or classification_summary.empty:
        return {
            "status": "missing",
            "notes": "classification summary not provided",
        }
    row = classification_summary.iloc[0]
    claim = str(row.get("svm_accuracy_claim_level", "no_accuracy_claim"))
    usable_min = _safe_float(row.get("usable_min_class_count"))
    feature_status = str(row.get("paper_protocol_match_status", "unknown"))
    complete = (
        int(row.get("class_count", 0)) == 4
        and np.isfinite(usable_min)
        and usable_min > 0
        and feature_status.startswith("feature_export_matches")
    )
    return {
        "status": "diagnostic_complete" if complete else "diagnostic_incomplete",
        "svm_accuracy_claim_level": claim,
        "usable_min_class_count": usable_min,
        "paper_protocol_match_status": feature_status,
        "notes": (
            "classification remains diagnostic and does not drive inverse search"
            if claim == "no_accuracy_claim"
            else "classification accuracy is simulated diagnostic, not paper reproduction"
        ),
    }


def shadow_all_crossing_dashboard(route_summary: pd.DataFrame | None) -> pd.DataFrame:
    if route_summary is None or route_summary.empty:
        return pd.DataFrame(
            [
                {
                    "scope": "ev_route_shadow",
                    "status": "missing",
                    "notes": "route summary not provided",
                }
            ]
        )
    rows = []
    selected_uplift = pd.to_numeric(
        route_summary.get("raw_mean_selected_annulus_uplift"),
        errors="coerce",
    )
    selected_fraction = pd.to_numeric(
        route_summary.get("raw_mean_selected_annulus_fraction"),
        errors="coerce",
    )
    selected_contribution = pd.to_numeric(
        route_summary.get("raw_mean_selected_annulus_contribution"),
        errors="coerce",
    )
    all_detection = pd.to_numeric(
        route_summary.get("raw_mean_all_crossing_detection"),
        errors="coerce",
    )
    selected_detection = pd.to_numeric(
        route_summary.get("raw_mean_selected_annulus_detection"),
        errors="coerce",
    )
    reference = route_summary.get("selected_annulus_reference_interpretation")
    rows.append(
        {
            "scope": "ev_route_shadow",
            "status": "available",
            "route_count": int(len(route_summary)),
            "selected_all_uplift_median": float(selected_uplift.median()),
            "selected_all_uplift_max": float(selected_uplift.max()),
            "selected_fraction_mean": float(selected_fraction.mean()),
            "selected_contribution_mean": float(selected_contribution.mean()),
            "all_crossing_detection_mean": float(all_detection.mean()),
            "selected_detection_mean": float(selected_detection.mean()),
            "reference_useful_routes": int(
                reference.astype(str).eq("reference_useful_selected_cross_check").sum()
            )
            if reference is not None
            else 0,
            "weak_reference_boundary_routes": int(
                reference.astype(str).eq("weak_reference_boundary_selected_only").sum()
            )
            if reference is not None
            else 0,
            "notes": "shadow only; not included in Tsuyama paper score",
        }
    )
    return pd.DataFrame(rows)


def build_acceptance_report(
    *,
    joint_summary: pd.DataFrame,
    target_frame: pd.DataFrame,
    classification_summary: pd.DataFrame | None = None,
    route_summary: pd.DataFrame | None = None,
    primary_score_mode: str = "strict",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    joint_summary = add_paper_reproduction_metrics(joint_summary)
    signing_summary, aggregation_info = seed_median_acceptance_frame(
        joint_summary,
        primary_score_mode=primary_score_mode,
    )
    if primary_score_mode.startswith("paper_reproduction"):
        signing_summary = add_paper_reproduction_metrics(signing_summary)
    best = _best_joint_candidate(signing_summary, primary_score_mode=primary_score_mode)
    hard_targets = target_frame[target_frame["usable_for_hard_acceptance"].astype(bool)]
    hard_has_diagnostic = bool((hard_targets["confidence"] == "diagnostic_only").any())
    detection = detection_band_status(best)
    signal = signal_ratio_status(best)
    size_snr = size_snr_status(best)
    classification = classification_status(classification_summary)
    shadow = shadow_all_crossing_dashboard(route_summary)
    inverse_context = inverse_context_status(joint_summary, best)
    raw_alignment = raw_family_alignment_status(signing_summary)
    best_uses_local_fit = _uses_local_paper_fit(best)
    raw_signal_status = raw_alignment.get(
        "raw_signal_ratio_alignment_status",
        "not_evaluated",
    )
    raw_size_status = raw_alignment.get(
        "raw_size_response_alignment_status",
        "not_evaluated",
    )
    if best_uses_local_fit and raw_alignment["status"] != "pass":
        local_fit_status = "bounded_local_fit_diagnostic_only"
    elif best_uses_local_fit:
        local_fit_status = "local_fit_supported_by_raw_family_shadow"
    else:
        local_fit_status = "raw_or_nonlocal_fit_candidate"

    guardrails = [
        {
            "guardrail": "hard_targets_not_diagnostic_only",
            "status": "fail" if hard_has_diagnostic else "pass",
            "notes": "hard acceptance cannot use diagnostic_only target confidence",
        },
        {
            "guardrail": "annulus_fraction_min",
            "status": "pass"
            if _safe_float(best.get("annulus_fraction_min")) >= joint_fit.MIN_ANNULUS_FRACTION
            else "fail",
            "value": _safe_float(best.get("annulus_fraction_min")),
            "notes": "selected-annulus denominator guardrail",
        },
        {
            "guardrail": "transfer_gain_guardrail",
            "status": "pass"
            if _safe_float(best.get("transfer_gain_guardrail_penalty")) <= 1e-12
            else "fail",
            "value": _safe_float(best.get("transfer_gain_guardrail_penalty")),
            "notes": "bounded Ag transfer gain guardrail",
        },
        {
            "guardrail": "size_response_guardrail",
            "status": "pass"
            if _safe_float(best.get("size_response_guardrail_penalty")) <= 1e-12
            else "fail",
            "value": _safe_float(best.get("size_response_guardrail_penalty")),
            "notes": "bounded Au size-response delta guardrail",
        },
        {
            "guardrail": "reference_rho_na",
            "status": "fail"
            if any(
                _safe_bool(best.get(name))
                for name in ("reference_bad", "rho_bad", "na_cutoff_active")
            )
            else "pass",
            "notes": "reference-too-weak, rho, or NA boundary cannot sign accepted candidate",
        },
    ]
    guardrail_frame = pd.DataFrame(guardrails)
    no_go_reasons = guardrail_frame.loc[
        guardrail_frame["status"] == "fail",
        "guardrail",
    ].tolist()
    diagnostic_warnings: list[str] = []
    if classification["status"] == "diagnostic_incomplete":
        no_go_reasons.append("classification_diagnostic_incomplete")
    if detection.get("release_blocker"):
        no_go_reasons.append("detection_practical_gate_not_met")
    if inverse_context["has_family_ladder"] and raw_alignment["status"] != "pass":
        if raw_signal_status == "fail_strict_and_formula_consistent_targets":
            no_go_reasons.append("raw_signal_ratio_alignment_not_met")
        elif raw_signal_status == "pass_formula_consistent_table_s1_target_only":
            diagnostic_warnings.append(
                "strict_table_s1_signal_unresolved_formula_signal_pass"
            )
        if raw_size_status != "pass":
            no_go_reasons.append("raw_size_response_alignment_not_met")
    if inverse_context["has_family_ladder"] and not inverse_context["best_candidate_multi_seed_stable"]:
        no_go_reasons.append("top_candidate_multi_seed_or_mode_instability")

    primary_score_column = _effective_score_column(signing_summary, primary_score_mode)
    primary_reproduction = _primary_paper_reproduction_fields(
        best,
        primary_score_mode,
    )
    summary_rows = [
        _status_row("target_audit", "pass" if not hard_has_diagnostic else "fail", len(target_frame), "hard targets exclude diagnostic_only confidence"),
        _status_row("best_candidate_id", "info", best.get("candidate_id"), f"lowest {primary_score_column} row"),
        _status_row("primary_score_mode", "info", primary_score_mode, "candidate signing sort mode"),
        _status_row(primary_score_column, "info", _safe_float(best.get(primary_score_column)), "lower is better"),
        _status_row("detection_alignment", detection["detection_alignment_status"], json.dumps(detection["rows"], ensure_ascii=False), "Au20 low misses warn; Au20 over-detection and Au30-60 gate remain blockers"),
        _status_row("au20_detection_status", detection["au20_detection_status"], "", "Au20 lower-bound misses are warning-only; over-detection remains hard"),
        _status_row("au30_60_detection_status", detection["au30_60_detection_status"], "", "Au30/Au40/Au60 practical selected-annulus sanity gate"),
        _status_row("strict_interferometric_column_signal_ratio_pass", signal["strict_status"], signal["strict_score"], "raw Ag40/Au40 ratio against strict Table S1 interferometric-column target"),
        _status_row("formula_consistent_signal_ratio_pass", signal["formula_status"], signal["formula_score"], "raw Ag40/Au40 ratio against sqrt-scattering Table S1 target"),
        _status_row("recomputed_mie_signal_ratio_pass", signal["recomputed_mie_status"], signal["recomputed_mie_score"], "raw Ag40/Au40 ratio against simulator recomputed Mie sqrt-Csca target"),
        _status_row("calibrated_or_strict_signal_ratio_pass", signal["status"], signal["score"], "legacy calibrated/strict Ag40/Au40 residual"),
        _status_row("size_exponent_pass", size_snr["size_status"], size_snr["calibrated_size_exponent"], "calibrated Au size exponent"),
        _status_row("snr_ratio_pass", size_snr["snr_status"], size_snr["snr_ratio"], "Au30/Au20 SNR ratio"),
        _status_row("classification_diagnostic", classification["status"], classification.get("svm_accuracy_claim_level"), classification["notes"]),
        _status_row("acceptance_aggregation", aggregation_info["acceptance_aggregation_mode"], json.dumps(aggregation_info, ensure_ascii=False), "candidate signing uses seed-median rows when seeds are available"),
        _status_row("inverse_context", inverse_context["status"], json.dumps(inverse_context, ensure_ascii=False), "family-ladder / seed context for final signing"),
        _status_row("raw_family_alignment", raw_alignment["status"], json.dumps(raw_alignment, ensure_ascii=False), "raw/non-transfer family shadow check"),
        _status_row("raw_signal_ratio_alignment", raw_signal_status, raw_alignment.get("best_raw_strict_signal_ratio_score"), "strict and formula-consistent Table S1 target modes are reported separately"),
        _status_row("raw_size_response_alignment", raw_size_status, raw_alignment.get("best_raw_size_exponent_score"), "raw Au size-response must align before local fit can be signed"),
        _status_row("local_fit_interpretability", local_fit_status, best_uses_local_fit, "E-family transfer/size correction remains diagnostic unless raw family supports it"),
        _status_row("paper_reproduction_status", best.get("paper_reproduction_status"), best.get("paper_reproduction_score_formula"), "paper reproduction fit only; not physical calibration"),
        _status_row("paper_reproduction_candidate_class", best.get("paper_reproduction_candidate_class"), best.get("paper_reproduction_fit_dof_count"), "raw / bounded / maximal reproduction class"),
        _status_row("paper_reproduction_size_delta", best.get("paper_reproduction_size_delta_status"), best.get("paper_reproduction_applied_au_size_response_exponent_delta"), "global Au power-law delta needed for reproduction"),
        _status_row("paper_reproduction_corrected_au_exponent", "info", best.get("paper_reproduction_corrected_au_size_exponent"), "corrected exponent after reproduction-only global size delta"),
        _status_row("paper_reproduction_snr_scale", "info", best.get("paper_reproduction_fitted_global_snr_scale"), "single global SNR scale to paper Au20/Au30 anchors"),
        _status_row("paper_reproduction_snr_response_status", best.get("paper_reproduction_status_snr_response"), best.get("paper_reproduction_score_formula_snr_response"), "single global SNR response exponent plus scale"),
        _status_row("paper_reproduction_snr_response_exponent", best.get("paper_reproduction_snr_response_status"), best.get("paper_reproduction_snr_response_exponent"), "global readout/SNR exponent used only for reproduction rescore"),
        _status_row("paper_reproduction_reviewed_status", best.get("paper_reproduction_status_reviewed"), best.get("paper_reproduction_score_reviewed_snr_response"), "descriptive reviewed score; strict Table S1 is report-only and release status is unchanged"),
        _status_row("paper_reproduction_maximal_upper_status", best.get("paper_reproduction_status_maximal_upper"), best.get("paper_reproduction_score_maximal_upper"), "maximal upper-bound score with hypothetical strict Table S1 Ag transfer; not calibration"),
        _status_row("paper_reproduction_response_compression_status", best.get("paper_reproduction_status_response_compression"), best.get("paper_reproduction_score_response_compression"), "single global pulse-height/readout compression; descriptive reproduction-only lens"),
        _status_row("paper_reproduction_response_compression_gamma", best.get("paper_reproduction_response_compression_gamma_status"), best.get("paper_reproduction_applied_response_compression_gamma"), "global gamma shared across wavelength, geometry, and diameter"),
        _status_row("primary_paper_reproduction_status", primary_reproduction.get("primary_paper_reproduction_status"), primary_reproduction.get("primary_paper_reproduction_score"), "status/score for the selected paper reproduction score mode"),
        _status_row("paper_reproduction_strict_upper_ag_transfer_gain_range", best.get("paper_reproduction_strict_upper_ag_transfer_status"), json.dumps({"min": best.get("paper_reproduction_strict_upper_ag_transfer_gain_min"), "max": best.get("paper_reproduction_strict_upper_ag_transfer_gain_max")}), "hypothetical per-wavelength Ag transfer range used only for upper-bound scoring"),
        _status_row("paper_reproduction_score_strict_upper", "info", best.get("paper_reproduction_score_strict_upper"), "strict Table S1 upper-bound reproduction score"),
        _status_row("diagnostic_warnings", "info", json.dumps(diagnostic_warnings), "diagnostic warnings do not by themselves block release"),
        _status_row("no_go_status", "pass" if not no_go_reasons else "stop", json.dumps(no_go_reasons), "stop means publish diagnostic/negative result only"),
    ]
    summary_frame = pd.DataFrame(summary_rows)
    candidate_release_status = (
        "negative_or_diagnostic_result_only"
        if no_go_reasons
        else (
            "accepted_paper_calibrated_proxy_candidate"
            if inverse_context["has_family_ladder"]
            else "baseline_requires_phase2_inverse_confirmation"
        )
    )
    payload = {
        "schema_id": SCHEMA_ID,
        "generated_at_unix": time.time(),
        "best_candidate_id": str(best.get("candidate_id")),
        "best_candidate_family_id": str(best.get("family_id", "")),
        "best_candidate_uses_local_paper_fit": bool(best_uses_local_fit),
        "joint_signal_transfer_mode": str(best.get("joint_signal_transfer_mode", "")),
        "joint_size_response_mode": str(best.get("joint_size_response_mode", "")),
        "paper_fit_status": str(best.get("paper_fit_status")),
        "primary_score_mode": primary_score_mode,
        "primary_score_column": primary_score_column,
        "primary_paper_reproduction": _json_safe(primary_reproduction),
        "primary_paper_reproduction_status": primary_reproduction.get(
            "primary_paper_reproduction_status"
        ),
        "primary_paper_reproduction_score": primary_reproduction.get(
            "primary_paper_reproduction_score"
        ),
        "primary_paper_reproduction_candidate_class": primary_reproduction.get(
            "primary_paper_reproduction_candidate_class"
        ),
        "acceptance_aggregation_mode": aggregation_info["acceptance_aggregation_mode"],
        "acceptance_aggregation": aggregation_info,
        "detection": detection,
        "detection_alignment_status": detection["detection_alignment_status"],
        "au20_detection_status": detection["au20_detection_status"],
        "au30_60_detection_status": detection["au30_60_detection_status"],
        "signal": signal,
        "size_snr": size_snr,
        "classification": classification,
        "inverse_context": inverse_context,
        "raw_family_alignment": raw_alignment,
        "raw_signal_ratio_alignment_status": raw_signal_status,
        "raw_size_response_alignment_status": raw_size_status,
        "local_fit_interpretability_status": local_fit_status,
        "paper_reproduction": _json_safe(
            {
                key: best.get(key)
                for key in best.index
                if str(key).startswith("paper_reproduction_")
            }
        ),
        "diagnostic_warnings": diagnostic_warnings,
        "no_go_reasons": no_go_reasons,
        "candidate_release_status": candidate_release_status,
    }
    return summary_frame, guardrail_frame, shadow, payload


def build_input_manifest(
    *,
    joint_summary_path: Path,
    joint_summary: pd.DataFrame,
    target_manifest_path: Path | None,
    target_frame: pd.DataFrame,
    classification_summary_path: Path | None,
    classification_summary: pd.DataFrame | None,
    route_summary_path: Path | None,
    route_summary: pd.DataFrame | None,
) -> dict[str, Any]:
    selected_min = _numeric_column(
        joint_summary,
        "selected_detector_mode_annulus_edge_norm_min",
    )
    selected_max = _numeric_column(
        joint_summary,
        "selected_detector_mode_annulus_edge_norm_max",
    )
    selected_bounds = {
        "edge_norm_min": float(selected_min.dropna().iloc[0])
        if selected_min.notna().any()
        else joint_fit.SELECTED_DETECTOR_MODE_EDGE_NORM_MIN,
        "edge_norm_max": float(selected_max.dropna().iloc[0])
        if selected_max.notna().any()
        else joint_fit.SELECTED_DETECTOR_MODE_EDGE_NORM_MAX,
    }

    def file_record(path: Path | None, frame: pd.DataFrame | None) -> dict[str, Any]:
        if path is None:
            return {"source": "generated_from_code", "rows": int(len(frame)) if frame is not None else 0}
        record: dict[str, Any] = {
            "path": str(path),
            "exists": bool(path.exists()),
            "rows": int(len(frame)) if frame is not None else 0,
        }
        if path.exists():
            record["size_bytes"] = int(path.stat().st_size)
            record["sha256"] = _file_sha256(path)
        return record

    candidate_count = (
        int(joint_summary["candidate_id"].nunique())
        if "candidate_id" in joint_summary
        else int(len(joint_summary))
    )
    seed_count = (
        int(pd.to_numeric(joint_summary["random_seed"], errors="coerce").dropna().nunique())
        if "random_seed" in joint_summary
        else 0
    )
    return {
        "joint_summary": file_record(joint_summary_path, joint_summary),
        "target_manifest": file_record(target_manifest_path, target_frame),
        "classification_summary": file_record(
            classification_summary_path,
            classification_summary,
        ),
        "route_summary": file_record(route_summary_path, route_summary),
        "joint_summary_row_count": int(len(joint_summary)),
        "candidate_count": candidate_count,
        "seed_count": seed_count,
        "selected_annulus_bounds": selected_bounds,
    }


def paper_reproduction_score_decomposition(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        size = _safe_float(row.get("paper_reproduction_size_exponent_loss"))
        snr_ratio = _safe_float(row.get("paper_reproduction_snr_ratio_loss"))
        snr_anchor = _safe_float(row.get("paper_reproduction_snr_anchor_loss"))
        snr_response_ratio = _safe_float(
            row.get("paper_reproduction_snr_response_ratio_loss")
        )
        snr_response_anchor = _safe_float(
            row.get("paper_reproduction_snr_response_anchor_loss")
        )
        detection = _safe_float(row.get("paper_reproduction_detection_loss"))
        formula = _safe_float(row.get("paper_reproduction_formula_signal_loss"))
        strict = _safe_float(row.get("paper_reproduction_strict_signal_diagnostic_loss"))
        complexity = _safe_float(row.get("paper_reproduction_fit_complexity_penalty"))
        complexity_snr_response = _safe_float(
            row.get("paper_reproduction_fit_complexity_penalty_snr_response")
        )
        complexity_maximal_upper = _safe_float(
            row.get("paper_reproduction_fit_complexity_penalty_maximal_upper")
        )
        complexity_response_compression = _safe_float(
            row.get("paper_reproduction_fit_complexity_penalty_response_compression")
        )
        guardrail = _safe_float(row.get("paper_reproduction_guardrail_penalty"))
        guardrail_snr_response = _safe_float(
            row.get("paper_reproduction_guardrail_penalty_snr_response")
        )
        guardrail_maximal_upper = _safe_float(
            row.get("paper_reproduction_guardrail_penalty_maximal_upper")
        )
        guardrail_response_compression = _safe_float(
            row.get("paper_reproduction_guardrail_penalty_response_compression")
        )
        strict_upper_after_transfer = _safe_float(
            row.get("paper_reproduction_strict_upper_signal_loss_after_transfer")
        )
        response_compression_size = _safe_float(
            row.get("paper_reproduction_response_compression_size_loss")
        )
        response_compression_snr_ratio = _safe_float(
            row.get("paper_reproduction_response_compression_snr_ratio_loss")
        )
        response_compression_snr_anchor = _safe_float(
            row.get("paper_reproduction_response_compression_snr_anchor_loss")
        )
        response_compression_formula = _safe_float(
            row.get("paper_reproduction_response_compression_formula_signal_loss")
        )
        rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "family_id": row.get("family_id"),
                "paper_reproduction_score_formula": _safe_float(
                    row.get("paper_reproduction_score_formula")
                ),
                "weighted_size_exponent_loss": 4.0 * size,
                "weighted_snr_ratio_loss": 3.0 * snr_ratio,
                "weighted_snr_anchor_loss": snr_anchor,
                "weighted_detection_loss": 1.5 * detection,
                "weighted_formula_signal_loss": formula,
                "weighted_strict_signal_diagnostic_loss": 0.2 * strict,
                "weighted_fit_complexity_penalty": 1.2 * complexity,
                "guardrail_penalty": guardrail,
                "paper_reproduction_score_formula_snr_response": _safe_float(
                    row.get("paper_reproduction_score_formula_snr_response")
                ),
                "weighted_snr_response_ratio_loss": 3.0 * snr_response_ratio,
                "weighted_snr_response_anchor_loss": snr_response_anchor,
                "weighted_fit_complexity_penalty_snr_response": (
                    1.2 * complexity_snr_response
                ),
                "guardrail_penalty_snr_response": guardrail_snr_response,
                "paper_reproduction_score_reviewed_snr_response": _safe_float(
                    row.get("paper_reproduction_score_reviewed_snr_response")
                ),
                "weighted_detection_loss_reviewed": 0.5 * detection,
                "weighted_strict_signal_diagnostic_loss_reviewed": 0.0 * strict,
                "weighted_fit_complexity_penalty_reviewed": (
                    0.6 * complexity_snr_response
                ),
                "guardrail_penalty_reviewed": guardrail_snr_response,
                "paper_reproduction_score_maximal_upper": _safe_float(
                    row.get("paper_reproduction_score_maximal_upper")
                ),
                "paper_reproduction_score_response_compression": _safe_float(
                    row.get("paper_reproduction_score_response_compression")
                ),
                "weighted_detection_loss_maximal_upper": 0.2 * detection,
                "weighted_formula_signal_loss_maximal_upper": 0.2 * formula,
                "weighted_strict_upper_signal_loss_after_transfer": (
                    strict_upper_after_transfer
                ),
                "weighted_fit_complexity_penalty_maximal_upper": (
                    0.3 * complexity_maximal_upper
                ),
                "guardrail_penalty_maximal_upper": guardrail_maximal_upper,
                "weighted_response_compression_size_loss": (
                    4.0 * response_compression_size
                ),
                "weighted_response_compression_snr_ratio_loss": (
                    3.0 * response_compression_snr_ratio
                ),
                "weighted_response_compression_snr_anchor_loss": (
                    response_compression_snr_anchor
                ),
                "weighted_response_compression_detection_loss": 0.5 * detection,
                "weighted_response_compression_formula_signal_loss": (
                    response_compression_formula
                ),
                "weighted_fit_complexity_penalty_response_compression": (
                    0.6 * complexity_response_compression
                ),
                "guardrail_penalty_response_compression": (
                    guardrail_response_compression
                ),
                "snr_response_exponent": _safe_float(
                    row.get("paper_reproduction_snr_response_exponent")
                ),
                "response_compression_gamma": _safe_float(
                    row.get("paper_reproduction_applied_response_compression_gamma")
                ),
                "snr_response_status": row.get("paper_reproduction_snr_response_status"),
                "response_compression_status": row.get(
                    "paper_reproduction_status_response_compression"
                ),
                "reviewed_status": row.get("paper_reproduction_status_reviewed"),
                "maximal_upper_status": row.get(
                    "paper_reproduction_status_maximal_upper"
                ),
                "strict_upper_ag_transfer_gain_min": _safe_float(
                    row.get("paper_reproduction_strict_upper_ag_transfer_gain_min")
                ),
                "strict_upper_ag_transfer_gain_max": _safe_float(
                    row.get("paper_reproduction_strict_upper_ag_transfer_gain_max")
                ),
            }
        )
    return pd.DataFrame(rows)


def _size_response_value_column(
    diameter_nm: int,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    observable: str,
) -> str:
    case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
    if observable == "peak_height":
        suffix = "mean_peak_height"
    elif observable == "local_snr":
        suffix = "mean_local_snr"
    elif observable == "peak_margin_z":
        suffix = "mean_peak_margin_z"
    elif observable == "peak_height_times_width":
        suffix = "mean_peak_height_times_width"
    else:
        suffix = f"mean_{observable}"
    return f"au{diameter_nm}_{case_key}_{suffix}"


def _fit_log_power_exponent(diameters_nm: list[float], values: list[float]) -> float:
    valid = [
        (float(diameter), float(value))
        for diameter, value in zip(diameters_nm, values)
        if np.isfinite(diameter)
        and diameter > 0
        and np.isfinite(value)
        and value > 0
    ]
    if len(valid) < 2:
        return float("nan")
    x = np.log(np.asarray([diameter for diameter, _ in valid], dtype="float64"))
    y = np.log(np.asarray([value for _, value in valid], dtype="float64"))
    return float(np.polyfit(x, y, 1)[0])


def size_response_case_decomposition(frame: pd.DataFrame) -> pd.DataFrame:
    """Long-form Au size-response residuals for seed-median candidate rows."""
    rows: list[dict[str, Any]] = []
    diameters = list(joint_fit.GOLD_DIAMETERS_NM)
    pair_columns = {
        (20, 30): "pair_slope_20_30",
        (30, 40): "pair_slope_30_40",
        (40, 60): "pair_slope_40_60",
    }
    for _, row in frame.iterrows():
        for observable in joint_fit.SIZE_SIGNAL_OBSERVABLES:
            for wavelength_nm, width_nm, depth_nm in joint_fit.JOINT_CASES:
                values = [
                    _safe_float(
                        row.get(
                            _size_response_value_column(
                                diameter_nm,
                                wavelength_nm,
                                width_nm,
                                depth_nm,
                                observable,
                            )
                        )
                    )
                    for diameter_nm in diameters
                ]
                exponent = _fit_log_power_exponent([float(d) for d in diameters], values)
                pair_slopes: dict[tuple[int, int], float] = {}
                for first, second in pair_columns:
                    first_value = values[diameters.index(first)]
                    second_value = values[diameters.index(second)]
                    pair_slopes[(first, second)] = _fit_log_power_exponent(
                        [float(first), float(second)],
                        [first_value, second_value],
                    )
                finite_pairs = {
                    pair: slope
                    for pair, slope in pair_slopes.items()
                    if np.isfinite(slope)
                }
                if finite_pairs:
                    limiting_pair, limiting_slope = max(
                        finite_pairs.items(),
                        key=lambda item: abs(item[1] - joint_fit.AU_SIZE_EXPONENT_TARGET),
                    )
                    steepest_pair, steepest_slope = max(
                        finite_pairs.items(),
                        key=lambda item: item[1] - joint_fit.AU_SIZE_EXPONENT_TARGET,
                    )
                else:
                    limiting_pair, limiting_slope = (None, float("nan"))
                    steepest_pair, steepest_slope = (None, float("nan"))
                out: dict[str, Any] = {
                    "candidate_id": row.get("candidate_id"),
                    "family_id": row.get("family_id"),
                    "base_candidate_id": row.get("base_candidate_id"),
                    "joint_signal_transfer_mode": row.get("joint_signal_transfer_mode"),
                    "joint_size_response_mode": row.get("joint_size_response_mode"),
                    "observable": observable,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "geometry": f"{width_nm}x{depth_nm}",
                    "au20_value": values[0],
                    "au30_value": values[1],
                    "au40_value": values[2],
                    "au60_value": values[3],
                    "exponent_all_sizes": exponent,
                    "exponent_residual_vs_2p3": (
                        float(exponent - joint_fit.AU_SIZE_EXPONENT_TARGET)
                        if np.isfinite(exponent)
                        else float("nan")
                    ),
                    "exponent_abs_residual_vs_2p3": (
                        float(abs(exponent - joint_fit.AU_SIZE_EXPONENT_TARGET))
                        if np.isfinite(exponent)
                        else float("nan")
                    ),
                    "limiting_pair": (
                        f"{limiting_pair[0]}-{limiting_pair[1]}"
                        if limiting_pair is not None
                        else ""
                    ),
                    "limiting_pair_slope": limiting_slope,
                    "limiting_pair_abs_residual_vs_2p3": (
                        float(abs(limiting_slope - joint_fit.AU_SIZE_EXPONENT_TARGET))
                        if np.isfinite(limiting_slope)
                        else float("nan")
                    ),
                    "steepest_pair": (
                        f"{steepest_pair[0]}-{steepest_pair[1]}"
                        if steepest_pair is not None
                        else ""
                    ),
                    "steepest_pair_slope": steepest_slope,
                    "steepest_pair_residual_vs_2p3": (
                        float(steepest_slope - joint_fit.AU_SIZE_EXPONENT_TARGET)
                        if np.isfinite(steepest_slope)
                        else float("nan")
                    ),
                    "target_exponent": joint_fit.AU_SIZE_EXPONENT_TARGET,
                }
                for pair, column in pair_columns.items():
                    slope = pair_slopes[pair]
                    out[column] = slope
                    out[f"{column}_residual_vs_2p3"] = (
                        float(slope - joint_fit.AU_SIZE_EXPONENT_TARGET)
                        if np.isfinite(slope)
                        else float("nan")
                    )
                rows.append(out)
    return pd.DataFrame(rows)


def size_response_candidate_summary(case_frame: pd.DataFrame) -> pd.DataFrame:
    if case_frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    group_columns = ["candidate_id", "family_id", "observable"]
    for keys, group in case_frame.groupby(group_columns, dropna=False):
        candidate_id, family_id, observable = keys
        exponent = pd.to_numeric(group["exponent_all_sizes"], errors="coerce")
        residual = pd.to_numeric(group["exponent_residual_vs_2p3"], errors="coerce")
        abs_residual = pd.to_numeric(
            group["exponent_abs_residual_vs_2p3"],
            errors="coerce",
        )
        steepest = pd.to_numeric(
            group["steepest_pair_residual_vs_2p3"],
            errors="coerce",
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "family_id": family_id,
                "observable": observable,
                "case_count": int(len(group)),
                "median_exponent": float(exponent.median()),
                "min_exponent": float(exponent.min()),
                "max_exponent": float(exponent.max()),
                "median_residual_vs_2p3": float(residual.median()),
                "median_abs_residual_vs_2p3": float(abs_residual.median()),
                "max_abs_residual_vs_2p3": float(abs_residual.max()),
                "median_steepest_pair_residual_vs_2p3": float(steepest.median()),
                "best_case_exponent": float(exponent.iloc[abs_residual.argmin()])
                if abs_residual.notna().any()
                else float("nan"),
                "all_cases_within_0p4_of_target": bool((abs_residual <= 0.4).all()),
                "median_within_0p4_of_target": bool(abs_residual.median() <= 0.4),
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    return summary.sort_values(
        ["observable", "median_abs_residual_vs_2p3", "candidate_id"],
        ignore_index=True,
    )


def write_outputs(
    *,
    output_dir: Path,
    joint_summary_path: Path,
    target_manifest_path: Path | None,
    classification_summary_path: Path | None,
    route_summary_path: Path | None,
    primary_score_mode: str = "strict",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    joint_summary = pd.read_csv(joint_summary_path)
    targets = _target_frame(target_manifest_path)
    classification_summary = (
        pd.read_csv(classification_summary_path)
        if classification_summary_path is not None and classification_summary_path.exists()
        else None
    )
    route_summary = (
        pd.read_csv(route_summary_path)
        if route_summary_path is not None and route_summary_path.exists()
        else None
    )
    summary, guardrails, shadow, payload = build_acceptance_report(
        joint_summary=joint_summary,
        target_frame=targets,
        classification_summary=classification_summary,
        route_summary=route_summary,
        primary_score_mode=primary_score_mode,
    )
    payload["input_manifest"] = build_input_manifest(
        joint_summary_path=joint_summary_path,
        joint_summary=joint_summary,
        target_manifest_path=target_manifest_path,
        target_frame=targets,
        classification_summary_path=classification_summary_path,
        classification_summary=classification_summary,
        route_summary_path=route_summary_path,
        route_summary=route_summary,
    )
    summary_path = output_dir / SUMMARY_FILENAME
    guardrail_path = output_dir / GUARDRAIL_FILENAME
    shadow_path = output_dir / SHADOW_FILENAME
    json_path = output_dir / JSON_FILENAME
    report_path = output_dir / REPORT_FILENAME
    summary.to_csv(summary_path, index=False)
    guardrails.to_csv(guardrail_path, index=False)
    shadow.to_csv(shadow_path, index=False)
    rate_calib.write_json(json_path, payload)
    reproduction_files: list[Path] = []
    if primary_score_mode.startswith("paper_reproduction"):
        reproduction_frame, _ = seed_median_acceptance_frame(
            add_paper_reproduction_metrics(joint_summary),
            primary_score_mode=primary_score_mode,
        )
        reproduction_frame = add_paper_reproduction_metrics(reproduction_frame)
        score_column = _effective_score_column(reproduction_frame, primary_score_mode)
        if score_column in reproduction_frame:
            sort_columns = [score_column]
            if "candidate_id" in reproduction_frame:
                sort_columns.append("candidate_id")
            reproduction_frame = reproduction_frame.sort_values(
                sort_columns,
                ignore_index=True,
            )
        reproduction_summary_path = output_dir / REPRODUCTION_SUMMARY_FILENAME
        reproduction_best_path = output_dir / REPRODUCTION_BEST_FILENAME
        reproduction_json_path = output_dir / REPRODUCTION_JSON_FILENAME
        reproduction_report_path = output_dir / REPRODUCTION_REPORT_FILENAME
        reproduction_decomposition_path = output_dir / REPRODUCTION_DECOMPOSITION_FILENAME
        size_case_path = output_dir / SIZE_RESPONSE_CASE_DECOMPOSITION_FILENAME
        size_summary_path = output_dir / SIZE_RESPONSE_CANDIDATE_SUMMARY_FILENAME
        size_report_path = output_dir / SIZE_RESPONSE_REPORT_FILENAME
        reproduction_frame.to_csv(reproduction_summary_path, index=False)
        decomposition_frame = paper_reproduction_score_decomposition(reproduction_frame)
        decomposition_frame.to_csv(reproduction_decomposition_path, index=False)
        size_case_frame = size_response_case_decomposition(reproduction_frame)
        size_summary_frame = size_response_candidate_summary(size_case_frame)
        size_case_frame.to_csv(size_case_path, index=False)
        size_summary_frame.to_csv(size_summary_path, index=False)
        preferred_columns = [
            "candidate_id",
            "family_id",
            "paper_reproduction_candidate_class",
            "paper_reproduction_status",
            "paper_reproduction_score_formula",
            "paper_reproduction_score_strict_upper",
            "paper_reproduction_score_formula_snr_response",
            "paper_reproduction_score_reviewed_snr_response",
            "paper_reproduction_score_maximal_upper",
            "paper_reproduction_score_response_compression",
            "paper_reproduction_candidate_class_snr_response",
            "paper_reproduction_status_snr_response",
            "paper_reproduction_candidate_class_reviewed",
            "paper_reproduction_status_reviewed",
            "paper_reproduction_candidate_class_maximal_upper",
            "paper_reproduction_status_maximal_upper",
            "paper_reproduction_candidate_class_response_compression",
            "paper_reproduction_status_response_compression",
            "paper_reproduction_required_au_size_response_exponent_delta",
            "paper_reproduction_applied_au_size_response_exponent_delta",
            "paper_reproduction_corrected_au_size_exponent",
            "paper_reproduction_required_response_compression_gamma",
            "paper_reproduction_applied_response_compression_gamma",
            "paper_reproduction_response_compression_corrected_au_size_exponent",
            "paper_reproduction_fitted_global_snr_scale",
            "paper_reproduction_snr_response_exponent",
            "paper_reproduction_snr_response_scale",
            "paper_reproduction_response_compression_snr_scale",
            "paper_reproduction_formula_signal_loss",
            "paper_reproduction_strict_signal_diagnostic_loss",
            "paper_reproduction_snr_ratio_loss",
            "paper_reproduction_snr_anchor_loss",
            "paper_reproduction_snr_response_ratio_loss",
            "paper_reproduction_snr_response_anchor_loss",
            "paper_reproduction_response_compression_snr_ratio_loss",
            "paper_reproduction_response_compression_snr_anchor_loss",
            "paper_reproduction_response_compression_formula_signal_loss",
            "paper_reproduction_response_compression_strict_signal_loss",
            "paper_reproduction_detection_loss",
            "paper_reproduction_fit_complexity_penalty",
            "paper_reproduction_fit_complexity_penalty_snr_response",
            "paper_reproduction_fit_complexity_penalty_maximal_upper",
            "paper_reproduction_fit_complexity_penalty_response_compression",
            "paper_reproduction_strict_upper_ag_transfer_complexity_penalty",
            "paper_reproduction_strict_upper_ag_transfer_gain_min",
            "paper_reproduction_strict_upper_ag_transfer_gain_max",
            "paper_reproduction_guardrail_penalty",
            "paper_reproduction_guardrail_penalty_maximal_upper",
            "paper_reproduction_guardrail_penalty_response_compression",
            "joint_signal_transfer_mode",
            "joint_size_response_mode",
            "paper_fit_status",
        ]
        best_columns = [column for column in preferred_columns if column in reproduction_frame]
        reproduction_frame.loc[:, best_columns].head(20).to_csv(
            reproduction_best_path,
            index=False,
        )
        reproduction_payload = {
            "schema_id": "tsuyama_paper_reproduction_fit_v1",
            "source_acceptance_schema_id": SCHEMA_ID,
            "primary_score_mode": primary_score_mode,
            "claim_boundary": (
                "paper_reproduction_fit_only_not_physical_calibration"
            ),
            "ev_full_grid_writeback": False,
            "selected_annulus_changed": False,
            "global_material_defaults_changed": False,
            "best_candidate": payload.get("best_candidate_id"),
            "best_candidate_paper_reproduction": payload.get("paper_reproduction"),
            "input_manifest": payload.get("input_manifest", {}),
        }
        rate_calib.write_json(reproduction_json_path, reproduction_payload)
        reproduction_lines = [
            "# Tsuyama Paper Reproduction Fit Report",
            "",
            "## Boundary",
            "",
            "- This is a paper reproduction fit, not a physical calibration.",
            "- It does not modify EV full-grid, selected-annulus canonical bounds, or global material defaults.",
            "- It does not sign an accepted paper-calibrated raw candidate.",
            "- In response-compression mode, gamma is solved from target/raw Au exponent; SNR, signal, detection, and complexity are the residual tests.",
            f"- Primary score mode: `{primary_score_mode}`.",
            f"- Primary paper reproduction status: `{payload.get('primary_paper_reproduction_status')}`.",
            f"- Primary paper reproduction score: `{payload.get('primary_paper_reproduction_score')}`.",
            f"- Best candidate: `{payload.get('best_candidate_id')}`.",
            "",
            "## Best Candidates",
            "",
            rate_calib.dataframe_to_markdown(
                reproduction_frame.loc[:, best_columns].head(20)
            ),
            "",
            "## Score Decomposition",
            "",
            rate_calib.dataframe_to_markdown(decomposition_frame.head(20)),
            "",
            "## Raw Au Size-Response Residual Decomposition",
            "",
            "This decomposition is read-only. It refits Au20/Au30/Au40/Au60 "
            "log-log slopes by wavelength, geometry, and observable from the "
            "existing seed-median candidate summary.",
            "",
            rate_calib.dataframe_to_markdown(
                size_summary_frame[
                    size_summary_frame["observable"].eq("peak_height")
                ].head(12)
                if not size_summary_frame.empty and "observable" in size_summary_frame
                else size_summary_frame.head(12)
            ),
            "",
            "## Acceptance Boundary",
            "",
            f"- Candidate release status: `{payload['candidate_release_status']}`.",
            f"- No-Go reasons: `{json.dumps(payload['no_go_reasons'], ensure_ascii=False)}`.",
            f"- Diagnostic warnings: `{json.dumps(payload['diagnostic_warnings'], ensure_ascii=False)}`.",
            "",
            "## Output Files",
            "",
            f"- `{reproduction_summary_path}`",
            f"- `{reproduction_best_path}`",
            f"- `{reproduction_decomposition_path}`",
            f"- `{size_case_path}`",
            f"- `{size_summary_path}`",
            f"- `{size_report_path}`",
            f"- `{reproduction_json_path}`",
        ]
        reproduction_report_path.write_text(
            "\n".join(reproduction_lines) + "\n",
            encoding="utf-8",
        )
        size_report_lines = [
            "# Tsuyama Raw Au Size-Response Residual Decomposition",
            "",
            "## Boundary",
            "",
            "- This is a read-only diagnostic over existing seed-median summary rows.",
            "- It does not change selected-annulus bounds, simulation outputs, or release status.",
            "- Slopes are fitted from Au20/Au30/Au40/Au60 values by wavelength, geometry, and observable.",
            "",
            "## Candidate Summary",
            "",
            rate_calib.dataframe_to_markdown(size_summary_frame.head(40)),
            "",
            "## Case-Level Residuals",
            "",
            rate_calib.dataframe_to_markdown(size_case_frame.head(40)),
            "",
            "## Output Files",
            "",
            f"- `{size_case_path}`",
            f"- `{size_summary_path}`",
        ]
        size_report_path.write_text(
            "\n".join(size_report_lines) + "\n",
            encoding="utf-8",
        )
        reproduction_files = [
            reproduction_summary_path,
            reproduction_best_path,
            reproduction_decomposition_path,
            size_case_path,
            size_summary_path,
            size_report_path,
            reproduction_json_path,
            reproduction_report_path,
        ]
    inverse_available = bool(payload["inverse_context"]["has_family_ladder"])
    context_line = (
        "- It evaluates a completed family-ladder inverse search for candidate signing."
        if inverse_available
        else "- It freezes the current selected-annulus paper-audit baseline before inverse search."
    )
    lines = [
        "# Tsuyama Phase 2 Acceptance Report",
        "",
        "## Boundary",
        "",
        "- This report is read-only and does not rerun simulation.",
        context_line,
        f"- Acceptance aggregation mode: `{payload['acceptance_aggregation_mode']}`.",
        f"- Primary score mode: `{payload['primary_score_mode']}`.",
        "- Shadow all-crossing metrics are engineering sanity checks and do not enter the paper score.",
        "- In response-compression mode, gamma is solved from target/raw Au exponent; SNR, signal, detection, and complexity are the residual tests.",
        f"- Candidate release status: `{payload['candidate_release_status']}`.",
        f"- Primary paper reproduction status: `{payload.get('primary_paper_reproduction_status')}`.",
        f"- Primary paper reproduction score: `{payload.get('primary_paper_reproduction_score')}`.",
        f"- No-Go reasons: `{json.dumps(payload['no_go_reasons'], ensure_ascii=False)}`.",
        f"- Diagnostic warnings: `{json.dumps(payload['diagnostic_warnings'], ensure_ascii=False)}`.",
        "",
        "## Acceptance Summary",
        "",
        rate_calib.dataframe_to_markdown(summary),
        "",
        "## Guardrails",
        "",
        rate_calib.dataframe_to_markdown(guardrails),
        "",
        "## Input Manifest",
        "",
        "```json",
        json.dumps(payload["input_manifest"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Shadow All-Crossing Dashboard",
        "",
        rate_calib.dataframe_to_markdown(shadow),
        "",
        "## Output Files",
        "",
        f"- `{summary_path}`",
        f"- `{guardrail_path}`",
        f"- `{shadow_path}`",
        f"- `{json_path}`",
    ]
    if reproduction_files:
        lines.extend(["", "## Paper Reproduction Files", ""])
        lines.extend(f"- `{path}`" for path in reproduction_files)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary, payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a read-only Phase 2 acceptance report from existing summaries."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--joint-summary", type=Path, default=DEFAULT_JOINT_SUMMARY)
    parser.add_argument("--target-manifest", type=Path, default=None)
    parser.add_argument(
        "--classification-summary",
        type=Path,
        default=DEFAULT_CLASSIFICATION_SUMMARY,
    )
    parser.add_argument("--route-summary", type=Path, default=DEFAULT_ROUTE_SUMMARY)
    parser.add_argument(
        "--primary-score-mode",
        choices=sorted(PRIMARY_SCORE_COLUMNS),
        default="strict",
        help=(
            "Candidate signing sort mode. 'strict' preserves the legacy joint_fit_score; "
            "'formula' sorts by sqrt-scattering Table S1 target-mode score."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary, payload = write_outputs(
        output_dir=args.output_dir,
        joint_summary_path=args.joint_summary,
        target_manifest_path=args.target_manifest,
        classification_summary_path=args.classification_summary,
        route_summary_path=args.route_summary,
        primary_score_mode=args.primary_score_mode,
    )
    print(
        "Wrote Phase 2 acceptance report "
        f"({payload['candidate_release_status']}) to {args.output_dir}"
    )
    print(rate_calib.dataframe_to_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
