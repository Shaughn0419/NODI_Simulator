"""P1 physical-ceiling diagnostic and manifest helpers.

This module emits bounded no-solver rank diagnostics from existing P0 relative
audit evidence. It does not run physical solvers, simulations, calibrations, or
measured-data ingestion.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_csv_rows, write_json_atomic
from .review_package import PROJECT_ROOT


PHYSICAL_CEILING_DIR = Path("results/post_v2_physical_ceiling")
PHYSICAL_CEILING_CONTRACT_MANIFEST = (
    PHYSICAL_CEILING_DIR / "physical_ceiling_contract_manifest.json"
)
PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST = (
    PHYSICAL_CEILING_DIR / "physical_ceiling_diagnostic_schema_manifest.json"
)
PHYSICAL_CEILING_INPUT_BINDING_MANIFEST = (
    PHYSICAL_CEILING_DIR / "physical_ceiling_input_binding_manifest.json"
)
PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST = (
    PHYSICAL_CEILING_DIR / "physical_ceiling_route_coverage_manifest.json"
)
FULL_WAVE_GREEN_TENSOR_DIAGNOSTIC = (
    PHYSICAL_CEILING_DIR / "full_wave_green_tensor_diagnostic.csv"
)
VECTOR_JONES_POLARIZATION_DIAGNOSTIC = (
    PHYSICAL_CEILING_DIR / "vector_jones_polarization_diagnostic.csv"
)
ROUGHNESS_LEAKAGE_DIAGNOSTIC = PHYSICAL_CEILING_DIR / "roughness_leakage_diagnostic.csv"
TRANSPORT_RESIDENCE_TIME_DIAGNOSTIC = (
    PHYSICAL_CEILING_DIR / "transport_residence_time_diagnostic.csv"
)

DIAGNOSTIC_SCHEMA_VERSION = "ev_nodi_p1_physical_ceiling_no_solver_diagnostic_v1"
P0_MANDATORY_AUDIT_PATH = (
    "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv"
)
P0_PAIRWISE_INVERSION_PATH = (
    "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv"
)

CONTRACT_CONFIG_PATHS: tuple[str, ...] = (
    "configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml",
    "configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml",
    "configs/realism_v2/roughness_leakage_diagnostic_contract.yaml",
    "configs/realism_v2/transport_residence_time_diagnostic_contract.yaml",
)

LANE_REPORT_PATHS: tuple[str, ...] = (
    "reports/93_EV_NODI_P1_full_wave_green_tensor_diagnostic_contract.md",
    "reports/94_EV_NODI_P1_vector_jones_polarization_diagnostic_contract.md",
    "reports/95_EV_NODI_P1_roughness_leakage_diagnostic_contract.md",
    "reports/96_EV_NODI_P1_transport_residence_time_diagnostic_contract.md",
)

PHYSICAL_CEILING_README = PHYSICAL_CEILING_DIR / "README.md"


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _to_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _rank_percentiles_from_scores(
    rows: list[dict[str, str]], scores: dict[str, float]
) -> dict[str, tuple[int, float]]:
    ranked = sorted(
        rows,
        key=lambda row: (-scores[row["candidate_id"]], row["candidate_id"]),
    )
    total = len(ranked)
    result: dict[str, tuple[int, float]] = {}
    index = 0
    while index < total:
        score = scores[ranked[index]["candidate_id"]]
        end = index + 1
        while end < total and scores[ranked[end]["candidate_id"]] == score:
            end += 1
        average_rank = ((index + 1) + end) / 2.0
        percentile = 1.0 if total == 1 else 1.0 - ((average_rank - 1.0) / (total - 1.0))
        for row in ranked[index:end]:
            result[row["candidate_id"]] = (int(round(average_rank)), percentile)
        index = end
    return result


def _order_from_values(candidate_a: str, candidate_b: str, values: dict[str, float]) -> str:
    a_value = values[candidate_a]
    b_value = values[candidate_b]
    if abs(a_value - b_value) <= 1e-12:
        return "tie"
    if a_value > b_value:
        return "candidate_a_above_b"
    return "candidate_b_above_a"


def _pairwise_inversion_candidate_ids(
    project_root: Path,
    rows: list[dict[str, str]],
    diagnostic_percentiles: dict[str, float],
) -> set[str]:
    scalar = {
        row["candidate_id"]: _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        for row in rows
    }
    inverted: set[str] = set()
    for pair in _read_csv_dicts(project_root / P0_PAIRWISE_INVERSION_PATH):
        candidate_a = pair["candidate_a"]
        candidate_b = pair["candidate_b"]
        if candidate_a not in scalar or candidate_b not in scalar:
            continue
        if _order_from_values(candidate_a, candidate_b, scalar) != _order_from_values(
            candidate_a, candidate_b, diagnostic_percentiles
        ):
            inverted.update((candidate_a, candidate_b))
    return inverted


def _risk_label(delta: float, pairwise_inversion: bool, extra_medium: bool = False) -> str:
    if pairwise_inversion or abs(delta) >= 0.25:
        return "high_surrogate_risk"
    if abs(delta) >= 0.10 or extra_medium:
        return "medium_surrogate_risk"
    return "low_surrogate_risk"


def _reason_codes(
    *,
    lane_code: str,
    delta: float,
    pairwise_inversion: bool,
    extra_codes: list[str] | None = None,
) -> str:
    codes = [f"{lane_code}.NO_SOLVER_RANK_PROXY"]
    if abs(delta) >= 0.25:
        codes.append(f"{lane_code}.RANK_PERCENTILE_SHIFT_MAJOR")
    elif abs(delta) >= 0.10:
        codes.append(f"{lane_code}.RANK_PERCENTILE_SHIFT_MODERATE")
    if pairwise_inversion:
        codes.append(f"{lane_code}.PAIRWISE_ORDER_SHIFT")
    if extra_codes:
        codes.extend(extra_codes)
    return ";".join(codes)


def _load_contract(project_root: Path, relpath: str) -> dict[str, Any]:
    return load_json_yaml(project_root / relpath)


def build_full_wave_green_tensor_diagnostic_rows(
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Build a no-solver Green-tensor ceiling proxy from P0 rank evidence."""
    audit_rows = _read_csv_dicts(project_root / P0_MANDATORY_AUDIT_PATH)
    scores = {
        row["candidate_id"]: (
            0.45 * _to_float(row, "bfp_roi_rank_percentile_in_stratum")
            + 0.45 * _to_float(row, "tsuyama_signal_rank_percentile_in_stratum")
            + 0.10
            * (1.0 - min(_to_float(row, "noise_max_abs_percentile_delta_vs_nominal"), 1.0))
        )
        for row in audit_rows
    }
    ranks = _rank_percentiles_from_scores(audit_rows, scores)
    percentiles = {
        candidate_id: percentile for candidate_id, (_, percentile) in ranks.items()
    }
    pairwise = _pairwise_inversion_candidate_ids(project_root, audit_rows, percentiles)
    output_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        candidate_id = row["candidate_id"]
        percentile = percentiles[candidate_id]
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        delta = percentile - scalar
        pairwise_flag = candidate_id in pairwise
        output_rows.append(
            {
                "diagnostic_schema_version": DIAGNOSTIC_SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "route_key": row["route_key"],
                "comparison_stratum": row["comparison_stratum"],
                "v1_scalar_rank_percentile_in_stratum": scalar,
                "bfp_roi_rank_percentile_in_stratum": row[
                    "bfp_roi_rank_percentile_in_stratum"
                ],
                "green_tensor_rank_percentile_in_stratum": percentile,
                "green_tensor_vs_v1_rank_percentile_delta": delta,
                "green_tensor_pairwise_inversion_flag": pairwise_flag,
                "surrogate_risk_label": _risk_label(delta, pairwise_flag),
                "surrogate_risk_reason_codes": _reason_codes(
                    lane_code="GREEN_TENSOR",
                    delta=delta,
                    pairwise_inversion=pairwise_flag,
                ),
                "raw_complex_field_proxy_diagnostic_only": scores[candidate_id],
                "raw_magnitude_final_gate_allowed": False,
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "physical_ceiling_role": "surrogate_risk_reduction_only",
            }
        )
    return output_rows


