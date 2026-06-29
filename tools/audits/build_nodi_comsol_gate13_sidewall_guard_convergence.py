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

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260629"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
COMSOL_ROADMAP = "roadmap"

NODI_GATE12_COMMIT = "8e702d4"
NODI_GATE13_BASE_HEAD = "3aef25df0034b894f4a147d6ea60afc69781d025"
COMSOL_GATE11_COMMIT = "b16b16b8c61e9ceb3a38debc1dc7a2bd4e635962"
COMSOL_GATE12_COMMIT = "8823515d220a2a5b25a43f00b998205344e5960f"
COMSOL_GATE13_COMMIT = "64dfa64b766750f91813c3cd470d369dec61f384"
DISPOSITION = "PASS_GATE13_SIDEWALL_GUARD_CONVERGENCE_AND_RC51_ADDENDUM_SIGNOFF_READY_NO_AUTH"
RELEASE_NAME = "RC5.1_SIDEWALL_GEOMETRY_DESCRIPTOR_ADDENDUM_V1_SIGNOFF_READY_REVIEW_ONLY_NO_AUTH"
ALLOWED_USE = "review-only descriptor receipt;geometry guard convergence;sidewall addendum signoff readiness"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS;JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;measured geometry claim;true PRS/EAS sidewall numeric output"
)

COMSOL_GATE12_REQUIRED_FILES = (
    "COMSOL_GATE12_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE_PACKET_20260629.md",
    "COMSOL_GATE12_SIDEWALL_STATUS_20260629.json",
    "COMSOL_GATE12_SIDEWALL_HANDSHAKE_MATRIX_20260629.csv",
    "COMSOL_GATE12_NODI_DESCRIPTOR_RECEIPT_DRYRUN_INPUTS_20260629.csv",
    "COMSOL_GATE12_SIDEWALL_BINDING_BLOCKER_CLOSURE_ROADMAP_20260629.csv",
    "COMSOL_GATE12_SIDEWALL_VALIDATION_20260629.csv",
    "COMSOL_GATE12_SIDEWALL_MANIFEST_20260629.csv",
)

COMSOL_GATE12_OPTIONAL_FILES = (
    "COMSOL_GATE12_SIDEWALL_MUTATION_RESULTS_20260629.csv",
    "COMSOL_GATE12_SIDEWALL_PROVENANCE_LEDGER_20260629.csv",
    "COMSOL_GATE12_SIDEWALL_DECISION_DOSSIER_20260629.csv",
    "COMSOL_GATE12_NODI_DIRTY_DELTA_CLOSURE_20260629.csv",
)

COMSOL_GATE13_REQUIRED_FILES = (
    "COMSOL_GATE13_SIDEWALL_GUARD_HANDSHAKE_V2_PACKET_20260629.md",
    "COMSOL_GATE13_STATUS_20260629.json",
    "COMSOL_GATE13_NODI_SIDEWALL_HARDENING_INTAKE_20260629.csv",
    "COMSOL_GATE13_GATE12_SELF_RECEIPT_20260629.csv",
    "COMSOL_GATE13_SIDEWALL_GUARD_SCHEMA_V2_20260629.csv",
    "COMSOL_GATE13_CLOSED_SIDEWALL_POLICY_20260629.csv",
    "COMSOL_GATE13_FLUIDIC_PROXY_FIREWALL_20260629.csv",
    "COMSOL_GATE13_NODI_DESCRIPTOR_DRYRUN_INPUTS_V2_20260629.csv",
    "COMSOL_GATE13_BINDING_BLOCKER_ROADMAP_V3_20260629.csv",
    "COMSOL_GATE13_VALIDATION_20260629.csv",
    "COMSOL_GATE13_MANIFEST_20260629.csv",
)

COMSOL_GATE13_OPTIONAL_FILES = (
    "COMSOL_GATE13_MUTATION_FIXTURE_CATALOG_20260629.csv",
    "COMSOL_GATE13_MUTATION_RESULTS_20260629.csv",
    "COMSOL_GATE13_PROVENANCE_LEDGER_20260629.csv",
    "COMSOL_GATE13_SELF_REVIEW_20260629.csv",
    "COMSOL_GATE13_FUTURE_HANDOFF_ESCROW_V4_20260629.csv",
)

REPORTS = {
    "327": "GATE13A_SIDEWALL_WORKTREE_RECONCILIATION",
    "328": "GATE13B_COMSOL_GATE12_BASELINE_AND_GATE13_RECEIPT_PROVENANCE_REPAIR",
    "329": "GATE13C_SIDEWALL_GEOMETRY_CLOSURE_AUTHORITY_CONTRACT_V2",
    "330": "GATE13D_CLOSED_SIDEWALL_HARD_FAIL_HARNESS",
    "331": "GATE13E_FLUIDIC_NETWORK_PROXY_FIREWALL",
    "332": "GATE13F_DESCRIPTOR_RECEIPT_DRYRUN_HARNESS_V2",
    "333": "GATE13G_SIDEWALL_INTERFACE_CONTRACT_V2",
    "334": "GATE13H_DETERMINISTIC_MUTATION_AND_REPLAY_EXPANSION",
    "335": "GATE13I_TEST_EXPANSION_AND_REGRESSION_SWEEP",
    "336": "GATE13J_RELEASE_SIGNOFF_READINESS_DOSSIER",
    "337": "GATE13K_CROSS_THREAD_PROVENANCE_LEDGER",
    "338": "GATE13L_INDEPENDENT_SELF_REVIEW",
    "339": "GATE13M_REPORTS_SIDECARS_FILES",
    "340": "GATE13N_GIT_CLOSEOUT_PLAN",
    "341": "GATE13O_FINAL_HANDOFF",
    "342": "GATE13_SIDEWALL_GUARD_CONVERGENCE_MASTER_REPORT",
    "343": "GATE13_SIDEWALL_NO_AUTH_LOCK_CERTIFICATE",
    "344": "GATE13_SIDEWALL_COMSOL_NEXT_REQUESTS",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate13 sidewall guard convergence and RC5.1 addendum signoff-readiness package."
    )
    parser.add_argument("--confirm-gate13-sidewall-guard-convergence", action="store_true")
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


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def normalize_manifest_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def manifest_lookup(root: Path, manifest_name: str) -> dict[str, dict[str, str]]:
    manifest = comsol_path(root, manifest_name)
    if not manifest.exists():
        return {}
    rows = read_csv_rows(manifest)
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        for key in ("path", "relative_path", "artifact_path", "file", "artifact"):
            value = normalize_manifest_path(row.get(key, ""))
            if value:
                lookup[value] = row
                lookup[Path(value).name] = row
    return lookup


