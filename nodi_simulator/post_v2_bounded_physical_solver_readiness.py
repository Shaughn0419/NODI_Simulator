"""P2 bounded physical-solver readiness governance helpers.

This module records solver-readiness contracts only. It does not run physical
solvers, generate solver cases, ingest measured data, or promote routes.
"""

from __future__ import annotations

import json
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
P2_READINESS_ARTIFACT_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_artifact_manifest.json"
)
P2_READINESS_SCHEMA_MANIFEST = (
    P2_READINESS_DIR / "bounded_physical_solver_readiness_schema_manifest.json"
)
P2_READINESS_README = P2_READINESS_DIR / "README.md"

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
        "verifier_authorized",
    }
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
    if registry.get("stage") != "P2_bounded_physical_solver_readiness_phase_1":
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
        "stage": "P2_bounded_physical_solver_readiness_phase_1",
        "manifest_role": "schema_governance_artifact_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
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
        "stage": "P2_bounded_physical_solver_readiness_phase_1",
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
    for relpath in (P2_READINESS_REGISTRY, P2_READINESS_PLAN, P2_READINESS_README.as_posix()):
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P2 readiness claim language drifted: {relpath}")

    return [
        "PASS bounded_physical_solver_readiness_registry",
        "PASS bounded_physical_solver_readiness_schema_manifest_current",
        "PASS bounded_physical_solver_readiness_artifact_manifest_current",
        "PASS bounded_physical_solver_execution_blocked",
        "PASS bounded_physical_solver_measured_data_ingest_blocked",
        "PASS bounded_physical_solver_claim_boundaries",
    ]
