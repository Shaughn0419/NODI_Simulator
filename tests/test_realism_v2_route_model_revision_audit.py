from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def audit_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("r4_route_model_revision_audit")
    rv2.run_R4_route_model_revision_audit(output, write_root_manifest=False)
    return output


def test_route_model_revision_audit_requires_exact_authorization(tmp_path: Path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R4_route_model_revision_audit(
            tmp_path,
            external_authorization="PASS_TO_R5_PLAN",
            write_root_manifest=False,
        )


def test_route_model_revision_audit_outputs_required_files_only(audit_output: Path):
    produced = {path.name for path in audit_output.iterdir() if path.is_file()}

    assert produced == rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_OUTPUTS_IF_EXECUTED


def test_route_model_revision_audit_convention_result_blocks_R5(audit_output: Path):
    rows = _read_csv(audit_output / "cross_term_sign_convention_audit.csv")
    by_id = {row["convention_id"]: row for row in rows}

    assert set(by_id) == {
        "as_recorded_cross_term",
        "global_full_wave_cross_term_sign_flip",
        "global_surrogate_cross_term_sign_flip",
        "as_recorded_ROI_signal",
        "global_full_wave_ROI_signal_sign_flip",
    }
    assert by_id["as_recorded_cross_term"][
        "main_660_nonblank_sign_preserved_fraction"
    ] == "0.25"
    assert by_id["global_full_wave_cross_term_sign_flip"][
        "main_660_nonblank_sign_preserved_fraction"
    ] == "0.75"
    assert by_id["global_full_wave_cross_term_sign_flip"][
        "main_660_recovery_gate_met"
    ] == "False"
    assert by_id["global_full_wave_cross_term_sign_flip"][
        "decision_label"
    ] == "partial_global_convention_signal_main_660_gate_not_met"
    assert all(row["R5_plan_authorized"] == "False" for row in rows)


def test_route_model_revision_audit_reference_phase_is_invariant(audit_output: Path):
    rows = _read_csv(audit_output / "reference_phase_convention_audit.csv")

    assert {row["phase_label"] for row in rows} == {"0", "pi_over_2", "pi"}
    assert all(row["cross_term_invariant_under_common_phase"] == "True" for row in rows)
    assert all(row["decision_invariant_under_common_phase"] == "True" for row in rows)


def test_route_model_revision_audit_preserves_output_provenance(audit_output: Path):
    for filename in rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_OUTPUTS_IF_EXECUTED:
        if not filename.endswith(".csv"):
            continue
        rows = _read_csv(audit_output / filename)
        assert rows, filename
        for row in rows:
            rv2.validate_required_output_fields(row)
            assert row["scenario_id"] == "R4_route_model_revision_audit"
            assert "R4_route_model_revision_audit" not in row["base_route_key"]


def test_route_model_revision_audit_decision_table_blocks_R5(audit_output: Path):
    rows = _read_csv(audit_output / "route_model_revision_decision_table.csv")

    assert len(rows) == 1
    row = rows[0]
    assert row["best_allowed_convention_id"] == "global_full_wave_cross_term_sign_flip"
    assert row["best_main_660_nonblank_sign_preserved_fraction"] == "0.75"
    assert row["main_660_recovery_threshold"] == "0.8"
    assert row["main_660_recovery_gate_met"] == "False"
    assert row["route_model_revision_audit_decision"] == (
        "partial_convention_signal_but_main_660_recovery_gate_not_met"
    )
    assert row["R5_plan_preparation_authorized"] == "False"
    assert row["R5_full_grid_v2_run"] == "False"
    assert row["future_R4_rerun_required_before_R5_plan"] == "True"
    assert row["context_route_promotion_authorized"] == "False"
    assert row["main_660_redefinition_authorized"] == "False"


def test_route_model_revision_audit_guardrails_include_both_legacy_snr_names(
    audit_output: Path,
):
    rows = _read_csv(audit_output / "route_model_revision_guardrail_summary.csv")
    by_guardrail = {row["guardrail"]: row for row in rows}

    assert by_guardrail["legacy_detector_SNR_output_header_emitted"]["value"] == "False"
    assert by_guardrail["legacy_calibrated_detector_SNR_output_header_emitted"][
        "value"
    ] == "False"
    assert by_guardrail["R5_plan_or_full_grid_v2_started"]["value"] == "False"
    assert by_guardrail["context_route_promotion_attempted"]["value"] == "False"
    assert by_guardrail["main_660_redefinition_attempted"]["value"] == "False"


def test_route_model_revision_audit_manifest_keeps_R5_false(audit_output: Path):
    manifest = json.loads((audit_output / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
    assert manifest["scenario_budget"]["R5_plan_preparation_authorized"] is False
    assert manifest["scenario_budget"]["main_660_recovery_gate_met"] is False
