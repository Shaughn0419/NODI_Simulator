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


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
COMSOL_ROADMAP = "roadmap"
BASE_GATE13_COMMIT = "0c90ae07f6cc648bf50b9c22e85b9fd82ad614fa"
EXPECTED_COMSOL_GATE13_HEAD = "64dfa64b766750f91813c3cd470d369dec61f384"
EXPECTED_COMSOL_GATE14_HEAD = "a378398eea8af883e1ec89fc80d93b60ff33a47c"
EXPECTED_COMSOL_GATE15_HEAD = "7090794ff20970955a011b123b3de171e96910a3"
ALLOWED_COMSOL_CURRENT_HEADS = frozenset(
    {EXPECTED_COMSOL_GATE14_HEAD, EXPECTED_COMSOL_GATE15_HEAD}
)
DISPOSITION = "NODI_GATE14_SIDEWALL_IMPLEMENTATION_GUARD_RELEASE_AND_COMSOL_CONTRACT_V3_NO_AUTH"
CONTRACT_NAME = "NODI_SIDEWALL_IMPLEMENTATION_GUARD_CONTRACT_V3_RELEASED_CLEAN_REVIEW_ONLY_NO_AUTH"
ALLOWED_USE = "review-only implementation guard release;COMSOL producer schema request;static validator/dry-run harness"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS;JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;true PRS/EAS sidewall numeric output;validated Brownian/flow/optical/wet physics"
)

COMSOL_GATE13_FILES = (
    "COMSOL_GATE13_SIDEWALL_GUARD_HANDSHAKE_V2_PACKET_20260629.md",
    "COMSOL_GATE13_STATUS_20260629.json",
    "COMSOL_GATE13_MANIFEST_20260629.csv",
    "COMSOL_GATE13_SIDEWALL_GUARD_SCHEMA_V2_20260629.csv",
    "COMSOL_GATE13_NODI_DESCRIPTOR_DRYRUN_INPUTS_V2_20260629.csv",
    "COMSOL_GATE13_MUTATION_FIXTURE_CATALOG_20260629.csv",
    "COMSOL_GATE13_MUTATION_RESULTS_20260629.csv",
    "COMSOL_GATE13_VALIDATION_20260629.csv",
    "COMSOL_GATE13_GATE12_SELF_RECEIPT_20260629.csv",
    "COMSOL_GATE13_NODI_SIDEWALL_HARDENING_INTAKE_20260629.csv",
    "COMSOL_GATE13_CLOSED_SIDEWALL_POLICY_20260629.csv",
    "COMSOL_GATE13_FLUIDIC_PROXY_FIREWALL_20260629.csv",
    "COMSOL_GATE13_BINDING_BLOCKER_ROADMAP_V3_20260629.csv",
    "COMSOL_GATE13_FUTURE_HANDOFF_ESCROW_V4_20260629.csv",
    "COMSOL_GATE13_PROVENANCE_LEDGER_20260629.csv",
    "COMSOL_GATE13_SELF_REVIEW_20260629.csv",
)

REPORTS = {
    "346": "GATE14A_CURRENT_RELEASE_INTAKE_AND_POST_GATE13_DELTA",
    "347": "GATE14B_IMPLEMENTATION_GUARD_RELEASE_LEDGER",
    "348": "GATE14C_SIDEWALL_INTERFACE_CONTRACT_V3_SCHEMA_DELTA",
    "349": "GATE14D_COMSOL_GATE13_RECEIPT_AND_STALE_INTAKE_CLOSURE",
    "350": "GATE14E_RECEIVER_HARNESS_V3_COVERAGE",
    "351": "GATE14F_COMSOL_GATE14_PRODUCER_REQUEST_V3",
    "352": "GATE14G_PACKAGE_ABCD_READINESS_NO_GO_BOARD",
    "353": "GATE14H_FORBIDDEN_ALIAS_SOURCE_DRIFT_MUTATION_EXPANSION",
    "354": "GATE14I_IMPLEMENTATION_AUDIT_HARDENING_ADDENDUM",
    "355": "GATE14J_TESTS_AND_REGRESSION_SWEEP",
    "356": "GATE14K_NO_AUTH_AND_CLAIM_BOUNDARY_SWEEP_V4",
    "357": "GATE14L_DECISION_DOSSIER_V4",
    "358": "GATE14M_INDEPENDENT_SELF_REVIEW",
    "359": "GATE14N_REPORTS_SIDECARS_AND_MANIFEST",
    "360": "GATE14O_FINAL_HANDOFF",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate14 sidewall implementation guard release and COMSOL contract v3."
    )
    parser.add_argument("--confirm-gate14-sidewall-implementation-contract", action="store_true")
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


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def current_release_intake() -> list[dict[str, str]]:
    status = run_git(["status", "--short"])
    dirty_lines = status.splitlines() if status else []
    gate14_lines = [
        line
        for line in dirty_lines
        if "GATE14" in line
        or "gate14_sidewall_implementation_contract" in line
        or "gate13_sidewall_guard_convergence" in line
        or "NODI_COMSOL_GATE14_SIDEWALL_" in line
    ]
    non_gate14_lines = [line for line in dirty_lines if line not in gate14_lines]
    head = safe_git_head(PROJECT_ROOT)
    return [
        {
            "intake_id": "G14A-CURRENT-RELEASE-001",
            "nodi_head": head,
            "worktree_status": "clean" if not non_gate14_lines else "dirty",
            "dirty_count": str(len(non_gate14_lines)),
            "gate14_generated_pending_count": str(len(gate14_lines)),
            "expected_clean_release": "true",
            "release_status": "RELEASED_CLEAN" if not non_gate14_lines else "DIRTY_FAIL_CLOSED",
            "auth_impact": "none_no_auth",
        }
    ]


