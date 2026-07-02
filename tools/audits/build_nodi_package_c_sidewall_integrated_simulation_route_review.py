#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
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
PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_READY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_FAIL_CLOSED"
)
CLAIM_BOUNDARY = (
    "simulation_current_route_yield_detection_not_fabrication_or_production"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

DUAL_TRACK_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK_STATUS_20260701.json"
ROUTE_POLICY_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_POLICY_ROWS_20260701.csv"
WINNER_JRC_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_REVIEW_ROWS_20260701.csv"
CLAIM_VALUE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_VALUE_ROWS_20260701.csv"
READINESS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_STATUS_20260701.json"

ALLOWED_USE = (
    "integrated simulation-only route/yield/detection review after dual-track lock"
)
BLOCKED_USE = (
    "fabrication release;production ingestion;experimental claim;COMSOL rerun claim;"
    "bare final route_score/winner/JRC/yield/detection_probability"
)

SOURCE_FILES = {
    "dual_track_status": DUAL_TRACK_STATUS,
    "route_formula_policy_rows": ROUTE_POLICY_ROWS,
    "winner_jrc_review_rows": WINNER_JRC_ROWS,
    "yield_detection_claim_value_rows": CLAIM_VALUE_ROWS,
    "route_decision_readiness_status": READINESS_STATUS,
    "integrated_review_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_simulation_route_review.py",
    "integrated_review_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_simulation_route_review.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build integrated sidewall simulation route review."
    )
    parser.add_argument(
        "--confirm-sidewall-integrated-simulation-route-review",
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


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/584_{PREFIX}_20260701.md"
    build_edit_paths = {
        "tools/audits/build_nodi_package_c_sidewall_integrated_simulation_route_review.py",
        "tests/test_nodi_package_c_sidewall_integrated_simulation_route_review.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "integrated_simulation_route_review_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "integrated_simulation_route_review_output"
            release_decision = "included_or_rewritten_by_integrated_review_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_integrated_simulation_route_review"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def build_review_rows() -> list[dict[str, Any]]:
    policy_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(ROUTE_POLICY_ROWS)
    }
    winner_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(WINNER_JRC_ROWS)
    }
    claim_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(CLAIM_VALUE_ROWS)
    }
    rows: list[dict[str, Any]] = []
    for route_id in sorted(policy_by_route):
        policy = policy_by_route[route_id]
        winner = winner_by_route.get(route_id, {})
        claim = claim_by_route.get(route_id, {})
        top = _bool(winner.get("simulation_top_candidate_current"))
        rank = _int(winner.get("candidate_order_index_under_policy"))
        rows.append(
            {
                "integrated_review_row_id": f"INTEGRATED-SIM-ROUTE-REVIEW-{route_id}",
                "integrated_review_version": "sidewall_integrated_simulation_route_review_v1",
                "route_candidate_id": route_id,
                "route_geometry_family": policy.get("route_geometry_family", ""),
                "simulation_route_score_current": _bool(
                    policy.get("simulation_route_score_candidate_current")
                ),
                "simulation_route_score_value": _float(
                    policy.get("route_score_candidate_value")
                ),
                "simulation_rank_index": rank,
                "simulation_winner_current": top,
                "simulation_JRC_current": True,
                "simulation_JRC_value": (
                    "SIMULATION_TOP_ROUTE" if top else f"SIMULATION_RANK_{rank}"
                ),
                "simulation_yield_current": _bool(
                    claim.get("yield_simulation_candidate_current")
                ),
                "simulation_yield_value": _float(
                    claim.get("yield_simulation_candidate_value")
                ),
                "simulation_yield_ci_low": _float(
                    claim.get("yield_simulation_candidate_ci_low")
                ),
                "simulation_yield_ci_high": _float(
                    claim.get("yield_simulation_candidate_ci_high")
                ),
                "simulation_detection_probability_current": _bool(
                    claim.get("detection_probability_simulation_candidate_current")
                ),
                "simulation_detection_probability_value": _float(
                    claim.get("detection_probability_simulation_candidate_value")
                ),
                "simulation_detection_probability_ci_low": _float(
                    claim.get("detection_probability_simulation_candidate_ci_low")
                ),
                "simulation_detection_probability_ci_high": _float(
                    claim.get("detection_probability_simulation_candidate_ci_high")
                ),
                "simulation_wet_pass_probability_current": _bool(
                    claim.get("wet_pass_probability_simulation_candidate_current")
                ),
                "simulation_wet_pass_probability_value": _float(
                    claim.get("wet_pass_probability_simulation_candidate_value")
                ),
                "route_score_current": False,
                "winner_current": False,
                "JRC_current": False,
                "yield_current": False,
                "detection_probability_current": False,
                "wet_pass_probability_current": False,
                "production_ingestion_current": False,
                "integrated_simulation_review_status": (
                    "simulation_integrated_winner_ready"
                    if top
                    else "simulation_integrated_ranked_candidate_ready"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps({"review_rows": payload["review_rows"]}, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    dual = load_summary(DUAL_TRACK_STATUS)
    readiness = load_summary(READINESS_STATUS)
    rows = build_review_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    final_current_total = sum(
        sum(_int(row[key]) for key in (
            "route_score_current",
            "winner_current",
            "JRC_current",
            "yield_current",
            "detection_probability_current",
            "wet_pass_probability_current",
            "production_ingestion_current",
        ))
        for row in rows
    )
    simulation_ready_rows = sum(
        row["simulation_route_score_current"]
        and row["simulation_JRC_current"]
        and row["simulation_yield_current"]
        and row["simulation_detection_probability_current"]
        and row["simulation_wet_pass_probability_current"]
        for row in rows
    )
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    winner_rows = sum(row["simulation_winner_current"] for row in rows)
    disposition = DISPOSITION
    if (
        dual.get("disposition") != "NODI_PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK_READY"
        or source_missing
        or len(rows) != 2
        or simulation_ready_rows != len(rows)
        or winner_rows != 1
        or final_current_total != 0
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_dual_track_disposition": str(dual.get("disposition", "")),
        "source_readiness_disposition": str(readiness.get("disposition", "")),
        "review_rows": len(rows),
        "simulation_ready_rows": simulation_ready_rows,
        "simulation_route_score_current_rows": sum(
            row["simulation_route_score_current"] for row in rows
        ),
        "simulation_winner_current_rows": winner_rows,
        "simulation_JRC_current_rows": sum(
            row["simulation_JRC_current"] for row in rows
        ),
        "simulation_yield_current_rows": sum(
            row["simulation_yield_current"] for row in rows
        ),
        "simulation_detection_probability_current_rows": sum(
            row["simulation_detection_probability_current"] for row in rows
        ),
        "simulation_wet_pass_probability_current_rows": sum(
            row["simulation_wet_pass_probability_current"] for row in rows
        ),
        "top_route_candidate_id": next(
            (row["route_candidate_id"] for row in rows if row["simulation_winner_current"]),
            "",
        ),
        "top_route_geometry_family": next(
            (
                row["route_geometry_family"]
                for row in rows
                if row["simulation_winner_current"]
            ),
            "",
        ),
        "final_current_total_rows": final_current_total,
        "production_ingestion_current_rows": 0,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "use simulation_current rows for assumption-bound route narrative and "
            "optional production/fabrication-separated promotion package"
        ),
    }
    payload = {
        "summary": summary,
        "review_rows": rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("integrated_review_not_ready")
    if summary["review_rows"] != 2:
        failures.append("expected_two_review_rows")
    if summary["simulation_ready_rows"] != 2:
        failures.append("expected_two_simulation_ready_rows")
    if summary["simulation_winner_current_rows"] != 1:
        failures.append("expected_one_simulation_winner")
    if summary["final_current_total_rows"] != 0:
        failures.append("final_current_rows_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "review_rows": OUTPUT_DIR / f"{PREFIX}_REVIEW_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"584_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {
            "disposition": payload["summary"]["disposition"],
            "summary": payload["summary"],
        },
        sort_keys=True,
    )
    write_csv_rows(outputs["review_rows"], payload["review_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Integrated Simulation Route Review",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Simulation-ready rows: `{s['simulation_ready_rows']}` / `{s['review_rows']}`.",
            f"Simulation winner: `{s['top_route_candidate_id']}` (`{s['top_route_geometry_family']}`).",
            f"Final-current total rows: `{s['final_current_total_rows']}`.",
            "",
            (
                "This package promotes candidate values into an assumption-bound "
                "simulation-current review layer. It does not declare fabrication, "
                "production, or experimental performance."
            ),
            "",
        ]
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_integrated_simulation_route_review:
        raise SystemExit(
            "--confirm-sidewall-integrated-simulation-route-review is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
