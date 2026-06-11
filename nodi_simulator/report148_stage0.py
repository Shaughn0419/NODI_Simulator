from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from tools._common import write_csv_records, write_json_file

from .config_trace import build_minimal_config_trace


T8_REQUIRED_COLUMNS = (
    "E_sca_normalized",
    "cross_term_detector_integrated",
    "signal_detector_integrated",
    "roi_vs_scalar_signal_ratio",
)
T8_SIDECAR_KEY_COLUMNS = (
    "particle_name",
    "particle_material",
    "particle_family",
    "particle_diameter_nm",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "normalization_scope",
    "reference_route",
    "reference_na_edge_policy",
    "field_coordinate_measure",
    "bfp_to_angle_jacobian_applied",
    "detector_forward_model",
    "readout_observable_mode",
    "case_id",
    "config_hash",
    "case_hash",
)
T8_GROUP_COLUMNS = (
    "wavelength_nm",
    "particle_family",
    "normalization_scope",
    "reference_route",
    "reference_na_edge_policy",
    "field_coordinate_measure",
    "bfp_to_angle_jacobian_applied",
    "detector_forward_model",
    "readout_observable_mode",
)
T6_REQUIRED_COLUMNS = (
    "particle_family",
    "wavelength_nm",
    "cross_term_detector_integrated",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_columns(
    fieldnames: Sequence[str] | None,
    required: tuple[str, ...],
    *,
    label: str,
) -> None:
    missing = [column for column in required if not fieldnames or column not in fieldnames]
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _finite_float(row: dict[str, str], column: str, *, label: str) -> float:
    raw = row.get(column, "")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} column {column} is not a float: {raw!r}") from exc
    if not np.isfinite(value):
        raise ValueError(f"{label} column {column} is not finite: {raw!r}")
    return value


