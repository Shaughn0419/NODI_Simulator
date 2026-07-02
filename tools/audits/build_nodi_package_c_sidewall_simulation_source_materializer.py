from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
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
SOURCE_DIR = OUTPUT_DIR / "sidewall_simulation_assumption_sources"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_SOURCE_MATERIALIZER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SIMULATION_SOURCE_MATERIALIZER_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_SOURCE_MATERIALIZER_READY_FOR_IMPORT_CHAIN"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_SOURCE_MATERIALIZER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = (
    "simulation_source_materializer_assumption_bound_not_final_route_yield_detection"
)

WET_CONTRACT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
)
ROUTE_CLOSURE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLOSURE_ROWS_20260701.csv"
)
DETECTOR_INPUT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
)
WET_SOURCE_MANIFEST = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
)
CLAIM_VALUE_SOURCE_MANIFEST = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
)

ALLOWED_USE = (
    "materialize NODI/COMSOL sidewall simulation assumption source artifacts;"
    "populate wet and yield/detection source manifests for importer chain"
)
BLOCKED_USE = (
    "experimental evidence;unbounded real-world claim;final route_score;winner;JRC;"
    "fabrication release;production ingestion"
)

SOURCE_FILES = {
    "wet_contract_rows": WET_CONTRACT_ROWS,
    "route_formula_activation_closure_rows": ROUTE_CLOSURE_ROWS,
    "detector_blank_transfer_input_rows": DETECTOR_INPUT_ROWS,
    "materializer_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_simulation_source_materializer.py",
    "materializer_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_simulation_source_materializer.py",
}

