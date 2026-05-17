"""Shared output-contract constants for the realism v2 lane.

These constants are intentionally data-only. Keeping them separate from the
large execution module makes the public governance contract easier to audit
without importing or editing the full simulation/reporting pipeline.
"""

from __future__ import annotations

RUN_MANIFEST_VOLATILE_FIELDS: frozenset[str] = frozenset({"created_at"})
RUN_MANIFEST_PROVENANCE_CHECKSUM_KIND = "stable_content_v1"
RUN_MANIFEST_LEGACY_CHECKSUM_KINDS: frozenset[str | None] = frozenset(
    {None, "raw_sha256_file", "sha256_file"}
)

MODULE_STATES = (
    "off",
    "surrogate",
    "bounded_prior",
    "measured_prior",
    "calibrated",
    "blocked",
)

CLAIM_LEVELS = (
    "relative_proxy",
    "relative_with_priors",
    "scenario_count_rate",
    "safety_sidecar",
    "diagnostic_only",
    "absolute_blocked",
    "calibrated_absolute",
)

SOURCE_TYPES = (
    "assumption",
    "datasheet",
    "literature",
    "synthetic",
    "bounded_prior",
    "measured",
    "calibrated",
)

REQUIRED_OUTPUT_PROVENANCE_FIELDS = (
    "unit",
    "source_type",
    "scenario_id",
    "claim_level",
    "calibration_dependency",
    "module_status",
    "base_route_key",
    "scenario_identity",
    "run_manifest_path",
)

FORBIDDEN_OUTPUT_NAMES: frozenset[str] = frozenset({"detector_SNR", "calibrated_detector_SNR"})


__all__ = [
    "CLAIM_LEVELS",
    "FORBIDDEN_OUTPUT_NAMES",
    "MODULE_STATES",
    "REQUIRED_OUTPUT_PROVENANCE_FIELDS",
    "RUN_MANIFEST_LEGACY_CHECKSUM_KINDS",
    "RUN_MANIFEST_PROVENANCE_CHECKSUM_KIND",
    "RUN_MANIFEST_VOLATILE_FIELDS",
    "SOURCE_TYPES",
]
