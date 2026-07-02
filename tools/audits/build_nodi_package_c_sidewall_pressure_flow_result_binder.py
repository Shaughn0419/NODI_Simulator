#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.sidewall_pressure_flow_result_binder import (  # noqa: E402
    PORT_BALANCE_THRESHOLD_DEFAULT,
    Q_TOTAL_RECONCILIATION_THRESHOLD_DEFAULT,
    SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
    bind_pressure_flow_external_results,
    build_external_result_template_rows,
    build_formal_qch_sidecar_rows,
    pressure_flow_result_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_20260701"
DISPOSITION_WAITING = (
    "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_READY_WAITING_FOR_EXTERNAL_RESULT"
)
DISPOSITION_FORMAL_READY = (
    "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_READY"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY

PRESSURE_FLOW_HARNESS_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_STATUS_20260701.json"
)
PRESSURE_FLOW_REQUEST_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REQUEST_ROWS_20260701.csv"
)
PRESSURE_FLOW_CONTROL_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CONTROL_ROWS_20260701.csv"
)
PRESSURE_FLOW_LEDGER_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_STATUS_20260701.json"
)
PRESSURE_FLOW_LEDGER_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
OPTIONAL_EXTERNAL_RESULT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_EXTERNAL_RESULT_ROWS_20260701.csv"
)

ALLOWED_USE = "pressure-flow external result binding;formal qch sidecar acceptance preflight"
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "pressure_flow_validation_harness_status": PRESSURE_FLOW_HARNESS_STATUS,
    "pressure_flow_validation_harness_request_rows": PRESSURE_FLOW_REQUEST_ROWS,
    "pressure_flow_validation_harness_control_rows": PRESSURE_FLOW_CONTROL_ROWS,
    "integrated_promotion_ledger_pressure_flow_status": PRESSURE_FLOW_LEDGER_STATUS,
    "integrated_promotion_ledger_pressure_flow_lanes": PRESSURE_FLOW_LEDGER_LANES,
    "pressure_flow_result_binder_module": PROJECT_ROOT
    / "nodi_simulator/sidewall_pressure_flow_result_binder.py",
    "pressure_flow_result_binder_module_tests": PROJECT_ROOT
    / "tests/test_sidewall_pressure_flow_result_binder.py",
    "pressure_flow_result_binder_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_pressure_flow_result_binder.py",
    "pressure_flow_result_binder_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_pressure_flow_result_binder.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_pressure_flow_result_binder.py",
    "tests/test_sidewall_pressure_flow_result_binder.py",
    "tools/audits/build_nodi_package_c_sidewall_pressure_flow_result_binder.py",
    "tests/test_nodi_package_c_sidewall_pressure_flow_result_binder.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}
UPSTREAM_PRESSURE_FLOW_HARNESS_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_"
)
UPSTREAM_PRESSURE_FLOW_HARNESS_PUBLIC_REPORT = (
    "reports/541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
)
UPSTREAM_PRESSURE_FLOW_LEDGER_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_"
)
UPSTREAM_PRESSURE_FLOW_LEDGER_PUBLIC_REPORT = (
    "reports/542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_20260701.md"
)