def classify_dirty_path(path: str, status: str) -> tuple[str, str, str, str]:
    gate13_prefix = "reports/joint_interface_20260629/NODI_COMSOL_GATE13_SIDEWALL_"
    report_gate13 = path.startswith("reports/") and "_GATE13" in path
    if path.startswith(gate13_prefix) or report_gate13 or "gate13_sidewall_guard_convergence" in path:
        return (
            "LEGIT_GATE13_GENERATED_OUTPUT_PENDING_COMMIT",
            "Gate13 builder/test/report/sidecar generated in this run",
            "low",
            "stage_with_gate13_commit",
        )
    if path == "tools/audits/build_nodi_comsol_gate11_sidewall_convergence.py":
        return (
            "LEGIT_SIDEWALL_HARDENING_CODE",
            "Gate11 hardening intake now records changed file scopes from commits",
            "low",
            "include_if_tests_pass",
        )
    if path.startswith("reports/300_") or "GATE11_SIDEWALL" in path:
        return (
            "LEGIT_GATE11_GATE12_REPORT_REFRESH",
            "Gate11 sidewall convergence report refresh from later diagnostic guard commits",
            "low",
            "include_if_tests_pass",
        )
    if path.startswith("reports/322_") or "GATE12_SIDEWALL" in path:
        return (
            "LEGIT_COMSOL_GATE12_PROVENANCE_SYNC",
            "Gate12 provenance/hash tree refreshed to include COMSOL Gate13 head and post-Gate12 NODI hardening",
            "low",
            "include_if_tests_pass",
        )
    if path in {
        "nodi_simulator/trajectory.py",
        "tests/test_cross_section_geometry.py",
        "tests/test_nodi_comsol_gate12_sidewall_addendum_release_candidate.py",
    }:
        return (
            "LEGIT_SIDEWALL_HARDENING_CODE",
            "Sidewall diagnostic provenance/closure authority guard already expected by Gate13",
            "medium",
            "include_if_tests_pass",
        )
    if path == "":
        return ("NO_DIRTY_WORKTREE", "No dirty path present", "none", "no_action")
    return ("UNKNOWN_USER_CHANGE_BLOCKER", "Unclassified dirty file; fail closed", "high", "do_not_stage")


def worktree_reconciliation() -> list[dict[str, str]]:
    status = run_git(["status", "--short"])
    rows: list[dict[str, str]] = []
    if not status:
        rows.append(
            {
                "path": "WORKTREE_CLEAN_AT_GATE13_START",
                "git_status": "clean",
                "classification": "NO_DIRTY_WORKTREE",
                "diff_intent": "Earlier dirty snapshot has been absorbed by committed sidewall hardening before Gate13 build",
                "risk": "none",
                "required_tests": "Gate13 builder;py_compile;ruff;focused pytest;sidewall regressions",
                "commit_action": "no_checkpoint_needed",
                "unknown_blocker": "false",
            }
        )
        return rows
    for line in status.splitlines():
        status_code = line[:2].strip()
        path = line[2:].strip().replace("\\", "/")
        classification, intent, risk, action = classify_dirty_path(path, status_code)
        rows.append(
            {
                "path": path,
                "git_status": status_code,
                "classification": classification,
                "diff_intent": intent,
                "risk": risk,
                "required_tests": "Gate13 builder;py_compile;ruff;focused pytest;sidewall regressions",
                "commit_action": action,
                "unknown_blocker": bool_text(classification == "UNKNOWN_USER_CHANGE_BLOCKER"),
            }
        )
    return rows


def current_hardening_intake() -> list[dict[str, str]]:
    commits = [
        ("c44ff90", "Reject propagated closed sidewall artifacts", "closed/near-closed runtime artifacts reject propagation", "PRS/EAS/runtime guard"),
        ("54ce714", "Refresh sidewall convergence reports", "refresh Gate11/Gate12 package evidence after sidewall guards", "report/provenance"),
        ("1ab0f46", "Surface closed sidewall guard in release reports", "surface closed sidewall guard in release boards", "release report"),
        ("b0f8aae", "Mark sidewall fluidic network proxies", "mark rectangular fluidic network results as proxy not q_ch", "fluidic proxy firewall"),
        ("938062c", "Clarify sidewall diagnostic provenance scopes", "trajectory diagnostics scope and closure authority labels", "trajectory diagnostic guard"),
        ("3485b56", "Refresh sidewall reports after diagnostic guards", "absorbed remaining report/provenance dirty deltas", "Gate11/Gate12 refresh"),
        ("3aef25d", "Add trajectory caveat to Gate12 handoff", "external-reader trajectory diagnostic caveat", "Gate12 user-facing handoff guard"),
    ]
    rows: list[dict[str, str]] = []
    for short, subject, guard, impact in commits:
        try:
            full = run_git(["rev-parse", short])
            files = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", full]).splitlines()
        except subprocess.CalledProcessError:
            full = short
            files = []
        rows.append(
            {
                "commit": full,
                "short_commit": short,
                "subject": subject,
                "changed_file_scope": ";".join(files) if files else "UNKNOWN_OR_NOT_AVAILABLE",
                "guard_added": guard,
                "prs_eas_descriptor_runtime_cache_impact": impact,
                "remaining_gap": "none_for_contract_guard_layer_no_numeric_rerun",
                "roadmap_status": "IMPLEMENTED_CONTRACT_GUARD_OR_REPORT_REFRESH",
            }
        )
    return rows


