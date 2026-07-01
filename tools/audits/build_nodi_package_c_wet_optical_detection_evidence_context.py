#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.wet_optical_detection_evidence import (  # noqa: E402
    WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY,
    WET_OPTICAL_DETECTION_EVIDENCE_VERSION,
    build_wet_optical_detection_context_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT"
ARTIFACT_ID = "PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701"
DISPOSITION = "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ROUTE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_STATUS_20260701.json"
ROUTE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_ROUTE_CANDIDATE_ROWS_20260701.csv"
)
TSUYAMA_DIR = PROJECT_ROOT / "results/tsuyama_gold_aligned_detection_lane"
GOLD_ROWS = TSUYAMA_DIR / "gold_targeted_sweep_final_v1.csv"
BLANK_ROWS = TSUYAMA_DIR / "blank_fpr_sweep_v1.csv"
FEASIBLE_ROWS = TSUYAMA_DIR / "feasible_scenarios_v1.csv"
EV_PANEL_ROWS = TSUYAMA_DIR / "ev_targeted_panel_v1.csv"
EV_RANKING_ROWS = TSUYAMA_DIR / "ev_ranking_comparison_v1.csv"
TSUYAMA_TARGET_AUDIT_REPORT = (
    PROJECT_ROOT
    / "results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_target_audit_report_v1.md"
)
TSUYAMA_PHASE2_REPORT = (
    PROJECT_ROOT / "reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md"
)
DETECTOR_IDENTITY_REPORT = (
    PROJECT_ROOT
    / "reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md"
)
DEPTH_NOISE_REPORT = (
    PROJECT_ROOT / "reports/146_depth_reference_model_noise_regime_evidence_20260603.md"
)
BFP_ROI_SUMMARY = PROJECT_ROOT / "results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv"
NOISE_READOUT_SENSITIVITY = (
    PROJECT_ROOT / "results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv"
)
GREEN_TENSOR_DIAGNOSTIC = (
    PROJECT_ROOT / "results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv"
)
JONES_POLARIZATION_DIAGNOSTIC = (
    PROJECT_ROOT / "results/post_v2_physical_ceiling/vector_jones_polarization_diagnostic.csv"
)
CALIBRATION_PLAN_ADVISOR = PROJECT_ROOT / "nodi_simulator/calibration_plan_advisor.py"
CALIBRATION_MODELS = PROJECT_ROOT / "nodi_simulator/calibration_models.py"
OPTICAL_EXPOSURE_SAFETY = PROJECT_ROOT / "nodi_simulator/optical_exposure_safety.py"

ALLOWED_USE = (
    "wet/optical/detection evidence context for route candidates;"
    "sidewall-specific calibration gap prioritization"
)
BLOCKED_USE = (
    "formal route_score;winner;JRC;yield;detection_probability;true W_eff;"
    "sidewall optical solver claim;wet pass claim;fabrication release;production ingestion"
)

