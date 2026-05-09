"""EV reporting metadata readiness diagnostics for package-local use."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EVPreanalyticalMetadata:
    sample_source: str | None = None
    donor_or_cell_line: str | None = None
    culture_medium: str | None = None
    serum_depletion_method: str | None = None
    collection_time_h: float | None = None
    storage_temperature_C: float | None = None
    freeze_thaw_cycles: int | None = None
    isolation_method: str | None = None
    concentration_method: str | None = None
    buffer_exchange_method: str | None = None
    final_buffer: str | None = None
    filtration_um: float | None = None
    protein_assay_available: bool = False
    lipid_assay_available: bool = False
    RNA_assay_available: bool = False
    marker_panel_available: bool = False
    negative_marker_available: bool = False
    orthogonal_size_method: str | None = None


EV_REPORTING_DIAGNOSTIC_FIELDS = (
    "ev_reporting_readiness_score",
    "misev_metadata_completeness",
    "evtrack_reporting_completeness",
    "ev_characterization_completeness",
    "ev_sample_identity_claim_level",
    "ev_biological_specificity_claim_allowed",
    "ev_biological_specificity_blocker_summary",
    "ev_reporting_metadata_status",
    "ev_reporting_required_missing_fields",
    "ev_reporting_gate_passed",
)


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _fraction_present(metadata: EVPreanalyticalMetadata, fields: tuple[str, ...]) -> float:
    if not fields:
        return 1.0
    present_count = sum(1 for field in fields if _present(getattr(metadata, field)))
    return present_count / len(fields)


def build_ev_reporting_metadata_diagnostics(
    metadata: EVPreanalyticalMetadata | None = None,
) -> dict[str, object]:
    """Export EV reporting readiness and biological-specificity blockers."""
    metadata = metadata or EVPreanalyticalMetadata()
    identity_required = (
        "sample_source",
        "isolation_method",
        "final_buffer",
        "orthogonal_size_method",
    )
    preanalytical_fields = identity_required + (
        "donor_or_cell_line",
        "storage_temperature_C",
        "freeze_thaw_cycles",
    )
    characterization_flags = (
        metadata.protein_assay_available,
        metadata.lipid_assay_available,
        metadata.RNA_assay_available,
        metadata.marker_panel_available,
        metadata.negative_marker_available,
    )
    missing_required = tuple(
        field for field in identity_required if not _present(getattr(metadata, field))
    )
    misev_completeness = _fraction_present(metadata, preanalytical_fields)
    evtrack_completeness = _fraction_present(
        metadata,
        preanalytical_fields
        + (
            "culture_medium",
            "serum_depletion_method",
            "collection_time_h",
            "concentration_method",
            "buffer_exchange_method",
            "filtration_um",
        ),
    )
    characterization_completeness = sum(bool(flag) for flag in characterization_flags) / len(
        characterization_flags
    )
    biological_claim_allowed = bool(
        not missing_required
        and metadata.marker_panel_available
        and metadata.negative_marker_available
    )
    readiness = (
        0.4 * misev_completeness
        + 0.2 * evtrack_completeness
        + 0.4 * characterization_completeness
    )

    blockers = list(missing_required)
    if not metadata.marker_panel_available:
        blockers.append("marker_panel_missing")
    if not metadata.negative_marker_available:
        blockers.append("negative_marker_missing")

    if biological_claim_allowed:
        claim_level = "biological_EV_specificity_metadata_ready"
        status = "metadata_ready_for_biological_specificity_claim"
    elif not missing_required:
        claim_level = "EV_like_optical_particle_under_marker_limits"
        status = "identity_metadata_present_marker_controls_missing"
    else:
        claim_level = "EV_like_optical_particle_metadata_incomplete"
        status = "blocked_missing_required_preanalytical_metadata"

    return {
        "ev_reporting_readiness_score": readiness,
        "misev_metadata_completeness": misev_completeness,
        "evtrack_reporting_completeness": evtrack_completeness,
        "ev_characterization_completeness": characterization_completeness,
        "ev_sample_identity_claim_level": claim_level,
        "ev_biological_specificity_claim_allowed": biological_claim_allowed,
        "ev_biological_specificity_blocker_summary": (
            "none" if not blockers else " / ".join(blockers)
        ),
        "ev_reporting_metadata_status": status,
        "ev_reporting_required_missing_fields": missing_required,
        "ev_reporting_gate_passed": biological_claim_allowed,
    }
