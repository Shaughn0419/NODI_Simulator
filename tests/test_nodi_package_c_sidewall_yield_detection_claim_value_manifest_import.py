from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows, write_csv_rows
from tools.audits import (
    build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import as builder,
)
from tests.test_sidewall_yield_detection_claim_value_manifest_import import (
    _manifest_rows,
)


def test_claim_value_manifest_import_builder_defaults_to_manifest_required() -> None:
    payload = builder.build_payload(
        source_manifest=builder.DEFAULT_SOURCE_MANIFEST,
        artifact_root=builder.PROJECT_ROOT,
    )
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.MANIFEST_REQUIRED_DISPOSITION
    assert summary["source_manifest_present"] is False
    assert summary["imported_claim_value_rows"] == 0
    assert summary["canonical_detection_input_written"] is False
    assert summary["canonical_yield_input_written"] is False
    assert summary["detection_probability_current"] is False
    assert summary["yield_current"] is False
    assert payload["import_audit_rows"][0]["import_rejection_reason"] == (
        "source_manifest_missing"
    )


def test_claim_value_manifest_import_builder_writes_canonical_value_rows(
    tmp_path: Path,
) -> None:
    source_manifest = tmp_path / "source_manifest.csv"
    write_csv_rows(source_manifest, _manifest_rows(tmp_path))

    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_detection = builder.CANONICAL_DETECTION_VALUE_INPUT_ROWS
    old_yield = builder.CANONICAL_YIELD_VALUE_INPUT_ROWS
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.CANONICAL_DETECTION_VALUE_INPUT_ROWS = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_DETECTION_PROBABILITY_VALUE_INPUT_ROWS_20260701.csv"
        )
        builder.CANONICAL_YIELD_VALUE_INPUT_ROWS = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_YIELD_WET_VALUE_INPUT_ROWS_20260701.csv"
        )
        payload = builder.build_payload(
            source_manifest=source_manifest,
            artifact_root=tmp_path,
        )
        failures = builder.validate_payload(payload)
        paths = builder.write_outputs(payload)
        detection_rows = read_csv_rows(builder.CANONICAL_DETECTION_VALUE_INPUT_ROWS)
        yield_rows = read_csv_rows(builder.CANONICAL_YIELD_VALUE_INPUT_ROWS)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.CANONICAL_DETECTION_VALUE_INPUT_ROWS = old_detection
        builder.CANONICAL_YIELD_VALUE_INPUT_ROWS = old_yield

    assert failures == []
    assert payload["summary"]["disposition"] == builder.READY_DISPOSITION
    assert payload["summary"]["imported_detection_value_rows"] == 2
    assert payload["summary"]["imported_yield_value_rows"] == 2
    assert payload["summary"]["canonical_detection_input_written"] is True
    assert payload["summary"]["canonical_yield_input_written"] is True
    assert len(detection_rows) == 2
    assert len(yield_rows) == 2
    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_IMPORTED_DETECTION_VALUE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_IMPORTED_YIELD_VALUE_ROWS_20260701.csv" in names
    assert f"579_{builder.PREFIX}_20260701.md" in names


def test_claim_value_manifest_import_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-yield-detection-claim-value-manifest-import is required" in (
        result.stderr + result.stdout
    )
