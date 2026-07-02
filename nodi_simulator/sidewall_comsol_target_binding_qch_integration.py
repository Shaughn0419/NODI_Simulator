"""COMSOL W500/D900 target binding plus formal q_ch integration rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_VERSION = (
    "sidewall_comsol_target_binding_qch_integration_v1"
)
SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY = (
    "comsol_target_binding_and_formal_qch_input_not_route_score_not_yield_not_detection"
)
SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_STATUS = (
    "comsol_target_bound_existing_exact_pressure_flow_formal_qch_integrated"
)


@dataclass(frozen=True)
class SidewallComsolTargetBindingQchIntegrationRow:
    integration_row_id: str
    integration_version: str
    route_candidate_id: str
    route_geometry_family: str
    validation_request_id: str
    case_id: str
    qch_sidecar_id: str
    source_geometry_hash: str
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    top_width_nm: float
    depth_nm: float
    launcher_binding_status: str
    launcher_path: str
    launcher_sha256: str
    build_scaffold_sha256: str
    pressure_runner_sha256: str
    connections_sha256: str
    nodi_template_sha256: str
    comsol_repo_head: str
    comsol_repo_dirty_count: int
    launch_command_template_sha256: str
    launch_command_template: str
    expected_stage11_channels_csv: str
    expected_stage11_summary_csv: str
    expected_stage11_mph: str
    stage11_legacy_reference_ack_required: bool
    comsol_launch_required_for_current_qch: bool
    comsol_rerun_allowed_by_user_authorization: bool
    comsol_rerun_recommended_now: bool
    external_result_id: str
    model_or_measurement_id: str
    result_artifact_sha256: str
    pressure_drop_Pa: float
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    pressure_flow_binding_status: str
    formal_qch_sidecar_current: bool
    formal_qch_weighting_current: bool
    may_satisfy_route_formula_qch_branch_now: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    production_ingestion_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallComsolTargetBindingQchGuardRow:
    guard_row_id: str
    integration_version: str
    guard_target: str
    implementation_authorized: bool
    current_input_status: str
    claim_current: bool
    activation_allowed_now: bool
    required_next_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_comsol_target_binding_qch_integration(
    *,
    request_rows: list[Mapping[str, Any]],
    binding_rows: list[Mapping[str, Any]],
    sidecar_rows: list[Mapping[str, Any]],
    source_hashes: Mapping[str, str],
    launcher_path: str,
    launch_command_template: str,
    launch_command_template_sha256: str,
    comsol_repo_head: str,
    comsol_repo_dirty_count: int,
) -> tuple[
    list[SidewallComsolTargetBindingQchIntegrationRow],
    list[SidewallComsolTargetBindingQchGuardRow],
]:
    bindings_by_request = {
        str(row.get("validation_request_id", "")): row for row in binding_rows
    }
    sidecars_by_request = {
        str(row.get("source_validation_request_id", "")): row for row in sidecar_rows
    }
    rows: list[SidewallComsolTargetBindingQchIntegrationRow] = []
    for request in sorted(
        request_rows,
        key=lambda row: str(row.get("validation_request_id", "")),
    ):
        request_id = str(request.get("validation_request_id", ""))
        binding = bindings_by_request.get(request_id, {})
        sidecar = sidecars_by_request.get(request_id, {})
        route_candidate_id = str(request.get("route_candidate_id", ""))
        case_id = str(request.get("case_id", ""))
        sidewall_deg = _float(request.get("sidewall_deg_comsol"))
        taper_deg = _float(request.get("sidewall_taper_angle_deg_nodi"))
        route_family = (
            "ideal_rectangle"
            if abs(sidewall_deg - 90.0) < 1.0e-9 and abs(taper_deg) < 1.0e-9
            else "trapezoid_tapered_sidewalls"
        )
        label = _stage11_label(request_id, taper_deg)
        accepted = (
            str(binding.get("per_route_acceptance_status", ""))
            == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
            and _bool(sidecar.get("formal_qch_sidecar_current"))
        )
        rows.append(
            SidewallComsolTargetBindingQchIntegrationRow(
                integration_row_id=f"COMSOL-TARGET-QCH-{route_candidate_id}",
                integration_version=SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_VERSION,
                route_candidate_id=route_candidate_id,
                route_geometry_family=route_family,
                validation_request_id=request_id,
                case_id=case_id,
                qch_sidecar_id=str(request.get("qch_sidecar_id", "")),
                source_geometry_hash=str(request.get("source_geometry_hash", "")),
                sidewall_deg_comsol=sidewall_deg,
                sidewall_taper_angle_deg_nodi=taper_deg,
                top_width_nm=_float(request.get("top_width_nm")),
                depth_nm=_float(request.get("depth_nm")),
                launcher_binding_status="launcher_source_bound_existing_exact_result_available",
                launcher_path=launcher_path,
                launcher_sha256=source_hashes.get("launcher", ""),
                build_scaffold_sha256=source_hashes.get("build_scaffold", ""),
                pressure_runner_sha256=source_hashes.get("pressure_runner", ""),
                connections_sha256=source_hashes.get("connections", ""),
                nodi_template_sha256=source_hashes.get("nodi_template", ""),
                comsol_repo_head=comsol_repo_head,
                comsol_repo_dirty_count=comsol_repo_dirty_count,
                launch_command_template_sha256=launch_command_template_sha256,
                launch_command_template=launch_command_template,
                expected_stage11_channels_csv=(
                    f"full_chip/dwg_analysis/stage11_explicit_nano_pressure_only_{label}_channels_raw.csv"
                ),
                expected_stage11_summary_csv=(
                    f"full_chip/dwg_analysis/stage11_explicit_nano_pressure_only_{label}_summary.csv"
                ),
                expected_stage11_mph=(
                    "full_chip/models/stage11_explicit_nano_pressure_only/"
                    f"stage11_explicit_nano_pressure_only_{label}.mph"
                ),
                stage11_legacy_reference_ack_required=True,
                comsol_launch_required_for_current_qch=False,
                comsol_rerun_allowed_by_user_authorization=True,
                comsol_rerun_recommended_now=False,
                external_result_id=str(binding.get("external_result_id", "")),
                model_or_measurement_id=str(binding.get("external_result_id", ""))
                and str(sidecar.get("source_external_result_id", "")),
                result_artifact_sha256=str(
                    _external_result_hash(binding, sidecar)
                ),
                pressure_drop_Pa=_float(binding.get("pressure_drop_Pa")),
                q_ch_m3_s=_float(sidecar.get("q_ch_m3_s")),
                formal_flow_split_fraction=_float(
                    sidecar.get("formal_flow_split_fraction")
                ),
                pressure_flow_binding_status=(
                    "accepted_exact_pressure_flow_formal_qch_input"
                    if accepted
                    else "blocked_missing_exact_pressure_flow_or_formal_qch_sidecar"
                ),
                formal_qch_sidecar_current=accepted,
                formal_qch_weighting_current=False,
                may_satisfy_route_formula_qch_branch_now=accepted,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                detection_probability_current=False,
                production_ingestion_current=False,
                next_required_evidence=(
                    "route formula policy plus detector/blank transfer and wet observation evidence"
                ),
                hard_fail_if=(
                    "q_ch_input_promoted_to_route_score_winner_yield_detection_or_production_without_formula_and_detector_wet_evidence"
                ),
                claim_boundary=SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY,
            )
        )
    return rows, _guard_rows()


def _guard_rows() -> list[SidewallComsolTargetBindingQchGuardRow]:
    specs = [
        (
            "comsol_rerun",
            "authorized_available_not_required_current_qch",
            False,
            "operator may rerun only through bound command template when fresh COMSOL receipt is needed",
            "comsol_rerun_without_bound_launcher_hash_command_template_and_output_target",
        ),
        (
            "formal_qch_input",
            "accepted_exact_pressure_flow_available",
            True,
            "route formula packet before weighting or scoring",
            "formal_qch_used_as_route_score_without_route_formula_packet",
        ),
        (
            "route_score",
            "blocked_formula_detector_wet_required",
            False,
            "route formula plus detector/blank transfer and wet observation evidence",
            "route_score_true_from_qch_only",
        ),
        (
            "yield",
            "blocked_wet_evidence_required",
            False,
            "wet observation evidence and yield model packet",
            "yield_true_from_pressure_flow_or_detector_context_only",
        ),
        (
            "detection_probability",
            "blocked_detector_transfer_required",
            False,
            "detector blank transfer evidence and detection model packet",
            "detection_probability_true_from_qch_or_profile_grid_only",
        ),
    ]
    return [
        SidewallComsolTargetBindingQchGuardRow(
            guard_row_id=f"COMSOL-TARGET-QCH-GUARD-{target}",
            integration_version=SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_VERSION,
            guard_target=target,
            implementation_authorized=True,
            current_input_status=status,
            claim_current=current,
            activation_allowed_now=current and target == "formal_qch_input",
            required_next_evidence=required,
            hard_fail_if=hard_fail,
            claim_boundary=SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY,
        )
        for target, status, current, required, hard_fail in specs
    ]


def _stage11_label(request_id: str, taper_deg: float) -> str:
    suffix = "rect90" if request_id.endswith("001") else "theta85"
    theta = f"{taper_deg:.1f}".replace(".", "p")
    return f"pkgc_w500_d900_{suffix}_taper{theta}"


def _external_result_hash(
    binding: Mapping[str, Any],
    sidecar: Mapping[str, Any],
) -> str:
    for key in ("result_artifact_sha256",):
        value = str(binding.get(key, "") or sidecar.get(key, ""))
        if value:
            return value
    return ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))