def _quantile_summary(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(arr)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _is_ev_family(family: str) -> bool:
    lowered = str(family).lower()
    return "gold" not in lowered and any(
        token in lowered
        for token in ("exo", "membrane", "msc", "biomim", "sev", "vesicle", "ev")
    )


def compute_t8_static_fields(row: dict[str, str]) -> dict[str, float | str]:
    self_collapsed = _finite_float(row, "E_sca_normalized", label="T8 summary row") ** 2
    cross_joint = _finite_float(row, "cross_term_detector_integrated", label="T8 summary row")
    b_static = _finite_float(row, "signal_detector_integrated", label="T8 summary row")
    roi_ratio = _finite_float(row, "roi_vs_scalar_signal_ratio", label="T8 summary row")
    abs_c = abs(b_static) / max(abs(roi_ratio), 1e-30)
    a_static = self_collapsed + cross_joint
    return {
        "self_collapsed_signal_static": float(self_collapsed),
        "cross_joint_signal_static": float(cross_joint),
        "A_static_signal_signed": float(a_static),
        "B_static_signal_signed": float(b_static),
        "abs_C_signal_static": float(abs_c),
        "A_vs_B_abs_signal_ratio_static": float(abs(a_static) / max(abs(b_static), 1e-30)),
        "A_vs_C_abs_signal_ratio_static": float(abs(a_static) / max(abs_c, 1e-30)),
        "report148_stage0_task": "T8",
        "report148_stage0_claim_level": "static_postprocess_relative_audit_only",
        "report148_stage0_status": "zero_rerun_static_postprocess",
        "report148_stage0_polarity_status": "A_vs_C_unsigned_only_abs_ratio",
        "report148_stage0_detector_truth_status": "not_calibrated_detector_truth",
    }


def write_t8_static_ratio_outputs(
    *,
    summary_csv: Path,
    output_csv: Path,
    summary_table_csv: Path,
    metadata_json: Path,
) -> dict[str, Any]:
    with summary_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, T8_REQUIRED_COLUMNS, label=str(summary_csv))
        input_fieldnames = list(reader.fieldnames or [])
        added_columns = [
            "self_collapsed_signal_static",
            "cross_joint_signal_static",
            "A_static_signal_signed",
            "B_static_signal_signed",
            "abs_C_signal_static",
            "A_vs_B_abs_signal_ratio_static",
            "A_vs_C_abs_signal_ratio_static",
            "report148_stage0_task",
            "report148_stage0_claim_level",
            "report148_stage0_status",
            "report148_stage0_polarity_status",
            "report148_stage0_detector_truth_status",
        ]
        grouped: dict[tuple[str, ...], dict[str, list[float]]] = defaultdict(
            lambda: {
                "A_vs_B_abs_signal_ratio_static": [],
                "A_vs_C_abs_signal_ratio_static": [],
            }
        )
        output_fieldnames = [
            column for column in T8_SIDECAR_KEY_COLUMNS if column in input_fieldnames
        ] + added_columns
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", encoding="utf-8", newline="") as out_handle:
            writer = csv.DictWriter(
                out_handle,
                fieldnames=output_fieldnames,
            )
            writer.writeheader()
            row_count = 0
            for row in reader:
                metrics = compute_t8_static_fields(row)
                row_count += 1
                for metric_name in (
                    "A_vs_B_abs_signal_ratio_static",
                    "A_vs_C_abs_signal_ratio_static",
                ):
                    grouped[tuple(row.get(column, "") for column in T8_GROUP_COLUMNS)][metric_name].append(
                        float(metrics[metric_name])
                    )
                serializable_row = {
                    key: row.get(key, "")
                    for key in output_fieldnames
                    if key not in added_columns
                }
                serializable_row.update(
                    {
                        key: (
                            f"{value:.17g}" if isinstance(value, float) else str(value)
                        )
                        for key, value in metrics.items()
                    }
                )
                writer.writerow(serializable_row)

    summary_records: list[dict[str, Any]] = []
    for group_key, metric_values in sorted(grouped.items()):
        record: dict[str, Any] = {
            column: group_key[idx] for idx, column in enumerate(T8_GROUP_COLUMNS)
        }
        record["rows_in_group"] = len(metric_values["A_vs_B_abs_signal_ratio_static"])
        for metric_name, values in metric_values.items():
            stats = _quantile_summary(values)
            for stat_name, stat_value in stats.items():
                record[f"{metric_name}_{stat_name}"] = stat_value
        record["report148_stage0_task"] = "T8"
        record["report148_stage0_claim_level"] = "static_postprocess_relative_audit_only"
        record["report148_stage0_status"] = "grouped_zero_rerun_static_summary"
        summary_records.append(record)
    write_csv_records(summary_table_csv, summary_records)

    metadata = {
        "task": "T8",
        "generated_at": _utc_now_iso(),
        "source_summary_csv": str(summary_csv),
        "source_summary_sha256": _sha256_file(summary_csv),
        "output_csv": str(output_csv),
        "summary_table_csv": str(summary_table_csv),
        "row_count": row_count,
        "sidecar_key_columns": [
            column for column in T8_SIDECAR_KEY_COLUMNS if column in input_fieldnames
        ],
        "group_columns": list(T8_GROUP_COLUMNS),
        "required_columns": list(T8_REQUIRED_COLUMNS),
        "claim_level": "static_postprocess_relative_audit_only",
        "status": "zero_rerun_static_postprocess",
        "polarity_boundary": "A_vs_C uses abs_C and does not support signed polarity inference",
    }
    write_json_file(metadata_json, metadata)
    return metadata


