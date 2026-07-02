from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_real_evidence_input_workspace as builder


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _patch_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(builder, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(builder, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(builder, "DETECTOR_TEMPLATE_ROWS", tmp_path / "detector_template.csv")
    monkeypatch.setattr(builder, "WET_TEMPLATE_ROWS", tmp_path / "wet_template.csv")
    monkeypatch.setattr(
        builder, "DETECTION_VALUE_TEMPLATE_ROWS", tmp_path / "detection_template.csv"
    )
    monkeypatch.setattr(builder, "YIELD_VALUE_TEMPLATE_ROWS", tmp_path / "yield_template.csv")
    monkeypatch.setattr(builder, "DETECTOR_TARGET_INPUT_ROWS", tmp_path / "detector_input.csv")
    monkeypatch.setattr(builder, "WET_TARGET_INPUT_ROWS", tmp_path / "wet_input.csv")
    monkeypatch.setattr(
        builder, "DETECTION_VALUE_TARGET_INPUT_ROWS", tmp_path / "detection_input.csv"
    )
    monkeypatch.setattr(builder, "YIELD_VALUE_TARGET_INPUT_ROWS", tmp_path / "yield_input.csv")


def _write_templates(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "detector_template.csv",
        [{"route_candidate_id": "ROUTE-CAND-001", "blank_trace_sha256": ""}],
    )
    _write_csv(
        tmp_path / "wet_template.csv",
        [{"route_candidate_id": "ROUTE-CAND-001", "endpoint_id": "wet_pass_probability"}],
    )
    _write_csv(
        tmp_path / "detection_template.csv",
        [{"route_candidate_id": "ROUTE-CAND-001", "detection_probability_estimate": ""}],
    )
    _write_csv(
        tmp_path / "yield_template.csv",
        [{"route_candidate_id": "ROUTE-CAND-001", "yield_estimate": ""}],
    )


def test_real_evidence_input_workspace_builds_header_only_targets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_paths(monkeypatch, tmp_path)
    _write_templates(tmp_path)

    payload = builder.build_payload(create_missing_targets=True)
    summary = payload["summary"]

    assert summary["disposition"] == builder.DISPOSITION
    assert summary["workspace_rows"] == 4
    assert summary["target_created_now_rows"] == 4
    assert summary["target_header_only_rows"] == 4
    assert summary["target_real_data_rows_total"] == 0
    assert builder.validate_payload(payload) == []


def test_real_evidence_input_workspace_writes_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_paths(monkeypatch, tmp_path)
    _write_templates(tmp_path)
    payload = builder.build_payload(create_missing_targets=True)
    outputs = builder.write_outputs(payload)

    names = {path.name for path in outputs}
    assert f"{builder.PREFIX}_WORKSPACE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
    assert f"577_{builder.PREFIX}_20260701.md" in names
    assert (tmp_path / "detector_input.csv").exists()
    assert (tmp_path / "yield_input.csv").exists()


def test_real_evidence_input_workspace_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_real_evidence_input_workspace.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-real-evidence-input-workspace is required" in (
        result.stderr + result.stdout
    )
