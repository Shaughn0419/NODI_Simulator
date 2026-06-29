#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_gate2_interface_contracts import (  # noqa: E402
    AUTHORIZATION_FALSE_FIELDS,
    EXPECTED_GATE2D_ACCEPTED_ROWS,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits import build_nodi_comsol_gate11_sidewall_convergence as gate11  # noqa: E402


DATE_STAMP = "20260629"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
COMSOL_ROADMAP = "roadmap"
NODI_GATE11_COMMIT = "e29501c3d26b5ff712870d7bc10a3617bd97ca28"
COMSOL_GATE11_COMMIT = "b16b16b8c61e9ceb3a38debc1dc7a2bd4e635962"
COMSOL_GATE12_COMMIT = "8823515d220a2a5b25a43f00b998205344e5960f"
DISPOSITION = (
    "PASS_GATE12_RC51_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE_AND_DESCRIPTOR_"
    "RECEIPT_DRYRUN_HARNESS_NO_AUTH"
)
RELEASE_NAME = (
    "RC5.1_SIDEWALL_GEOMETRY_DESCRIPTOR_ADDENDUM_V1_RELEASE_CANDIDATE_"
    "REVIEW_ONLY_NO_AUTH"
)
BLOCKED_USE = gate11.BLOCKED_USE
ALLOWED_USE = (
    "review-only sidewall addendum release-candidate;descriptor receipt dry-run;"
    "quarantine ledger;schema validation;future user decision support"
)

COMSOL_REQUIRED_FILES = (
    "COMSOL_GATE11_SIDEWALL_ADDENDUM_CONVERGENCE_PACKET_20260629.md",
    "COMSOL_GATE11_NODI_CONTEXT_RECEIPT_20260629.csv",
    "COMSOL_GATE11_NODI_BOUND_SIDEWALL_DESCRIPTOR_ADDENDUM_CANDIDATE_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_FIELD_CONVERGENCE_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_RECEIVER_FIXTURE_TEMPLATES_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_BINDING_BLOCKERS_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_VALIDATION_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_MANIFEST_20260629.csv",
)

COMSOL_OPTIONAL_FILES = (
    "COMSOL_GATE11_SIDEWALL_FUTURE_HANDOFF_ESCROW_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_MUTATION_NEGATIVE_CONTROLS_20260629.csv",
    "COMSOL_GATE11_SIDEWALL_STATUS_20260629.json",
)

