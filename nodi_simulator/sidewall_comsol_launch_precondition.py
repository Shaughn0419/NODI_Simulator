"""COMSOL launch precondition packet for sidewall Package C branches."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION = (
    "sidewall_comsol_launch_precondition_v1"
)
SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY = (
    "comsol_launch_precondition_authorized_path_not_launch_not_solver_claim"
)
COMSOL_LAUNCH_PRECONDITION_READY_STATUS = (
    "comsol_launch_precondition_ready_target_binding_required"
)


@dataclass(frozen=True)
class SidewallComsolLaunchPreconditionRow:
    precondition_row_id: str
    precondition_version: str
    lane: str
    current_status: str
    user_authorization_status: str
    authorized_to_prepare: bool
    authorized_to_launch_when_preconditions_pass: bool
    precondition_passed: bool
    launch_allowed_now: bool
    mph_load_allowed_now: bool
    comsol_executable_detected: bool
    comsolbatch_executable_detected: bool
    version_check_passed: bool
    nodi_current_head_bound: bool
    comsol_side_project_detected: bool
    comsol_side_project_head_bound: bool
    comsol_side_project_clean_required: bool
    target_mph_or_model_bound: bool
    branch_solver_script_bound: bool
    launch_command_hash_bound: bool
    output_manifest_path_bound: bool
    current_claim_level: str
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallComsolContextRow:
    context_row_id: str
    precondition_version: str
    context_kind: str
    context_path: str
    context_status: str
    target_nodi_commit: str
    observed_value: str
    stale_or_missing_reason: str
    allowed_use: str
    blocked_use: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallComsolLaunchClaimGuardRow:
    guard_row_id: str
    precondition_version: str
    promotion_target: str
    implementation_authorized: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_comsol_launch_precondition(
    *,
    solver_branch_rows: list[Mapping[str, Any]],
    electrokinetic_preflight_status: Mapping[str, Any],
    toolchain: Mapping[str, Any],
    comsol_project: Mapping[str, Any],
    mirror_request_rows: list[Mapping[str, Any]],
    nodi_current_head: str,
) -> tuple[
    list[SidewallComsolLaunchPreconditionRow],
    list[SidewallComsolContextRow],
    list[SidewallComsolLaunchClaimGuardRow],
]:
    comsol_branch = _branch_row(solver_branch_rows, "comsol_clean_mirror_receipt")
    flow_branch = _branch_row(solver_branch_rows, "trapezoid_flow_solver")
    ek_ready = (
        str(electrokinetic_preflight_status.get("disposition", ""))
        == "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_READY_PROFILE_GRID_REQUIRED"
    )
    rows = [
        _precondition_row(
            lane="toolchain_detection",
            policy=comsol_branch,
            current_status="comsol_toolchain_detected_version_checked"
            if _bool(toolchain.get("comsolbatch_detected"))
            else "blocked_comsolbatch_missing",
            passed=_bool(toolchain.get("comsolbatch_detected"))
            and _bool(toolchain.get("version_check_passed")),
            comsol_executable_detected=_bool(toolchain.get("comsol_detected")),
            comsolbatch_executable_detected=_bool(toolchain.get("comsolbatch_detected")),
            version_check_passed=_bool(toolchain.get("version_check_passed")),
            nodi_current_head_bound=True,
            comsol_side_project_detected=_bool(comsol_project.get("project_detected")),
            comsol_side_project_head_bound=_bool(comsol_project.get("head_bound")),
            comsol_side_project_clean_required=True,
            current_claim_level="toolchain_detection_only_no_model_launch",
            next_required_evidence="target model path, solver script, command hash, and output manifest",
            hard_fail_if="launch_started_from_toolchain_detection_only",
        ),
        _precondition_row(
            lane="clean_mirror_receipt",
            policy=comsol_branch,
            current_status="clean_mirror_receipt_required_for_current_nodi_head",
            passed=False,
            comsol_executable_detected=_bool(toolchain.get("comsol_detected")),
            comsolbatch_executable_detected=_bool(toolchain.get("comsolbatch_detected")),
            version_check_passed=_bool(toolchain.get("version_check_passed")),
            nodi_current_head_bound=True,
            comsol_side_project_detected=_bool(comsol_project.get("project_detected")),
            comsol_side_project_head_bound=_bool(comsol_project.get("head_bound")),
            comsol_side_project_clean_required=True,
            current_claim_level="receipt_required_no_comsol_launch",
            next_required_evidence="COMSOL-side mirror receipt targeting current NODI head",
            hard_fail_if="comsol_launch_true_without_current_head_clean_mirror_receipt",
        ),
        _precondition_row(
            lane="target_model_binding",
            policy=flow_branch,
            current_status="blocked_target_mph_or_solver_script_not_bound",
            passed=False,
            comsol_executable_detected=_bool(toolchain.get("comsol_detected")),
            comsolbatch_executable_detected=_bool(toolchain.get("comsolbatch_detected")),
            version_check_passed=_bool(toolchain.get("version_check_passed")),
            nodi_current_head_bound=True,
            comsol_side_project_detected=_bool(comsol_project.get("project_detected")),
            comsol_side_project_head_bound=_bool(comsol_project.get("head_bound")),
            comsol_side_project_clean_required=True,
            current_claim_level="launch_precondition_not_model_execution",
            next_required_evidence=(
                "branch-specific target .mph or solver-generation script, source descriptor, "
                "output manifest path, and command hash"
            ),
            hard_fail_if="mph_load_or_solver_run_true_without_target_model_binding",
        ),
        _precondition_row(
            lane="electrokinetic_dependency",
            policy=flow_branch,
            current_status="electrokinetic_preflight_available_but_no_solver_grid_output"
            if ek_ready
            else "blocked_electrokinetic_preflight_missing",
            passed=ek_ready,
            comsol_executable_detected=_bool(toolchain.get("comsol_detected")),
            comsolbatch_executable_detected=_bool(toolchain.get("comsolbatch_detected")),
            version_check_passed=_bool(toolchain.get("version_check_passed")),
            nodi_current_head_bound=True,
            comsol_side_project_detected=_bool(comsol_project.get("project_detected")),
            comsol_side_project_head_bound=_bool(comsol_project.get("head_bound")),
            comsol_side_project_clean_required=True,
            current_claim_level="electrokinetic_preflight_dependency_only",
            next_required_evidence=(
                "profile-aware electrokinetic grid implementation or explicit branch exclusion"
            ),
            hard_fail_if="electrokinetic_solver_claim_true_from_comsol_launch_precondition",
        ),
        _precondition_row(
            lane="launch_command_binding",
            policy=flow_branch,
            current_status="blocked_launch_command_hash_missing",
            passed=False,
            comsol_executable_detected=_bool(toolchain.get("comsol_detected")),
            comsolbatch_executable_detected=_bool(toolchain.get("comsolbatch_detected")),
            version_check_passed=_bool(toolchain.get("version_check_passed")),
            nodi_current_head_bound=True,
            comsol_side_project_detected=_bool(comsol_project.get("project_detected")),
            comsol_side_project_head_bound=_bool(comsol_project.get("head_bound")),
            comsol_side_project_clean_required=True,
            current_claim_level="command_preflight_not_execution",
            next_required_evidence="dry-run command string, command sha256, expected outputs, and timeout policy",
            hard_fail_if="comsolbatch_started_without_command_hash_and_output_manifest",
        ),
    ]
    contexts = _context_rows(
        toolchain=toolchain,
        comsol_project=comsol_project,
        mirror_request_rows=mirror_request_rows,
        nodi_current_head=nodi_current_head,
    )
    return rows, contexts, _claim_guard_rows()


def _branch_row(rows: list[Mapping[str, Any]], branch_id: str) -> Mapping[str, Any]:
    for row in rows:
        if str(row.get("branch_id", "")) == branch_id:
            return row
    return {}


def _precondition_row(
    *,
    lane: str,
    policy: Mapping[str, Any],
    current_status: str,
    passed: bool,
    comsol_executable_detected: bool,
    comsolbatch_executable_detected: bool,
    version_check_passed: bool,
    nodi_current_head_bound: bool,
    comsol_side_project_detected: bool,
    comsol_side_project_head_bound: bool,
    comsol_side_project_clean_required: bool,
    current_claim_level: str,
    next_required_evidence: str,
    hard_fail_if: str,
) -> SidewallComsolLaunchPreconditionRow:
    return SidewallComsolLaunchPreconditionRow(
        precondition_row_id=f"COMSOL-LAUNCH-PRECONDITION-{lane}",
        precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
        lane=lane,
        current_status=current_status,
        user_authorization_status=str(policy.get("user_authorization_status", "authorized")),
        authorized_to_prepare=_bool(policy.get("authorized_to_prepare", True)),
        authorized_to_launch_when_preconditions_pass=True,
        precondition_passed=passed,
        launch_allowed_now=False,
        mph_load_allowed_now=False,
        comsol_executable_detected=comsol_executable_detected,
        comsolbatch_executable_detected=comsolbatch_executable_detected,
        version_check_passed=version_check_passed,
        nodi_current_head_bound=nodi_current_head_bound,
        comsol_side_project_detected=comsol_side_project_detected,
        comsol_side_project_head_bound=comsol_side_project_head_bound,
        comsol_side_project_clean_required=comsol_side_project_clean_required,
        target_mph_or_model_bound=False,
        branch_solver_script_bound=False,
        launch_command_hash_bound=False,
        output_manifest_path_bound=False,
        current_claim_level=current_claim_level,
        next_required_evidence=next_required_evidence,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
    )


def _context_rows(
    *,
    toolchain: Mapping[str, Any],
    comsol_project: Mapping[str, Any],
    mirror_request_rows: list[Mapping[str, Any]],
    nodi_current_head: str,
) -> list[SidewallComsolContextRow]:
    stale_targets = sorted(
        {
            str(row.get("target_nodi_commit", ""))
            for row in mirror_request_rows
            if str(row.get("target_nodi_commit", ""))
            and str(row.get("target_nodi_commit", "")) != nodi_current_head
        }
    )
    rows = [
        SidewallComsolContextRow(
            context_row_id="COMSOL-CONTEXT-toolchain",
            precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
            context_kind="toolchain",
            context_path=str(toolchain.get("comsolbatch_path", "")),
            context_status="detected" if _bool(toolchain.get("comsolbatch_detected")) else "missing",
            target_nodi_commit=nodi_current_head,
            observed_value=str(toolchain.get("version_text", "")),
            stale_or_missing_reason="",
            allowed_use="toolchain availability evidence for future branch packet",
            blocked_use="model launch or solver claim",
            claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
        ),
        SidewallComsolContextRow(
            context_row_id="COMSOL-CONTEXT-comsol-side-project",
            precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
            context_kind="sibling_project",
            context_path=str(comsol_project.get("project_path", "")),
            context_status="detected" if _bool(comsol_project.get("project_detected")) else "missing",
            target_nodi_commit=nodi_current_head,
            observed_value=str(comsol_project.get("head", "")),
            stale_or_missing_reason=str(comsol_project.get("dirty_summary", "")),
            allowed_use="project location and head context for clean mirror receipt",
            blocked_use="implicit acceptance of dirty COMSOL state",
            claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
        ),
        SidewallComsolContextRow(
            context_row_id="COMSOL-CONTEXT-legacy-mirror-request",
            precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
            context_kind="legacy_mirror_request",
            context_path="reports/joint_interface_20260701/NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.csv",
            context_status="stale_for_current_head" if stale_targets else "not_present_or_current",
            target_nodi_commit=nodi_current_head,
            observed_value=";".join(stale_targets),
            stale_or_missing_reason=(
                "legacy request targets older NODI commit" if stale_targets else ""
            ),
            allowed_use="historical no-run mirror context only",
            blocked_use="current launch authorization or current mirror receipt",
            claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
        ),
        SidewallComsolContextRow(
            context_row_id="COMSOL-CONTEXT-target-model-binding",
            precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
            context_kind="target_model_binding",
            context_path="",
            context_status="missing_target_mph_or_solver_script",
            target_nodi_commit=nodi_current_head,
            observed_value="",
            stale_or_missing_reason="no branch-specific NODI sidewall target model/script bound",
            allowed_use="next execution requirement",
            blocked_use="COMSOL launch or .mph load",
            claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
        ),
    ]
    return rows


def _claim_guard_rows() -> list[SidewallComsolLaunchClaimGuardRow]:
    specs = [
        (
            "comsol_launch",
            "current-head mirror receipt, target model/script, command hash, output manifest",
            "comsol_launch_true_without_all_preconditions",
        ),
        (
            "mph_load",
            "target .mph path, read mode, expected extracted fields, and output hash",
            "mph_load_true_without_target_mph_binding",
        ),
        (
            "pressure_flow_solver_claim",
            "solver output manifest, tolerance, mesh/grid validation, and source hash",
            "pressure_flow_solver_claim_true_without_solver_manifest",
        ),
        (
            "electrokinetic_solver_claim",
            "profile-aware grid solver package and electrokinetic preflight pass",
            "electrokinetic_claim_true_from_launch_precondition",
        ),
        (
            "formal_q_ch_or_route_score",
            "formal q_ch sidecar plus route/yield/detection contract",
            "q_ch_or_route_score_true_from_comsol_precondition",
        ),
        (
            "yield_detection_wet_or_production",
            "wet/detection evidence packets and separate release ledger",
            "yield_detection_or_production_true_from_comsol_precondition",
        ),
    ]
    return [
        SidewallComsolLaunchClaimGuardRow(
            guard_row_id=f"COMSOL-LAUNCH-GUARD-{target}",
            precondition_version=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
        )
        for target, required, hard_fail in specs
    ]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}
