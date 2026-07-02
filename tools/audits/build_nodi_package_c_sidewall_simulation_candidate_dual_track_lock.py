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
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK_READY"
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_SIMULATION_CANDIDATE_DUAL_TRACK_LOCK_FAIL_CLOSED"
)
CLAIM_BOUNDARY = "simulation_candidates_available_final_claims_locked_false"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

WET_INTAKE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_STATUS_20260701.json"
CLAIM_VALUE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_STATUS_20260701.json"
ROUTE_FORMULA_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_STATUS_20260701.json"
WINNER_JRC_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_STATUS_20260701.json"
READINESS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_STATUS_20260701.json"

ALLOWED_USE = (
    "simulation-candidate route ranking and integrated review bookkeeping; "
    "candidate values may drive the simulation branch"
)
BLOCKED_USE = (
    "final route_score;final winner;final JRC;final yield;final detection_probability;"
    "wet_pass_probability as final production claim;production ingestion;fabrication release"
)

SOURCE_FILES = {
    "wet_intake_status": WET_INTAKE_STATUS,
    "claim_value_status": CLAIM_VALUE_STATUS,
    "route_formula_policy_status": ROUTE_FORMULA_STATUS,
    "winner_jrc_policy_status": WINNER_JRC_STATUS,
    "route_decision_readiness_status": READINESS_STATUS,
    "dual_track_lock_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
    "dual_track_lock_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
}