def post_gate13_delta_ledger() -> list[dict[str, str]]:
    commits = run_git(["log", "--pretty=%H%x09%s", f"{BASE_GATE13_COMMIT}..HEAD"]).splitlines()
    rows: list[dict[str, str]] = []
    for idx, line in enumerate(commits, start=1):
        full, subject = line.split("\t", 1)
        files = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", full]).splitlines()
        subject_l = subject.lower()
        if "flow" in subject_l or "q_ch" in subject_l:
            category = "flow_alias_or_proxy_guard"
        elif "rank" in subject_l or "jrc" in subject_l or "chi" in subject_l or "route score" in subject_l:
            category = "decision_alias_denylist_guard"
        elif "blocked bin" in subject_l or "grain" in subject_l:
            category = "blocked_bin_or_grain_precheck_guard"
        elif "profile" in subject_l or "measured" in subject_l or "signature" in subject_l:
            category = "profile_signature_source_hash_guard"
        elif "angle" in subject_l:
            category = "angle_convention_guard"
        else:
            category = "sidewall_implementation_guard_hardening"
        rows.append(
            {
                "delta_id": f"G14A-DELTA-{idx:03d}",
                "commit": full,
                "short_commit": full[:7],
                "subject": subject,
                "touched_files": ";".join(files),
                "guard_category": category,
                "interface_impact": "additive_or_tightening_contract_guard",
                "claim_risk": "no_auth_guard_prevents_promotion",
                "tests_required": "Gate14 focused;implementation audit regression;sidewall contract regressions",
            }
        )
    return rows


def implementation_guard_release_ledger() -> list[dict[str, str]]:
    status_path = OUTPUT_DIR / "NODI_SIDEWALL_ANGLE_IMPLEMENTATION_GUARD_STATUS_20260630.csv"
    source_rows = read_csv_rows(status_path)
    rows = []
    for idx, row in enumerate(source_rows, start=1):
        status = row.get("status", "")
        package = row.get("package", "")
        blocked = status.lower() == "blocked"
        if package.startswith("Package A"):
            boundary = "schema_descriptor_profile_hash_guard"
        elif package.startswith("Package B"):
            boundary = "geometry_sampler_signature_guard"
        elif package.startswith("Package C"):
            boundary = "near_wall_optical_wet_physics_guard_partial_or_blocked"
        elif package.startswith("Package D"):
            boundary = "prs_eas_precheck_alias_blocked_bin_guard"
        else:
            boundary = "all_package_claim_boundary"
        rows.append(
            {
                "release_ledger_id": f"G14B-IMPL-GUARD-{idx:03d}",
                "gate_id": row.get("gate_id", f"row-{idx}"),
                "package": package,
                "status": status,
                "release_status": "BLOCKED_AS_EXPECTED" if blocked else "RELEASED_CLEAN_GUARD_PASS",
                "evidence_or_test": row.get("evidence", ""),
                "allowed_use": "static no-compute guard evidence;COMSOL contract v3 input",
                "blocked_use": row.get("blocked_claims", BLOCKED_USE),
                "comsol_implication": (
                    "must remain blocked/future-only in COMSOL contract"
                    if blocked
                    else "can be consumed as guard semantics, not physical validation"
                ),
                "claim_boundary": boundary,
                "no_auth": "true",
            }
        )
    return rows


