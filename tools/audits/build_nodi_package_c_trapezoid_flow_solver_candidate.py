#!/usr/bin/env python3
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

from nodi_simulator.cross_section_geometry import TrapezoidCrossSection  # noqa: E402
from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.trapezoid_flow_solver import (  # noqa: E402
    TRAPEZOID_FLOW_SOLVER_VERSION,
    solve_trapezoid_pressure_flow_candidate,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE"
DISPOSITION = "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_FAIL_CLOSED"
ARTIFACT_ID = "PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701"
CLAIM_BOUNDARY = "trapezoid_flow_solver_candidate_not_qch_not_route_not_wet"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Trapezoid flow solver candidate evidence;flow/q_ch preflight;route promotion contract input"
)
BLOCKED_USE = (
    "formal q_ch weighting;route_score;winner;JRC;yield;detection_probability;wet claim;"
    "COMSOL validation claim;.mph evidence claim;fabrication release;production ingestion"
)

MAINLINE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_STATUS_20260701.json"
RUNTIME_EXEC_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STATUS_20260701.json"

SOURCE_FILES = {
    "authorized_mainline_status": MAINLINE_STATUS,
    "runtime_execution_status": RUNTIME_EXEC_STATUS,
    "trapezoid_flow_solver_source": PROJECT_ROOT / "nodi_simulator/trapezoid_flow_solver.py",
    "trapezoid_flow_solver_tests": PROJECT_ROOT / "tests/test_trapezoid_flow_solver.py",
    "flow_candidate_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_trapezoid_flow_solver_candidate.py",
    "flow_candidate_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_trapezoid_flow_solver_candidate.py",
}

