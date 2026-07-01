#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = "NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION"
ARTIFACT_ID = "PACKAGE_C_PROOF_READINESS_INDEX_20260701"
CLAIM_BOUNDARY = "proof_readiness_index_candidate_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C proof-readiness index;single entrypoint for candidate evidence;"
    "external AI context;no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

CONSOLIDATION_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
)
TIMESERIES_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json"
)
STATIONARITY_ENSEMBLE_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_STATUS_20260701.json"
)
ONE_WALL_WALL_PILEUP_STATUS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_STATUS_20260701.json"
)
NEAR_BOUNDARY_EXPECTED_BAND_STATUS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_STATUS_20260701.json"
)
SUBSTEP_HARDENING_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
)
DT_REFINEMENT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json"
)
RUNTIME_SUBSTEP_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
)
AUTHORIZATION_PREFLIGHT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_STATUS_20260701.json"
)
USER_AUTHORIZATION_LEDGER_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"
)
THRESHOLD_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_STATUS_20260701.json"
)
THRESHOLD_TABLE = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv"
)

SOURCE_FILES = {
    "metric_hardening_consolidation_status": CONSOLIDATION_STATUS,
    "timeseries_ess_status": TIMESERIES_STATUS,
    "stationarity_ensemble_status": STATIONARITY_ENSEMBLE_STATUS,
    "one_wall_wall_pileup_status": ONE_WALL_WALL_PILEUP_STATUS,
    "near_boundary_expected_band_status": NEAR_BOUNDARY_EXPECTED_BAND_STATUS,
    "substep_fail_policy_status": SUBSTEP_HARDENING_STATUS,
    "substep_dt_refinement_status": DT_REFINEMENT_STATUS,
    "runtime_substep_policy_design_status": RUNTIME_SUBSTEP_POLICY_STATUS,
    "authorization_preflight_status": AUTHORIZATION_PREFLIGHT_STATUS,
    "user_authorization_ledger_status": USER_AUTHORIZATION_LEDGER_STATUS,
    "proof_threshold_status": THRESHOLD_STATUS,
    "proof_threshold_table": THRESHOLD_TABLE,
    "proof_readiness_index_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py",
    "proof_readiness_index_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_proof_readiness_index.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a Package C proof-readiness index from candidate artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-proof-readiness-index",
        action="store_true",
    )
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


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("summary", {})


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_label": label,
                "path": rel(path),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "github_raw_url": raw_url(path),
                "github_blob_url": blob_url(path),
                "github_visibility_status": GITHUB_VISIBILITY_STATUS,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_PROOF_READINESS_INDEX_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "substep_runtime_policy_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "true_w_eff_authorized": "false",
            "wet_claim_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "production_ingestion_authorized": "false",
        }
    ]