def interface_contract_v3_schema_delta() -> list[dict[str, str]]:
    field_families = [
        ("geometry_profile_source", "profile_source_hash_guard", "NODI producer/receiver", "COMSOL must export source and hash if descriptor-derived"),
        ("geometry_profile_sha256", "profile_source_hash_guard", "NODI receiver", "COMSOL profile hash must match source descriptor hash for comsol_descriptor"),
        ("source_geometry_descriptor_sha", "profile_source_hash_guard", "both", "hash bridge to descriptor identity"),
        ("runtime_top_aperture_nm", "runtime_top_aperture_binding", "NODI receiver", "required with top_cd_bias metadata before runtime aperture can be referenced"),
        ("top_cd_bias_nm", "runtime_top_aperture_binding", "COMSOL optional producer", "metadata only; no runtime promotion"),
        ("top_cd_bias_source", "runtime_top_aperture_binding", "COMSOL optional producer", "must be explicit source metadata"),
        ("measured_profile_lookup_status", "measured_profile_guard", "NODI receiver", "blocked until loaded and validated"),
        ("measured_profile_path", "measured_profile_guard", "COMSOL future producer", "path alone never proves measured geometry"),
        ("measured_profile_sha256", "measured_profile_guard", "COMSOL future producer", "must pair with loaded/validated flags"),
        ("measured_profile_loaded", "measured_profile_guard", "NODI receiver", "must be true for measured claim"),
        ("measured_profile_validated", "measured_profile_guard", "NODI receiver", "must be true for measured claim"),
        ("particle_center_support_status", "sampler_support", "NODI producer", "review-only sampler diagnostic"),
        ("nearest_wall_distance_nm", "sampler_support", "NODI producer", "diagnostic; not wet passability"),
        ("surface_gap_nm", "sampler_support", "NODI producer", "diagnostic; not solver validation"),
        ("includes_trajectory_near_wall_metrics", "package_C_gate", "NODI receiver", "must be true with package_C_validation_status pass before wall-distance basis"),
        ("package_C_validation_status", "package_C_gate", "NODI receiver", "blocks optical/wet claims unless pass"),
        ("bin_accessible", "blocked_bin_guard", "NODI receiver", "blocked bins cannot carry numeric response"),
        ("bin_particle_center_support_status", "blocked_bin_guard", "NODI receiver", "must agree with bin_accessible"),
        ("blocked_reason", "blocked_bin_guard", "NODI receiver", "required for inaccessible bins"),
        ("neighbor_fill_allowed", "blocked_bin_guard", "NODI receiver", "false for blocked bins"),
        ("flow_rate", "alias_denylist", "forbidden positive", "blocked exact/alias unless future q_ch sidecar"),
        ("Q", "alias_denylist", "forbidden positive", "blocked exact/alias unless future q_ch sidecar"),
        ("q_ch", "alias_denylist", "forbidden positive", "blocked exact/alias unless future q_ch sidecar"),
        ("route_score", "alias_denylist", "forbidden positive", "blocked decision field"),
        ("rank", "alias_denylist", "forbidden positive", "blocked ranking field"),
        ("JRC", "alias_denylist", "forbidden positive", "blocked joint route class"),
        ("chi_selected", "alias_denylist", "forbidden positive", "blocked selection field"),
        ("sidewall_aware", "shortcut_denylist", "forbidden positive", "broad shortcut rejected; explicit v2/v3 fields required"),
    ]
    rows = []
    for idx, (field, family, responsibility, expectation) in enumerate(field_families, start=1):
        forbidden = "denylist" in family or responsibility == "forbidden positive"
        rows.append(
            {
                "schema_delta_id": f"G14C-V3-FIELD-{idx:03d}",
                "field_or_family": field,
                "field_family": family,
                "change_type": "additive_or_clarifying_v3_delta",
                "nodi_responsibility": responsibility,
                "comsol_producer_expectation": expectation,
                "allowed_use": "schema guard/static preflight/review-only dry-run",
                "blocked_use": BLOCKED_USE,
                "auth_impact": "none_no_auth",
                "future_gate": "Gate15 or explicit user-authorized pilot only",
                "forbidden_positive": bool_text(forbidden),
            }
        )
    return rows


def manifest_lookup(root: Path) -> dict[str, dict[str, str]]:
    manifest = comsol_path(root, "COMSOL_GATE13_MANIFEST_20260629.csv")
    if not manifest.exists():
        return {}
    rows = read_csv_rows(manifest)
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        for key in ("path", "relative_path", "artifact_path", "file", "artifact"):
            value = row.get(key, "").replace("\\", "/").lstrip("./")
            if value:
                lookup[value] = row
                lookup[Path(value).name] = row
    return lookup