OUTPUT_NAMES = {
    f"{PREFIX}_STATUS_20260701.json",
    f"{PREFIX}_SOLVER_ROWS_20260701.csv",
    f"{PREFIX}_QCH_PROMOTION_BLOCKERS_20260701.csv",
    f"{PREFIX}_SOURCE_LOCK_20260701.csv",
    f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
    f"{PREFIX}_SELF_REVIEW_20260701.csv",
    f"{PREFIX}_MANIFEST_20260701.csv",
    f"{PREFIX}_REPORT_20260701.json",
    "521_NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701.md",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/trapezoid_flow_solver.py",
    "tests/test_trapezoid_flow_solver.py",
    "tools/audits/build_nodi_package_c_trapezoid_flow_solver_candidate.py",
    "tests/test_nodi_package_c_trapezoid_flow_solver_candidate.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build trapezoid flow solver candidate packet.")
    parser.add_argument("--confirm-trapezoid-flow-solver-candidate", action="store_true")
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
    if path in source_paths or path in BUILD_EDIT_PATHS:
        return True
    return (
        path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_")
        or path == "reports/521_NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if Path(path).name in OUTPUT_NAMES:
            classification = "flow_solver_candidate_output"
            release_decision = "included_or_rewritten_by_flow_solver_candidate"
        elif path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "flow_solver_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_flow_solver_candidate"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_flow_solver_candidate_not_source_locked"
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
    return rows


def solver_rows() -> list[dict[str, str]]:
    cases = [
        ("rectangle_limit_theta90_D900_W500", 500e-9, 900e-9, 0.0),
        ("taper_theta85_D900_W500", 500e-9, 900e-9, 5.0),
        ("closed_theta70_D900_W500", 500e-9, 900e-9, 20.0),
    ]
    rows: list[dict[str, str]] = []
    for case_id, width_m, depth_m, taper_deg in cases:
        result = solve_trapezoid_pressure_flow_candidate(
            TrapezoidCrossSection(width_m, depth_m, taper_deg),
            grid_nx=21,
            grid_nu=21,
        )
        rows.append(
            {
                "case_id": case_id,
                "solver_version": result.solver_version,
                "solver_status": result.solver_status,
                "solver_claim_level": result.solver_claim_level,
                "sidewall_taper_angle_deg_nodi": f"{result.sidewall_taper_angle_deg:.9g}",
                "sidewall_deg_comsol": f"{90.0 - result.sidewall_taper_angle_deg:.9g}",
                "active_cell_count": str(result.active_cell_count),
                "hydraulic_resistance_Pa_s_m3": f"{result.hydraulic_resistance_Pa_s_m3:.12g}",
                "rectangle_proxy_resistance_Pa_s_m3": f"{result.rectangle_proxy_resistance_Pa_s_m3:.12g}",
                "resistance_ratio_vs_rectangle_proxy": f"{result.resistance_ratio_vs_rectangle_proxy:.12g}",
                "not_qch_weighted": str(result.not_qch_weighted).lower(),
                "q_ch_weighting_current": str(result.q_ch_weighting_current).lower(),
                "route_score_current": str(result.route_score_current).lower(),
                "winner_current": str(result.winner_current).lower(),
                "claim_boundary": result.claim_boundary,
            }
        )
    return rows


def qch_blocker_rows() -> list[dict[str, str]]:
    blockers = [
        (
            "q_ch_weighting",
            "requires_flow_solver_validation_or_COMSOL_pressure_flow_comparison_hash",
        ),
        (
            "route_score",
            "requires_qch_sidecar_and_package_D_route_precheck",
        ),
        (
            "winner",
            "requires_route_score_audit_and_no_borrowing_guards",
        ),
        (
            "yield_detection_probability",
            "requires_wet_detection_evidence_contract_pass",
        ),
    ]
    return [
        {
            "blocked_target": target,
            "current_value": "false",
            "implementation_authorized": "true",
            "candidate_solver_evidence_available": "true",
            "required_evidence_before_true": evidence,
            "hard_fail_if": f"{target}_true_without_required_evidence",
        }
        for target, evidence in blockers
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "solver_rows": payload["solver_rows"],
        "qch_blockers": payload["qch_blockers"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    mainline = load_json(MAINLINE_STATUS)
    runtime = load_json(RUNTIME_EXEC_STATUS)
    rows = solver_rows()
    qch_rows = qch_blocker_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing_rows = sum(row["exists"] != "true" for row in source_lock)
    release_scoped_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    tapered = {row["case_id"]: row for row in rows}["taper_theta85_D900_W500"]
    closed = {row["case_id"]: row for row in rows}["closed_theta70_D900_W500"]
    status = (
        DISPOSITION
        if source_missing_rows == 0
        and release_scoped_dirty_blockers == 0
        and mainline.get("solver_branches_authorized_to_prepare") is True
        and runtime.get("guarded_runtime_smoke_executed") is True
        and tapered["solver_status"] == "candidate_solver_output"
        and closed["solver_status"] == "blocked_geometry_closed"
        and all(row["q_ch_weighting_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "solver_version": TRAPEZOID_FLOW_SOLVER_VERSION,
        "mainline_disposition": mainline.get("disposition", ""),
        "runtime_execution_disposition": runtime.get("disposition", ""),
        "solver_candidate_rows": len(rows),
        "candidate_solver_output_rows": sum(row["solver_status"] == "candidate_solver_output" for row in rows),
        "blocked_solver_rows": sum(row["solver_status"].startswith("blocked") for row in rows),
        "q_ch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_detection_probability_current": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "trapezoid_flow_solver_candidate_output_current": True,
        "trapezoid_flow_solver_final_claim_current": False,
        "theta85_resistance_ratio_vs_rectangle_proxy": float(
            tapered["resistance_ratio_vs_rectangle_proxy"]
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing_rows,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_scoped_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "solver_rows": rows,
        "qch_blockers": qch_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "candidate trapezoid Poisson solver executed",
        "rectangle-limit sanity row present",
        "tapered sidewall row changes resistance",
        "geometry-closed row blocked",
        "q_ch and route fields remain false",
        "COMSOL/.mph validation not claimed",
    ]
    return [
        {
            "review_id": f"FLOW-CANDIDATE-SELF-{idx:02d}",
            "dimension": topic,
            "verdict": "PASS_FLOW_SOLVER_CANDIDATE_NOT_QCH",
            "notes": "Candidate flow solver evidence is separated from formal q_ch and route claims.",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "candidate solver rows present": s["candidate_solver_output_rows"] >= 2,
        "closed row blocked": s["blocked_solver_rows"] >= 1,
        "runtime prerequisite present": bool(s["runtime_execution_disposition"]),
        "theta85 resistance increased": s["theta85_resistance_ratio_vs_rectangle_proxy"] > 1.0,
        "no q_ch": s["q_ch_weighting_current"] is False,
        "no route score": s["route_score_current"] is False,
        "no winner": s["winner_current"] is False,
        "no yield detection": s["yield_detection_probability_current"] is False,
        "no COMSOL": s["comsol_launch_started"] is False,
        "no MPH": s["mph_load_started"] is False,
        "no final flow claim": s["trapezoid_flow_solver_final_claim_current"] is False,
    }
    for row in payload["solver_rows"]:
        checks[f"row not qch: {row['case_id']}"] = (
            row["not_qch_weighted"] == "true"
            and row["q_ch_weighting_current"] == "false"
            and row["route_score_current"] == "false"
            and row["winner_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Trapezoid Flow Solver Candidate",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Solver version: `{s['solver_version']}`.",
            f"- Semantic digest: `{s['semantic_digest']}`.",
            f"- Candidate solver rows: `{s['candidate_solver_output_rows']}`; blocked rows: `{s['blocked_solver_rows']}`.",
            f"- Theta85 resistance ratio vs rectangular proxy: `{s['theta85_resistance_ratio_vs_rectangle_proxy']}`.",
            "- This is candidate trapezoid Poisson/no-slip flow evidence. It is not q_ch weighting, route scoring, COMSOL validation, `.mph` evidence, wet evidence, fabrication, or production.",
            "",
        ]
    )


def artifact_manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "trapezoid_flow_solver_candidate_not_qch",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    report_dir: Path = REPORT_DIR,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_SOLVER_ROWS_20260701.csv": payload["solver_rows"],
        f"{PREFIX}_QCH_PROMOTION_BLOCKERS_20260701.csv": payload["qch_blockers"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = output_dir / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = output_dir / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_json_path = output_dir / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_json_path, payload)
    paths.append(report_json_path)

    public_report = report_dir / "521_NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = output_dir / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, artifact_manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_trapezoid_flow_solver_candidate:
        parser.error("--confirm-trapezoid-flow-solver-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