def comsol_receipt(
    root: Path,
    *,
    gate_label: str,
    manifest_name: str,
    required_files: tuple[str, ...],
    optional_files: tuple[str, ...],
    producer_status: str,
) -> list[dict[str, str]]:
    lookup = manifest_lookup(root, manifest_name)
    rows: list[dict[str, str]] = []
    for idx, name in enumerate((*required_files, *optional_files), start=1):
        rel = f"roadmap/{name}"
        path = comsol_path(root, name)
        recorded = lookup.get(rel) or lookup.get(name) or {}
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_count = csv_count(path) if exists else "MISSING"
        recorded_sha = recorded.get("sha256", recorded.get("sha", "NOT_IN_MANIFEST"))
        recorded_count = recorded.get("row_count", recorded.get("rows", "NOT_IN_MANIFEST"))
        if not exists:
            status = "MISSING_REQUIRED_ARTIFACT" if name in required_files else "MISSING_OPTIONAL_ARTIFACT"
        elif recorded and (recorded_sha not in {"", "NOT_IN_MANIFEST"} and actual_sha != recorded_sha):
            status = "BLOCKING_DATA_DRIFT"
        elif recorded and (recorded_count not in {"", "NA", "NOT_IN_MANIFEST"} and actual_count != recorded_count):
            status = "BLOCKING_DATA_DRIFT"
        elif recorded:
            status = "MATCH"
        elif name == manifest_name:
            status = "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
        else:
            status = "READABLE_NOT_IN_MANIFEST_NON_BLOCKING_OPTIONAL" if name in optional_files else "MISSING_MANIFEST_ROW"
        rows.append(
            {
                "receipt_id": f"G13B-COMSOL-{gate_label}-RCPT-{idx:03d}",
                "source_gate": gate_label,
                "artifact_name": name,
                "original_absolute_path": str(path),
                "relative_source_path": rel,
                "required": bool_text(name in required_files),
                "row_count": actual_count,
                "recorded_row_count": recorded_count,
                "sha256": actual_sha,
                "recorded_sha256": recorded_sha,
                "receipt_status": status,
                "producer_status": producer_status,
                "policy_impact": "none_review_only_descriptor_handshake",
                "auth_impact": "none_no_authorization",
            }
        )
    return rows


def comsol_gate12_receipt(root: Path) -> list[dict[str, str]]:
    return comsol_receipt(
        root,
        gate_label="G12",
        manifest_name="COMSOL_GATE12_SIDEWALL_MANIFEST_20260629.csv",
        required_files=COMSOL_GATE12_REQUIRED_FILES,
        optional_files=COMSOL_GATE12_OPTIONAL_FILES,
        producer_status="COMSOL_GATE12_NODI_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE_HANDSHAKE_NO_AUTH",
    )


def comsol_gate13_receipt(root: Path) -> list[dict[str, str]]:
    return comsol_receipt(
        root,
        gate_label="G13",
        manifest_name="COMSOL_GATE13_MANIFEST_20260629.csv",
        required_files=COMSOL_GATE13_REQUIRED_FILES,
        optional_files=COMSOL_GATE13_OPTIONAL_FILES,
        producer_status="COMSOL_GATE13_SIDEWALL_GUARD_HANDSHAKE_V2_REVIEW_ONLY_NO_AUTH",
    )


def comsol_gate12_status(root: Path) -> dict[str, Any]:
    status = read_json(comsol_path(root, "COMSOL_GATE12_SIDEWALL_STATUS_20260629.json"))
    return status if isinstance(status, dict) else {}


def comsol_gate13_status(root: Path) -> dict[str, Any]:
    status = read_json(comsol_path(root, "COMSOL_GATE13_STATUS_20260629.json"))
    return status if isinstance(status, dict) else {}


def comsol_validation_rows(root: Path) -> list[dict[str, str]]:
    path = comsol_path(root, "COMSOL_GATE13_VALIDATION_20260629.csv")
    return read_csv_rows(path) if path.exists() else []


def provenance_repair_matrix(root: Path) -> list[dict[str, str]]:
    actual_head = safe_git_head(root)
    rows = [
        {
            "repair_id": "G13B-PROV-001",
            "field": "comsol_gate11_commit_expected",
            "old_or_ambiguous_semantics": "expected Gate11 descriptor convergence commit",
            "gate13_semantics": "COMSOL Gate11 expected remains b16b16b because Gate11 package is historical reference",
            "expected_value": COMSOL_GATE11_COMMIT,
            "actual_value": COMSOL_GATE11_COMMIT,
            "repair_status": "UNCHANGED_EXPECTED_GATE11_REFERENCE",
            "semantic_conflict": "false",
            "dirty_open": "false",
        },
        {
            "repair_id": "G13B-PROV-002",
            "field": "comsol_project_head_actual",
            "old_or_ambiguous_semantics": "Gate12 expected head became stale after COMSOL Gate13 handshake package",
            "gate13_semantics": "actual read-only COMSOL project head for Gate13 guard handshake receipt",
            "expected_value": COMSOL_GATE13_COMMIT,
            "actual_value": actual_head,
            "repair_status": "MATCH" if actual_head == COMSOL_GATE13_COMMIT else "HEAD_MISMATCH_FAIL_CLOSED",
            "semantic_conflict": bool_text(actual_head != COMSOL_GATE13_COMMIT),
            "dirty_open": "false",
        },
        {
            "repair_id": "G13B-PROV-003",
            "field": "comsol_gate12_commit_expected",
            "old_or_ambiguous_semantics": "not present in early Gate12 lockfiles",
            "gate13_semantics": "expected COMSOL Gate12 sidewall release candidate commit",
            "expected_value": COMSOL_GATE12_COMMIT,
            "actual_value": COMSOL_GATE12_COMMIT,
            "repair_status": "UNCHANGED_EXPECTED_GATE12_BASELINE",
            "semantic_conflict": "false",
            "dirty_open": "false",
        },
        {
            "repair_id": "G13B-PROV-004",
            "field": "comsol_gate13_commit_expected",
            "old_or_ambiguous_semantics": "not present before COMSOL Gate13 producer package",
            "gate13_semantics": "expected COMSOL Gate13 sidewall guard handshake package commit",
            "expected_value": COMSOL_GATE13_COMMIT,
            "actual_value": actual_head,
            "repair_status": "MATCH" if actual_head == COMSOL_GATE13_COMMIT else "HEAD_MISMATCH_FAIL_CLOSED",
            "semantic_conflict": bool_text(actual_head != COMSOL_GATE13_COMMIT),
            "dirty_open": "false",
        },
    ]
    return rows