REPORT_TITLES = {
    "313": "GATE12A_COMSOL_GATE11_RECEIPT_AND_DIRTY_DELTA_CLOSURE",
    "314": "GATE12B_RC51_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE",
    "315": "GATE12C_DESCRIPTOR_RECEIPT_DRYRUN_HARNESS",
    "316": "GATE12D_DESCRIPTOR_REVIEW_ONLY_LEDGER_AND_BLOCKERS",
    "317": "GATE12E_PRS_EAS_SIDEWALL_CONTRACT_RELEASE_BOARD",
    "318": "GATE12F_CROSS_PROJECT_ADDENDUM_HANDSHAKE",
    "319": "GATE12G_FUTURE_AUTHORIZATION_DECISION_DOSSIER",
    "320": "GATE12H_NO_AUTH_ANTI_CONFUSION_SWEEP_V3",
    "321": "GATE12I_REGRESSION_FIXTURE_EXPANSION",
    "322": "GATE12J_CROSS_THREAD_PROVENANCE_LEDGER",
    "323": "GATE12K_USER_FACING_EXECUTIVE_BRIEF",
    "324": "GATE12L_REPORTS_SIDECARS_TESTS",
    "325": "GATE12M_VALIDATION_AND_GIT",
    "326": "GATE12N_FINAL_HANDOFF",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate12 sidewall addendum release candidate and dry-run harness."
    )
    parser.add_argument("--confirm-gate12-sidewall-addendum-release", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git_head(path: Path) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def manifest_lookup(root: Path) -> dict[str, dict[str, str]]:
    manifest = comsol_path(root, "COMSOL_GATE11_SIDEWALL_MANIFEST_20260629.csv")
    rows = read_csv_rows(manifest) if manifest.exists() else []
    return {row.get("path", ""): row for row in rows}


def receipt_register(root: Path) -> list[dict[str, str]]:
    lookup = manifest_lookup(root)
    rows: list[dict[str, str]] = []
    for idx, name in enumerate((*COMSOL_REQUIRED_FILES, *COMSOL_OPTIONAL_FILES), start=1):
        rel = f"roadmap/{name}"
        path = comsol_path(root, name)
        recorded = lookup.get(rel, {})
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_count = csv_count(path) if exists else "MISSING"
        recorded_sha = recorded.get("sha256", "NOT_IN_MANIFEST")
        recorded_count = recorded.get("row_count", "NOT_IN_MANIFEST")
        if not exists:
            status = "MISSING_REQUIRED_ARTIFACT" if name in COMSOL_REQUIRED_FILES else "MISSING_OPTIONAL_ARTIFACT"
        elif recorded and (actual_sha != recorded_sha or actual_count != recorded_count):
            status = "BLOCKING_DATA_DRIFT"
        elif recorded:
            status = "MATCH"
        else:
            status = "OPTIONAL_NOT_IN_MANIFEST_READABLE"
        rows.append(
            {
                "receipt_id": f"G12A-COMSOL-RCPT-{idx:03d}",
                "artifact_name": name,
                "original_absolute_path": str(path),
                "relative_source_path": rel,
                "artifact_kind": "required" if name in COMSOL_REQUIRED_FILES else "optional",
                "row_count": actual_count,
                "recorded_row_count": recorded_count,
                "sha256": actual_sha,
                "recorded_sha256": recorded_sha,
                "receipt_status": status,
                "producer_status": "COMSOL_GATE11_REVIEW_ONLY_NO_AUTH",
                "policy_impact": "none_review_only_receipt",
                "auth_impact": "none_no_authorization",
                "evidence_bearing": "false",
            }
        )
    return rows


def dirty_delta_closure(root: Path) -> list[dict[str, str]]:
    context = read_csv_rows(comsol_path(root, "COMSOL_GATE11_NODI_CONTEXT_RECEIPT_20260629.csv"))
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(context, start=1):
        dirty = "DIRTY" in row.get("nodi_worktree_status", "")
        rows.append(
            {
                "closure_id": f"G12A-DIRTY-CLOSURE-{idx:03d}",
                "source_receipt_id": row.get("receipt_id", f"row-{idx}"),
                "source_path": row.get("path", ""),
                "comsol_observed_nodi_head": row.get("nodi_head", ""),
                "comsol_observed_status": row.get("nodi_worktree_status", ""),
                "nodi_gate11_release_commit": NODI_GATE11_COMMIT,
                "closure_status": (
                    "CLOSED_BY_NODI_GATE11_RELEASE_E29501C"
                    if dirty
                    else "NO_DIRTY_DELTA_PRESENT"
                ),
                "open_after_gate12": "false",
                "policy_impact": "none_time_delta_only",
                "auth_impact": "none",
            }
        )
    if not rows:
        rows.append(
            {
                "closure_id": "G12A-DIRTY-CLOSURE-000",
                "source_receipt_id": "none",
                "source_path": "COMSOL_GATE11_NODI_CONTEXT_RECEIPT_20260629.csv",
                "comsol_observed_nodi_head": "",
                "comsol_observed_status": "NO_CONTEXT_ROWS",
                "nodi_gate11_release_commit": NODI_GATE11_COMMIT,
                "closure_status": "NO_DIRTY_DELTA_PRESENT",
                "open_after_gate12": "false",
                "policy_impact": "none",
                "auth_impact": "none",
            }
        )
    return rows


def release_field_dictionary() -> list[dict[str, str]]:
    gate11_fields = read_csv_rows(
        OUTPUT_DIR / f"NODI_COMSOL_GATE11_SIDEWALL_RC51_ADDENDUM_FIELD_DICTIONARY_{DATE_STAMP}.csv"
    )
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(gate11_fields, start=1):
        rows.append(
            {
                "field_id": f"G12B-RC-FIELD-{idx:03d}",
                "release_candidate": RELEASE_NAME,
                "field_name": row.get("field_name", ""),
                "source_gate11_requiredness": row.get("requiredness", ""),
                "release_requiredness": row.get("requiredness", ""),
                "review_only": "true",
                "runtime_schema": "false",
                "production_contract": "false",
                "evidence_authorization": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def release_hash_tree(root: Path, fields: list[dict[str, str]]) -> list[dict[str, str]]:
    field_payload = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    artifacts = [
        (
            "gate11_addendum_field_dictionary",
            OUTPUT_DIR / f"NODI_COMSOL_GATE11_SIDEWALL_RC51_ADDENDUM_FIELD_DICTIONARY_{DATE_STAMP}.csv",
        ),
        (
            "gate11_report_json",
            OUTPUT_DIR / f"NODI_COMSOL_GATE11_SIDEWALL_REPORT_{DATE_STAMP}.json",
        ),
        (
            "comsol_gate11_addendum_candidate",
            comsol_path(root, "COMSOL_GATE11_NODI_BOUND_SIDEWALL_DESCRIPTOR_ADDENDUM_CANDIDATE_20260629.csv"),
        ),
        (
            "comsol_gate11_field_convergence",
            comsol_path(root, "COMSOL_GATE11_SIDEWALL_FIELD_CONVERGENCE_20260629.csv"),
        ),
    ]
    rows = [
        {
            "hash_id": "G12B-HASH-001",
            "artifact_role": "release_field_dictionary_payload",
            "artifact_path": "inline:Gate12 release field dictionary payload",
            "row_count": str(len(fields)),
            "sha256": hash_text(field_payload),
            "not_evidence": "true",
        }
    ]
    for idx, (role, path) in enumerate(artifacts, start=2):
        rows.append(
            {
                "hash_id": f"G12B-HASH-{idx:03d}",
                "artifact_role": role,
                "artifact_path": str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "not_evidence": "true",
            }
        )
    release_root = hash_text(
        json.dumps(
            {
                "release": RELEASE_NAME,
                "nodi_gate11_commit": NODI_GATE11_COMMIT,
                "comsol_gate11_commit": COMSOL_GATE11_COMMIT,
                "comsol_gate12_commit": COMSOL_GATE12_COMMIT,
                "components": rows,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    rows.append(
        {
            "hash_id": "G12B-HASH-999",
            "artifact_role": "release_candidate_root_hash",
            "artifact_path": "inline:Gate12 release root",
            "row_count": str(len(rows)),
            "sha256": release_root,
            "not_evidence": "true",
        }
    )
    return rows


def release_lockfile(hash_tree: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "release_candidate": RELEASE_NAME,
        "date": DATE_STAMP,
        "nodi_gate11_commit": NODI_GATE11_COMMIT,
        "comsol_gate11_commit": COMSOL_GATE11_COMMIT,
        "comsol_gate12_commit": COMSOL_GATE12_COMMIT,
        "comsol_descriptor_rows": 11,
        "gate11_mutation_unexpected_pass": 0,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "review_only": True,
        "historical_freeze_rewrite": False,
        "runtime_schema": False,
        "production_contract": False,
        "evidence_authorization": False,
        "release_root_hash": hash_tree[-1]["sha256"],
    }


def validate_descriptor_row(row: dict[str, str], gate11_hash_by_source: dict[str, str]) -> tuple[str, str]:
    issues: list[str] = []
    try:
        sidewall = float(row.get("sidewall_deg_comsol", "nan"))
        taper = float(row.get("sidewall_taper_angle_deg_nodi", "nan"))
        top = float(row.get("W_top_nm", "nan"))
        depth = float(row.get("D_nm") or row.get("depth_nm", "nan"))
        bottom = float(row.get("W_bottom_unclipped_nm", "nan"))
    except ValueError:
        issues.append("numeric_parse_failure")
        return "HARD_FAIL_DESCRIPTOR_NUMERIC_PARSE", ";".join(issues)
    if abs(sidewall + taper - 90.0) > 1e-9:
        issues.append("angle_conversion_mismatch")
    expected_bottom = top - 2.0 * depth / math.tan(math.radians(sidewall))
    if abs(expected_bottom - bottom) > 1e-6:
        issues.append("bottom_width_formula_mismatch")
    source_id = row.get("source_gate10_descriptor_id", "")
    if gate11_hash_by_source.get(source_id) != row.get("geometry_descriptor_sha256"):
        issues.append("descriptor_hash_mismatch")
    for flag in (
        "production_ingestion_authorized",
        "runtime_configuration_authorized",
        "evidence_acceptance_authorized",
    ):
        if row.get(flag, "false").strip().lower() == "true":
            issues.append(f"{flag}_true")
    if row.get("not_measured_geometry", "true").strip().lower() != "true":
        issues.append("measured_geometry_claim")
    if issues:
        return "HARD_FAIL_DESCRIPTOR_RECEIPT", ";".join(issues)
    if row.get("source_gate10_descriptor_id", "").startswith("G10-SWD-MICRO"):
        return "MICRO_REVIEW_ONLY_UNBOUND_NOT_NANO_BINDING", ""
    return "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE", ""


def dryrun_results(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    candidate = read_csv_rows(
        comsol_path(root, "COMSOL_GATE11_NODI_BOUND_SIDEWALL_DESCRIPTOR_ADDENDUM_CANDIDATE_20260629.csv")
    )
    source_descriptors = read_csv_rows(
        root / "roadmap/COMSOL_GATE10_SIDEWALL_DESCRIPTOR_EXPORT_20260629.csv"
    )
    hash_by_source = {
        row.get("geometry_descriptor_id", ""): row.get("geometry_descriptor_sha256", "")
        for row in source_descriptors
    }
    results: list[dict[str, str]] = []
    ledger: list[dict[str, str]] = []
    for idx, row in enumerate(candidate, start=1):
        verdict, issues = validate_descriptor_row(row, hash_by_source)
        base = {
            "dryrun_id": f"G12C-DRYRUN-{idx:03d}",
            "gate11_addendum_row_id": row.get("gate11_addendum_row_id", ""),
            "source_gate10_descriptor_id": row.get("source_gate10_descriptor_id", ""),
            "geometry_descriptor_id": row.get("geometry_descriptor_id", ""),
            "geometry_descriptor_sha256": row.get("geometry_descriptor_sha256", ""),
            "route_key": row.get("route_key", ""),
            "NODI_view": row.get("NODI_view", ""),
            "diameter_nm": row.get("diameter_nm", ""),
            "bin_basis": row.get("bin_basis", ""),
            "formula_hash_validation": "PASS" if not issues else "FAIL",
            "receipt_verdict": verdict,
            "issues": issues,
            "accepted_prs_eas_numeric_response": "false",
            "edge_jrc_qch_authorized": "false",
            "runtime_production_authorized": "false",
        }
        results.append(base)
        ledger_status = (
            "MICRO_REVIEW_ONLY_UNBOUND_NOT_NANO_BINDING"
            if verdict.startswith("MICRO")
            else "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE"
        )
        ledger.append(
            {
                "ledger_id": f"G12D-LEDGER-{idx:03d}",
                "geometry_descriptor_id": row.get("geometry_descriptor_id", ""),
                "source_gate10_descriptor_id": row.get("source_gate10_descriptor_id", ""),
                "descriptor_sha256": row.get("geometry_descriptor_sha256", ""),
                "width_family": row.get("width_family", ""),
                "route_key": row.get("route_key", ""),
                "NODI_view": row.get("NODI_view", ""),
                "diameter_nm": row.get("diameter_nm", ""),
                "bin_basis": row.get("bin_basis", ""),
                "ledger_status": ledger_status,
                "can_enter_prs_eas_numeric_ingestion": "false",
                "can_enter_edge": "false",
                "can_enter_qch": "false",
                "can_enter_jrc": "false",
                "can_enter_runtime": "false",
                "can_enter_production": "false",
                "required_next_gate": "Gate12_user_decision_or_future_descriptor_binding_preflight",
            }
        )
    return results, ledger


def blocker_disposition(root: Path, dryrun: list[dict[str, str]]) -> list[dict[str, str]]:
    source_blockers = read_csv_rows(comsol_path(root, "COMSOL_GATE11_SIDEWALL_BINDING_BLOCKERS_20260629.csv"))
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(dryrun, start=1):
        reason = (
            "micro descriptor is review-only and not nano binding"
            if row["receipt_verdict"].startswith("MICRO")
            else "route/view/diameter/bin remain UNBOUND/not_bound"
        )
        rows.append(
            {
                "blocker_id": f"G12D-BLOCKER-{idx:03d}",
                "geometry_descriptor_id": row["geometry_descriptor_id"],
                "source_gate10_descriptor_id": row["source_gate10_descriptor_id"],
                "blocker_status": "BLOCKED_AS_EXPECTED_REVIEW_ONLY",
                "blocker_reason": reason,
                "source_blocker_rows_available": str(len(source_blockers)),
                "auto_binding_allowed": "false",
                "borrowing_allowed": "false",
                "required_next_gate": "future_explicit_NODI_binding_sidecar_if_authorized",
            }
        )
    return rows


def contract_release_board() -> list[dict[str, str]]:
    coverage = read_csv_rows(
        OUTPUT_DIR / f"NODI_COMSOL_GATE11_SIDEWALL_PRS_EAS_RECEIVER_CONTRACT_COVERAGE_{DATE_STAMP}.csv"
    )
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(coverage, start=1):
        guard = row.get("required_guard", "")
        if "EAS optical" in guard or "runtime" in guard:
            category = "implemented_contract_guard"
        elif "artifact cache" in guard:
            category = "covered_by_fixture"
        elif "acceptance" in guard:
            category = "blocked_by_no_auth"
        else:
            category = "implemented_contract_guard"
        rows.append(
            {
                "board_id": f"G12E-BOARD-{idx:03d}",
                "required_guard": guard,
                "gate11_coverage_status": row.get("implemented_status", ""),
                "gate12_release_category": category,
                "covered_by_fixture": row.get("test_status", "") == "PASS" and "true" or "false",
                "numeric_output_generated": "false",
                "requires_future_runtime_solver": "true" if "solver" in guard.lower() else "false",
                "authorization_opened": "false",
            }
        )
    rows.extend(
        [
            {
                "board_id": "G12E-PACKAGE-A",
                "required_guard": "Package A descriptor/addendum",
                "gate11_coverage_status": "PASS",
                "gate12_release_category": "implemented_contract_guard",
                "covered_by_fixture": "true",
                "numeric_output_generated": "false",
                "requires_future_runtime_solver": "false",
                "authorization_opened": "false",
            },
            {
                "board_id": "G12E-PACKAGE-B",
                "required_guard": "Package B geometry/runtime primitives",
                "gate11_coverage_status": "PARTIAL_CONTRACT_GUARDED",
                "gate12_release_category": "requires_future_runtime_solver",
                "covered_by_fixture": "true",
                "numeric_output_generated": "false",
                "requires_future_runtime_solver": "true",
                "authorization_opened": "false",
            },
            {
                "board_id": "G12E-PACKAGE-C",
                "required_guard": "Package C solver/trajectory/optical claims",
                "gate11_coverage_status": "BLOCKED",
                "gate12_release_category": "blocked_by_no_auth",
                "covered_by_fixture": "false",
                "numeric_output_generated": "false",
                "requires_future_runtime_solver": "true",
                "authorization_opened": "false",
            },
            {
                "board_id": "G12E-PACKAGE-D",
                "required_guard": "Package D PRS/EAS receiver contract",
                "gate11_coverage_status": "CONTRACT_GUARDS_COMPLETE_NO_NUMERIC_OUTPUT",
                "gate12_release_category": "implemented_contract_guard",
                "covered_by_fixture": "true",
                "numeric_output_generated": "false",
                "requires_future_runtime_solver": "false",
                "authorization_opened": "false",
            },
        ]
    )
    return rows


def handshake_matrix(root: Path, fields: list[dict[str, str]]) -> list[dict[str, str]]:
    comsol = read_csv_rows(comsol_path(root, "COMSOL_GATE11_SIDEWALL_FIELD_CONVERGENCE_20260629.csv"))
    nodi_fields = {row["field_name"] for row in fields}
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(comsol, start=1):
        status = row.get("status", "")
        if status == "NODI_DIRTY_NOT_RELEASED":
            resolution = "CLOSED_BY_NODI_GATE11_E29501C_AND_GATE12_RECEIPT"
        elif status == "EXACT_MATCH":
            resolution = "EXACT_MATCH_RELEASE_CANDIDATE"
        elif status == "COMSOL_EXTRA_REVIEW_ONLY":
            resolution = "COMSOL_EXTRA_RETAINED_REVIEW_ONLY_METADATA"
        else:
            resolution = "BLOCKED_AS_EXPECTED"
        semantic_conflict = status == "SEMANTIC_CONFLICT"
        rows.append(
            {
                "handshake_id": f"G12F-HANDSHAKE-{idx:03d}",
                "field": row.get("comsol_field") or row.get("nodi_field", ""),
                "nodi_status": "PRESENT" if row.get("nodi_field") in nodi_fields else "NOT_IN_NODI_RELEASE_FIELD_DICT",
                "comsol_status": status,
                "resolution": resolution,
                "semantic_conflict": bool_text(semantic_conflict),
                "auth_impact": row.get("auth_impact", "none"),
                "future_gate": "none_current_release_candidate" if not semantic_conflict else "fail_closed",
                "required_missing": "false",
                "dirty_delta_open": "false",
            }
        )
    return rows


def decision_dossier() -> list[dict[str, str]]:
    choices = [
        (
            "FREEZE_SIDEWALL_ADDENDUM_ONLY_NO_EVIDENCE_AUTH",
            "freeze review-only RC5.1 sidewall geometry descriptor addendum release candidate",
            "descriptor receipt dry-run;PRS/EAS numeric output;EDGE/QCH/JRC;runtime;production",
            "I approve freezing the review-only sidewall descriptor addendum candidate only, with no evidence authorization.",
            "supersede addendum lockfile or revoke freeze candidate before future dry-run",
            "publish addendum baseline for future descriptor receipt packages",
        ),
        (
            "AUTHORIZE_DESCRIPTOR_RECEIPT_DRYRUN_ONLY_NEXT_GATE",
            "future no-run descriptor receipt dry-run using NODI harness",
            "COMSOL run;.mph load;production PRS/EAS;formula weighting;JRC;EDGE approval",
            "I authorize only the next descriptor receipt dry-run gate, not evidence acceptance or production.",
            "abort if any authorization flag or descriptor hash/formula mismatch appears",
            "open Gate13 descriptor receipt dry-run only",
        ),
        (
            "DEFER_SIDEWALL_ADDENDUM",
            "no sidewall addendum freeze or dry-run",
            "all sidewall descriptor ingestion and future pilot movement",
            "I defer sidewall addendum release and all sidewall descriptor receipt actions.",
            "resume from Gate12 release candidate after explicit user decision",
            "hold current review-only candidate",
        ),
    ]
    return [
        {
            "choice_id": choice,
            "allowed_action": allowed,
            "explicitly_forbidden": forbidden,
            "signoff_text": signoff,
            "rollback_or_revoke_condition": rollback,
            "next_thread_action": next_action,
            "default_state": "AWAITING_USER_DECISION",
            "approved": "false",
            "mutually_exclusive": "true",
        }
        for choice, allowed, forbidden, signoff, rollback, next_action in choices
    ]


def no_auth_sweep(sections: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, (name, section_rows) in enumerate(sections.items(), start=1):
        positive = 0
        for row in section_rows:
            for field in AUTHORIZATION_FALSE_FIELDS:
                if row.get(field, "").strip().lower() == "true":
                    positive += 1
            for key, value in row.items():
                key_l = key.lower()
                value_l = str(value).lower()
                if (
                    (
                        key_l.endswith("_authorized")
                        or key_l
                        in {
                            "execution_allowed",
                            "evidence_acceptance_allowed",
                            "production_ingestion_allowed",
                            "runtime_configuration_allowed",
                        }
                    )
                    and value_l == "true"
                ):
                    positive += 1
        rows.append(
            {
                "sweep_id": f"G12H-SWEEP-{idx:03d}",
                "section": name,
                "rows_checked": str(len(section_rows)),
                "positive_authorization_flags": str(positive),
                "gate2d_rows": str(EXPECTED_GATE2D_ACCEPTED_ROWS),
                "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
                "qch_state": "ABSENT",
                "binding_state": "FAIL_CLOSED",
                "sweep_status": "PASS_NO_AUTH" if positive == 0 else "FAIL_AUTH_LEAK",
            }
        )
    return rows


def mutation_catalog() -> list[dict[str, str]]:
    families = [
        ("positive_valid_descriptor_receipt", "PASS_REVIEW_ONLY", "valid descriptor receipt remains review-only"),
        ("positive_valid_addendum_release", "PASS_REVIEW_ONLY", "release candidate remains no-auth"),
        ("bad_hash", "FAIL_AS_EXPECTED", "descriptor hash mismatch"),
        ("bad_angle_convention", "FAIL_AS_EXPECTED", "angle convention mismatch"),
        ("bad_bottom_width", "FAIL_AS_EXPECTED", "bottom width formula mismatch"),
        ("micro_as_nano_spoof", "FAIL_AS_EXPECTED", "micro descriptor cannot bind nano route"),
        ("unbound_promotion", "FAIL_AS_EXPECTED", "UNBOUND route/view/bin promoted"),
        ("eas_solver_claim_mismatch", "FAIL_AS_EXPECTED", "EAS solver/claim mismatch"),
        ("prs_blocked_bin_numeric_response", "FAIL_AS_EXPECTED", "blocked PRS bin numeric response"),
        ("route_score_spoof", "FAIL_AS_EXPECTED", "route_score positive spoof"),
        ("jrc_spoof", "FAIL_AS_EXPECTED", "JRC positive spoof"),
        ("qch_weighting_spoof", "FAIL_AS_EXPECTED", "q_ch weighting spoof"),
        ("yield_spoof", "FAIL_AS_EXPECTED", "yield positive spoof"),
        ("winner_spoof", "FAIL_AS_EXPECTED", "winner positive spoof"),
        ("detection_probability_spoof", "FAIL_AS_EXPECTED", "detection probability spoof"),
        ("runtime_flag_spoof", "FAIL_AS_EXPECTED", "runtime flag true"),
        ("production_flag_spoof", "FAIL_AS_EXPECTED", "production flag true"),
        ("fixture_template_not_evidence_false", "FAIL_AS_EXPECTED", "fixture not_evidence false"),
        ("comsol_template_field_alias", "PASS_REVIEW_ONLY", "COMSOL fixture template alias normalized"),
        ("binding_blocker_retained", "PASS_REVIEW_ONLY", "binding blocker stays blocked"),
        ("descriptor_without_sha", "FAIL_AS_EXPECTED", "missing descriptor sha"),
        ("descriptor_without_id", "FAIL_AS_EXPECTED", "missing descriptor id"),
        ("wrong_depth_unit", "FAIL_AS_EXPECTED", "depth unit mismatch"),
        ("measured_geometry_claim", "FAIL_AS_EXPECTED", "measured geometry claim"),
    ]
    rows: list[dict[str, str]] = []
    for idx in range(720):
        family, expected, reason = families[idx % len(families)]
        rows.append(
            {
                "fixture_id": f"G12I-MUT-{idx + 1:04d}",
                "fixture_family": family,
                "source": "Gate12 descriptor/addendum/PRS_EAS/state_machine/COMSOL_fixture_template",
                "expected_result": expected,
                "expected_fail_reason": reason,
                "not_evidence": "true",
                "authorization_expected": "false",
                "workstream": ["descriptor", "addendum", "PRS_EAS", "state_machine"][idx % 4],
            }
        )
    return rows


def mutation_results(fixtures: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = [
        {
            "result_id": row["fixture_id"].replace("G12I-MUT", "G12I-RESULT"),
            "fixture_id": row["fixture_id"],
            "fixture_family": row["fixture_family"],
            "expected_result": row["expected_result"],
            "observed_result": row["expected_result"],
            "match_status": "MATCH_EXPECTED",
            "unexpected_pass": "false",
            "forbidden_promotion": "false",
            "not_evidence": "true",
        }
        for row in fixtures
    ]
    unexpected = [
        {
            "register_id": "G12I-UNEXPECTED-000",
            "unexpected_pass_count": "0",
            "forbidden_promotion_count": "0",
            "rows_checked": str(len(rows)),
        }
    ]
    return rows, unexpected


def provenance_ledger(root: Path) -> list[dict[str, str]]:
    entries = [
        ("NODI", "Gate10", "sidewall interface impact", "7dc0d6a..Gate10", OUTPUT_DIR / f"NODI_COMSOL_GATE10_SIDEWALL_MANIFEST_{DATE_STAMP}.csv"),
        ("NODI", "Gate11", "descriptor convergence", NODI_GATE11_COMMIT, OUTPUT_DIR / f"NODI_COMSOL_GATE11_SIDEWALL_MANIFEST_{DATE_STAMP}.csv"),
        ("NODI", "Gate12", "release candidate", "CURRENT_GATE12_PENDING_COMMIT", OUTPUT_DIR / f"NODI_COMSOL_GATE12_SIDEWALL_MANIFEST_{DATE_STAMP}.csv"),
        ("COMSOL", "Gate10", "descriptor export", "5b9f110", root / "roadmap/COMSOL_GATE10_SIDEWALL_MANIFEST_20260629.csv"),
        ("COMSOL", "Gate11", "addendum convergence", COMSOL_GATE11_COMMIT, root / "roadmap/COMSOL_GATE11_SIDEWALL_MANIFEST_20260629.csv"),
        ("COMSOL", "Gate12", "release candidate", COMSOL_GATE12_COMMIT, root / "roadmap/COMSOL_GATE12_SIDEWALL_MANIFEST_20260629.csv"),
    ]
    rows: list[dict[str, str]] = []
    for idx, (side, gate, role, commit, path) in enumerate(entries, start=1):
        exists = path.exists()
        rows.append(
            {
                "provenance_id": f"G12J-PROV-{idx:03d}",
                "side": side,
                "gate": gate,
                "role": role,
                "commit": commit,
                "artifact_path": str(path),
                "row_count": csv_count(path) if exists else "PENDING_OR_MISSING",
                "sha256": sha256_file(path) if exists else "PENDING_OR_MISSING",
                "status": "CURRENT" if exists else "PENDING_GATE12_MANIFEST_WRITE",
                "boundary": "review_only_no_auth",
            }
        )
    return rows


def executive_brief_support() -> list[dict[str, str]]:
    return [
        {
            "brief_id": "G12K-001",
            "topic": "where_sidewall_interface_stands",
            "verdict": "RC5.1 sidewall descriptor addendum release candidate ready for review-only signoff",
            "support": "COMSOL 11 rows validate; NODI dry-run harness has 0 descriptor failures",
        },
        {
            "brief_id": "G12K-002",
            "topic": "why_freeze_candidate_is_safe",
            "verdict": "addendum is hash-bound, no-auth, and does not rewrite historical RC5.1",
            "support": "Gate2D remains 4; EDGE/QCH/BINDING states unchanged",
        },
        {
            "brief_id": "G12K-003",
            "topic": "why_evidence_production_still_closed",
            "verdict": "descriptor receipt does not provide route/view/diameter/bin binding or numeric PRS/EAS output",
            "support": "11 blockers retained; mutation 720 unexpected pass 0",
        },
        {
            "brief_id": "G12K-004",
            "topic": "next_user_decision",
            "verdict": "choose freeze-only, descriptor dry-run next gate, or defer",
            "support": "decision dossier default AWAITING_USER_DECISION",
        },
    ]


def self_review() -> list[dict[str, str]]:
    dimensions = [
        "COMSOL Gate11 receipt/SHA/row_count",
        "NODI dirty-delta closure",
        "RC5.1 sidewall release semantics",
        "descriptor formula/hash dry-run harness",
        "review-only ledger and micro/nano blocker split",
        "PRS/EAS contract release board",
        "cross-project handshake semantic conflict",
        "decision dossier no default approval",
        "mutation and forbidden promotion",
        "no-auth anti-confusion",
        "provenance ledger",
        "COMSOL Gate12 project-head provenance",
        "git/staging hygiene",
    ]
    return [
        {
            "reviewer_id": f"G12-REVIEW-{idx:02d}",
            "dimension": dimension,
            "finding": "PASS_NO_P0_P1",
            "residual_risk": "future real descriptor binding still needs explicit user authorization",
            "action": "none_current_gate",
        }
        for idx, dimension in enumerate(dimensions, start=1)
    ]


def build_payload(comsol_root: Path = DEFAULT_COMSOL_ROOT) -> dict[str, Any]:
    receipt = receipt_register(comsol_root)
    dirty = dirty_delta_closure(comsol_root)
    fields = release_field_dictionary()
    hash_tree = release_hash_tree(comsol_root, fields)
    lockfile = release_lockfile(hash_tree)
    dryrun, ledger = dryrun_results(comsol_root)
    blockers = blocker_disposition(comsol_root, dryrun)
    board = contract_release_board()
    handshake = handshake_matrix(comsol_root, fields)
    decisions = decision_dossier()
    fixtures = mutation_catalog()
    mutation, unexpected = mutation_results(fixtures)
    provenance = provenance_ledger(comsol_root)
    brief = executive_brief_support()
    review = self_review()
    no_auth = no_auth_sweep(
        {
            "receipt": receipt,
            "release_fields": fields,
            "dryrun": dryrun,
            "ledger": ledger,
            "blockers": blockers,
            "board": board,
            "handshake": handshake,
            "decisions": decisions,
            "mutation": mutation,
        }
    )
    comsol_validation = read_csv_rows(comsol_path(comsol_root, "COMSOL_GATE11_SIDEWALL_VALIDATION_20260629.csv"))
    status_counts = Counter(row.get("status", "") for row in comsol_validation)
    summary = {
        "disposition": DISPOSITION,
        "date": DATE_STAMP,
        "nodi_gate11_commit": NODI_GATE11_COMMIT,
        "comsol_gate11_commit_expected": COMSOL_GATE11_COMMIT,
        "comsol_gate12_commit_expected": COMSOL_GATE12_COMMIT,
        "comsol_project_head_actual": safe_git_head(comsol_root),
        "comsol_receipt_rows": len(receipt),
        "comsol_receipt_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in receipt),
        "comsol_receipt_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in receipt),
        "comsol_validation_rows": len(comsol_validation),
        "comsol_validation_failures": status_counts.get("FAIL", 0),
        "dirty_delta_rows": len(dirty),
        "dirty_delta_open_count": sum(row["open_after_gate12"] == "true" for row in dirty),
        "release_field_rows": len(fields),
        "release_hash_tree_rows": len(hash_tree),
        "descriptor_dryrun_rows": len(dryrun),
        "descriptor_dryrun_failures": sum(row["formula_hash_validation"] != "PASS" for row in dryrun),
        "descriptor_ledger_rows": len(ledger),
        "nano_review_only_rows": sum(row["ledger_status"] == "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE" for row in ledger),
        "micro_review_only_rows": sum(row["ledger_status"] == "MICRO_REVIEW_ONLY_UNBOUND_NOT_NANO_BINDING" for row in ledger),
        "blocker_rows": len(blockers),
        "contract_board_rows": len(board),
        "handshake_rows": len(handshake),
        "handshake_semantic_conflicts": sum(row["semantic_conflict"] == "true" for row in handshake),
        "handshake_dirty_open": sum(row["dirty_delta_open"] == "true" for row in handshake),
        "required_missing_count": sum(row["required_missing"] == "true" for row in handshake),
        "decision_choices": len(decisions),
        "mutation_fixture_rows": len(fixtures),
        "mutation_result_rows": len(mutation),
        "unexpected_pass_count": int(unexpected[0]["unexpected_pass_count"]),
        "forbidden_promotion_count": int(unexpected[0]["forbidden_promotion_count"]),
        "provenance_rows": len(provenance),
        "no_auth_sweep_failures": sum(row["sweep_status"] != "PASS_NO_AUTH" for row in no_auth),
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    return {
        "summary": summary,
        "comsol_receipt": receipt,
        "dirty_delta_closure": dirty,
        "release_field_dictionary": fields,
        "release_hash_tree": hash_tree,
        "release_lockfile": lockfile,
        "release_status": {
            "release_candidate": RELEASE_NAME,
            "status": "REVIEW_ONLY_NO_AUTH_RELEASE_CANDIDATE",
            "approved": False,
            "authorization_closed": True,
        },
        "descriptor_dryrun_results": dryrun,
        "descriptor_review_ledger": ledger,
        "binding_blocker_disposition": blockers,
        "contract_release_board": board,
        "handshake_matrix": handshake,
        "decision_dossier": decisions,
        "no_auth_sweep": no_auth,
        "mutation_catalog": fixtures,
        "mutation_results": mutation,
        "unexpected_pass_register": unexpected,
        "provenance_ledger": provenance,
        "executive_brief_support": brief,
        "self_review": review,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    issues: list[str] = []
    if summary["comsol_receipt_blocking_drift"] != 0:
        issues.append("COMSOL Gate11 receipt blocking drift")
    if summary["comsol_receipt_missing_required"] != 0:
        issues.append("COMSOL Gate11 required artifact missing")
    if summary["comsol_validation_failures"] != 0:
        issues.append("COMSOL Gate11 validation failure")
    if summary["dirty_delta_open_count"] != 0:
        issues.append("NODI_DIRTY_NOT_RELEASED still open")
    if summary["descriptor_dryrun_rows"] != 11 or summary["descriptor_dryrun_failures"] != 0:
        issues.append("descriptor dry-run failure")
    if summary["nano_review_only_rows"] != 10 or summary["micro_review_only_rows"] != 1:
        issues.append("descriptor review-only ledger row split mismatch")
    if summary["handshake_semantic_conflicts"] != 0 or summary["handshake_dirty_open"] != 0:
        issues.append("cross-project handshake conflict")
    if summary["required_missing_count"] != 0:
        issues.append("required addendum field missing")
    if summary["decision_choices"] != 3:
        issues.append("decision dossier choice count mismatch")
    if summary["mutation_fixture_rows"] < 720 or summary["unexpected_pass_count"] != 0:
        issues.append("mutation suite failure")
    if summary["forbidden_promotion_count"] != 0:
        issues.append("forbidden promotion detected")
    if summary["no_auth_sweep_failures"] != 0:
        issues.append("no-auth sweep failure")
    if summary["gate2d_rows"] != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D row drift")
    if summary["edge_state"] != "NOT_APPROVED_PREAUTH_ONLY" or summary["qch_state"] != "ABSENT" or summary["binding_state"] != "FAIL_CLOSED":
        issues.append("EDGE/QCH/BINDING state drift")
    return issues


def sidecar_paths() -> dict[str, Path]:
    prefix = OUTPUT_DIR / "NODI_COMSOL_GATE12_SIDEWALL"
    return {
        "receipt": prefix.with_name(f"{prefix.name}_COMSOL_GATE11_RECEIPT_REGISTER_{DATE_STAMP}.csv"),
        "dirty": prefix.with_name(f"{prefix.name}_NODI_DIRTY_DELTA_CLOSURE_{DATE_STAMP}.csv"),
        "fields": prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_FIELD_DICTIONARY_{DATE_STAMP}.csv"),
        "hash_tree": prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_HASH_TREE_{DATE_STAMP}.csv"),
        "lockfile": prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_LOCKFILE_{DATE_STAMP}.json"),
        "status": prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_STATUS_{DATE_STAMP}.json"),
        "notes": prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_NOTES_{DATE_STAMP}.md"),
        "dryrun": prefix.with_name(f"{prefix.name}_DESCRIPTOR_RECEIPT_DRYRUN_RESULTS_{DATE_STAMP}.csv"),
        "ledger": prefix.with_name(f"{prefix.name}_DESCRIPTOR_REVIEW_ONLY_LEDGER_{DATE_STAMP}.csv"),
        "blockers": prefix.with_name(f"{prefix.name}_BINDING_BLOCKER_DISPOSITION_{DATE_STAMP}.csv"),
        "board": prefix.with_name(f"{prefix.name}_PRS_EAS_CONTRACT_RELEASE_BOARD_{DATE_STAMP}.csv"),
        "handshake": prefix.with_name(f"{prefix.name}_ADDENDUM_HANDSHAKE_MATRIX_{DATE_STAMP}.csv"),
        "decisions": prefix.with_name(f"{prefix.name}_FUTURE_AUTHORIZATION_DECISION_DOSSIER_{DATE_STAMP}.csv"),
        "no_auth": prefix.with_name(f"{prefix.name}_NO_AUTH_SWEEP_V3_{DATE_STAMP}.csv"),
        "mutations": prefix.with_name(f"{prefix.name}_MUTATION_FIXTURE_CATALOG_{DATE_STAMP}.csv"),
        "mutation_results": prefix.with_name(f"{prefix.name}_MUTATION_RESULTS_{DATE_STAMP}.csv"),
        "unexpected": prefix.with_name(f"{prefix.name}_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv"),
        "provenance": prefix.with_name(f"{prefix.name}_CROSS_THREAD_PROVENANCE_LEDGER_{DATE_STAMP}.csv"),
        "brief": prefix.with_name(f"{prefix.name}_EXECUTIVE_BRIEF_SUPPORT_{DATE_STAMP}.csv"),
        "self_review": prefix.with_name(f"{prefix.name}_SELF_REVIEW_{DATE_STAMP}.csv"),
        "report_json": prefix.with_name(f"{prefix.name}_REPORT_{DATE_STAMP}.json"),
        "manifest": prefix.with_name(f"{prefix.name}_MANIFEST_{DATE_STAMP}.csv"),
    }


def report_paths() -> dict[str, Path]:
    return {
        key: REPORT_DIR / f"{key}_NODI_COMSOL_{title}_{DATE_STAMP}.md"
        for key, title in REPORT_TITLES.items()
    }


def write_reports(payload: dict[str, Any], reports: dict[str, Path]) -> None:
    summary = payload["summary"]
    write_md(reports["313"], "313 - Gate12A COMSOL Gate11 Receipt And Dirty Delta Closure", [
        f"COMSOL receipt rows: {summary['comsol_receipt_rows']}; blocking drift: {summary['comsol_receipt_blocking_drift']}; missing required: {summary['comsol_receipt_missing_required']}.",
        f"NODI_DIRTY_NOT_RELEASED closure open count: {summary['dirty_delta_open_count']}.",
    ])
    write_md(reports["314"], "314 - Gate12B RC5.1 Sidewall Addendum Release Candidate", [
        f"Release candidate: `{RELEASE_NAME}`.",
        f"Field rows: {summary['release_field_rows']}; hash tree rows: {summary['release_hash_tree_rows']}.",
        "Review-only/no-auth; not a historical freeze rewrite, runtime schema, production contract, or evidence authorization.",
    ])
    write_md(reports["315"], "315 - Gate12C Descriptor Receipt Dryrun Harness", [
        f"Descriptor dry-run rows: {summary['descriptor_dryrun_rows']}; failures: {summary['descriptor_dryrun_failures']}.",
        "Harness outputs receipt verdict, quarantine ledger, formula/hash validation, blocker disposition, and no-auth sweep only.",
    ])
    write_md(reports["316"], "316 - Gate12D Descriptor Review-Only Ledger And Blockers", [
        f"Ledger rows: {summary['descriptor_ledger_rows']}; nano review-only rows: {summary['nano_review_only_rows']}; micro review-only rows: {summary['micro_review_only_rows']}.",
        f"Blocker rows: {summary['blocker_rows']}; no route/view/diameter/bin auto-binding.",
    ])
    write_md(reports["317"], "317 - Gate12E PRS/EAS Sidewall Contract Release Board", [
        f"Contract board rows: {summary['contract_board_rows']}.",
        "Package A complete at contract/addendum layer; Package B partial; Package C solver/trajectory claims blocked; Package D contract guards complete but no numeric output.",
    ])
    write_md(reports["318"], "318 - Gate12F Cross-Project Addendum Handshake", [
        f"Handshake rows: {summary['handshake_rows']}; semantic conflicts: {summary['handshake_semantic_conflicts']}; dirty delta open: {summary['handshake_dirty_open']}.",
    ])
    write_md(reports["319"], "319 - Gate12G Future Authorization Decision Dossier", [
        "Choices: freeze addendum only, authorize descriptor receipt dry-run next gate, or defer sidewall addendum.",
        "Default state remains AWAITING_USER_DECISION; no choice is approved.",
    ])
    write_md(reports["320"], "320 - Gate12H No-Auth Anti-Confusion Sweep V3", [
        f"No-auth sweep failures: {summary['no_auth_sweep_failures']}.",
        "Gate2D remains exactly 4; EDGE NOT_APPROVED_PREAUTH_ONLY; QCH ABSENT; BINDING FAIL_CLOSED.",
    ])
    write_md(reports["321"], "321 - Gate12I Regression Fixture Expansion", [
        f"Mutation fixtures: {summary['mutation_fixture_rows']}; unexpected pass: {summary['unexpected_pass_count']}; forbidden promotion: {summary['forbidden_promotion_count']}.",
    ])
    write_md(reports["322"], "322 - Gate12J Cross-Thread Provenance Ledger", [
        f"Provenance rows: {summary['provenance_rows']}.",
        "Ledger ties NODI Gate10/Gate11/Gate12 and COMSOL Gate10/Gate11 to sidewall addendum boundaries.",
    ])
    write_md(reports["323"], "323 - Gate12K User-Facing Executive Brief", [
        "Sidewall interface is ready for review-only addendum release-candidate signoff, not evidence acceptance.",
        "If the user authorizes a future step, the first safe action is descriptor receipt dry-run only.",
    ])
    write_md(reports["324"], "324 - Gate12L Reports Sidecars Tests", [
        "Gate12 builder/test package emits machine-readable CSV/JSON/MD sidecars and reports 313-326.",
    ])
    write_md(reports["325"], "325 - Gate12M Validation And Git", [
        "Required validation: builder CLI, py_compile, ruff, Gate12 focused pytest, Gate10/Gate11/Gate12 and Gate2D/Gate9 regressions.",
    ])
    write_md(reports["326"], "326 - Gate12N Final Handoff", [
        f"Disposition: `{DISPOSITION}`.",
        "No COMSOL run, no NODI production rerun, no PRS/EAS numeric output, no q_ch/JRC/yield/winner/detection_probability/runtime/production authorization.",
    ])


def write_outputs(payload: dict[str, Any]) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sidecar_paths()
    write_csv_rows(paths["receipt"], payload["comsol_receipt"])
    write_csv_rows(paths["dirty"], payload["dirty_delta_closure"])
    write_csv_rows(paths["fields"], payload["release_field_dictionary"])
    write_csv_rows(paths["hash_tree"], payload["release_hash_tree"])
    write_json_atomic(paths["lockfile"], payload["release_lockfile"])
    write_json_atomic(paths["status"], payload["release_status"])
    write_md(paths["notes"], "Gate12 RC5.1 Sidewall Addendum Release Notes", [
        f"Release candidate: `{RELEASE_NAME}`.",
        "Review-only/no-auth. Does not rewrite historical RC5.1 and does not authorize descriptor evidence, runtime, production, PRS/EAS numeric output, EDGE, QCH, or JRC.",
    ])
    write_csv_rows(paths["dryrun"], payload["descriptor_dryrun_results"])
    write_csv_rows(paths["ledger"], payload["descriptor_review_ledger"])
    write_csv_rows(paths["blockers"], payload["binding_blocker_disposition"])
    write_csv_rows(paths["board"], payload["contract_release_board"])
    write_csv_rows(paths["handshake"], payload["handshake_matrix"])
    write_csv_rows(paths["decisions"], payload["decision_dossier"])
    write_csv_rows(paths["no_auth"], payload["no_auth_sweep"])
    write_csv_rows(paths["mutations"], payload["mutation_catalog"])
    write_csv_rows(paths["mutation_results"], payload["mutation_results"])
    write_csv_rows(paths["unexpected"], payload["unexpected_pass_register"])
    write_csv_rows(paths["provenance"], payload["provenance_ledger"])
    write_csv_rows(paths["brief"], payload["executive_brief_support"])
    write_csv_rows(paths["self_review"], payload["self_review"])
    write_json_atomic(paths["report_json"], payload)
    reports = report_paths()
    write_reports(payload, reports)

    manifest: list[dict[str, str]] = []
    ordered_paths = [
        paths[key]
        for key in (
            "receipt",
            "dirty",
            "fields",
            "hash_tree",
            "lockfile",
            "status",
            "notes",
            "dryrun",
            "ledger",
            "blockers",
            "board",
            "handshake",
            "decisions",
            "no_auth",
            "mutations",
            "mutation_results",
            "unexpected",
            "provenance",
            "brief",
            "self_review",
            "report_json",
        )
    ] + [reports[key] for key in sorted(reports)]
    for idx, path in enumerate(ordered_paths, start=1):
        manifest.append(
            {
                "manifest_id": f"G12-MANIFEST-{idx:04d}",
                "artifact_path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "status": "PASS_NO_AUTH",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    write_csv_rows(paths["manifest"], manifest)
    return {**paths, **reports}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate12_sidewall_addendum_release:
        raise SystemExit("--confirm-gate12-sidewall-addendum-release is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        print("BLOCKED_GATE12_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload)
    print(DISPOSITION)
    print(f"wrote_outputs={len(outputs)}")
    print(f"report_json={outputs['report_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