FINAL_KEYS = (
    "route_score_current_rows",
    "winner_current_rows",
    "JRC_current_rows",
    "yield_current_rows",
    "detection_probability_current_rows",
    "wet_pass_probability_current_rows",
    "production_ingestion_current_rows",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall simulation-candidate/final-current dual-track lock."
    )
    parser.add_argument(
        "--confirm-sidewall-simulation-candidate-dual-track-lock",
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
    output_report = f"reports/583_{PREFIX}_20260701.md"
    build_edit_paths = {
        "tools/audits/build_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
        "tests/test_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "dual_track_lock_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "dual_track_lock_output"
            release_decision = "included_or_rewritten_by_dual_track_lock_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_dual_track_lock"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def lock_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    claim_value = sources["claim_value"]
    route_formula = sources["route_formula"]
    winner_jrc = sources["winner_jrc"]
    readiness = sources["readiness"]
    wet = sources["wet"]
    return [
        {
            "track_id": "wet_surface_observation",
            "candidate_signal": "wet_accepted_observation_rows_total",
            "simulation_candidate_rows": _int(
                readiness.get(
                    "wet_accepted_observation_rows_total",
                    wet.get("accepted_observation_rows_total", 0),
                )
            ),
            "final_current_rows": _int(
                readiness.get("wet_pass_probability_current_rows", 0)
            ),
            "candidate_ready": _int(
                readiness.get(
                    "wet_accepted_observation_rows_total",
                    wet.get("accepted_observation_rows_total", 0),
                )
            )
            > 0,
            "final_locked_false": _int(
                readiness.get("wet_pass_probability_current_rows", 0)
            )
            == 0,
        },
        {
            "track_id": "route_score",
            "candidate_signal": "simulation_route_score_candidate_current_rows",
            "simulation_candidate_rows": _int(
                route_formula.get("simulation_route_score_candidate_current_rows", 0)
            ),
            "final_current_rows": _int(route_formula.get("route_score_current_rows", 0)),
            "candidate_ready": _int(
                route_formula.get("simulation_route_score_candidate_current_rows", 0)
            )
            > 0,
            "final_locked_false": _int(route_formula.get("route_score_current_rows", 0))
            == 0,
        },
        {
            "track_id": "winner_jrc",
            "candidate_signal": "simulation_top_candidate_current_rows",
            "simulation_candidate_rows": _int(
                winner_jrc.get("simulation_top_candidate_current_rows", 0)
            ),
            "final_current_rows": _int(winner_jrc.get("winner_current_rows", 0))
            + _int(winner_jrc.get("JRC_current_rows", 0)),
            "candidate_ready": _int(
                winner_jrc.get("simulation_top_candidate_current_rows", 0)
            )
            > 0,
            "final_locked_false": (
                _int(winner_jrc.get("winner_current_rows", 0)) == 0
                and _int(winner_jrc.get("JRC_current_rows", 0)) == 0
            ),
        },
        {
            "track_id": "yield_detection_values",
            "candidate_signal": "yield_detection_values_ready_rows",
            "simulation_candidate_rows": _int(
                readiness.get("yield_detection_values_ready_rows", 0)
            ),
            "final_current_rows": _int(claim_value.get("yield_current_rows", 0))
            + _int(claim_value.get("detection_probability_current_rows", 0))
            + _int(claim_value.get("wet_pass_probability_current_rows", 0)),
            "candidate_ready": _int(readiness.get("yield_detection_values_ready_rows", 0))
            > 0,
            "final_locked_false": (
                _int(claim_value.get("yield_current_rows", 0)) == 0
                and _int(claim_value.get("detection_probability_current_rows", 0)) == 0
                and _int(claim_value.get("wet_pass_probability_current_rows", 0)) == 0
            ),
        },
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps({"lock_rows": payload["lock_rows"]}, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    sources = {
        "wet": load_summary(WET_INTAKE_STATUS),
        "claim_value": load_summary(CLAIM_VALUE_STATUS),
        "route_formula": load_summary(ROUTE_FORMULA_STATUS),
        "winner_jrc": load_summary(WINNER_JRC_STATUS),
        "readiness": load_summary(READINESS_STATUS),
    }
    rows = lock_rows(sources)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    final_current_total = sum(
        _int(sources["readiness"].get(key, sources["route_formula"].get(key, 0)))
        for key in FINAL_KEYS
    )
    candidate_ready_rows = sum(row["candidate_ready"] for row in rows)
    final_locked_rows = sum(row["final_locked_false"] for row in rows)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    disposition = DISPOSITION
    if source_missing or candidate_ready_rows != len(rows) or final_current_total != 0:
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_wet_disposition": str(sources["wet"].get("disposition", "")),
        "source_claim_value_disposition": str(
            sources["claim_value"].get("disposition", "")
        ),
        "source_route_formula_disposition": str(
            sources["route_formula"].get("disposition", "")
        ),
        "source_winner_jrc_disposition": str(
            sources["winner_jrc"].get("disposition", "")
        ),
        "source_readiness_disposition": str(
            sources["readiness"].get("disposition", "")
        ),
        "lock_rows": len(rows),
        "candidate_ready_rows": candidate_ready_rows,
        "final_locked_false_rows": final_locked_rows,
        "final_current_total_rows": final_current_total,
        "route_score_candidate_ready_rows": _int(
            sources["readiness"].get("route_score_candidate_ready_rows", 0)
        ),
        "winner_jrc_candidate_ready_rows": _int(
            sources["readiness"].get("winner_jrc_candidate_ready_rows", 0)
        ),
        "yield_detection_values_ready_rows": _int(
            sources["readiness"].get("yield_detection_values_ready_rows", 0)
        ),
        "wet_accepted_observation_rows_total": _int(
            sources["readiness"].get("wet_accepted_observation_rows_total", 0)
        ),
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
            "use simulation candidate rows for integrated simulation route review; "
            "do not promote final/current claims without a separate promotion package"
        ),
    }
    payload = {
        "summary": summary,
        "lock_rows": rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("dual_track_lock_not_ready")
    if summary["lock_rows"] != 4:
        failures.append("expected_four_lock_rows")
    if summary["candidate_ready_rows"] != 4:
        failures.append("expected_all_candidate_tracks_ready")
    if summary["final_locked_false_rows"] != 4:
        failures.append("expected_all_final_tracks_locked_false")
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
        "lock_rows": OUTPUT_DIR / f"{PREFIX}_LOCK_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"583_{PREFIX}_20260701.md",
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
    write_csv_rows(outputs["lock_rows"], payload["lock_rows"])
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
            "# NODI Package C Sidewall Simulation Candidate Dual-Track Lock",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Candidate-ready tracks: `{s['candidate_ready_rows']}` / `{s['lock_rows']}`.",
            f"Final-current total rows: `{s['final_current_total_rows']}`.",
            f"Route-score candidate rows: `{s['route_score_candidate_ready_rows']}`.",
            f"Winner/JRC candidate rows: `{s['winner_jrc_candidate_ready_rows']}`.",
            f"Yield/detection value rows: `{s['yield_detection_values_ready_rows']}`.",
            f"Wet accepted observation rows: `{s['wet_accepted_observation_rows_total']}`.",
            "",
            (
                "This lock means the simulation-candidate branch is ready to keep "
                "moving, while final/current route, wet, yield, detection, and "
                "production claims remain explicitly false."
            ),
            "",
        ]
    )


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_simulation_candidate_dual_track_lock:
        raise SystemExit(
            "--confirm-sidewall-simulation-candidate-dual-track-lock is required"
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