def _signed_cross_stats(cross_values: list[float]) -> dict[str, float]:
    arr = np.asarray(cross_values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("no finite signed cross values")
    scale = float(np.nanmedian(np.abs(arr)))
    eps = max(1e-15, 1e-12 * scale)
    return {
        "median_signed_cross_term_detector_integrated": float(np.median(arr)),
        "median_abs_cross_term_detector_integrated": float(np.median(np.abs(arr))),
        "cross_term_zero_tolerance": float(eps),
        "cross_term_negative_fraction": float(np.mean(arr < -eps)),
        "cross_term_near_zero_fraction": float(np.mean(np.abs(arr) <= eps)),
        "cross_term_positive_fraction": float(np.mean(arr > eps)),
        "cross_term_sample_count": int(arr.size),
    }


def repair_t6_mechanism_chain_outputs(
    *,
    mechanism_chain_csv: Path,
    summary_csv: Path,
    output_csv: Path,
    metadata_json: Path,
) -> dict[str, Any]:
    cross_by_wavelength: dict[str, list[float]] = defaultdict(list)
    with summary_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, T6_REQUIRED_COLUMNS, label=str(summary_csv))
        for row in reader:
            if not _is_ev_family(row.get("particle_family", "")):
                continue
            wavelength = str(row.get("wavelength_nm", "")).strip()
            if not wavelength:
                raise ValueError("summary row is missing wavelength_nm for T6 repair")
            cross_by_wavelength[wavelength].append(
                _finite_float(row, "cross_term_detector_integrated", label="T6 summary row")
            )
    if not cross_by_wavelength:
        raise ValueError("no EV rows were found for T6 repair")

    signed_stats = {
        wavelength: _signed_cross_stats(values)
        for wavelength, values in sorted(cross_by_wavelength.items())
    }

    with mechanism_chain_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if "wavelength_nm" not in fieldnames:
            raise ValueError(f"{mechanism_chain_csv} is missing wavelength_nm")
        output_records: list[dict[str, Any]] = []
        for row in reader:
            wavelength = str(row.get("wavelength_nm", "")).strip()
            if wavelength not in signed_stats:
                raise ValueError(
                    f"mechanism chain wavelength {wavelength!r} was not found in signed stats"
                )
            record = dict(row)
            legacy_value = record.pop("median_cross_term_detector_integrated", None)
            if legacy_value is not None:
                record["median_cross_term_detector_integrated_magnitude_deprecated"] = legacy_value
            record["legacy_cross_term_column_status"] = "deprecated_magnitude_only"
            record.update(signed_stats[wavelength])
            record["lineage"] = "v1_channel_angular_surrogate"
            record["lineage_provenance"] = "inferred_from_stage0_v1_summary_contract"
            record["phase_convention"] = "current_uncalibrated"
            record["phase_convention_provenance"] = "inferred_from_report147_signed_audit_context"
            record["report148_stage0_task"] = "T6"
            record["report148_stage0_claim_level"] = "signed_relative_interference_audit_only"
            record["report148_stage0_status"] = "zero_rerun_signed_table_repair"
            output_records.append(record)
    write_csv_records(output_csv, output_records)

    metadata = {
        "task": "T6",
        "generated_at": _utc_now_iso(),
        "source_mechanism_chain_csv": str(mechanism_chain_csv),
        "source_mechanism_chain_sha256": _sha256_file(mechanism_chain_csv),
        "source_summary_csv": str(summary_csv),
        "source_summary_sha256": _sha256_file(summary_csv),
        "output_csv": str(output_csv),
        "wavelengths": sorted(signed_stats.keys(), key=float),
        "signed_stats": signed_stats,
        "claim_level": "signed_relative_interference_audit_only",
        "status": "zero_rerun_signed_table_repair",
    }
    write_json_file(metadata_json, metadata)
    return metadata


