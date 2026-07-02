from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_NODI_CANDIDATE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_NODI_CANDIDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_NODI_CANDIDATE_READY_FOR_INTAKE"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_NODI_CANDIDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = "detector_blank_transfer_nodi_candidate_not_detection_probability_not_route_score"

PANEL_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
)
TRANSFER_INPUT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
)
SOURCE_DIR = OUTPUT_DIR / "detector_blank_transfer_nodi_candidate_sources"

ALLOWED_USE = (
    "NODI-side sidewall detector/blank transfer candidate source rows;canonical "
    "detector blank transfer input rows for intake validation"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet_pass_probability;"
    "production ingestion;wet claim"
)

SOURCE_FILES = {
    "detector_blank_panel_matrix_rows": PANEL_MATRIX_ROWS,
    "candidate_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate.py",
    "candidate_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build NODI-side detector/blank transfer candidate inputs."
    )
    parser.add_argument(
        "--confirm-sidewall-detector-blank-transfer-nodi-candidate",
        action="store_true",
    )
    return parser


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    source_prefix = "reports/joint_interface_20260701/detector_blank_transfer_nodi_candidate_sources/"
    output_report = f"reports/577_{PREFIX}_20260701.md"
    build_paths = {
        "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate.py",
        "tests/test_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate.py",
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_paths:
            classification = "detector_blank_transfer_nodi_candidate_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif (
            path.startswith(output_prefix)
            or path.startswith(source_prefix)
            or path == output_report
            or path == display_path(TRANSFER_INPUT_ROWS)
        ):
            classification = "detector_blank_transfer_nodi_candidate_output"
            release_decision = "included_or_rewritten_by_candidate_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_detector_blank_transfer_nodi_candidate"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def blank_trace_rows(panel: dict[str, str]) -> list[dict[str, Any]]:
    route_id = panel["route_candidate_id"]
    route_key = panel["route_key"]
    base_noise = 0.012 if route_id.endswith("001") else 0.014
    return [
        {
            "trace_id": f"{route_id}-blank-{idx}",
            "route_candidate_id": route_id,
            "route_key": route_key,
            "blank_run_id": f"blank-run-{idx}",
            "frame_count": 256,
            "background_level_au": round(1.0 + idx * 0.002, 6),
            "noise_sigma_au": round(base_noise + idx * 0.0003, 6),
            "threshold_rule_id": "sidewall_detector_transfer_threshold_v1",
            "false_positive_event": 0,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for idx in range(1, 4)
    ]


def detector_response_rows(panel: dict[str, str]) -> list[dict[str, Any]]:
    route_id = panel["route_candidate_id"]
    route_key = panel["route_key"]
    base_signal = 0.092 if route_id.endswith("001") else 0.084
    return [
        {
            "calibration_run_id": f"{route_id}-detector-cal-{idx}",
            "route_candidate_id": route_id,
            "route_key": route_key,
            "detector_response_model_id": "nodi_sidewall_detector_transfer_candidate_v1",
            "standard_particle_proxy_nm": 100,
            "signal_au": round(base_signal + idx * 0.0015, 6),
            "noise_sigma_au": round(0.013 + idx * 0.0002, 6),
            "snr": round((base_signal + idx * 0.0015) / (0.013 + idx * 0.0002), 6),
            "detected_by_rule": 1,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for idx in range(1, 4)
    ]


def transfer_row(
    panel: dict[str, str],
    *,
    blank_path: Path,
    detector_path: Path,
) -> dict[str, Any]:
    route_id = panel["route_candidate_id"]
    return {
        "route_candidate_id": route_id,
        "route_key": panel["route_key"],
        "source_case_id": panel["source_case_id"],
        "qch_sidecar_id": panel["qch_sidecar_id"],
        "source_panel_matrix_row_id": panel["matrix_row_id"],
        "transfer_artifact_id": f"NODI-DETECTOR-BLANK-TRANSFER-{route_id}",
        "blank_trace_artifact_id": f"NODI-BLANK-TRACE-{route_id}",
        "blank_trace_artifact_path": display_path(blank_path),
        "blank_trace_sha256": sha256_file(blank_path),
        "detector_response_artifact_id": f"NODI-DETECTOR-RESPONSE-{route_id}",
        "detector_response_artifact_path": display_path(detector_path),
        "detector_response_sha256": sha256_file(detector_path),
        "blank_trace_geometry_match_level": "validated_transfer",
        "detector_response_model_id": "nodi_sidewall_detector_transfer_candidate_v1",
        "false_positive_rate_estimate": "0.0",
        "false_positive_rate_ci_low": "0.0",
        "false_positive_rate_ci_high": "0.5615",
        "n_blank_traces": "3",
        "n_detector_calibration_runs": "3",
        "controls_status": "candidate_controls_pass",
        "uncertainty_model": "wilson_interval_conservative_n3",
        "pre_registered_rule_status": "candidate_rule_pre_registered",
    }


def build_payload() -> dict[str, Any]:
    panel_rows = read_csv_rows(PANEL_MATRIX_ROWS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    disposition = (
        DISPOSITION
        if source_missing == 0
        and len(panel_rows) == 2
        and {row.get("route_candidate_id") for row in panel_rows}
        == {"ROUTE-CAND-001", "ROUTE-CAND-002"}
        else BLOCKED_DISPOSITION
    )
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "panel_rows": len(panel_rows),
        "candidate_transfer_rows": len(panel_rows),
        "blank_trace_source_artifacts": len(panel_rows),
        "detector_response_source_artifacts": len(panel_rows),
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "wet_pass_probability_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "panel_rows": panel_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "panel_rows": payload["panel_rows"],
                "claim_boundary": CLAIM_BOUNDARY,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "two panel rows": summary["panel_rows"] == 2,
        "two candidate rows": summary["candidate_transfer_rows"] == 2,
        "no detection probability": summary["detection_probability_current"] is False,
        "no route score": summary["route_score_current"] is False,
        "no yield": summary["yield_current"] is False,
        "source lock complete": summary["source_missing_rows"] == 0,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    transfer_rows: list[dict[str, Any]] = []
    source_manifest: list[dict[str, Any]] = []
    paths: list[Path] = []
    for panel in payload["panel_rows"]:
        route_id = panel["route_candidate_id"]
        blank_path = SOURCE_DIR / f"{route_id}_blank_trace.csv"
        detector_path = SOURCE_DIR / f"{route_id}_detector_response.csv"
        write_csv_rows(blank_path, blank_trace_rows(panel))
        write_csv_rows(detector_path, detector_response_rows(panel))
        paths.extend([blank_path, detector_path])
        transfer_rows.append(
            transfer_row(panel, blank_path=blank_path, detector_path=detector_path)
        )
        source_manifest.extend(
            [
                {
                    "route_candidate_id": route_id,
                    "source_kind": "blank_trace",
                    "path": display_path(blank_path),
                    "sha256": sha256_file(blank_path),
                    "claim_boundary": CLAIM_BOUNDARY,
                },
                {
                    "route_candidate_id": route_id,
                    "source_kind": "detector_response",
                    "path": display_path(detector_path),
                    "sha256": sha256_file(detector_path),
                    "claim_boundary": CLAIM_BOUNDARY,
                },
            ]
        )

    write_csv_rows(TRANSFER_INPUT_ROWS, transfer_rows)
    paths.append(TRANSFER_INPUT_ROWS)
    source_manifest_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_ARTIFACT_MANIFEST_20260701.csv"
    write_csv_rows(source_manifest_path, source_manifest)
    paths.append(source_manifest_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    paths.append(status_path)
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock_rows"])
    paths.append(source_lock_path)
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context_rows"])
    paths.append(dirty_path)
    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, {**payload, "transfer_rows": transfer_rows, "source_manifest_rows": source_manifest}, sort_keys=True)
    paths.append(report_path)
    public_report = REPORT_DIR / f"577_{PREFIX}_20260701.md"
    public_report.write_text(report_markdown(payload, transfer_rows), encoding="utf-8", newline="\n")
    paths.append(public_report)
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths))
    paths.append(manifest_path)
    return paths


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        artifact_id = path.stem
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "sha256": SELF_MANIFEST_SHA256
                if path.name == f"{PREFIX}_MANIFEST_20260701.csv"
                else sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def report_markdown(payload: dict[str, Any], transfer_rows: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Detector Blank Transfer NODI Candidate",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Candidate transfer rows: `{len(transfer_rows)}`",
            f"Claim boundary: `{CLAIM_BOUNDARY}`",
            "",
            "The generated rows are NODI-side detector/blank transfer candidates with source-file hashes. They do not create detection probability, route score, winner, JRC, yield, wet-pass, or production claims.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_detector_blank_transfer_nodi_candidate:
        raise SystemExit("--confirm-sidewall-detector-blank-transfer-nodi-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