def upstream_pressure_flow_output(path: str) -> bool:
    return (
        path.startswith(UPSTREAM_PRESSURE_FLOW_HARNESS_PREFIX)
        or path == UPSTREAM_PRESSURE_FLOW_HARNESS_PUBLIC_REPORT
        or path.startswith(UPSTREAM_PRESSURE_FLOW_LEDGER_PREFIX)
        or path == UPSTREAM_PRESSURE_FLOW_LEDGER_PUBLIC_REPORT
    )

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bind exact W500/D900 pressure-flow external results into a formal q_ch sidecar preflight."
    )
    parser.add_argument("--confirm-sidewall-pressure-flow-result-binder", action="store_true")
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
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_"
        )
        or path
        == "reports/543_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "pressure_flow_result_binder_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif upstream_pressure_flow_output(path):
            classification = "source_locked_upstream_pressure_flow_dirty_context"
            release_decision = "included_in_chain_rebuild_not_result_binder_blocker"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_"
        ) or path == (
            "reports/543_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_20260701.md"
        ):
            classification = "pressure_flow_result_binder_output"
            release_decision = "included_or_rewritten_by_pressure_flow_result_binder"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_pressure_flow_result_binder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_pressure_flow_result_binder_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


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
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    if OPTIONAL_EXTERNAL_RESULT_ROWS.exists():
        rows.append(
            {
                "source_id": "optional_external_pressure_flow_result_rows",
                "path": display_path(OPTIONAL_EXTERNAL_RESULT_ROWS),
                "exists": "true",
                "sha256": sha256_file(OPTIONAL_EXTERNAL_RESULT_ROWS),
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "external_result_template_rows": payload["external_result_template_rows"],
        "binding_rows": payload["binding_rows"],
        "formal_qch_sidecar_rows": payload["formal_qch_sidecar_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    harness_status = load_json(PRESSURE_FLOW_HARNESS_STATUS)
    ledger_status = load_json(PRESSURE_FLOW_LEDGER_STATUS)
    request_rows = read_csv_rows(PRESSURE_FLOW_REQUEST_ROWS) if PRESSURE_FLOW_REQUEST_ROWS.exists() else []
    control_rows = read_csv_rows(PRESSURE_FLOW_CONTROL_ROWS) if PRESSURE_FLOW_CONTROL_ROWS.exists() else []
    external_rows = (
        read_csv_rows(OPTIONAL_EXTERNAL_RESULT_ROWS)
        if OPTIONAL_EXTERNAL_RESULT_ROWS.exists()
        else []
    )
    template_rows = [
        row.to_dict() for row in build_external_result_template_rows(request_rows)
    ]
    binding_objects = bind_pressure_flow_external_results(request_rows, external_rows)
    formal_objects = build_formal_qch_sidecar_rows(binding_objects)
    binding_rows = [row.to_dict() for row in binding_objects]
    formal_rows = [row.to_dict() for row in formal_objects]
    promotion_rows = pressure_flow_result_promotion_update_rows(
        binding_objects,
        formal_objects,
    )
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    accepted_bindings = sum(
        row["per_route_acceptance_status"]
        == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        for row in binding_rows
    )
    missing_bindings = sum(
        row["per_route_acceptance_status"] == "missing_external_result"
        for row in binding_rows
    )
    formal_ready = len(formal_rows) == len(request_rows) and len(formal_rows) == 2
    expected_waiting = len(external_rows) == 0 and missing_bindings == 2
    disposition = (
        DISPOSITION_FORMAL_READY
        if formal_ready
        else DISPOSITION_WAITING
        if expected_waiting
        else BLOCKED_DISPOSITION
    )
    if (
        source_missing != 0
        or release_dirty_blockers != 0
        or harness_status.get("disposition")
        != "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_READY_EXECUTION_INPUT"
        or ledger_status.get("disposition")
        != "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_READY_PREFLIGHT_ONLY"
        or len(request_rows) != 2
        or len(control_rows) != 1
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_pressure_flow_harness_disposition": harness_status.get("disposition", ""),
        "source_pressure_flow_ledger_disposition": ledger_status.get("disposition", ""),
        "request_rows": len(request_rows),
        "closed_geometry_control_rows": len(control_rows),
        "external_result_input_present": OPTIONAL_EXTERNAL_RESULT_ROWS.exists(),
        "external_result_rows": len(external_rows),
        "external_result_template_rows": len(template_rows),
        "binding_rows": len(binding_rows),
        "missing_external_result_binding_rows": missing_bindings,
        "accepted_exact_pressure_flow_binding_rows": accepted_bindings,
        "formal_qch_sidecar_rows": len(formal_rows),
        "formal_qch_sidecar_current": formal_ready,
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "port_balance_threshold_max": PORT_BALANCE_THRESHOLD_DEFAULT,
        "q_total_reconciliation_threshold_max": Q_TOTAL_RECONCILIATION_THRESHOLD_DEFAULT,
        "acceptance_ratio_threshold_note": (
            "0.5-2.0 is a sanity guard for external-to-candidate flow scale, "
            "not a calibrated pressure-flow agreement threshold"
        ),
        "promotion_update_rows": len(promotion_rows),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "external_result_template_rows": template_rows,
        "binding_rows": binding_rows,
        "formal_qch_sidecar_rows": formal_rows,
        "promotion_update_rows": promotion_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    waiting = summary["disposition"] == DISPOSITION_WAITING
    formal = summary["disposition"] == DISPOSITION_FORMAL_READY
    checks = {
        "disposition valid": waiting or formal,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two request rows": summary["request_rows"] == 2,
        "one closed control": summary["closed_geometry_control_rows"] == 1,
        "two template rows": summary["external_result_template_rows"] == 2,
        "two binding rows": summary["binding_rows"] == 2,
        "one promotion update": summary["promotion_update_rows"] == 1,
        "formal weighting false": summary["formal_qch_weighting_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    if waiting:
        checks["waiting has no formal rows"] = summary["formal_qch_sidecar_rows"] == 0
        checks["waiting missing external rows"] = (
            summary["missing_external_result_binding_rows"] == 2
        )
    if formal:
        checks["formal rows complete"] = summary["formal_qch_sidecar_rows"] == 2
        checks["accepted bindings complete"] = (
            summary["accepted_exact_pressure_flow_binding_rows"] == 2
        )
    for row in payload["binding_rows"]:
        checks[f"binding no route claim {row['binding_id']}"] = (
            row["route_score_current"] is False
            and row["yield_current"] is False
            and row["detection_probability_current"] is False
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    template_path = OUTPUT_DIR / f"{PREFIX}_EXTERNAL_RESULT_TEMPLATE_ROWS_20260701.csv"
    write_csv_rows(template_path, payload["external_result_template_rows"])
    paths.append(template_path)

    binding_path = OUTPUT_DIR / f"{PREFIX}_BINDING_ROWS_20260701.csv"
    write_csv_rows(binding_path, payload["binding_rows"])
    paths.append(binding_path)

    if payload["formal_qch_sidecar_rows"]:
        formal_path = OUTPUT_DIR / f"{PREFIX}_FORMAL_QCH_SIDECAR_ROWS_20260701.csv"
        write_csv_rows(formal_path, payload["formal_qch_sidecar_rows"])
        paths.append(formal_path)

    promotion_path = OUTPUT_DIR / f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv"
    write_csv_rows(promotion_path, payload["promotion_update_rows"])
    paths.append(promotion_path)

    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock"])
    paths.append(source_lock_path)

    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context"])
    paths.append(dirty_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = REPORT_DIR / "543_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path, payload["summary"]["disposition"]))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Pressure-Flow Result Binder",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- External result input present: `{s['external_result_input_present']}`.",
            f"- Binding rows: `{s['binding_rows']}`.",
            f"- Formal q_ch sidecar rows: `{s['formal_qch_sidecar_rows']}`.",
            f"- Port-balance threshold: `{s['port_balance_threshold_max']}`.",
            f"- q_total reconciliation threshold: `{s['q_total_reconciliation_threshold_max']}`.",
            f"- Ratio threshold note: {s['acceptance_ratio_threshold_note']}.",
            "- The binder validates exact W500/D900 pressure-flow results before formal q_ch sidecar emission.",
            "- Route score, winner/JRC, yield, and detection probability remain false.",
            "",
        ]
    )


def manifest_rows(paths: list[Path], manifest_path: Path, disposition: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": disposition,
                "policy_impact": "external_pressure_flow_result_binder_not_route_score",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": disposition,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_pressure_flow_result_binder:
        parser.error("--confirm-sidewall-pressure-flow-result-binder is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
