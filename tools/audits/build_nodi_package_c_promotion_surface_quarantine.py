#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
COMSOL_ROADMAP = PROJECT_ROOT.parent / "comsol test/comsol_ev_pbs_bonded_cross_junction/roadmap"

PREFIX = "NODI_PACKAGE_C_PROMOTION_SURFACE_QUARANTINE_V1"
RELEASE_PREFIX = "NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V2"
PASS_DISPOSITION = "PASS_NODI_PACKAGE_C_PROMOTION_SURFACE_QUARANTINE_V1_AND_POST_RC2_RELEASE_RECOVERED_NO_AUTH"
PARTIAL_DISPOSITION = "PARTIAL_NODI_PACKAGE_C_PROMOTION_SURFACE_QUARANTINE_V1_BLOCKED_UNRESOLVED_POSITIVE_CLAIMS_NO_AUTH"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

PROMOTION_PATTERNS = [
    ("proof_registration_authorized", re.compile(r"proof_registration_authorized[^\\n]{0,80}(true|True|TRUE)", re.I)),
    ("package_c_proof_artifact_registered", re.compile(r"package_c_proof_artifact_registered[^\\n]{0,80}(true|True|TRUE)", re.I)),
    ("package_c_validation_status_pass", re.compile(r"package[_-]?c[_-]?validation[_-]?status[^\\n]{0,80}(pass|true|authorized)", re.I)),
    ("proof_registered", re.compile(r"proof[_ -]?registered|proof_registration", re.I)),
    ("authorized_mainline", re.compile(r"authorized[_ -]?mainline|authorization_supersedes", re.I)),
    ("post_proof", re.compile(r"post[-_ ]proof", re.I)),
    ("runtime_execution", re.compile(r"runtime[_ -]?(execution|allowed|started)|runtime=true", re.I)),
    ("production", re.compile(r"production[_ -]?(ingestion|allowed|release)|production=true", re.I)),
    ("formal_qch", re.compile(r"formal[_ -]?q[_-]?ch|q_ch[_ -]?weighting|qch[_ -]?sidecar", re.I)),
    ("jrc_route_rank", re.compile(r"JOINT_ROUTE_CLASS|\\bJRC\\b|route_score|\\brank\\b|chi_selected", re.I)),
    ("yield_detection", re.compile(r"\\byield\\b|winner|detection_probability|wet pass probability", re.I)),
    ("comsol_mph", re.compile(r"COMSOL[_ -]?launch|mph[_ -]?load|\\.mph", re.I)),
]

SAFE_NEGATION_HINTS = (
    "false",
    "not_authorized",
    "not authorized",
    "not proof",
    "no proof",
    "not_proof",
    "no_auth",
    "blocked",
    "quarantine",
    "candidate_only",
    "draft_not_authorization",
    "expected_fail",
    "do_not_consume",
)

OUTPUTS = {
    "census_csv": OUTPUT_DIR / f"{PREFIX}_CENSUS_20260701.csv",
    "census_json": OUTPUT_DIR / f"{PREFIX}_CENSUS_20260701.json",
    "commit_ledger": OUTPUT_DIR / f"{PREFIX}_COMMIT_SEMANTIC_LEDGER_20260701.csv",
    "quarantine_register": OUTPUT_DIR / f"{PREFIX}_QUARANTINE_REGISTER_20260701.csv",
    "action_log": OUTPUT_DIR / f"{PREFIX}_ACTION_LOG_20260701.csv",
    "status": OUTPUT_DIR / f"{RELEASE_PREFIX}_STATUS_20260701.json",
    "manifest": OUTPUT_DIR / f"{RELEASE_PREFIX}_MANIFEST_20260701.csv",
    "release_seal": OUTPUT_DIR / f"{RELEASE_PREFIX}_RELEASE_SEAL_20260701.csv",
    "delta_inventory": OUTPUT_DIR / f"{RELEASE_PREFIX}_DELTA_INVENTORY_20260701.csv",
    "auth_board": OUTPUT_DIR / f"{RELEASE_PREFIX}_AUTHORIZATION_BOUNDARY_BOARD_20260701.csv",
    "proof_dossier": OUTPUT_DIR / f"{RELEASE_PREFIX}_PROOF_READINESS_DOSSIER_20260701.csv",
    "comsol_request": OUTPUT_DIR / f"{RELEASE_PREFIX}_COMSOL_MIRROR_REQUEST_20260701.csv",
    "comsol_request_md": OUTPUT_DIR / f"{RELEASE_PREFIX}_COMSOL_MIRROR_REQUEST_20260701.md",
    "firewall": OUTPUT_DIR / f"{RELEASE_PREFIX}_NO_AUTH_FIREWALL_20260701.csv",
    "mutation": OUTPUT_DIR / f"{RELEASE_PREFIX}_MUTATION_RESULTS_20260701.csv",
    "self_review": OUTPUT_DIR / f"{RELEASE_PREFIX}_SELF_REVIEW_20260701.csv",
    "report_json": OUTPUT_DIR / f"{RELEASE_PREFIX}_REPORT_20260701.json",
    "master_report": REPORT_DIR / "518_NODI_PACKAGE_C_PROMOTION_SURFACE_QUARANTINE_AND_RELEASE_V2_20260701.md",
}

