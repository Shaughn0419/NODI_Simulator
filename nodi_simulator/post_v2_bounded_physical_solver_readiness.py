"""P2 bounded physical-solver readiness governance helpers.

This module records solver-readiness contracts only. It does not run physical
solvers, generate solver cases, ingest measured data, or promote routes.
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P2_READINESS_DIR = Path("results/post_v2_bounded_physical_solver_readiness")
P2_READINESS_REGISTRY = (
    "configs/realism_v2/bounded_physical_solver_readiness_registry.yaml"
)
P2_READINESS_PLAN = "reports/98_EV_NODI_P2_bounded_physical_solver_readiness_plan.md"
P2_READINESS_COMPLETION_NOTE = (
    "reports/99_EV_NODI_P2_bounded_physical_solver_readiness_completion_note.md"
)
P2_READINESS_ARTIFACT_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_artifact_manifest.json"
)
P2_READINESS_SCHEMA_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_schema_manifest.json"
)
P2_READINESS_SOURCE_BINDING_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_source_binding_manifest.json"
)
P2_READINESS_ROUTE_UNIVERSE_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_route_universe_manifest.json"
)
P2_READINESS_README = P2_READINESS_DIR / "README.md"
P2_READINESS_TEXT_PATHS: tuple[str, ...] = (
    P2_READINESS_REGISTRY,
    P2_READINESS_PLAN,
    P2_READINESS_COMPLETION_NOTE,
    P2_READINESS_README.as_posix(),
    "docs/schemas/bounded_physical_solver_readiness_schema_manifest_schema.md",
    "docs/schemas/bounded_physical_solver_readiness_artifact_manifest_schema.md",
    "docs/schemas/bounded_physical_solver_readiness_source_binding_manifest_schema.md",
    "docs/schemas/bounded_physical_solver_readiness_route_universe_manifest_schema.md",
)
P0_MANDATORY_AUDIT_PATH = (
    "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv"
)
P1_FULL_WAVE_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv"
)
P1_VECTOR_JONES_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/vector_jones_polarization_diagnostic.csv"
)
P1_ROUGHNESS_LEAKAGE_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/roughness_leakage_diagnostic.csv"
)
P1_TRANSPORT_RESIDENCE_TIME_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/transport_residence_time_diagnostic.csv"
)

EXPECTED_LANE_IDS: frozenset[str] = frozenset(
    {
        "full_wave_green_tensor_spot_check_readiness",
        "vector_jones_basis_sweep_readiness",
        "roughness_leakage_perturbation_readiness",
        "transport_residence_time_perturbation_readiness",
    }
)

TOP_LEVEL_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "physical_solver_execution_authorized",
    "measured_data_ingest_authorized",
)

CLAIM_BOUNDARY_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_snr_claim_allowed",
    "absolute_lod_claim_allowed",
    "true_ev_concentration_claim_allowed",
    "biological_specificity_claim_allowed",
    "detector_voltage_prediction_claim_allowed",
    "absolute_event_probability_claim_allowed",
    "sample_count_claim_allowed",
    "measured_blank_safety_claim_allowed",
    "route_promotion_authorized",
)

ALLOWED_TRUE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "readiness_schema_and_governance_authorized",
        "artifact_manifest_generation_authorized",
        "schema_manifest_generation_authorized",
        "source_binding_manifest_generation_authorized",
        "route_universe_manifest_generation_authorized",
        "verifier_authorized",
    }
)

SOURCE_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "p0_mandatory_audit_primary_route_universe",
        "path": P0_MANDATORY_AUDIT_PATH,
        "source_role": "bounded_route_universe_source",
        "required_fields": [
            "candidate_id",
            "route_key",
            "comparison_stratum",
            "route_role_final",
            "final_audit_decision",
            "required_next_artifact_priority",
            "calibrated_snr_claim_allowed",
            "absolute_lod_claim_allowed",
            "true_ev_concentration_claim_allowed",
            "biological_specificity_claim_allowed",
            "detector_voltage_prediction_claim_allowed",
            "main_660_redefinition_authorized",
        ],
    },
    {
        "source_id": "p1_full_wave_green_tensor_no_solver_diagnostic",
        "path": P1_FULL_WAVE_DIAGNOSTIC_PATH,
        "source_role": "p1_surrogate_risk_context",
        "required_fields": [
            "candidate_id",
            "route_key",
            "comparison_stratum",
            "surrogate_risk_label",
            "green_tensor_pairwise_inversion_flag",
            "raw_magnitude_final_gate_allowed",
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "physical_ceiling_role",
        ],
    },
    {
        "source_id": "p1_vector_jones_no_solver_diagnostic",
        "path": P1_VECTOR_JONES_DIAGNOSTIC_PATH,
        "source_role": "p1_surrogate_risk_context",
        "required_fields": [
            "candidate_id",
            "route_key",
            "comparison_stratum",
            "polarization_surrogate_risk_label",
            "jones_pairwise_inversion_flag",
            "raw_magnitude_final_gate_allowed",
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "physical_ceiling_role",
        ],
    },
    {
        "source_id": "p1_roughness_leakage_no_solver_diagnostic",
        "path": P1_ROUGHNESS_LEAKAGE_DIAGNOSTIC_PATH,
        "source_role": "p1_surrogate_risk_context",
        "required_fields": [
            "candidate_id",
            "route_key",
            "comparison_stratum",
            "roughness_leakage_surrogate_risk_label",
            "roughness_leakage_pairwise_inversion_flag",
            "raw_magnitude_final_gate_allowed",
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "physical_ceiling_role",
        ],
    },
    {
        "source_id": "p1_transport_residence_time_no_solver_diagnostic",
        "path": P1_TRANSPORT_RESIDENCE_TIME_DIAGNOSTIC_PATH,
        "source_role": "p1_surrogate_risk_context",
        "required_fields": [
            "candidate_id",
            "route_key",
            "comparison_stratum",
            "transport_surrogate_risk_label",
            "transport_residence_pairwise_inversion_flag",
            "raw_magnitude_final_gate_allowed",
            "calibrated_claim_allowed",
            "p0_release_conclusion_changed",
            "physical_ceiling_role",
        ],
    },
)


def load_readiness_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P2_READINESS_REGISTRY)


def _require_false(mapping: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise ValueError(f"{context} must keep {key}=false")


def _validate_claim_boundary(claims: dict[str, Any], context: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != "bounded_solver_readiness_only":
        raise ValueError(f"{context} claim level drifted")


def validate_readiness_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if (
        registry.get("schema_version")
        != "ev_nodi_p2_bounded_physical_solver_readiness_registry_v1"
    ):
        raise ValueError("unexpected P2 readiness registry schema")
    if registry.get("stage") != "P2_bounded_physical_solver_readiness_complete":
        raise ValueError("unexpected P2 readiness stage")
    _require_false(registry, TOP_LEVEL_FALSE_FIELDS, "P2 registry")
    if registry.get("p1_surrogate_risk_role_preserved") is not True:
        raise ValueError("P1 surrogate-risk role must remain preserved")

    authority = registry["implementation_authority"]
    for key, value in authority.items():
        if key in ALLOWED_TRUE_AUTHORITY_FIELDS:
            if value is not True:
                raise ValueError(f"P2 readiness authority missing: {key}")
            continue
        if value is not False:
            raise ValueError(f"P2 execution authority drifted: {key}")

    _validate_claim_boundary(registry["claim_governance"], "P2 registry")

    score = registry["score_governance"]
    if score["raw_arbitrary_unit_magnitude_final_gate_allowed"] is not False:
        raise ValueError("raw arbitrary-unit magnitude final gate drifted")
    if set(score["final_gate_metric_family"]) != {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }:
        raise ValueError("P2 final gate metric families drifted")

    jacobian = registry["jacobian_governance"]
    if jacobian["v1_bfp_to_angle_jacobian_applied"] is not False:
        raise ValueError("v1 Jacobian source flag drifted")
    if jacobian["audit_bfp_jacobian_applied"] is not True:
        raise ValueError("audit Jacobian sidecar flag drifted")

    lanes = registry["readiness_lanes"]
    if {lane["lane_id"] for lane in lanes} != EXPECTED_LANE_IDS:
        raise ValueError("P2 readiness lane set drifted")
    for lane in lanes:
        if lane["readiness_status"] != "schema_governance_only_not_executable":
            raise ValueError(f"lane readiness status drifted: {lane['lane_id']}")
        if lane["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"lane P1 role drifted: {lane['lane_id']}")
        _require_false(lane, TOP_LEVEL_FALSE_FIELDS, lane["lane_id"])
        _validate_claim_boundary(lane["claim_boundary"], lane["lane_id"])
        for key, value in lane["execution_authority"].items():
            if value is not False:
                raise ValueError(f"lane execution authority drifted: {lane['lane_id']} {key}")
        output = lane["readiness_output_contract"]
        if output["artifact_status"] != "planned_readiness_schema_only":
            raise ValueError(f"lane output status drifted: {lane['lane_id']}")
        if output["solver_output_path"] is not None:
            raise ValueError(f"lane must not declare solver output: {lane['lane_id']}")
        if "raw_magnitude_final_gate_allowed" not in output["required_false_fields"]:
            raise ValueError(f"lane missing raw-magnitude guard: {lane['lane_id']}")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (
        "calibrated_claim_allowed",
        "p0_release_conclusion_changed",
        "p1_surrogate_risk_role_preserved",
        "physical_solver_execution_authorized",
        "measured_data_ingest_authorized",
    ):
        if field not in required:
            raise ValueError(f"P2 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P2 artifact missing schema fields: {artifact['artifact_id']}")
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        if artifact["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"P2 artifact P1 role drifted: {artifact['artifact_id']}")
    return registry


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_fields_and_count(path: Path) -> tuple[list[str], int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        row_count = sum(1 for _ in reader)
    return fields, row_count


def _bool_from_csv(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"unexpected CSV boolean value: {value!r}")


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P2_READINESS_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_readiness_artifact_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    registry = validate_readiness_registry(load_readiness_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": (
            "ev_nodi_p2_bounded_physical_solver_readiness_artifact_manifest_v1"
        ),
        "stage": "P2_bounded_physical_solver_readiness_complete",
        "manifest_role": "schema_governance_artifact_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
        "claim_boundary": dict.fromkeys(CLAIM_BOUNDARY_FALSE_FIELDS, False)
        | {"allowed_claim_level": "bounded_solver_readiness_only"},
    }


def validate_readiness_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p2_bounded_physical_solver_readiness_artifact_manifest_v1"
    ):
        raise ValueError("unexpected P2 artifact manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P2 artifact manifest")
    if manifest["p1_surrogate_risk_role_preserved"] is not True:
        raise ValueError("P2 artifact manifest P1 role drifted")
    _validate_claim_boundary(manifest["claim_boundary"], "P2 artifact manifest")
    if manifest["artifact_count"] <= 0:
        raise ValueError("P2 artifact manifest must not be empty")
    for artifact in manifest["artifacts"]:
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        if artifact["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"P2 artifact P1 role drifted: {artifact['artifact_id']}")
        is_self_manifest = artifact["path"] == P2_READINESS_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P2 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P2 artifact hash missing: {artifact['path']}")
    return manifest


def build_readiness_source_binding_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    bindings = []
    for source in SOURCE_CONTRACTS:
        source_path = project_root / source["path"]
        fields, row_count = _csv_fields_and_count(source_path)
        missing = [field for field in source["required_fields"] if field not in fields]
        bindings.append(
            {
                "source_id": source["source_id"],
                "source_role": source["source_role"],
                "source_path": source["path"],
                "source_exists": source_path.is_file(),
                "source_sha256": sha256_file(source_path) if source_path.is_file() else None,
                "source_row_count": row_count,
                "required_fields": source["required_fields"],
                "missing_required_fields": missing,
                "required_fields_present": not missing,
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "p1_surrogate_risk_role_preserved": True,
                "physical_solver_execution_authorized": False,
                "measured_data_ingest_authorized": False,
            }
        )
    return {
        "schema_version": (
            "ev_nodi_p2_bounded_physical_solver_readiness_source_binding_manifest_v1"
        ),
        "stage": "P2_bounded_physical_solver_readiness_complete",
        "manifest_role": "source_binding_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "source_count": len(bindings),
        "bindings": bindings,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
    }


def validate_readiness_source_binding_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p2_bounded_physical_solver_readiness_source_binding_manifest_v1"
    ):
        raise ValueError("unexpected P2 source binding manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P2 source binding manifest")
    if manifest["p1_surrogate_risk_role_preserved"] is not True:
        raise ValueError("P2 source binding manifest P1 role drifted")
    if manifest["source_count"] != len(SOURCE_CONTRACTS):
        raise ValueError("P2 source binding count drifted")
    for binding in manifest["bindings"]:
        _require_false(binding, TOP_LEVEL_FALSE_FIELDS, binding["source_id"])
        if binding["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"P2 binding P1 role drifted: {binding['source_id']}")
        if binding["source_exists"] is not True:
            raise ValueError(f"P2 source missing: {binding['source_path']}")
        if binding["required_fields_present"] is not True:
            raise ValueError(
                f"P2 source missing required fields: {binding['source_id']} "
                f"{binding['missing_required_fields']}"
            )
        if binding["source_row_count"] <= 0:
            raise ValueError(f"P2 source row count empty: {binding['source_id']}")
    return manifest


def _rows_by_candidate(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv_dicts(path)
    return {row["candidate_id"]: row for row in rows}


def build_readiness_route_universe_manifest(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    p0_rows = _read_csv_dicts(project_root / P0_MANDATORY_AUDIT_PATH)
    full_wave = _rows_by_candidate(project_root / P1_FULL_WAVE_DIAGNOSTIC_PATH)
    vector = _rows_by_candidate(project_root / P1_VECTOR_JONES_DIAGNOSTIC_PATH)
    roughness = _rows_by_candidate(project_root / P1_ROUGHNESS_LEAKAGE_DIAGNOSTIC_PATH)
    transport = _rows_by_candidate(project_root / P1_TRANSPORT_RESIDENCE_TIME_DIAGNOSTIC_PATH)

    universe_rows = []
    for row in p0_rows:
        candidate_id = row["candidate_id"]
        lane_rows = {
            "full_wave": full_wave[candidate_id],
            "vector_jones": vector[candidate_id],
            "roughness_leakage": roughness[candidate_id],
            "transport_residence_time": transport[candidate_id],
        }
        risk_labels = {
            "full_wave_green_tensor_surrogate_risk_label": lane_rows["full_wave"][
                "surrogate_risk_label"
            ],
            "vector_jones_surrogate_risk_label": lane_rows["vector_jones"][
                "polarization_surrogate_risk_label"
            ],
            "roughness_leakage_surrogate_risk_label": lane_rows["roughness_leakage"][
                "roughness_leakage_surrogate_risk_label"
            ],
            "transport_residence_time_surrogate_risk_label": lane_rows[
                "transport_residence_time"
            ]["transport_surrogate_risk_label"],
        }
        pairwise_flags = {
            "full_wave_green_tensor_pairwise_inversion_flag": _bool_from_csv(
                lane_rows["full_wave"]["green_tensor_pairwise_inversion_flag"]
            ),
            "vector_jones_pairwise_inversion_flag": _bool_from_csv(
                lane_rows["vector_jones"]["jones_pairwise_inversion_flag"]
            ),
            "roughness_leakage_pairwise_inversion_flag": _bool_from_csv(
                lane_rows["roughness_leakage"][
                    "roughness_leakage_pairwise_inversion_flag"
                ]
            ),
            "transport_residence_time_pairwise_inversion_flag": _bool_from_csv(
                lane_rows["transport_residence_time"][
                    "transport_residence_pairwise_inversion_flag"
                ]
            ),
        }
        universe_rows.append(
            {
                "readiness_schema_version": (
                    "ev_nodi_p2_bounded_physical_solver_route_universe_v1"
                ),
                "candidate_id": candidate_id,
                "route_key": row["route_key"],
                "comparison_stratum": row["comparison_stratum"],
                "route_role_final": row["route_role_final"],
                "final_audit_decision": row["final_audit_decision"],
                "required_next_artifact_priority": row["required_next_artifact_priority"],
                **risk_labels,
                **pairwise_flags,
                "any_p1_high_surrogate_risk": any(
                    value == "high_surrogate_risk" for value in risk_labels.values()
                ),
                "any_p1_pairwise_inversion_flag": any(pairwise_flags.values()),
                "bounded_route_universe_role": "future_solver_preflight_only",
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "p1_surrogate_risk_role_preserved": True,
                "physical_solver_execution_authorized": False,
                "measured_data_ingest_authorized": False,
                "raw_magnitude_final_gate_allowed": False,
                "route_promotion_authorized": False,
            }
        )

    return {
        "schema_version": (
            "ev_nodi_p2_bounded_physical_solver_readiness_route_universe_manifest_v1"
        ),
        "stage": "P2_bounded_physical_solver_readiness_complete",
        "manifest_role": "bounded_route_universe_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "source_paths": [source["path"] for source in SOURCE_CONTRACTS],
        "source_sha256": {
            source["path"]: sha256_file(project_root / source["path"])
            for source in SOURCE_CONTRACTS
        },
        "route_universe_row_count": len(universe_rows),
        "comparison_strata": sorted({row["comparison_stratum"] for row in universe_rows}),
        "high_surrogate_risk_route_count": sum(
            row["any_p1_high_surrogate_risk"] for row in universe_rows
        ),
        "pairwise_inversion_route_count": sum(
            row["any_p1_pairwise_inversion_flag"] for row in universe_rows
        ),
        "routes": universe_rows,
        "required_false_fields": [
            *TOP_LEVEL_FALSE_FIELDS,
            "raw_magnitude_final_gate_allowed",
            "route_promotion_authorized",
        ],
    }


def validate_readiness_route_universe_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p2_bounded_physical_solver_readiness_route_universe_manifest_v1"
    ):
        raise ValueError("unexpected P2 route universe manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P2 route universe manifest")
    if manifest["p1_surrogate_risk_role_preserved"] is not True:
        raise ValueError("P2 route universe manifest P1 role drifted")
    if manifest["route_universe_row_count"] <= 0:
        raise ValueError("P2 route universe is empty")
    if set(manifest["source_paths"]) != {source["path"] for source in SOURCE_CONTRACTS}:
        raise ValueError("P2 route universe source set drifted")
    for row in manifest["routes"]:
        _require_false(row, TOP_LEVEL_FALSE_FIELDS, row["candidate_id"])
        if row["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"P2 route P1 role drifted: {row['candidate_id']}")
        if row["raw_magnitude_final_gate_allowed"] is not False:
            raise ValueError(f"P2 route raw gate drifted: {row['candidate_id']}")
        if row["route_promotion_authorized"] is not False:
            raise ValueError(f"P2 route promotion drifted: {row['candidate_id']}")
        if row["bounded_route_universe_role"] != "future_solver_preflight_only":
            raise ValueError(f"P2 route role drifted: {row['candidate_id']}")
        if any(
            key.startswith("raw_") and key != "raw_magnitude_final_gate_allowed"
            for key in row
        ):
            raise ValueError(f"P2 route universe must not carry raw proxy fields: {row['candidate_id']}")
    return manifest


def build_readiness_schema_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_readiness_registry(load_readiness_registry(project_root))
    lanes = []
    for lane in registry["readiness_lanes"]:
        output = lane["readiness_output_contract"]
        lanes.append(
            {
                "lane_id": lane["lane_id"],
                "readiness_status": lane["readiness_status"],
                "artifact_status": output["artifact_status"],
                "solver_output_path": output["solver_output_path"],
                "required_readiness_fields": output["required_readiness_fields"],
                "required_false_fields": output["required_false_fields"],
                "allowed_gate_metric_families": lane["gate_policy"][
                    "allowed_gate_metric_families"
                ],
                "raw_magnitude_final_gate_allowed": lane["gate_policy"][
                    "raw_arbitrary_unit_magnitude_final_gate_allowed"
                ],
                "calibrated_claim_allowed": lane["calibrated_claim_allowed"],
                "p0_release_conclusion_changed": lane["p0_release_conclusion_changed"],
                "p1_surrogate_risk_role_preserved": lane[
                    "p1_surrogate_risk_role_preserved"
                ],
                "physical_solver_execution_authorized": lane[
                    "physical_solver_execution_authorized"
                ],
                "measured_data_ingest_authorized": lane[
                    "measured_data_ingest_authorized"
                ],
            }
        )
    return {
        "schema_version": (
            "ev_nodi_p2_bounded_physical_solver_readiness_schema_manifest_v1"
        ),
        "stage": "P2_bounded_physical_solver_readiness_complete",
        "manifest_role": "lane_readiness_schema_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "lane_count": len(lanes),
        "lanes": lanes,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
        "required_gate_metric_families": [
            "rank",
            "rank_percentile",
            "pairwise_inversion",
        ],
    }


def validate_readiness_schema_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p2_bounded_physical_solver_readiness_schema_manifest_v1"
    ):
        raise ValueError("unexpected P2 schema manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P2 schema manifest")
    if manifest["p1_surrogate_risk_role_preserved"] is not True:
        raise ValueError("P2 schema manifest P1 role drifted")
    if manifest["lane_count"] != len(EXPECTED_LANE_IDS):
        raise ValueError("P2 schema manifest lane count drifted")
    for lane in manifest["lanes"]:
        _require_false(lane, TOP_LEVEL_FALSE_FIELDS, lane["lane_id"])
        if lane["p1_surrogate_risk_role_preserved"] is not True:
            raise ValueError(f"P2 lane P1 role drifted: {lane['lane_id']}")
        if lane["artifact_status"] != "planned_readiness_schema_only":
            raise ValueError(f"P2 lane artifact status drifted: {lane['lane_id']}")
        if lane["solver_output_path"] is not None:
            raise ValueError(f"P2 lane must not declare solver output: {lane['lane_id']}")
        if lane["raw_magnitude_final_gate_allowed"] is not False:
            raise ValueError(f"P2 lane raw gate drifted: {lane['lane_id']}")
        if set(lane["allowed_gate_metric_families"]) != {
            "rank",
            "rank_percentile",
            "pairwise_inversion",
        }:
            raise ValueError(f"P2 lane gate families drifted: {lane['lane_id']}")
        for field in TOP_LEVEL_FALSE_FIELDS:
            if field not in lane["required_false_fields"]:
                raise ValueError(f"P2 lane missing false field: {lane['lane_id']} {field}")
    return manifest


def write_readiness_schema_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_readiness_schema_manifest(
        build_readiness_schema_manifest(project_root)
    )
    output_path = project_root / P2_READINESS_SCHEMA_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_readiness_source_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_readiness_source_binding_manifest(
        build_readiness_source_binding_manifest(project_root)
    )
    output_path = project_root / P2_READINESS_SOURCE_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_readiness_route_universe_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_readiness_route_universe_manifest(
        build_readiness_route_universe_manifest(project_root)
    )
    output_path = project_root / P2_READINESS_ROUTE_UNIVERSE_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_readiness_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_readiness_artifact_manifest(
        build_readiness_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P2_READINESS_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_readiness_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        write_readiness_source_binding_manifest(project_root),
        write_readiness_route_universe_manifest(project_root),
        write_readiness_schema_manifest(project_root),
        write_readiness_artifact_manifest(project_root),
    ]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P2 readiness manifests")


def verify_readiness_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_readiness_registry(load_readiness_registry(project_root))
    source_binding_manifest = validate_readiness_source_binding_manifest(
        build_readiness_source_binding_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P2_READINESS_SOURCE_BINDING_MANIFEST,
        source_binding_manifest,
        "P2 readiness source binding manifest",
    )
    route_universe_manifest = validate_readiness_route_universe_manifest(
        build_readiness_route_universe_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P2_READINESS_ROUTE_UNIVERSE_MANIFEST,
        route_universe_manifest,
        "P2 readiness route universe manifest",
    )
    schema_manifest = validate_readiness_schema_manifest(
        build_readiness_schema_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P2_READINESS_SCHEMA_MANIFEST,
        schema_manifest,
        "P2 readiness schema manifest",
    )
    artifact_manifest = validate_readiness_artifact_manifest(
        build_readiness_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P2_READINESS_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P2 readiness artifact manifest",
    )

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P2_READINESS_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P2 readiness claim language drifted: {relpath}")

    return [
        "PASS bounded_physical_solver_readiness_registry",
        "PASS bounded_physical_solver_readiness_source_binding_manifest_current",
        "PASS bounded_physical_solver_readiness_route_universe_manifest_current",
        "PASS bounded_physical_solver_readiness_schema_manifest_current",
        "PASS bounded_physical_solver_readiness_artifact_manifest_current",
        "PASS bounded_physical_solver_execution_blocked",
        "PASS bounded_physical_solver_measured_data_ingest_blocked",
        "PASS bounded_physical_solver_claim_boundaries",
    ]