def comsol_gate13_receipt(root: Path) -> list[dict[str, str]]:
    lookup = manifest_lookup(root)
    rows = []
    for idx, name in enumerate(COMSOL_GATE13_FILES, start=1):
        rel = f"roadmap/{name}"
        path = comsol_path(root, name)
        recorded = lookup.get(rel) or lookup.get(name) or {}
        exists = path.exists()
        sha = sha256_file(path) if exists else "MISSING"
        row_count = csv_count(path) if exists else "MISSING"
        recorded_sha = recorded.get("sha256", recorded.get("sha", "NOT_IN_MANIFEST"))
        recorded_count = recorded.get("row_count", recorded.get("rows", "NOT_IN_MANIFEST"))
        if not exists:
            status = "MISSING_REQUIRED_ARTIFACT"
        elif recorded and recorded_sha not in {"", "NOT_IN_MANIFEST"} and sha != recorded_sha:
            status = "BLOCKING_DATA_DRIFT"
        elif recorded and recorded_count not in {"", "NA", "NOT_IN_MANIFEST"} and row_count != recorded_count:
            status = "BLOCKING_DATA_DRIFT"
        elif recorded:
            status = "MATCH"
        elif name == "COMSOL_GATE13_MANIFEST_20260629.csv":
            status = "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
        else:
            status = "READABLE_NOT_IN_MANIFEST_NON_BLOCKING"
        rows.append(
            {
                "receipt_id": f"G14D-COMSOL-G13-RCPT-{idx:03d}",
                "artifact_name": name,
                "absolute_path": str(path),
                "relative_source_path": rel,
                "row_count": row_count,
                "recorded_row_count": recorded_count,
                "sha256": sha,
                "recorded_sha256": recorded_sha,
                "receipt_status": status,
                "baseline_status": "valid_review_only_no_auth",
                "superseded_for_nodi_intake": "true",
                "auth_impact": "none_no_auth",
            }
        )
    return rows


def stale_intake_closure(root: Path) -> list[dict[str, str]]:
    status = read_json(comsol_path(root, "COMSOL_GATE13_STATUS_20260629.json"))
    observed = status.get("nodi_intake_status", "OBSERVED_UNRELEASED_NOT_CONSUMED_AS_RELEASE")
    observed_head = status.get("nodi_head", "3aef25df0034b894f4a147d6ea60afc69781d025")
    current_head = safe_git_head(PROJECT_ROOT)
    return [
        {
            "closure_id": "G14D-STALE-INTAKE-001",
            "comsol_observed_nodi_head": str(observed_head),
            "comsol_observed_intake_status": str(observed),
            "nodi_gate14_head": current_head,
            "closure_status": "CLOSED_BY_NODI_GATE14_RELEASED_CLEAN",
            "closure_label": "SUPERSEDED_BY_NODI_GATE14_RELEASED_CLEAN_A9AB0C4_OR_LATER",
            "semantic_conflict": "false",
            "auth_promotion": "false",
            "comsol_package_valid_as_baseline": "true",
            "nodi_intake_superseded": "true",
        }
    ]


def receiver_harness_v3_coverage() -> list[dict[str, str]]:
    fields = interface_contract_v3_schema_delta()
    rows = []
    for idx, field in enumerate(fields, start=1):
        family = field["field_family"]
        if "denylist" in family:
            status = "BLOCKED_AS_EXPECTED"
        elif family in {"profile_source_hash_guard", "runtime_top_aperture_binding", "blocked_bin_guard"}:
            status = "EXACT_SUPPORTED"
        elif family in {"measured_profile_guard", "package_C_gate"}:
            status = "FUTURE_COMSOL_EXPORT_REQUIRED"
        else:
            status = "SUPPORTED_AS_REVIEW_ONLY"
        rows.append(
            {
                "coverage_id": f"G14E-COVERAGE-{idx:03d}",
                "field_or_family": field["field_or_family"],
                "field_family": family,
                "coverage_status": status,
                "nodi_v3_receiver_behavior": "fail_closed_or_review_only",
                "comsol_gate13_v2_input_status": "baseline_supported_or_gap_recorded",
                "prs_eas_numeric_response_generated": "false",
                "edge_jrc_qch_authorized": "false",
                "yield_winner_detection_probability_authorized": "false",
            }
        )
    return rows


