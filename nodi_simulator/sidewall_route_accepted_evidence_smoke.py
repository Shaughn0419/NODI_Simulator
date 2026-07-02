"""Fixture-only accepted evidence smoke for the sidewall route formula chain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from nodi_simulator.sidewall_detector_wet_evidence_activation_runner import (
    build_detector_wet_evidence_activation_runner,
)
from nodi_simulator.sidewall_route_formula_activation_closure import (
    build_route_formula_activation_closure,
)
from nodi_simulator.sidewall_route_formula_review_dry_run import (
    build_route_formula_review_dry_run,
)


SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_VERSION = (
    "sidewall_route_accepted_evidence_smoke_v1"
)
SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_CLAIM_BOUNDARY = (
    "fixture_smoke_not_evidence_not_route_score_not_yield_not_detection"
)


@dataclass(frozen=True)
class SidewallRouteAcceptedEvidenceSmokeRow:
    smoke_row_id: str
    smoke_version: str
    route_candidate_id: str
    route_geometry_family: str
    detector_fixture_rows: int
    wet_fixture_rows: int
    detector_activation_ready: bool
    wet_activation_ready: bool
    route_formula_ready_for_claim_review: bool
    component_vector_ready_for_policy_review: bool
    fixture_not_evidence: bool
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    smoke_status: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_accepted_evidence_smoke(
    *,
    detector_panel_matrix_rows: list[Mapping[str, Any]],
    wet_contract_rows: list[Mapping[str, Any]],
    qch_detector_wet_binder_rows: list[Mapping[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[SidewallRouteAcceptedEvidenceSmokeRow],
    list[dict[str, Any]],
]:
    detector_fixture_rows = _detector_fixture_rows(detector_panel_matrix_rows)
    wet_fixture_rows = _wet_fixture_rows(wet_contract_rows)
    activation_rows, _contracts = build_detector_wet_evidence_activation_runner(
        detector_panel_matrix_rows=detector_panel_matrix_rows,
        wet_contract_rows=wet_contract_rows,
        detector_transfer_input_rows=detector_fixture_rows,
        wet_observation_input_rows=wet_fixture_rows,
        detector_input_present=True,
        wet_input_present=True,
        detector_input_path="fixture_not_evidence_detector_blank_transfer_rows",
        wet_input_path="fixture_not_evidence_wet_observation_rows",
    )
    closure_rows = build_route_formula_activation_closure(
        qch_detector_wet_binder_rows=qch_detector_wet_binder_rows,
        detector_wet_activation_rows=[row.to_dict() for row in activation_rows],
    )
    dry_run_rows = build_route_formula_review_dry_run(
        closure_rows=[row.to_dict() for row in closure_rows]
    )
    activation_by_route = {row.route_candidate_id: row for row in activation_rows}
    dry_by_route = {row.route_candidate_id: row for row in dry_run_rows}
    detector_counts = _count_by_route(detector_fixture_rows)
    wet_counts = _count_by_route(wet_fixture_rows)
    smoke_rows: list[SidewallRouteAcceptedEvidenceSmokeRow] = []
    for closure in closure_rows:
        route_id = closure.route_candidate_id
        activation = activation_by_route.get(route_id)
        dry = dry_by_route.get(route_id)
        formula_ready = closure.route_formula_ready_for_claim_review
        component_ready = bool(
            dry
            and dry.route_formula_review_dry_run_status
            == "route_formula_component_vector_ready_for_policy_review_not_scored"
        )
        smoke_rows.append(
            SidewallRouteAcceptedEvidenceSmokeRow(
                smoke_row_id=f"ROUTE-ACCEPTED-EVIDENCE-SMOKE-{route_id}",
                smoke_version=SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_VERSION,
                route_candidate_id=route_id,
                route_geometry_family=closure.route_geometry_family,
                detector_fixture_rows=detector_counts.get(route_id, 0),
                wet_fixture_rows=wet_counts.get(route_id, 0),
                detector_activation_ready=bool(
                    activation and activation.detector_branch_ready_for_formula
                ),
                wet_activation_ready=bool(
                    activation and activation.wet_branch_ready_for_formula
                ),
                route_formula_ready_for_claim_review=formula_ready,
                component_vector_ready_for_policy_review=component_ready,
                fixture_not_evidence=True,
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                yield_current=False,
                detection_probability_current=False,
                wet_pass_probability_current=False,
                production_ingestion_current=False,
                smoke_status=(
                    "fixture_path_passes_chain_to_component_vector_not_evidence"
                    if formula_ready and component_ready
                    else "fixture_path_failed_to_open_component_vector"
                ),
                hard_fail_if=(
                    "fixture_not_evidence_rows_written_to_real_input_paths_or_counted_as_evidence"
                ),
                claim_boundary=SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_CLAIM_BOUNDARY,
            )
        )
    return (
        detector_fixture_rows,
        wet_fixture_rows,
        smoke_rows,
        [row.to_dict() for row in dry_run_rows],
    )


def _detector_fixture_rows(panel_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, panel in enumerate(panel_rows, start=1):
        route_id = str(panel.get("route_candidate_id", ""))
        rows.append(
            {
                "route_candidate_id": route_id,
                "transfer_artifact_id": f"fixture-transfer-{route_id}",
                "blank_trace_artifact_id": f"fixture-blank-{route_id}",
                "blank_trace_artifact_path": (
                    f"fixture_not_evidence/detector_blank/{route_id}/blank_trace.csv"
                ),
                "blank_trace_sha256": _hex(index),
                "detector_response_artifact_id": f"fixture-detector-{route_id}",
                "detector_response_artifact_path": (
                    f"fixture_not_evidence/detector_blank/{route_id}/"
                    "detector_response.csv"
                ),
                "detector_response_sha256": _hex(index + 16),
                "blank_trace_geometry_match_level": "sidewall_specific",
                "detector_response_model_id": "fixture-detector-response-v1",
                "false_positive_rate_estimate": "0.0001",
                "false_positive_rate_ci_low": "0.0",
                "false_positive_rate_ci_high": "0.0004",
                "n_blank_traces": "3",
                "n_detector_calibration_runs": "3",
                "controls_status": "controls_pass",
                "uncertainty_model": "fixture_wilson_interval",
                "pre_registered_rule_status": "pre_registered",
                "fixture_not_evidence": "true",
            }
        )
    return rows


def _wet_fixture_rows(contract_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, contract in enumerate(contract_rows, start=1):
        endpoint_id = str(contract.get("endpoint_id", ""))
        route_id = str(contract.get("route_candidate_id", ""))
        rows.append(
            {
                "route_candidate_id": route_id,
                "endpoint_id": endpoint_id,
                "observation_artifact_id": f"fixture-obs-{route_id}-{endpoint_id}",
                "observation_artifact_class": str(
                    contract.get("required_artifact_class", "")
                ),
                "observation_source_artifact": (
                    f"fixture_not_evidence/{route_id}/{endpoint_id}.csv"
                ),
                "observation_source_sha256": _hex(index + 32),
                "source_geometry_match_level": "sidewall_specific",
                "provided_fields": str(contract.get("required_fields", "")),
                "controls_status": "controls_pass",
                "replicate_count": "1"
                if endpoint_id in {"material_surface_identity", "ev_sample_panel"}
                else "3",
                "uncertainty_interval_status": "uncertainty_interval_missing"
                if endpoint_id in {"material_surface_identity", "ev_sample_panel"}
                else "uncertainty_interval_present",
                "pre_registered_rule_status": "pre_registered"
                if endpoint_id
                in {"wet_pass_probability", "yield_bridge", "clogging_time_series"}
                else "not_required_for_endpoint",
                "fixture_not_evidence": "true",
            }
        )
    return rows


def _count_by_route(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        route_id = str(row.get("route_candidate_id", ""))
        counts[route_id] = counts.get(route_id, 0) + 1
    return counts


def _hex(seed: int) -> str:
    value = f"{seed:x}"
    return (value * 64)[:64]
