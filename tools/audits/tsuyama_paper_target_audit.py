#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from tools.audits import tsuyama_selected_annulus_joint_fit as joint_fit

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_phase2_paper_target_audit_v1"
SCHEMA_ID = "tsuyama_phase2_paper_target_audit_v1"
CSV_FILENAME = "tsuyama_paper_targets_v1.csv"
JSON_FILENAME = "tsuyama_paper_targets_v1.json"
REPORT_FILENAME = "tsuyama_paper_target_audit_report_v1.md"


def _target_record(
    *,
    target_name: str,
    paper_or_source: str,
    figure_table_or_protocol_anchor: str,
    mechanism_scope: str,
    value: float | str,
    band_low: float | None,
    band_high: float | None,
    confidence: str,
    usable_for_hard_acceptance: bool,
    notes: str,
    target_mode: str = "",
    target_integrity_status: str = "",
    recommended_signal_ratio_target_mode: str = "",
    table_s1_interferometric_consistency_residual: float | None = None,
) -> dict[str, Any]:
    return {
        "schema_id": SCHEMA_ID,
        "target_name": target_name,
        "target_mode": target_mode,
        "paper_or_source": paper_or_source,
        "figure_table_or_protocol_anchor": figure_table_or_protocol_anchor,
        "mechanism_scope": mechanism_scope,
        "value": value,
        "band_low": band_low,
        "band_high": band_high,
        "confidence": confidence,
        "usable_for_hard_acceptance": bool(usable_for_hard_acceptance),
        "target_integrity_status": target_integrity_status,
        "recommended_signal_ratio_target_mode": recommended_signal_ratio_target_mode,
        "table_s1_interferometric_consistency_residual": (
            table_s1_interferometric_consistency_residual
        ),
        "notes": notes,
    }


def _table_s1_material_consistency_residual(material: str, wavelength_nm: int) -> float:
    interferometric = lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING[material][
        int(wavelength_nm)
    ]
    if material == "gold":
        sqrt_scattering = float(
            joint_fit.TABLE_S1_SCATTERING_CROSS_SECTION["gold"][int(wavelength_nm)] ** 0.5
        )
    elif material == "silver":
        sqrt_scattering = float(
            joint_fit.TABLE_S1_SCATTERING_CROSS_SECTION["silver"][int(wavelength_nm)] ** 0.5
        )
    else:
        raise ValueError(f"Unknown Table S1 material: {material}")
    return abs(float(interferometric) - sqrt_scattering) / max(sqrt_scattering, 1e-12)


def _table_s1_integrity_status(wavelength_nm: int) -> tuple[str, float]:
    gold_residual = _table_s1_material_consistency_residual("gold", wavelength_nm)
    silver_residual = _table_s1_material_consistency_residual("silver", wavelength_nm)
    residual = max(gold_residual, silver_residual)
    status = (
        "unresolved_table_s1_interferometric_column_inconsistency"
        if residual > 0.25
        else "table_s1_interferometric_column_formula_consistent"
    )
    return status, residual