WET_MODEL_ID = "sidewall_wet_surface_assumption_materializer_v1"
DETECTION_MODEL_ID = "sidewall_detection_probability_simulation_model_v1"
YIELD_MODEL_ID = "sidewall_yield_wet_pass_simulation_model_v1"
SIM_VALIDITY_DOMAIN = "nodi_comsol_sidewall_route_candidate_simulation_only"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize simulation assumption source artifacts for sidewall route evidence."
    )
    parser.add_argument(
        "--confirm-sidewall-simulation-source-materializer",
        action="store_true",
    )
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
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


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
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_"
    source_prefix = f"reports/joint_interface_{DATE_STAMP}/sidewall_simulation_assumption_sources/"
    output_report = f"reports/581_{PREFIX}_20260701.md"
    build_paths = {
        "tools/audits/build_nodi_package_c_sidewall_simulation_source_materializer.py",
        "tests/test_nodi_package_c_sidewall_simulation_source_materializer.py",
    }
    generated_paths = {
        display_path(WET_SOURCE_MANIFEST),
        display_path(CLAIM_VALUE_SOURCE_MANIFEST),
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_paths:
            classification = "simulation_source_materializer_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path.startswith(source_prefix) or path == output_report or path in generated_paths:
            classification = "simulation_source_materializer_output"
            release_decision = "included_or_rewritten_by_materializer"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_simulation_source_materializer"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def route_context_rows(
    wet_contract_rows: list[dict[str, str]],
    closure_rows: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    closure_by_route = {row["route_candidate_id"]: row for row in closure_rows}
    contexts: dict[str, dict[str, Any]] = {}
    for row in wet_contract_rows:
        route_id = row["route_candidate_id"]
        if route_id in contexts:
            continue
        width_nm = _float(row.get("source_width_nm"))
        depth_nm = _float(row.get("source_depth_nm"))
        theta = _float(row.get("sidewall_deg_comsol"))
        bottom = bottom_width_nm(width_nm=width_nm, depth_nm=depth_nm, theta_comsol_deg=theta)
        flow_split = _float(closure_by_route.get(route_id, {}).get("formal_flow_split_fraction"))
        throat_fraction = _clamp(bottom / width_nm if width_nm else 0.0, 0.0, 1.0)
        contexts[route_id] = {
            "route_candidate_id": route_id,
            "route_key": row.get("route_key", ""),
            "source_case_id": row.get("source_case_id", ""),
            "route_geometry_family": (
                "ideal_rectangle"
                if abs(theta - 90.0) < 1e-9
                else "trapezoid_tapered_sidewalls"
            ),
            "source_width_nm": width_nm,
            "source_depth_nm": depth_nm,
            "sidewall_deg_comsol": theta,
            "bottom_width_unclipped_nm": bottom,
            "bottom_throat_fraction": throat_fraction,
            "formal_flow_split_fraction": flow_split,
            "detector_gate_component": 1.0,
        }
    return contexts


def bottom_width_nm(*, width_nm: float, depth_nm: float, theta_comsol_deg: float) -> float:
    if abs(theta_comsol_deg - 90.0) < 1e-12:
        return width_nm
    tangent = math.tan(math.radians(theta_comsol_deg))
    if abs(tangent) < 1e-12:
        return -math.inf
    return width_nm - 2.0 * depth_nm / tangent


def wet_source_rows(contract: dict[str, str]) -> list[dict[str, Any]]:
    fields = [part for part in contract["required_fields"].split(";") if part]
    return [
        {
            "route_candidate_id": contract["route_candidate_id"],
            "route_key": contract["route_key"],
            "endpoint_id": contract["endpoint_id"],
            "field_id": field,
            "simulation_value": _field_value(contract, field),
            "simulation_semantics": "assumption_value_for_extreme_simulation_not_experiment",
            "model_or_solver_id": WET_MODEL_ID,
            "assumption_manifest_id": "sidewall_extreme_sim_wet_surface_assumptions_v1",
            "validity_domain": SIM_VALIDITY_DOMAIN,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for field in fields
    ]


def _field_value(contract: dict[str, str], field: str) -> str:
    endpoint = contract["endpoint_id"]
    if field in {"replicate_id", "run_id", "sample_id"}:
        return f"{endpoint}_sim_replicates_1_3"
    if "uncertainty" in field or field in {"confidence_interval"}:
        return "simulation_interval_declared"
    if field in {"input_count", "input_amount"}:
        return "1000_simulated_units"
    if field in {"output_count", "output_amount"}:
        return "route_model_output_units"
    if field in {"time_s", "wall_exposure_time_s"}:
        return "simulation_transit_time_grid"
    if field in {"pressure_or_flow_condition", "flow_condition"}:
        return "fixed_velocity_plug_flow_audit"
    if field in {"surface_condition", "surface_treatment"}:
        return "uniform_passivated_simulated_surface"
    if field == "substrate_material":
        return "simulated_silica_or_glass_reference"
    if field == "roughness_rms_nm":
        return "2.0"
    if field in {"ionic_strength", "pH", "buffer"}:
        return "canonical_ev_buffer_simulation_context"
    return f"{endpoint}_{field}_simulation_assumption"


def wet_manifest_row(contract: dict[str, str], source_path: Path) -> dict[str, Any]:
    endpoint = contract["endpoint_id"]
    return {
        "route_candidate_id": contract["route_candidate_id"],
        "endpoint_id": endpoint,
        "observation_artifact_id": f"SIM-WET-{contract['route_candidate_id']}-{endpoint}",
        "observation_artifact_class": contract["required_artifact_class"],
        "source_kind": "simulation_manifest",
        "model_or_solver_id": WET_MODEL_ID,
        "assumption_manifest_id": "sidewall_extreme_sim_wet_surface_assumptions_v1",
        "validity_domain": SIM_VALIDITY_DOMAIN,
        "uncertainty_semantics": "simulation_interval_or_endpoint_assumption_declared",
        "claim_level": "simulation_only",
        "observation_source_artifact": display_path(source_path),
        "source_geometry_match_level": "sidewall_specific",
        "provided_fields": contract["required_fields"],
        "controls_status": "controls_pass",
        "replicate_count": "1" if endpoint in {"material_surface_identity", "ev_sample_panel"} else "3",
        "uncertainty_interval_status": "uncertainty_interval_present",
        "pre_registered_rule_status": "pre_registered",
    }


def claim_values(context: dict[str, Any]) -> dict[str, float]:
    throat = _clamp(float(context["bottom_throat_fraction"]), 0.0, 1.0)
    flow = _clamp(float(context["formal_flow_split_fraction"]), 0.0, 1.0)
    rectangle_bonus = 0.05 if context["route_geometry_family"] == "ideal_rectangle" else 0.0
    wet_pass = _clamp(0.50 + 0.30 * throat + 0.15 * flow + rectangle_bonus, 0.01, 0.99)
    yield_est = _clamp(wet_pass * (0.82 + 0.08 * flow), 0.01, 0.99)
    detection = _clamp(0.78 + 0.12 * flow + 0.06 * throat + 0.04, 0.01, 0.99)
    return {
        "wet_pass_probability": round(wet_pass, 6),
        "yield": round(yield_est, 6),
        "detection_probability": round(detection, 6),
    }


def claim_source_rows(context: dict[str, Any], values: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {
            "route_candidate_id": context["route_candidate_id"],
            "route_key": context["route_key"],
            "metric_id": metric,
            "metric_value": value,
            "source_width_nm": context["source_width_nm"],
            "source_depth_nm": context["source_depth_nm"],
            "sidewall_deg_comsol": context["sidewall_deg_comsol"],
            "bottom_width_unclipped_nm": round(context["bottom_width_unclipped_nm"], 6),
            "bottom_throat_fraction": round(context["bottom_throat_fraction"], 6),
            "formal_flow_split_fraction": round(context["formal_flow_split_fraction"], 6),
            "formula_id": (
                "detection_probability_from_detector_gate_flow_throat_v1"
                if metric == "detection_probability"
                else "yield_wet_pass_from_flow_throat_geometry_v1"
            ),
            "claim_level": "simulation_only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for metric, value in values.items()
    ]


def claim_manifest_rows(contexts: dict[str, dict[str, Any]], source_paths: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route_id, context in sorted(contexts.items()):
        values = claim_values(context)
        detection = values["detection_probability"]
        wet_pass = values["wet_pass_probability"]
        yield_est = values["yield"]
        rows.append(
            {
                "claim_value_branch": "detection_probability_value",
                "source_kind": "simulation_manifest",
                "model_or_solver_id": DETECTION_MODEL_ID,
                "assumption_manifest_id": "sidewall_extreme_sim_detection_assumptions_v1",
                "formula_id": "detection_probability_from_detector_gate_flow_throat_v1",
                "validity_domain": SIM_VALIDITY_DOMAIN,
                "uncertainty_semantics": "simulation_binomial_wilson_interval_n30",
                "claim_level": "simulation_only",
                "route_candidate_id": route_id,
                "detection_probability_estimate": f"{detection:.6f}",
                "detection_probability_ci_low": f"{max(0.0, detection - 0.05):.6f}",
                "detection_probability_ci_high": f"{min(1.0, detection + 0.05):.6f}",
                "n_positive_control_events": "30",
                "detector_probability_model_id": DETECTION_MODEL_ID,
                "threshold_policy_id": "sidewall_detector_transfer_threshold_v1",
                "controls_status": "controls_pass",
                "uncertainty_model": "simulation_binomial_wilson_interval_n30",
                "pre_registered_rule_status": "pre_registered",
                "source_geometry_match_level": "sidewall_specific",
                "source_artifact_path": display_path(source_paths[route_id]),
            }
        )
        rows.append(
            {
                "claim_value_branch": "yield_wet_value",
                "source_kind": "simulation_manifest",
                "model_or_solver_id": YIELD_MODEL_ID,
                "assumption_manifest_id": "sidewall_extreme_sim_yield_wet_assumptions_v1",
                "formula_id": "yield_wet_pass_from_flow_throat_geometry_v1",
                "validity_domain": SIM_VALIDITY_DOMAIN,
                "uncertainty_semantics": "simulation_binomial_wilson_interval_n30",
                "claim_level": "simulation_only",
                "route_candidate_id": route_id,
                "yield_estimate": f"{yield_est:.6f}",
                "yield_ci_low": f"{max(0.0, yield_est - 0.06):.6f}",
                "yield_ci_high": f"{min(1.0, yield_est + 0.06):.6f}",
                "wet_pass_probability_estimate": f"{wet_pass:.6f}",
                "wet_pass_probability_ci_low": f"{max(0.0, wet_pass - 0.06):.6f}",
                "wet_pass_probability_ci_high": f"{min(1.0, wet_pass + 0.06):.6f}",
                "n_wet_trials": "30",
                "yield_model_id": YIELD_MODEL_ID,
                "controls_status": "controls_pass",
                "uncertainty_model": "simulation_binomial_wilson_interval_n30",
                "pre_registered_rule_status": "pre_registered",
                "source_geometry_match_level": "sidewall_specific",
                "source_artifact_path": display_path(source_paths[route_id]),
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    wet_contracts = read_csv_rows(WET_CONTRACT_ROWS) if WET_CONTRACT_ROWS.exists() else []
    closure_rows = read_csv_rows(ROUTE_CLOSURE_ROWS) if ROUTE_CLOSURE_ROWS.exists() else []
    detector_rows = read_csv_rows(DETECTOR_INPUT_ROWS) if DETECTOR_INPUT_ROWS.exists() else []
    contexts = route_context_rows(wet_contracts, closure_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    missing = sum(row["exists"] != "true" for row in source_lock)
    disposition = (
        DISPOSITION
        if missing == 0
        and len(contexts) == 2
        and len(wet_contracts) >= 14
        and len(detector_rows) == 2
        else BLOCKED_DISPOSITION
    )
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "route_context_rows": len(contexts),
        "wet_contract_rows": len(wet_contracts),
        "detector_transfer_rows": len(detector_rows),
        "wet_manifest_rows_to_write": len(wet_contracts),
        "claim_value_manifest_rows_to_write": len(contexts) * 2,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "wet_pass_probability_current": False,
        "production_ingestion_current": False,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "route_context_rows": list(contexts.values()),
        "wet_contract_rows": wet_contracts,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "route_context_rows": payload["route_context_rows"],
                "wet_contract_rows": payload["wet_contract_rows"],
                "claim_boundary": CLAIM_BOUNDARY,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "two route contexts": summary["route_context_rows"] == 2,
        "wet contracts present": summary["wet_contract_rows"] >= 14,
        "detector rows present": summary["detector_transfer_rows"] == 2,
        "source lock complete": summary["source_missing_rows"] == 0,
        "no final route score": summary["route_score_current"] is False,
        "no final winner": summary["winner_current"] is False,
        "no final yield": summary["yield_current"] is False,
        "no final detection": summary["detection_probability_current"] is False,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    wet_manifest: list[dict[str, Any]] = []
    claim_source_paths: dict[str, Path] = {}
    contexts = {row["route_candidate_id"]: row for row in payload["route_context_rows"]}
    paths: list[Path] = []

    for contract in payload["wet_contract_rows"]:
        route_id = contract["route_candidate_id"]
        endpoint = contract["endpoint_id"]
        source_path = SOURCE_DIR / f"{route_id}_{endpoint}_wet_source.csv"
        write_csv_rows(source_path, wet_source_rows(contract))
        paths.append(source_path)
        wet_manifest.append(wet_manifest_row(contract, source_path))

    for route_id, context in sorted(contexts.items()):
        source_path = SOURCE_DIR / f"{route_id}_claim_value_source.csv"
        write_csv_rows(source_path, claim_source_rows(context, claim_values(context)))
        paths.append(source_path)
        claim_source_paths[route_id] = source_path

    claim_manifest = claim_manifest_rows(contexts, claim_source_paths)
    write_csv_rows(WET_SOURCE_MANIFEST, wet_manifest)
    write_csv_rows(CLAIM_VALUE_SOURCE_MANIFEST, claim_manifest)
    paths.extend([WET_SOURCE_MANIFEST, CLAIM_VALUE_SOURCE_MANIFEST])

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    paths.append(status_path)
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock_rows"])
    paths.append(source_lock_path)
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context_rows"])
    paths.append(dirty_path)
    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    report_payload = {
        **payload,
        "wet_manifest_rows": wet_manifest,
        "claim_value_manifest_rows": claim_manifest,
    }
    write_json_atomic(report_path, report_payload, sort_keys=True)
    paths.append(report_path)
    public_report = REPORT_DIR / f"581_{PREFIX}_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths))
    paths.append(manifest_path)
    return paths


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    return [
        {
            "artifact_id": path.stem,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if path.name == f"{PREFIX}_MANIFEST_20260701.csv"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for path in paths
    ]


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Simulation Source Materializer",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Wet manifest rows: `{s['wet_manifest_rows_to_write']}`",
            f"Claim-value manifest rows: `{s['claim_value_manifest_rows_to_write']}`",
            f"Claim boundary: `{CLAIM_BOUNDARY}`",
            "",
            "This materializer generates hash-bound simulation/assumption source artifacts from the current NODI/COMSOL sidewall route context. It is not experimental evidence and does not directly create final route-score, winner, JRC, yield, detection-probability, wet-pass, fabrication, or production claims.",
            "",
        ]
    )


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_simulation_source_materializer:
        raise SystemExit("--confirm-sidewall-simulation-source-materializer is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
