from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2n_to_gate2r_roundtrip_freeze as gate2n


def _stage_inputs(tmp_path: Path, monkeypatch) -> Path:
    nodi = tmp_path / "nodi"
    joint = nodi / "reports" / "joint_interface_20260628"
    joint.mkdir(parents=True)
    write_csv_rows(joint / "gate2d.csv", [{"id": str(i)} for i in range(4)])
    write_csv_rows(joint / "j_field.csv", [{"crosswalk_status": "MATCH", "formula_use_authorized": "false"}])
    write_csv_rows(joint / "j_rule.csv", [{"crosswalk_status": "MATCH", "jrc_authorized": "false"}])
    write_csv_rows(joint / "j_fixture.csv", [{"fixture_name": "formula_flag_true"}])
    write_csv_rows(joint / "k_neg.csv", [{"fixture_name": "formula_flag_true", "harness_result": "PASS_EXPECTED_FAIL"}])
    write_csv_rows(joint / "qch_neg.csv", [{"fixture_name": "q_ch_eta_field_present", "harness_result": "PASS_EXPECTED_FAIL"}])
    write_csv_rows(joint / "binding_neg.csv", [{"fixture_name": "220_auto_map_true", "harness_result": "PASS_EXPECTED_FAIL"}])
    write_csv_rows(
        joint / "m_dash.csv",
        [
            {"workstream": "LOCAL_Q", "negative_fixture_count": "0"},
            {"workstream": "V4", "negative_fixture_count": "0"},
            {"workstream": "STRONG_CLAIMS", "negative_fixture_count": "0"},
        ],
    )
    monkeypatch.setattr(gate2n, "NODI_G2D_LEDGER", joint / "gate2d.csv")
    monkeypatch.setattr(gate2n, "NODI_J_FIELD", joint / "j_field.csv")
    monkeypatch.setattr(gate2n, "NODI_J_RULE", joint / "j_rule.csv")
    monkeypatch.setattr(gate2n, "NODI_J_FIXTURE", joint / "j_fixture.csv")
    monkeypatch.setattr(gate2n, "NODI_K_NEG", joint / "k_neg.csv")
    monkeypatch.setattr(gate2n, "NODI_L_QCH_NEG", joint / "qch_neg.csv")
    monkeypatch.setattr(gate2n, "NODI_L_BINDING_NEG", joint / "binding_neg.csv")
    monkeypatch.setattr(gate2n, "NODI_M_DASH", joint / "m_dash.csv")

    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    full = comsol_root / "full_chip" / "dwg_analysis"
    roadmap.mkdir(parents=True)
    full.mkdir(parents=True)
    (comsol_root / gate2n.COMSOL_MASTER).write_text("master\n", encoding="utf-8")
    (comsol_root / gate2n.COMSOL_VALIDATOR_ALL).write_text("print('ok')\n", encoding="utf-8")
    (comsol_root / gate2n.COMSOL_VALIDATOR_EDGE).write_text("print('ok')\n", encoding="utf-8")
    write_csv_rows(
        comsol_root / gate2n.COMSOL_VALIDATION,
        [{"check_id": f"V{i}", "status": "PASS" if i < 16 else "PASS_BLOCKED_AS_EXPECTED"} for i in range(1, 17)],
    )
    write_csv_rows(comsol_root / gate2n.COMSOL_EDGE_ASSIM, [{"status": "MATCH"}])
    write_csv_rows(comsol_root / gate2n.COMSOL_EDGE_CROSSWALK, [{"status": "MATCH"}])
    write_csv_rows(comsol_root / gate2n.COMSOL_EDGE_GAPS, [{"gap": "ADAPTER_REQUIRED"}])
    write_csv_rows(
        comsol_root / gate2n.COMSOL_EDGE_TEMPLATE,
        [
            {
                "gate2k_template_row_id": f"E{i:02d}",
                "schema_version": "2.0-template",
                "template_only": "true",
                "not_evidence": "true",
                "edge20_bin_id": f"edge_{i - 1:02d}",
                "edge20_definition_hash": gate2n.EXPECTED_EDGE20_HASH,
                "policy_use_requested": "false",
                "formula_use_authorized": "false",
                "direct_prs_bin_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
            }
            for i in range(1, 21)
        ],
    )
    write_csv_rows(comsol_root / gate2n.COMSOL_EDGE_POS, [{"result": "schema_only", "not_evidence": "true"}])
    write_csv_rows(
        comsol_root / gate2n.COMSOL_EDGE_NEG,
        [
            {
                "fixture_result_id": "EN1",
                "failure_mode": "formula_flag_true",
                "expected_result": "FAIL_EXPECTED_HARD_FAIL",
                "actual_result": "FAIL_EXPECTED_HARD_FAIL",
                "formula_use_authorized": "false",
            }
        ],
    )
    write_csv_rows(
        comsol_root / gate2n.COMSOL_QCH_TEMPLATE,
        [
            {
                "qch_template_row_id": "Q1",
                "template_only": "true",
                "not_evidence": "true",
                "is_formal_gate2_qch_sidecar": "false",
                "current_status": "NO_FORMAL_QCH_SIDECAR_PRESENT",
                "qch_weighting_authorized": "false",
                "qch_eta_authorized": "false",
                "qch_chi_eta_authorized": "false",
                "jrc_authorized": "false",
                "chi_selected_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
            }
        ],
    )
    write_csv_rows(
        comsol_root / gate2n.COMSOL_QCH_NEG,
        [{"qch_negative_fixture_id": "QN1", "failure_mode": "q_ch_eta_field_present", "expected_validator_result": "FAIL_EXPECTED_NOT_FORMAL_SIDECAR", "qch_weighting_authorized": "false"}],
    )
    write_csv_rows(
        comsol_root / gate2n.COMSOL_BINDING_TEMPLATE,
        [
            {
                "binding_template_row_id": "B1",
                "template_only": "true",
                "not_evidence": "true",
                "blocker_type": "220NM",
                "auto_map_authorized": "false",
                "accepted_context_authorized": "false",
                "formula_use_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
            }
        ],
    )
    write_csv_rows(
        comsol_root / gate2n.COMSOL_BINDING_NEG,
        [{"binding_negative_fixture_id": "BN1", "failure_mode": "220_auto_map_true", "expected_validator_result": "FAIL_EXPECTED_FAIL_CLOSED", "auto_map_authorized": "false"}],
    )
    write_csv_rows(
        comsol_root / gate2n.COMSOL_M_DASH,
        [
            {"workstream": "EDGE", "rows_prepared": "20"},
            {"workstream": "QCH", "rows_prepared": "1"},
            {"workstream": "BINDING", "rows_prepared": "1"},
        ],
    )
    write_csv_rows(comsol_root / gate2n.COMSOL_M_REQUESTS, [{"workstream": "EDGE", "requested_deliverable": "future evidence"}])
    write_csv_rows(comsol_root / gate2n.COMSOL_M_GUARD, [{"field": "formula_use_authorized", "formula_use_authorized": "false"}])
    manifest_rows = []
    for relative in (
        gate2n.COMSOL_VALIDATOR_ALL,
        gate2n.COMSOL_VALIDATOR_EDGE,
        gate2n.COMSOL_MASTER,
        gate2n.COMSOL_VALIDATION,
        gate2n.COMSOL_EDGE_ASSIM,
        gate2n.COMSOL_EDGE_CROSSWALK,
        gate2n.COMSOL_EDGE_GAPS,
        gate2n.COMSOL_EDGE_TEMPLATE,
        gate2n.COMSOL_EDGE_NEG,
        gate2n.COMSOL_EDGE_POS,
        gate2n.COMSOL_QCH_TEMPLATE,
        gate2n.COMSOL_QCH_NEG,
        gate2n.COMSOL_BINDING_TEMPLATE,
        gate2n.COMSOL_BINDING_NEG,
        gate2n.COMSOL_M_DASH,
        gate2n.COMSOL_M_REQUESTS,
        gate2n.COMSOL_M_GUARD,
    ):
        path = comsol_root / relative
        manifest_rows.append(
            {
                "artifact_id": relative.stem,
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "row_count": str(len(gate2n.read_csv_rows(path))) if path.suffix == ".csv" else "0",
            }
        )
    write_csv_rows(comsol_root / gate2n.COMSOL_MANIFEST, manifest_rows)
    return comsol_root


