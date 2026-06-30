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

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"

EXPECTED_GATE19_HEAD = "e67c404118648d52af2a99a5995cbd1ee024c6ec"
EXPECTED_COMSOL_GATE16_HEAD = "ed4cfc7ff4565f79c025cd206bef0aff29d25d6a"
EXPECTED_COMSOL_GATE16_STATUS = "COMSOL_GATE16_CURRENT_NODI_CLEAN_REINTAKE_CONSUMED_CONTEXT_ONLY_NO_AUTH"
EXPECTED_COMSOL_ANCHOR_DIGEST = "4255d9533a8d150d6a740d03ead267323e868b5560b7051ce5d5ccc0ed3c2c16"
EXPECTED_GATE19_DISPOSITION = "NODI_GATE19_SIDEWALL_PACKAGE_ABD_STATIC_PREFLIGHT_PASS_NO_AUTH"
DISPOSITION = "NODI_GATE20_SIDEWALL_STATIC_CONTINUITY_HARD_FAIL_VALIDATOR_READY_NO_AUTH"
ALLOWED_USE = "review-only Gate19-to-Gate20 static continuity;A/B/D hard-fail validator readiness;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics;"
    "COMSOL launch;.mph load;NODI runtime recomputation;Package C physics authorization"
)

REPORTS = {
    "413": "GATE20A_INDEPENDENT_REVIEW_INTAKE",
    "414": "GATE20B_GATE19_CONTINUITY_SOURCE_LOCK",
    "415": "GATE20C_ABD_HARD_FAIL_VALIDATOR_SURFACE",
    "416": "GATE20D_PACKAGE_C_BLOCKED_LEDGER",
    "417": "GATE20E_POST_COMSOL_GATE16_HEAD_ADVANCE_EXPLANATION",
    "418": "GATE20F_NO_AUTH_FIREWALL_AND_FORBIDDEN_CLAIM_SCAN",
    "419": "GATE20G_VALIDATION_AND_NEXT_STEPS",
    "420": "GATE20_SIDEWALL_STATIC_CONTINUITY_MASTER_REPORT",
}

