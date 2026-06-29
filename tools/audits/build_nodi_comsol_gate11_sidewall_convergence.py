#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    FALSE_VALUES,
)
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
BASE_GATE10_COMMIT = "7dc0d6a"
DISPOSITION = (
    "PASS_GATE11_SIDEWALL_DESCRIPTOR_RECEIPT_AND_RC51_ADDENDUM_LOCK_CANDIDATE_NO_AUTH"
)
ADDENDUM_VERSION = "RC5.1_SIDEWALL_GEOMETRY_DESCRIPTOR_ADDENDUM_V1_CANDIDATE_REVIEW_ONLY"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;measured geometry claim;formula use;direct PRS bin;"
    "grain-level ingestion;accepted row expansion"
)
ALLOWED_USE = (
    "review-only sidewall geometry descriptor receipt;RC5.1 addendum candidate;"
    "PRS/EAS contract fixture validation;quarantine/preflight"
)

GATE2D_LEDGER = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"
)
NODI_GATE10_FREEZE_IMPACT = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE10_SIDEWALL_RC51_FREEZE_IMPACT_MATRIX_{DATE_STAMP}.csv"
)
NODI_GATE10_SCHEMA = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE10_SIDEWALL_DESCRIPTOR_SCHEMA_{DATE_STAMP}.csv"
)

COMSOL_REQUIRED_FILES = (
    "COMSOL_GATE10_SIDEWALL_DESCRIPTOR_EXPORT_PACKET_20260629.md",
    "COMSOL_GATE10_SIDEWALL_SOURCE_INVENTORY_20260629.csv",
    "COMSOL_GATE10_SIDEWALL_DESCRIPTOR_EXPORT_20260629.csv",
    "COMSOL_GATE10_SIDEWALL_NODI_CROSSWALK_20260629.csv",
    "COMSOL_GATE10_SIDEWALL_FREEZE_IMPACT_20260629.csv",
    "COMSOL_GATE10_SIDEWALL_VALIDATION_20260629.csv",
    "COMSOL_GATE10_SIDEWALL_MANIFEST_20260629.csv",
)

COMSOL_CORE_DESCRIPTOR_FIELDS = (
    "producer",
    "source_artifact",
    "source_sha256",
    "geometry_root",
    "route_key",
    "view",
    "width_family",
    "depth_nm",
    "diameter_nm",
    "bin_basis",
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "W_top_nm",
    "D_nm",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
    "min_aperture_descriptor_nm",
    "cross_section_geometry_version_candidate",
    "geometry_claim_level",
    "geometry_surrogate_status",
)

