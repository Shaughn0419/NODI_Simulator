from __future__ import annotations

import csv
import json
from pathlib import Path

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_micro_anchor_dry_run_outputs_required_files(tmp_path):
    summary = rv2.run_micro_anchor(tmp_path, write_root_manifest=False)

    assert summary["micro_anchor_rows"] == 16
    assert summary["invalid_et2030_current_path"] == "forbidden"
    for name in (
        "micro_anchor_summary.csv",
        "unit_guardrail_summary.csv",
        "detector_connection_state_machine_summary.csv",
        "mie_to_power_unit_check.csv",
        "blank_rare_tail_check.csv",
        "smoke_run_cost_estimate.csv",
        "run_manifest.json",
        "micro_anchor_report.md",
    ):
        assert (tmp_path / name).exists(), name


def test_micro_anchor_guardrails_are_encoded_in_outputs(tmp_path):
    rv2.run_micro_anchor(tmp_path, write_root_manifest=False)

    micro_rows = _read_csv(tmp_path / "micro_anchor_summary.csv")
    unit_rows = _read_csv(tmp_path / "unit_guardrail_summary.csv")
    state_rows = _read_csv(tmp_path / "detector_connection_state_machine_summary.csv")
    blank_rows = _read_csv(tmp_path / "blank_rare_tail_check.csv")
    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))

    assert micro_rows
    assert all(row["P_ref_ROI_W_unit"] == "W" for row in micro_rows)
    assert all(row["P_sca_ROI_W_unit"] == "W" for row in micro_rows)
    assert all(row["P_cross_ROI_W_unit"] == "W" for row in micro_rows)
    assert all(row["SNR_claim_level"] != "calibrated_absolute" for row in micro_rows)
    assert all(row["scenario_detector_SNR"] for row in micro_rows)
    assert all(row["operator_throughput_preserved"] == "True" for row in micro_rows)
    assert all(
        row["finite_monte_carlo_zero_event_inferred"] == "False" for row in blank_rows
    )
    assert any(
        row["connection_state_id"] == "ET2030_BNC_direct_to_LI5640_current_input"
        and row["connection_physical_validity"] == "forbidden"
        for row in state_rows
    )
    assert {row["unit"] for row in unit_rows} == {"W"}
    assert manifest["R2_anchor_smoke_run"] is False
    assert manifest["R3_reduced_grid_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["scenario_budget"]["uses_full_scenario_registry"] is False


def test_micro_anchor_output_rows_have_required_v2_provenance(tmp_path):
    rv2.run_micro_anchor(tmp_path, write_root_manifest=False)
    for row in _read_csv(tmp_path / "micro_anchor_summary.csv"):
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] == "micro_anchor_nominal_sanity"
        assert row["claim_level"] == "absolute_blocked"
        assert "micro_anchor_nominal_sanity" not in row["base_route_key"]
        assert "micro_anchor_nominal_sanity" in row["scenario_identity"]


def test_micro_anchor_reference_power_independent_of_particle(tmp_path):
    rv2.run_micro_anchor(tmp_path, write_root_manifest=False)
    rows = _read_csv(tmp_path / "micro_anchor_summary.csv")
    grouped: dict[tuple[str, str, str], set[str]] = {}
    for row in rows:
        key = (row["wavelength_nm"], row["width_nm"], row["depth_nm"])
        grouped.setdefault(key, set()).add(row["P_ref_ROI_W"])
        assert row["P_ref_scale_independent_of_particle"] == "True"

    assert grouped
    assert all(len(values) == 1 for values in grouped.values())
