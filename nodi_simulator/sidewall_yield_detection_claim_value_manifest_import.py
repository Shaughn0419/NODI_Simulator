"""Import manifest-bound yield and detection value artifacts into review rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.realism_v2_io import sha256_file
from nodi_simulator.sidewall_yield_detection_claim_value_review import (
    DETECTION_REQUIRED_FIELDS,
    YIELD_REQUIRED_FIELDS,
)


SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_VERSION = (
    "sidewall_yield_detection_claim_value_manifest_import_v1"
)
SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_CLAIM_BOUNDARY = (
    "yield_detection_claim_value_manifest_import_not_template_not_route_score"
)
DETECTION_CLAIM_VALUE_BRANCH = "detection_probability_value"
YIELD_CLAIM_VALUE_BRANCH = "yield_wet_value"
IMPORT_READY_STATUS = "yield_detection_claim_value_manifest_row_ready_for_review"
IMPORT_REJECTED_STATUS = "yield_detection_claim_value_manifest_row_rejected"
ALLOWED_SOURCE_KINDS = {
    "simulation_manifest",
    "assumption_manifest",
    "solver_output",
    "surrogate_output",
    "nodi_output",
    "comsol_context",
}
SIMULATION_CLAIM_LEVEL = "simulation_only"
SIMULATION_PROVENANCE_FIELDS = (
    "source_kind",
    "model_or_solver_id",
    "assumption_manifest_id",
    "formula_id",
    "validity_domain",
    "uncertainty_semantics",
    "claim_level",
)


@dataclass(frozen=True)
class SidewallYieldDetectionClaimValueManifestImportAuditRow:
    import_row_id: str
    import_version: str
    claim_value_branch: str
    route_candidate_id: str
    source_kind: str
    model_or_solver_id: str
    assumption_manifest_id: str
    formula_id: str
    validity_domain: str
    uncertainty_semantics: str
    claim_level: str
    source_artifact_path: str
    source_artifact_sha256: str
    import_status: str
    import_rejection_reason: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_yield_detection_claim_value_rows_from_manifest(
    *,
    manifest_rows: list[Mapping[str, Any]],
    artifact_root: str | Path,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[SidewallYieldDetectionClaimValueManifestImportAuditRow],
]:
    detection_rows: list[dict[str, str]] = []
    yield_rows: list[dict[str, str]] = []
    audit_rows: list[SidewallYieldDetectionClaimValueManifestImportAuditRow] = []
    seen: set[tuple[str, str]] = set()
    for manifest in manifest_rows:
        key = (
            str(manifest.get("claim_value_branch", "")).strip(),
            str(manifest.get("route_candidate_id", "")).strip(),
        )
        duplicate_key = bool(key[0] and key[1] and key in seen)
        if key[0] and key[1]:
            seen.add(key)
        output_row, audit_row = _build_import_row(
            manifest=manifest,
            artifact_root=Path(artifact_root),
            duplicate_key=duplicate_key,
        )
        audit_rows.append(audit_row)
        if output_row is None:
            continue
        if key[0] == DETECTION_CLAIM_VALUE_BRANCH:
            detection_rows.append(output_row)
        elif key[0] == YIELD_CLAIM_VALUE_BRANCH:
            yield_rows.append(output_row)
    return detection_rows, yield_rows, audit_rows


def _build_import_row(
    *,
    manifest: Mapping[str, Any],
    artifact_root: Path,
    duplicate_key: bool,
) -> tuple[dict[str, str] | None, SidewallYieldDetectionClaimValueManifestImportAuditRow]:
    branch = str(manifest.get("claim_value_branch", "")).strip()
    route_id = str(manifest.get("route_candidate_id", "")).strip()
    source_text = str(manifest.get("source_artifact_path", "")).strip()
    source_kind = str(manifest.get("source_kind", "")).strip()
    claim_level = str(manifest.get("claim_level", "")).strip()
    rejection_reason = ""
    source_sha = ""
    if branch == DETECTION_CLAIM_VALUE_BRANCH:
        required_fields = DETECTION_REQUIRED_FIELDS
    elif branch == YIELD_CLAIM_VALUE_BRANCH:
        required_fields = YIELD_REQUIRED_FIELDS
    else:
        required_fields = ()
        rejection_reason = "invalid_claim_value_branch"
    if not rejection_reason and duplicate_key:
        rejection_reason = "duplicate_route_branch"
    if not rejection_reason:
        manifest_required = tuple(
            field for field in required_fields if field != "source_artifact_sha256"
        )
        missing_fields = [
            field
            for field in (
                "claim_value_branch",
                *SIMULATION_PROVENANCE_FIELDS,
                *manifest_required,
            )
            if not str(manifest.get(field, "")).strip()
        ]
        if missing_fields:
            rejection_reason = "missing_manifest_fields:" + ";".join(missing_fields)
    if not rejection_reason and source_kind not in ALLOWED_SOURCE_KINDS:
        rejection_reason = "invalid_source_kind"
    if not rejection_reason and claim_level != SIMULATION_CLAIM_LEVEL:
        rejection_reason = "invalid_claim_level"
    if not rejection_reason:
        source_path = Path(source_text)
        if not source_path.is_absolute():
            source_path = artifact_root / source_path
        if not source_path.exists() or not source_path.is_file():
            rejection_reason = "source_artifact_missing"
        else:
            source_sha = sha256_file(source_path)
    status = IMPORT_READY_STATUS if not rejection_reason else IMPORT_REJECTED_STATUS
    audit_row = SidewallYieldDetectionClaimValueManifestImportAuditRow(
        import_row_id=f"YIELD-DETECTION-VALUE-MANIFEST-IMPORT-{branch or 'unknown'}-{route_id or 'unknown'}",
        import_version=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_VERSION,
        claim_value_branch=branch,
        route_candidate_id=route_id,
        source_kind=source_kind,
        model_or_solver_id=str(manifest.get("model_or_solver_id", "")).strip(),
        assumption_manifest_id=str(
            manifest.get("assumption_manifest_id", "")
        ).strip(),
        formula_id=str(manifest.get("formula_id", "")).strip(),
        validity_domain=str(manifest.get("validity_domain", "")).strip(),
        uncertainty_semantics=str(
            manifest.get("uncertainty_semantics", "")
        ).strip(),
        claim_level=claim_level,
        source_artifact_path=source_text,
        source_artifact_sha256=source_sha,
        import_status=status,
        import_rejection_reason=rejection_reason,
        claim_boundary=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_CLAIM_BOUNDARY,
    )
    if rejection_reason:
        return None, audit_row
    output_row = {
        field: (
            source_sha
            if field == "source_artifact_sha256"
            else str(manifest.get(field, ""))
        )
        for field in required_fields
    }
    output_row.update(
        {
            field: str(manifest.get(field, ""))
            for field in SIMULATION_PROVENANCE_FIELDS
        }
    )
    return output_row, audit_row