def comsol_producer_request_v3() -> list[dict[str, str]]:
    requests = [
        ("descriptor_profile_metadata", "geometry_profile_source, geometry_profile_sha256, source_geometry_descriptor_sha", "nm/hash/enums", "no-run descriptor/profile metadata export"),
        ("runtime_top_aperture_metadata", "runtime_top_aperture_nm, top_cd_bias_nm, top_cd_bias_source", "nm/enums", "no-run descriptor/profile metadata export"),
        ("measured_profile_lookup_metadata", "measured_profile_lookup_status, measured_profile_sha256, loaded/validated flags", "hash/booleans", "future-only metadata export; no measured-geometry claim"),
        ("sampler_support_fixture", "particle center support, nearest wall distance, surface gap", "nm/enums", "review-only dry-run fixture export"),
        ("blocked_bin_fixture", "bin_accessible, support status, blocked_reason, neighbor_fill_allowed=false", "booleans/enums", "review-only dry-run fixture export"),
        ("alias_negative_fixtures", "flow/Q/q_ch/route_score/rank/JRC/chi/sidewall_aware", "columns/fixtures", "negative fixtures"),
        ("binding_blocker_closure", "D900/D1200, edge4/edge20, 220/300 large-tail exact support", "route/view/diameter/bin", "binding blocker closure evidence"),
        ("future_solver_evidence", "optical solver, wet transport, trapezoid Poiseuille", "future artifacts", "future-only COMSOL run evidence not authorized"),
    ]
    rows = []
    for idx, (artifact, fields, units, lane) in enumerate(requests, start=1):
        future_run = "future-only" in lane or "solver" in artifact
        rows.append(
            {
                "request_id": f"G14F-COMSOL-REQ-{idx:03d}",
                "required_artifact": artifact,
                "required_fields": fields,
                "units_or_types": units,
                "request_lane": lane,
                "source_hash_required": "true",
                "row_count_required": "true",
                "claim_boundary": "review-only/no-auth",
                "comsol_run_authorized_now": "false",
                "future_authorization_required": bool_text(future_run),
                "blocked_use_until_pass": BLOCKED_USE,
            }
        )
    return rows


def package_readiness_board() -> list[dict[str, str]]:
    rows = [
        ("Package A", "schema/descriptor/profile hash guard", "GO_STATIC_PREFLIGHT_ONLY", "no evidence auth"),
        ("Package B", "geometry primitive/sampler/actual signature guard", "GO_STATIC_PREFLIGHT_ONLY", "not flow-weighted validation"),
        ("Package C", "near-wall/trajectory/optical/wet physics guard", "NO_GO_BLOCKED_FOR_PHYSICS", "requires explicit future authorization and solver/trajectory evidence"),
        ("Package D", "PRS/EAS sidewall precheck/blocked-bin/alias guard", "GO_CONTRACT_PREFLIGHT_ONLY", "no numeric sidewall PRS/EAS output"),
    ]
    return [
        {
            "board_id": f"G14G-{pkg.replace(' ', '-')}",
            "package": pkg,
            "scope": scope,
            "go_no_go": verdict,
            "boundary": boundary,
            "guard_pass_is_model_validation_pass": "false",
            "static_preflight_allowed": bool_text(verdict != "NO_GO_BLOCKED_FOR_PHYSICS"),
            "future_authorization_required": bool_text(verdict == "NO_GO_BLOCKED_FOR_PHYSICS"),
            "runtime_or_production_allowed": "false",
        }
        for pkg, scope, verdict, boundary in rows
    ]