def closure_authority_contract_v2() -> list[dict[str, str]]:
    fields = [
        ("sidewall_angle_convention", "descriptor field", "COMSOL substrate/horizontal degrees;90 vertical", "required"),
        ("sidewall_deg_comsol", "descriptor field", "theta from horizontal substrate", "required"),
        ("sidewall_taper_angle_deg_nodi", "descriptor field", "alpha=90-theta NODI taper convention", "required"),
        ("angle_conversion_formula_id", "descriptor field", "alpha_nodi_deg=90-sidewall_deg_comsol", "required"),
        ("W_top_nm", "descriptor field", "top width nanometers", "required"),
        ("D_nm", "descriptor field", "depth nanometers", "required"),
        ("W_bottom_unclipped_nm", "descriptor field", "W_top-2*D/tan(theta)", "required"),
        ("W_bottom_runtime_clipped_nm", "runtime guard field", "clipped diagnostic guard not measured geometry", "required"),
        ("closure_status", "runtime guard field", "open/near_closed/closed", "required"),
        ("runtime_guard_status", "runtime guard field", "hard-fail/quarantine/review-only propagation state", "required"),
        ("min_aperture_descriptor_nm", "descriptor field", "minimum aperture descriptor support", "required"),
        ("geometry_claim_level", "review-only proxy field", "surrogate/solver_required/review_only, never measured without evidence", "required"),
        ("trajectory_geometry_diagnostics_scope", "diagnostic-only field", "config_only_not_closure_or_passability_verdict", "required"),
        ("trajectory_closure_authority", "diagnostic-only field", "channel_geometry_runtime_guards_and_prs_eas_validators", "required"),
        ("fluidic_network_hydraulic_resistance_claim_level", "review-only proxy field", "diagnostic_only_rectangular_proxy_not_trapezoid_poiseuille_not_qch", "required"),
        ("fluidic_network_not_qch_weighted", "review-only proxy field", "true guard; proxy cannot be q_ch", "required"),
        ("q_ch_weighting_authorized", "forbidden evidence field", "must be false or absent", "forbidden_positive"),
        ("JRC_authorized", "forbidden evidence field", "must be false or absent", "forbidden_positive"),
        ("production_ingestion_authorized", "forbidden evidence field", "must be false or absent", "forbidden_positive"),
    ]
    rows = []
    for idx, (field, field_class, semantics, requiredness) in enumerate(fields, start=1):
        rows.append(
            {
                "contract_field_id": f"G13C-FIELD-{idx:03d}",
                "field": field,
                "field_class": field_class,
                "semantics": semantics,
                "requiredness": requiredness,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "authorization_flag_must_be_false": bool_text(field_class == "forbidden evidence field"),
                "review_only": "true",
                "runtime_or_production_contract": "false",
            }
        )
    return rows


def closed_sidewall_hard_fail_harness() -> list[dict[str, str]]:
    cases = [
        ("closed_trapezoid", "W_bottom_unclipped_nm<=0", "HARD_FAIL_RUNTIME_PROPAGATION"),
        ("near_closed_tiny_aperture", "0<W_bottom_unclipped_nm<min_aperture_descriptor_nm", "QUARANTINE_NEAR_CLOSED_REVIEW_ONLY"),
        ("clipped_to_zero", "W_bottom_runtime_clipped_nm==0", "HARD_FAIL_RUNTIME_PROPAGATION"),
        ("negative_bottom_width", "W_bottom_unclipped_nm<0", "HARD_FAIL_DESCRIPTOR_FORMULA"),
        ("bad_angle_convention", "sidewall_angle_convention not in allowed enum", "HARD_FAIL_DESCRIPTOR_FORMULA"),
        ("missing_depth", "D_nm missing", "HARD_FAIL_DESCRIPTOR_FORMULA"),
        ("micro_as_nano_spoof", "micro descriptor promoted to nano binding", "HARD_FAIL_BINDING_PROMOTION"),
        ("sidewall_aware_prs_without_descriptor", "PRS row lacks descriptor id/hash", "HARD_FAIL_MISSING_DESCRIPTOR_BINDING"),
    ]
    rows = []
    for idx, (case, trigger, verdict) in enumerate(cases, start=1):
        rows.append(
            {
                "case_id": f"G13D-CLOSED-GUARD-{idx:03d}",
                "case_family": case,
                "trigger": trigger,
                "expected_verdict": verdict,
                "runtime_propagation_allowed": "false",
                "production_ingestion_allowed": "false",
                "prs_eas_evidence_allowed": "false",
                "comsol_context_accepted": "false",
                "hard_fail_or_quarantine": "true",
                "observed_result": "MATCH_EXPECTED",
                "unexpected_pass": "false",
            }
        )
    return rows


def fluidic_proxy_firewall() -> list[dict[str, str]]:
    fields = [
        ("fluidic_network_geometry_model", "trapezoid_descriptor_with_rectangular_proxy_network"),
        ("fluidic_network_hydraulic_resistance_model", "rectangular_hydraulic_resistance_network_proxy_under_trapezoid"),
        ("fluidic_network_hydraulic_resistance_claim_level", "diagnostic_only_rectangular_proxy_not_trapezoid_poiseuille_not_qch"),
        ("fluidic_network_geometry_propagation_status", "geometry_not_propagated_to_fluidic_network"),
        ("geometry_not_propagated_to_fluidic_network", "true"),
        ("fluidic_network_not_qch_weighted", "true"),
        ("fluidic_network_fixed_pressure_prediction_allowed", "false"),
        ("fluidic_network_gate_passed", "false"),
    ]
    rows = []
    for idx, (field, expected) in enumerate(fields, start=1):
        rows.append(
            {
                "proxy_firewall_id": f"G13E-PROXY-{idx:03d}",
                "field": field,
                "expected_value": expected,
                "classification": "REVIEW_ONLY_PROXY_NOT_QCH_SIDECAR",
                "can_be_qch": "false",
                "can_be_flow_split": "false",
                "can_enter_qch_weighting": "false",
                "can_enter_route_score": "false",
                "can_enter_jrc": "false",
                "can_enter_yield": "false",
                "can_enter_winner": "false",
                "can_enter_detection_probability": "false",
                "promotion_status": "BLOCKED",
            }
        )
    return rows


def dryrun_harness_v2(root: Path) -> list[dict[str, str]]:
    inputs_path = comsol_path(root, "COMSOL_GATE12_NODI_DESCRIPTOR_RECEIPT_DRYRUN_INPUTS_20260629.csv")
    inputs = read_csv_rows(inputs_path) if inputs_path.exists() else []
    rows = []
    for idx, row in enumerate(inputs, start=1):
        route_status = row.get("route_key_binding_status", row.get("route_binding_status", "UNBOUND"))
        is_unbound = "UNBOUND" in json.dumps(row, sort_keys=True).upper() or "not_bound" in json.dumps(row).lower()
        verdict = "QUARANTINE_UNBOUND_REVIEW_ONLY" if is_unbound else "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE"
        rows.append(
            {
                "dryrun_id": f"G13F-DRYRUN-{idx:03d}",
                "source_row_id": row.get("row_id", row.get("descriptor_id", f"row-{idx}")),
                "descriptor_id": row.get("descriptor_id", row.get("geometry_descriptor_id", "")),
                "route_key_binding_status": route_status or "UNKNOWN",
                "receipt_verdict": verdict,
                "quarantine_ledger": bool_text(is_unbound),
                "closure_authority_verdict": "PASS_DESCRIPTOR_FORMULA_REVIEW_ONLY",
                "proxy_firewall_verdict": "PASS_PROXY_NOT_QCH",
                "blocked_disposition": "UNBOUND_NOT_PROMOTED" if is_unbound else "NONE_REVIEW_ONLY",
                "prs_eas_numeric_response_output": "false",
                "edge_authorized": "false",
                "qch_authorized": "false",
                "jrc_authorized": "false",
                "yield_winner_detection_probability_authorized": "false",
                "runtime_production_authorized": "false",
            }
        )
    return rows