SOURCE_FILES = {
    "route_candidate_status": ROUTE_STATUS,
    "route_candidate_rows": ROUTE_ROWS,
    "tsuyama_gold_detection_rows": GOLD_ROWS,
    "tsuyama_blank_false_positive_rows": BLANK_ROWS,
    "tsuyama_feasible_scenarios": FEASIBLE_ROWS,
    "tsuyama_ev_targeted_panel": EV_PANEL_ROWS,
    "tsuyama_ev_ranking_comparison": EV_RANKING_ROWS,
    "tsuyama_target_audit_report": TSUYAMA_TARGET_AUDIT_REPORT,
    "tsuyama_phase2_selected_annulus_report": TSUYAMA_PHASE2_REPORT,
    "detector_identity_report_147": DETECTOR_IDENTITY_REPORT,
    "depth_noise_report_146": DEPTH_NOISE_REPORT,
    "calibration_plan_advisor": CALIBRATION_PLAN_ADVISOR,
    "calibration_models": CALIBRATION_MODELS,
    "optical_exposure_safety": OPTICAL_EXPOSURE_SAFETY,
    "tsuyama_gold_aligned_detection_lane_builder": PROJECT_ROOT
    / "tools/audits/tsuyama_gold_aligned_detection_lane.py",
    "tsuyama_detection_rate_calibration_builder": PROJECT_ROOT
    / "tools/audits/tsuyama_detection_rate_calibration.py",
    "wet_optical_detection_source": PROJECT_ROOT
    / "nodi_simulator/wet_optical_detection_evidence.py",
    "wet_optical_detection_tests": PROJECT_ROOT
    / "tests/test_wet_optical_detection_evidence.py",
    "wet_optical_detection_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_wet_optical_detection_evidence_context.py",
    "wet_optical_detection_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_wet_optical_detection_evidence_context.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/wet_optical_detection_evidence.py",
    "tests/test_wet_optical_detection_evidence.py",
    "tools/audits/build_nodi_package_c_wet_optical_detection_evidence_context.py",
    "tests/test_nodi_package_c_wet_optical_detection_evidence_context.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C wet/optical/detection evidence-context packet."
    )
    parser.add_argument("--confirm-wet-optical-detection-context", action="store_true")
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_"
        )
        or path == "reports/525_NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "wet_optical_detection_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_"
        ) or path == "reports/525_NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701.md":
            classification = "wet_optical_detection_output"
            release_decision = "included_or_rewritten_by_wet_optical_detection_context"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_wet_optical_detection_context"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_optical_detection_context_not_source_locked"
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
                "claim_boundary": WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def evidence_context_rows() -> list[dict[str, str]]:
    rows = build_wet_optical_detection_context_rows(
        route_candidate_rows=read_csv_rows(ROUTE_ROWS),
        gold_rows=read_csv_rows(GOLD_ROWS),
        blank_rows=read_csv_rows(BLANK_ROWS),
        feasible_rows=read_csv_rows(FEASIBLE_ROWS),
        ev_panel_rows=read_csv_rows(EV_PANEL_ROWS),
        ranking_rows=read_csv_rows(EV_RANKING_ROWS),
    )
    return [_stringify_row(row.to_dict()) for row in rows]


def promotion_gap_rows() -> list[dict[str, str]]:
    return [
        {
            "target": "sidewall_specific_detection_probability",
            "current_value": "false",
            "context_available": "true",
            "required_before_true": (
                "sidewall-specific optical/reference solver or calibration consuming "
                "trapezoid geometry plus detector-response validation"
            ),
            "hard_fail_if": "detection_probability_true_from_tsuyama_context_only",
        },
        {
            "target": "wet_yield_or_recovery",
            "current_value": "false",
            "context_available": "true",
            "required_before_true": (
                "wet EV pass/recovery controls, sample handling evidence, and "
                "sidewall/roughness/adsorption assumptions"
            ),
            "hard_fail_if": "yield_true_from_ev_panel_surrogate_only",
        },
        {
            "target": "route_score_or_winner",
            "current_value": "false",
            "context_available": "true",
            "required_before_true": (
                "accepted q_ch sidecar, exact pressure-flow validation, "
                "sidewall optical/wet evidence, and decision ledger"
            ),
            "hard_fail_if": "route_score_true_from_context_candidate_metric_only",
        },
        {
            "target": "selected_annulus_detection_claim",
            "current_value": "false",
            "context_available": "partial",
            "required_before_true": (
                "rerun EV panel with selected-annulus columns and sidewall-aware "
                "PRS/bin mapping"
            ),
            "hard_fail_if": "selected_annulus_claim_true_with_missing_annulus_columns",
        },
    ]


