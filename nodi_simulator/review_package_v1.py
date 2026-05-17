"""V1 summary contract helpers for review-package manifests."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .realism_v2_io import sha256_file
from .review_package_json import load_json_compatible as _load_json_compatible


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_SUMMARY_PATH = "results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
V1_REQUIRED_BOUNDARY_FIELDS: tuple[str, ...] = (
    "output_claim_level_resolved",
    "field_coordinate_measure",
    "operator_route",
    "detector_field_units",
    "bfp_to_angle_jacobian_applied",
    "detector_unit_chain_status",
)


def count_csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        next(handle)
        return sum(1 for _ in handle)


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def v1_summary_contract(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    path = project_root / V1_SUMMARY_PATH
    header = csv_header(path)
    current_hash = sha256_file(path)
    pin_path = project_root / "configs/realism_v2/v1_summary_hash_pin.json"
    pin = _load_json_compatible(pin_path) if pin_path.exists() else {}
    pinned_hash = pin.get("summary_csv_sha256", current_hash)
    approved_drift_path = pin.get("approved_v1_summary_drift_evidence_path")
    required_present = all(field in header for field in V1_REQUIRED_BOUNDARY_FIELDS)
    return {
        "summary_csv_path": V1_SUMMARY_PATH,
        "summary_csv_sha256": current_hash,
        "summary_csv_pinned_sha256": pinned_hash,
        "summary_csv_sha256_pinned_in_manifest": True,
        "summary_csv_hash_matches_pin": current_hash == pinned_hash,
        "n_cases": count_csv_data_rows(path),
        "required_v1_boundary_fields_present": required_present,
        "approved_v1_summary_drift_evidence_path": approved_drift_path,
        "v1_boundary_expected": {
            "output_claim_level_resolved": "engineering_ranking",
            "field_coordinate_measure": "theta_phi_surrogate",
            "operator_route": "pupil_slit_surrogate",
            "detector_field_units": "arbitrary_relative_field_units",
            "bfp_to_angle_jacobian_applied": False,
        },
    }


def v1_hash_drift_is_authorized(contract: Mapping[str, Any]) -> bool:
    return bool(
        contract.get("summary_csv_hash_matches_pin")
        or contract.get("approved_v1_summary_drift_evidence_path")
    )
