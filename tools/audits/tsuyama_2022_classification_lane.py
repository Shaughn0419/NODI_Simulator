#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from copy import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator.parameter_sweep import run_single_case_batch
from nodi_simulator.type_coerce import float_or_nan as _safe_float
from nodi_simulator.utils import compute_baseline_normalization
from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from tools.audits import tsuyama_selected_annulus_joint_fit as joint_fit

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_2022_classification_lane"
SCHEMA_ID = "tsuyama_2022_linked_488_window_532_max_classification_protocol_v2"
FEATURE_FILENAME = "tsuyama_2022_classification_features_v2.csv"
SUMMARY_FILENAME = "tsuyama_2022_classification_summary_v2.csv"
META_FILENAME = "tsuyama_2022_classification_meta_v2.json"
REPORT_FILENAME = "tsuyama_2022_classification_report_v2.md"
CLASSIFICATION_CLASSES: tuple[tuple[str, int], ...] = (
    ("gold", 40),
    ("gold", 60),
    ("silver", 40),
    ("silver", 60),
)
CLASSIFICATION_WAVELENGTHS_NM = (488, 532)
SVM_FEATURE_COLUMNS_RAW = (
    "peak_height_488",
    "peak_width_s_488",
    "peak_height_532",
    "peak_width_s_532",
)
SVM_FEATURE_COLUMNS_TRANSFERRED = (
    "paper_transfer_peak_height_488",
    "peak_width_s_488",
    "paper_transfer_peak_height_532",
    "peak_width_s_532",
)


def class_label(material: str, diameter_nm: int) -> str:
    prefix = "Au" if material == "gold" else "Ag" if material == "silver" else material
    return f"{prefix}{int(diameter_nm)}"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def extract_best_peak_feature(event: dict[str, Any], *, wavelength_nm: int) -> dict[str, Any]:
    features = event.get("features_nodi") or event.get("features") or {}
    peaks = list(features.get("peaks", []))
    threshold = _safe_float(event.get("threshold"))
    robust_std = max(_safe_float(event.get("threshold_robust_std")), 1e-15)
    if not peaks:
        return {
            f"detected_{wavelength_nm}": False,
            f"n_peaks_{wavelength_nm}": 0,
            f"peak_height_{wavelength_nm}": float("nan"),
            f"peak_width_s_{wavelength_nm}": float("nan"),
            f"peak_time_s_{wavelength_nm}": float("nan"),
            f"peak_window_start_s_{wavelength_nm}": float("nan"),
            f"peak_window_end_s_{wavelength_nm}": float("nan"),
            f"peak_margin_z_{wavelength_nm}": float("nan"),
            f"threshold_{wavelength_nm}": threshold,
            f"threshold_robust_std_{wavelength_nm}": robust_std,
        }
    best = max(peaks, key=lambda peak: _safe_float(peak.get("peak_height")))
    height = _safe_float(best.get("peak_height"))
    return {
        f"detected_{wavelength_nm}": True,
        f"n_peaks_{wavelength_nm}": int(len(peaks)),
        f"peak_height_{wavelength_nm}": height,
        f"peak_width_s_{wavelength_nm}": _safe_float(best.get("peak_width_s")),
        f"peak_time_s_{wavelength_nm}": _safe_float(best.get("peak_time_s")),
        f"peak_window_start_s_{wavelength_nm}": _safe_float(
            best.get("peak_threshold_left_time_s"),
            _safe_float(best.get("peak_time_s")) - 0.5 * _safe_float(best.get("peak_width_s"), 0.0),
        ),
        f"peak_window_end_s_{wavelength_nm}": _safe_float(
            best.get("peak_threshold_right_time_s"),
            _safe_float(best.get("peak_time_s")) + 0.5 * _safe_float(best.get("peak_width_s"), 0.0),
        ),
        f"peak_margin_z_{wavelength_nm}": float(max(height - threshold, 0.0) / robust_std),
        f"threshold_{wavelength_nm}": threshold,
        f"threshold_robust_std_{wavelength_nm}": robust_std,
    }