def write_t5_provenance_backfill_outputs(
    *,
    run_manifest_json: Path,
    diagnostic_rows_csvs: list[Path],
    output_json: Path,
    output_csv: Path,
) -> dict[str, Any]:
    from tools.lens_b_ev_gold_fullgrid_runner import (
        _cfg_for_normalization_lane,
        build_frozen_b_cfg,
    )

    manifest = json.loads(run_manifest_json.read_text(encoding="utf-8"))
    base_cfg, optical_template = build_frozen_b_cfg(
        int(manifest["n_events"]),
        int(manifest["seed"]),
    )
    lane_records: list[dict[str, Any]] = []
    lane_backfills: dict[str, Any] = {}
    for diagnostic_path in diagnostic_rows_csvs:
        with diagnostic_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            first_row = next(reader, None)
        if first_row is None:
            raise ValueError(f"diagnostic rows file is empty: {diagnostic_path}")
        normalization_lane = str(first_row.get("normalization_lane", "")).strip()
        if not normalization_lane:
            raise ValueError(f"{diagnostic_path} is missing normalization_lane")
        lane_cfg = _cfg_for_normalization_lane(base_cfg, normalization_lane)
        trace = build_minimal_config_trace(
            cfg=lane_cfg,
            optical_template=optical_template,
            normalization_view=normalization_lane,
            config_trace_status="backfilled",
            field_origin_overrides={
                "reference_model": "reconstructed_from_code",
                "reference_route": "reconstructed_from_code",
                "reference_na_edge_policy": "source_diagnostic_rows_or_reconstructed_from_code",
                "noise_std": "reconstructed_from_code",
                "shot_noise_scale": "source_diagnostic_rows_or_reconstructed_from_code",
                "post_readout_noise_std": "reconstructed_from_code",
                "field_coordinate_measure": "reconstructed_from_code",
                "bfp_to_angle_jacobian_applied": "reconstructed_from_code",
                "interference_overlap_mode": "reconstructed_from_code",
                "scattering_projection_mode": "reconstructed_from_code",
                "NA_collection": "optical_template_reconstructed_from_code",
                "rho": "reconstructed_from_code",
                "threshold_sigma": "source_diagnostic_rows_or_reconstructed_from_code",
                "normalization_view": "source_diagnostic_rows",
            },
            field_source_overrides={
                "reference_model": "tools.lens_b_ev_gold_fullgrid_runner.build_frozen_b_cfg",
                "reference_route": "resolve_reference_route_name(build_frozen_b_cfg().reference_model, cfg.reference_route)",
                "reference_na_edge_policy": f"{diagnostic_path.name}:reference_na_edge_policy",
                "shot_noise_scale": f"{diagnostic_path.name}:shot_noise_scale",
                "threshold_sigma": f"{diagnostic_path.name}:threshold_sigma",
                "normalization_view": f"{diagnostic_path.name}:normalization_lane",
            },
        )
        lane_backfills[normalization_lane] = {
            "diagnostic_rows_csv": str(diagnostic_path),
            "diagnostic_rows_sha256": _sha256_file(diagnostic_path),
            "runtime_config_subset_backfill": trace.runtime_config_subset,
            "manifest_field_origins": trace.manifest_field_origins,
            "manifest_field_sources": trace.manifest_field_sources,
            "manifest_field_confidence": trace.manifest_field_confidence,
            "unresolved_fields": list(trace.unresolved_fields),
        }
        for field_name in trace.manifest_field_origins:
            lane_records.append(
                {
                    "normalization_view": normalization_lane,
                    "field": field_name,
                    "value": trace.runtime_config_subset.get(field_name),
                    "origin": trace.manifest_field_origins[field_name],
                    "source": trace.manifest_field_sources[field_name],
                    "confidence": trace.manifest_field_confidence[field_name],
                    "config_trace_status": trace.runtime_config_subset["config_trace_status"],
                    "backfilled_at": trace.runtime_config_subset.get("backfilled_at"),
                    "source_manifest": str(run_manifest_json),
                    "source_manifest_sha256": _sha256_file(run_manifest_json),
                    "source_diagnostic_rows": str(diagnostic_path),
                }
            )
    write_csv_records(output_csv, lane_records)

    payload = {
        "task": "T5",
        "generated_at": _utc_now_iso(),
        "config_trace_status": "backfilled",
        "source_manifest": str(run_manifest_json),
        "source_manifest_sha256": _sha256_file(run_manifest_json),
        "existing_runtime_config_subset_keys": sorted(
            manifest.get("runtime_config_subset", {}).keys()
        ),
        "lane_backfills": lane_backfills,
        "notes": [
            "Historical manifest and diagnostic rows were not modified in place.",
            "interference_overlap_status remains unresolved without case-level reference evaluation.",
        ],
    }
    write_json_file(output_json, payload)
    return payload