def build_vector_jones_polarization_diagnostic_rows(
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Build a no-solver Jones/polarization proxy from BFP audit evidence."""
    audit_rows = _read_csv_dicts(project_root / P0_MANDATORY_AUDIT_PATH)
    percentiles = {
        row["candidate_id"]: _to_float(row, "bfp_roi_rank_percentile_in_stratum")
        for row in audit_rows
    }
    pairwise = _pairwise_inversion_candidate_ids(project_root, audit_rows, percentiles)
    output_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        candidate_id = row["candidate_id"]
        percentile = percentiles[candidate_id]
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        delta = percentile - scalar
        pairwise_flag = candidate_id in pairwise
        output_rows.append(
            {
                "diagnostic_schema_version": DIAGNOSTIC_SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "route_key": row["route_key"],
                "comparison_stratum": row["comparison_stratum"],
                "jones_basis_family_id": "bfp_roi_jacobian_audit_proxy_no_vector_solver",
                "v1_scalar_rank_percentile_in_stratum": scalar,
                "bfp_roi_rank_percentile_in_stratum": percentile,
                "jones_rank_percentile_in_stratum": percentile,
                "jones_vs_v1_rank_percentile_delta": delta,
                "jones_pairwise_inversion_flag": pairwise_flag,
                "polarization_surrogate_risk_label": _risk_label(delta, pairwise_flag),
                "polarization_surrogate_risk_reason_codes": _reason_codes(
                    lane_code="JONES",
                    delta=delta,
                    pairwise_inversion=pairwise_flag,
                ),
                "raw_jones_amplitude_proxy_diagnostic_only": row["bfp_roi_score"],
                "raw_magnitude_final_gate_allowed": False,
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "physical_ceiling_role": "surrogate_risk_reduction_only",
            }
        )
    return output_rows


def build_roughness_leakage_diagnostic_rows(
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Build a no-solver roughness/leakage proxy from route geometry and BFP shifts."""
    audit_rows = _read_csv_dicts(project_root / P0_MANDATORY_AUDIT_PATH)
    max_width = max(_to_float(row, "width_nm") for row in audit_rows)
    max_depth = max(_to_float(row, "depth_nm") for row in audit_rows)
    scores: dict[str, float] = {}
    raw_proxy: dict[str, float] = {}
    for row in audit_rows:
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        bfp = _to_float(row, "bfp_roi_rank_percentile_in_stratum")
        width_fraction = _to_float(row, "width_nm") / max_width
        depth_fraction = _to_float(row, "depth_nm") / max_depth
        geometry_margin_proxy = 0.5 * (width_fraction + depth_fraction)
        leakage_proxy = (1.0 - geometry_margin_proxy) + abs(bfp - scalar)
        raw_proxy[row["candidate_id"]] = leakage_proxy
        scores[row["candidate_id"]] = scalar - 0.25 * leakage_proxy
    ranks = _rank_percentiles_from_scores(audit_rows, scores)
    percentiles = {
        candidate_id: percentile for candidate_id, (_, percentile) in ranks.items()
    }
    pairwise = _pairwise_inversion_candidate_ids(project_root, audit_rows, percentiles)
    output_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        candidate_id = row["candidate_id"]
        percentile = percentiles[candidate_id]
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        delta = percentile - scalar
        pairwise_flag = candidate_id in pairwise
        extra_codes = []
        if raw_proxy[candidate_id] >= 0.50:
            extra_codes.append("ROUGHNESS_LEAKAGE.GEOMETRY_MARGIN_PROXY_HIGH")
        output_rows.append(
            {
                "diagnostic_schema_version": DIAGNOSTIC_SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "route_key": row["route_key"],
                "comparison_stratum": row["comparison_stratum"],
                "perturbation_family_id": "geometry_margin_leakage_proxy_no_simulation",
                "v1_scalar_rank_percentile_in_stratum": scalar,
                "bfp_roi_rank_percentile_in_stratum": row[
                    "bfp_roi_rank_percentile_in_stratum"
                ],
                "roughness_leakage_rank_percentile_in_stratum": percentile,
                "roughness_leakage_vs_v1_rank_percentile_delta": delta,
                "roughness_leakage_pairwise_inversion_flag": pairwise_flag,
                "roughness_leakage_surrogate_risk_label": _risk_label(
                    delta,
                    pairwise_flag,
                    extra_medium=bool(extra_codes),
                ),
                "roughness_leakage_surrogate_risk_reason_codes": _reason_codes(
                    lane_code="ROUGHNESS_LEAKAGE",
                    delta=delta,
                    pairwise_inversion=pairwise_flag,
                    extra_codes=extra_codes,
                ),
                "raw_leakage_proxy_diagnostic_only": raw_proxy[candidate_id],
                "raw_magnitude_final_gate_allowed": False,
                "measured_blank_safety_claim_allowed": False,
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "physical_ceiling_role": "surrogate_risk_reduction_only",
            }
        )
    return output_rows


def build_transport_residence_time_diagnostic_rows(
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Build a no-solver transport/residence proxy from P0 relative stability fields."""
    audit_rows = _read_csv_dicts(project_root / P0_MANDATORY_AUDIT_PATH)
    scores: dict[str, float] = {}
    residence_proxy: dict[str, float] = {}
    coincidence_proxy: dict[str, float] = {}
    for row in audit_rows:
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        noise = _to_float(row, "noise_pass_fraction")
        ev = _to_float(row, "ev_polydispersity_pass_fraction_proxy")
        coincidence = (
            1.0 if row["coincidence_event_overlap_proxy_label"] == "non_fragile" else 0.0
        )
        contaminant = _to_float(row, "contaminant_pass_fraction")
        residence_proxy[row["candidate_id"]] = 0.5 * noise + 0.3 * ev + 0.2 * coincidence
        coincidence_proxy[row["candidate_id"]] = coincidence
        scores[row["candidate_id"]] = (
            0.45 * scalar
            + 0.25 * noise
            + 0.20 * ev
            + 0.05 * coincidence
            + 0.05 * contaminant
        )
    ranks = _rank_percentiles_from_scores(audit_rows, scores)
    percentiles = {
        candidate_id: percentile for candidate_id, (_, percentile) in ranks.items()
    }
    pairwise = _pairwise_inversion_candidate_ids(project_root, audit_rows, percentiles)
    output_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        candidate_id = row["candidate_id"]
        percentile = percentiles[candidate_id]
        scalar = _to_float(row, "v1_scalar_rank_percentile_in_stratum")
        delta = percentile - scalar
        pairwise_flag = candidate_id in pairwise
        extra_codes = []
        if row["ev_sample_profile_id"] == "unknown":
            extra_codes.append("TRANSPORT.RESIDENCE_SAMPLE_PROFILE_UNKNOWN")
        if row["coincidence_event_overlap_proxy_label"] != "non_fragile":
            extra_codes.append("TRANSPORT.COINCIDENCE_PROXY_FRAGILE")
        output_rows.append(
            {
                "diagnostic_schema_version": DIAGNOSTIC_SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "route_key": row["route_key"],
                "comparison_stratum": row["comparison_stratum"],
                "transport_family_id": "relative_stability_residence_proxy_no_simulation",
                "v1_scalar_rank_percentile_in_stratum": scalar,
                "transport_residence_rank_percentile_in_stratum": percentile,
                "transport_residence_vs_v1_rank_percentile_delta": delta,
                "transport_residence_pairwise_inversion_flag": pairwise_flag,
                "transport_surrogate_risk_label": _risk_label(
                    delta,
                    pairwise_flag,
                    extra_medium=bool(extra_codes),
                ),
                "transport_surrogate_risk_reason_codes": _reason_codes(
                    lane_code="TRANSPORT",
                    delta=delta,
                    pairwise_inversion=pairwise_flag,
                    extra_codes=extra_codes,
                ),
                "coincidence_proxy_diagnostic_only": coincidence_proxy[candidate_id],
                "raw_residence_time_proxy_diagnostic_only": residence_proxy[candidate_id],
                "raw_magnitude_final_gate_allowed": False,
                "true_ev_concentration_claim_allowed": False,
                "sample_count_claim_allowed": False,
                "absolute_event_probability_claim_allowed": False,
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "physical_ceiling_role": "surrogate_risk_reduction_only",
            }
        )
    return output_rows


def build_physical_ceiling_diagnostic_outputs(
    project_root: Path = PROJECT_ROOT,
) -> dict[Path, list[dict[str, Any]]]:
    return {
        FULL_WAVE_GREEN_TENSOR_DIAGNOSTIC: build_full_wave_green_tensor_diagnostic_rows(
            project_root
        ),
        VECTOR_JONES_POLARIZATION_DIAGNOSTIC: build_vector_jones_polarization_diagnostic_rows(
            project_root
        ),
        ROUGHNESS_LEAKAGE_DIAGNOSTIC: build_roughness_leakage_diagnostic_rows(
            project_root
        ),
        TRANSPORT_RESIDENCE_TIME_DIAGNOSTIC: build_transport_residence_time_diagnostic_rows(
            project_root
        ),
    }


def write_physical_ceiling_diagnostic_outputs(
    project_root: Path = PROJECT_ROOT,
) -> list[Path]:
    output_paths = []
    for relpath, rows in build_physical_ceiling_diagnostic_outputs(project_root).items():
        output_path = project_root / relpath
        write_csv_rows(output_path, rows)
        output_paths.append(output_path)
    return output_paths


def build_physical_ceiling_contract_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Build a P1 manifest for completed no-solver physical-ceiling diagnostics."""
    contracts = [_load_contract(project_root, relpath) for relpath in CONTRACT_CONFIG_PATHS]
    diagnostic_outputs = [
        str(contract["output_schema"]["planned_output_path"]) for contract in contracts
    ]

    contract_rows = []
    for relpath, contract in zip(CONTRACT_CONFIG_PATHS, contracts, strict=True):
        output_path = project_root / contract["output_schema"]["planned_output_path"]
        contract_rows.append(
            {
                "lane_id": contract["lane_id"],
                "contract_path": relpath,
                "contract_sha256": sha256_file(project_root / relpath),
                "contract_stage": contract["stage"],
                "planned_output_path": contract["output_schema"]["planned_output_path"],
                "planned_output_exists": output_path.exists(),
                "artifact_status": contract["output_schema"]["artifact_status"],
                "calibrated_claim_allowed": contract["calibrated_claim_allowed"],
                "p0_release_conclusion_changed": contract["p0_release_conclusion_changed"],
                "physical_ceiling_role": contract["physical_ceiling_role"],
                "raw_magnitude_final_gate_allowed": contract["gate_policy"][
                    "raw_arbitrary_unit_magnitude_final_gate_allowed"
                ],
                "decision_authority": contract["gate_policy"]["decision_authority"],
            }
        )

    return {
        "schema_version": "ev_nodi_p1_physical_ceiling_contract_manifest_v1",
        "stage": "P1_no_solver_rank_diagnostics_complete",
        "manifest_role": "contract_registry_and_generated_no_solver_output_guard",
        "p0_release_conclusion_changed": False,
        "calibrated_claim_allowed": False,
        "physical_ceiling_role": "surrogate_risk_reduction_only",
        "diagnostic_outputs_generated": True,
        "solver_or_simulation_execution_authorized": False,
        "diagnostic_output_paths": diagnostic_outputs,
        "diagnostic_output_count": len(diagnostic_outputs),
        "diagnostic_output_existing_count": sum(
            (project_root / output).exists() for output in diagnostic_outputs
        ),
        "contract_count": len(contract_rows),
        "contract_paths": list(CONTRACT_CONFIG_PATHS),
        "lane_report_paths": list(LANE_REPORT_PATHS),
        "contracts": contract_rows,
        "required_false_fields": [
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "solver_or_simulation_execution_authorized",
        ],
        "claim_boundary": {
            "calibrated_snr_claim_allowed": False,
            "absolute_lod_claim_allowed": False,
            "true_ev_concentration_claim_allowed": False,
            "biological_specificity_claim_allowed": False,
            "detector_voltage_prediction_claim_allowed": False,
            "absolute_event_probability_claim_allowed": False,
        },
    }


def validate_physical_ceiling_contract_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p1_physical_ceiling_contract_manifest_v1":
        raise ValueError("unexpected physical-ceiling contract manifest schema")
    for key in manifest["required_false_fields"]:
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if manifest["physical_ceiling_role"] != "surrogate_risk_reduction_only":
        raise ValueError("physical_ceiling_role drifted")
    if manifest["diagnostic_outputs_generated"] is not True:
        raise ValueError("diagnostic outputs must be generated for completed P1 package")
    if manifest["diagnostic_output_existing_count"] != manifest["diagnostic_output_count"]:
        raise ValueError("diagnostic outputs are missing for completed P1 package")
    if manifest["contract_count"] != len(CONTRACT_CONFIG_PATHS):
        raise ValueError("contract count mismatch")
    for contract in manifest["contracts"]:
        for key in (
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "raw_magnitude_final_gate_allowed",
        ):
            if contract[key] is not False:
                raise ValueError(f"contract guard failed: {contract['lane_id']} {key}")
        if contract["planned_output_exists"] is not True:
            raise ValueError(f"missing planned output: {contract['lane_id']}")
        if contract["physical_ceiling_role"] != "surrogate_risk_reduction_only":
            raise ValueError(f"contract role drifted: {contract['lane_id']}")
        if contract["artifact_status"] != "generated_no_solver_rank_diagnostic":
            raise ValueError(f"unexpected artifact status: {contract['lane_id']}")
        if contract["decision_authority"] != "diagnostic_flag_only_no_route_promotion":
            raise ValueError(f"unexpected decision authority: {contract['lane_id']}")
    for key, value in manifest["claim_boundary"].items():
        if value is not False:
            raise ValueError(f"claim boundary drifted: {key}")
    return manifest


def write_physical_ceiling_contract_manifest(
    project_root: Path = PROJECT_ROOT,
) -> Path:
    manifest = validate_physical_ceiling_contract_manifest(
        build_physical_ceiling_contract_manifest(project_root)
    )
    output_path = project_root / PHYSICAL_CEILING_CONTRACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def build_physical_ceiling_diagnostic_schema_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    contracts = [_load_contract(project_root, relpath) for relpath in CONTRACT_CONFIG_PATHS]
    schema_rows = []
    for relpath, contract in zip(CONTRACT_CONFIG_PATHS, contracts, strict=True):
        output = contract["output_schema"]
        output_path = project_root / output["planned_output_path"]
        schema_rows.append(
            {
                "lane_id": contract["lane_id"],
                "contract_path": relpath,
                "planned_output_path": output["planned_output_path"],
                "planned_output_exists": output_path.exists(),
                "artifact_status": output["artifact_status"],
                "row_granularity": output["row_granularity"],
                "required_column_count": len(output["required_columns"]),
                "required_columns": output["required_columns"],
                "required_false_columns": output["required_false_columns"],
                "required_role_column_value": output["required_role_column_value"],
                "primary_gate_metrics": contract["gate_policy"]["primary_gate_metrics"],
                "raw_magnitude_final_gate_allowed": contract["gate_policy"][
                    "raw_arbitrary_unit_magnitude_final_gate_allowed"
                ],
                "decision_authority": contract["gate_policy"]["decision_authority"],
            }
        )
    return {
        "schema_version": "ev_nodi_p1_physical_ceiling_diagnostic_schema_manifest_v1",
        "stage": "P1_diagnostic_schema_manifest_generated_no_solver_outputs",
        "manifest_role": "generated_output_schema_registry_and_no_solver_guard",
        "p0_release_conclusion_changed": False,
        "calibrated_claim_allowed": False,
        "physical_ceiling_role": "surrogate_risk_reduction_only",
        "diagnostic_outputs_generated": True,
        "solver_or_simulation_execution_authorized": False,
        "schema_count": len(schema_rows),
        "schemas": schema_rows,
        "required_false_fields": [
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "solver_or_simulation_execution_authorized",
        ],
        "required_gate_metric_families": [
            "rank_percentile",
            "pairwise_inversion",
        ],
    }


def validate_physical_ceiling_diagnostic_schema_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p1_physical_ceiling_diagnostic_schema_manifest_v1"
    ):
        raise ValueError("unexpected physical-ceiling diagnostic schema manifest")
    for key in manifest["required_false_fields"]:
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if manifest["physical_ceiling_role"] != "surrogate_risk_reduction_only":
        raise ValueError("physical_ceiling_role drifted")
    if manifest["diagnostic_outputs_generated"] is not True:
        raise ValueError("diagnostic outputs must be generated for completed P1 package")
    if manifest["schema_count"] != len(CONTRACT_CONFIG_PATHS):
        raise ValueError("diagnostic schema count mismatch")
    for schema in manifest["schemas"]:
        if schema["planned_output_exists"] is not True:
            raise ValueError(f"diagnostic output missing: {schema['planned_output_path']}")
        if schema["artifact_status"] != "generated_no_solver_rank_diagnostic":
            raise ValueError(f"unexpected artifact status: {schema['lane_id']}")
        if schema["raw_magnitude_final_gate_allowed"] is not False:
            raise ValueError(f"raw magnitude gate drifted: {schema['lane_id']}")
        if schema["decision_authority"] != "diagnostic_flag_only_no_route_promotion":
            raise ValueError(f"decision authority drifted: {schema['lane_id']}")
        if "calibrated_claim_allowed" not in schema["required_false_columns"]:
            raise ValueError(f"missing calibrated guard column: {schema['lane_id']}")
        if "p0_release_conclusion_changed" not in schema["required_false_columns"]:
            raise ValueError(f"missing P0 guard column: {schema['lane_id']}")
        if "raw_magnitude_final_gate_allowed" not in schema["required_false_columns"]:
            raise ValueError(f"missing raw magnitude guard column: {schema['lane_id']}")
        if schema["required_role_column_value"] != "surrogate_risk_reduction_only":
            raise ValueError(f"role column drifted: {schema['lane_id']}")
        gate_text = " ".join(schema["primary_gate_metrics"])
        if "rank_percentile" not in gate_text or "pairwise_inversion" not in gate_text:
            raise ValueError(f"gate metrics are not rank/pairwise based: {schema['lane_id']}")
    return manifest


def _source_fields_and_count(path: Path) -> tuple[list[str], int | None, str]:
    if path.suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            row_count = sum(1 for _ in reader)
        return fields, row_count, "csv"
    payload = load_json_yaml(path)
    return sorted(str(key) for key in payload), None, "json_compatible_yaml"


def _csv_route_keys(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "route_key" not in (reader.fieldnames or []):
            return set()
        return {row["route_key"] for row in reader if row.get("route_key")}


def build_physical_ceiling_input_binding_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    contracts = [_load_contract(project_root, relpath) for relpath in CONTRACT_CONFIG_PATHS]
    bindings = []
    for relpath, contract in zip(CONTRACT_CONFIG_PATHS, contracts, strict=True):
        for source in contract["input_contract"]["required_sources"]:
            source_path = project_root / source["path"]
            fields, row_count, source_type = _source_fields_and_count(source_path)
            missing = [field for field in source["required_fields"] if field not in fields]
            bindings.append(
                {
                    "lane_id": contract["lane_id"],
                    "contract_path": relpath,
                    "source_id": source["source_id"],
                    "source_path": source["path"],
                    "source_type": source_type,
                    "source_sha256": sha256_file(source_path),
                    "source_exists": source_path.is_file(),
                    "source_row_count": row_count,
                    "required_fields": source["required_fields"],
                    "required_field_count": len(source["required_fields"]),
                    "missing_required_fields": missing,
                    "required_fields_present": not missing,
                    "calibrated_claim_allowed": False,
                    "p0_release_conclusion_changed": False,
                    "physical_ceiling_role": "surrogate_risk_reduction_only",
                    "diagnostic_output_generated": True,
                }
            )
    return {
        "schema_version": "ev_nodi_p1_physical_ceiling_input_binding_manifest_v1",
        "stage": "P1_input_binding_manifest_generated_no_solver_outputs",
        "manifest_role": "p0_source_binding_registry_and_no_solver_output_guard",
        "p0_release_conclusion_changed": False,
        "calibrated_claim_allowed": False,
        "physical_ceiling_role": "surrogate_risk_reduction_only",
        "diagnostic_outputs_generated": True,
        "solver_or_simulation_execution_authorized": False,
        "binding_count": len(bindings),
        "bindings": bindings,
        "required_false_fields": [
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "solver_or_simulation_execution_authorized",
        ],
    }


def validate_physical_ceiling_input_binding_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p1_physical_ceiling_input_binding_manifest_v1"
    ):
        raise ValueError("unexpected physical-ceiling input binding manifest schema")
    for key in manifest["required_false_fields"]:
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if manifest["physical_ceiling_role"] != "surrogate_risk_reduction_only":
        raise ValueError("physical_ceiling_role drifted")
    if manifest["diagnostic_outputs_generated"] is not True:
        raise ValueError("diagnostic outputs must be generated for completed P1 package")
    if manifest["binding_count"] <= 0:
        raise ValueError("input binding manifest must not be empty")
    for binding in manifest["bindings"]:
        if binding["source_exists"] is not True:
            raise ValueError(f"missing source: {binding['source_path']}")
        if binding["required_fields_present"] is not True:
            raise ValueError(
                f"missing required source fields for {binding['lane_id']} "
                f"{binding['source_id']}: {binding['missing_required_fields']}"
            )
        for key in (
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
        ):
            if binding[key] is not False:
                raise ValueError(f"binding guard failed: {binding['lane_id']} {key}")
        if binding["diagnostic_output_generated"] is not True:
            raise ValueError(f"binding output state failed: {binding['lane_id']}")
        if binding["physical_ceiling_role"] != "surrogate_risk_reduction_only":
            raise ValueError(f"binding role drifted: {binding['lane_id']}")
    return manifest


def build_physical_ceiling_route_coverage_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    contracts = [_load_contract(project_root, relpath) for relpath in CONTRACT_CONFIG_PATHS]
    primary_source = "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv"
    primary_route_keys = _csv_route_keys(project_root / primary_source)
    lane_rows = []
    source_rows = []
    for relpath, contract in zip(CONTRACT_CONFIG_PATHS, contracts, strict=True):
        output_path = project_root / contract["output_schema"]["planned_output_path"]
        route_sources = []
        for source in contract["input_contract"]["required_sources"]:
            source_path = project_root / source["path"]
            fields, row_count, source_type = _source_fields_and_count(source_path)
            has_route_key = "route_key" in fields
            route_keys = _csv_route_keys(source_path) if source_type == "csv" and has_route_key else set()
            missing_from_source = sorted(primary_route_keys - route_keys) if has_route_key else []
            source_row = {
                "lane_id": contract["lane_id"],
                "source_id": source["source_id"],
                "source_path": source["path"],
                "source_type": source_type,
                "source_row_count": row_count,
                "source_has_route_key_field": has_route_key,
                "source_route_key_count": len(route_keys) if has_route_key else None,
                "primary_route_key_count": len(primary_route_keys),
                "missing_primary_route_key_count": len(missing_from_source),
                "missing_primary_route_keys": missing_from_source,
                "coverage_role": "route_key_coverage_source" if has_route_key else "non_route_key_context_source",
                "diagnostic_output_generated": True,
            }
            source_rows.append(source_row)
            route_sources.append(source_row)
        lane_rows.append(
            {
                "lane_id": contract["lane_id"],
                "contract_path": relpath,
                "planned_output_path": contract["output_schema"]["planned_output_path"],
                "planned_output_exists": output_path.exists(),
                "primary_source_path": primary_source,
                "primary_route_key_count": len(primary_route_keys),
                "route_key_source_count": sum(row["source_has_route_key_field"] for row in route_sources),
                "route_key_sources_with_full_primary_coverage": sum(
                    row["source_has_route_key_field"]
                    and row["missing_primary_route_key_count"] == 0
                    for row in route_sources
                ),
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "physical_ceiling_role": "surrogate_risk_reduction_only",
                "diagnostic_output_generated": True,
            }
        )
    return {
        "schema_version": "ev_nodi_p1_physical_ceiling_route_coverage_manifest_v1",
        "stage": "P1_route_coverage_manifest_generated_no_solver_outputs",
        "manifest_role": "p0_route_coverage_registry_and_no_solver_output_guard",
        "p0_release_conclusion_changed": False,
        "calibrated_claim_allowed": False,
        "physical_ceiling_role": "surrogate_risk_reduction_only",
        "diagnostic_outputs_generated": True,
        "solver_or_simulation_execution_authorized": False,
        "primary_source_path": primary_source,
        "primary_route_key_count": len(primary_route_keys),
        "lane_count": len(lane_rows),
        "lanes": lane_rows,
        "source_binding_count": len(source_rows),
        "source_bindings": source_rows,
        "required_false_fields": [
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "solver_or_simulation_execution_authorized",
        ],
    }


def validate_physical_ceiling_route_coverage_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p1_physical_ceiling_route_coverage_manifest_v1"
    ):
        raise ValueError("unexpected physical-ceiling route coverage manifest schema")
    for key in manifest["required_false_fields"]:
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if manifest["physical_ceiling_role"] != "surrogate_risk_reduction_only":
        raise ValueError("physical_ceiling_role drifted")
    if manifest["diagnostic_outputs_generated"] is not True:
        raise ValueError("diagnostic outputs must be generated for completed P1 package")
    if manifest["primary_route_key_count"] <= 0:
        raise ValueError("primary route universe is empty")
    if manifest["lane_count"] != len(CONTRACT_CONFIG_PATHS):
        raise ValueError("route coverage lane count mismatch")
    for lane in manifest["lanes"]:
        for key in (
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
        ):
            if lane[key] is not False:
                raise ValueError(f"lane coverage guard failed: {lane['lane_id']} {key}")
        if lane["planned_output_exists"] is not True:
            raise ValueError(f"lane diagnostic output missing: {lane['lane_id']}")
        if lane["diagnostic_output_generated"] is not True:
            raise ValueError(f"lane diagnostic output state failed: {lane['lane_id']}")
        if lane["physical_ceiling_role"] != "surrogate_risk_reduction_only":
            raise ValueError(f"lane coverage role drifted: {lane['lane_id']}")
        if lane["route_key_source_count"] <= 0:
            raise ValueError(f"lane has no route-key source: {lane['lane_id']}")
        if lane["route_key_sources_with_full_primary_coverage"] <= 0:
            raise ValueError(f"lane has no full-coverage route source: {lane['lane_id']}")
    for source in manifest["source_bindings"]:
        if source["diagnostic_output_generated"] is not True:
            raise ValueError(f"source binding output state failed: {source['source_path']}")
        if source["source_has_route_key_field"] and source["missing_primary_route_key_count"] != 0:
            raise ValueError(
                f"route coverage gap in {source['lane_id']} {source['source_id']}: "
                f"{source['missing_primary_route_keys'][:5]}"
            )
    return manifest