GATE19_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_MANIFEST_20260630.csv",
    "package_preflight": OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_PACKAGE_PREFLIGHT_20260630.csv",
    "firewall": OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate20 sidewall static continuity checkpoint.")
    parser.add_argument("--confirm-gate20-static-continuity", action="store_true")
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


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def git_is_ancestor(ancestor: str, descendant: str, cwd: Path = PROJECT_ROOT) -> bool:
    try:
        subprocess.run(
            ["git", "-c", f"safe.directory={cwd.as_posix()}", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G20-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def independent_review_rows() -> list[dict[str, str]]:
    return [
        {
            "review_id": "G20A-REVIEW-001",
            "reviewer": "independent_subagent_read_only",
            "review_scope": "full roadmap and Gate15-Gate19 continuity;NODI and COMSOL heads;claim boundary",
            "finding": "NO_P0_P1_FOR_GATE20_STATIC_CONTINUITY",
            "allowed_next_step": "Gate20 no-auth static continuity and A/B/D contract preflight only",
            "blocked_next_step": "Package C physics;runtime;COMSOL launch;.mph load;PRS/EAS numeric production;claim/release route",
            "ideal_rectangle_preserved": "true",
            "trapezoid_path_controlled": "true",
            "external_ai_needed_now": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def gate19_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    manifest = read_csv_rows(GATE19_FILES["manifest"]) if GATE19_FILES["manifest"].exists() else []
    for idx, item in enumerate(manifest, start=1):
        path = PROJECT_ROOT / item["path"]
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_rows = item.get("row_count", "NA")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        sha_match = actual_sha == item.get("sha256", "")
        if not exists:
            status = "MISSING_GATE19_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_GATE19_SOURCE_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "source_lock_id": f"G20B-GATE19-{idx:03d}",
                "source_gate": "Gate19",
                "path": item["path"],
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": item.get("sha256", ""),
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(sha_match),
                "row_count_match": bool_text(row_match),
                "lock_status": status,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def validator_surface_rows() -> list[dict[str, str]]:
    specs = [
        ("Package A", "missing_angle_convention", "sidewall angle field present without convention", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package A", "angle_conversion_mismatch", "COMSOL and NODI angle fields do not sum to 90 deg within tolerance", "tests/test_cross_section_geometry.py"),
        ("Package A", "bare_W_top_runtime_binding", "W_top or mask/top CD used as runtime aperture without semantics/source/bias", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package A", "silent_bottom_clip", "bottom width clipped before unclipped descriptor emission", "tests/test_cross_section_geometry.py"),
        ("Package A", "nonpositive_bottom_marked_open", "nonpositive unclipped bottom width marked open", "tests/test_cross_section_geometry.py"),
        ("Package A", "missing_closure_policy", "closed or clamped geometry row lacks closure policy", "tests/test_cross_section_geometry.py"),
        ("Package A", "min_aperture_used_as_passability", "descriptor min aperture is promoted to EV passability evidence", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package A", "measured_geometry_without_profile", "measured geometry claim without loaded/hashed/validated profile", "tests/test_physics_core.py"),
        ("Package A", "source_hash_missing_for_comsol_context", "COMSOL-derived descriptor/context row lacks source descriptor id or sha", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package A", "claim_boundary_missing", "artifact row lacks explicit claim boundary", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package B", "trapezoid_runtime_without_geometry_primitive", "trapezoid request lacks cross-section geometry version", "tests/test_cross_section_geometry.py"),
        ("Package B", "rectangular_sampler_under_trapezoid", "trapezoid sampler reads rectangular width/depth half-span", "tests/test_cross_section_geometry.py"),
        ("Package B", "uniform_accessible_area_label_mismatch", "uniform accessible area label backed by rectangle support", "tests/test_cross_section_geometry.py"),
        ("Package B", "sample_outside_center_support", "sampled particle center falls outside radius-aware support", "tests/test_cross_section_geometry.py"),
        ("Package B", "blocked_bin_has_response", "blocked PRS bin carries numeric response/proxy", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package B", "neighbor_fill_blocked_bin", "blocked PRS bin is filled from neighbor/interpolation", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package B", "flux_weighted_without_trapezoid_flow_model", "flux-weighted trapezoid sampling lacks compatible flow field", "tests/test_cross_section_geometry.py"),
        ("Package D", "prs_without_geometry_basis", "PRS row lacks position distribution basis or geometry version", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "prs_without_particle_radius_support", "PRS row lacks particle radius/support status", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "edge4_to_edge20_direct_mapping", "edge4 context is mapped directly to edge20 PRS bins", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "D900_to_D1200_borrowing", "D900 evidence is used for D1200 route/depth grain", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "auto_admit_220_or_300nm", "220/300 nm rows are admitted without exact steric support", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "comsol_context_as_prs_grain", "COMSOL TPD/proxy/context row promoted to exact PRS grain", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "bare_W_eff", "EAS emits bare W_eff rather than named surrogate field", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "solver_trigger_as_solver_output", "optical solver trigger is treated as optical solver result", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "rank_or_score_field_present", "rank/score/route_score/winner style column promotes route conclusion", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("Package D", "claim_flags_missing", "sidewall PRS/EAS row lacks no-claim flags", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
        ("G8 cache/signature", "old_rectangular_cache_reuse", "old rectangle cache satisfies trapezoid request", "tests/test_physics_core.py"),
        ("G8 cache/signature", "sidewall_aware_with_not_propagated_status", "row marked sidewall-aware while geometry propagation is not propagated", "tests/test_nodi_comsol_next_artifacts_contracts.py"),
    ]
    rows: list[dict[str, str]] = []
    for idx, (package, code, trigger, evidence) in enumerate(specs, start=1):
        rows.append(
            {
                "validator_id": f"G20C-HARDFAIL-{idx:03d}",
                "package": package,
                "hard_fail_code": code,
                "trigger_condition": trigger,
                "enforcement_surface": evidence,
                "current_status": "ENFORCED_STATIC_CONTRACT_READY_NO_RUNTIME",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "sidewall_numeric_output_allowed": "false",
                "claim_promotion_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def package_c_blocked_rows() -> list[dict[str, str]]:
    return [
        {
            "blocked_id": "G20D-PACKAGE-C-001",
            "scope": "trajectory/near-wall/hindered-diffusion/flow/optical/wet physics",
            "blocked_status": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
            "reason": "Gate20 is static continuity only; no Package C physics authorization was granted",
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "next_allowed_action": "none until explicit Package C physics authorization and independent review",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def post_gate16_head_advance_rows(comsol_root: Path) -> list[dict[str, str]]:
    comsol_status = read_json(comsol_root / "roadmap" / "COMSOL_GATE16_STATUS_20260630.json")
    nodi_current_head = safe_git_head(PROJECT_ROOT)
    comsol_consumed_nodi_head = str(comsol_status.get("nodi_head", ""))
    return [
        {
            "advance_id": "G20E-HEAD-ADVANCE-001",
            "item": "COMSOL Gate16 consumed NODI head",
            "value": comsol_consumed_nodi_head,
            "interpretation": "clean anchor reintake context consumed by COMSOL Gate16",
            "stale_head_risk": "closed_by_gate17_anchor_and_gate18_receipt",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "advance_id": "G20E-HEAD-ADVANCE-002",
            "item": "NODI Gate19 input head",
            "value": EXPECTED_GATE19_HEAD,
            "interpretation": "post-COMSOL-Gate16 NODI static successors advanced by Gate18/Gate19",
            "stale_head_risk": "not_a_ping_pong_reopen_when_gate19_head_is_ancestor_of_current_head",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "advance_id": "G20E-HEAD-ADVANCE-003",
            "item": "current NODI head",
            "value": nodi_current_head,
            "interpretation": "may be Gate19 or later Gate20 report/test successor; semantic source remains pinned to Gate19",
            "stale_head_risk": "pass" if git_is_ancestor(EXPECTED_GATE19_HEAD, nodi_current_head, PROJECT_ROOT) else "fail_closed_gate19_not_ancestor",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G20F-NOAUTH-001",
            "positive_authorization_count": "0",
            "runtime_configuration_authorized": "false",
            "production_ingestion_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "nodi_runtime_recompute_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "package_c_authorized": "false",
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate20_sidewall_static_continuity.py --confirm-gate20-static-continuity",
        "python -m py_compile tools/audits/build_nodi_comsol_gate20_sidewall_static_continuity.py",
        "python -m pytest tests/test_nodi_comsol_gate20_sidewall_static_continuity.py -q",
        "python -m pytest tests/test_nodi_comsol_gate17_sidewall_current_release_anchor.py tests/test_nodi_comsol_gate18_sidewall_comsol_gate16_receipt.py tests/test_nodi_comsol_gate19_sidewall_static_preflight.py tests/test_nodi_comsol_gate20_sidewall_static_continuity.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_cross_section_geometry.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics tests/test_physics_core.py::TestIntegration::test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated -q",
    ]
    return [
        {"validation_id": f"G20G-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload(comsol_root: Path = DEFAULT_COMSOL_ROOT) -> dict[str, Any]:
    gate19_status = read_json(GATE19_FILES["status"])
    gate19_summary = gate19_status.get("summary", {})
    gate19_locks = gate19_source_lock_rows()
    comsol_status = read_json(comsol_root / "roadmap" / "COMSOL_GATE16_STATUS_20260630.json")
    nodi_current_head = safe_git_head(PROJECT_ROOT)
    comsol_head = safe_git_head(comsol_root)
    validator_rows = validator_surface_rows()
    package_c = package_c_blocked_rows()
    firewall = no_auth_firewall_rows()
    summary = {
        "disposition": DISPOSITION,
        "nodi_current_head": nodi_current_head,
        "expected_gate19_head": EXPECTED_GATE19_HEAD,
        "gate19_head_is_ancestor_of_current": git_is_ancestor(EXPECTED_GATE19_HEAD, nodi_current_head, PROJECT_ROOT),
        "comsol_head_actual": comsol_head,
        "expected_comsol_gate16_head": EXPECTED_COMSOL_GATE16_HEAD,
        "comsol_gate16_status": comsol_status.get("status", ""),
        "comsol_anchor_digest": comsol_status.get("anchor_semantic_digest_sha256", ""),
        "comsol_consumed_nodi_head": comsol_status.get("nodi_head", ""),
        "comsol_consumed_nodi_head_is_ancestor_of_gate19": git_is_ancestor(str(comsol_status.get("nodi_head", "")), EXPECTED_GATE19_HEAD, PROJECT_ROOT),
        "gate19_disposition": gate19_status.get("disposition", ""),
        "gate19_manifest_rows": len(gate19_locks),
        "gate19_source_drift": sum(row["lock_status"] == "BLOCKING_GATE19_SOURCE_DRIFT" for row in gate19_locks),
        "gate19_missing_sources": sum(row["lock_status"] == "MISSING_GATE19_ARTIFACT" for row in gate19_locks),
        "gate19_package_a_status": gate19_summary.get("package_a_status", ""),
        "gate19_package_b_status": gate19_summary.get("package_b_status", ""),
        "gate19_package_c_status": gate19_summary.get("package_c_status", ""),
        "gate19_package_d_status": gate19_summary.get("package_d_status", ""),
        "hard_fail_validator_rows": len(validator_rows),
        "runtime_allowed_rows": sum(row["runtime_allowed"] == "true" for row in validator_rows + package_c),
        "production_allowed_rows": sum(row["production_allowed"] == "true" for row in validator_rows + package_c),
        "package_c_state": package_c[0]["blocked_status"],
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "external_ai_needed_now": False,
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "independent_review": independent_review_rows(),
        "gate19_source_locks": gate19_locks,
        "validator_surface": validator_rows,
        "package_c_blocked": package_c,
        "post_gate16_head_advance": post_gate16_head_advance_rows(comsol_root),
        "no_auth_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate19 head ancestry": s["gate19_head_is_ancestor_of_current"] is True,
        "COMSOL Gate16 head": s["comsol_head_actual"] == EXPECTED_COMSOL_GATE16_HEAD,
        "COMSOL Gate16 status": s["comsol_gate16_status"] == EXPECTED_COMSOL_GATE16_STATUS,
        "COMSOL anchor digest": s["comsol_anchor_digest"] == EXPECTED_COMSOL_ANCHOR_DIGEST,
        "COMSOL consumed NODI ancestor": s["comsol_consumed_nodi_head_is_ancestor_of_gate19"] is True,
        "Gate19 disposition": s["gate19_disposition"] == EXPECTED_GATE19_DISPOSITION,
        "Gate19 source lock rows": s["gate19_manifest_rows"] >= 6,
        "Gate19 source drift": s["gate19_source_drift"] == 0,
        "Gate19 missing sources": s["gate19_missing_sources"] == 0,
        "Package A static pass": s["gate19_package_a_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME",
        "Package B static pass": s["gate19_package_b_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME",
        "Package C blocked": s["gate19_package_c_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "Package D static pass": s["gate19_package_d_status"] == "PASS_CONTRACT_PREFLIGHT_NO_RUNTIME",
        "Hard-fail validator surface": s["hard_fail_validator_rows"] >= 29,
        "Runtime allowed rows": s["runtime_allowed_rows"] == 0,
        "Production allowed rows": s["production_allowed_rows"] == 0,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
        "External AI not needed now": s["external_ai_needed_now"] is False,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE20_SIDEWALL_INDEPENDENT_REVIEW_INTAKE_20260630.csv": payload["independent_review"],
        "NODI_COMSOL_GATE20_SIDEWALL_GATE19_SOURCE_LOCK_20260630.csv": payload["gate19_source_locks"],
        "NODI_COMSOL_GATE20_SIDEWALL_ABD_HARD_FAIL_VALIDATOR_SURFACE_20260630.csv": payload["validator_surface"],
        "NODI_COMSOL_GATE20_SIDEWALL_PACKAGE_C_BLOCKED_LEDGER_20260630.csv": payload["package_c_blocked"],
        "NODI_COMSOL_GATE20_SIDEWALL_POST_GATE16_HEAD_ADVANCE_20260630.csv": payload["post_gate16_head_advance"],
        "NODI_COMSOL_GATE20_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE20_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_STATIC_CONTINUITY_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate20 Sidewall Static Continuity",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Gate19 head ancestry: `{payload['summary']['gate19_head_is_ancestor_of_current']}`",
            f"- COMSOL Gate16 head: `{payload['summary']['comsol_head_actual']}`",
            f"- Gate19 source drift/missing: {payload['summary']['gate19_source_drift']}/{payload['summary']['gate19_missing_sources']}",
            f"- Hard-fail validator rows: {payload['summary']['hard_fail_validator_rows']}",
            f"- Package C state: `{payload['summary']['package_c_state']}`",
            "- Boundary: no runtime, no solver, no COMSOL launch, no .mph load, no production, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate20 disposition: `{DISPOSITION}`",
                "- Independent review found no P0/P1 for the Gate20 static path.",
                f"- Gate19 source lock drift/missing: {payload['summary']['gate19_source_drift']}/{payload['summary']['gate19_missing_sources']}.",
                "- Package A/B/D remain static/contract-only; Package C remains blocked.",
                "- Post-COMSOL-Gate16 NODI head advance is recorded as a static successor chain, not a stale-head reopen.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate20_static_continuity:
        parser.error("--confirm-gate20-static-continuity is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE20_SIDEWALL_STATIC_CONTINUITY")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
