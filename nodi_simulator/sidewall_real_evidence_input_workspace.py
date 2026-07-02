"""Create and audit real-evidence input CSV workspaces for sidewall routes."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import io
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.realism_v2_io import read_csv_headers, read_csv_rows


SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION = (
    "sidewall_real_evidence_input_workspace_v1"
)
SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_CLAIM_BOUNDARY = (
    "real_evidence_input_workspace_not_template_as_evidence"
)

TARGET_HEADER_ONLY_STATUS = "target_header_only_ready_no_evidence_rows"
TARGET_REAL_ROWS_PRESENT_STATUS = (
    "target_real_rows_present_not_rewritten_by_workspace"
)
TARGET_HEADER_MISMATCH_STATUS = "target_header_mismatch_blocked"
TEMPLATE_MISSING_STATUS = "template_artifact_missing_blocked"
TEMPLATE_EMPTY_STATUS = "template_header_missing_blocked"


@dataclass(frozen=True)
class SidewallRealEvidenceInputWorkspaceSpec:
    input_branch: str
    template_artifact_path: str
    target_input_path: str
    accepted_status_required: str


@dataclass(frozen=True)
class SidewallRealEvidenceInputWorkspaceRow:
    workspace_row_id: str
    workspace_version: str
    input_branch: str
    template_artifact_path: str
    target_input_path: str
    template_rows: int
    template_columns: str
    target_preexisting: bool
    target_created_now: bool
    target_header_refreshed_now: bool
    target_data_rows: int
    target_header_matches_template: bool
    target_validation_status: str
    accepted_status_required: str
    evidence_current: bool
    required_next_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_real_evidence_input_workspace(
    specs: list[SidewallRealEvidenceInputWorkspaceSpec],
    *,
    create_missing_targets: bool,
) -> list[SidewallRealEvidenceInputWorkspaceRow]:
    return [
        _workspace_row(spec, create_missing_targets=create_missing_targets)
        for spec in specs
    ]


def _workspace_row(
    spec: SidewallRealEvidenceInputWorkspaceSpec,
    *,
    create_missing_targets: bool,
) -> SidewallRealEvidenceInputWorkspaceRow:
    template_path = Path(spec.template_artifact_path)
    target_path = Path(spec.target_input_path)
    if not template_path.exists():
        return _blocked_row(spec, TEMPLATE_MISSING_STATUS)
    template_headers = read_csv_headers(template_path)
    if not template_headers:
        return _blocked_row(spec, TEMPLATE_EMPTY_STATUS)
    template_rows = read_csv_rows(template_path)

    target_preexisting = target_path.exists()
    target_created_now = False
    target_header_refreshed_now = False
    if create_missing_targets and not target_preexisting:
        _write_header_only_csv(target_path, template_headers)
        target_created_now = True

    target_rows: list[dict[str, str]] = []
    target_header_matches_template = False
    if target_path.exists():
        target_headers = read_csv_headers(target_path)
        target_header_matches_template = target_headers == template_headers
        target_rows = read_csv_rows(target_path)
        if (
            create_missing_targets
            and not target_header_matches_template
            and not target_rows
        ):
            _write_header_only_csv(target_path, template_headers)
            target_header_refreshed_now = True
            target_header_matches_template = True
            target_rows = []

    status = _target_status(
        target_exists=target_path.exists(),
        header_matches=target_header_matches_template,
        target_data_rows=len(target_rows),
    )
    return SidewallRealEvidenceInputWorkspaceRow(
        workspace_row_id=f"REAL-EVIDENCE-WORKSPACE-{spec.input_branch}",
        workspace_version=SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION,
        input_branch=spec.input_branch,
        template_artifact_path=str(template_path),
        target_input_path=str(target_path),
        template_rows=len(template_rows),
        template_columns=";".join(template_headers),
        target_preexisting=target_preexisting,
        target_created_now=target_created_now,
        target_header_refreshed_now=target_header_refreshed_now,
        target_data_rows=len(target_rows),
        target_header_matches_template=target_header_matches_template,
        target_validation_status=status,
        accepted_status_required=spec.accepted_status_required,
        evidence_current=False,
        required_next_action=(
            "fill target input rows with real artifacts, hashes, controls, "
            "uncertainty, and pre-registration fields; rerun the nine-step chain"
        ),
        hard_fail_if="header_only_or_template_rows_counted_as_claim_evidence",
        claim_boundary=SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_CLAIM_BOUNDARY,
    )


def _blocked_row(
    spec: SidewallRealEvidenceInputWorkspaceSpec,
    status: str,
) -> SidewallRealEvidenceInputWorkspaceRow:
    return SidewallRealEvidenceInputWorkspaceRow(
        workspace_row_id=f"REAL-EVIDENCE-WORKSPACE-{spec.input_branch}",
        workspace_version=SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION,
        input_branch=spec.input_branch,
        template_artifact_path=str(spec.template_artifact_path),
        target_input_path=str(spec.target_input_path),
        template_rows=0,
        template_columns="",
        target_preexisting=Path(spec.target_input_path).exists(),
        target_created_now=False,
        target_header_refreshed_now=False,
        target_data_rows=0,
        target_header_matches_template=False,
        target_validation_status=status,
        accepted_status_required=spec.accepted_status_required,
        evidence_current=False,
        required_next_action="restore template artifact before creating target input rows",
        hard_fail_if="input_workspace_used_without_template_contract",
        claim_boundary=SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_CLAIM_BOUNDARY,
    )


def _target_status(
    *,
    target_exists: bool,
    header_matches: bool,
    target_data_rows: int,
) -> str:
    if not target_exists:
        return TEMPLATE_MISSING_STATUS
    if not header_matches:
        return TARGET_HEADER_MISMATCH_STATUS
    if target_data_rows:
        return TARGET_REAL_ROWS_PRESENT_STATUS
    return TARGET_HEADER_ONLY_STATUS


def _write_header_only_csv(path: Path, headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="")