def write_physical_ceiling_route_coverage_manifest(
    project_root: Path = PROJECT_ROOT,
) -> Path:
    manifest = validate_physical_ceiling_route_coverage_manifest(
        build_physical_ceiling_route_coverage_manifest(project_root)
    )
    output_path = project_root / PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_physical_ceiling_input_binding_manifest(
    project_root: Path = PROJECT_ROOT,
) -> Path:
    manifest = validate_physical_ceiling_input_binding_manifest(
        build_physical_ceiling_input_binding_manifest(project_root)
    )
    output_path = project_root / PHYSICAL_CEILING_INPUT_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_physical_ceiling_diagnostic_schema_manifest(
    project_root: Path = PROJECT_ROOT,
) -> Path:
    manifest = validate_physical_ceiling_diagnostic_schema_manifest(
        build_physical_ceiling_diagnostic_schema_manifest(project_root)
    )
    output_path = project_root / PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_physical_ceiling_manifests(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        write_physical_ceiling_contract_manifest(project_root),
        write_physical_ceiling_diagnostic_schema_manifest(project_root),
        write_physical_ceiling_input_binding_manifest(project_root),
        write_physical_ceiling_route_coverage_manifest(project_root),
    ]


def write_physical_ceiling_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    diagnostic_paths = write_physical_ceiling_diagnostic_outputs(project_root)
    manifest_paths = write_physical_ceiling_manifests(project_root)
    return [*diagnostic_paths, *manifest_paths]


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P1 physical-ceiling manifests")


