from __future__ import annotations

from argparse import Namespace
import csv
import json
from pathlib import Path

import pytest

from nodi_simulator.config_trace import build_minimal_config_trace
from nodi_simulator.data_objects import BASELINE_OPTICAL, DEFAULT_SIM_CFG
from nodi_simulator.report148_stage0 import (
    repair_t6_mechanism_chain_outputs,
    write_t5_provenance_backfill_outputs,
    write_t8_static_ratio_outputs,
)
from tools.lens_b_ev_gold_fullgrid_runner import _write_manifest, SourceScope


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_t8_static_ratio_outputs_use_abs_ratio_fields_and_group_summary(tmp_path: Path) -> None:
    summary_csv = tmp_path / "summary.csv"
    _write_csv(
        summary_csv,
        [
            {
                "wavelength_nm": "404",
                "particle_family": "gold",
                "normalization_scope": "per_wavelength",
                "reference_route": "engineering_fallback",
                "reference_na_edge_policy": "hard_guardrail",
                "field_coordinate_measure": "theta_phi_surrogate",
                "bfp_to_angle_jacobian_applied": "False",
                "detector_forward_model": "joint_overlap_coherent_surrogate",
                "readout_observable_mode": "magnitude",
                "E_sca_normalized": "2.0",
                "cross_term_detector_integrated": "1.0",
                "signal_detector_integrated": "10.0",
                "roi_vs_scalar_signal_ratio": "5.0",
            },
            {
                "wavelength_nm": "404",
                "particle_family": "gold",
                "normalization_scope": "per_wavelength",
                "reference_route": "engineering_fallback",
                "reference_na_edge_policy": "hard_guardrail",
                "field_coordinate_measure": "theta_phi_surrogate",
                "bfp_to_angle_jacobian_applied": "False",
                "detector_forward_model": "joint_overlap_coherent_surrogate",
                "readout_observable_mode": "magnitude",
                "E_sca_normalized": "3.0",
                "cross_term_detector_integrated": "1.0",
                "signal_detector_integrated": "20.0",
                "roi_vs_scalar_signal_ratio": "5.0",
            },
        ],
    )

    output_csv = tmp_path / "with_static.csv"
    summary_table = tmp_path / "summary_table.csv"
    metadata_json = tmp_path / "metadata.json"
    metadata = write_t8_static_ratio_outputs(
        summary_csv=summary_csv,
        output_csv=output_csv,
        summary_table_csv=summary_table,
        metadata_json=metadata_json,
    )

    with output_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert float(rows[0]["A_vs_B_abs_signal_ratio_static"]) == pytest.approx(0.5)
    assert float(rows[0]["A_vs_C_abs_signal_ratio_static"]) == pytest.approx(2.5)
    assert rows[0]["report148_stage0_polarity_status"] == "A_vs_C_unsigned_only_abs_ratio"

    with summary_table.open(encoding="utf-8", newline="") as handle:
        grouped = list(csv.DictReader(handle))
    assert len(grouped) == 1
    assert float(grouped[0]["A_vs_B_abs_signal_ratio_static_median"]) == pytest.approx(0.5)
    assert float(grouped[0]["A_vs_C_abs_signal_ratio_static_max"]) == pytest.approx(2.5)
    assert metadata["claim_level"] == "static_postprocess_relative_audit_only"
    assert json.loads(metadata_json.read_text(encoding="utf-8"))["row_count"] == 2


def test_t6_repair_outputs_signed_and_deprecated_magnitude_columns(tmp_path: Path) -> None:
    summary_csv = tmp_path / "summary.csv"
    _write_csv(
        summary_csv,
        [
            {
                "particle_family": "EV_sEV",
                "wavelength_nm": "404",
                "cross_term_detector_integrated": "-4.0",
            },
            {
                "particle_family": "EV_sEV",
                "wavelength_nm": "404",
                "cross_term_detector_integrated": "-2.0",
            },
            {
                "particle_family": "EV_sEV",
                "wavelength_nm": "660",
                "cross_term_detector_integrated": "-1.0",
            },
            {
                "particle_family": "EV_sEV",
                "wavelength_nm": "660",
                "cross_term_detector_integrated": "1.0e-18",
            },
        ],
    )
    mechanism_csv = tmp_path / "mechanism.csv"
    _write_csv(
        mechanism_csv,
        [
            {
                "wavelength_nm": "404",
                "median_cross_term_detector_integrated": "9.4",
            },
            {
                "wavelength_nm": "660",
                "median_cross_term_detector_integrated": "1.1",
            },
        ],
    )

    output_csv = tmp_path / "mechanism_repaired.csv"
    metadata_json = tmp_path / "metadata.json"
    metadata = repair_t6_mechanism_chain_outputs(
        mechanism_chain_csv=mechanism_csv,
        summary_csv=summary_csv,
        output_csv=output_csv,
        metadata_json=metadata_json,
    )

    with output_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    first = rows[0]
    assert first["median_cross_term_detector_integrated_magnitude_deprecated"] == "9.4"
    assert float(first["median_signed_cross_term_detector_integrated"]) == pytest.approx(-3.0)
    assert float(first["median_abs_cross_term_detector_integrated"]) == pytest.approx(3.0)
    assert float(first["cross_term_negative_fraction"]) == pytest.approx(1.0)
    assert first["phase_convention"] == "current_uncalibrated"
    assert metadata["signed_stats"]["404"]["cross_term_negative_fraction"] == pytest.approx(1.0)