def _bool_mask(df: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column in df.columns:
        return df[column].astype(bool)
    return pd.Series([bool(default)] * len(df), index=df.index, dtype=bool)


def _event_time_and_signal(event: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    signal = np.asarray(event.get("signal_noisy", []), dtype=float)
    if "pulse_time_s" in event:
        time_s = np.asarray(event["pulse_time_s"], dtype=float)
    else:
        trajectory = event.get("trajectory", {})
        time_s = np.asarray(trajectory.get("time_s", []), dtype=float)
    if signal.size == 0 or time_s.size != signal.size:
        return np.empty(0, dtype=float), np.empty(0, dtype=float)
    return time_s, signal


def extract_window_max_feature(
    event: dict[str, Any],
    *,
    wavelength_nm: int,
    window_start_s: float,
    window_end_s: float,
    linked_window_width_s: float,
) -> dict[str, Any]:
    threshold = _safe_float(event.get("threshold"))
    robust_std = max(_safe_float(event.get("threshold_robust_std")), 1e-15)
    time_s, signal = _event_time_and_signal(event)
    if (
        time_s.size == 0
        or signal.size == 0
        or not np.isfinite(window_start_s)
        or not np.isfinite(window_end_s)
        or window_end_s < window_start_s
    ):
        return {
            f"detected_{wavelength_nm}": False,
            f"n_peaks_{wavelength_nm}": 0,
            f"peak_height_{wavelength_nm}": float("nan"),
            f"peak_width_s_{wavelength_nm}": linked_window_width_s,
            f"peak_time_s_{wavelength_nm}": float("nan"),
            f"peak_window_start_s_{wavelength_nm}": window_start_s,
            f"peak_window_end_s_{wavelength_nm}": window_end_s,
            f"peak_margin_z_{wavelength_nm}": float("nan"),
            f"threshold_{wavelength_nm}": threshold,
            f"threshold_robust_std_{wavelength_nm}": robust_std,
            f"linked_window_feature_status_{wavelength_nm}": "missing_signal_or_invalid_window",
        }
    mask = (time_s >= float(window_start_s)) & (time_s <= float(window_end_s))
    if not bool(np.any(mask)):
        idx = int(np.argmin(np.abs(time_s - 0.5 * (float(window_start_s) + float(window_end_s)))))
        mask = np.zeros_like(time_s, dtype=bool)
        mask[idx] = True
    local_signal = signal[mask]
    local_time = time_s[mask]
    local_idx = int(np.argmax(local_signal))
    height = float(local_signal[local_idx])
    peak_time = float(local_time[local_idx])
    return {
        f"detected_{wavelength_nm}": bool(height >= threshold),
        f"n_peaks_{wavelength_nm}": int(1 if height >= threshold else 0),
        f"peak_height_{wavelength_nm}": height,
        f"peak_width_s_{wavelength_nm}": linked_window_width_s,
        f"peak_time_s_{wavelength_nm}": peak_time,
        f"peak_window_start_s_{wavelength_nm}": float(window_start_s),
        f"peak_window_end_s_{wavelength_nm}": float(window_end_s),
        f"peak_margin_z_{wavelength_nm}": float((height - threshold) / robust_std),
        f"threshold_{wavelength_nm}": threshold,
        f"threshold_robust_std_{wavelength_nm}": robust_std,
        f"linked_window_feature_status_{wavelength_nm}": "max_within_488_pulse_window",
    }


def build_linked_feature_rows(
    events_by_class_wavelength: dict[tuple[str, int, int], list[dict[str, Any]]],
    *,
    width_nm: int,
    depth_nm: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for material, diameter_nm in CLASSIFICATION_CLASSES:
        events_488 = events_by_class_wavelength.get((material, diameter_nm, 488), [])
        events_532 = events_by_class_wavelength.get((material, diameter_nm, 532), [])
        if not events_488 or not events_532:
            continue
        n_events = min(len(events_488), len(events_532))
        for event_index in range(n_events):
            feature_488 = extract_best_peak_feature(events_488[event_index], wavelength_nm=488)
            window_start = _safe_float(feature_488.get("peak_window_start_s_488"))
            window_end = _safe_float(feature_488.get("peak_window_end_s_488"))
            window_width = _safe_float(feature_488.get("peak_width_s_488"))
            feature_532 = extract_window_max_feature(
                events_532[event_index],
                wavelength_nm=532,
                window_start_s=window_start,
                window_end_s=window_end,
                linked_window_width_s=window_width,
            )
            row: dict[str, Any] = {
                "schema_id": SCHEMA_ID,
                "class_label": class_label(material, diameter_nm),
                "particle_material": material,
                "particle_diameter_nm": int(diameter_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "linked_event_index": int(event_index),
                "linked_event_policy": "common_random_numbers_488_pulse_window_532_max",
            }
            row.update(feature_488)
            row.update(feature_532)
            row["usable_both_detected"] = bool(
                row.get("detected_488", False) and row.get("detected_532", False)
            )
            row["usable_488_detected"] = bool(row.get("detected_488", False))
            row["usable_for_paper_svm"] = bool(
                row["usable_488_detected"] and np.isfinite(_safe_float(row.get("peak_height_532")))
            )
            rows.append(row)
    return pd.DataFrame(rows)


def compute_silver_transfer_gains(feature_table: pd.DataFrame) -> dict[int, float]:
    gains: dict[int, float] = {}
    if feature_table.empty:
        return {wavelength_nm: float("nan") for wavelength_nm in CLASSIFICATION_WAVELENGTHS_NM}
    for wavelength_nm in CLASSIFICATION_WAVELENGTHS_NM:
        column = f"peak_height_{wavelength_nm}"
        au40 = feature_table[
            (feature_table["particle_material"] == "gold")
            & (feature_table["particle_diameter_nm"].astype(int) == 40)
            & _bool_mask(feature_table, "usable_for_paper_svm")
        ][column]
        ag40 = feature_table[
            (feature_table["particle_material"] == "silver")
            & (feature_table["particle_diameter_nm"].astype(int) == 40)
            & _bool_mask(feature_table, "usable_for_paper_svm")
        ][column]
        observed = float(ag40.mean()) / max(float(au40.mean()), 1e-12) if len(au40) and len(ag40) else float("nan")
        target = (
            lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][wavelength_nm]
            / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][wavelength_nm]
        )
        gains[wavelength_nm] = (
            float(target / observed) if np.isfinite(observed) and observed > 0 else float("nan")
        )
    return gains


def apply_silver_transfer_columns(
    feature_table: pd.DataFrame,
    gains: dict[int, float],
) -> pd.DataFrame:
    out = feature_table.copy()
    for wavelength_nm in CLASSIFICATION_WAVELENGTHS_NM:
        source = f"peak_height_{wavelength_nm}"
        target = f"paper_transfer_peak_height_{wavelength_nm}"
        gain = float(gains.get(wavelength_nm, float("nan")))
        silver_mask = out["particle_material"].astype(str) == "silver"
        out[target] = out[source]
        if np.isfinite(gain):
            out.loc[silver_mask, target] = out.loc[silver_mask, source].astype(float) * gain
        out[f"paper_transfer_gain_{wavelength_nm}"] = gain
    return out


def summarize_feature_table(
    feature_table: pd.DataFrame,
    *,
    n_events: int,
    width_nm: int,
    depth_nm: int,
    silver_transfer_gains: dict[int, float],
) -> dict[str, Any]:
    usable_for_paper_svm = (
        feature_table[_bool_mask(feature_table, "usable_for_paper_svm")]
        if not feature_table.empty
        else feature_table
    )
    usable_both_detected = (
        feature_table[_bool_mask(feature_table, "usable_both_detected")]
        if not feature_table.empty
        else feature_table
    )
    class_counts = (
        usable_for_paper_svm.groupby("class_label", dropna=False).size().to_dict()
        if not usable_for_paper_svm.empty
        else {}
    )
    min_class_count = min(class_counts.values()) if class_counts else 0
    return {
        "schema_id": SCHEMA_ID,
        "n_events_requested_per_class": int(n_events),
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "class_count": int(len(CLASSIFICATION_CLASSES)),
        "feature_rows": int(len(feature_table)),
        "usable_both_detected_rows": int(len(usable_both_detected)),
        "usable_for_paper_svm_rows": int(len(usable_for_paper_svm)),
        "usable_min_class_count": int(min_class_count),
        "usable_class_counts_json": _json_dumps({str(k): int(v) for k, v in class_counts.items()}),
        "paper_transfer_gain_488": float(silver_transfer_gains.get(488, float("nan"))),
        "paper_transfer_gain_532": float(silver_transfer_gains.get(532, float("nan"))),
        "classification_feature_policy": (
            "linked_488_detected_pulse_window_532_maximum"
        ),
        "paper_protocol_match_status": (
            "feature_export_matches_488_pulse_window_532_maximum_protocol"
        ),
    }


def evaluate_optional_svm(
    feature_table: pd.DataFrame,
    *,
    random_seed: int,
    use_paper_transfer: bool,
) -> dict[str, Any]:
    try:
        model_selection = importlib.import_module("sklearn.model_selection")
        pipeline_mod = importlib.import_module("sklearn.pipeline")
        preprocessing = importlib.import_module("sklearn.preprocessing")
        svm_mod = importlib.import_module("sklearn.svm")
        metrics_mod = importlib.import_module("sklearn.metrics")
    except ModuleNotFoundError:
        return {
            "sklearn_available": False,
            "svm_accuracy_status": "not_computed_missing_optional_sklearn_dependency",
            "svm_accuracy_claim_level": "no_accuracy_claim",
        }

    usable = feature_table[feature_table["usable_for_paper_svm"].astype(bool)].copy()
    feature_columns = SVM_FEATURE_COLUMNS_TRANSFERRED if use_paper_transfer else SVM_FEATURE_COLUMNS_RAW
    usable = usable.replace([np.inf, -np.inf], np.nan).dropna(subset=list(feature_columns))
    class_counts = usable.groupby("class_label", dropna=False).size()
    if usable.empty or len(class_counts) < 2 or int(class_counts.min()) < 10:
        return {
            "sklearn_available": True,
            "svm_accuracy_status": "not_computed_insufficient_usable_class_counts",
            "svm_accuracy_claim_level": "no_accuracy_claim",
        }

    x = usable[list(feature_columns)].to_numpy(dtype=float)
    y = usable["class_label"].astype(str).to_numpy()
    model = pipeline_mod.make_pipeline(
        preprocessing.StandardScaler(),
        svm_mod.SVC(kernel="rbf", C=1.0, gamma=0.1),
    )
    splitter = model_selection.StratifiedKFold(n_splits=10, shuffle=True, random_state=int(random_seed))
    cv_scores = model_selection.cross_val_score(model, x, y, cv=splitter)
    x_train, x_test, y_train, y_test = model_selection.train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=int(random_seed),
        stratify=y,
    )
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    return {
        "sklearn_available": True,
            "svm_accuracy_status": "computed_paper_feature_protocol_surrogate_simulation",
            "svm_accuracy_claim_level": (
                "simulated_feature_accuracy_not_experimental_reproduction"
            ),
        "svm_feature_columns_json": _json_dumps(list(feature_columns)),
        "svm_cv_accuracy_mean": float(np.mean(cv_scores)),
        "svm_cv_accuracy_std": float(np.std(cv_scores, ddof=1)) if len(cv_scores) > 1 else 0.0,
        "svm_holdout_accuracy": float(metrics_mod.accuracy_score(y_test, predicted)),
    }


def _simulate_events_for_class_wavelength(
    candidate: joint_fit.JointFitCandidate,
    *,
    material: str,
    diameter_nm: int,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    n_events: int,
    random_seed: int,
    scenario_id: str,
) -> list[dict[str, Any]]:
    cfg = joint_fit.build_joint_cfg(
        candidate,
        n_events=n_events,
        random_seed=random_seed,
        scenario_id=scenario_id,
    )
    cfg = replace(
        cfg,
        n_events=int(n_events),
        random_seed=int(random_seed),
        random_sequence_policy="common_random_numbers",
        event_sampling_policy="random",
    )
    optical = copy(rate_calib.build_candidate_optical_template(rate_calib.candidate_by_id()[candidate.base_candidate_id]))
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    particle = lane.make_tsuyama_2022_table_s1_particle(material, diameter_nm, wavelength_nm)
    baseline_particle = lane.make_tsuyama_2022_table_s1_particle("gold", 40, wavelength_nm)
    baseline = compute_baseline_normalization(
        baseline_particle,
        lane.WATER,
        optical,
        lane.THETA_GRID_RAD,
        channel=channel,
        sim_cfg=cfg,
    )
    batch = run_single_case_batch(
        particle,
        lane.WATER,
        channel,
        optical,
        cfg,
        float(baseline["E_sca_ref"]),
        lane.THETA_GRID_RAD,
        retain_event_traces=True,
        stream_summary_only=False,
    )
    return list(batch.get("events", []))


def run_classification_lane(
    *,
    output_dir: Path,
    base_candidate_id: str,
    variant_id: str,
    scenario_id: str,
    width_nm: int,
    depth_nm: int,
    n_events: int,
    random_seed: int,
    compute_svm: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = joint_fit.build_joint_candidates(
        base_candidate_ids=[base_candidate_id],
        variant_ids=[variant_id],
    )[0]
    start = time.time()
    events_by_class_wavelength: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
    for material, diameter_nm in CLASSIFICATION_CLASSES:
        for wavelength_nm in CLASSIFICATION_WAVELENGTHS_NM:
            print(
                f"[classification-lane] {class_label(material, diameter_nm)} {wavelength_nm}nm",
                flush=True,
            )
            events_by_class_wavelength[(material, diameter_nm, wavelength_nm)] = (
                _simulate_events_for_class_wavelength(
                    candidate,
                    material=material,
                    diameter_nm=diameter_nm,
                    wavelength_nm=wavelength_nm,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    n_events=n_events,
                    random_seed=random_seed,
                    scenario_id=scenario_id,
                )
            )

    features = build_linked_feature_rows(events_by_class_wavelength, width_nm=width_nm, depth_nm=depth_nm)
    transfer_gains = compute_silver_transfer_gains(features)
    features = apply_silver_transfer_columns(features, transfer_gains)
    summary_row = summarize_feature_table(
        features,
        n_events=n_events,
        width_nm=width_nm,
        depth_nm=depth_nm,
        silver_transfer_gains=transfer_gains,
    )
    summary_row.update(
        evaluate_optional_svm(
            features,
            random_seed=random_seed,
            use_paper_transfer=True,
        )
        if compute_svm
        else {
            "sklearn_available": False,
            "svm_accuracy_status": "not_requested_feature_export_only",
            "svm_accuracy_claim_level": "no_accuracy_claim",
        }
    )
    summary = pd.DataFrame([summary_row])

    features_path = output_dir / FEATURE_FILENAME
    summary_path = output_dir / SUMMARY_FILENAME
    features.to_csv(features_path, index=False)
    summary.to_csv(summary_path, index=False)
    meta = {
        "schema_id": SCHEMA_ID,
        "base_candidate_id": base_candidate_id,
        "variant_id": variant_id,
        "candidate_id": candidate.candidate_id,
        "scenario_id": scenario_id,
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "n_events": int(n_events),
        "random_seed": int(random_seed),
        "runtime_s": time.time() - start,
        "feature_path": str(features_path),
        "summary_path": str(summary_path),
        "paper_target_accuracy": "71.9 +/- 4.0%",
        "paper_classes": [class_label(material, diameter_nm) for material, diameter_nm in CLASSIFICATION_CLASSES],
    }
    rate_calib.write_json(output_dir / META_FILENAME, meta)
    write_report(output_dir, summary=summary, meta=meta)
    return features, summary, meta


def write_report(output_dir: Path, *, summary: pd.DataFrame, meta: dict[str, Any]) -> Path:
    report_path = output_dir / REPORT_FILENAME
    lines = [
        "# Tsuyama 2022 Linked 488/532 Classification Lane",
        "",
        "## Scope",
        "",
        "- This lane exports linked 488/532 event features for the 2022 Au/Ag classification protocol.",
        "- It does not modify joint-fit scoring, global simulator defaults, or EV ranking.",
        "- The 532 feature is measured as the maximum within the matched 488 pulse window.",
        "- Any computed SVM value is simulated feature accuracy, not an experimental reproduction claim.",
        "",
        "## Metadata",
        "",
        f"- schema: `{meta['schema_id']}`",
        f"- candidate: `{meta['candidate_id']}`",
        f"- scenario: `{meta['scenario_id']}`",
        f"- geometry: `{meta['width_nm']}x{meta['depth_nm']}`",
        f"- n_events/class: `{meta['n_events']}`",
        f"- random_seed: `{meta['random_seed']}`",
        "",
        "## Summary",
        "",
        rate_calib.dataframe_to_markdown(summary),
        "",
        "## Output Files",
        "",
        f"- `{FEATURE_FILENAME}`",
        f"- `{SUMMARY_FILENAME}`",
        f"- `{META_FILENAME}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export linked 488/532 features for Tsuyama 2022 Au/Ag classification audit."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--base-candidate-id", default="baseline_current_estimates")
    parser.add_argument("--variant-id", default="paper_5sigma_signal_transfer_fit")
    parser.add_argument("--scenario-id", default="nodi_2022_10sigma_single")
    parser.add_argument("--width-nm", type=int, default=800)
    parser.add_argument("--depth-nm", type=int, default=550)
    parser.add_argument("--n-events", type=int, default=400)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument(
        "--compute-svm",
        action="store_true",
        help="Compute optional surrogate SVM accuracy when scikit-learn is installed.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run_classification_lane(
        output_dir=Path(args.output_dir),
        base_candidate_id=str(args.base_candidate_id),
        variant_id=str(args.variant_id),
        scenario_id=str(args.scenario_id),
        width_nm=int(args.width_nm),
        depth_nm=int(args.depth_nm),
        n_events=int(args.n_events),
        random_seed=int(args.random_seed),
        compute_svm=bool(args.compute_svm),
    )


if __name__ == "__main__":
    main()