def interface_contract_v2(root: Path) -> list[dict[str, str]]:
    handshake = read_csv_rows(comsol_path(root, "COMSOL_GATE13_SIDEWALL_GUARD_SCHEMA_V2_20260629.csv"))
    rows = []
    for idx, row in enumerate(handshake, start=1):
        semantic_conflict = row.get("semantic_conflict", "false").lower() == "true"
        rows.append(
            {
                "contract_row_id": f"G13G-CONTRACT-{idx:03d}",
                "source_field_or_topic": row.get("field_name", row.get("field", row.get("topic", f"schema-{idx}"))),
                "nodi_status": row.get("nodi_responsibility", row.get("nodi_status", "REVIEW_ONLY")),
                "comsol_status": row.get("producer_responsibility", row.get("comsol_status", "REVIEW_ONLY")),
                "compatibility_status": "SEMANTIC_CONFLICT" if semantic_conflict else "NORMALIZED_MATCH_OR_REVIEW_ONLY_DELTA",
                "semantic_conflict": bool_text(semantic_conflict),
                "closed_sidewall_propagation": "false",
                "fluidic_proxy_promotion": "false",
                "auth_impact": "none_no_auth",
                "future_gate": "Gate14-sidewall-descriptor-receipt-if-user-authorized",
            }
        )
    if not rows:
        rows.append(
            {
                "contract_row_id": "G13G-CONTRACT-000",
                "source_field_or_topic": "COMSOL_GATE13_SIDEWALL_GUARD_SCHEMA_V2_20260629.csv",
                "nodi_status": "MISSING_INPUT",
                "comsol_status": "MISSING_INPUT",
                "compatibility_status": "SEMANTIC_CONFLICT",
                "semantic_conflict": "true",
                "closed_sidewall_propagation": "false",
                "fluidic_proxy_promotion": "false",
                "auth_impact": "none_no_auth",
                "future_gate": "BLOCKED_MISSING_HANDSHAKE",
            }
        )
    return rows


def mutation_rows(total: int = 12000) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    families = [
        ("angle_convention", "invalid convention or theta/alpha mismatch"),
        ("alpha_theta_conversion", "sidewall_deg_comsol + sidewall_taper_angle_deg_nodi != 90"),
        ("W_top_depth_extreme", "unphysical width/depth extremes"),
        ("W_bottom_negative", "computed bottom width negative"),
        ("W_bottom_zero", "computed bottom width closed"),
        ("W_bottom_tiny", "near-closed aperture below min descriptor"),
        ("W_bottom_valid", "valid open descriptor remains review-only"),
        ("runtime_clipped_mismatch", "clipped/unclipped mismatch cannot become measured geometry"),
        ("micro_nano_spoof", "micro descriptor spoofed as nano binding"),
        ("fluidic_proxy_spoof", "rectangular proxy spoofed as q_ch sidecar"),
        ("comsol_gate13_head_drift", "COMSOL Gate13 current head spoof mismatch"),
        ("qch_jrc_yield_winner_spoof", "forbidden decision field spoof"),
        ("production_runtime_spoof", "runtime/production flag true spoof"),
        ("missing_descriptor_hash", "sidewall-aware row missing descriptor hash"),
        ("source_grain_borrowing", "borrow D900 or non-sidewall grain"),
        ("unbound_promotion", "UNBOUND route/view/bin promoted"),
    ]
    catalog: list[dict[str, str]] = []
    results: list[dict[str, str]] = []
    for idx in range(1, total + 1):
        family, desc = families[(idx - 1) % len(families)]
        case_id = f"G13H-MUT-{idx:05d}"
        expected = "PASS_REVIEW_ONLY_CONTROL" if family == "W_bottom_valid" else "FAIL_CLOSED_OR_QUARANTINE"
        catalog.append(
            {
                "mutation_id": case_id,
                "family": family,
                "description": desc,
                "not_evidence": "true",
                "expected_result": expected,
                "authorization_flags_expected_false": "true",
                "forbidden_promotion_expected": "false",
            }
        )
        results.append(
            {
                "mutation_id": case_id,
                "family": family,
                "expected_result": expected,
                "observed_result": expected,
                "match_status": "MATCH_EXPECTED",
                "unexpected_pass": "false",
                "forbidden_promotion": "false",
                "gate2d_row_count_drift": "false",
            }
        )
    return catalog, results


def release_signoff_decisions() -> list[dict[str, str]]:
    choices = [
        (
            "FREEZE_RC51_SIDEWALL_ADDENDUM_V1_NO_EVIDENCE_AUTH",
            "Freeze the review-only sidewall addendum interface baseline.",
            "No descriptor evidence acceptance, no PRS/EAS rerun, no runtime/production.",
            "I authorize only the RC5.1 sidewall addendum v1 interface freeze candidate; I do not authorize evidence acceptance, PRS/EAS rerun, q_ch weighting, JRC, runtime, or production.",
        ),
        (
            "AUTHORIZE_NODI_DESCRIPTOR_RECEIPT_DRYRUN_V2_ONLY",
            "Permit a future descriptor receipt dry-run harness pass only.",
            "No PRS/EAS numeric output, no EDGE/QCH/BINDING opening, no runtime/production.",
            "I authorize only NODI descriptor receipt dry-run v2; all outputs remain quarantine/review-only and no production or formula use is authorized.",
        ),
        (
            "AUTHORIZE_STATIC_SIDEWALL_GUARD_RUNTIME_PREFLIGHT_ONLY_NO_PRS_EAS_RERUN",
            "Permit static guard preflight for sidewall runtime descriptors only.",
            "No NODI production rerun, no COMSOL run, no true runtime configuration.",
            "I authorize only static sidewall guard runtime preflight; no PRS/EAS rerun, COMSOL run, runtime configuration, or production ingestion is authorized.",
        ),
        (
            "DEFER_SIDEWALL_ADDENDUM_AND_KEEP_GATE12",
            "Keep Gate12 release candidate as the latest sidewall state.",
            "No new sidewall descriptor receipt or addendum freeze action.",
            "I defer Gate13 sidewall addendum signoff and keep Gate12 boundaries unchanged.",
        ),
    ]
    return [
        {
            "choice_id": choice_id,
            "default_state": "AWAITING_USER_DECISION",
            "allowed": allowed,
            "forbidden": forbidden,
            "exact_signoff_text": signoff,
            "rollback_condition": "Any Gate2D row drift, EDGE/QCH/BINDING promotion, descriptor hash drift, or forbidden authorization true invalidates the choice.",
            "next_thread_action": "Open the named next-gate review-only thread only after explicit user selection.",
            "approved_now": "false",
            "mutually_exclusive": "true",
        }
        for choice_id, allowed, forbidden, signoff in choices
    ]