def readiness_index_rows() -> list[dict[str, str]]:
    c = read_json_summary(CONSOLIDATION_STATUS)
    t = read_json_summary(TIMESERIES_STATUS)
    e = read_json_summary(STATIONARITY_ENSEMBLE_STATUS)
    ow = read_json_summary(ONE_WALL_WALL_PILEUP_STATUS)
    nb = read_json_summary(NEAR_BOUNDARY_EXPECTED_BAND_STATUS)
    s = read_json_summary(SUBSTEP_HARDENING_STATUS)
    d = read_json_summary(DT_REFINEMENT_STATUS)
    r = read_json_summary(RUNTIME_SUBSTEP_POLICY_STATUS)
    a = read_json_summary(AUTHORIZATION_PREFLIGHT_STATUS)
    u = read_json_summary(USER_AUTHORIZATION_LEDGER_STATUS)
    p = read_json_summary(THRESHOLD_STATUS)
    rows = [
        {
            "artifact_id": c.get("artifact_id", ""),
            "artifact_role": "metric_hardening_consolidation",
            "disposition": c.get("disposition", ""),
            "candidate_status": c.get("candidate_metric_hardening_status", ""),
            "proof_status": (
                "superseded_by_timeseries_substep_threshold_packets_still_not_proof_registered"
            ),
            "key_values": (
                f"evidence_index_rows={c.get('evidence_index_rows', '')};"
                f"readiness_criteria_rows={c.get('readiness_criteria_rows', '')};"
                f"algorithmic_pileup_signal_rows={c.get('algorithmic_pileup_signal_rows', '')}"
            ),
            "next_action": "use_as_metric_hardening_entrypoint_not_proof",
        },
        {
            "artifact_id": t.get("artifact_id", ""),
            "artifact_role": "timeseries_ess_candidate",
            "disposition": t.get("disposition", ""),
            "candidate_status": t.get("timeseries_ess_candidate_status", ""),
            "proof_status": t.get("proof_readiness_impact", ""),
            "key_values": (
                f"min_ess={t.get('min_effective_sample_size', '')};"
                f"max_u_l1={t.get('max_u_accessible_cdf_l1_to_uniform', '')};"
                f"max_x_l1={t.get('max_x_local_norm_l1_to_uniform', '')}"
            ),
            "next_action": "proof_level_stationarity_and_ess_method_needed",
        },
        {
            "artifact_id": e.get("artifact_id", ""),
            "artifact_role": "stationarity_ensemble_refinement",
            "disposition": e.get("disposition", ""),
            "candidate_status": e.get("stationarity_ensemble_status", ""),
            "proof_status": e.get("proof_readiness_impact", ""),
            "key_values": (
                f"min_independent_ess={e.get('min_independent_ensemble_ess', '')};"
                f"max_final_u_l1={e.get('max_final_u_accessible_cdf_l1_to_uniform', '')};"
                f"max_final_x_l1={e.get('max_final_x_local_norm_l1_to_uniform', '')};"
                f"total_samples={e.get('total_independent_samples', '')}"
            ),
            "next_action": "use_as_stationarity_gap_reduction_candidate_not_proof",
        },
        {
            "artifact_id": ow.get("artifact_id", ""),
            "artifact_role": "one_wall_wall_pileup_refinement",
            "disposition": ow.get("disposition", ""),
            "candidate_status": ow.get("one_wall_wall_pileup_status", ""),
            "proof_status": ow.get("proof_readiness_impact", ""),
            "key_values": (
                f"max_one_wall_ks={ow.get('max_one_wall_positive_control_ks', '')};"
                f"max_wall_pileup_ratio={ow.get('max_wall_pileup_ratio', '')};"
                f"max_wall_pileup_ci95_high={ow.get('max_wall_pileup_ratio_ci95_high', '')};"
                f"sample_count={ow.get('one_wall_sample_count', '')}"
            ),
            "next_action": "use_as_one_wall_wall_pileup_threshold_reduction_candidate_not_proof",
        },
        {
            "artifact_id": nb.get("artifact_id", ""),
            "artifact_role": "near_boundary_expected_band_method",
            "disposition": nb.get("disposition", ""),
            "candidate_status": nb.get("near_boundary_expected_band_method_status", ""),
            "proof_status": nb.get("proof_readiness_impact", ""),
            "key_values": (
                f"max_abs_z={nb.get('max_abs_z_to_expected', '')};"
                f"z_hard_line={nb.get('z_hard_line', '')};"
                f"expected_band_rows={nb.get('expected_band_rows', '')};"
                f"legacy_sparse_context_rows={nb.get('legacy_sparse_context_rows', '')}"
            ),
            "next_action": "use_as_near_boundary_method_binding_candidate_not_proof",
        },
        {
            "artifact_id": s.get("artifact_id", ""),
            "artifact_role": "substep_fail_policy_hardening",
            "disposition": s.get("disposition", ""),
            "candidate_status": s.get("validator_hardening_status", ""),
            "proof_status": s.get("proof_readiness_impact", ""),
            "key_values": (
                f"triggered_rows={s.get('triggered_policy_rows', '')};"
                f"bound_trigger_count={s.get('substep_policy_bound_trigger_count', '')};"
                f"scope={s.get('substep_policy_scope', '')}"
            ),
            "next_action": "future_proof_pass_must_bind_substep_policy_evidence_sha",
        },
        {
            "artifact_id": d.get("artifact_id", ""),
            "artifact_role": "substep_dt_refinement_requirements",
            "disposition": d.get("disposition", ""),
            "candidate_status": d.get("dt_refinement_candidate_status", ""),
            "proof_status": d.get("proof_readiness_impact", ""),
            "key_values": (
                f"max_required_substeps={d.get('max_required_substeps_to_meet_threshold', '')};"
                f"min_required_dt_s={d.get('min_required_dt_s_to_meet_threshold', '')};"
                f"max_projected_trigger={d.get('max_projected_trigger_value_after_required_substeps', '')}"
            ),
            "next_action": "manual_runtime_cost_review_before_any_substep_runtime_policy",
        },
        {
            "artifact_id": r.get("artifact_id", ""),
            "artifact_role": "runtime_substep_policy_design",
            "disposition": r.get("disposition", ""),
            "candidate_status": r.get("runtime_substep_policy_design_status", ""),
            "proof_status": r.get("proof_readiness_impact", ""),
            "key_values": (
                f"max_required_substeps={r.get('max_required_substeps_to_meet_threshold', '')};"
                f"prohibitive_rows={r.get('prohibitive_substep_cost_rows', '')};"
                f"runtime_policy_auth={r.get('runtime_policy_authorization_status', '')}"
            ),
            "next_action": "manual_authorization_and_substep_runtime_tests_before_activation",
        },
        {
            "artifact_id": a.get("artifact_id", ""),
            "artifact_role": "authorization_preflight",
            "disposition": a.get("disposition", ""),
            "candidate_status": a.get("authorization_preflight_status", ""),
            "proof_status": a.get("manual_authorization_ledger_status", ""),
            "key_values": (
                f"target_commit={a.get('target_reviewed_commit_sha', '')};"
                f"head_matches_origin={a.get('head_matches_origin_main', '')};"
                f"ledger_status={a.get('manual_authorization_ledger_status', '')}"
            ),
            "next_action": "manual_authorization_ledger_required_before_proof_or_runtime",
        },
        {
            "artifact_id": u.get("artifact_id", ""),
            "artifact_role": "user_authorization_ledger",
            "disposition": u.get("disposition", ""),
            "candidate_status": u.get("authorization_ledger_status", ""),
            "proof_status": u.get("proof_readiness_impact", ""),
            "key_values": (
                f"authorized_scopes={u.get('authorized_scope_rows', '')};"
                f"proof_path_auth={u.get('package_c_proof_registration_path_authorized', '')};"
                f"runtime_auth={u.get('runtime_substep_policy_authorized', '')};"
                f"solver_auth={u.get('solver_branch_authorized', '')};"
                f"wet_auth={u.get('wet_branch_authorized', '')}"
            ),
            "next_action": "build_evidence_packets_before_result_promotion",
        },
        {
            "artifact_id": p.get("artifact_id", ""),
            "artifact_role": "proof_threshold_table",
            "disposition": p.get("disposition", ""),
            "candidate_status": p.get("threshold_table_status", ""),
            "proof_status": p.get("proof_readiness_impact", ""),
            "key_values": (
                f"threshold_rows={p.get('threshold_rows', '')};"
                f"proof_gap_rows={p.get('proof_gap_rows', '')};"
                f"runtime_policy_gap_rows={p.get('runtime_policy_gap_rows', '')}"
            ),
            "next_action": "use_threshold_rows_to_drive_future_external_research_or_authorization",
        },
    ]
    return [
        {
            **row,
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for row in rows
    ]


def blocker_rows() -> list[dict[str, str]]:
    threshold_rows = read_csv_rows(THRESHOLD_TABLE) if THRESHOLD_TABLE.exists() else []
    authorization_accepted = user_authorization_accepted()
    proof_gap_metrics = [
        row["metric_id"]
        for row in threshold_rows
        if "proof_gap" in row.get("current_status", "")
    ]
    proof_method_gap_metrics = [
        row["metric_id"]
        for row in threshold_rows
        if "proof_method_gap" in row.get("current_status", "")
    ]
    runtime_gap_metrics = [
        row["metric_id"]
        for row in threshold_rows
        if "runtime" in row.get("current_status", "")
    ]
    base_rows = [
        (
            "clean_reviewed_commit_binding_pending",
            (
                "authorization_preflight target commit identified"
                if read_json_summary(AUTHORIZATION_PREFLIGHT_STATUS).get(
                    "head_matches_origin_main",
                    False,
                )
                else "reviewed_commit_binding_status remains pending in candidate packets"
            ),
            (
                "future proof/pass artifact must bind final reviewed clean commit and manual ledger"
                if read_json_summary(AUTHORIZATION_PREFLIGHT_STATUS).get(
                    "head_matches_origin_main",
                    False,
                )
                else "future proof/pass artifact must bind a reviewed clean commit and source lock"
            ),
        ),
        (
            (
                "runtime_substep_execution_evidence_pending"
                if authorization_accepted
                else "runtime_policy_gaps_present"
            ),
            ";".join(runtime_gap_metrics),
            (
                "runtime/substep path is authorized; implementation tests and execution packet are required before runtime output"
                if authorization_accepted
                else "manual runtime cost and substep policy review required before runtime use"
            ),
        ),
        (
            (
                "solver_wet_evidence_pending"
                if authorization_accepted
                else "no_solver_or_wet_claim_authorized"
            ),
            (
                "solver/wet branches authorized, but solver/wet evidence packets have not been produced"
                if authorization_accepted
                else "hindered diffusion, flow, electrokinetic, optical, wet claims all remain blocked"
            ),
            (
                "produce solver/experiment evidence before solver or wet claims"
                if authorization_accepted
                else "separate solver/experiment authorization required"
            ),
        ),
    ]
    if authorization_accepted:
        base_rows.insert(
            0,
            (
                "proof_artifact_registration_pending",
                "proof registration path authorized but Package C proof artifact is not registered",
                "build proof registration artifact with source/evidence hashes before Package C pass",
            ),
        )
    else:
        base_rows.insert(
            0,
            (
                "manual_authorization_ledger_missing",
                "proof_registration_authorized remains false",
                "explicit manual authorization ledger that supersedes no-auth ledger",
            ),
        )
    if proof_gap_metrics:
        base_rows.insert(
            2,
            (
                "proof_threshold_gaps_present",
                ";".join(proof_gap_metrics),
                "resolve or explicitly accept proof thresholds with external/statistical review",
            ),
        )
    if proof_method_gap_metrics:
        base_rows.insert(
            2,
            (
                "proof_method_gaps_present",
                ";".join(proof_method_gap_metrics),
                "bind proof-level statistical method, expected-band mass model, and uncertainty review",
            ),
        )
    return [
        {
            "blocker_id": blocker_id,
            "evidence": evidence,
            "required_resolution": resolution,
            "blocker_status": "open_fail_closed",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for blocker_id, evidence, resolution in base_rows
    ]


def user_authorization_accepted() -> bool:
    user_auth = read_json_summary(USER_AUTHORIZATION_LEDGER_STATUS)
    return (
        user_auth.get("authorization_ledger_status")
        == "accepted_scope_authorization_no_result_promotion"
    )


def external_research_question_rows() -> list[dict[str, str]]:
    questions = [
        (
            "stationarity_ess_method",
            "What proof-level stationarity and ESS method is appropriate for finite-step reflected Brownian motion in a convex offset trapezoid?",
            "Use stationarity ensemble and threshold rows for min ESS and u/x-local L1 gaps; do not infer proof/pass or runtime authorization.",
        ),
        (
            "near_boundary_expected_band_external_review",
            "Is the expected-band area formula and z<=3 candidate line an acceptable future proof-registration method binding?",
            "Use the 513 expected-band method artifact as candidate evidence only; keep no wet/hindered hydrodynamic/runtime claim.",
        ),
        (
            "one_wall_wall_pileup_method_binding",
            "Are the expanded one-wall KS <=0.01 and wall-pileup ratio/CI <=1.25 candidate lines sufficient for future proof registration, and what raw evidence should be bound?",
            "Use the one-wall/wall-pileup refinement as candidate evidence only; no proof/pass or runtime claim, and avoid turning candidate metrics into validated solver output.",
        ),
        (
            "substep_runtime_cost",
            "Given max_required_substeps=526, what substep or smaller-dt strategy is numerically defensible before runtime activation?",
            "Treat this as proof-policy design only; no NODI runtime, COMSOL, PRS/EAS numeric output, or production claim.",
        ),
    ]
    return [
        {
            "question_id": question_id,
            "question": question,
            "scope_guard": scope_guard,
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for question_id, question, scope_guard in questions
    ]


def build_payload() -> dict[str, Any]:
    readiness_rows = readiness_index_rows()
    blockers = blocker_rows()
    questions = external_research_question_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    path_authorization_accepted = user_authorization_accepted()
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "readiness_index_rows": len(readiness_rows),
        "open_blocker_rows": len(blockers),
        "external_research_question_rows": len(questions),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "proof_readiness_index_status": "single_entrypoint_ready_not_proof_registered",
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "path_authorization_accepted": path_authorization_accepted,
        "result_authorization_status": (
            "no_result_authorization_path_authorization_only"
            if path_authorization_accepted
            else "no_authorization"
        ),
        "candidate_only": True,
        "no_auth": True,
        "no_auth_semantics": (
            "legacy field meaning no proof/pass/runtime result authorization; "
            "path authorization may be accepted separately"
        ),
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "readiness_index": readiness_rows,
        "blockers": blockers,
        "external_research_questions": questions,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Readiness rows": s["readiness_index_rows"] == 11,
        "Blockers present": s["open_blocker_rows"] >= 4,
        "External questions present": s["external_research_question_rows"] >= 4,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Readiness status": s["proof_readiness_index_status"]
        == "single_entrypoint_ready_not_proof_registered",
        "No proof registration": s["proof_registration_authorized"] is False,
        "No Package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
        "Path authorization accepted": s["path_authorization_accepted"] is True,
        "No result authorization": (
            s["result_authorization_status"]
            == "no_result_authorization_path_authorization_only"
        ),
    }
    blocker_ids = {row["blocker_id"] for row in payload["blockers"]}
    checks["Authorization accounted"] = (
        "manual_authorization_ledger_missing" in blocker_ids
        or "proof_artifact_registration_pending" in blocker_ids
    )
    checks["Runtime blocker"] = (
        "runtime_policy_gaps_present" in blocker_ids
        or "runtime_substep_execution_evidence_pending" in blocker_ids
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            checks[f"Firewall false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def artifact_manifest_rows(
    paths: list[Path],
    *,
    self_manifest_path: Path | None = None,
) -> list[dict[str, str]]:
    rows = [
        {
            "artifact": path.name,
            "path": rel(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "proof_readiness_index_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]
    if self_manifest_path is not None:
        rows.append(
            {
                "artifact": self_manifest_path.name,
                "path": rel(self_manifest_path),
                "sha256": SELF_MANIFEST_SHA256,
                "disposition": DISPOSITION,
                "policy_impact": "manifest_self_row_no_recursive_sha_no_proof_registration",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path | None = None,
    report_dir: Path | None = None,
) -> dict[str, Path]:
    active_output_dir = output_dir or OUTPUT_DIR
    active_report_dir = report_dir or REPORT_DIR
    active_output_dir.mkdir(parents=True, exist_ok=True)
    active_report_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    csv_specs = {
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv": payload[
            "readiness_index"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv": payload[
            "blockers"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_EXTERNAL_RESEARCH_QUESTIONS_20260701.csv": payload[
            "external_research_questions"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    active_report = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_REPORT_20260701.md"
    write_md(
        active_report,
        "NODI COMSOL Package C Proof Readiness Index",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Readiness rows: `{payload['summary']['readiness_index_rows']}`.",
            f"- Open blocker rows: `{payload['summary']['open_blocker_rows']}`.",
            f"- External research question rows: `{payload['summary']['external_research_question_rows']}`.",
            "- Boundary: single-entrypoint readiness index only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = active_report_dir / "509_NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.md"
    write_md(
        public_report,
        "NODI COMSOL Package C Proof Readiness Index",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet is the single entrypoint for the current Package C metric-hardening state.",
            f"- Readiness rows: `{payload['summary']['readiness_index_rows']}`.",
            f"- Open blocker rows: `{payload['summary']['open_blocker_rows']}`.",
            f"- External research question rows: `{payload['summary']['external_research_question_rows']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is readiness/context evidence only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_REPORT_20260701.json"
    report_outputs = [path.name for path in generated] + [report_path.name, manifest_path.name]
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": report_outputs})
    generated.append(report_path)
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {"status": status_path, "report": report_path, "manifest": manifest_path}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_package_c_proof_readiness_index:
        parser.error("--confirm-package-c-proof-readiness-index is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_PROOF_READINESS_INDEX")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
