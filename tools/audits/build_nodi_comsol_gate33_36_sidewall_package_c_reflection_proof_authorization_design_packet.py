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


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_GATE32_DISPOSITION = (
    "NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION"
)
EXPECTED_GATE30_31_DISPOSITION = (
    "NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
EXPECTED_RC2_DISPOSITION = (
    "PASS_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_READY_FOR_COMSOL_REINTAKE_NO_PROOF_REGISTRATION"
)
EXTERNAL_VERDICT = "READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY"
DISPOSITION = (
    "NODI_GATE33_36_SIDEWALL_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "GATE33_36_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_PACKET_20260630"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_OUTPUT_STATUSES = (
    "candidate_review_ready",
    "needs_candidate_metric_revision",
    "authorization_required_no_proof_registration",
)
PACKET_OUTPUT_STATUS = "authorization_required_no_proof_registration"
ALLOWED_USE = (
    "external research synthesis intake;Package C reflection metric hardening design;"
    "future proof-registration authorization preflight;no-proof-registration"
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

GATE30_31_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_STATUS_20260630.json"
GATE30_31_SUMMARY_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json"
GATE30_31_RAW_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json"
GATE30_31_CANDIDATE_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.csv"
GATE30_31_PARAMETER_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_TEST_PARAMETER_MATRIX_20260630.csv"
GATE30_31_SEED_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_RNG_SEED_MATRIX_20260630.csv"
GATE30_31_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE32_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_STATUS_20260630.json"
GATE32_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_REPORT_20260630.json"
GATE32_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE32_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE32_PROMPT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_PROMPT_20260630.md"
RC2_STATUS = OUTPUT_DIR / "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_STATUS_20260630.json"
RC2_METRIC_QA = OUTPUT_DIR / "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_METRIC_QA_20260630.csv"
RC2_GAP_LEDGER = OUTPUT_DIR / "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_REGISTRATION_GAP_LEDGER_20260630.csv"
RC2_FIREWALL = OUTPUT_DIR / "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_NO_PROOF_FIREWALL_20260630.csv"
RC2_MANIFEST = OUTPUT_DIR / "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_MANIFEST_20260630.csv"

SOURCE_FILES = {
    "gate30_31_status": GATE30_31_STATUS,
    "gate30_31_summary_metrics": GATE30_31_SUMMARY_METRICS,
    "gate30_31_raw_metrics": GATE30_31_RAW_METRICS,
    "gate30_31_candidate_manifest": GATE30_31_CANDIDATE_MANIFEST,
    "gate30_31_parameter_matrix": GATE30_31_PARAMETER_MATRIX,
    "gate30_31_seed_matrix": GATE30_31_SEED_MATRIX,
    "gate30_31_no_proof_firewall": GATE30_31_FIREWALL,
    "gate32_status": GATE32_STATUS,
    "gate32_report": GATE32_REPORT,
    "gate32_source_lock": GATE32_SOURCE_LOCK,
    "gate32_no_proof_firewall": GATE32_FIREWALL,
    "gate32_external_research_prompt": GATE32_PROMPT,
    "rc2_status": RC2_STATUS,
    "rc2_metric_qa": RC2_METRIC_QA,
    "rc2_registration_gap_ledger": RC2_GAP_LEDGER,
    "rc2_no_proof_firewall": RC2_FIREWALL,
    "rc2_manifest": RC2_MANIFEST,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "next_artifacts_contract": PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "gate33_36_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet.py",
    "gate33_36_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

REPORTS = {
    "491": "GATE33_36A_EXTERNAL_RESEARCH_SYNTHESIS_INTAKE",
    "492": "GATE33_36B_PROOF_METRIC_HARDENING_BACKLOG",
    "493": "GATE33_36C_AUTHORIZATION_LEDGER_PLACEHOLDER",
    "494": "GATE33_36D_HARD_FAIL_CHECKLIST",
    "495": "GATE33_36_REFLECTION_PROOF_AUTHORIZATION_DESIGN_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate33-36 Package C reflection proof authorization design packet."
    )
    parser.add_argument(
        "--confirm-gate33-36-package-c-proof-authorization-design",
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


def git_worktree_status(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["status", "--short"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_WORKTREE_STATUS"


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def gate_status(path: Path) -> dict[str, Any]:
    data = read_json(path)
    return data.get("summary", data)


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
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def external_research_capture_lines() -> list[str]:
    return [
        f"- External verdict captured from user-provided external AI feedback: `{EXTERNAL_VERDICT}`.",
        "- Narrow meaning: Gate32 can move into proof-registration authorization design review only.",
        "- It does not authorize Package C proof/pass registration, runtime configuration, numeric PRS/EAS output, COMSOL launch, .mph load, validated Brownian solver output, hindered diffusion, trapezoid pressure-flow, electrokinetic or optical solver claims, true W_eff, route/yield/detection/wet/fab/production claims.",
        "- Recommended route: one combined Gate33-36 package instead of repeated small review loops.",
        "- Immediate work allowed: clean source-lock design, raw metric reproducibility design, exact/near-boundary atom split, one-wall folded-normal suite, equilibrium ESS, corner bias telemetry, dt worst-case refinement, negative controls, hard-fail checklist, and authorization ledger placeholder.",
        "- Manual or external dependency still required: proof registration authorization ledger, solver packages for flow/electrokinetic/optical claims, measured-profile metrology, and wet EV performance evidence.",
    ]


def proof_hardening_backlog_rows() -> list[dict[str, str]]:
    items = [
        (
            "G33-36-BACKLOG-001",
            "clean_reviewed_commit_binding",
            "Bind reviewed commit, worktree clean status, git tree hash, and source lock before any future proof registry update.",
            "candidate_may_include_uncommitted_or_unreviewed_changes_in_prior_exchange",
            "immediate_design_then_future_clean_commit_run",
            "proof_registration_hard_fail_if_missing",
        ),
        (
            "G33-36-BACKLOG-002",
            "exact_vs_near_boundary_atom_split",
            "Separate exact boundary atoms from epsilon-band near-boundary mass and wall pile-up ratios.",
            "Gate30/31 reports max boundary atom fraction as one aggregate.",
            "immediate_metric_builder_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-003",
            "raw_histogram_artifact",
            "Emit u marginal, x_local_norm by u slice, wall-distance, nearest-wall, corner-bin histograms with bin edges and hashes.",
            "summary metrics exist, raw review histograms are not yet line-broken and independently inspectable.",
            "immediate_metric_builder_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-004",
            "ess_autocorrelation_burnin_stride",
            "Report effective sample size, autocorrelation method, burn-in, sample stride, and seed policy.",
            "raw sample counts exist but ESS caveat is not bound.",
            "immediate_metric_builder_extension",
            "proof_reproducibility_required",
        ),
        (
            "G33-36-BACKLOG-005",
            "one_wall_folded_normal_suite",
            "Add d/sigma grid 0, 0.25, 0.5, 1, 2, 4 with KS or Wasserstein distance, normal mean/variance, tangential variance, and boundary atom split.",
            "one-wall candidate status exists but proof-level raw CDF/histogram is not bound.",
            "immediate_metric_builder_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-006",
            "projection_clamp_negative_control",
            "Run legacy projection/clamp negative control expected to fail boundary atom or pile-up diagnostics.",
            "negative control absent from proof candidate packet.",
            "immediate_test_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-007",
            "rejection_resampling_negative_control",
            "Run rejection/resampling negative control expected to fail one-step transition equivalence.",
            "negative control absent from proof candidate packet.",
            "immediate_test_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-008",
            "worst_case_dt_refinement",
            "Select worst 10 scenarios by dt delta, corner rate, and near-closed margin; add dt=6.25e-6 s refinement.",
            "candidate dt grid stops at 1.25e-5 s.",
            "immediate_metric_builder_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-009",
            "corner_area_normalized_heatmap",
            "Emit corner occupancy divided by accessible-area expectation, corner active-set rate, p50/p95/p99/max iterations, and nonconvergence count.",
            "corner candidate status exists but proof-level heatmap and ratio are not bound.",
            "immediate_metric_builder_extension",
            "proof_metric_required",
        ),
        (
            "G33-36-BACKLOG-010",
            "line_broken_review_artifacts",
            "Write pretty JSON and compact CSV summaries so reviewers can inspect rows without one-line minified blobs.",
            "some JSON artifacts are machine-readable but not reviewer-friendly.",
            "immediate_artifact_format_extension",
            "review_quality_required",
        ),
    ]
    return [
        {
            "backlog_id": backlog_id,
            "work_item": work_item,
            "required_change": required_change,
            "current_gap": current_gap,
            "codex_action_class": action_class,
            "proof_registration_relevance": relevance,
            "current_status": "not_yet_implemented_in_gate33_36_design_packet",
            "can_register_proof_now": "false",
            "claim_boundary": PACKET_OUTPUT_STATUS,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for backlog_id, work_item, required_change, current_gap, action_class, relevance in items
    ]


def metric_expansion_spec_rows() -> list[dict[str, str]]:
    specs = [
        (
            "G33-36-METRIC-001",
            "exact_boundary_atom_fraction",
            "Exact g_i equality or declared floating tolerance atom, separated from near-band mass.",
            "Gate30/31 aggregate boundary atom fraction",
            "add metric fields and raw per-wall counts",
            "exact atom fraction zero or justified deterministic setup",
        ),
        (
            "G33-36-METRIC-002",
            "near_boundary_band_mass",
            "0 <= g_i < eps band mass by wall with area expectation and standard error.",
            "Gate30/31 aggregate boundary atom fraction",
            "add analytic expected band mass and pile-up ratio",
            "near band within expected plus declared SE threshold",
        ),
        (
            "G33-36-METRIC-003",
            "wall_pileup_ratio",
            "First near-wall band density divided by adjacent band density.",
            "not bound",
            "add raw histograms and ratio",
            "candidate <= 1.5, future proof <= 1.25",
        ),
        (
            "G33-36-METRIC-004",
            "equilibrium_uniformity_with_ess",
            "u marginal, x_local_norm slices, symmetry, nearest-wall counts, ESS and confidence caveat.",
            "candidate distance without ESS binding",
            "add ESS/autocorrelation/burn-in/stride fields",
            "future proof distance <= 0.04 hard and target <= 0.03",
        ),
        (
            "G33-36-METRIC-005",
            "dt_halving_worst_case_refinement",
            "dt, dt/2, dt/4 and added dt/8 for worst cases.",
            "candidate max delta 0.096354167",
            "add dt=6.25e-6 s rows for selected scenarios",
            "future proof max delta <= 0.075 hard and target <= 0.05",
        ),
        (
            "G33-36-METRIC-006",
            "one_wall_folded_normal_kernel",
            "d/sigma grid CDF or histogram comparison against reflected one-wall kernel.",
            "candidate status without proof raw CDF binding",
            "add raw CDF/histogram and KS/Wasserstein metrics",
            "candidate <= 0.02, future proof <= 0.01",
        ),
        (
            "G33-36-METRIC-007",
            "corner_active_set_bias",
            "Corner occupancy ratio, p99 iterations, max iterations, nonconvergence count.",
            "candidate status without proof heatmap binding",
            "add active-set telemetry and corner heatmap",
            "nonconverged=0, p99<=3, max<=6 or substep/fail",
        ),
        (
            "G33-36-METRIC-008",
            "negative_controls",
            "Projection clamp and rejection/resampling controls must fail designated proof tests.",
            "not bound",
            "add negative-control runner and expected-fail assertions",
            "proof tests must be strong enough to reject known bad boundary treatments",
        ),
    ]
    return [
        {
            "metric_id": metric_id,
            "evidence_target": target,
            "definition": definition,
            "current_gate_source": current_source,
            "immediate_codex_action": action,
            "proof_level_requirement": requirement,
            "current_status": "design_specified_not_registered",
            "claim_boundary": PACKET_OUTPUT_STATUS,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for metric_id, target, definition, current_source, action, requirement in specs
    ]


def threshold_matrix_rows() -> list[dict[str, str]]:
    thresholds = [
        (
            "support_invariance",
            "0 violations",
            "0 violations",
            "hard fail if any simulated point is outside center support",
        ),
        (
            "exact_boundary_atom",
            "<= 1e-5 or explicitly separated",
            "0 exact atoms except deterministic initialization explicitly excluded",
            "separate exact atom from near-boundary band mass",
        ),
        (
            "near_boundary_band_mass",
            "<= expected + 3 SE",
            "<= expected + 2 SE or pile-up ratio <= 1.25",
            "must include per-wall expected band mass",
        ),
        (
            "equilibrium_uniformity_distance",
            "<= 0.06",
            "<= 0.04 hard, target <= 0.03",
            "must include u marginal, x_local_norm slices, symmetry and ESS",
        ),
        (
            "dt_halving_distribution_delta",
            "<= 0.10",
            "<= 0.075 hard, target <= 0.05",
            "current candidate value 0.096354167 remains candidate-only",
        ),
        (
            "one_wall_kernel_distance",
            "KS or Wasserstein <= 0.02",
            "KS or Wasserstein <= 0.01",
            "d/sigma grid must include 0, 0.25, 0.5, 1, 2, 4",
        ),
        (
            "rectangle_limit",
            "machine or 1e-18 tolerance with distinct cache/signature",
            "same with reviewed raw delta artifact",
            "numeric equivalence cannot collapse schema or cache identity",
        ),
        (
            "corner_active_set",
            "nonconverged=0, p99 iterations <= 3, max <= 6 or substep/review",
            "nonconverged=0, p99 iterations <= 3, max <= 6 else fail/substep",
            "must report active-wall count and corner rate",
        ),
        (
            "corner_pileup_ratio",
            "<= 1.5",
            "<= 1.25",
            "normalize corner occupancy by accessible-area expectation",
        ),
        (
            "angle_depth_radius_mutation",
            "geometry/signature/wall-distance/event-count changes present",
            "same plus raw metric deltas and source hash binding",
            "D900 and D1200 cannot borrow context or caches",
        ),
    ]
    return [
        {
            "threshold_id": f"G33-36-THRESHOLD-{idx:03d}",
            "metric_name": metric,
            "candidate_threshold": candidate,
            "future_proof_level_threshold": proof,
            "hard_fail_note": note,
            "current_gate33_36_status": "specified_for_future_metric_hardening_no_proof_registration",
            "claim_boundary": PACKET_OUTPUT_STATUS,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (metric, candidate, proof, note) in enumerate(thresholds, start=1)
    ]


def authorization_ledger_placeholder_rows() -> list[dict[str, str]]:
    fields = [
        ("external_review_verdict", EXTERNAL_VERDICT, "captured_from_user_provided_external_ai_feedback"),
        ("external_review_artifact_sha256", "", "pending_exact_external_review_artifact_binding"),
        ("external_review_confirms_no_claim_promotion", "", "pending_manual_review_of_capture"),
        ("reviewed_candidate_manifest_sha256", "", "pending_future_reviewed_manifest_binding"),
        ("reviewed_summary_metrics_sha256", "", "pending_future_reviewed_summary_binding"),
        ("reviewed_raw_metrics_sha256", "", "pending_future_reviewed_raw_metrics_binding"),
        ("reviewed_commit_sha", "", "pending_clean_reviewed_commit"),
        ("worktree_clean_status", "", "pending_clean_reviewed_commit"),
        ("git_tree_sha256", "", "pending_tree_lock"),
        ("source_lock_manifest_sha256", "", "pending_source_lock_after_hardening"),
        ("artifact_generation_command_sha256", "", "pending_command_lock"),
        ("manual_authorization_ledger_id", "", "pending_human_authorization"),
        ("manual_authorization_ledger_sha256", "", "pending_human_authorization"),
        ("proof_registry_update_plan_sha256", "", "pending_registry_update_plan"),
        ("proof_claim_text_sha256", "", "pending_claim_text_review"),
        ("package_C_proof_artifact_registered", "false", "must_remain_false_in_gate33_36"),
        ("proof_registration_authorized", "false", "must_remain_false_in_gate33_36"),
        ("package_C_validation_status_pass_authorized", "false", "must_remain_false_in_gate33_36"),
        ("runtime_allowed", "false", "must_remain_false_in_gate33_36"),
        ("numeric_prs_eas_allowed", "false", "must_remain_false_in_gate33_36"),
        ("comsol_launch_allowed", "false", "must_remain_false_in_gate33_36"),
        ("mph_load_allowed", "false", "must_remain_false_in_gate33_36"),
    ]
    return [
        {
            "ledger_row_id": f"G33-36-AUTH-PLACEHOLDER-{idx:03d}",
            "field_name": field,
            "current_value": value,
            "current_status": status,
            "required_before_proof_registration": "true",
            "can_register_proof_now": "false",
            "can_mark_package_c_pass_now": "false",
            "claim_boundary": PACKET_OUTPUT_STATUS,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (field, value, status) in enumerate(fields, start=1)
    ]


def evidence_chain_rows(payload_summary: dict[str, Any]) -> list[dict[str, str]]:
    inputs = [
        ("gate30_31_status", GATE30_31_STATUS, "candidate metric counts and no-auth state"),
        (
            "gate30_31_summary_metrics",
            GATE30_31_SUMMARY_METRICS,
            "candidate reflection metric summary",
        ),
        ("gate30_31_raw_metrics", GATE30_31_RAW_METRICS, "raw candidate scenarios"),
        ("gate30_31_candidate_manifest", GATE30_31_CANDIDATE_MANIFEST, "proof candidate fields"),
        ("gate32_status", GATE32_STATUS, "external research handoff disposition"),
        ("gate32_prompt", GATE32_PROMPT, "broad external research question packet"),
        ("rc2_status", RC2_STATUS, "clean successor and candidate exchange closure"),
        ("rc2_metric_qa", RC2_METRIC_QA, "RC2 metric QA normalization"),
        ("rc2_gap_ledger", RC2_GAP_LEDGER, "registration gap and fail-closed rows"),
    ]
    rows: list[dict[str, str]] = []
    for idx, (label, path, role) in enumerate(inputs, start=1):
        rows.append(
            {
                "evidence_id": f"G33-36-EVIDENCE-{idx:03d}",
                "source_label": label,
                "path": rel(path),
                "exists": bool_text(path.exists()),
                "sha256": sha256_file(path) if path.exists() else "",
                "evidence_role": role,
                "absorbed_into_gate33_36_field": _evidence_absorption_field(label),
                "current_gate33_36_status": payload_summary["packet_output_status"],
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _evidence_absorption_field(label: str) -> str:
    mapping = {
        "gate30_31_status": "scenario/open/blocked/dt counts and candidate statuses",
        "gate30_31_summary_metrics": "threshold baseline values",
        "gate30_31_raw_metrics": "future raw metric expansion reference",
        "gate30_31_candidate_manifest": "proof-field gap baseline",
        "gate32_status": "external handoff baseline",
        "gate32_prompt": "external research scope baseline",
        "rc2_status": "clean successor and no-promotion baseline",
        "rc2_metric_qa": "candidate_pass_not_proof normalization",
        "rc2_gap_ledger": "authorization ledger placeholder seed",
    }
    return mapping.get(label, "supporting evidence")


def review_request_rows() -> list[dict[str, str]]:
    requests = [
        (
            "G33-36-REVIEW-001",
            "Verify the packet keeps output status at authorization_required_no_proof_registration.",
            "no proof/pass registration, no runtime, no numeric PRS/EAS",
        ),
        (
            "G33-36-REVIEW-002",
            "Confirm threshold matrix lowers dt candidate threshold to <=0.10 and future proof hard line to <=0.075.",
            "candidate metric hardening only",
        ),
        (
            "G33-36-REVIEW-003",
            "Confirm exact atom, near-boundary band, wall pile-up, ESS, one-wall kernel, negative controls, and worst-case dt refinement are all required before proof registration.",
            "future proof metrics not yet registered",
        ),
        (
            "G33-36-REVIEW-004",
            "Confirm manual authorization ledger and external-review artifact SHA remain placeholders and cannot be auto-filled by this builder.",
            "authorization design only",
        ),
        (
            "G33-36-REVIEW-005",
            "Confirm all no-proof firewall authorization fields remain false.",
            "no runtime/COMSOL/.mph/PRS-EAS/wet/route/yield/detection",
        ),
    ]
    return [
        {
            "review_request_id": request_id,
            "question": question,
            "expected_boundary": boundary,
            "acceptable_answers": "accepted_as_design_only|needs_candidate_metric_revision|claim_promotion_found",
            "can_register_proof_now": "false",
            "can_mark_package_c_pass_now": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for request_id, question, boundary in requests
    ]


def mutation_results_rows(payload_summary: dict[str, Any]) -> list[dict[str, str]]:
    checks = [
        (
            "G33-36-MUTATION-001",
            "proof_registration_authorized",
            payload_summary["proof_registration_authorized"],
            False,
        ),
        (
            "G33-36-MUTATION-002",
            "package_c_validation_status_pass_authorized",
            payload_summary["package_c_validation_status_pass_authorized"],
            False,
        ),
        ("G33-36-MUTATION-003", "runtime_allowed", payload_summary["runtime_allowed"], False),
        (
            "G33-36-MUTATION-004",
            "numeric_prs_eas_allowed",
            payload_summary["numeric_prs_eas_allowed"],
            False,
        ),
        (
            "G33-36-MUTATION-005",
            "comsol_launch_allowed",
            payload_summary["comsol_launch_allowed"],
            False,
        ),
        ("G33-36-MUTATION-006", "mph_load_allowed", payload_summary["mph_load_allowed"], False),
        (
            "G33-36-MUTATION-007",
            "rc2_forbidden_promotion_count",
            payload_summary["rc2_forbidden_promotion_count"],
            0,
        ),
        (
            "G33-36-MUTATION-008",
            "rc2_authorization_promotion_count",
            payload_summary["rc2_authorization_promotion_count"],
            0,
        ),
        (
            "G33-36-MUTATION-009",
            "support_violation_count",
            payload_summary["support_violation_count"],
            0,
        ),
    ]
    rows: list[dict[str, str]] = []
    for check_id, field, actual, expected in checks:
        rows.append(
            {
                "mutation_check_id": check_id,
                "field": field,
                "actual_value": str(actual).lower()
                if isinstance(actual, bool)
                else str(actual),
                "expected_value": str(expected).lower()
                if isinstance(expected, bool)
                else str(expected),
                "mutation_status": "pass"
                if actual == expected
                else "fail_block_gate33_36_design_packet",
                "claim_boundary": PACKET_OUTPUT_STATUS,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def self_review_rows(payload_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        (
            "G33-36-SELF-001",
            "external_ai_used_for_broad_research_not_stepwise_micro_review",
            EXTERNAL_VERDICT == "READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY",
        ),
        (
            "G33-36-SELF-002",
            "combined_packet_instead_of_gate_by_gate_fragmentation",
            payload_summary["packet_output_status"] == PACKET_OUTPUT_STATUS,
        ),
        (
            "G33-36-SELF-003",
            "no_claim_promotion",
            not payload_summary["proof_registration_authorized"]
            and not payload_summary["runtime_allowed"],
        ),
        (
            "G33-36-SELF-004",
            "rc2_no_promotion_absorbed",
            payload_summary["rc2_forbidden_promotion_count"] == 0
            and payload_summary["rc2_authorization_promotion_count"] == 0,
        ),
        (
            "G33-36-SELF-005",
            "hardening_work_has_machine_readable_rows",
            payload_summary["proof_hardening_backlog_rows"] >= 10
            and payload_summary["hard_fail_checklist_rows"] >= 14,
        ),
    ]
    return [
        {
            "self_review_id": review_id,
            "check": check,
            "result": "pass" if passed else "fail",
            "effect_if_fail": "block_gate33_36_packet_publication",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for review_id, check, passed in rows
    ]


def hard_fail_checklist_rows() -> list[dict[str, str]]:
    checks = [
        ("worktree_dirty_or_unreviewed_commit", "worktree is dirty or reviewed_commit_sha is missing"),
        ("external_review_artifact_missing", "external_review_artifact_sha256 is missing"),
        ("manual_authorization_ledger_missing", "manual_authorization_ledger_sha256 is missing"),
        ("proof_registry_plan_missing", "proof_registry_update_plan_sha256 is missing"),
        ("exact_atom_split_missing", "exact boundary atoms are not separated from near-band mass"),
        ("raw_histogram_artifact_missing", "raw histogram artifact or bin edges are missing"),
        ("ess_autocorrelation_missing", "ESS, autocorrelation, burn-in, or stride metadata is missing"),
        ("one_wall_suite_missing", "one-wall folded-normal d/sigma suite is missing"),
        ("dt_worst_case_refinement_missing", "worst-case dt=6.25e-6 s refinement is missing"),
        ("corner_bias_heatmap_missing", "corner area-normalized heatmap or pile-up ratio is missing"),
        ("negative_controls_missing", "projection clamp or rejection/resampling negative control is missing"),
        ("no_proof_firewall_false", "any no-proof/no-runtime/no-wet/no-route firewall field is violated"),
        ("runtime_or_numeric_flag_true", "runtime, numeric PRS/EAS, COMSOL, or .mph authorization becomes true"),
        ("forbidden_claim_column_present", "unqualified route_score, winner, q_ch, W_eff, yield, detection_probability, wet pass, clogging, recovery, or production-ready claim appears"),
    ]
    return [
        {
            "hard_fail_id": f"G33-36-HARD-FAIL-{idx:03d}",
            "condition": condition,
            "trigger": trigger,
            "effect": "block_proof_registration_and_package_c_pass",
            "current_gate33_36_state": "not_triggered_for_design_packet_but_required_for_future_registration",
            "can_register_proof_now": "false",
            "can_mark_package_c_pass_now": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (condition, trigger) in enumerate(checks, start=1)
    ]


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE33_36_AUTHORIZATION_DESIGN_NO_PROOF_REGISTRATION",
            "external_research_synthesis_received": "true",
            "external_verdict": EXTERNAL_VERDICT,
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
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
            "wet_pass_probability_authorized": "false",
            "clogging_rate_authorized": "false",
            "time_to_clog_authorized": "false",
            "recovery_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "production_ingestion_authorized": "false",
        }
    ]


def build_payload() -> dict[str, Any]:
    gate30_31 = gate_status(GATE30_31_STATUS)
    gate32 = gate_status(GATE32_STATUS)
    rc2 = gate_status(RC2_STATUS)
    source_rows = source_lock_rows()
    backlog = proof_hardening_backlog_rows()
    metric_specs = metric_expansion_spec_rows()
    thresholds = threshold_matrix_rows()
    auth_rows = authorization_ledger_placeholder_rows()
    hard_fails = hard_fail_checklist_rows()
    firewall = no_proof_firewall_rows()
    worktree_status = git_worktree_status()
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "gate33_36_build_head": safe_git_head(),
        "gate33_36_worktree_clean_at_build_time": worktree_status == "",
        "gate33_36_worktree_status_line_count_at_build_time": len(
            [line for line in worktree_status.splitlines() if line.strip()]
        ),
        "external_verdict": EXTERNAL_VERDICT,
        "packet_output_status": PACKET_OUTPUT_STATUS,
        "allowed_output_statuses": list(ALLOWED_OUTPUT_STATUSES),
        "gate32_disposition": gate32.get("disposition", ""),
        "gate32_expected_disposition": EXPECTED_GATE32_DISPOSITION,
        "gate30_31_disposition": gate30_31.get("disposition", ""),
        "gate30_31_expected_disposition": EXPECTED_GATE30_31_DISPOSITION,
        "rc2_disposition": rc2.get("disposition", ""),
        "rc2_expected_disposition": EXPECTED_RC2_DISPOSITION,
        "rc2_forbidden_promotion_count": int(rc2.get("forbidden_promotion_count", 0) or 0),
        "rc2_authorization_promotion_count": int(
            rc2.get("authorization_promotion_count", 0) or 0
        ),
        "rc2_unexpected_pass_count": int(rc2.get("unexpected_pass_count", 0) or 0),
        "scenario_metric_rows": int(gate30_31.get("scenario_metric_rows", 0) or 0),
        "open_candidate_metric_rows": int(
            gate30_31.get("open_candidate_metric_rows", 0) or 0
        ),
        "blocked_candidate_rows": int(gate30_31.get("blocked_candidate_rows", 0) or 0),
        "dt_halving_rows": int(gate30_31.get("dt_halving_rows", 0) or 0),
        "support_violation_count": int(gate30_31.get("support_violation_count", 0) or 0),
        "max_boundary_atom_fraction": gate30_31.get("max_boundary_atom_fraction"),
        "max_equilibrium_uniformity_distance": gate30_31.get(
            "max_equilibrium_uniformity_distance"
        ),
        "dt_halving_max_distribution_delta": gate30_31.get(
            "dt_halving_max_distribution_delta"
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "proof_hardening_backlog_rows": len(backlog),
        "metric_expansion_spec_rows": len(metric_specs),
        "threshold_matrix_rows": len(thresholds),
        "authorization_ledger_placeholder_rows": len(auth_rows),
        "hard_fail_checklist_rows": len(hard_fails),
        "no_proof_firewall_rows": len(firewall),
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "review_only": True,
        "no_auth": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    evidence_chain = evidence_chain_rows(summary)
    review_requests = review_request_rows()
    mutation_results = mutation_results_rows(summary)
    self_review = self_review_rows(summary)
    summary.update(
        {
            "evidence_chain_rows": len(evidence_chain),
            "review_request_rows": len(review_requests),
            "mutation_result_rows": len(mutation_results),
            "self_review_rows": len(self_review),
            "mutation_fail_count": sum(
                row["mutation_status"] != "pass" for row in mutation_results
            ),
            "self_review_fail_count": sum(row["result"] != "pass" for row in self_review),
        }
    )
    return {
        "summary": summary,
        "gate30_31_summary": gate30_31,
        "gate32_summary": gate32,
        "rc2_summary": rc2,
        "source_locks": source_rows,
        "evidence_chain": evidence_chain,
        "external_research_capture_lines": external_research_capture_lines(),
        "proof_hardening_backlog": backlog,
        "metric_expansion_spec": metric_specs,
        "threshold_matrix": thresholds,
        "authorization_ledger_placeholder": auth_rows,
        "hard_fail_checklist": hard_fails,
        "review_requests": review_requests,
        "mutation_results": mutation_results,
        "self_review": self_review,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate32 disposition": s["gate32_disposition"] == EXPECTED_GATE32_DISPOSITION,
        "Gate30/31 disposition": s["gate30_31_disposition"] == EXPECTED_GATE30_31_DISPOSITION,
        "RC2 disposition": s["rc2_disposition"] == EXPECTED_RC2_DISPOSITION,
        "RC2 no forbidden promotion": s["rc2_forbidden_promotion_count"] == 0,
        "RC2 no authorization promotion": s["rc2_authorization_promotion_count"] == 0,
        "RC2 no unexpected pass": s["rc2_unexpected_pass_count"] == 0,
        "External verdict captured": s["external_verdict"] == EXTERNAL_VERDICT,
        "Allowed output status": s["packet_output_status"] in ALLOWED_OUTPUT_STATUSES,
        "Scenario metrics present": s["scenario_metric_rows"] >= 200,
        "Support violations zero": s["support_violation_count"] == 0,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Backlog present": s["proof_hardening_backlog_rows"] >= 10,
        "Metric expansion present": s["metric_expansion_spec_rows"] >= 8,
        "Threshold matrix present": s["threshold_matrix_rows"] >= 10,
        "Authorization placeholder present": s["authorization_ledger_placeholder_rows"] >= 20,
        "Hard fail checklist present": s["hard_fail_checklist_rows"] >= 14,
        "Evidence chain present": s["evidence_chain_rows"] >= 9,
        "Review requests present": s["review_request_rows"] >= 5,
        "Mutation results pass": s["mutation_fail_count"] == 0,
        "Self review passes": s["self_review_fail_count"] == 0,
        "No proof registration": s["proof_registration_authorized"] is False,
        "No package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
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
            "policy_impact": "authorization_design_only_no_proof_registration",
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

    capture_path = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_EXTERNAL_RESEARCH_SYNTHESIS_CAPTURE_20260630.md"
    write_md(
        capture_path,
        "NODI COMSOL Gate33-36 Sidewall External Research Synthesis Capture",
        payload["external_research_capture_lines"],
    )
    generated.append(capture_path)

    csv_specs = {
        "NODI_COMSOL_GATE33_36_SIDEWALL_SOURCE_LOCK_20260630.csv": payload["source_locks"],
        "NODI_COMSOL_GATE33_36_SIDEWALL_EVIDENCE_CHAIN_20260630.csv": payload[
            "evidence_chain"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_PROOF_HARDENING_BACKLOG_20260630.csv": payload[
            "proof_hardening_backlog"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_METRIC_EXPANSION_SPEC_20260630.csv": payload[
            "metric_expansion_spec"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_THRESHOLD_MATRIX_20260630.csv": payload[
            "threshold_matrix"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_AUTHORIZATION_LEDGER_PLACEHOLDER_20260630.csv": payload[
            "authorization_ledger_placeholder"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_HARD_FAIL_CHECKLIST_20260630.csv": payload[
            "hard_fail_checklist"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_REVIEW_REQUEST_20260630.csv": payload[
            "review_requests"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_MUTATION_RESULTS_20260630.csv": payload[
            "mutation_results"
        ],
        "NODI_COMSOL_GATE33_36_SIDEWALL_SELF_REVIEW_20260630.csv": payload["self_review"],
        "NODI_COMSOL_GATE33_36_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_path = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(
        report_path,
        {
            "summary": payload["summary"],
            "outputs": [path.name for path in generated],
        },
    )
    generated.append(report_path)

    status_path = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "review_only": True,
            "no_auth": True,
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    master_md = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_REFLECTION_PROOF_AUTHORIZATION_DESIGN_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate33-36 Sidewall Reflection Proof Authorization Design",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- External verdict: `{EXTERNAL_VERDICT}`",
            f"- Output status: `{PACKET_OUTPUT_STATUS}`",
            f"- Backlog rows: {payload['summary']['proof_hardening_backlog_rows']}.",
            f"- Metric expansion rows: {payload['summary']['metric_expansion_spec_rows']}.",
            f"- Threshold rows: {payload['summary']['threshold_matrix_rows']}.",
            f"- Authorization placeholder rows: {payload['summary']['authorization_ledger_placeholder_rows']}.",
            f"- Hard-fail rows: {payload['summary']['hard_fail_checklist_rows']}.",
            "- Boundary: authorization design only; no Package C proof/pass registration, no runtime, no numeric PRS/EAS, no COMSOL launch, no .mph load, no route/yield/detection/wet/fab/production claim.",
        ],
    )
    generated.append(master_md)

    review_request_md = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_REVIEW_REQUEST_20260630.md"
    write_md(
        review_request_md,
        "NODI COMSOL Gate33-36 Sidewall Review Request",
        [
            f"- Verdict intake: `{EXTERNAL_VERDICT}`",
            f"- Requested status review: `{PACKET_OUTPUT_STATUS}` only.",
            "- Please review whether the hardening backlog, threshold matrix, authorization placeholder, and firewall are sufficient to guide the next implementation block without claim promotion.",
            "- Do not interpret this packet as proof/pass registration, runtime authorization, COMSOL launch, .mph load, numeric PRS/EAS, wet/route/yield/detection, or production evidence.",
        ],
    )
    generated.append(review_request_md)

    for number, title in REPORTS.items():
        path = active_report_dir / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate33-36 disposition: `{DISPOSITION}`",
                f"- External verdict: `{EXTERNAL_VERDICT}`",
                f"- Output status: `{PACKET_OUTPUT_STATUS}`",
                f"- Source head: `{payload['summary']['gate33_36_build_head']}`",
                f"- Gate32 source disposition: `{payload['summary']['gate32_disposition']}`",
                f"- Gate30/31 source disposition: `{payload['summary']['gate30_31_disposition']}`",
                f"- RC2 source disposition: `{payload['summary']['rc2_disposition']}`",
                "- Boundary: design packet only; proof registration and Package C pass remain unauthorized.",
                f"- Machine-readable support: `{rel(active_output_dir)}`.",
            ],
        )
        generated.append(path)

    manifest_path = active_output_dir / "NODI_COMSOL_GATE33_36_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )

    return {
        "capture": capture_path,
        "report": report_path,
        "status": status_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate33_36_package_c_proof_authorization_design:
        parser.error("--confirm-gate33-36-package-c-proof-authorization-design is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE33_36_SIDEWALL_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