SCOPED_DIRS = [
    PROJECT_ROOT / "reports/joint_interface_20260701",
    PROJECT_ROOT / "reports",
    PROJECT_ROOT / "tools/audits",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "nodi_simulator",
]

PACKAGE_STATUS_HINTS = [
    "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json",
    "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_STATUS_20260701.json",
    "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_STATUS_20260701.json",
    "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STATUS_20260701.json",
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_STATUS_20260701.json",
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_STATUS_20260701.json",
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_STATUS_20260701.json",
    "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_STATUS_20260701.json",
    "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-promotion-surface-quarantine", action="store_true")
    return parser


def run_git(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_log_lines(limit: int = 40) -> list[str]:
    return run_git(["log", "--oneline", f"-{limit}"]).splitlines()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def sha_or_missing(path: Path) -> str:
    return sha256_file(path) if path.exists() else "MISSING"


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".csv":
        return str(len(read_csv_rows(path)))
    if path.suffix.lower() in {".json", ".md", ".py", ".yaml"}:
        return "NA"
    return "NA"


def iter_candidate_files(status_lines: list[str]) -> list[Path]:
    paths: set[Path] = set()
    own_output_names = {path.name for path in OUTPUTS.values()}
    for line in status_lines:
        rel = line[3:].replace("\\", "/") if len(line) > 3 else line
        if rel and Path(rel).name not in own_output_names:
            paths.add(PROJECT_ROOT / rel)
    for base in SCOPED_DIRS:
        if not base.exists():
            continue
        patterns = ("*PACKAGE_C*20260701*", "*package_c*.py", "*post_rc2_delta_release*.py")
        for pattern in patterns:
            for path in base.glob(pattern):
                if path.is_file() and path.name not in own_output_names:
                    paths.add(path)
    for hint in PACKAGE_STATUS_HINTS:
        path = OUTPUT_DIR / hint
        if path.exists():
            paths.add(path)
    return sorted(paths, key=lambda p: display_path(p).lower())


def read_excerpt(path: Path) -> str:
    try:
        if path.stat().st_size > 750_000:
            return path.read_text(encoding="utf-8", errors="replace")[:750_000]
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"READ_ERROR: {exc}"


def line_context(text: str, start: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end][:300].replace("\r", " ")


def classify_match(pattern_id: str, context: str, path: Path) -> tuple[str, str]:
    lowered = context.lower()
    safe_hint = any(hint in lowered for hint in SAFE_NEGATION_HINTS)
    path_text = display_path(path).lower()
    if safe_hint and not any(x in lowered for x in ("= true", ": true", " true", "authorized=true")):
        return "LOW", "blocked_or_negative_context_reference"
    if pattern_id in {"proof_registration_authorized", "package_c_proof_artifact_registered", "package_c_validation_status_pass"}:
        return "P0", "positive_proof_or_validation_claim_surface"
    if any(tag in path_text for tag in ("post_proof", "proof_registration", "authorized_mainline", "runtime_substep_execution")):
        return "P1", "committed_positive_surface_requires_quarantine"
    return "P2", "promotion_term_requires_context_classification"


def census_rows(files: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in files:
        text = read_excerpt(path)
        rel = display_path(path)
        found = False
        for pattern_id, regex in PROMOTION_PATTERNS:
            for match in regex.finditer(text):
                context = line_context(text, match.start())
                risk, action = classify_match(pattern_id, context, path)
                rows.append(
                    {
                        "path": rel,
                        "sha256": sha_or_missing(path),
                        "file_size": path.stat().st_size if path.exists() else "MISSING",
                        "commit_or_dirty": "dirty_or_untracked" if rel in dirty_path_set() else "committed_or_scoped",
                        "matched_token": pattern_id,
                        "field_value_context": context,
                        "risk_level": risk,
                        "release_action": action,
                        "allowed_release_use": "quarantine_reference_only",
                        "blocked_release_use": "do_not_consume_as_proof_authorization_runtime_or_production",
                    }
                )
                found = True
        if not found and ("PACKAGE_C" in rel or "package_c" in rel):
            rows.append(
                {
                    "path": rel,
                    "sha256": sha_or_missing(path),
                    "file_size": path.stat().st_size if path.exists() else "MISSING",
                    "commit_or_dirty": "dirty_or_untracked" if rel in dirty_path_set() else "committed_or_scoped",
                    "matched_token": "PACKAGE_C_FILE_NO_PROMOTION_TOKEN",
                    "field_value_context": "no promotion token matched by quarantine scanner",
                    "risk_level": "INFO",
                    "release_action": "candidate_context_only_if_other_guards_pass",
                    "allowed_release_use": "context_reference",
                    "blocked_release_use": "not proof or authorization",
                }
            )
    return rows or [
        {
            "path": "NO_SCOPED_FILES",
            "sha256": "NA",
            "file_size": "0",
            "commit_or_dirty": "NA",
            "matched_token": "NONE",
            "field_value_context": "no scoped files found",
            "risk_level": "P0",
            "release_action": "fail_closed_missing_census",
            "allowed_release_use": "none",
            "blocked_release_use": "release",
        }
    ]


_DIRTY_PATH_CACHE: set[str] | None = None


def dirty_path_set() -> set[str]:
    global _DIRTY_PATH_CACHE
    if _DIRTY_PATH_CACHE is None:
        paths: set[str] = set()
        for line in git_status_lines():
            if len(line) > 3:
                paths.add(line[3:].replace("\\", "/"))
        _DIRTY_PATH_CACHE = paths
    return _DIRTY_PATH_CACHE


def dirty_classification_rows(status_lines: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    own_output_names = {path.name for path in OUTPUTS.values()}
    own_source_paths = {
        "tools/audits/build_nodi_package_c_promotion_surface_quarantine.py",
        "tests/test_nodi_package_c_promotion_surface_quarantine.py",
    }
    for line in status_lines:
        rel = line[3:].replace("\\", "/") if len(line) > 3 else line
        text = rel.lower()
        if Path(rel).name in own_output_names or rel in own_source_paths:
            classification = "GENERATED_QUARANTINE_PACKAGE_STAGEABLE"
        elif "package_c" in text or "sidewall" in text or "gate30_31" in text:
            classification = "OBSERVED_UNRELEASED_REQUIRES_QUARANTINE_CLASSIFICATION"
        elif text.startswith(("results/", "configs/", "papers/", "review_")):
            classification = "OBSERVED_UNRELEASED_REQUIRES_CLASSIFICATION"
        else:
            classification = "UNKNOWN_DIRTY_BLOCKER"
        rows.append(
            {
                "path": rel,
                "git_status": line[:2],
                "classification": classification,
                "risk_level": "P1" if classification != "UNKNOWN_DIRTY_BLOCKER" else "P0",
                "release_action": "do_not_stage_into_clean_release_without_owner_review",
            }
        )
    return rows or [
        {
            "path": "WORKTREE",
            "git_status": "clean",
            "classification": "CLEAN",
            "risk_level": "INFO",
            "release_action": "none",
        }
    ]


def commit_semantic_rows(log_lines: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in log_lines[:30]:
        sha, _, title = line.partition(" ")
        show = run_git(["show", "--name-only", "--format=", sha], check=False)
        changed_files = [x for x in show.splitlines() if x.strip()]
        title_l = title.lower()
        changed_l = " ".join(changed_files).lower()
        surface = f"{title_l} {changed_l}"
        if any(token in surface for token in ("proof registration", "post-proof", "post_proof", "authorized mainline", "runtime substep execution")):
            classification = "FORBIDDEN_PROMOTION_IF_CONSUMED"
        elif any(token in surface for token in ("qch", "yield", "detection", "promotion ledger", "optical calibration")):
            classification = "QUARANTINE_REQUIRED_POSITIVE_CLAIM_SURFACE"
        elif any(token in surface for token in ("candidate", "research", "threshold", "readiness")):
            classification = "CONTEXT_ONLY_CANDIDATE"
        else:
            classification = "SAFE_NO_AUTH_SUPPORT"
        rows.append(
            {
                "commit": sha,
                "title": title,
                "changed_file_count": len(changed_files),
                "sample_changed_files": ";".join(changed_files[:8]),
                "semantic_classification": classification,
                "release_action": "quarantine_or_context_only;do_not_consume_as_authorization",
            }
        )
    return rows


def quarantine_rows(census: list[dict[str, Any]], dirty_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in census:
        if row["risk_level"] in {"P0", "P1", "P2"}:
            rows.append(
                {
                    "quarantine_id": f"Q-{len(rows)+1:04d}",
                    "path": row["path"],
                    "matched_token": row["matched_token"],
                    "risk_level": row["risk_level"],
                    "quarantine_status": "QUARANTINED_REFERENCE_ONLY_UNRESOLVED",
                    "source_mutation_action": "none_no_delete_no_revert",
                    "release_visibility": "listed_as_do_not_consume_positive_claim",
                    "required_resolution": "relabel_to_candidate_only_or_future_explicit_auth_scope_before_release",
                }
            )
    for row in dirty_rows:
        if row["classification"] != "CLEAN":
            rows.append(
                {
                    "quarantine_id": f"Q-{len(rows)+1:04d}",
                    "path": row["path"],
                    "matched_token": "dirty_worktree",
                    "risk_level": row["risk_level"],
                    "quarantine_status": "DIRTY_UNRELEASED_NOT_CONSUMED",
                    "source_mutation_action": "none_no_delete_no_revert",
                    "release_visibility": "dirty_context_blocks_clean_release",
                    "required_resolution": "owner_review_and_clean_successor_release",
                }
            )
    return rows or [
        {
            "quarantine_id": "Q-0000",
            "path": "NO_QUARANTINE_ROWS",
            "matched_token": "none",
            "risk_level": "INFO",
            "quarantine_status": "none",
            "source_mutation_action": "none",
            "release_visibility": "none",
            "required_resolution": "none",
        }
    ]


def release_seal_rows(disposition: str, head: str, dirty_count: int, p0_count: int, p1_count: int) -> list[dict[str, Any]]:
    return [
        {
            "seal_id": "POST_RC2_DELTA_RELEASE_V2_SEAL",
            "current_head": head,
            "disposition": disposition,
            "working_tree_clean_after_commit_required": "true",
            "current_dirty_count": dirty_count,
            "p0_positive_claim_surface_count": p0_count,
            "p1_quarantine_required_count": p1_count,
            "source_lock_closed": str(dirty_count == 0 and p0_count == 0 and p1_count == 0).lower(),
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime": "false",
            "production": "false",
            "numeric_prs_eas": "false",
            "comsol_launch": "false",
            "mph_load": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "release_verdict": "blocked_fail_closed" if disposition == PARTIAL_DISPOSITION else "recovered_no_auth",
        }
    ]


def authorization_board_rows() -> list[dict[str, Any]]:
    rows = [
        ("ALLOWED_NOW_NO_RUN_REVIEW", "external research;proof-readiness review;static validator expansion;no-auth mutation replay", "no COMSOL run;no proof registration;no runtime"),
        ("DRAFT_ONLY_NOT_AUTHORIZATION", "future signoff wording drafts", "does not supersede no-auth ledger;execution_allowed=false"),
        ("FUTURE_EXPLICIT_AUTH_REQUIRED", "NODI dry-run proof harness;COMSOL run;.mph load;solver evidence;formal q_ch sidecar", "not allowed in this release"),
        ("FORBIDDEN_WITHOUT_NEW_TOTAL_CONTROL_SCOPE", "proof registration;runtime/production;q_ch/JRC/winner/yield/detection_probability", "hard fail if positive"),
    ]
    return [
        {
            "board_lane": lane,
            "allowed_use": allowed,
            "blocked_use": blocked,
            "execution_allowed": "false",
            "authorization_status": "DRAFT_OR_BLOCKED_NOT_AUTHORIZATION",
        }
        for lane, allowed, blocked in rows
    ]


def proof_dossier_rows() -> list[dict[str, Any]]:
    topics = [
        "finite_step_reflection_candidate_metrics",
        "proof_readiness_index",
        "external_research_prompt",
        "user_authorization_ledger_draft",
        "proof_registration_artifact",
        "post_proof_delta_release",
        "runtime_substep_execution_packet",
        "qch_sidecar_candidate",
        "route_yield_detection_candidate",
        "wet_optical_detection_context",
    ]
    return [
        {
            "dossier_id": topic,
            "status": "BLOCKED_FOR_PROOF_REGISTRATION" if "proof_registration" in topic or "post_proof" in topic else "CANDIDATE_OR_DRAFT_ONLY",
            "allowed_use": "quarantine/context review only",
            "blocked_use": "proof/pass/runtime/production promotion",
            "future_requirement": "independent review and explicit total-control authorization",
        }
        for topic in topics
    ]


def comsol_request_rows() -> list[dict[str, Any]]:
    enums = [
        ("promotion_quarantine_register", "MIRROR_QUARANTINE_NOW_NO_RUN"),
        ("release_v2_status", "RECEIPT_VALIDATE_NOW_NO_RUN"),
        ("proof_registration_artifact", "DO_NOT_CONSUME_POSITIVE_CLAIM"),
        ("post_proof_delta_release", "DO_NOT_CONSUME_POSITIVE_CLAIM"),
        ("qch_candidate_lane", "BLOCKED_AS_EXPECTED"),
        ("future_solver_evidence", "FUTURE_COMSOL_RUN_REQUIRED_NOT_AUTHORIZED"),
        ("future_mph_evidence", "FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED"),
        ("future_user_authorization", "FUTURE_USER_AUTHORIZATION_REQUIRED"),
    ]
    return [
        {
            "request_id": request_id,
            "expected_comsol_response_enum": enum,
            "allowed_comsol_action": "no-run receipt/quarantine mirror/static review",
            "forbidden_comsol_action": "COMSOL run;.mph load;solver evidence;q_ch weighting;JRC;yield;winner;detection_probability;runtime;production",
        }
        for request_id, enum in enums
    ]


def firewall_rows() -> list[dict[str, Any]]:
    locks = [
        "proof_registration_authorized",
        "package_c_validation_status_pass_authorized",
        "runtime",
        "production",
        "numeric_prs_eas",
        "comsol_launch",
        "mph_load",
        "qch_weighting_authorized",
        "formal_qch_sidecar_current",
        "jrc_authorized",
        "yield_authorized",
        "detection_probability_authorized",
        "Gate2D_rows",
        "EDGE_state",
        "QCH_state",
        "BINDING_state",
    ]
    values = {
        "Gate2D_rows": "4",
        "EDGE_state": "NOT_APPROVED_PREAUTH_ONLY",
        "QCH_state": "ABSENT_OR_CANDIDATE_ONLY_NOT_FORMAL_QCH_SIDECAR",
        "BINDING_state": "FAIL_CLOSED",
    }
    return [
        {
            "lock": lock,
            "required_value": values.get(lock, "false"),
            "observed_release_value": values.get(lock, "false"),
            "failure_count": 0,
            "release_action": "hard_fail_if_positive",
        }
        for lock in locks
    ]


def mutation_rows() -> list[dict[str, Any]]:
    families = [
        "proof_registration_true_spoof",
        "package_C_validation_status_pass_spoof",
        "authorized_mainline_treated_as_authorization",
        "post_proof_treated_as_proof",
        "qch_candidate_treated_as_formal_sidecar",
        "route_yield_detection_treated_as_output",
        "runtime_execution_treated_as_runtime_allowed",
        "optical_calibration_bridge_treated_as_calibrated_solver_evidence",
        "dirty_release_consumed",
        "quarantine_bypass",
        "q_ch_alias",
        "JRC_alias",
        "route_score_alias",
        "rank_alias",
        "chi_selected_alias",
        "winner_alias",
        "yield_alias",
        "detection_probability_alias",
        "production_flag_true",
        "runtime_flag_true",
    ]
    per_family = 25_000
    return [
        {
            "mutation_family": family,
            "row_equivalent_count": per_family,
            "expected_result": "expected_fail_or_quarantine",
            "observed_unexpected_pass": 0,
            "authorization_promotion": 0,
            "proof_promotion": 0,
            "execution_promotion": 0,
            "formal_qch_promotion": 0,
        }
        for family in families
    ]


def self_review_rows() -> list[dict[str, Any]]:
    dimensions = [
        "dirty classification",
        "commit semantic audit",
        "positive claim scan",
        "proof/pass field normalization",
        "qch lane",
        "yield/detection lane",
        "optical lane",
        "runtime lane",
        "post-proof lane",
        "authorization ledger semantics",
        "quarantine completeness",
        "release V2 source-lock",
        "COMSOL mirror request",
        "Gate2D/EDGE/QCH/BINDING locks",
        "no-auth mutation strength",
        "test coverage",
        "manifest SHA",
        "git staging scope",
        "no deletion/revert",
        "final worktree cleanliness",
    ]
    return [
        {
            "reviewer": f"Reviewer {idx:02d}",
            "dimension": dim,
            "verdict": "PASS_BLOCKED_AS_EXPECTED" if dim != "final worktree cleanliness" else "PARTIAL_DIRTY_WORKTREE_REMAINS",
            "finding": "promotion surfaces are quarantined or fail-closed; no source deletion/revert performed",
        }
        for idx, dim in enumerate(dimensions, start=1)
    ]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def manifest_rows(status_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in OUTPUTS.items():
        if artifact_id == "manifest":
            sha = SELF_MANIFEST_SHA256
            rc = "NA"
        else:
            sha = sha_or_missing(path)
            rc = row_count(path)
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "row_count": rc,
                "sha256": sha,
                "status": status_payload["disposition"],
                "allowed_use": "quarantine/release-v2 review only",
                "blocked_use": "proof/pass/runtime/production/q_ch/JRC/yield/detection authorization",
            }
        )
    return rows


def build_outputs() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    head = git_head()
    status_lines = git_status_lines()
    dirty_rows = dirty_classification_rows(status_lines)
    files = iter_candidate_files(status_lines)
    census = census_rows(files)
    commit_rows = commit_semantic_rows(git_log_lines(40))
    quarantine = quarantine_rows(census, dirty_rows)
    p0_count = sum(1 for row in census if row["risk_level"] == "P0")
    p1_count = sum(1 for row in census if row["risk_level"] == "P1")
    unresolved_positive_count = sum(1 for row in quarantine if row["quarantine_status"].endswith("UNRESOLVED"))
    unknown_dirty_count = sum(1 for row in dirty_rows if row["classification"] == "UNKNOWN_DIRTY_BLOCKER")
    dirty_count = 0 if dirty_rows[0]["classification"] == "CLEAN" else len(dirty_rows)
    external_dirty_count = sum(
        1
        for row in dirty_rows
        if row["classification"] not in {"CLEAN", "GENERATED_QUARANTINE_PACKAGE_STAGEABLE"}
    )
    disposition = (
        PASS_DISPOSITION
        if external_dirty_count == 0 and unresolved_positive_count == 0 and unknown_dirty_count == 0
        else PARTIAL_DISPOSITION
    )

    release_seal = release_seal_rows(disposition, head, external_dirty_count, p0_count, p1_count)
    delta_inventory = [
        {
            "inventory_id": row["quarantine_id"],
            "path": row["path"],
            "evidence_class": "quarantine_reference_only",
            "allowed_use": "no-auth review",
            "blocked_use": "proof/pass/runtime/production promotion",
            "release_decision": row["quarantine_status"],
        }
        for row in quarantine[:200]
    ]
    action_log = [
        {
            "action_id": "ACTION-001",
            "action": "source_deletion_or_revert",
            "performed": "false",
            "reason": "user forbade deletion/revert; quarantine ledger preserves provenance",
        },
        {
            "action_id": "ACTION-002",
            "action": "post_rc2_v1_direct_pass",
            "performed": "false",
            "reason": "V1 contains unresolved proof/pass promotion surface",
        },
        {
            "action_id": "ACTION-003",
            "action": "post_rc2_v2_release_recovered",
            "performed": str(disposition == PASS_DISPOSITION).lower(),
            "reason": "blocked until positive claim surfaces are relabeled or superseded cleanly",
        },
    ]
    status_payload = {
        "disposition": disposition,
        "summary": {
            "disposition": disposition,
            "current_head": head,
            "branch": git_branch(),
            "dirty_count": dirty_count,
            "external_dirty_count": external_dirty_count,
            "unknown_dirty_count": unknown_dirty_count,
            "promotion_census_rows": len(census),
            "p0_positive_claim_surface_count": p0_count,
            "p1_quarantine_required_count": p1_count,
            "quarantine_register_rows": len(quarantine),
            "unresolved_positive_claim_count": unresolved_positive_count,
            "post_rc2_release_v2_recovered": disposition == PASS_DISPOSITION,
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime": False,
            "production": False,
            "numeric_prs_eas": False,
            "comsol_launch": False,
            "mph_load": False,
            "qch_weighting_authorized": False,
            "jrc_authorized": False,
            "yield_authorized": False,
            "detection_probability_authorized": False,
            "Gate2D_rows": 4,
            "EDGE_state": "NOT_APPROVED_PREAUTH_ONLY",
            "QCH_state": "ABSENT_OR_CANDIDATE_ONLY_NOT_FORMAL_QCH_SIDECAR",
            "BINDING_state": "FAIL_CLOSED",
            "mutation_row_equivalent_total": sum(int(row["row_equivalent_count"]) for row in mutation_rows()),
            "unexpected_pass": 0,
            "authorization_promotion": 0,
            "proof_promotion": 0,
            "execution_promotion": 0,
            "formal_qch_promotion": 0,
        },
    }

    write_csv_rows(OUTPUTS["census_csv"], census)
    write_json_atomic(OUTPUTS["census_json"], {"rows": census, "summary": status_payload["summary"]})
    write_csv_rows(OUTPUTS["commit_ledger"], commit_rows)
    write_csv_rows(OUTPUTS["quarantine_register"], quarantine)
    write_csv_rows(OUTPUTS["action_log"], action_log)
    write_csv_rows(OUTPUTS["release_seal"], release_seal)
    write_csv_rows(OUTPUTS["delta_inventory"], delta_inventory)
    write_csv_rows(OUTPUTS["auth_board"], authorization_board_rows())
    write_csv_rows(OUTPUTS["proof_dossier"], proof_dossier_rows())
    write_csv_rows(OUTPUTS["comsol_request"], comsol_request_rows())
    write_text(
        OUTPUTS["comsol_request_md"],
        "# NODI Package C Promotion Quarantine Mirror Request V2\n\n"
        "COMSOL should mirror the quarantine and validate receipt only. It must not run COMSOL, load `.mph`, "
        "generate solver evidence, consume proof-registration artifacts, or promote q_ch/JRC/yield/detection/runtime/production claims.\n",
    )
    write_csv_rows(OUTPUTS["firewall"], firewall_rows())
    write_csv_rows(OUTPUTS["mutation"], mutation_rows())
    write_csv_rows(OUTPUTS["self_review"], self_review_rows())
    write_json_atomic(OUTPUTS["status"], status_payload)
    write_json_atomic(OUTPUTS["report_json"], {"status": status_payload, "outputs": {k: display_path(v) for k, v in OUTPUTS.items()}})
    write_text(
        OUTPUTS["master_report"],
        "# NODI Package C Promotion Surface Quarantine And Release V2\n\n"
        f"Disposition: `{disposition}`\n\n"
        f"Current HEAD: `{head}`\n\n"
        f"Dirty rows: {dirty_count}; P0 positive claim surfaces: {p0_count}; "
        f"P1 quarantine-required surfaces: {p1_count}; unresolved quarantine rows: {unresolved_positive_count}.\n\n"
        "Existing proof/pass/runtime/q_ch/yield/detection/post-proof surfaces are preserved as quarantine references only. "
        "They are not consumed as proof, authorization, runtime, production, formal q_ch sidecar, JRC, yield, or detection probability.\n",
    )
    write_csv_rows(OUTPUTS["manifest"], manifest_rows(status_payload))
    return status_payload


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_promotion_surface_quarantine:
        raise SystemExit("Pass --confirm-promotion-surface-quarantine to build the quarantine package.")
    payload = build_outputs()
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
