"""P18 bounded-lane synthesis and stop-or-continue governance helpers.

P18 summarizes the existing bounded trace lanes P6/P8/P10/P12/P14/P16.
It does not execute another solver lane, generate solver output, ingest
measured/calibration data, generate meshes, export operators, or promote routes.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_csv_rows, write_json_atomic
from .review_package import PROJECT_ROOT, claim_text_passes, load_forbidden_claims_lexicon


P18_DIR = Path("results/post_v2_bounded_lane_synthesis_stop_continue")
P18_REGISTRY = "configs/realism_v2/bounded_lane_synthesis_stop_continue_registry.yaml"
P18_REPORT = "reports/120_EV_NODI_P18_bounded_lane_synthesis_stop_continue_design.md"
P18_README = P18_DIR / "README.md"
P18_RANK_SUMMARY_CSV = P18_DIR / "bounded_lane_rank_behavior_summary.csv"
P18_SYNTHESIS_RECORD = P18_DIR / "bounded_lane_synthesis_stop_continue_record.json"
P18_ARTIFACT_MANIFEST = P18_DIR / "bounded_lane_synthesis_artifact_manifest.json"

P18_STAGE = "P18_bounded_lane_synthesis_stop_continue_design_complete"
P18_SCHEMA_VERSION = "ev_nodi_p18_bounded_lane_synthesis_stop_continue_registry_v1"
P18_DECISION = "stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy"
P18_NEXT_STAGE = "P19_next_evidence_strategy_gate"
P18_BLOCKED_FUTURE_PHRASE = "authorize seventh bounded solver lane execution"

LANE_SPECS: tuple[dict[str, str], ...] = (
    {
        "lane_stage": "P6",
        "lane_id": "minimal_bounded_green_kernel_trace",
        "path": "results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output.csv",
        "rank_field": "solver_response_rank",
        "percentile_field": "solver_response_rank_percentile",
        "signature_field": "pairwise_order_signature",
        "delta_field": "",
    },
    {
        "lane_stage": "P8",
        "lane_id": "second_bounded_phase_gradient_trace",
        "path": "results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_trace_output.csv",
        "rank_field": "second_lane_response_rank",
        "percentile_field": "second_lane_response_rank_percentile",
        "signature_field": "second_lane_pairwise_order_signature",
        "delta_field": "second_lane_vs_p6_rank_delta",
    },
    {
        "lane_stage": "P10",
        "lane_id": "third_bounded_curvature_balance_trace",
        "path": "results/post_v2_third_bounded_solver_lane_execution/third_bounded_solver_lane_trace_output.csv",
        "rank_field": "third_lane_response_rank",
        "percentile_field": "third_lane_response_rank_percentile",
        "signature_field": "third_lane_pairwise_order_signature",
        "delta_field": "third_lane_vs_p8_rank_delta",
    },
    {
        "lane_stage": "P12",
        "lane_id": "fourth_bounded_resonance_compactness_trace",
        "path": "results/post_v2_fourth_bounded_solver_lane_execution/fourth_bounded_solver_lane_trace_output.csv",
        "rank_field": "fourth_lane_response_rank",
        "percentile_field": "fourth_lane_response_rank_percentile",
        "signature_field": "fourth_lane_pairwise_order_signature",
        "delta_field": "fourth_lane_vs_p10_rank_delta",
    },
    {
        "lane_stage": "P14",
        "lane_id": "fifth_bounded_phase_curvature_residual_trace",
        "path": "results/post_v2_fifth_bounded_solver_lane_execution/fifth_bounded_solver_lane_trace_output.csv",
        "rank_field": "fifth_lane_response_rank",
        "percentile_field": "fifth_lane_response_rank_percentile",
        "signature_field": "fifth_lane_pairwise_order_signature",
        "delta_field": "fifth_lane_vs_p12_rank_delta",
    },
    {
        "lane_stage": "P16",
        "lane_id": "sixth_bounded_phase_curvature_residual_trace",
        "path": "results/post_v2_sixth_bounded_solver_lane_execution/sixth_bounded_solver_lane_trace_output.csv",
        "rank_field": "sixth_lane_response_rank",
        "percentile_field": "sixth_lane_response_rank_percentile",
        "signature_field": "sixth_lane_pairwise_order_signature",
        "delta_field": "sixth_lane_vs_p14_rank_delta",
    },
)

FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "physical_solver_execution_authorized",
    "seventh_bounded_solver_lane_execution_authorized",
    "solver_output_generated",
    "measured_data_ingest_authorized",
    "calibration_data_ingest_authorized",
    "new_mesh_generation_authorized",
    "operator_export_generation_authorized",
    "full_wave_solver_execution_authorized",
    "vector_solver_execution_authorized",
    "roughness_leakage_simulation_authorized",
    "transport_residence_time_simulation_authorized",
    "route_promotion_authorized",
    "raw_magnitude_final_gate_allowed",
    "solver_native_raw_magnitude_final_gate_allowed",
    "bounded_lanes_sufficient_for_route_promotion",
    "continue_mechanical_lanes_without_acceptance_criteria",
    "future_authorization_phrase_already_received",
)

TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
    "p5_authorization_gate_scope_preserved",
    "p6_minimal_execution_scope_preserved",
    "p7_authorization_design_scope_preserved",
    "p8_second_bounded_execution_scope_preserved",
    "p9_authorization_design_scope_preserved",
    "p10_third_bounded_execution_scope_preserved",
    "p10_closure_scope_preserved",
    "p11_authorization_design_scope_preserved",
    "p12_fourth_bounded_execution_scope_preserved",
    "p12_closure_scope_preserved",
    "p13_authorization_design_scope_preserved",
    "p14_fifth_bounded_execution_scope_preserved",
    "p14_closure_scope_preserved",
    "p15_authorization_design_scope_preserved",
    "p16_sixth_bounded_execution_scope_preserved",
    "p16_closure_scope_preserved",
    "p17_authorization_design_scope_preserved",
    "rank_instability_across_bounded_lanes_detected",
    "p19_evidence_strategy_gate_required",
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
    "main_660_redefinition_authorized",
    "optional_660_W900_D1400_redefines_main_660",
)

SUMMARY_FIELDS: tuple[str, ...] = (
    "lane_stage",
    "lane_id",
    "source_path",
    "candidate_id",
    "route_key",
    "route_role_final",
    "rank",
    "rank_percentile",
    "pairwise_order_signature",
    "previous_lane_rank_delta",
    *FALSE_FIELDS,
    *TRUE_FIELDS,
)

P18_TEXT_PATHS: tuple[str, ...] = (
    P18_REGISTRY,
    P18_REPORT,
    P18_README.as_posix(),
    "docs/schemas/p18_bounded_lane_synthesis_record_schema.md",
    "docs/schemas/p18_bounded_lane_synthesis_artifact_manifest_schema.md",
)


def _guard_payload() -> dict[str, bool]:
    return {key: False for key in FALSE_FIELDS} | {key: True for key in TRUE_FIELDS}


def _require_false(mapping: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise ValueError(f"{context} must keep {key}=false")


def _require_true(mapping: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if mapping.get(key) is not True:
            raise ValueError(f"{context} must keep {key}=true")


def _validate_guard_fields(mapping: dict[str, Any], context: str) -> None:
    _require_false(mapping, FALSE_FIELDS, context)
    _require_true(mapping, TRUE_FIELDS, context)


def _validate_claim_boundary(claims: dict[str, Any], context: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != "bounded_lane_synthesis_stop_continue_only":
        raise ValueError(f"{context} claim level drifted")


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_synthesis_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P18_REGISTRY)


def validate_synthesis_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P18_SCHEMA_VERSION:
        raise ValueError("unexpected P18 synthesis registry schema")
    if registry.get("stage") != P18_STAGE:
        raise ValueError("unexpected P18 synthesis stage")
    if registry.get("synthesis_role") != "bounded_lane_synthesis_stop_continue_design_only":
        raise ValueError("P18 synthesis role drifted")
    _validate_guard_fields(registry, "P18 registry")
    if registry["stop_continue_decision"] != P18_DECISION:
        raise ValueError("P18 stop-or-continue decision drifted")
    if registry["next_required_stage"] != P18_NEXT_STAGE:
        raise ValueError("P18 next required stage drifted")
    if registry["blocked_future_authorization_phrase"] != P18_BLOCKED_FUTURE_PHRASE:
        raise ValueError("P18 blocked future phrase drifted")
    _validate_claim_boundary(registry["claim_governance"], "P18 registry")
    if registry["lane_set"]["lane_count"] != 6:
        raise ValueError("P18 lane count drifted")
    if [lane["lane_stage"] for lane in registry["lane_set"]["lanes"]] != [
        spec["lane_stage"] for spec in LANE_SPECS
    ]:
        raise ValueError("P18 lane stages drifted")
    _validate_guard_fields(registry["lane_set"], "P18 lane set")
    _validate_synthesis_conclusion(registry["synthesis_conclusion"], "P18 synthesis conclusion")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def _validate_synthesis_conclusion(mapping: dict[str, Any], context: str) -> None:
    _validate_guard_fields(mapping, context)
    if mapping["stop_continue_decision"] != P18_DECISION:
        raise ValueError(f"{context} decision drifted")
    if mapping["route_promotion_conclusion"] != "not_supported_by_bounded_trace_lanes":
        raise ValueError(f"{context} route-promotion conclusion drifted")
    if mapping["next_required_stage"] != P18_NEXT_STAGE:
        raise ValueError(f"{context} next stage drifted")
    if mapping["main_660_top_sequence"] != [
        "main_660_W800_D1400",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "main_660_W800_D1500",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
    ]:
        raise ValueError(f"{context} main-660 top sequence drifted")
    if mapping["main_660_swap_events"] != ["P8_to_P10", "P12_to_P14", "P14_to_P16"]:
        raise ValueError(f"{context} main-660 swap events drifted")


def _read_lane_csv(project_root: Path, spec: dict[str, str]) -> list[dict[str, str]]:
    path = project_root / spec["path"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 3:
        raise ValueError(f"P18 lane source must contain exactly three rows: {spec['path']}")
    if {row["candidate_id"] for row in rows} != {
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "probe_404_W600_D1300",
    }:
        raise ValueError(f"P18 lane source route universe drifted: {spec['path']}")
    return rows


def build_rank_summary_rows(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    validate_synthesis_registry(load_synthesis_registry(project_root))
    summary: list[dict[str, Any]] = []
    for spec in LANE_SPECS:
        rows = _read_lane_csv(project_root, spec)
        for row in rows:
            if row.get("route_promotion_authorized") != "False":
                raise ValueError(f"P18 source lane route promotion drifted: {spec['path']}")
            summary.append(
                {
                    "lane_stage": spec["lane_stage"],
                    "lane_id": spec["lane_id"],
                    "source_path": spec["path"],
                    "candidate_id": row["candidate_id"],
                    "route_key": row["route_key"],
                    "route_role_final": row["route_role_final"],
                    "rank": int(row[spec["rank_field"]]),
                    "rank_percentile": float(row[spec["percentile_field"]]),
                    "pairwise_order_signature": row[spec["signature_field"]],
                    "previous_lane_rank_delta": (
                        "" if not spec["delta_field"] else int(row[spec["delta_field"]])
                    ),
                    **_guard_payload(),
                }
            )
    validate_rank_summary_rows(summary)
    return summary


def validate_rank_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) != 18:
        raise ValueError("P18 rank summary must contain 18 rows")
    for lane_stage in [spec["lane_stage"] for spec in LANE_SPECS]:
        lane_rows = [row for row in rows if row["lane_stage"] == lane_stage]
        if len(lane_rows) != 3:
            raise ValueError(f"P18 lane summary row count drifted: {lane_stage}")
        if sorted(row["rank"] for row in lane_rows) != [1, 2, 3]:
            raise ValueError(f"P18 lane ranks drifted: {lane_stage}")
        for row in lane_rows:
            for field in SUMMARY_FIELDS:
                if field not in row:
                    raise ValueError(f"P18 summary row missing field: {field}")
            _validate_guard_fields(row, f"P18 summary {lane_stage} {row['candidate_id']}")
    top_by_lane = [
        min((row for row in rows if row["lane_stage"] == spec["lane_stage"]), key=lambda row: row["rank"])[
            "candidate_id"
        ]
        for spec in LANE_SPECS
    ]
    if top_by_lane != [
        "main_660_W800_D1400",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "main_660_W800_D1500",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
    ]:
        raise ValueError("P18 top-rank sequence drifted")
    return rows


def write_rank_summary_csv(project_root: Path = PROJECT_ROOT) -> Path:
    rows = validate_rank_summary_rows(build_rank_summary_rows(project_root))
    output_path = project_root / P18_RANK_SUMMARY_CSV
    write_csv_rows(output_path, rows)
    return output_path


def _read_rank_summary_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parsed: list[dict[str, Any]] = []
    for row in rows:
        parsed.append(
            {
                **row,
                "rank": int(row["rank"]),
                "rank_percentile": float(row["rank_percentile"]),
                "previous_lane_rank_delta": (
                    "" if row["previous_lane_rank_delta"] == "" else int(row["previous_lane_rank_delta"])
                ),
                **{key: row[key] == "True" for key in (*FALSE_FIELDS, *TRUE_FIELDS) if key in row},
            }
        )
    return validate_rank_summary_rows(parsed)


def _source_binding_manifest(project_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "lane_stage": spec["lane_stage"],
            "lane_id": spec["lane_id"],
            "path": spec["path"],
            "sha256": sha256_file(project_root / spec["path"]),
        }
        for spec in LANE_SPECS
    ]


def build_synthesis_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_synthesis_registry(load_synthesis_registry(project_root))
    rows = validate_rank_summary_rows(_read_rank_summary_csv(project_root / P18_RANK_SUMMARY_CSV))
    top_sequence = [
        min((row for row in rows if row["lane_stage"] == spec["lane_stage"]), key=lambda row: row["rank"])[
            "candidate_id"
        ]
        for spec in LANE_SPECS
    ]
    record = {
        "schema_version": "ev_nodi_p18_bounded_lane_synthesis_record_v1",
        "stage": P18_STAGE,
        "record_role": "bounded_lane_synthesis_stop_continue_record",
        "source_bindings": _source_binding_manifest(project_root),
        "source_lane_count": len(LANE_SPECS),
        "summary_csv_path": P18_RANK_SUMMARY_CSV.as_posix(),
        "summary_csv_sha256": sha256_file(project_root / P18_RANK_SUMMARY_CSV),
        "summary_row_count": len(rows),
        "main_660_top_sequence": top_sequence,
        "main_660_swap_events": ["P8_to_P10", "P12_to_P14", "P14_to_P16"],
        "route_promotion_conclusion": "not_supported_by_bounded_trace_lanes",
        "stop_continue_decision": P18_DECISION,
        "next_required_stage": P18_NEXT_STAGE,
        "blocked_future_authorization_phrase": P18_BLOCKED_FUTURE_PHRASE,
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "bounded_lane_synthesis_stop_continue_only"},
        **_guard_payload(),
    }
    validate_synthesis_record(record)
    return record


def validate_synthesis_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p18_bounded_lane_synthesis_record_v1":
        raise ValueError("unexpected P18 synthesis record schema")
    if record["source_lane_count"] != 6:
        raise ValueError("P18 source lane count drifted")
    if record["summary_row_count"] != 18:
        raise ValueError("P18 summary row count drifted")
    if record["summary_csv_path"] != P18_RANK_SUMMARY_CSV.as_posix():
        raise ValueError("P18 summary CSV path drifted")
    _validate_synthesis_conclusion(record, "P18 synthesis record")
    _validate_claim_boundary(record["claim_boundary"], "P18 synthesis record")
    return record


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    path = project_root / artifact["path"]
    is_self = artifact["path"] == P18_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self else path.is_file(),
        "sha256": None if is_self else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_synthesis_registry(load_synthesis_registry(project_root))
    artifacts = [_artifact_entry(project_root, artifact) for artifact in registry["planned_artifacts"]]
    manifest = {
        "schema_version": "ev_nodi_p18_bounded_lane_synthesis_artifact_manifest_v1",
        "stage": P18_STAGE,
        "manifest_role": "bounded_lane_synthesis_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "source_bindings": _source_binding_manifest(project_root),
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "bounded_lane_synthesis_stop_continue_only"},
        "stop_continue_decision": P18_DECISION,
        "next_required_stage": P18_NEXT_STAGE,
        **_guard_payload(),
    }
    validate_artifact_manifest(manifest, project_root, allow_missing_self_manifest=True)
    return manifest


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p18_bounded_lane_synthesis_artifact_manifest_v1":
        raise ValueError("unexpected P18 artifact manifest schema")
    _validate_guard_fields(manifest, "P18 artifact manifest")
    if manifest["stop_continue_decision"] != P18_DECISION:
        raise ValueError("P18 artifact manifest decision drifted")
    _validate_claim_boundary(manifest["claim_boundary"], "P18 artifact manifest")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self = artifact["path"] == P18_ARTIFACT_MANIFEST.as_posix()
        if not (project_root / artifact["path"]).is_file() and not (allow_missing_self_manifest and is_self):
            raise ValueError(f"P18 artifact missing: {artifact['path']}")
    return manifest


def write_synthesis_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    summary_path = write_rank_summary_csv(project_root)
    record_path = project_root / P18_SYNTHESIS_RECORD
    write_json_atomic(record_path, build_synthesis_record(project_root), sort_keys=True)
    manifest_path = project_root / P18_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, build_artifact_manifest(project_root), sort_keys=True)
    return [summary_path, record_path, manifest_path]


def _assert_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if _load_json_file(path) != expected:
        raise ValueError(f"stale {label}: regenerate P18 synthesis package")


def verify_synthesis_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    expected_rows = validate_rank_summary_rows(build_rank_summary_rows(project_root))
    actual_rows = _read_rank_summary_csv(project_root / P18_RANK_SUMMARY_CSV)
    if actual_rows != expected_rows:
        raise ValueError("stale P18 rank summary CSV: regenerate synthesis package")
    record = build_synthesis_record(project_root)
    _assert_current(project_root / P18_SYNTHESIS_RECORD, record, "P18 synthesis record")
    manifest = build_artifact_manifest(project_root)
    _assert_current(project_root / P18_ARTIFACT_MANIFEST, manifest, "P18 artifact manifest")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P18_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P18 claim language drifted: {relpath}")

    return [
        "PASS bounded_lane_synthesis_registry",
        "PASS bounded_lane_rank_behavior_summary_current",
        "PASS bounded_lane_synthesis_record_current",
        "PASS bounded_lane_synthesis_artifact_manifest_current",
        "PASS bounded_lane_synthesis_no_new_solver_execution",
        "PASS bounded_lane_synthesis_route_promotion_blocked",
        "PASS bounded_lane_synthesis_p19_strategy_required",
        "PASS bounded_lane_synthesis_claim_boundaries",
    ]