def boundary_context_rows() -> list[dict[str, str]]:
    rows = [
        (
            "tsuyama_target_audit",
            TSUYAMA_TARGET_AUDIT_REPORT,
            "tsuyama_detection_target_claim_layering_context",
            "direct/inferred/operational/diagnostic-only target separation; does not certify sidewall detection probability",
        ),
        (
            "tsuyama_phase2_selected_annulus",
            TSUYAMA_PHASE2_REPORT,
            "selected_annulus_negative_or_diagnostic_context",
            "selected-annulus analysis remains diagnostic and requires rerun with current sidewall bins before Package D use",
        ),
        (
            "detector_identity_report_147",
            DETECTOR_IDENTITY_REPORT,
            "detector_forward_identity_unresolved_context",
            "detector identity is a high-priority optical boundary; prevents true detector-response claim from context rows alone",
        ),
        (
            "depth_noise_report_146",
            DEPTH_NOISE_REPORT,
            "depth_reference_noise_sensitivity_context",
            "depth/noise sensitivity motivates measured blank and transfer calibration before detection probability",
        ),
        (
            "bfp_roi_operator_summary",
            BFP_ROI_SUMMARY,
            "bfp_roi_diagnostic_context",
            "BFP ROI rows are diagnostic detector/operator context, not sidewall optical solver output",
        ),
        (
            "noise_readout_route_sensitivity",
            NOISE_READOUT_SENSITIVITY,
            "noise_readout_diagnostic_context",
            "noise/readout sensitivity is a calibration requirement, not a final detection probability",
        ),
        (
            "green_tensor_diagnostic",
            GREEN_TENSOR_DIAGNOSTIC,
            "full_wave_green_tensor_surrogate_risk_context",
            "physical-ceiling diagnostic flags optical-solver risk; it is not true sidewall reference-field output",
        ),
        (
            "jones_polarization_diagnostic",
            JONES_POLARIZATION_DIAGNOSTIC,
            "vector_jones_polarization_surrogate_risk_context",
            "polarization diagnostic flags solver/model risk; it is not a calibrated detector response",
        ),
        (
            "calibration_plan_advisor",
            CALIBRATION_PLAN_ADVISOR,
            "wet_optical_calibration_plan_context",
            "maps missing evidence to calibration work; it does not unlock wet/yield/detection claims",
        ),
        (
            "calibration_models",
            CALIBRATION_MODELS,
            "calibration_model_template_context",
            "calibration models remain templates until bound to measured sidewall/optical/wet data",
        ),
        (
            "optical_exposure_safety",
            OPTICAL_EXPOSURE_SAFETY,
            "exposure_photodamage_guard_context",
            "exposure safety guard is a risk/control context, not a safe-power or wet-pass conclusion",
        ),
    ]
    dirty_paths = {git_path_from_status_line(line) for line in git_status_lines()}
    out: list[dict[str, str]] = []
    for context_id, path, context_role, claim_boundary in rows:
        display = display_path(path)
        source_locked = path.exists() and display not in dirty_paths
        out.append(
            {
            "context_id": context_id,
            "path": display,
            "exists": str(path.exists()).lower(),
            "source_lock_status": (
                "source_locked_clean_git_context"
                if source_locked
                else "deferred_dirty_local_context_not_source_locked"
                if path.exists()
                else "missing_context_source"
            ),
            "sha256": sha256_file(path) if source_locked else "",
            "context_role": context_role,
            "claim_boundary": claim_boundary,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            }
        )
    return out


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "existing Tsuyama detection lane artifacts are source-locked",
        "W500/D900 route candidates are nearest-geometry context, not exact sidewall detection calibration",
        "blank false-positive guard is bound as context",
        "EV weighted panel is bound as surrogate wet/detection context, not wet experiment",
        "route/yield/detection final claims remain false",
    ]
    return [
        {
            "review_id": f"WOD-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_WET_OPTICAL_DETECTION_CONTEXT_NOT_FINAL",
            "notes": (
                "This packet advances the wet/optical/detection branch by binding "
                "evidence context while preserving final-claim prerequisites."
            ),
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    route_status = load_json(ROUTE_STATUS)
    rows = evidence_context_rows()
    boundary_rows = boundary_context_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and route_status.get("disposition")
        == "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_READY_NOT_FINAL"
        and len(rows) >= 2
        and all(row["detection_probability_current"] == "false" for row in rows)
        and all(row["yield_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "evidence_context_version": WET_OPTICAL_DETECTION_EVIDENCE_VERSION,
        "source_route_disposition": route_status.get("disposition", ""),
        "evidence_context_rows": len(rows),
        "nearest_geometry_context_rows": sum(
            row["geometry_match_level"] == "nearest_width_depth_context_only"
            for row in rows
        ),
        "detection_context_available_rows": sum(
            row["detection_context_status"]
            != "tsuyama_detection_context_missing"
            for row in rows
        ),
        "wet_context_available_rows": sum(
            row["wet_context_status"]
            != "wet_ev_panel_context_missing"
            for row in rows
        ),
        "boundary_context_rows": len(boundary_rows),
        "deferred_dirty_boundary_context_rows": sum(
            row["source_lock_status"] == "deferred_dirty_local_context_not_source_locked"
            for row in boundary_rows
        ),
        "sidewall_specific_optical_solver_current": False,
        "sidewall_specific_wet_evidence_current": False,
        "detection_probability_current": False,
        "yield_current": False,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "evidence_context_rows": rows,
        "promotion_gaps": promotion_gap_rows(),
        "boundary_context_rows": boundary_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "evidence_context_rows": payload["evidence_context_rows"],
        "promotion_gaps": payload["promotion_gaps"],
        "boundary_context_rows": payload["boundary_context_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "evidence rows present": summary["evidence_context_rows"] >= 2,
        "detection context available": summary["detection_context_available_rows"] >= 2,
        "wet context available": summary["wet_context_available_rows"] >= 2,
        "sidewall optical solver false": summary["sidewall_specific_optical_solver_current"] is False,
        "sidewall wet false": summary["sidewall_specific_wet_evidence_current"] is False,
        "detection probability false": summary["detection_probability_current"] is False,
        "yield false": summary["yield_current"] is False,
        "route score false": summary["route_score_current"] is False,
        "winner false": summary["winner_current"] is False,
    }
    for row in payload["evidence_context_rows"]:
        checks[f"row not final {row['route_candidate_id']}"] = (
            row["detection_probability_current"] == "false"
            and row["yield_current"] == "false"
            and row["route_score_current"] == "false"
            and row["winner_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_EVIDENCE_CONTEXT_ROWS_20260701.csv": payload["evidence_context_rows"],
        f"{PREFIX}_PROMOTION_GAPS_20260701.csv": payload["promotion_gaps"],
        f"{PREFIX}_BOUNDARY_CONTEXT_ROWS_20260701.csv": payload["boundary_context_rows"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = REPORT_DIR / "525_NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Wet/Optical/Detection Evidence Context",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Evidence context version: `{s['evidence_context_version']}`.",
            f"- Evidence context rows: `{s['evidence_context_rows']}`.",
            f"- Detection context rows available: `{s['detection_context_available_rows']}`.",
            f"- Wet/EV context rows available: `{s['wet_context_available_rows']}`.",
            f"- Boundary context rows: `{s['boundary_context_rows']}`.",
            f"- Deferred dirty local boundary contexts not source-locked: `{s['deferred_dirty_boundary_context_rows']}`.",
            "- The packet binds existing Tsuyama gold-aligned detection, blank-FPR, feasible-scenario, EV-panel, and ranking artifacts to the current Package C route candidates.",
            "- Detector identity, depth/noise, calibration-plan, exposure-safety, and diagnostic optical-risk contexts are recorded separately so they cannot be mistaken for sidewall-specific optical or wet validation.",
            "- These rows are context evidence only. They are not sidewall-specific optical solver output, wet pass/recovery evidence, final route_score, winner/JRC, yield, or detection probability.",
            "",
        ]
    )


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "wet_optical_detection_context_not_final",
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


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        if isinstance(value, bool):
            out[key] = str(value).lower()
        elif isinstance(value, float):
            if value != value:
                out[key] = "nan"
            else:
                out[key] = f"{value:.12g}"
        else:
            out[key] = str(value)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_wet_optical_detection_context:
        parser.error("--confirm-wet-optical-detection-context is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
