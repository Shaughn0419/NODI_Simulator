"""Import manifest-bound wet observation artifacts into intake rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.realism_v2_io import sha256_file


SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION = (
    "sidewall_wet_surface_observation_manifest_import_v1"
)
SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_CLAIM_BOUNDARY = (
    "wet_surface_observation_manifest_import_not_yield_not_detection_not_route_score"
)
IMPORT_READY_STATUS = "wet_observation_manifest_row_ready_for_intake"
IMPORT_REJECTED_STATUS = "wet_observation_manifest_row_rejected"
ALLOWED_SOURCE_KINDS = {
    "simulation_manifest",
    "assumption_manifest",
    "solver_output",
    "surrogate_output",
    "nodi_output",
    "comsol_context",
}
SIMULATION_CLAIM_LEVEL = "simulation_only"


@dataclass(frozen=True)
class SidewallWetSurfaceObservationManifestImportAuditRow:
    import_row_id: str
    import_version: str
    route_candidate_id: str
    endpoint_id: str
    source_kind: str
    model_or_solver_id: str
    assumption_manifest_id: str
    validity_domain: str
    uncertainty_semantics: str
    claim_level: str
    observation_source_artifact: str
    observation_source_sha256: str
    import_status: str
    import_rejection_reason: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_MANIFEST_FIELDS = (
    "route_candidate_id",
    "endpoint_id",
    "observation_artifact_id",
    "observation_artifact_class",
    "source_kind",
    "model_or_solver_id",
    "assumption_manifest_id",
    "validity_domain",
    "uncertainty_semantics",
    "claim_level",
    "observation_source_artifact",
    "source_geometry_match_level",
    "provided_fields",
    "controls_status",
    "replicate_count",
    "uncertainty_interval_status",
    "pre_registered_rule_status",
)


def build_wet_observation_rows_from_manifest(
    *,
    contract_rows: list[Mapping[str, Any]],
    manifest_rows: list[Mapping[str, Any]],
    artifact_root: str | Path,
) -> tuple[list[dict[str, str]], list[SidewallWetSurfaceObservationManifestImportAuditRow]]:
    contracts = {
        (
            str(row.get("route_candidate_id", "")),
            str(row.get("endpoint_id", "")),
        ): row
        for row in contract_rows
    }
    output_rows: list[dict[str, str]] = []
    audit_rows: list[SidewallWetSurfaceObservationManifestImportAuditRow] = []
    for manifest in manifest_rows:
        output_row, audit_row = _build_import_row(
            manifest=manifest,
            contract=contracts.get(
                (
                    str(manifest.get("route_candidate_id", "")),
                    str(manifest.get("endpoint_id", "")),
                )
            ),
            artifact_root=Path(artifact_root),
        )
        audit_rows.append(audit_row)
        if output_row is not None:
            output_rows.append(output_row)
    return output_rows, audit_rows


def _build_import_row(
    *,
    manifest: Mapping[str, Any],
    contract: Mapping[str, Any] | None,
    artifact_root: Path,
) -> tuple[dict[str, str] | None, SidewallWetSurfaceObservationManifestImportAuditRow]:
    route_id = str(manifest.get("route_candidate_id", ""))
    endpoint_id = str(manifest.get("endpoint_id", ""))
    source_text = str(manifest.get("observation_source_artifact", "")).strip()
    source_kind = str(manifest.get("source_kind", "")).strip()
    claim_level = str(manifest.get("claim_level", "")).strip()
    missing_fields = [
        field for field in REQUIRED_MANIFEST_FIELDS if not str(manifest.get(field, "")).strip()
    ]
    rejection_reason = ""
    source_sha = ""
    if contract is None:
        rejection_reason = "contract_row_missing"
    elif missing_fields:
        rejection_reason = "missing_manifest_fields:" + ";".join(missing_fields)
    elif source_kind not in ALLOWED_SOURCE_KINDS:
        rejection_reason = "invalid_source_kind"
    elif claim_level != SIMULATION_CLAIM_LEVEL:
        rejection_reason = "invalid_claim_level"
    else:
        source_path = Path(source_text)
        if not source_path.is_absolute():
            source_path = artifact_root / source_path
        if not source_path.exists() or not source_path.is_file():
            rejection_reason = "source_artifact_missing"
        else:
            source_sha = sha256_file(source_path)
    status = IMPORT_READY_STATUS if not rejection_reason else IMPORT_REJECTED_STATUS
    audit_row = SidewallWetSurfaceObservationManifestImportAuditRow(
        import_row_id=f"WET-OBS-MANIFEST-IMPORT-{route_id}-{endpoint_id}",
        import_version=SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION,
        route_candidate_id=route_id,
        endpoint_id=endpoint_id,
        source_kind=source_kind,
        model_or_solver_id=str(manifest.get("model_or_solver_id", "")).strip(),
        assumption_manifest_id=str(
            manifest.get("assumption_manifest_id", "")
        ).strip(),
        validity_domain=str(manifest.get("validity_domain", "")).strip(),
        uncertainty_semantics=str(
            manifest.get("uncertainty_semantics", "")
        ).strip(),
        claim_level=claim_level,
        observation_source_artifact=source_text,
        observation_source_sha256=source_sha,
        import_status=status,
        import_rejection_reason=rejection_reason,
        claim_boundary=SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_CLAIM_BOUNDARY,
    )
    if rejection_reason:
        return None, audit_row
    output_row = {
        "route_candidate_id": route_id,
        "endpoint_id": endpoint_id,
        "observation_artifact_id": str(manifest.get("observation_artifact_id", "")),
        "observation_artifact_class": str(manifest.get("observation_artifact_class", "")),
        "source_kind": source_kind,
        "model_or_solver_id": str(manifest.get("model_or_solver_id", "")),
        "assumption_manifest_id": str(manifest.get("assumption_manifest_id", "")),
        "validity_domain": str(manifest.get("validity_domain", "")),
        "uncertainty_semantics": str(manifest.get("uncertainty_semantics", "")),
        "claim_level": claim_level,
        "observation_source_artifact": source_text,
        "observation_source_sha256": source_sha,
        "source_geometry_match_level": str(manifest.get("source_geometry_match_level", "")),
        "provided_fields": str(manifest.get("provided_fields", "")),
        "controls_status": str(manifest.get("controls_status", "")),
        "replicate_count": str(manifest.get("replicate_count", "")),
        "uncertainty_interval_status": str(
            manifest.get("uncertainty_interval_status", "")
        ),
        "pre_registered_rule_status": str(
            manifest.get("pre_registered_rule_status", "")
        ),
    }
    return output_row, audit_row