def build_target_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for wavelength_nm in joint_fit.JOINT_WAVELENGTHS_NM:
        integrity_status, consistency_residual = _table_s1_integrity_status(wavelength_nm)
        for target_mode in joint_fit.SIGNAL_RATIO_TARGET_MODES:
            value = joint_fit.table_s1_signal_ratio_target(wavelength_nm, target_mode)
            is_formula_mode = target_mode == "sqrt_scattering_column_ratio"
            is_strict_mode = target_mode == "interferometric_column_ratio"
            records.append(
                _target_record(
                    target_name=f"ag40_to_au40_{target_mode}_{wavelength_nm}",
                    target_mode=target_mode,
                    paper_or_source="Tsuyama 2022 NODI Supporting Table S1",
                    figure_table_or_protocol_anchor=(
                        "Table S1 fixed-nk scattering/interferometric scattering values"
                    ),
                    mechanism_scope="2022_NODI_single_channel_material_ratio",
                    value=float(value),
                    band_low=None,
                    band_high=None,
                    confidence="direct" if not target_mode.startswith("recomputed") else "inferred",
                    usable_for_hard_acceptance=bool(is_formula_mode),
                    target_integrity_status=integrity_status,
                    recommended_signal_ratio_target_mode="sqrt_scattering_column_ratio",
                    table_s1_interferometric_consistency_residual=consistency_residual,
                    notes=(
                        "Formula-consistent Table S1 Ag40/Au40 target mode."
                        if is_formula_mode
                        else (
                            "Strict legacy Table S1 interferometric-column ratio. "
                            "Retained for audit, but not the sole hard target because "
                            "the Ag interferometric column is inconsistent with the "
                            "paper text that interferometric scattering follows the "
                            "square root of scattering."
                            if is_strict_mode
                            else "Simulator Mie recomputation using Table S1 fixed n,k; diagnostic cross-check."
                        )
                    ),
                )
            )

    for diameter_nm, target in joint_fit.DETECTION_RATE_TARGETS.items():
        if diameter_nm == 20:
            records.append(
                _target_record(
                    target_name="au20_selected_annulus_low_sensitivity_warning",
                    paper_or_source="Project Tsuyama 2022 selected-annulus proxy",
                    figure_table_or_protocol_anchor=(
                        "Operational warning from 2022 NODI Au20 weak-SNR statement"
                    ),
                    mechanism_scope="2022_NODI_selected_annulus_detection_proxy",
                    value=float(target["target"]),
                    band_low=float(target["low"]),
                    band_high=float(target["high"]),
                    confidence="operational",
                    usable_for_hard_acceptance=False,
                    notes=(
                        "Au20 lower-bound misses are warning-only because the paper "
                        "states 20 nm Au pulses were observed but not all particles "
                        "might be detected; no crossing-denominator lower efficiency "
                        "is published."
                    ),
                )
            )
            records.append(
                _target_record(
                    target_name="au20_selected_annulus_upper_detection_guard",
                    paper_or_source="Project Tsuyama 2022 selected-annulus proxy",
                    figure_table_or_protocol_anchor=(
                        "Operational upper guard from 2022 NODI Au20 weak-SNR statement"
                    ),
                    mechanism_scope="2022_NODI_selected_annulus_detection_proxy",
                    value=float(target["high"]),
                    band_low=None,
                    band_high=float(target["high"]),
                    confidence="operational",
                    usable_for_hard_acceptance=True,
                    notes=(
                        "Au20 over-detection remains a hard sanity guard because it "
                        "would conflict with the paper's weak-SNR/not-all-detected "
                        "description."
                    ),
                )
            )
            continue
        records.append(
            _target_record(
                target_name=f"au{diameter_nm}_selected_annulus_detection_proxy",
                paper_or_source="Project Tsuyama 2022 selected-annulus proxy",
                figure_table_or_protocol_anchor=(
                    "Operational band inferred from 2022 NODI gold conclusions"
                ),
                mechanism_scope="2022_NODI_selected_annulus_detection_proxy",
                value=float(target["target"]),
                band_low=float(target["low"]),
                band_high=float(target["high"]),
                confidence="operational",
                usable_for_hard_acceptance=True,
                notes=(
                    "The paper does not publish a crossing-denominator detection "
                    "efficiency table. This target can gate proxy fit only when "
                    "reported as operational/inferred, never as direct reproduction."
                ),
            )
        )

    records.extend(
        [
            _target_record(
                target_name="au_size_exponent",
                paper_or_source="Tsuyama 2022 NODI size-response discussion",
                figure_table_or_protocol_anchor="Au20/Au30/Au40/Au60 size trend",
                mechanism_scope="2022_NODI_gold_size_response_proxy",
                value=float(joint_fit.AU_SIZE_EXPONENT_TARGET),
                band_low=1.9,
                band_high=2.7,
                confidence="inferred",
                usable_for_hard_acceptance=True,
                notes=(
                    "Used as a bounded paper-audit proxy. Raw and calibrated "
                    "size exponents must be reported separately."
                ),
            ),
            _target_record(
                target_name="au30_to_au20_snr_ratio",
                paper_or_source="Tsuyama 2022 NODI reported Au20/Au30 SNR",
                figure_table_or_protocol_anchor="Au20 mean SNR about 12; Au30 about 33",
                mechanism_scope="2022_NODI_gold_snr_ratio_proxy",
                value=float(joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET),
                band_low=0.70 * float(joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET),
                band_high=1.42 * float(joint_fit.AU30_TO_AU20_SNR_RATIO_TARGET),
                confidence="inferred",
                usable_for_hard_acceptance=True,
                notes=(
                    "Ratio is computed from reported means. It is useful for "
                    "readout/noise sanity, not absolute SNR reproduction."
                ),
            ),
            _target_record(
                target_name="selected_annulus_geometry_guardrail",
                paper_or_source="Project P0.5 annulus sensitivity decision",
                figure_table_or_protocol_anchor="Canonical edge_norm 0.5-0.8",
                mechanism_scope="selected_annulus_denominator_guardrail",
                value="0.5-0.8",
                band_low=joint_fit.MIN_ANNULUS_FRACTION,
                band_high=None,
                confidence="operational",
                usable_for_hard_acceptance=True,
                notes=(
                    "The annulus window is fixed for Phase 2 and is not a fit "
                    "parameter. The fraction guardrail prevents empty-denominator fits."
                ),
            ),
            _target_record(
                target_name="classification_accuracy_71p9_pm_4p0",
                paper_or_source="Tsuyama 2022 classification protocol metadata",
                figure_table_or_protocol_anchor="Au/Ag 40/60 linked 488/532 SVM",
                mechanism_scope="2022_NODI_classification_diagnostic",
                value="71.9 +/- 4.0%",
                band_low=None,
                band_high=None,
                confidence="diagnostic_only",
                usable_for_hard_acceptance=False,
                notes=(
                    "Keep diagnostic until source audit and local sklearn/protocol "
                    "verification are complete. It must not drive Phase 2 inverse search."
                ),
            ),
            _target_record(
                target_name="pod_2020_au20_near_100pct_counting",
                paper_or_source="Tsuyama 2020 POD thermal counting",
                figure_table_or_protocol_anchor="POD thermal absorption counting",
                mechanism_scope="not_2022_NODI_target",
                value="excluded",
                band_low=None,
                band_high=None,
                confidence="diagnostic_only",
                usable_for_hard_acceptance=False,
                notes=(
                    "Explicit exclusion target. 2020 POD thermal counting must "
                    "not calibrate the 2022 single-channel NODI lane."
                ),
            ),
            _target_record(
                target_name="paired_pod_nodi_2024_classification",
                paper_or_source="Tsuyama 2024 paired POD+NODI",
                figure_table_or_protocol_anchor="Paired absorption/scattering platform",
                mechanism_scope="not_2022_single_channel_NODI_target",
                value="excluded",
                band_low=None,
                band_high=None,
                confidence="diagnostic_only",
                usable_for_hard_acceptance=False,
                notes=(
                    "Explicit exclusion target. 2024 paired POD+NODI results "
                    "are not used for 2022 single-channel NODI calibration."
                ),
            ),
        ]
    )
    return records


