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

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import TrapezoidCrossSection  # noqa: E402
from nodi_simulator.data_objects import Channel, OpticalSystem, SimulationConfig  # noqa: E402
from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.runtime_substep_policy import (  # noqa: E402
    TRAPEZOID_RUNTIME_SUBSTEP_POLICY_VERSION,
    build_trapezoid_runtime_substep_decision,
)
from nodi_simulator.trajectory import simulate_particle_trajectory  # noqa: E402


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET"
DISPOSITION = "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_READY_WITH_GUARDED_SMOKE"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_FAIL_CLOSED"
ARTIFACT_ID = "PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701"
CLAIM_BOUNDARY = (
    "guarded_runtime_smoke_executed_not_prs_eas_not_comsol_not_solver_wet_not_route"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Package C guarded runtime/substep smoke evidence;runtime execution packet;"
    "substep stress blocker evidence;next solver/wet preflight context"
)
BLOCKED_USE = (
    "sidewall PRS/EAS numeric output;COMSOL launch;.mph load;solver output promotion;"
    "wet claim promotion;route_score;winner;JRC;q_ch weighting;yield;detection_probability;"
    "fabrication release;production ingestion"
)

MAINLINE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_STATUS_20260701.json"
POST_PROOF_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_STATUS_20260701.json"
RUNTIME_POLICY_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"

SOURCE_FILES = {
    "authorized_mainline_status": MAINLINE_STATUS,
    "post_proof_status": POST_PROOF_STATUS,
    "runtime_substep_policy_status": RUNTIME_POLICY_STATUS,
    "runtime_substep_policy_source": PROJECT_ROOT / "nodi_simulator/runtime_substep_policy.py",
    "trajectory_source": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "execution_packet_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_runtime_substep_execution_packet.py",
    "execution_packet_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_runtime_substep_execution_packet.py",
}

OUTPUT_NAMES = {
    f"{PREFIX}_STATUS_20260701.json",
    f"{PREFIX}_CASE_RESULTS_20260701.csv",
    f"{PREFIX}_TRAJECTORY_SMOKE_SUMMARY_20260701.csv",
    f"{PREFIX}_STRESS_BLOCKERS_20260701.csv",
    f"{PREFIX}_SOURCE_LOCK_20260701.csv",
    f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
    f"{PREFIX}_SELF_REVIEW_20260701.csv",
    f"{PREFIX}_MANIFEST_20260701.csv",
    f"{PREFIX}_REPORT_20260701.json",
    "520_NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701.md",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_runtime_substep_execution_packet.py",
    "tests/test_nodi_package_c_runtime_substep_execution_packet.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}
UPSTREAM_RUNTIME_POLICY_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_"
)
UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT = (
    "reports/514_NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701.md"
)
UPSTREAM_POST_PROOF_PREFIX = (
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_"
)
UPSTREAM_POST_PROOF_PUBLIC_REPORT = (
    "reports/518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md"
)
UPSTREAM_MAINLINE_PREFIX = (
    "reports/joint_interface_20260701/NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_"
)
UPSTREAM_MAINLINE_PUBLIC_REPORT = (
    "reports/519_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701.md"
)


def upstream_runtime_policy_output(path: str) -> bool:
    return path.startswith(UPSTREAM_RUNTIME_POLICY_PREFIX) or (
        path == UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT
    )


def upstream_post_proof_output(path: str) -> bool:
    return path.startswith(UPSTREAM_POST_PROOF_PREFIX) or (
        path == UPSTREAM_POST_PROOF_PUBLIC_REPORT
    )