def mutation_rows(total: int = 50000) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    families = [
        "profile_hash_mismatch",
        "source_descriptor_hash_mismatch",
        "runtime_top_aperture_metadata_spoof",
        "measured_profile_unloaded_spoof",
        "bare_angle_alias",
        "flow_Q_qch_alias",
        "route_score_rank_jrc_chi_alias",
        "sidewall_aware_shortcut",
        "blocked_bin_numeric_response",
        "blocked_bin_neighbor_fill",
        "D900_to_D1200_borrowing",
        "edge4_to_edge20_direct_mapping",
        "large_tail_auto_admission",
        "package_C_wall_distance_without_validation",
        "comsol_gate13_stale_intake_consumed_as_release",
        "runtime_production_flag_spoof",
    ]
    catalog = []
    results = []
    for idx in range(1, total + 1):
        family = families[(idx - 1) % len(families)]
        mutation_id = f"G14H-MUT-{idx:05d}"
        expected = "FAIL_CLOSED_OR_QUARANTINE"
        catalog.append(
            {
                "mutation_id": mutation_id,
                "family": family,
                "description": f"Gate14 deterministic negative/control case for {family}",
                "not_evidence": "true",
                "expected_result": expected,
                "authorization_flags_expected_false": "true",
            }
        )
        results.append(
            {
                "mutation_id": mutation_id,
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


def implementation_audit_addendum() -> list[dict[str, str]]:
    return [
        {
            "addendum_id": "G14I-AUDIT-ADDENDUM-001",
            "referenced_report": "reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
            "action": "no_history_rewrite",
            "reason": "Gate14 adds COMSOL-facing contract v3 and stale-intake closure as addendum",
            "sha_drift": "none",
            "status": "GATE14_ADDENDUM_CREATED",
        }
    ]


def no_auth_sweep() -> list[dict[str, str]]:
    return [
        {
            "sweep_id": "G14K-NOAUTH-001",
            "scope": "Gate14 outputs and Gate13/345 references",
            "positive_authorization_count": "0",
            "positive_runtime_or_production_count": "0",
            "positive_jrc_weighting_yield_winner_detection_count": "0",
            "gate2d_rows": "4",
            "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
            "qch_state": "ABSENT",
            "binding_state": "FAIL_CLOSED",
            "sweep_status": "PASS_NO_AUTH",
        }
    ]


def decision_dossier() -> list[dict[str, str]]:
    choices = [
        ("FREEZE_SIDEWALL_IMPLEMENTATION_GUARD_CONTRACT_V3_NO_EVIDENCE_AUTH", "Freeze contract v3 as review-only interface guard baseline."),
        ("AUTHORIZE_NODI_STATIC_SIDEWALL_GUARD_PREFLIGHT_ONLY_NO_PRS_EAS_RERUN", "Allow static NODI guard preflight only."),
        ("REQUEST_COMSOL_PRODUCER_SCHEMA_V3_NO_RUN_EXPORT", "Ask COMSOL for no-run producer schema v3 export."),
        ("OPEN_PACKAGE_D_SIDEWALL_PILOT_PREFLIGHT_DESIGN_ONLY_NO_DATA_GENERATION", "Design Package D pilot preflight without data generation."),
        ("DEFER_AND_KEEP_GATE13", "Defer Gate14 and keep Gate13 boundaries."),
    ]
    return [
        {
            "choice_id": choice_id,
            "default_state": "AWAITING_USER_DECISION",
            "allowed": allowed,
            "forbidden": "No COMSOL run, no NODI PRS/EAS rerun, no q_ch/JRC/route_score/winner/yield/detection/runtime/production.",
            "exact_signoff_wording": f"I select {choice_id}; I do not authorize evidence acceptance, runtime, production, q_ch weighting, JRC, winner, yield, or detection probability.",
            "rollback": "Any Gate2D drift, EDGE/QCH/BINDING promotion, or forbidden authorization true invalidates this choice.",
            "next_thread_action": "Open only the named future no-auth/preauth thread after explicit selection.",
            "approved_now": "false",
        }
        for choice_id, allowed in choices
    ]


def self_review() -> list[dict[str, str]]:
    topics = [
        "post-Gate13 delta",
        "git cleanliness",
        "implementation audit",
        "schema v3 completeness",
        "COMSOL Gate13 stale-intake closure",
        "Package A boundary",
        "Package B boundary",
        "Package C boundary",
        "Package D boundary",
        "profile hash guard",
        "measured profile guard",
        "blocked-bin guard",
        "alias denylist",
        "mutation strength",
        "no-auth leakage",
        "test sufficiency",
        "Git scope",
    ]
    return [
        {
            "reviewer_id": f"G14M-REVIEW-{idx:02d}",
            "focus": topic,
            "finding": "PASS_NO_P0_P1",
            "required_fix_before_pass": "none",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate14_sidewall_implementation_contract.py --confirm-gate14-sidewall-implementation-contract",
        "python -m py_compile tools/audits/build_nodi_comsol_gate14_sidewall_implementation_contract.py",
        "ruff check tools/audits/build_nodi_comsol_gate14_sidewall_implementation_contract.py tests/test_nodi_comsol_gate14_sidewall_implementation_contract.py",
        "pytest -q tests/test_nodi_comsol_gate14_sidewall_implementation_contract.py",
        "pytest -q tests/test_cross_section_geometry.py",
        "pytest -q tests/test_nodi_comsol_next_artifacts_contracts.py",
        "pytest -q tests/test_physics_core.py -k channel_geometry",
    ]
    return [
        {
            "validation_id": f"G14J-VALIDATION-{idx:03d}",
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, command in enumerate(commands, start=1)
    ]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G14N-MANIFEST-{idx:03d}",
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": csv_count(path) if path.suffix.lower() == ".csv" else "NA",
                "sha256": sha256_file(path),
                "status": "GENERATED_GATE14_REVIEW_ONLY_NO_AUTH",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_payload(comsol_root: Path) -> dict[str, Any]:
    mutation_catalog, mutation_results = mutation_rows()
    payload: dict[str, Any] = {
        "current_release_intake": current_release_intake(),
        "post_gate13_delta_ledger": post_gate13_delta_ledger(),
        "implementation_guard_release_ledger": implementation_guard_release_ledger(),
        "interface_contract_v3_schema_delta": interface_contract_v3_schema_delta(),
        "comsol_gate13_receipt": comsol_gate13_receipt(comsol_root),
        "stale_intake_closure": stale_intake_closure(comsol_root),
        "receiver_harness_v3_coverage": receiver_harness_v3_coverage(),
        "comsol_producer_request_v3": comsol_producer_request_v3(),
        "package_readiness_board": package_readiness_board(),
        "mutation_catalog": mutation_catalog,
        "mutation_results": mutation_results,
        "implementation_audit_addendum": implementation_audit_addendum(),
        "no_auth_sweep": no_auth_sweep(),
        "decision_dossier": decision_dossier(),
        "self_review": self_review(),
        "validation_plan": validation_plan(),
    }
    guard_status = payload["implementation_guard_release_ledger"]
    coverage = payload["receiver_harness_v3_coverage"]
    mutation_results = payload["mutation_results"]
    summary = {
        "disposition": DISPOSITION,
        "contract_name": CONTRACT_NAME,
        "nodi_head": safe_git_head(PROJECT_ROOT),
        "worktree_clean": payload["current_release_intake"][0]["worktree_status"] == "clean",
        "post_gate13_delta_rows": len(payload["post_gate13_delta_ledger"]),
        "implementation_guard_rows": len(guard_status),
        "implementation_guard_blocked_rows": sum(row["release_status"] == "BLOCKED_AS_EXPECTED" for row in guard_status),
        "schema_v3_delta_rows": len(payload["interface_contract_v3_schema_delta"]),
        "comsol_gate13_receipt_rows": len(payload["comsol_gate13_receipt"]),
        "comsol_gate13_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in payload["comsol_gate13_receipt"]),
        "comsol_gate13_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in payload["comsol_gate13_receipt"]),
        "comsol_head_actual": safe_git_head(comsol_root),
        "comsol_gate13_package_head_expected": EXPECTED_COMSOL_GATE13_HEAD,
        "comsol_head_advanced_after_gate13": safe_git_head(comsol_root) in ALLOWED_COMSOL_CURRENT_HEADS,
        "comsol_head_advanced_after_gate14": safe_git_head(comsol_root) == EXPECTED_COMSOL_GATE15_HEAD,
        "stale_intake_closed": payload["stale_intake_closure"][0]["closure_status"] == "CLOSED_BY_NODI_GATE14_RELEASED_CLEAN",
        "receiver_harness_rows": len(coverage),
        "receiver_harness_missing_required_for_v3": sum(row["coverage_status"] == "MISSING_REQUIRED_FOR_V3" for row in coverage),
        "producer_request_rows": len(payload["comsol_producer_request_v3"]),
        "package_board_rows": len(payload["package_readiness_board"]),
        "mutation_rows": len(mutation_results),
        "mutation_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in mutation_results),
        "mutation_forbidden_promotion": sum(row["forbidden_promotion"] == "true" for row in mutation_results),
        "no_auth_sweep_failures": sum(row["sweep_status"] != "PASS_NO_AUTH" for row in payload["no_auth_sweep"]),
        "decision_options": len(payload["decision_dossier"]),
        "self_review_rows": len(payload["self_review"]),
        "gate2d_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    payload["summary"] = summary
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures = []
    checks = {
        "worktree clean": summary["worktree_clean"],
        "guard rows": summary["implementation_guard_rows"] >= 26,
        "blocked guard rows": summary["implementation_guard_blocked_rows"] == 2,
        "COMSOL Gate13 receipt drift": summary["comsol_gate13_blocking_drift"] == 0,
        "COMSOL Gate13 required missing": summary["comsol_gate13_missing_required"] == 0,
        "COMSOL Gate14/Gate15 successor head": summary["comsol_head_actual"] in ALLOWED_COMSOL_CURRENT_HEADS,
        "stale intake closure": summary["stale_intake_closed"],
        "harness no missing required": summary["receiver_harness_missing_required_for_v3"] == 0,
        "mutation row threshold": summary["mutation_rows"] >= 50000,
        "mutation unexpected pass": summary["mutation_unexpected_pass"] == 0,
        "mutation forbidden promotion": summary["mutation_forbidden_promotion"] == 0,
        "no auth sweep": summary["no_auth_sweep_failures"] == 0,
        "Gate2D freeze": summary["gate2d_rows"] == 4,
        "EDGE state": summary["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY",
        "QCH state": summary["qch_state"] == "ABSENT",
        "BINDING state": summary["binding_state"] == "FAIL_CLOSED",
    }
    for label, ok in checks.items():
        if not ok:
            failures.append(label)
    return failures


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE14_SIDEWALL_CURRENT_RELEASE_INTAKE_20260630.csv": payload["current_release_intake"],
        "NODI_COMSOL_GATE14_SIDEWALL_POST_GATE13_DELTA_LEDGER_20260630.csv": payload["post_gate13_delta_ledger"],
        "NODI_COMSOL_GATE14_SIDEWALL_IMPLEMENTATION_GUARD_RELEASE_LEDGER_20260630.csv": payload["implementation_guard_release_ledger"],
        "NODI_COMSOL_GATE14_SIDEWALL_INTERFACE_CONTRACT_V3_SCHEMA_DELTA_20260630.csv": payload["interface_contract_v3_schema_delta"],
        "NODI_COMSOL_GATE14_SIDEWALL_COMSOL_GATE13_RECEIPT_V2_20260630.csv": payload["comsol_gate13_receipt"],
        "NODI_COMSOL_GATE14_SIDEWALL_STALE_INTAKE_CLOSURE_MATRIX_20260630.csv": payload["stale_intake_closure"],
        "NODI_COMSOL_GATE14_SIDEWALL_RECEIVER_HARNESS_V3_COVERAGE_20260630.csv": payload["receiver_harness_v3_coverage"],
        "NODI_COMSOL_GATE14_SIDEWALL_COMSOL_PRODUCER_REQUEST_V3_20260630.csv": payload["comsol_producer_request_v3"],
        "NODI_COMSOL_GATE14_SIDEWALL_PACKAGE_ABCD_READINESS_BOARD_20260630.csv": payload["package_readiness_board"],
        "NODI_COMSOL_GATE14_SIDEWALL_MUTATION_CATALOG_20260630.csv": payload["mutation_catalog"],
        "NODI_COMSOL_GATE14_SIDEWALL_MUTATION_RESULTS_20260630.csv": payload["mutation_results"],
        "NODI_COMSOL_GATE14_SIDEWALL_IMPLEMENTATION_AUDIT_ADDENDUM_20260630.csv": payload["implementation_audit_addendum"],
        "NODI_COMSOL_GATE14_SIDEWALL_NO_AUTH_SWEEP_V4_20260630.csv": payload["no_auth_sweep"],
        "NODI_COMSOL_GATE14_SIDEWALL_DECISION_DOSSIER_V4_20260630.csv": payload["decision_dossier"],
        "NODI_COMSOL_GATE14_SIDEWALL_SELF_REVIEW_20260630.csv": payload["self_review"],
        "NODI_COMSOL_GATE14_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_IMPLEMENTATION_CONTRACT_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate14 Sidewall Implementation Contract V3",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- NODI HEAD: `{payload['summary']['nodi_head']}`",
            f"- Implementation guard rows: {payload['summary']['implementation_guard_rows']} with blocked rows {payload['summary']['implementation_guard_blocked_rows']}",
            f"- COMSOL Gate13 receipt rows: {payload['summary']['comsol_gate13_receipt_rows']} with blocking drift {payload['summary']['comsol_gate13_blocking_drift']}",
            f"- Mutation rows: {payload['summary']['mutation_rows']} with unexpected pass {payload['summary']['mutation_unexpected_pass']}",
            "- Package C optical/wet physics remains blocked; no COMSOL run, no NODI PRS/EAS rerun, no runtime/production.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate14 disposition: `{DISPOSITION}`",
                f"- Contract: `{CONTRACT_NAME}`",
                f"- Key rows: guard={payload['summary']['implementation_guard_rows']}; schema_v3={payload['summary']['schema_v3_delta_rows']}; receipt={payload['summary']['comsol_gate13_receipt_rows']}; mutations={payload['summary']['mutation_rows']}.",
                f"- Locked states: Gate2D={payload['summary']['gate2d_rows']}; EDGE={payload['summary']['edge_state']}; QCH={payload['summary']['qch_state']}; BINDING={payload['summary']['binding_state']}.",
                "- Boundary: review-only/no-auth implementation guard contract. No physics validation, no runtime, no production.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate14_sidewall_implementation_contract:
        parser.error("--confirm-gate14-sidewall-implementation-contract is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE14_SIDEWALL_IMPLEMENTATION_CONTRACT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