def test_gate2n_to_gate2r_passes_with_expected_blocked_validation(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2n.build_payload(comsol_root=comsol_root)

    assert payload["gate2n_disposition"] == gate2n.GATE2N_PASS
    assert payload["gate2o_disposition"] == gate2n.GATE2O_PASS
    assert payload["gate2p_disposition"] == gate2n.GATE2P_PASS
    assert payload["gate2q_disposition"] == gate2n.GATE2Q_PASS
    assert payload["gate2r_disposition"] == gate2n.GATE2R_PASS
    assert payload["gate2d_accepted_row_count"] == 4
    assert payload["edge_template_v2_row_count"] == 20
    assert all(row["receiver_dry_run_status"].endswith("NOT_EVIDENCE") for row in payload["qch_dry_run_rows"])
    assert all(row["concordance_status"] == "PASS_EXPECTED_FAIL" for row in payload["negative_concordance_rows"])
    assert gate2n.validate_payload(payload, comsol_root=comsol_root) == []


def test_gate2n_to_gate2r_hard_fails_authorization_and_ledger_expansion(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2n.build_payload(comsol_root=comsol_root)
    payload["edge_dry_run_rows"][0]["formula_use_authorized"] = "true"
    payload["r_auth_sweep_rows"] = gate2n.build_auth_sweep([payload["edge_dry_run_rows"]])
    assert any("authorization sweep failed" in issue for issue in gate2n.validate_payload(payload, comsol_root=comsol_root))

    payload = gate2n.build_payload(comsol_root=comsol_root)
    payload["gate2d_accepted_row_count"] = 5
    assert any("Gate2D accepted ledger" in issue for issue in gate2n.validate_payload(payload, comsol_root=comsol_root))


def test_gate2n_manifest_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    manifest_path = comsol_root / gate2n.COMSOL_MANIFEST
    rows = gate2n.read_csv_rows(manifest_path)
    rows[0]["sha256"] = "bad"
    write_csv_rows(manifest_path, rows)
    payload = gate2n.build_payload(comsol_root=comsol_root)
    assert any(row["reconciliation_status"] == "BLOCKING_MISMATCH" for row in payload["manifest_reconciliation_rows"])
    assert any("manifest mismatch" in issue for issue in gate2n.validate_payload(payload, comsol_root=comsol_root))