def upstream_mainline_output(path: str) -> bool:
    return path.startswith(UPSTREAM_MAINLINE_PREFIX) or (
        path == UPSTREAM_MAINLINE_PUBLIC_REPORT
    )

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C guarded runtime/substep execution packet."
    )
    parser.add_argument("--confirm-runtime-substep-execution-packet", action="store_true")
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
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    if path in source_paths or path in BUILD_EDIT_PATHS:
        return True
    return (
        path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_")
        or path == "reports/520_NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if Path(path).name in OUTPUT_NAMES:
            classification = "runtime_execution_packet_output"
            release_decision = "included_or_rewritten_by_execution_packet"
        elif path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "runtime_execution_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif upstream_runtime_policy_output(path):
            classification = "source_locked_upstream_runtime_policy_dirty_context"
            release_decision = "included_in_chain_rebuild_not_runtime_execution_blocker"
        elif upstream_post_proof_output(path):
            classification = "source_locked_upstream_post_proof_dirty_context"
            release_decision = "included_in_chain_rebuild_not_runtime_execution_blocker"
        elif upstream_mainline_output(path):
            classification = "source_locked_upstream_mainline_dirty_context"
            release_decision = "included_in_chain_rebuild_not_runtime_execution_blocker"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_runtime_execution_packet"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_runtime_execution_packet_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _cfg(*, taper_deg: float, total_time_s: float = 2.0e-4) -> SimulationConfig:
    return SimulationConfig(
        total_time_s=total_time_s,
        sampling_rate_Hz=4.0e4,
        mean_flow_velocity_m_s=1.0e-3,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=taper_deg,
        include_diffusion=True,
        diffusion_coefficient_m2_s=4.0e-12,
        reflecting_boundary=True,
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        random_seed=31031,
    )


def _optical() -> OpticalSystem:
    return OpticalSystem(
        wavelength_m=660e-9,
        peak_irradiance_W_m2=1.0e8,
        beam_waist_x_m=1.0e-6,
        beam_waist_y_m=1.0e-6,
        beam_waist_z_m=1.0e-6,
    )


def run_low_cost_smoke() -> tuple[dict[str, Any], dict[str, Any]]:
    channel = Channel(width_m=500e-9, depth_m=900e-9)
    cfg = _cfg(taper_deg=0.0)
    radius_m = 20e-9
    decision = build_trapezoid_runtime_substep_decision(
        channel=channel,
        sim_cfg=cfg,
        particle_radius_m=radius_m,
        surface_gap_quantile_m=7.438709749e-9,
    )
    trajectory = simulate_particle_trajectory(
        channel,
        _optical(),
        cfg,
        initial_x_m=0.0,
        initial_z_m=0.0,
        particle_radius_m=radius_m,
        diffusion_coefficient=4.0e-12,
    )
    geometry = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )
    x_values = np.asarray(trajectory["x_m"], dtype=float)
    z_values = np.asarray(trajectory["z_m"], dtype=float)
    u_values = z_values + channel.depth_m / 2.0
    support_ok = [
        geometry.contains_particle_center(float(x), float(u), radius_m)
        for x, u in zip(x_values, u_values, strict=True)
    ]
    gaps = [
        float(geometry.particle_wall_gap_diagnostics_m(float(x), float(u), radius_m)[
            "surface_gap_for_particle_m"
        ])
        for x, u in zip(x_values, u_values, strict=True)
    ]
    summary = {
        "case_id": "low_cost_theta90_D900_r20_seed31031",
        "case_role": "guarded_runtime_smoke_executed",
        "runtime_smoke_executed": "true",
        "runtime_policy_status": decision.runtime_policy_status,
        "runtime_policy_class": decision.runtime_policy_class,
        "runtime_allowed_by_guard": str(decision.runtime_allowed).lower(),
        "execution_packet_required": str(decision.execution_packet_required).lower(),
        "required_substeps_to_meet_threshold": str(decision.required_substeps_to_meet_threshold),
        "trajectory_sample_count": str(len(x_values)),
        "support_violation_count": str(sum(not ok for ok in support_ok)),
        "min_surface_gap_nm": f"{min(gaps) * 1e9:.9g}",
        "max_abs_x_nm": f"{float(np.max(np.abs(x_values))) * 1e9:.9g}",
        "max_abs_z_nm": f"{float(np.max(np.abs(z_values))) * 1e9:.9g}",
        "random_seed": str(cfg.random_seed),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return decision.to_dict(), summary


def build_stress_blocker() -> tuple[dict[str, Any], dict[str, Any]]:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=800e-9, depth_m=900e-9),
        sim_cfg=_cfg(taper_deg=20.0),
        particle_radius_m=150e-9,
        surface_gap_quantile_m=0.61687242e-9,
    )
    blocker = {
        "case_id": "narrow_tail_theta70_D900_r150",
        "case_role": "prohibitive_substep_stress_blocked",
        "runtime_smoke_executed": "false",
        "runtime_policy_status": decision.runtime_policy_status,
        "runtime_policy_class": decision.runtime_policy_class,
        "runtime_allowed_by_guard": str(decision.runtime_allowed).lower(),
        "execution_packet_required": str(decision.execution_packet_required).lower(),
        "required_substeps_to_meet_threshold": str(decision.required_substeps_to_meet_threshold),
        "stress_blocker_status": "blocked_as_expected_no_manual_waiver",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return decision.to_dict(), blocker


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "case_results": payload["case_results"],
        "smoke": payload["trajectory_smoke_summary"],
        "stress": payload["stress_blockers"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    mainline = load_json(MAINLINE_STATUS)
    post_proof = load_json(POST_PROOF_STATUS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    low_decision, smoke = run_low_cost_smoke()
    stress_decision, stress = build_stress_blocker()
    case_results = [
        {
            "case_id": smoke["case_id"],
            "case_role": smoke["case_role"],
            "runtime_policy_status": low_decision["runtime_policy_status"],
            "runtime_policy_class": low_decision["runtime_policy_class"],
            "runtime_allowed_by_guard": str(low_decision["runtime_allowed"]).lower(),
            "runtime_smoke_executed": "true",
            "sidewall_prs_eas_numeric_allowed": str(
                low_decision["sidewall_prs_eas_numeric_allowed"]
            ).lower(),
            "comsol_launch_started": "false",
            "mph_load_started": "false",
            "solver_wet_route_claim_current": "false",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "case_id": stress["case_id"],
            "case_role": stress["case_role"],
            "runtime_policy_status": stress_decision["runtime_policy_status"],
            "runtime_policy_class": stress_decision["runtime_policy_class"],
            "runtime_allowed_by_guard": str(stress_decision["runtime_allowed"]).lower(),
            "runtime_smoke_executed": "false",
            "sidewall_prs_eas_numeric_allowed": str(
                stress_decision["sidewall_prs_eas_numeric_allowed"]
            ).lower(),
            "comsol_launch_started": "false",
            "mph_load_started": "false",
            "solver_wet_route_claim_current": "false",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]
    source_missing_rows = sum(row["exists"] != "true" for row in source_lock)
    release_scoped_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    smoke_support_violations = int(smoke["support_violation_count"])
    status = (
        DISPOSITION
        if source_missing_rows == 0
        and release_scoped_dirty_blockers == 0
        and mainline.get("all_downstream_branches_authorized_to_implement") is True
        and post_proof.get("package_c_proof_artifact_registered") is True
        and smoke_support_violations == 0
        and stress["runtime_policy_status"] == "blocked_prohibitive_substep_cost"
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "runtime_policy_version": TRAPEZOID_RUNTIME_SUBSTEP_POLICY_VERSION,
        "mainline_disposition": mainline.get("disposition", ""),
        "post_proof_disposition": post_proof.get("disposition", ""),
        "package_c_proof_artifact_registered": post_proof.get(
            "package_c_proof_artifact_registered"
        )
        is True,
        "runtime_execution_packet_built": True,
        "guarded_runtime_smoke_executed": True,
        "production_runtime_execution_started": False,
        "nodi_runtime_recomputation_started": False,
        "sidewall_prs_eas_numeric_output_current": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "solver_output_current": False,
        "wet_claim_current": False,
        "route_yield_detection_claim_current": False,
        "low_cost_smoke_support_violation_count": smoke_support_violations,
        "low_cost_smoke_sample_count": int(smoke["trajectory_sample_count"]),
        "stress_required_substeps": int(stress["required_substeps_to_meet_threshold"]),
        "stress_blocked_as_expected": stress["runtime_policy_status"]
        == "blocked_prohibitive_substep_cost",
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing_rows,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_scoped_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "case_results": case_results,
        "trajectory_smoke_summary": [smoke],
        "stress_blockers": [stress],
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "low-cost guarded trajectory smoke executed",
        "support invariant checked against trapezoid geometry",
        "prohibitive 526-substep stress case blocked",
        "no PRS/EAS numeric output emitted",
        "no COMSOL launch or .mph load",
        "no solver/wet/route/yield/detection claim promotion",
    ]
    return [
        {
            "review_id": f"RUNTIME-EXEC-SELF-{idx:02d}",
            "dimension": topic,
            "verdict": "PASS_GUARDED_RUNTIME_SMOKE_NOT_FINAL_CLAIM",
            "notes": "Runtime smoke evidence is candidate execution evidence only.",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "mainline authorized": bool(s["mainline_disposition"]),
        "proof registered": s["package_c_proof_artifact_registered"] is True,
        "runtime packet built": s["runtime_execution_packet_built"] is True,
        "guarded smoke executed": s["guarded_runtime_smoke_executed"] is True,
        "smoke support invariant": s["low_cost_smoke_support_violation_count"] == 0,
        "stress blocked": s["stress_blocked_as_expected"] is True,
        "stress required substeps": s["stress_required_substeps"] == 526,
        "no production runtime": s["production_runtime_execution_started"] is False,
        "no PRS/EAS numeric": s["sidewall_prs_eas_numeric_output_current"] is False,
        "no COMSOL": s["comsol_launch_started"] is False,
        "no MPH": s["mph_load_started"] is False,
        "no solver output": s["solver_output_current"] is False,
        "no wet": s["wet_claim_current"] is False,
        "no route/yield/detection": s["route_yield_detection_claim_current"] is False,
    }
    for row in payload["case_results"]:
        checks[f"case no PRS/EAS: {row['case_id']}"] = (
            row["sidewall_prs_eas_numeric_allowed"] == "false"
            and row["solver_wet_route_claim_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Runtime/Substep Execution Packet",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Semantic digest: `{s['semantic_digest']}`.",
            "- A low-cost trapezoid guarded runtime smoke trajectory was executed with fixed seed `31031`.",
            f"- Low-cost smoke sample count: `{s['low_cost_smoke_sample_count']}`; support violations: `{s['low_cost_smoke_support_violation_count']}`.",
            f"- Prohibitive stress case required substeps: `{s['stress_required_substeps']}` and is blocked as expected.",
            "- No sidewall PRS/EAS numeric output, COMSOL launch, `.mph` load, solver/wet output, route/yield/detection claim, fabrication release, or production ingestion is created by this packet.",
            "",
        ]
    )


def artifact_manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "guarded_runtime_smoke_evidence",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    report_dir: Path = REPORT_DIR,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_CASE_RESULTS_20260701.csv": payload["case_results"],
        f"{PREFIX}_TRAJECTORY_SMOKE_SUMMARY_20260701.csv": payload[
            "trajectory_smoke_summary"
        ],
        f"{PREFIX}_STRESS_BLOCKERS_20260701.csv": payload["stress_blockers"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = output_dir / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = output_dir / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_json_path = output_dir / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_json_path, payload)
    paths.append(report_json_path)

    public_report = report_dir / "520_NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = output_dir / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, artifact_manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_runtime_substep_execution_packet:
        parser.error("--confirm-runtime-substep-execution-packet is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
