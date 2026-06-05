from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING_PATH = ROOT / "papers" / "analysis_full_v1" / "critical_paper_target_binding.csv"
TABLE_GAP_REVIEW_PATH = ROOT / "papers" / "analysis_full_v1" / "library_table_gap_review.csv"

EXPECTED_CRITICAL_PAPERS = {
    "nonfluorescent_molecule_detection_in_10_sup2_sup_nm_nanofluidic_channels_by_12a71db55c30",
    "concentration_determination_at_a_countable_molecular_level_in_nanofluidics_by_07518f2d2a3e",
    "detection_and_characterization_of_individual_nanoparticles_in_a_liquid_by_a6892db6b63d",
    "nanofluidic_optical_diffraction_interferometry_for_detection_and_classification_ba1a4bf36519",
    "supplementary_file1_3a1b5f67fa8d",
    "characterization_of_optical_diffraction_by_single_nanochannel_for_alfl_sample_detection_in_30ac3e7d5a22",
    "nanofluidic_detection_platform_for_simultaneous_light_absorption_and_scattering_measuremen_87728e30572d",
    "extended_nanofluidics_fundamental_technologies_unique_liquid_properties_and_application_in_5aa4edb149a4",
    "concentration_determination_at_a_countable_molecular_level_in_nanofluidics_by_solvent_enha_289f63ca81ca",
}

EXPECTED_TARGET_SECTIONS = {
    "channel geometry",
    "wavelength/objective/detector optics",
    "flow/pressure/transit/concentration",
    "detector/readout/threshold/SN/blank handling",
    "POD thermal parameters",
    "NODI reference/slit/BFP/ROI/diffraction fields",
}

ALLOWED_UNBOUND_STATUSES = {
    "not_parameterizable",
    "deferred_to_measured_plan",
    "engineering_default_unconfirmed_against_paper",
}


def _load_rows() -> list[dict[str, str]]:
    with BINDING_PATH.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_critical_binding_file_loads_and_covers_all_papers() -> None:
    rows = _load_rows()

    assert rows, "critical paper binding CSV must not be empty"
    assert {row["paper_id"] for row in rows} == EXPECTED_CRITICAL_PAPERS


def test_expected_critical_set_matches_library_table_gap_review() -> None:
    with TABLE_GAP_REVIEW_PATH.open(newline="") as handle:
        live_critical = {
            row["paper_id"]
            for row in csv.DictReader(handle)
            if row["priority"] == "critical"
        }

    assert EXPECTED_CRITICAL_PAPERS == live_critical, (
        f"missing={live_critical - EXPECTED_CRITICAL_PAPERS}, "
        f"extra={EXPECTED_CRITICAL_PAPERS - live_critical}"
    )


def test_each_critical_paper_has_all_required_target_sections() -> None:
    rows = _load_rows()

    for paper_id in EXPECTED_CRITICAL_PAPERS:
        sections = {row["target_section"] for row in rows if row["paper_id"] == paper_id}
        assert EXPECTED_TARGET_SECTIONS <= sections, paper_id


def test_bound_rows_have_source_value_unit_and_target_field() -> None:
    rows = _load_rows()

    for row in rows:
        if row["binding_status"] != "bound":
            continue
        assert row["source_page_or_rendered_page"], row
        assert row["paper_value"], row
        assert row["unit"], row
        assert row["target_config_field"], row


def test_target_module_files_exist_in_repo() -> None:
    rows = _load_rows()
    seen_paths: set[str] = set()

    for row in rows:
        for piece in row["target_module"].split(";"):
            path = piece.strip()
            if path:
                seen_paths.add(path)

    for path in seen_paths:
        assert (ROOT / path).exists(), f"target_module path missing: {path}"


def test_unbound_rows_use_explicit_boundary_statuses() -> None:
    rows = _load_rows()

    for row in rows:
        if row["binding_status"] == "bound":
            continue
        assert row["binding_status"] in ALLOWED_UNBOUND_STATUSES, row
        assert row["if_unavailable_boundary"], row


def test_bound_rows_unlock_only_level_one_or_no_current_claim() -> None:
    rows = _load_rows()

    for row in rows:
        if row["binding_status"] != "bound":
            continue
        claim = row["claim_level_unlocked"].lower()
        assert (
            claim.startswith("level-1")
            or claim.startswith("level 1")
            or claim.startswith("no ")
        ), row


def test_level_two_or_higher_requires_measured_artifact_provenance() -> None:
    rows = _load_rows()
    measured_tokens = {
        "measured_artifact",
        "measured_blank",
        "measured_transfer",
        "calibrated_lookup",
        "empirical_blank",
    }

    for row in rows:
        claim = row["claim_level_unlocked"].lower()
        if "level-2" not in claim and "level 2" not in claim and "level-3" not in claim and "level 3" not in claim:
            continue
        provenance = " ".join(
            [
                row["source_type"],
                row["source_page_or_rendered_page"],
                row["extraction_status"],
            ]
        ).lower()
        assert any(token in provenance for token in measured_tokens), row
