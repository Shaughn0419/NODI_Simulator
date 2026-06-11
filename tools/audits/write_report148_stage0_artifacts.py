#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools._common import write_json_file

from nodi_simulator.report148_stage0 import (
    repair_t6_mechanism_chain_outputs,
    write_t5_provenance_backfill_outputs,
    write_t8_static_ratio_outputs,
)


DEFAULT_V1_SUMMARY = Path(
    "results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
)
DEFAULT_MECHANISM_CHAIN = Path(
    "reports/current/47_ev_design_full_grid_analysis/mechanism_chain_by_wavelength_EV_medians.csv"
)
DEFAULT_LENS_B_RUN_DIR = Path(
    "results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed11_16worker_20260518"
)


def _default_output_dir() -> Path:
    return Path("results/audits") / f"report148_stage0_{datetime.now().strftime('%Y%m%d')}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate zero-rerun Stage 0 postprocess and provenance artifacts for report 148."
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=["all"],
        choices=["all", "t8", "t6", "t5"],
        help="Which Stage 0 tasks to run.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument("--v1-summary", type=Path, default=DEFAULT_V1_SUMMARY)
    parser.add_argument("--mechanism-chain", type=Path, default=DEFAULT_MECHANISM_CHAIN)
    parser.add_argument("--lensb-run-dir", type=Path, default=DEFAULT_LENS_B_RUN_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = set(args.tasks)
    if "all" in tasks:
        tasks = {"t8", "t6", "t5"}

    manifest: dict[str, object] = {
        "output_dir": str(output_dir),
        "requested_tasks": sorted(tasks),
    }

    if "t8" in tasks:
        manifest["t8"] = write_t8_static_ratio_outputs(
            summary_csv=args.v1_summary,
            output_csv=output_dir / "report148_stage0_v1_summary_with_static_ratios.csv",
            summary_table_csv=output_dir / "report148_stage0_v1_static_ratio_summary.csv",
            metadata_json=output_dir / "report148_stage0_t8_metadata.json",
        )

    if "t6" in tasks:
        manifest["t6"] = repair_t6_mechanism_chain_outputs(
            mechanism_chain_csv=args.mechanism_chain,
            summary_csv=args.v1_summary,
            output_csv=output_dir / "report148_stage0_mechanism_chain_by_wavelength_EV_medians.csv",
            metadata_json=output_dir / "report148_stage0_t6_metadata.json",
        )

    if "t5" in tasks:
        manifest["t5"] = write_t5_provenance_backfill_outputs(
            run_manifest_json=args.lensb_run_dir / "run_manifest.json",
            diagnostic_rows_csvs=[
                args.lensb_run_dir / "seed_11_fixed_660_gold_diagnostic_rows.csv",
                args.lensb_run_dir / "seed_11_per_wavelength_gold_diagnostic_rows.csv",
            ],
            output_json=output_dir / "report148_stage0_provenance_backfill.json",
            output_csv=output_dir / "report148_stage0_audit_minimal_config_trace.csv",
        )

    write_json_file(output_dir / "report148_stage0_artifact_manifest.json", manifest)


if __name__ == "__main__":
    main()
