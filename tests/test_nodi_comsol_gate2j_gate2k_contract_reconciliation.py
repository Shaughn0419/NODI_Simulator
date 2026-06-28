from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2j_gate2k_contract_reconciliation as gate2j


def _stage_inputs(tmp_path: Path, monkeypatch) -> Path:
    nodi = tmp_path / "nodi"
    reports = nodi / "reports"
    joint = reports / "joint_interface_20260628"
    joint.mkdir(parents=True)
    report207 = reports / "207.md"
    report208 = reports / "208.md"
    report207.write_text("Gate2H PASS no formula no JRC\n", encoding="utf-8")
    report208.write_text("Gate2I PASS no formula no JRC\n", encoding="utf-8")

    write_csv_rows(
        joint / "schema.csv",
        [
            {
                "schema_row_id": "S1",
                "field_or_section": "numeric_aggregation_error_bound",
                "required_type": "number",
                "acceptance_requirement": "finite bound",
                "requirement_level": "required",
            },
            {
                "schema_row_id": "S2",
                "field_or_section": "authorization_request_flags_default_false",
                "required_type": "boolean set",
                "acceptance_requirement": "all false",
                "requirement_level": "required",
            },
        ],
    )
    write_csv_rows(
        joint / "rules.csv",
        [
            {
                "decision_rule_id": "R1",
                "condition": "numeric_error_bounds_present",
                "rule_description": "missing numeric bound -> not approved",
                "decision": "NOT_APPROVED",
            },
            {
                "decision_rule_id": "R2",
                "condition": "all_authorization_flags_false_by_default",
                "rule_description": "flag true -> hard fail",
                "decision": "HARD_FAIL",
            },
        ],
    )
    write_csv_rows(joint / "checklist.csv", [{"check": "unit"}])
    write_csv_rows(
        joint / "negative.csv",
        [
            {"negative_fixture_id": "N1", "fixture_name": "missing_numeric_error_bound", "expected_validator_result": "NOT_APPROVED"},
            {"negative_fixture_id": "N2", "fixture_name": "formula_flag_true", "expected_validator_result": "HARD_FAIL"},
            {"negative_fixture_id": "N3", "fixture_name": "auto_map_220nm", "expected_validator_result": "HARD_FAIL"},
        ],
    )
    write_csv_rows(joint / "validation.csv", [{"validation_rule_id": "V1", "rule": "all_authorization_flags_false_by_default"}])
    write_csv_rows(joint / "non_edge.csv", [{"workstream": "QCH", "status": "FORMAL_SIDECAR_ABSENT_SCHEMA_READY_NO_WEIGHTING"}])
    write_csv_rows(
        joint / "qch_binding.csv",
        [
            {"dashboard_id": "D1", "workstream": "QCH", "status": "FORMAL_SIDECAR_ABSENT_SCHEMA_READY_NO_WEIGHTING"},
            {"dashboard_id": "D2", "workstream": "BINDING", "status": "220_D1200_UNBOUND_FAIL_CLOSED_NO_AUTO_MAP"},
        ],
    )
    write_csv_rows(joint / "gate2d.csv", [{"id": str(index)} for index in range(4)])

    monkeypatch.setattr(gate2j, "NODI_REPORT_207", report207)
    monkeypatch.setattr(gate2j, "NODI_REPORT_208", report208)
    monkeypatch.setattr(gate2j, "NODI_I_SCHEMA", joint / "schema.csv")
    monkeypatch.setattr(gate2j, "NODI_I_RULES", joint / "rules.csv")
    monkeypatch.setattr(gate2j, "NODI_I_CHECKLIST", joint / "checklist.csv")
    monkeypatch.setattr(gate2j, "NODI_I_NEGATIVE", joint / "negative.csv")
    monkeypatch.setattr(gate2j, "NODI_I_VALIDATION", joint / "validation.csv")
    monkeypatch.setattr(gate2j, "NODI_I_NON_EDGE", joint / "non_edge.csv")
    monkeypatch.setattr(gate2j, "NODI_I_QCH_BINDING", joint / "qch_binding.csv")
    monkeypatch.setattr(gate2j, "NODI_G2D_LEDGER", joint / "gate2d.csv")

    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    (comsol_root / gate2j.COMSOL_MASTER).write_text("master\n", encoding="utf-8")
    write_csv_rows(
        comsol_root / gate2j.COMSOL_EDGE_CONTRACT,
        [
            {"contract_field_id": "C1", "field_name": "numeric_error_value", "required_type": "number"},
            {"contract_field_id": "C2", "field_name": "error_bound_lower", "required_type": "number"},
            {"contract_field_id": "C3", "field_name": "error_bound_upper", "required_type": "number"},
            {"contract_field_id": "C4", "field_name": "policy_use_requested", "required_type": "boolean"},
        ],
    )
    write_csv_rows(comsol_root / gate2j.COMSOL_EDGE_GAP, [{"gap_id": "G1", "status": "OPEN"}])
    write_csv_rows(
        comsol_root / gate2j.COMSOL_CHECKS,
        [
            {"diagnostic_check_id": "C1", "check_name": "numeric_error_bounds_present", "check_definition": "numeric_error_bounds_present"},
            {"diagnostic_check_id": "C2", "check_name": "all_authorization_flags_false_by_default", "check_definition": "authorization flag hard fail"},
        ],
    )
    write_csv_rows(
        comsol_root / gate2j.COMSOL_TEMPLATE,
        [
            {
                "template_row_id": "T1",
                "template_only": "true",
                "is_formal_policy_evidence": "false",
                "route_key": "660/W800/D900",
                "NODI_view": "fixed_660_gold",
                "diameter_nm": "300",
                "edge20_definition_hash": gate2j.EXPECTED_EDGE20_HASH,
                "numeric_error_value": "",
                "error_bound_lower": "",
                "error_bound_upper": "",
                "policy_use_requested": "false",
                "formula_use_authorized": "false",
                "direct_prs_bin_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
            }
        ],
    )
    write_csv_rows(
        comsol_root / gate2j.COMSOL_NEGATIVE,
        [
            {"negative_fixture_id": "CN1", "failure_mode": "missing_numeric_error_bound", "field_or_rule_under_test": "numeric_error_value"},
            {"negative_fixture_id": "CN2", "failure_mode": "bad_formula_use_authorized", "field_or_rule_under_test": "formula_use_authorized"},
        ],
    )
    write_csv_rows(
        comsol_root / gate2j.COMSOL_POSITIVE_SCHEMA,
        [
            {"schema_field_id": "P1", "field_name": "numeric_error_value", "required_for_positive_fixture": "true"},
            {"schema_field_id": "P2", "field_name": "policy_use_requested", "required_for_positive_fixture": "true"},
        ],
    )
    write_csv_rows(comsol_root / gate2j.COMSOL_VALIDATION, [{"check_id": "VAL1", "status": "PASS"}])
    write_csv_rows(comsol_root / gate2j.COMSOL_NON_EDGE, [{"hook_id": "H1", "workstream": "QCH", "formula_use_authorized": "false"}])
    write_csv_rows(comsol_root / gate2j.COMSOL_PARALLEL, [{"parallel_hook_id": "P1", "workstream": "Gate2I-QCH", "qch_weighting_authorized": "false"}])
    manifest_rows = []
    for relative in (
        gate2j.COMSOL_EDGE_CONTRACT,
        gate2j.COMSOL_EDGE_GAP,
        gate2j.COMSOL_CHECKS,
        gate2j.COMSOL_TEMPLATE,
        gate2j.COMSOL_NEGATIVE,
        gate2j.COMSOL_POSITIVE_SCHEMA,
        gate2j.COMSOL_VALIDATION,
        gate2j.COMSOL_NON_EDGE,
        gate2j.COMSOL_PARALLEL,
    ):
        path = comsol_root / relative
        manifest_rows.append(
            {
                "artifact_id": relative.stem,
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "row_count": str(len(gate2j.read_csv_rows(path))),
                "allowed_use": "contract only",
                "blocked_use": "formula use",
                "claim_boundary": "template-only",
            }
        )
    write_csv_rows(comsol_root / gate2j.COMSOL_MANIFEST, manifest_rows)
    return comsol_root


