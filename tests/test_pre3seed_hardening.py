from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from nodi_simulator.pre3seed_hardening import (
    CANDIDATE_MANIFEST_PATH,
    CARRY_FORWARD_PATH,
    FORMAL_LAUNCH_CONFIRMATION_FLAG,
    FORMAL_LAUNCH_CONTRACT_VERSION,
    FORMAL_P19_REQUIRED_ARTIFACT_PATHS,
    FORMAL_PRELAUNCH_MANIFEST_PATH,
    FORMAL_RUN_PLAN_CSV_PATH,
    FORMAL_RUN_PLAN_JSON_PATH,
    FORMAL_WORKER_COUNT,
    PreflightGateError,
    _json_safe_diagnostic_value,
    STABILITY_MATRIX_PATH,
    _flatten_sweep_result,
    _sweep_scope_metadata,
    analysis_script_hash,
    build_candidate_manifest_rows,
    build_claim_linter_policy,
    build_detector_readout_outputs,
    build_ev_prior_outputs,
    build_formula_ledger_rows,
    build_dual_lens_top_table,
    build_formal_3seed_run_plan,
    build_formal_prelaunch_manifest,
    build_geometry_transport_matrix,
    build_interface_outputs,
    build_pooled_per_seed_consistency,
    build_reference_ablation_outputs,
    build_stability_synthesis,
    relpath,
    scan_preflight_claim_text,
    sha256_or_na,
    sha256_payload,
    validate_formula_ledger,
    validate_formal_execution_freeze,
    validate_preflight_table_scope,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _base_governed_row(**overrides):
    row = {
        "lens_policy": "lens_B_only",
        "b_stage": "B7",
        "events_per_case": "1000",
        "normalization_policy": "fixed_660_reference",
        "reference_route": "channel_angular_surrogate",
        "detector_route": "theta_phi_surrogate",
        "threshold_source": "synthetic_background_mad",
        "readout_route": "lockin_surrogate",
        "claim_level": "synthetic/proxy recommendation-qualification gate",
        "selected_annulus_boundary": "selected-annulus event-position window",
    }
    row.update(overrides)
    return row


def test_preflight_claim_linter_blocks_unscoped_winners_and_allows_boundaries():
    policy = build_claim_linter_policy()

    blocked = scan_preflight_claim_text(
        "404 wins and has the best sensitivity.",
        policy,
        source="unit",
    )
    assert {finding["severity"] for finding in blocked} == {"hard_stop"}

    allowed = scan_preflight_claim_text(
        "404 branch remains a stress branch; calibrated cross-wavelength "
        "superiority is blocked pending measured calibration.",
        policy,
        source="unit",
    )
    assert allowed == []


def test_validate_preflight_table_scope_rejects_unscoped_mixed_lens():
    rows = [
        _base_governed_row(lens_policy="lens_A"),
        _base_governed_row(lens_policy="lens_B"),
    ]

    with pytest.raises(PreflightGateError, match="mixed lens_policy"):
        validate_preflight_table_scope(rows, table_name="mixed_lens")


def test_validate_preflight_table_scope_rejects_mixed_lens_even_when_diagnostic():
    rows = [
        _base_governed_row(lens_policy="lens_A", claim_level="diagnostic comparison only"),
        _base_governed_row(lens_policy="lens_B", claim_level="diagnostic comparison only"),
    ]

    with pytest.raises(PreflightGateError, match="mixed lens_policy"):
        validate_preflight_table_scope(rows, table_name="mixed_diagnostic_lens")


def test_validate_preflight_table_scope_rejects_detection_rate_without_denominator():
    rows = [_base_governed_row(detection_rate=0.2)]

    with pytest.raises(PreflightGateError, match="detection_rate fields require"):
        validate_preflight_table_scope(rows, table_name="missing_denominator")


def test_validate_preflight_table_scope_requires_selected_annulus_boundary():
    rows = [_base_governed_row(selected_annulus_boundary="selected-annulus optical BFP annulus")]

    with pytest.raises(PreflightGateError, match="selected-annulus lacks"):
        validate_preflight_table_scope(rows, table_name="bad_annulus")


def test_formula_ledger_covers_mandatory_topics_with_tests_or_blockers():
    rows = build_formula_ledger_rows()

    validate_formula_ledger(rows)
    topic_text = "\n".join(
        f"{row['model_step']} {row['formula_or_transformation']}".lower()
        for row in rows
    )
    for token in [
        "diameter",
        "vacuum",
        "medium wavelength",
        "core-shell",
        "dcsca/domega",
        "bfp jacobian",
        "exact complex",
        "brownian",
        "selected-annulus",
        "wilson",
        "normalization",
    ]:
        assert token in topic_text
    assert all(row["test_id"] or "blocker" in row["dimension_check_status"] for row in rows)


def test_candidate_manifest_is_multi_source_and_preserves_stress_branches():
    rows = build_candidate_manifest_rows()

    sources = {
        source
        for row in rows
        for source in str(row["candidate_set_source"]).split(";")
        if source
    }
    assert sources >= {
        "historical_top",
        "B7_sidecar",
        "Tsuyama_like_control",
        "Au_anchor",
        "reference_stress",
        "detector_stress",
        "threshold_readout_stress",
        "EV_prior_stress",
        "contaminant_overlap_stress",
        "geometry_wall_risk_stress",
        "short_wavelength_exploratory",
        "narrow_channel_exploratory",
    }
    assert "stress_branch" in {row["preflight_role"] for row in rows}
    assert all(
        float(row["particle_radius_nm"]) == pytest.approx(float(row["diameter_nm"]) / 2.0)
        for row in rows
    )


def test_candidate_stability_classes_preserve_nonrobust_branches():
    candidates = build_candidate_manifest_rows()
    _, reference_summary, _ = build_reference_ablation_outputs(candidates)
    _, detector_labels, threshold_labels, pulse_guardrail = build_detector_readout_outputs(candidates)
    geometry_rows = build_geometry_transport_matrix(candidates)
    _, _, ev_summary = build_ev_prior_outputs(candidates)
    interface_matrix, _ = build_interface_outputs(candidates)

    stability_rows, demotions, carry_forward = build_stability_synthesis(
        candidates,
        reference_summary,
        detector_labels,
        threshold_labels,
        geometry_rows,
        ev_summary,
        interface_matrix,
    )

    classes = {row["stability_class"] for row in stability_rows}
    assert "robust_relative_candidate" in classes
    assert "conditional_candidate" in classes
    assert "stress_branch" in classes
    assert "diagnostic_only" in classes
    assert demotions
    assert all(row["allowed_in_low_event_rehearsal"] == "true" for row in carry_forward)


def test_shortwave_flags_do_not_demote_by_wavelength_alone():
    candidates = build_candidate_manifest_rows()
    _, reference_summary, _ = build_reference_ablation_outputs(candidates)
    _, detector_labels, threshold_labels, _ = build_detector_readout_outputs(candidates)
    geometry_rows = build_geometry_transport_matrix(candidates)
    _, _, ev_summary = build_ev_prior_outputs(candidates)
    interface_matrix, _ = build_interface_outputs(candidates)
    stability_rows, _, _ = build_stability_synthesis(
        candidates,
        reference_summary,
        detector_labels,
        threshold_labels,
        geometry_rows,
        ev_summary,
        interface_matrix,
    )
    by_family = {row["candidate_family_id"]: row for row in stability_rows}

    assert by_family["shortwave_404_W600_D1300"]["stability_class"] == "conditional_candidate"
    assert by_family["less_narrow_404_W700_D1400"]["stability_class"] == "conditional_candidate"
    assert "short_wavelength_exposure_transfer_unknown" in by_family["shortwave_404_W600_D1300"]["claim_boundary_flags"]
    assert by_family["narrow_404_W500_D1500"]["stability_class"] == "stress_branch"
    assert "geometry_or_wall_transport_high_risk" in by_family["narrow_404_W500_D1500"]["classification_reason"]


def test_shortwave_can_enter_robust_when_evidence_gates_are_stable():
    candidates = build_candidate_manifest_rows()
    _, reference_summary, _ = build_reference_ablation_outputs(candidates)
    patched_reference = []
    for row in reference_summary:
        row = dict(row)
        if row["candidate_family_id"] == "shortwave_404_W600_D1300":
            row["reference_stability_label"] = "reference_stable_for_relative_recommendation"
            row["reference_rank_delta"] = "0"
            row["unsupported_only_winner"] = "false"
            row["phase_sign_sensitive"] = "false"
        patched_reference.append(row)
    _, detector_labels, threshold_labels, _ = build_detector_readout_outputs(candidates)
    geometry_rows = build_geometry_transport_matrix(candidates)
    _, _, ev_summary = build_ev_prior_outputs(candidates)
    interface_matrix, _ = build_interface_outputs(candidates)
    stability_rows, _, _ = build_stability_synthesis(
        candidates,
        patched_reference,
        detector_labels,
        threshold_labels,
        geometry_rows,
        ev_summary,
        interface_matrix,
    )
    row = {
        row["candidate_family_id"]: row
        for row in stability_rows
    }["shortwave_404_W600_D1300"]

    assert row["stability_class"] == "robust_relative_candidate"
    assert "short_wavelength_exposure_transfer_unknown" in row["claim_boundary_flags"]


def test_formal_sweep_rows_are_not_tagged_as_micro_smoke():
    result = {
        "particle_name": "EV_like_nominal_100nm",
        "wavelength_m": 660e-9,
        "width_m": 800e-9,
        "depth_m": 1400e-9,
        "summary": {
            "n_events": 10_000,
            "n_detected": 100,
            "detection_rate": 0.01,
            "selected_detector_mode_annulus_n_events": 120,
            "selected_detector_mode_annulus_n_detected": 2,
        },
        "reference": {},
    }

    row = _flatten_sweep_result(
        result,
        seed=11,
        route_id="660_800x1400",
        scope=_sweep_scope_metadata("pre3seed_formal_3seed_10000e"),
    )

    assert row["claim_level"] == "formal_3seed_10000e_relative_proxy_no_calibration_raw_summary"
    assert row["lens_policy"] == "parallel_all_crossing_and_selected_annulus_outputs"
    assert row["b_stage"] == "formal_3seed_10000e"
    assert "micro_smoke" not in row["claim_level"]


def _stability_fixture():
    candidates = build_candidate_manifest_rows()
    family_rows = {}
    for row in candidates:
        family_rows.setdefault(row["candidate_family_id"], row)
    family_rows = list(family_rows.values())
    _, reference_summary, _ = build_reference_ablation_outputs(family_rows)
    _, detector_labels, threshold_labels, _ = build_detector_readout_outputs(family_rows)
    geometry_rows = build_geometry_transport_matrix(candidates)
    _, _, ev_summary = build_ev_prior_outputs(candidates)
    interface_matrix, _ = build_interface_outputs(family_rows)
    stability_rows, _, carry_rows = build_stability_synthesis(
        family_rows,
        reference_summary,
        detector_labels,
        threshold_labels,
        geometry_rows,
        ev_summary,
        interface_matrix,
    )
    return candidates, family_rows, stability_rows, carry_rows


def test_formal_run_plan_is_manifest_driven_and_freezes_dual_outputs():
    candidates, family_rows, stability_rows, carry_rows = _stability_fixture()

    plan = build_formal_3seed_run_plan(
        carry_rows,
        family_rows,
        stability_rows,
        seeds=(11, 22, 33),
        events_per_case=10_000,
        particle_panel_size=len({row["particle_id"] for row in candidates}),
    )

    allowed = {
        row["candidate_family_id"]
        for row in carry_rows
        if row["allowed_in_large_3seed_10000e"] == "true"
    }
    assert {row["candidate_family_id"] for row in plan} == allowed
    assert {int(row["seed"]) for row in plan} == {11, 22, 33}
    assert {int(row["events_per_case"]) for row in plan} == {10_000}
    assert all(row["all_crossing_output_required"] == "true" for row in plan)
    assert all(row["selected_annulus_output_required"] == "true" for row in plan)
    assert all("event-position window" in row["selected_annulus_boundary"] for row in plan)


def test_dual_lens_top_table_separates_denominators_and_scope_keys():
    _, family_rows, stability_rows, _ = _stability_fixture()
    summary_rows = [
        {
            "seed": 11,
            "particle_name": "EV_like_nominal_100nm",
            "wavelength_nm": 660,
            "width_nm": 800,
            "depth_nm": 1400,
            "n_events": 10,
            "detection_rate": 0.5,
            "all_crossing_n_events": 10,
            "all_crossing_detection_rate": 0.5,
            "selected_detector_mode_annulus_n_events": 4,
            "selected_detector_mode_annulus_detection_rate": 0.75,
        },
        {
            "seed": 22,
            "particle_name": "EV_like_nominal_100nm",
            "wavelength_nm": 660,
            "width_nm": 800,
            "depth_nm": 1400,
            "n_events": 10,
            "detection_rate": 0.4,
            "all_crossing_n_events": 10,
            "all_crossing_detection_rate": 0.4,
            "selected_detector_mode_annulus_n_events": 5,
            "selected_detector_mode_annulus_detection_rate": 0.8,
        },
    ]

    top_rows = build_dual_lens_top_table(summary_rows, stability_rows, family_rows)
    consistency = build_pooled_per_seed_consistency(top_rows)

    assert {"all_crossing", "selected_annulus_event_position_window"} <= {
        row["lens_policy"] for row in top_rows
    }
    assert all("lens=" in row["route_scope_key"] for row in top_rows)
    selected = [
        row for row in top_rows
        if row["lens_policy"] == "selected_annulus_event_position_window"
    ]
    assert selected
    assert all("event-position window" in row["selected_annulus_boundary"] for row in selected)
    assert all(row["detection_rate_denominator"] in {4, 5, 9} for row in selected)
    assert consistency


def test_formal_prelaunch_manifest_records_command_hashes_and_boundaries():
    _, family_rows, stability_rows, carry_rows = _stability_fixture()
    plan = build_formal_3seed_run_plan(carry_rows, family_rows, stability_rows)
    top_rows = build_dual_lens_top_table(
        [
            {
                "seed": 11,
                "particle_name": "EV_like_nominal_100nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 1400,
                "n_events": 10,
                "detection_rate": 0.5,
                "all_crossing_n_events": 10,
                "all_crossing_detection_rate": 0.5,
                "selected_detector_mode_annulus_n_events": 4,
                "selected_detector_mode_annulus_detection_rate": 0.75,
            }
        ],
        stability_rows,
        family_rows,
    )
    consistency = build_pooled_per_seed_consistency(top_rows)

    manifest = build_formal_prelaunch_manifest(
        formal_plan_rows=plan,
        top_table_rows=top_rows,
        consistency_rows=consistency,
    )

    assert "--events-per-case 10000" in manifest["exact_command_template"]
    assert "--allow-large-run" in manifest["exact_command_template"]
    assert FORMAL_LAUNCH_CONFIRMATION_FLAG in manifest["exact_command_template"]
    assert f"--workers {FORMAL_WORKER_COUNT}" in manifest["exact_command_template"]
    assert manifest["events_per_case"] == 10_000
    assert manifest["planned_worker_count"] == FORMAL_WORKER_COUNT
    assert manifest["seed_list"] == [11, 22, 33]
    assert "route_scope_key" in manifest["required_top_table_blocker_columns"]
    assert "no formal 10000e computation" in manifest["claim_boundary"]
    assert manifest["diagnostic_snapshot_required"] is True
    assert manifest["diagnostic_snapshot_schema"] == "pre3seed_formal_case_diagnostic_snapshot_v1"
    assert "pre3seed_formal_3seed_10000e_diagnostic_snapshot.jsonl" in manifest["expected_formal_output_files"]
    contract = manifest["launch_authorization_contract"]
    assert contract["contract_version"] == FORMAL_LAUNCH_CONTRACT_VERSION
    assert contract["requires_explicit_user_launch_authorization"] is True
    assert FORMAL_LAUNCH_CONFIRMATION_FLAG in contract["required_execute_flags"]
    assert contract["planned_worker_count"] == FORMAL_WORKER_COUNT
    assert contract["required_worker_flag"] == f"--workers {FORMAL_WORKER_COUNT}"
    assert contract["scope"] == "no_measured_data_level1_relative_proxy_route_ranking"
    assert manifest["p19_required_artifact_hashes"]
    for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS:
        assert relpath(PROJECT_ROOT / path, PROJECT_ROOT) in manifest["p19_required_artifact_hashes"]


def test_formal_execution_freeze_rejects_input_hash_mismatch(tmp_path):
    for path in (
        CARRY_FORWARD_PATH,
        CANDIDATE_MANIFEST_PATH,
        STABILITY_MATRIX_PATH,
        FORMAL_RUN_PLAN_CSV_PATH,
        FORMAL_RUN_PLAN_JSON_PATH,
        FORMAL_PRELAUNCH_MANIFEST_PATH,
    ):
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("placeholder\n", encoding="utf-8")
    plan = [{"candidate_family_id": "unit_family", "seed": 11}]
    plan_hash = sha256_payload(plan)
    (tmp_path / FORMAL_RUN_PLAN_JSON_PATH).write_text(
        json.dumps({"formal_run_plan_hash": plan_hash}),
        encoding="utf-8",
    )
    (tmp_path / FORMAL_PRELAUNCH_MANIFEST_PATH).write_text(
        json.dumps({"formal_run_plan_hash": plan_hash}),
        encoding="utf-8",
    )
    input_hashes = {
        relpath(tmp_path / path, tmp_path): sha256_or_na(tmp_path / path)
        for path in (
            CARRY_FORWARD_PATH,
            CANDIDATE_MANIFEST_PATH,
            STABILITY_MATRIX_PATH,
            FORMAL_RUN_PLAN_CSV_PATH,
            FORMAL_RUN_PLAN_JSON_PATH,
            FORMAL_PRELAUNCH_MANIFEST_PATH,
        )
    }
    freeze_path = tmp_path / "results/pre3seed_freeze_manifest_20260518.json"
    freeze_path.write_text(
        json.dumps(
            {
                "git_dirty_state": {"dirty": False},
                "postprocess_script_hash": analysis_script_hash(tmp_path),
                "candidate_carry_forward_manifest_hash": "wrong_hash",
                "input_file_hashes": input_hashes,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PreflightGateError, match="input hash mismatch"):
        validate_formal_execution_freeze(
            formal_plan_rows=plan,
            project_root=tmp_path,
            freeze_manifest_path=freeze_path,
            require_git_clean=False,
        )


def test_formal_execution_freeze_rejects_missing_launch_contract(tmp_path):
    required_paths = (
        CARRY_FORWARD_PATH,
        CANDIDATE_MANIFEST_PATH,
        STABILITY_MATRIX_PATH,
        FORMAL_RUN_PLAN_CSV_PATH,
        FORMAL_RUN_PLAN_JSON_PATH,
        FORMAL_PRELAUNCH_MANIFEST_PATH,
    )
    for path in required_paths:
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("placeholder\n", encoding="utf-8")
    plan = [{"candidate_family_id": "unit_family", "seed": 11}]
    plan_hash = sha256_payload(plan)
    (tmp_path / FORMAL_RUN_PLAN_JSON_PATH).write_text(
        json.dumps({"formal_run_plan_hash": plan_hash}),
        encoding="utf-8",
    )
    (tmp_path / FORMAL_PRELAUNCH_MANIFEST_PATH).write_text(
        json.dumps({"formal_run_plan_hash": plan_hash}),
        encoding="utf-8",
    )
    input_hashes = {
        relpath(tmp_path / path, tmp_path): sha256_or_na(tmp_path / path)
        for path in required_paths
    }
    freeze_path = tmp_path / "results/pre3seed_freeze_manifest_20260518.json"
    freeze_path.write_text(
        json.dumps(
            {
                "git_dirty_state": {"dirty": False},
                "postprocess_script_hash": analysis_script_hash(tmp_path),
                "candidate_carry_forward_manifest_hash": sha256_or_na(tmp_path / CARRY_FORWARD_PATH),
                "input_file_hashes": input_hashes,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PreflightGateError, match="lacks launch_authorization_contract"):
        validate_formal_execution_freeze(
            formal_plan_rows=plan,
            project_root=tmp_path,
            freeze_manifest_path=freeze_path,
            require_git_clean=False,
        )


def test_diagnostic_snapshot_json_safety_summarizes_large_sequences():
    payload = {
        "long_numeric": list(range(100)),
        "short_numeric": [1, 2, 3],
        "complex_value": 1 + 2j,
    }

    safe = _json_safe_diagnostic_value(payload)

    assert safe["long_numeric"]["sequence_summary_type"] == "numeric_sequence"
    assert safe["long_numeric"]["size"] == 100
    assert safe["long_numeric"]["max"] == 99.0
    assert safe["short_numeric"] == [1, 2, 3]
    assert safe["complex_value"]["complex_abs"] > 2.2


def test_formal_runner_refuses_execute_without_allow_large_run():
    completed = subprocess.run(
        [sys.executable, "tools/run_pre3seed_3seed_10000e_from_manifest.py", "--execute"],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    assert "--execute requires --allow-large-run" in completed.stderr + completed.stdout


def test_formal_runner_refuses_execute_without_p19_confirmation():
    completed = subprocess.run(
        [
            sys.executable,
            "tools/run_pre3seed_3seed_10000e_from_manifest.py",
            "--execute",
            "--allow-large-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    assert "--execute requires --confirm-p19-level1-launch" in completed.stderr + completed.stdout


def test_formal_runner_refuses_worker_count_scope_drift():
    completed = subprocess.run(
        [
            sys.executable,
            "tools/run_pre3seed_3seed_10000e_from_manifest.py",
            "--dry-run",
            "--workers",
            "15",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    assert "formal P19 full run requires --workers 16" in completed.stderr + completed.stdout