def build_target_frame() -> pd.DataFrame:
    frame = pd.DataFrame(build_target_records())
    confidence_order = {"direct": 0, "inferred": 1, "operational": 2, "diagnostic_only": 3}
    frame["_confidence_order"] = frame["confidence"].map(confidence_order).fillna(99)
    frame = frame.sort_values(
        ["usable_for_hard_acceptance", "_confidence_order", "target_name"],
        ascending=[False, True, True],
        ignore_index=True,
    )
    return frame.drop(columns=["_confidence_order"])


def write_outputs(output_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = build_target_frame()
    csv_path = output_dir / CSV_FILENAME
    json_path = output_dir / JSON_FILENAME
    report_path = output_dir / REPORT_FILENAME
    targets.to_csv(csv_path, index=False)
    payload = {
        "schema_id": SCHEMA_ID,
        "generated_at_unix": time.time(),
        "target_count": int(len(targets)),
        "hard_acceptance_target_count": int(targets["usable_for_hard_acceptance"].sum()),
        "diagnostic_only_count": int((targets["confidence"] == "diagnostic_only").sum()),
        "targets": targets.to_dict(orient="records"),
    }
    rate_calib.write_json(json_path, payload)
    lines = [
        "# Tsuyama Phase 2 Paper Target Audit",
        "",
        "## Scope",
        "",
        "- This manifest separates direct, inferred, operational, and diagnostic-only targets.",
        "- Diagnostic-only targets cannot be used for Phase 2 hard acceptance.",
        "- Detection-rate bands are operational proxy targets, not direct paper efficiencies.",
        "",
        "## Target Manifest",
        "",
        rate_calib.dataframe_to_markdown(targets),
        "",
        "## Output Files",
        "",
        f"- `{csv_path}`",
        f"- `{json_path}`",
        f"- `{report_path}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return targets, payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write the Phase 2 Tsuyama paper target audit manifest."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    targets, _ = write_outputs(args.output_dir)
    print(f"Wrote {len(targets)} target records to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