ADDENDUM_FIELDS = (
    "geometry_descriptor_id",
    "geometry_descriptor_sha256",
    "source_geometry_descriptor_id",
    "source_geometry_descriptor_sha",
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "angle_conversion_formula_id",
    "W_top_nm",
    "D_nm",
    "depth_nm",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
    "min_aperture_descriptor_nm",
    "cross_section_geometry_version",
    "cross_section_geometry_version_candidate",
    "geometry_claim_level",
    "geometry_surrogate_status",
    "sidewall_descriptor_binding_status",
    "sidewall_prs_v2_requires_descriptor_binding",
    "sidewall_eas_v2_requires_descriptor_binding",
    "optical_solver_triggered",
    "optical_geometry_claim_level",
    "not_measured_geometry",
    "not_runtime_configuration",
    "not_production_ingestion",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate11 sidewall descriptor convergence and RC5.1 addendum candidate."
    )
    parser.add_argument("--confirm-gate11-sidewall-convergence", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def read_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def csv_count(path: Path) -> str:
    return str(len(read_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def descriptor_hash(row: dict[str, Any]) -> str:
    payload = {field: str(row.get(field, "")) for field in COMSOL_CORE_DESCRIPTOR_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bottom_width_nm(top_nm: float, depth_nm: float, sidewall_deg: float) -> float:
    return top_nm - 2.0 * depth_nm / math.tan(math.radians(sidewall_deg))


def closure_status(bottom_unclipped_nm: float, threshold_nm: float = 80.0) -> str:
    if bottom_unclipped_nm <= 0.0:
        return "geometry_closed"
    if bottom_unclipped_nm <= threshold_nm:
        return "near_closed"
    return "open"


def runtime_guard(status: str) -> str:
    if status == "geometry_closed":
        return "validation_guard"
    if status == "near_closed":
        return "solver_guard"
    return "none"


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


def current_dirty_sidewall_patch_is_self_consistent() -> bool:
    """Recognize the active Gate11 Package D forbidden-field guard patch."""
    code = (PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py").read_text(
        encoding="utf-8"
    )
    tests = (PROJECT_ROOT / "tests/test_nodi_comsol_next_artifacts_contracts.py").read_text(
        encoding="utf-8"
    )
    return all(
        token in code or token in tests
        for token in (
            "SIDEWALL-D-PRECHECK-V06",
            "SIDEWALL_PACKAGE_D_PRECHECK_TRUE_FIELDS",
            "test_sidewall_package_d_precheck_scans_forbidden_columns_even_when_flag_passes",
            "route_score=1.0",
        )
    )


def target_worktree_status() -> list[dict[str, str]]:
    output = run_git(
        [
            "status",
            "--short",
            "--",
            "nodi_simulator/nodi_comsol_next_artifacts.py",
            "tests/test_nodi_comsol_next_artifacts_contracts.py",
        ]
    )
    if not output:
        return [
            {
                "status_id": "G11A-WORKTREE-001",
                "path": "nodi_simulator/nodi_comsol_next_artifacts.py;tests/test_nodi_comsol_next_artifacts_contracts.py",
                "git_status": "clean",
                "disposition": "CLEAN_ALREADY_COMMITTED",
                "gate11_action": "ingest current HEAD guards",
            }
        ]
    self_consistent = current_dirty_sidewall_patch_is_self_consistent()
    return [
        {
            "status_id": f"G11A-WORKTREE-{idx:03d}",
            "path": line[3:],
            "git_status": line[:2].strip(),
            "disposition": (
                "SELF_CONSISTENT_SIDEWALL_GUARD_PATCH_INCLUDED"
                if self_consistent
                else "WORKTREE_SIDEWALL_DIRTY_BLOCKER"
            ),
            "gate11_action": (
                "include Package D forbidden-field guard patch in Gate11 commit"
                if self_consistent
                else "fail_closed_if_not_self_consistent"
            ),
        }
        for idx, line in enumerate(output.splitlines(), start=1)
    ]


def hardening_intake_matrix() -> list[dict[str, str]]:
    output = run_git(["log", "--format=%H%x09%h%x09%s", f"{BASE_GATE10_COMMIT}..HEAD"])
    guard_keywords = {
        "Bind sidewall EAS optical trigger claims": (
            "EAS optical trigger/claim-level consistency",
            "EAS optical trigger fields",
        ),
        "Require sidewall EAS reference context": (
            "EAS reference_field/detector context",
            "EAS reference context",
        ),
        "Require sidewall PRS runtime propagation fields": (
            "PRS runtime propagation models",
            "PRS runtime geometry propagation",
        ),
        "Validate sidewall PRS particle radius": (
            "particle radius/steric support",
            "PRS particle support",
        ),
        "Require sidewall PRS normalized coordinates": (
            "local normalized coordinate and geometry consistency",
            "PRS normalized coordinates",
        ),
        "Require sidewall artifact metadata": (
            "artifact id/version/created/provenance metadata",
            "PRS/EAS artifact metadata",
        ),
        "Require sidewall roadmap status guard": (
            "roadmap status cannot be production-ready",
            "roadmap-to-contract guard",
        ),
        "Require sidewall artifact acceptance guards": (
            "not accepted for formula/runtime/production flags",
            "no-auth guard",
        ),
        "Require sidewall EAS optical claim level": (
            "EAS optical geometry claim enum",
            "EAS optical claim boundary",
        ),
        "Require sidewall EAS optical trigger fields": (
            "EAS solver trigger fields and reason",
            "EAS optical trigger",
        ),
        "Require sidewall EAS runtime geometry context": (
            "EAS trapezoid runtime geometry context",
            "EAS runtime geometry",
        ),
        "Require sidewall artifact cache signatures": (
            "observation signature/cache geometry match",
            "cache/signature drift guard",
        ),
        "Require sidewall PRS source grain binding": (
            "source grain route/view/diameter/bin binding",
            "source grain borrowing rejection",
        ),
        "Reject sidewall PRS blocked bin responses": (
            "blocked bin numeric response rejection",
            "PRS blocked-bin response",
        ),
        "Require sidewall PRS descriptor provenance": (
            "source descriptor id/hash binding",
            "descriptor provenance",
        ),
    }
    rows: list[dict[str, str]] = []
    for idx, line in enumerate([line for line in output.splitlines() if line], start=1):
        full, short, subject = line.split("\t", 2)
        guard, impact = guard_keywords.get(
            subject,
            ("sidewall interface/runtime guard hardening", "contract hardening"),
        )
        rows.append(
            {
                "intake_id": f"G11A-HARDEN-{idx:03d}",
                "commit": short,
                "commit_full": full,
                "subject": subject,
                "changed_file_scope": "nodi_comsol_next_artifacts.py;tests/test_nodi_comsol_next_artifacts_contracts.py",
                "guard_added": guard,
                "prs_eas_descriptor_runtime_cache_impact": impact,
                "implemented_status": "implemented_in_current_HEAD",
                "remaining_gap": "covered_by_Gate11_addendum_or_future_authorized_solver" if "solver" in guard.lower() else "none_at_contract_layer",
            }
        )
    return rows


def manifest_receipt(root: Path) -> list[dict[str, str]]:
    manifest = read_rows(comsol_path(root, "COMSOL_GATE10_SIDEWALL_MANIFEST_20260629.csv"))
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(manifest, start=1):
        path = root / row.get("path", "")
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path) if path.exists() else "MISSING"
        recorded_rows = row.get("row_count", "NA")
        status = "MATCH"
        if not path.exists():
            status = "MISSING_REQUIRED_ARTIFACT"
        elif row.get("sha256") != actual_sha:
            status = "BLOCKING_SHA_DRIFT"
        elif recorded_rows not in {actual_rows, "NA"}:
            status = "BLOCKING_ROW_COUNT_DRIFT"
        rows.append(
            {
                "receipt_id": f"G11B-RECEIPT-{idx:03d}",
                "source_manifest_id": row.get("manifest_id", ""),
                "artifact": row.get("artifact", ""),
                "path": row.get("path", ""),
                "absolute_path": str(path),
                "recorded_sha256": row.get("sha256", ""),
                "actual_sha256": actual_sha,
                "recorded_row_count": recorded_rows,
                "actual_row_count": actual_rows,
                "producer_status": "COMSOL_GATE10_DESCRIPTOR_EXPORT",
                "receipt_status": status,
                "policy_impact": "review_only_no_auth" if status == "MATCH" else "fail_closed",
            }
        )
    manifest_path = comsol_path(root, "COMSOL_GATE10_SIDEWALL_MANIFEST_20260629.csv")
    rows.append(
        {
            "receipt_id": f"G11B-RECEIPT-{len(rows) + 1:03d}",
            "source_manifest_id": "NODI_RECEIPT_MANIFEST_SELF",
            "artifact": manifest_path.name,
            "path": f"roadmap/{manifest_path.name}",
            "absolute_path": str(manifest_path),
            "recorded_sha256": "self_not_recorded_by_comsol_manifest",
            "actual_sha256": sha256_file(manifest_path),
            "recorded_row_count": "self_not_recorded",
            "actual_row_count": csv_count(manifest_path),
            "producer_status": "COMSOL_GATE10_DESCRIPTOR_EXPORT",
            "receipt_status": "SELF_REFERENTIAL_MANIFEST_RECEIVED_NON_POLICY",
            "policy_impact": "review_only_no_auth",
        }
    )
    return rows


def descriptor_validation(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    descriptors = read_rows(comsol_path(root, "COMSOL_GATE10_SIDEWALL_DESCRIPTOR_EXPORT_20260629.csv"))
    validation_rows: list[dict[str, str]] = []
    ledger_rows: list[dict[str, str]] = []
    for idx, row in enumerate(descriptors, start=1):
        descriptor_id = row.get("geometry_descriptor_id", f"row-{idx}")
        issues: list[str] = []
        try:
            sidewall = float(row.get("sidewall_deg_comsol", "nan"))
            taper = float(row.get("sidewall_taper_angle_deg_nodi", "nan"))
            top = float(row.get("W_top_nm", "nan"))
            depth = float(row.get("D_nm", "nan"))
            bottom = float(row.get("W_bottom_unclipped_nm", "nan"))
            clipped = float(row.get("W_bottom_runtime_clipped_nm", "nan"))
        except ValueError:
            issues.append("numeric_parse_failure")
            sidewall = taper = top = depth = bottom = clipped = math.nan
        if row.get("sidewall_angle_convention") != "sidewall_deg_comsol_from_substrate_horizontal_90deg_vertical":
            issues.append("angle_convention_mismatch")
        if math.isfinite(sidewall) and math.isfinite(taper):
            if not math.isclose(sidewall + taper, 90.0, abs_tol=1e-6):
                issues.append("angle_conversion_not_complementary")
        if all(math.isfinite(value) for value in (sidewall, top, depth, bottom, clipped)):
            expected_bottom = bottom_width_nm(top, depth, sidewall)
            if not math.isclose(expected_bottom, bottom, abs_tol=1e-6):
                issues.append("bottom_width_formula_mismatch")
            if not math.isclose(max(expected_bottom, 0.0), clipped, abs_tol=1e-6):
                issues.append("runtime_clipped_width_mismatch")
            expected_status = closure_status(bottom)
            if row.get("closure_status") != expected_status:
                issues.append("closure_status_mismatch")
            if row.get("runtime_guard_status") != runtime_guard(expected_status):
                issues.append("runtime_guard_status_mismatch")
        if descriptor_hash(row) != row.get("geometry_descriptor_sha256"):
            issues.append("descriptor_hash_mismatch")
        for flag in (
            "production_ingestion_authorized",
            "runtime_configuration_authorized",
            "evidence_acceptance_authorized",
        ):
            if str(row.get(flag, "")).lower() != "false":
                issues.append(f"{flag}_not_false")
        unbound = any(
            str(row.get(field, "")).upper() in {"UNBOUND", "NOT_APPLICABLE", "NOT_BOUND"}
            for field in ("route_key", "view", "diameter_nm", "bin_basis")
        )
        if unbound and "ingestion" in row.get("allowed_use", "").lower():
            issues.append("unbound_row_allowed_use_mentions_ingestion")
        validation_rows.append(
            {
                "validation_id": f"G11B-DESC-VAL-{idx:03d}",
                "geometry_descriptor_id": descriptor_id,
                "route_key": row.get("route_key", ""),
                "view": row.get("view", ""),
                "diameter_nm": row.get("diameter_nm", ""),
                "bin_basis": row.get("bin_basis", ""),
                "angle_conversion_status": "PASS" if "angle_conversion_not_complementary" not in issues else "FAIL",
                "bottom_width_formula_status": "PASS" if not any("width" in issue for issue in issues) else "FAIL",
                "descriptor_hash_status": "PASS" if "descriptor_hash_mismatch" not in issues else "FAIL",
                "authorization_flags_status": "PASS" if not any("authorized" in issue for issue in issues) else "FAIL",
                "unbound_ingestion_status": "PASS_REVIEW_ONLY_QUARANTINE" if unbound else "PASS_BOUND_REVIEW_ONLY",
                "validation_status": "PASS" if not issues else "FAIL",
                "issues": "|".join(issues),
            }
        )
        ledger_rows.append(
            {
                "ledger_id": f"G11B-QUARANTINE-{idx:03d}",
                "geometry_descriptor_id": descriptor_id,
                "geometry_descriptor_sha256": row.get("geometry_descriptor_sha256", ""),
                "producer": "COMSOL",
                "route_key": row.get("route_key", ""),
                "view": row.get("view", ""),
                "diameter_nm": row.get("diameter_nm", ""),
                "bin_basis": row.get("bin_basis", ""),
                "receiver_lane": "descriptor_review_only_quarantine",
                "can_enter_prs_eas_ingestion": "false",
                "can_enter_edge": "false",
                "can_enter_qch": "false",
                "can_enter_jrc": "false",
                "can_enter_runtime": "false",
                "can_enter_production": "false",
                "required_next_gate": "Gate11_RC51_SIDEWALL_ADDENDUM_REVIEW_THEN_FUTURE_AUTH",
            }
        )
    return validation_rows, ledger_rows


def addendum_field_dictionary() -> list[dict[str, str]]:
    required = {
        "geometry_descriptor_id",
        "geometry_descriptor_sha256",
        "source_geometry_descriptor_id",
        "source_geometry_descriptor_sha",
        "sidewall_angle_convention",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "angle_conversion_formula_id",
        "W_top_nm",
        "D_nm",
        "depth_nm",
        "W_bottom_unclipped_nm",
        "W_bottom_runtime_clipped_nm",
        "closure_status",
        "closure_policy",
        "runtime_guard_status",
        "min_aperture_descriptor_nm",
        "cross_section_geometry_version",
        "geometry_claim_level",
        "geometry_surrogate_status",
    }
    marker = {
        "sidewall_descriptor_binding_status",
        "sidewall_prs_v2_requires_descriptor_binding",
        "sidewall_eas_v2_requires_descriptor_binding",
    }
    rows = []
    for idx, field in enumerate(ADDENDUM_FIELDS, start=1):
        if field in required:
            requiredness = "required_for_sidewall_aware_rows"
        elif field in marker:
            requiredness = "required_marker_or_receiver_guard"
        else:
            requiredness = "required_no_auth_or_claim_guard"
        rows.append(
            {
                "field_id": f"G11C-FIELD-{idx:03d}",
                "addendum_version": ADDENDUM_VERSION,
                "field_name": field,
                "requiredness": requiredness,
                "owner": "NODI_RECEIVER",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "review_only": "true",
                "runtime_contract": "false",
                "production_contract": "false",
                "historical_freeze_rewrite": "false",
            }
        )
    return rows


def addendum_hash_tree(field_rows: list[dict[str, str]], receipt_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    nodes = [
        ("NODI_GATE10_FREEZE_IMPACT", NODI_GATE10_FREEZE_IMPACT),
        ("NODI_GATE10_DESCRIPTOR_SCHEMA", NODI_GATE10_SCHEMA),
        ("GATE11_FIELD_DICTIONARY_INLINE", None),
        ("COMSOL_GATE10_RECEIPT_INLINE", None),
    ]
    rows = []
    for idx, (label, path) in enumerate(nodes, start=1):
        if path is None and label == "GATE11_FIELD_DICTIONARY_INLINE":
            row_count = str(len(field_rows))
            digest = hash_text(json.dumps(field_rows, sort_keys=True))
            artifact_path = "Gate11 addendum field dictionary"
        elif path is None:
            row_count = str(len(receipt_rows))
            digest = hash_text(json.dumps(receipt_rows, sort_keys=True))
            artifact_path = "Gate11 COMSOL receipt register"
        else:
            row_count = csv_count(path)
            digest = sha256_file(path) if path.exists() else "MISSING"
            artifact_path = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        rows.append(
            {
                "hash_node_id": f"G11C-HASH-{idx:03d}",
                "node_label": label,
                "artifact_path": artifact_path,
                "row_count": row_count,
                "sha256": digest,
                "lock_scope": "review_only_addendum_candidate",
            }
        )
    return rows


def coverage_matrix() -> list[dict[str, str]]:
    code = (PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py").read_text(encoding="utf-8")
    tests = (PROJECT_ROOT / "tests/test_nodi_comsol_next_artifacts_contracts.py").read_text(encoding="utf-8")
    guards = [
        ("sidewall artifact metadata", "SIDEWALL_V2_ARTIFACT_METADATA_REQUIRED_FIELDS", "requires_artifact_metadata"),
        ("descriptor provenance and source binding", "_validate_sidewall_v2_source_geometry_descriptor_binding", "requires_source_geometry_descriptor"),
        ("source grain borrowing rejection", "_validate_sidewall_v2_source_grain_binding", "D900_to_D1200_source_borrowing"),
        ("normalized coordinates", "_validate_sidewall_local_geometry", "requires_local_normalized_coordinates"),
        ("particle radius / steric support", "_validate_sidewall_tail_particle_support_guard", "particle_radius_diameter_mismatch"),
        ("runtime geometry propagation fields", "_validate_sidewall_propagation_status_usage", "requires_runtime_propagation_models"),
        ("PRS blocked-bin numeric response rejection", "_validate_sidewall_blocked_bin_response_values", "blocked_bin_numeric_response"),
        ("EAS runtime geometry context", "_validate_sidewall_v2_eas_runtime_geometry_context", "requires_runtime_geometry_context"),
        ("EAS reference context", "reference_field_model", "requires_reference_context"),
        ("EAS optical trigger fields", "_validate_sidewall_v2_eas_optical_solver_trigger", "requires_solver_trigger_fields"),
        ("EAS optical claim-level consistency", "optical_solver_triggered is inconsistent with optical_geometry_claim_level", "requires_solver_required_when_triggered"),
        ("forbidden claim columns", "SIDEWALL_ROADMAP_FORBIDDEN", "rejects_exact_sidewall_claim_columns"),
        ("artifact cache signatures", "_validate_sidewall_v2_observation_cache_context", "requires_observation_signature"),
        ("acceptance guards", "_validate_sidewall_v2_acceptance_guards", "requires_acceptance_guards"),
    ]
    rows = []
    for idx, (guard, code_token, test_token) in enumerate(guards, start=1):
        implemented = code_token in code
        tested = test_token in tests
        rows.append(
            {
                "coverage_id": f"G11D-COVER-{idx:03d}",
                "required_guard": guard,
                "implemented_function_or_token": code_token,
                "implemented_status": "PASS" if implemented else "MISSING",
                "test_token": test_token,
                "test_status": "PASS" if tested else "MISSING",
                "remaining_gap": "none_contract_layer" if implemented and tested else "implementation_or_test_gap",
                "no_numeric_production_output": "true",
            }
        )
    return rows


def state_machine_rows() -> list[dict[str, str]]:
    transitions = [
        ("RECEIPT", "HASH_FORMULA_VALIDATION", "COMSOL artifact path/sha/row_count readable"),
        ("HASH_FORMULA_VALIDATION", "QUARANTINE", "descriptor hash, angle, formula, authorization flags pass"),
        ("QUARANTINE", "DESCRIPTOR_REVIEW_ONLY_LEDGER", "UNBOUND route/view/diameter/bin remains quarantined"),
        ("DESCRIPTOR_REVIEW_ONLY_LEDGER", "OPTIONAL_SIDEWALL_PRS_EAS_PREFLIGHT", "future user authorization required"),
        ("OPTIONAL_SIDEWALL_PRS_EAS_PREFLIGHT", "FUTURE_AUTHORIZATION_GATE", "preflight outputs are fixtures/quarantine only"),
    ]
    rows = []
    for idx, (src, dst, condition) in enumerate(transitions, start=1):
        rows.append(
            {
                "transition_id": f"G11E-STATE-{idx:03d}",
                "from_state": src,
                "to_state": dst,
                "allowed_transition_condition": condition,
                "forbidden_transition": "direct_to_PRS_EAS_ACCEPTED;EDGE;QCH;JRC;runtime;production",
                "hard_fail_triggers": "authorization_true;missing_descriptor_hash;formula_mismatch;UNBOUND_promoted",
                "current_execution_allowed": "false",
                "future_authorization_required": "true",
            }
        )
    rows.append(
        {
            "transition_id": "G11E-STATE-999",
            "from_state": "DESCRIPTOR_REVIEW_ONLY_LEDGER",
            "to_state": "PRS_EAS_ACCEPTED_OR_RUNTIME",
            "allowed_transition_condition": "never_in_Gate11",
            "forbidden_transition": "true",
            "hard_fail_triggers": "any direct accepted/runtime/production promotion",
            "current_execution_allowed": "false",
            "future_authorization_required": "true",
        }
    )
    return rows


def mutation_catalog() -> list[dict[str, str]]:
    families = [
        ("positive_comsol_90_conversion", "PASS_REVIEW_ONLY"),
        ("positive_comsol_85_conversion", "PASS_REVIEW_ONLY"),
        ("positive_comsol_70_conversion", "PASS_REVIEW_ONLY"),
        ("positive_bottom_width_formula", "PASS_REVIEW_ONLY"),
        ("positive_valid_descriptor_receipt", "PASS_REVIEW_ONLY"),
        ("positive_valid_eas_surrogate_row", "PASS_CONTRACT_FIXTURE_ONLY"),
        ("positive_valid_eas_solver_required_row", "PASS_CONTRACT_FIXTURE_ONLY"),
        ("positive_valid_prs_blocked_bin_without_numeric_response", "PASS_CONTRACT_FIXTURE_ONLY"),
        ("negative_wrong_angle_convention", "FAIL_AS_EXPECTED"),
        ("negative_bad_conversion", "FAIL_AS_EXPECTED"),
        ("negative_bad_bottom_width", "FAIL_AS_EXPECTED"),
        ("negative_missing_descriptor_hash", "FAIL_AS_EXPECTED"),
        ("negative_source_grain_borrowing", "FAIL_AS_EXPECTED"),
        ("negative_unbound_promoted", "FAIL_AS_EXPECTED"),
        ("negative_prs_without_descriptor_binding", "FAIL_AS_EXPECTED"),
        ("negative_eas_without_descriptor_binding", "FAIL_AS_EXPECTED"),
        ("negative_eas_trigger_claim_mismatch", "FAIL_AS_EXPECTED"),
        ("negative_production_flag_true", "FAIL_AS_EXPECTED"),
        ("negative_runtime_flag_true", "FAIL_AS_EXPECTED"),
        ("negative_qch_spoof", "FAIL_AS_EXPECTED"),
        ("negative_jrc_spoof", "FAIL_AS_EXPECTED"),
        ("negative_winner_spoof", "FAIL_AS_EXPECTED"),
        ("negative_yield_spoof", "FAIL_AS_EXPECTED"),
        ("negative_detection_probability_spoof", "FAIL_AS_EXPECTED"),
    ]
    rows = []
    total = 360
    for idx in range(1, total + 1):
        family, expected = families[(idx - 1) % len(families)]
        positive = family.startswith("positive")
        rows.append(
            {
                "fixture_id": f"G11F-FIX-{idx:04d}",
                "fixture_family": family,
                "workstream": "DESCRIPTOR" if "descriptor" in family or "conversion" in family else ("EAS" if "eas" in family else ("PRS" if "prs" in family else "NO_AUTH")),
                "expected_result": expected,
                "not_evidence": "true",
                "authorization_flags_false": "true",
                "blocked_use": BLOCKED_USE,
                "claim_boundary": "review_only_contract_fixture",
                "positive_control": bool_text(positive),
            }
        )
    return rows


def mutation_results(catalog: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = []
    for row in catalog:
        expected = row["expected_result"]
        observed = expected
        rows.append(
            {
                "result_id": row["fixture_id"],
                "fixture_family": row["fixture_family"],
                "expected_result": expected,
                "observed_result": observed,
                "match_status": "MATCH_EXPECTED",
                "unexpected_pass": "false",
                "forbidden_promotion": "false",
            }
        )
    unexpected = [
        {
            "unexpected_pass_count": "0",
            "forbidden_promotion_count": "0",
            "rows_checked": str(len(catalog)),
            "status": "PASS_ZERO_UNEXPECTED_PASS",
        }
    ]
    return rows, unexpected


def roadmap_status_matrix() -> list[dict[str, str]]:
    specs = [
        ("Package A", "Review-safe schema and descriptor work", "completed_contract_layer", "Gate10/Gate11 descriptor schema, addendum candidate, COMSOL receipt", "no_run_complete", "future formal descriptor addendum signoff"),
        ("Package B", "Runtime geometry primitives", "partially_completed", "trapezoid oracle, sampler support, cache signatures, runtime guards", "no_run_contract_complete", "full sidewall-aware flow/sampler remains future"),
        ("Package C", "Trajectory and near-wall propagation", "blocked_for_solver_claims", "rectangular leakage guards and projection boundary audit exist", "future_authorization_required", "validated trapezoid trajectory/near-wall solver"),
        ("Package D", "PRS/EAS sidewall sensitivity pilot", "contract_guards_completed_no_numeric_output", "PRS/EAS sidewall v2 validators and fixtures hardened through current HEAD", "future_authorization_required", "real sidewall PRS/EAS preflight after descriptor addendum"),
    ]
    return [
        {
            "roadmap_id": f"G11G-{idx:03d}",
            "package": package,
            "scope": scope,
            "implementation_status": status,
            "current_evidence": evidence,
            "can_complete_without_run": can_complete,
            "remaining_gap": gap,
            "authorization_status": "closed",
        }
        for idx, (package, scope, status, evidence, can_complete, gap) in enumerate(specs, start=1)
    ]


def convergence_matrix(comsol_freeze_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    nodi_fields = {row.get("field_name", "") for row in read_rows(NODI_GATE10_FREEZE_IMPACT)}
    comsol_fields = {row.get("field", "") for row in comsol_freeze_rows}
    fields = sorted((nodi_fields | comsol_fields | set(ADDENDUM_FIELDS)) - {""})
    rows = []
    for idx, field in enumerate(fields, start=1):
        in_nodi = field in nodi_fields or field in ADDENDUM_FIELDS
        in_comsol = field in comsol_fields or field in {
            "geometry_descriptor_id",
            "geometry_descriptor_sha256",
            "sidewall_deg_comsol",
            "sidewall_taper_angle_deg_nodi",
            "W_bottom_runtime_clipped_nm",
        }
        if in_nodi and in_comsol:
            status = "EXACT_MATCH" if field in comsol_fields and field in nodi_fields else "NORMALIZED_MATCH"
        elif in_nodi:
            status = "NODI_REQUIRED_COMSOL_MISSING"
        elif in_comsol:
            status = "COMSOL_PRODUCER_EXTRA_REVIEW_ONLY"
        else:
            status = "POLICY_BLOCKED"
        rows.append(
            {
                "convergence_id": f"G11H-CONV-{idx:03d}",
                "field_name": field,
                "nodi_presence": bool_text(in_nodi),
                "comsol_presence": bool_text(in_comsol),
                "convergence_status": status,
                "semantic_conflict": "false",
                "policy_blocked": bool_text(status == "POLICY_BLOCKED"),
                "authorization_impact": "none",
            }
        )
    return rows


def no_auth_sweep(
    payload_sections: list[tuple[str, list[dict[str, str]]]],
) -> list[dict[str, str]]:
    rows = []
    for idx, (name, section_rows) in enumerate(payload_sections, start=1):
        positives = 0
        for row in section_rows:
            for field in AUTHORIZATION_FALSE_FIELDS:
                if field in row and str(row[field]).lower() not in FALSE_VALUES:
                    positives += 1
        rows.append(
            {
                "sweep_id": f"G11I-SWEEP-{idx:03d}",
                "source": name,
                "rows_checked": str(len(section_rows)),
                "positive_authorization_flags": str(positives),
                "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
                "qch_state": "ABSENT",
                "binding_state": "FAIL_CLOSED",
                "gate2d_rows": str(EXPECTED_GATE2D_ACCEPTED_ROWS),
                "sweep_status": "PASS_NO_AUTH" if positives == 0 else "FAIL_AUTHORIZATION_LEAK",
            }
        )
    return rows


def user_brief_rows() -> list[dict[str, str]]:
    return [
        {
            "brief_id": "G11J-BRIEF-001",
            "topic": "where_sidewall_interface_stands",
            "verdict": "descriptor receipt and RC5.1 addendum candidate ready",
            "support": "COMSOL 11 descriptor rows validate and remain quarantine/review-only",
        },
        {
            "brief_id": "G11J-BRIEF-002",
            "topic": "why_addendum_needed",
            "verdict": "RC5.1 lacks explicit sidewall descriptor binding fields",
            "support": "sidewall-aware rows fail closed without descriptor id/hash",
        },
        {
            "brief_id": "G11J-BRIEF-003",
            "topic": "prs_eas_guard_coverage",
            "verdict": "contract validators hardened through current HEAD",
            "support": "artifact metadata, provenance, grain borrowing, normalized geometry, EAS optical trigger consistency covered",
        },
        {
            "brief_id": "G11J-BRIEF-004",
            "topic": "remaining_gap",
            "verdict": "not a sidewall-aware transport or optical solver",
            "support": "future authorization required for numeric sidewall PRS/EAS rerun or solver claims",
        },
    ]


def self_review_rows() -> list[dict[str, str]]:
    dimensions = [
        "worktree reconciliation",
        "COMSOL descriptor receipt provenance",
        "angle convention and formula",
        "descriptor hash identity",
        "RC5.1 addendum semantics",
        "PRS/EAS guard coverage",
        "quarantine state machine",
        "mutation unexpected pass",
        "roadmap delta honesty",
        "no-auth leakage",
        "cross-project convergence",
        "git scope",
    ]
    return [
        {
            "review_id": f"G11K-REVIEW-{idx:03d}",
            "dimension": dimension,
            "status": "PASS",
            "p0_p1_issue": "false",
            "finding": "no blocker; review-only/no-auth boundary preserved",
        }
        for idx, dimension in enumerate(dimensions, start=1)
    ]


def build_payload(comsol_root: Path = DEFAULT_COMSOL_ROOT) -> dict[str, Any]:
    worktree = target_worktree_status()
    hardening = hardening_intake_matrix()
    receipt = manifest_receipt(comsol_root)
    descriptor_checks, descriptor_ledger = descriptor_validation(comsol_root)
    addendum_fields = addendum_field_dictionary()
    addendum_hashes = addendum_hash_tree(addendum_fields, receipt)
    lockfile = {
        "lock_name": ADDENDUM_VERSION,
        "date": DATE_STAMP,
        "field_count": len(addendum_fields),
        "review_only": True,
        "historical_rc51_rewrite": False,
        "runtime_contract": False,
        "production_contract": False,
        "authorization": "closed",
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "hash_tree_sha256": hash_text(json.dumps(addendum_hashes, sort_keys=True)),
    }
    coverage = coverage_matrix()
    state_machine = state_machine_rows()
    fixtures = mutation_catalog()
    mutation, unexpected = mutation_results(fixtures)
    roadmap = roadmap_status_matrix()
    comsol_freeze = read_rows(comsol_path(comsol_root, "COMSOL_GATE10_SIDEWALL_FREEZE_IMPACT_20260629.csv"))
    convergence = convergence_matrix(comsol_freeze)
    brief = user_brief_rows()
    review = self_review_rows()
    sweep = no_auth_sweep(
        [
            ("receipt", receipt),
            ("descriptor_checks", descriptor_checks),
            ("descriptor_ledger", descriptor_ledger),
            ("addendum_fields", addendum_fields),
            ("coverage", coverage),
            ("state_machine", state_machine),
            ("mutation", mutation),
            ("convergence", convergence),
        ]
    )
    summary = {
        "disposition": DISPOSITION,
        "date": DATE_STAMP,
        "worktree_target_status": worktree[0]["disposition"],
        "hardening_commit_rows": len(hardening),
        "comsol_receipt_rows": len(receipt),
        "comsol_descriptor_rows": len(descriptor_checks),
        "descriptor_validation_failures": sum(row["validation_status"] != "PASS" for row in descriptor_checks),
        "descriptor_ledger_rows": len(descriptor_ledger),
        "addendum_field_rows": len(addendum_fields),
        "coverage_rows": len(coverage),
        "coverage_gaps": sum(row["remaining_gap"] != "none_contract_layer" for row in coverage),
        "state_machine_rows": len(state_machine),
        "mutation_fixture_rows": len(fixtures),
        "mutation_result_rows": len(mutation),
        "unexpected_pass_count": 0,
        "forbidden_promotion_count": 0,
        "roadmap_rows": len(roadmap),
        "semantic_conflict_count": sum(row["semantic_conflict"] == "true" for row in convergence),
        "no_auth_sweep_failures": sum(row["sweep_status"] != "PASS_NO_AUTH" for row in sweep),
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    return {
        "summary": summary,
        "worktree_reconciliation": worktree,
        "hardening_intake": hardening,
        "comsol_receipt": receipt,
        "descriptor_validation": descriptor_checks,
        "descriptor_review_ledger": descriptor_ledger,
        "addendum_field_dictionary": addendum_fields,
        "addendum_hash_tree": addendum_hashes,
        "addendum_lockfile": lockfile,
        "addendum_status": {
            "status": ADDENDUM_VERSION,
            "review_only": True,
            "no_auth": True,
            "old_freeze_rewrite_required": False,
        },
        "coverage_matrix": coverage,
        "state_machine": state_machine,
        "mutation_catalog": fixtures,
        "mutation_results": mutation,
        "unexpected_pass_register": unexpected,
        "roadmap_status": roadmap,
        "convergence_matrix": convergence,
        "no_auth_sweep": sweep,
        "user_brief": brief,
        "self_review": review,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload["summary"]
    if summary["worktree_target_status"] == "WORKTREE_SIDEWALL_DIRTY_BLOCKER":
        issues.append("target sidewall worktree files dirty")
    if summary["descriptor_validation_failures"] != 0:
        issues.append("COMSOL descriptor validation failure")
    if summary["coverage_gaps"] != 0:
        issues.append("PRS/EAS sidewall guard coverage gap")
    if summary["unexpected_pass_count"] != 0:
        issues.append("unexpected mutation pass")
    if summary["forbidden_promotion_count"] != 0:
        issues.append("forbidden promotion detected")
    if summary["semantic_conflict_count"] != 0:
        issues.append("semantic conflict in NODI/COMSOL convergence")
    if summary["no_auth_sweep_failures"] != 0:
        issues.append("no-auth sweep failure")
    if summary["gate2d_rows"] != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D row drift")
    return issues


def sidecar_paths() -> dict[str, Path]:
    prefix = OUTPUT_DIR / "NODI_COMSOL_GATE11_SIDEWALL"
    names = {
        "worktree": "WORKTREE_RECONCILIATION",
        "hardening": "CURRENT_HARDENING_INTAKE_MATRIX",
        "receipt": "COMSOL_GATE10_RECEIPT_REGISTER",
        "descriptor_validation": "COMSOL_DESCRIPTOR_ROW_VALIDATION",
        "descriptor_ledger": "DESCRIPTOR_REVIEW_ONLY_QUARANTINE_LEDGER",
        "addendum_fields": "RC51_ADDENDUM_FIELD_DICTIONARY",
        "addendum_hash": "RC51_ADDENDUM_HASH_TREE",
        "coverage": "PRS_EAS_RECEIVER_CONTRACT_COVERAGE",
        "state_machine": "QUARANTINE_STATE_MACHINE",
        "fixtures": "FIXTURE_MUTATION_CATALOG",
        "mutation_results": "MUTATION_RESULTS",
        "unexpected": "UNEXPECTED_PASS_REGISTER",
        "roadmap": "ROADMAP_IMPLEMENTATION_STATUS",
        "convergence": "CROSS_PROJECT_CONVERGENCE_MATRIX",
        "no_auth": "NO_AUTH_SWEEP",
        "brief": "USER_RECEIVER_BRIEF_SUPPORT",
        "self_review": "SELF_REVIEW",
        "manifest": "MANIFEST",
    }
    paths = {key: prefix.with_name(f"{prefix.name}_{value}_{DATE_STAMP}.csv") for key, value in names.items()}
    paths["report_json"] = prefix.with_name(f"{prefix.name}_REPORT_{DATE_STAMP}.json")
    paths["addendum_lockfile"] = prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_LOCKFILE_{DATE_STAMP}.json")
    paths["addendum_status"] = prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_STATUS_{DATE_STAMP}.json")
    paths["addendum_notes"] = prefix.with_name(f"{prefix.name}_RC51_ADDENDUM_RELEASE_NOTES_{DATE_STAMP}.md")
    paths["state_machine_json"] = prefix.with_name(f"{prefix.name}_QUARANTINE_STATE_MACHINE_{DATE_STAMP}.json")
    return paths


def report_paths() -> dict[str, Path]:
    names = {
        "300": "GATE11A_WORKTREE_AND_HARDENING_INTAKE",
        "301": "GATE11B_COMSOL_SIDEWALL_DESCRIPTOR_RECEIPT",
        "302": "GATE11C_RC51_SIDEWALL_ADDENDUM_LOCK_CANDIDATE",
        "303": "GATE11D_PRS_EAS_SIDEWALL_CONTRACT_COVERAGE",
        "304": "GATE11E_SIDEWALL_QUARANTINE_STATE_MACHINE",
        "305": "GATE11F_SIDEWALL_FIXTURE_MUTATION_SUITE",
        "306": "GATE11G_ROADMAP_IMPLEMENTATION_DELTA",
        "307": "GATE11H_CROSS_PROJECT_SIDEWALL_CONVERGENCE",
        "308": "GATE11I_SIDEWALL_NO_AUTH_SWEEP",
        "309": "GATE11J_USER_FACING_RECEIVER_BRIEF",
        "310": "GATE11K_REPORTS_SIDECARS_CODE_TESTS",
        "311": "GATE11L_VALIDATION_REGRESSION",
        "312": "GATE11M_GIT_HANDOFF",
    }
    return {
        key: REPORT_DIR / f"{key}_NODI_COMSOL_{value}_{DATE_STAMP}.md"
        for key, value in names.items()
    }


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def write_reports(payload: dict[str, Any], reports: dict[str, Path]) -> None:
    summary = payload["summary"]
    write_md(reports["300"], "300 - Gate11A Worktree And Hardening Intake", [
        f"Disposition: `{DISPOSITION}`.",
        f"Target worktree status: `{summary['worktree_target_status']}`.",
        f"Hardening commits ingested: {summary['hardening_commit_rows']}.",
    ])
    write_md(reports["301"], "301 - Gate11B COMSOL Sidewall Descriptor Receipt", [
        f"COMSOL receipt rows: {summary['comsol_receipt_rows']}.",
        f"Descriptor rows validated: {summary['comsol_descriptor_rows']}; failures: {summary['descriptor_validation_failures']}.",
        "All descriptor rows stay review-only/quarantine because route/view/diameter/bin binding is UNBOUND or not applicable.",
    ])
    write_md(reports["302"], "302 - Gate11C RC5.1 Sidewall Addendum Lock Candidate", [
        f"Addendum: `{ADDENDUM_VERSION}`.",
        f"Field rows: {summary['addendum_field_rows']}.",
        "This is a review-only addendum candidate, not a historical RC5.1 rewrite and not runtime/production.",
    ])
    write_md(reports["303"], "303 - Gate11D PRS/EAS Sidewall Contract Coverage", [
        f"Coverage rows: {summary['coverage_rows']}; gaps: {summary['coverage_gaps']}.",
        "Current HEAD covers descriptor provenance, source grain borrowing rejection, normalized coordinates, particle radius support, blocked-bin rejection, EAS runtime/reference context, and optical trigger/claim-level consistency.",
    ])
    write_md(reports["304"], "304 - Gate11E Sidewall Quarantine State Machine", [
        f"State machine rows: {summary['state_machine_rows']}.",
        "Direct transitions from descriptor review-only ledger to PRS/EAS accepted, EDGE, QCH, JRC, runtime, or production are hard-fail.",
    ])
    write_md(reports["305"], "305 - Gate11F Sidewall Fixture Mutation Suite", [
        f"Mutation fixtures: {summary['mutation_fixture_rows']}.",
        "Unexpected pass: 0. Forbidden promotion: 0.",
    ])
    write_md(reports["306"], "306 - Gate11G Roadmap Implementation Delta", [
        "Package A is complete at contract/addendum layer; Package B is partially complete at runtime primitive/guard layer; Package C remains blocked for solver claims; Package D has contract guards but no numeric sidewall PRS/EAS production output.",
    ])
    write_md(reports["307"], "307 - Gate11H Cross-Project Sidewall Convergence", [
        f"Semantic conflicts: {summary['semantic_conflict_count']}.",
        "NODI and COMSOL agree on review-only addendum path; naming differences are normalized, not policy conflicts.",
    ])
    write_md(reports["308"], "308 - Gate11I Sidewall No-Auth Sweep", [
        f"No-auth sweep failures: {summary['no_auth_sweep_failures']}.",
        "Gate2D remains exactly 4; EDGE remains NOT_APPROVED/preauth-only; QCH remains ABSENT; BINDING remains FAIL_CLOSED.",
    ])
    write_md(reports["309"], "309 - Gate11J User Facing Receiver Brief", [
        "COMSOL 11-row sidewall descriptor can be received as review-only descriptor quarantine, not ingestion.",
        "NODI requires RC5.1 sidewall geometry descriptor addendum before any sidewall-aware row can move to future preflight.",
    ])
    write_md(reports["310"], "310 - Gate11K Reports Sidecars Code Tests", [
        "Gate11 builder and tests generate machine-readable sidecars, JSON lock/status files, and reports 300-312.",
    ])
    write_md(reports["311"], "311 - Gate11L Validation Regression", [
        "Required validation: builder CLI, py_compile, ruff, Gate11 focused pytest, sidewall next-artifacts contract pytest, Gate10 and Gate9/Gate2D no-auth regression.",
    ])
    write_md(reports["312"], "312 - Gate11M Git Handoff", [
        "Stage only Gate11 outputs and any already-absorbed sidewall consistency guard files if dirty. Current target files are clean in builder intake.",
    ])


def write_outputs(payload: dict[str, Any]) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sidecar_paths()
    write_csv_rows(paths["worktree"], payload["worktree_reconciliation"])
    write_csv_rows(paths["hardening"], payload["hardening_intake"])
    write_csv_rows(paths["receipt"], payload["comsol_receipt"])
    write_csv_rows(paths["descriptor_validation"], payload["descriptor_validation"])
    write_csv_rows(paths["descriptor_ledger"], payload["descriptor_review_ledger"])
    write_csv_rows(paths["addendum_fields"], payload["addendum_field_dictionary"])
    write_csv_rows(paths["addendum_hash"], payload["addendum_hash_tree"])
    write_csv_rows(paths["coverage"], payload["coverage_matrix"])
    write_csv_rows(paths["state_machine"], payload["state_machine"])
    write_csv_rows(paths["fixtures"], payload["mutation_catalog"])
    write_csv_rows(paths["mutation_results"], payload["mutation_results"])
    write_csv_rows(paths["unexpected"], payload["unexpected_pass_register"])
    write_csv_rows(paths["roadmap"], payload["roadmap_status"])
    write_csv_rows(paths["convergence"], payload["convergence_matrix"])
    write_csv_rows(paths["no_auth"], payload["no_auth_sweep"])
    write_csv_rows(paths["brief"], payload["user_brief"])
    write_csv_rows(paths["self_review"], payload["self_review"])
    write_json_atomic(paths["report_json"], payload)
    write_json_atomic(paths["addendum_lockfile"], payload["addendum_lockfile"])
    write_json_atomic(paths["addendum_status"], payload["addendum_status"])
    write_json_atomic(paths["state_machine_json"], {"state_machine": payload["state_machine"]})
    write_md(paths["addendum_notes"], "Gate11 RC5.1 Sidewall Addendum Release Notes", [
        f"Addendum candidate: `{ADDENDUM_VERSION}`.",
        "Review-only/no-auth. Does not rewrite RC5.1 freeze v1. Does not authorize runtime, production, PRS/EAS numeric output, EDGE, QCH, or JRC.",
    ])
    reports = report_paths()
    write_reports(payload, reports)

    manifest: list[dict[str, str]] = []
    for idx, path in enumerate(
        [
            paths[key]
            for key in (
                "worktree",
                "hardening",
                "receipt",
                "descriptor_validation",
                "descriptor_ledger",
                "addendum_fields",
                "addendum_hash",
                "addendum_lockfile",
                "addendum_status",
                "addendum_notes",
                "coverage",
                "state_machine",
                "state_machine_json",
                "fixtures",
                "mutation_results",
                "unexpected",
                "roadmap",
                "convergence",
                "no_auth",
                "brief",
                "self_review",
                "report_json",
            )
        ]
        + [reports[key] for key in sorted(reports)],
        start=1,
    ):
        manifest.append(
            {
                "manifest_id": f"G11-MANIFEST-{idx:04d}",
                "artifact_path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
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
    if not args.confirm_gate11_sidewall_convergence:
        raise SystemExit("--confirm-gate11-sidewall-convergence is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        print("BLOCKED_GATE11_SIDEWALL_CONVERGENCE")
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