def _assert_csv_current(path: Path, expected_rows: list[dict[str, Any]], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual_rows = _read_csv_dicts(path)
    expected_as_text = [
        {key: str(value) for key, value in row.items()} for row in expected_rows
    ]
    if actual_rows != expected_as_text:
        raise ValueError(f"stale {label}: regenerate P1 physical-ceiling package")


def _assert_diagnostic_rows_preserve_boundaries(
    rows: list[dict[str, str]], label: str
) -> None:
    if not rows:
        raise ValueError(f"empty physical-ceiling diagnostic: {label}")
    for row in rows:
        for key in (
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "raw_magnitude_final_gate_allowed",
        ):
            if row[key] != "False":
                raise ValueError(f"{label} guard failed: {key}")
        if row["physical_ceiling_role"] != "surrogate_risk_reduction_only":
            raise ValueError(f"{label} role drifted")
        if "rank_percentile" not in " ".join(row):
            raise ValueError(f"{label} row missing rank-percentile schema")


def verify_physical_ceiling_contract_package(
    project_root: Path = PROJECT_ROOT,
) -> list[str]:
    """Verify P1 physical-ceiling contracts and generated no-solver diagnostics."""
    expected_outputs = build_physical_ceiling_diagnostic_outputs(project_root)
    for relpath, expected_rows in expected_outputs.items():
        output_path = project_root / relpath
        _assert_csv_current(output_path, expected_rows, relpath.as_posix())
        _assert_diagnostic_rows_preserve_boundaries(
            _read_csv_dicts(output_path), relpath.as_posix()
        )

    contract_manifest = validate_physical_ceiling_contract_manifest(
        build_physical_ceiling_contract_manifest(project_root)
    )
    schema_manifest = validate_physical_ceiling_diagnostic_schema_manifest(
        build_physical_ceiling_diagnostic_schema_manifest(project_root)
    )

    _assert_manifest_current(
        project_root / PHYSICAL_CEILING_CONTRACT_MANIFEST,
        contract_manifest,
        "physical-ceiling contract manifest",
    )
    _assert_manifest_current(
        project_root / PHYSICAL_CEILING_DIAGNOSTIC_SCHEMA_MANIFEST,
        schema_manifest,
        "physical-ceiling diagnostic schema manifest",
    )
    input_binding_manifest = validate_physical_ceiling_input_binding_manifest(
        build_physical_ceiling_input_binding_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / PHYSICAL_CEILING_INPUT_BINDING_MANIFEST,
        input_binding_manifest,
        "physical-ceiling input binding manifest",
    )
    route_coverage_manifest = validate_physical_ceiling_route_coverage_manifest(
        build_physical_ceiling_route_coverage_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / PHYSICAL_CEILING_ROUTE_COVERAGE_MANIFEST,
        route_coverage_manifest,
        "physical-ceiling route coverage manifest",
    )

    readme = project_root / PHYSICAL_CEILING_README
    if not readme.is_file():
        raise ValueError("missing physical-ceiling README")
    readme_text = readme.read_text(encoding="utf-8")
    for required in (
        "generated no-solver rank diagnostics",
        "surrogate_risk_reduction_only",
        "does not change the P0 release conclusion",
    ):
        if required not in readme_text:
            raise ValueError(f"physical-ceiling README missing boundary text: {required}")

    return [
        "PASS physical_ceiling_no_solver_diagnostics_current",
        "PASS physical_ceiling_contract_manifest_current",
        "PASS physical_ceiling_diagnostic_schema_manifest_current",
        "PASS physical_ceiling_input_binding_manifest_current",
        "PASS physical_ceiling_route_coverage_manifest_current",
        "PASS physical_ceiling_solver_or_simulation_execution_blocked",
        "PASS physical_ceiling_claim_boundaries",
        "PASS physical_ceiling_readme_boundary",
    ]