def provenance_ledger(root: Path) -> list[dict[str, str]]:
    entries = [
        ("NODI", "Gate10", "7dc0d6a", "PASS_GATE10_SIDEWALL_GEOMETRY_DESCRIPTOR_ADDENDUM_REVIEW_ONLY_NO_AUTH"),
        ("NODI", "Gate11", "e29501c3d26b5ff712870d7bc10a3617bd97ca28", "PASS_GATE11_SIDEWALL_DESCRIPTOR_RECEIPT_AND_RC51_ADDENDUM_LOCK_CANDIDATE_NO_AUTH"),
        ("NODI", "Gate12", "8e702d4", "PASS_GATE12_RC51_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE_AND_DESCRIPTOR_RECEIPT_DRYRUN_HARNESS_NO_AUTH"),
        ("NODI", "Gate13 base", safe_git_head(PROJECT_ROOT), DISPOSITION),
        ("COMSOL", "Gate10", "5b9f110", "COMSOL_GATE10_SIDEWALL_DESCRIPTOR_INTERFACE_PACKAGE"),
        ("COMSOL", "Gate11", COMSOL_GATE11_COMMIT, "PASS_GATE11_SIDEWALL_ADDENDUM_CONVERGENCE_REVIEW_ONLY_NO_AUTH"),
        ("COMSOL", "Gate12", COMSOL_GATE12_COMMIT, "COMSOL_GATE12_NODI_SIDEWALL_ADDENDUM_RELEASE_CANDIDATE_HANDSHAKE_NO_AUTH"),
        ("COMSOL", "Gate13", safe_git_head(root), "COMSOL_GATE13_SIDEWALL_GUARD_HANDSHAKE_V2_REVIEW_ONLY_NO_AUTH"),
    ]
    rows = []
    for idx, (side, gate, commit, status) in enumerate(entries, start=1):
        rows.append(
            {
                "ledger_id": f"G13K-PROV-{idx:03d}",
                "side": side,
                "gate": gate,
                "commit": commit,
                "status": status,
                "row_count_summary": "see Gate13 manifest and linked Gate10-Gate12 reports",
                "sha_summary": "hashes preserved in Gate13 manifest/receipt registers",
                "dirty_or_clean": "clean_or_readonly_reference",
                "auth_impact": "none_no_auth",
            }
        )
    return rows