def test_gate2j_gate2k_gate2l_gate2m_contract_package_passes(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2j.build_payload(comsol_root=comsol_root)

    assert payload["gate2j_disposition"] == gate2j.GATE2J_PASS
    assert payload["gate2k_disposition"] == gate2j.GATE2K_PASS
    assert payload["gate2l_qch_disposition"] == gate2j.GATE2L_QCH_PASS
    assert payload["gate2l_binding_disposition"] == gate2j.GATE2L_BINDING_PASS
    assert payload["gate2m_disposition"] == gate2j.GATE2M_PASS
    assert payload["gate2d_accepted_row_count"] == 4
    assert any(row["crosswalk_status"] in {"MATCH", "ADAPTER_REQUIRED"} for row in payload["field_crosswalk_rows"])
    assert all(row["harness_result"] == "PASS_EXPECTED_FAIL" for row in payload["edge_negative_fixture_result_rows"])
    assert all(row["harness_result"] == "PASS_EXPECTED_FAIL" for row in payload["qch_negative_fixture_rows"])
    assert all(row["harness_result"] == "PASS_EXPECTED_FAIL" for row in payload["binding_negative_fixture_rows"])
    assert gate2j.validate_payload(payload, comsol_root=comsol_root) == []


def test_gate2j_authorization_true_and_gate2d_expansion_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2j.build_payload(comsol_root=comsol_root)
    payload["edge_positive_schema_fixture_rows"][0]["formula_use_authorized"] = "true"
    assert any("forbidden authorization true" in issue for issue in gate2j.validate_payload(payload, comsol_root=comsol_root))

    payload = gate2j.build_payload(comsol_root=comsol_root)
    payload["gate2d_accepted_row_count"] = 5
    assert any("Gate2D accepted ledger" in issue for issue in gate2j.validate_payload(payload, comsol_root=comsol_root))


def test_gate2j_source_manifest_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    manifest_path = comsol_root / gate2j.COMSOL_MANIFEST
    rows = gate2j.read_csv_rows(manifest_path)
    rows[0]["sha256"] = "bad"
    write_csv_rows(manifest_path, rows)
    payload = gate2j.build_payload(comsol_root=comsol_root)
    assert any(row["manifest_match_status"] == "BLOCKED_MISMATCH" for row in payload["source_receipt_requirement_rows"])
    assert any("manifest mismatch" in issue for issue in gate2j.validate_payload(payload, comsol_root=comsol_root))