def test_build_minimal_config_trace_marks_overlap_as_unresolved_without_reference_value() -> None:
    trace = build_minimal_config_trace(
        cfg=DEFAULT_SIM_CFG,
        optical_template=BASELINE_OPTICAL,
        normalization_view="per_wavelength_gold",
        config_trace_status="backfilled",
    )

    assert trace.runtime_config_subset["reference_model"] == "channel_angular_surrogate"
    assert trace.runtime_config_subset["reference_route"] == "engineering_fallback"
    assert trace.runtime_config_subset["NA_collection"] == pytest.approx(BASELINE_OPTICAL.NA_collection)
    assert trace.manifest_field_origins["interference_overlap_status"] == (
        "unavailable_without_case_reference_context"
    )
    assert "interference_overlap_status" in trace.unresolved_fields


def test_write_manifest_includes_minimal_config_trace_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    scope = SourceScope(
        routes=[(404, 800, 550)],
        particle_names=["gold_20nm"],
        ev_particle_names=[],
        gold_particle_names=["gold_20nm"],
        route_particle_rows_per_seed=1,
    )
    args = Namespace(
        workers=1,
        overwrite_output=False,
        accept_one_lane_primitive=True,
        n_events=100,
        seed=11,
        benchmark_seconds=None,
        particle_scope="gold_only",
        route_source="dummy.csv",
        normalization_lane="fixed_660_gold",
    )

    _write_manifest(
        output_dir=output_dir,
        args=args,
        scope=scope,
        cfg=DEFAULT_SIM_CFG,
        run_kind="unit_test_manifest",
        optical_template=BASELINE_OPTICAL,
    )
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    runtime = manifest["runtime_config_subset"]
    assert runtime["reference_model"] == "channel_angular_surrogate"
    assert runtime["reference_route"] == "engineering_fallback"
    assert runtime["NA_collection"] == pytest.approx(BASELINE_OPTICAL.NA_collection)
    assert runtime["config_trace_status"] == "original_runtime_record"
    assert runtime["manifest_field_origins"]["normalization_view"] == "runner_args"


def test_t5_backfill_writes_sidecars_without_touching_original_manifest(tmp_path: Path) -> None:
    run_dir = tmp_path / "lensb"
    run_dir.mkdir()
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "n_events": 100,
                "seed": 11,
                "runtime_config_subset": {"threshold_sigma": 5.0},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    fixed_path = run_dir / "seed_11_fixed_660_gold_diagnostic_rows.csv"
    per_path = run_dir / "seed_11_per_wavelength_gold_diagnostic_rows.csv"
    _write_csv(
        fixed_path,
        [
            {
                "normalization_lane": "fixed_660_gold",
                "reference_na_edge_policy": "hard_guardrail",
                "shot_noise_scale": "0.001",
                "threshold_sigma": "5.0",
            }
        ],
    )
    _write_csv(
        per_path,
        [
            {
                "normalization_lane": "per_wavelength_gold",
                "reference_na_edge_policy": "hard_guardrail",
                "shot_noise_scale": "0.001",
                "threshold_sigma": "5.0",
            }
        ],
    )

    output_json = tmp_path / "backfill.json"
    output_csv = tmp_path / "backfill.csv"
    payload = write_t5_provenance_backfill_outputs(
        run_manifest_json=manifest_path,
        diagnostic_rows_csvs=[fixed_path, per_path],
        output_json=output_json,
        output_csv=output_csv,
    )

    sidecar = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["config_trace_status"] == "backfilled"
    fixed_backfill = sidecar["lane_backfills"]["fixed_660_gold"]["runtime_config_subset_backfill"]
    assert fixed_backfill["reference_model"]
    assert fixed_backfill["reference_route"]
    assert "interference_overlap_status" in sidecar["lane_backfills"]["fixed_660_gold"][
        "unresolved_fields"
    ]
    with output_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(
        row["normalization_view"] == "per_wavelength_gold" and row["field"] == "reference_route"
        for row in rows
    )
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["runtime_config_subset"] == {
        "threshold_sigma": 5.0
    }