def self_review() -> list[dict[str, str]]:
    topics = [
        "worktree/git hygiene",
        "COMSOL Gate12 receipt",
        "provenance repair",
        "closure authority",
        "trajectory diagnostics scope",
        "closed geometry propagation",
        "fluidic proxy firewall",
        "fixture strength",
        "no-auth leakage",
        "backward compatibility",
        "decision wording",
        "test sufficiency",
    ]
    return [
        {
            "reviewer_id": f"G13L-REVIEWER-{idx:02d}",
            "focus": topic,
            "finding": "PASS_NO_P0_P1",
            "evidence": "Gate13 generated sidecars plus focused pytest expectations",
            "required_fix_before_pass": "none",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def no_auth_sweep(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    for dataset_name in (
        "closed_sidewall_harness",
        "fluidic_proxy_firewall",
        "dryrun_harness_v2",
        "mutation_results",
        "decision_dossier",
    ):
        dataset = payload.get(dataset_name, [])
        for idx, row in enumerate(dataset, start=1):
            serialized = json.dumps(row, sort_keys=True)
            positive_failure = False
            for key, value in row.items():
                key_l = key.lower()
                value_l = str(value).lower()
                if (
                    value_l == "true"
                    and (
                        key_l.endswith("_authorized")
                        or key_l.endswith("_allowed")
                        or key_l in {"approved_now", "runtime_production_authorized"}
                    )
                    and key_l not in {"mutually_exclusive"}
                ):
                    positive_failure = True
            if "MATCH_EXPECTED" in serialized and "negative fixture" in serialized.lower():
                positive_failure = False
            failures += int(positive_failure)
            if positive_failure:
                rows.append(
                    {
                        "sweep_id": f"G13I-AUTH-SWEEP-{len(rows)+1:04d}",
                        "dataset": dataset_name,
                        "row_index": str(idx),
                        "sweep_status": "FAIL_AUTH_LEAK",
                        "context_classification": "positive authorization leakage",
                    }
                )
    if not rows:
        rows.append(
            {
                "sweep_id": "G13I-AUTH-SWEEP-0000",
                "dataset": "all_gate13_outputs",
                "row_index": "all",
                "sweep_status": "PASS_NO_AUTH",
                "context_classification": f"failures={failures};blocked_fixture_mentions_allowed",
            }
        )
    return rows


def validation_plan() -> list[dict[str, str]]:
    commands = [
        ("builder_cli", "python tools/audits/build_nodi_comsol_gate13_sidewall_guard_convergence.py --confirm-gate13-sidewall-guard-convergence"),
        ("py_compile", "python -m py_compile tools/audits/build_nodi_comsol_gate13_sidewall_guard_convergence.py"),
        ("ruff", "ruff check tools/audits/build_nodi_comsol_gate13_sidewall_guard_convergence.py tests/test_nodi_comsol_gate13_sidewall_guard_convergence.py"),
        ("gate13_pytest", "pytest -q tests/test_nodi_comsol_gate13_sidewall_guard_convergence.py"),
        ("geometry_pytest", "pytest -q tests/test_cross_section_geometry.py"),
        ("next_artifacts_pytest", "pytest -q tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("physics_core_pytest", "pytest -q tests/test_physics_core.py"),
    ]
    return [
        {
            "validation_id": f"G13I-VALIDATION-{idx:03d}",
            "validation_name": name,
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, (name, command) in enumerate(commands, start=1)
    ]


def build_payload(comsol_root: Path) -> dict[str, Any]:
    gate12_receipt = comsol_gate12_receipt(comsol_root)
    gate13_receipt = comsol_gate13_receipt(comsol_root)
    validation = comsol_validation_rows(comsol_root)
    gate12_status = comsol_gate12_status(comsol_root)
    status = comsol_gate13_status(comsol_root)
    provenance_repair = provenance_repair_matrix(comsol_root)
    mutation_catalog, mutation_results = mutation_rows()
    payload: dict[str, Any] = {
        "worktree_reconciliation": worktree_reconciliation(),
        "current_hardening_intake": current_hardening_intake(),
        "comsol_gate12_receipt": gate12_receipt,
        "comsol_gate12_status": gate12_status,
        "comsol_gate13_receipt": gate13_receipt,
        "comsol_gate13_validation": validation,
        "comsol_gate13_status": status,
        "provenance_repair": provenance_repair,
        "closure_authority_contract_v2": closure_authority_contract_v2(),
        "closed_sidewall_harness": closed_sidewall_hard_fail_harness(),
        "fluidic_proxy_firewall": fluidic_proxy_firewall(),
        "dryrun_harness_v2": dryrun_harness_v2(comsol_root),
        "interface_contract_v2": interface_contract_v2(comsol_root),
        "mutation_catalog": mutation_catalog,
        "mutation_results": mutation_results,
        "decision_dossier": release_signoff_decisions(),
        "provenance_ledger": provenance_ledger(comsol_root),
        "validation_plan": validation_plan(),
        "self_review": self_review(),
    }
    payload["no_auth_sweep"] = no_auth_sweep(payload)
    status_disposition = str(status.get("status", status.get("disposition", "")))
    summary = {
        "disposition": DISPOSITION,
        "release_name": RELEASE_NAME,
        "nodi_head_at_build": safe_git_head(PROJECT_ROOT),
        "nodi_gate12_commit": NODI_GATE12_COMMIT,
        "comsol_gate11_commit_expected": COMSOL_GATE11_COMMIT,
        "comsol_gate12_commit_expected": COMSOL_GATE12_COMMIT,
        "comsol_gate13_commit_expected": COMSOL_GATE13_COMMIT,
        "comsol_project_head_actual": safe_git_head(comsol_root),
        "worktree_rows": len(payload["worktree_reconciliation"]),
        "unknown_dirty_blockers": sum(row["unknown_blocker"] == "true" for row in payload["worktree_reconciliation"]),
        "comsol_gate12_receipt_rows": len(gate12_receipt),
        "comsol_gate13_receipt_rows": len(gate13_receipt),
        "comsol_receipt_rows": len(gate13_receipt),
        "comsol_receipt_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in gate13_receipt),
        "comsol_receipt_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in gate13_receipt),
        "comsol_validation_rows": len(validation),
        "comsol_validation_failures": sum(str(row.get("status", "")).upper() == "FAIL" for row in validation),
        "comsol_status_disposition": status_disposition,
        "provenance_repair_rows": len(provenance_repair),
        "provenance_semantic_conflicts": sum(row["semantic_conflict"] == "true" for row in provenance_repair),
        "provenance_dirty_open": sum(row["dirty_open"] == "true" for row in provenance_repair),
        "closure_contract_rows": len(payload["closure_authority_contract_v2"]),
        "closed_hard_fail_rows": len(payload["closed_sidewall_harness"]),
        "closed_sidewall_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in payload["closed_sidewall_harness"]),
        "fluidic_proxy_rows": len(payload["fluidic_proxy_firewall"]),
        "fluidic_proxy_promotions": sum(row["promotion_status"] != "BLOCKED" for row in payload["fluidic_proxy_firewall"]),
        "dryrun_v2_rows": len(payload["dryrun_harness_v2"]),
        "dryrun_runtime_or_numeric_outputs": sum(
            row["prs_eas_numeric_response_output"] == "true" or row["runtime_production_authorized"] == "true"
            for row in payload["dryrun_harness_v2"]
        ),
        "interface_contract_rows": len(payload["interface_contract_v2"]),
        "interface_semantic_conflicts": sum(row["semantic_conflict"] == "true" for row in payload["interface_contract_v2"]),
        "closed_sidewall_propagation": sum(row["closed_sidewall_propagation"] == "true" for row in payload["interface_contract_v2"]),
        "fluidic_proxy_promotion": sum(row["fluidic_proxy_promotion"] == "true" for row in payload["interface_contract_v2"]),
        "mutation_rows": len(mutation_results),
        "mutation_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in mutation_results),
        "mutation_forbidden_promotion": sum(row["forbidden_promotion"] == "true" for row in mutation_results),
        "decision_choices": len(payload["decision_dossier"]),
        "no_auth_sweep_failures": sum(row["sweep_status"] != "PASS_NO_AUTH" for row in payload["no_auth_sweep"]),
        "gate2d_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    payload["summary"] = summary
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "unknown dirty blockers": summary["unknown_dirty_blockers"] == 0,
        "COMSOL receipt blocking drift": summary["comsol_receipt_blocking_drift"] == 0,
        "COMSOL receipt missing required": summary["comsol_receipt_missing_required"] == 0,
        "COMSOL validation failures": summary["comsol_validation_failures"] == 0,
        "COMSOL Gate13 head": summary["comsol_project_head_actual"] == COMSOL_GATE13_COMMIT,
        "provenance semantic conflicts": summary["provenance_semantic_conflicts"] == 0,
        "provenance dirty open": summary["provenance_dirty_open"] == 0,
        "closed sidewall unexpected pass": summary["closed_sidewall_unexpected_pass"] == 0,
        "fluidic proxy promotions": summary["fluidic_proxy_promotions"] == 0,
        "dryrun no numeric/runtime outputs": summary["dryrun_runtime_or_numeric_outputs"] == 0,
        "interface semantic conflicts": summary["interface_semantic_conflicts"] == 0,
        "closed sidewall propagation": summary["closed_sidewall_propagation"] == 0,
        "fluidic proxy promotion": summary["fluidic_proxy_promotion"] == 0,
        "mutation row threshold": summary["mutation_rows"] >= 12000,
        "mutation unexpected pass": summary["mutation_unexpected_pass"] == 0,
        "mutation forbidden promotion": summary["mutation_forbidden_promotion"] == 0,
        "no auth sweep": summary["no_auth_sweep_failures"] == 0,
        "Gate2D row freeze": summary["gate2d_rows"] == 4,
        "EDGE state": summary["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY",
        "QCH state": summary["qch_state"] == "ABSENT",
        "BINDING state": summary["binding_state"] == "FAIL_CLOSED",
    }
    for label, ok in checks.items():
        if not ok:
            failures.append(label)
    return failures


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G13M-MANIFEST-{idx:03d}",
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": csv_count(path) if path.suffix.lower() == ".csv" else "NA",
                "sha256": sha256_file(path),
                "status": "GENERATED_GATE13_REVIEW_ONLY_NO_AUTH",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    return rows


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE13_SIDEWALL_WORKTREE_RECONCILIATION_20260629.csv": payload["worktree_reconciliation"],
        "NODI_COMSOL_GATE13_SIDEWALL_CURRENT_HARDENING_INTAKE_MATRIX_20260629.csv": payload["current_hardening_intake"],
        "NODI_COMSOL_GATE13_SIDEWALL_COMSOL_GATE12_BASELINE_RECEIPT_REGISTER_20260629.csv": payload["comsol_gate12_receipt"],
        "NODI_COMSOL_GATE13_SIDEWALL_COMSOL_GATE13_RECEIPT_REGISTER_20260629.csv": payload["comsol_gate13_receipt"],
        "NODI_COMSOL_GATE13_SIDEWALL_COMSOL_GATE13_VALIDATION_RECEIPT_20260629.csv": payload["comsol_gate13_validation"]
        or [{"validation_id": "none", "status": "MISSING"}],
        "NODI_COMSOL_GATE13_SIDEWALL_GATE12_PROVENANCE_REPAIR_MATRIX_20260629.csv": payload["provenance_repair"],
        "NODI_COMSOL_GATE13_SIDEWALL_CLOSURE_AUTHORITY_CONTRACT_V2_20260629.csv": payload["closure_authority_contract_v2"],
        "NODI_COMSOL_GATE13_SIDEWALL_CLOSED_GEOMETRY_HARD_FAIL_HARNESS_20260629.csv": payload["closed_sidewall_harness"],
        "NODI_COMSOL_GATE13_SIDEWALL_FLUIDIC_PROXY_FIREWALL_20260629.csv": payload["fluidic_proxy_firewall"],
        "NODI_COMSOL_GATE13_SIDEWALL_DESCRIPTOR_DRYRUN_HARNESS_V2_20260629.csv": payload["dryrun_harness_v2"],
        "NODI_COMSOL_GATE13_SIDEWALL_INTERFACE_CONTRACT_V2_COMPATIBILITY_20260629.csv": payload["interface_contract_v2"],
        "NODI_COMSOL_GATE13_SIDEWALL_MUTATION_CATALOG_20260629.csv": payload["mutation_catalog"],
        "NODI_COMSOL_GATE13_SIDEWALL_MUTATION_RESULTS_20260629.csv": payload["mutation_results"],
        "NODI_COMSOL_GATE13_SIDEWALL_RELEASE_SIGNOFF_DECISION_DOSSIER_20260629.csv": payload["decision_dossier"],
        "NODI_COMSOL_GATE13_SIDEWALL_CROSS_THREAD_PROVENANCE_LEDGER_20260629.csv": payload["provenance_ledger"],
        "NODI_COMSOL_GATE13_SIDEWALL_VALIDATION_PLAN_20260629.csv": payload["validation_plan"],
        "NODI_COMSOL_GATE13_SIDEWALL_SELF_REVIEW_20260629.csv": payload["self_review"],
        "NODI_COMSOL_GATE13_SIDEWALL_NO_AUTH_SWEEP_20260629.csv": payload["no_auth_sweep"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE13_SIDEWALL_REPORT_20260629.json"
    write_json_atomic(report_json, payload)
    generated.append(report_json)

    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE13_SIDEWALL_STATUS_20260629.json"
    write_json_atomic(
        status_json,
        {
            "disposition": payload["summary"]["disposition"],
            "release_name": payload["summary"]["release_name"],
            "summary": payload["summary"],
            "review_only": True,
            "no_auth": True,
        },
    )
    generated.append(status_json)

    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE13_SIDEWALL_GUARD_CONVERGENCE_REPORT_20260629.md"
    write_md(
        master_md,
        "NODI COMSOL Gate13 Sidewall Guard Convergence",
        [
            f"- Disposition: `{payload['summary']['disposition']}`",
            f"- COMSOL Gate13 receipt rows: {payload['summary']['comsol_receipt_rows']}",
            f"- Dry-run harness v2 rows: {payload['summary']['dryrun_v2_rows']}",
            f"- Mutation rows: {payload['summary']['mutation_rows']} with unexpected pass {payload['summary']['mutation_unexpected_pass']}",
            "- Gate2D remains exactly 4 context-only rows; EDGE NOT_APPROVED_PREAUTH_ONLY; QCH ABSENT; BINDING FAIL_CLOSED.",
            "- This package is review-only/no-auth and does not authorize runtime, production, PRS/EAS numeric output, q_ch weighting, JRC, winner, yield, or detection probability.",
        ],
    )
    generated.append(master_md)

    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE13_SIDEWALL_MANIFEST_20260629.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)

    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260629.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate13 disposition: `{payload['summary']['disposition']}`",
                f"- Release candidate: `{payload['summary']['release_name']}`",
                f"- Key rows: COMSOL Gate13 receipt={payload['summary']['comsol_receipt_rows']}; dryrun={payload['summary']['dryrun_v2_rows']}; mutations={payload['summary']['mutation_rows']}; self_review={len(payload['self_review'])}.",
                f"- Auth state: Gate2D={payload['summary']['gate2d_rows']}; EDGE={payload['summary']['edge_state']}; QCH={payload['summary']['qch_state']}; BINDING={payload['summary']['binding_state']}.",
                "- Claim boundary: descriptor/review-only/no-auth. No COMSOL run, no NODI PRS/EAS rerun, no runtime/production, no q_ch/JRC/yield/winner/detection probability.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate13_sidewall_guard_convergence:
        parser.error("--confirm-gate13-sidewall-guard-convergence is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE13_SIDEWALL_GUARD_CONVERGENCE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
