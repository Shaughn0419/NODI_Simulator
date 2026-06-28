from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2e_receiver_policy_verdicts as gate2e


def _write_prs(path: Path) -> str:
    rows = [
        {
            "row_scope": "response_surface_bin",
            "distribution_type": "edge_norm_1d",
            "row_kind": "base_bin",
            "bin_id": f"edge_{index:02d}",
            "edge_norm_min": f"{index / 20:.2f}".rstrip("0").rstrip(".") if index else "0",
            "edge_norm_max": f"{(index + 1) / 20:.2f}".rstrip("0").rstrip("."),
        }
        for index in range(20)
    ]
    write_csv_rows(path, rows)
    return sha256_file(path)


def _stage_inputs(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path]:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    csv_payloads = {
        "COMSOL_GATE2E_EXPANSION_WORKSTREAM_INDEX_20260628.csv": [
            {"workstream_id": "Gate2E-EDGE"},
            {"workstream_id": "Gate2E-QCH"},
            {"workstream_id": "Gate2E-BINDING"},
        ],
        "COMSOL_GATE2E_EDGE4_EDGE20_POLICY_EVIDENCE_REQUIREMENTS_20260628.csv": [
            {"requirement_id": "EDGE-REQ-001", "requirement_area": "definition"},
            {"requirement_id": "EDGE-REQ-002", "requirement_area": "loss"},
        ],
        "COMSOL_GATE2E_QCH_FORMAL_SIDECAR_RECEIPT_REQUIREMENTS_20260628.csv": [
            {
                "requirement_id": "QCH-REQ-001",
                "requirement_area": "identity",
                "receipt_field": "route_key",
                "current_gap": "missing formal sidecar",
                "needed_from_comsol": "formal route_key",
            },
            {
                "requirement_id": "QCH-REQ-002",
                "requirement_area": "value",
                "receipt_field": "q_ch_value",
                "current_gap": "provenance only",
                "needed_from_comsol": "formal q_ch units",
            },
        ],
        "COMSOL_GATE2E_TPD_BINDING_REPAIR_REQUIREMENTS_20260628.csv": [
            {"requirement_id": "BIND-REQ-001", "binding_blocker": "220 nm", "affected_rows": "72"},
            {"requirement_id": "BIND-REQ-002", "binding_blocker": "D1200 exact grain", "affected_rows": "36"},
            {"requirement_id": "BIND-REQ-003", "binding_blocker": "UNBOUND NODI_view", "affected_rows": "16"},
        ],
        "COMSOL_GATE2E_EXPANSION_WORKSTREAM_VALIDATION_20260628.csv": [{"check_id": "VAL-001", "status": "PASS"}],
        "COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv": [{"row_id": str(index)} for index in range(92)],
    }
    md_payloads = {
        "COMSOL_GATE2E_EXPANSION_WORKSTREAM_MASTER_PLAN_20260628.md": "PASS_GATE2E_EXPANSION_WORKSTREAM_PLANNING_READY_NO_AUTHORIZATION\n",
        "COMSOL_GATE2E_EDGE4_EDGE20_POLICY_REVIEW_PACKET_20260628.md": "edge packet\n",
        "COMSOL_GATE2E_QCH_FORMAL_SIDECAR_PREFLIGHT_PACKET_20260628.md": "qch packet\n",
        "COMSOL_GATE2E_TPD_BINDING_REPAIR_PACKET_20260628.md": "binding packet\n",
    }
    for name, rows in csv_payloads.items():
        write_csv_rows(roadmap / name, rows)
    for name, text in md_payloads.items():
        (roadmap / name).write_text(text, encoding="utf-8")
    manifest_rows = []
    for _evidence_id, role, relative in gate2e.COMSOL_GATE2E_FILES:
        if relative.name == "COMSOL_GATE2E_EXPANSION_WORKSTREAM_MANIFEST_20260628.csv":
            continue
        path = comsol_root / relative
        manifest_rows.append(
            {
                "package_id": relative.stem,
                "manifest_role": role,
                "path": relative.as_posix(),
                "row_count": str(len(gate2e.read_csv_rows(path))) if path.suffix == ".csv" else "0",
                "sha256": sha256_file(path),
                "status": "PASS",
                "notes": "unit",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2E_EXPANSION_WORKSTREAM_MANIFEST_20260628.csv", manifest_rows)

    nodi = tmp_path / "nodi"
    nodi.mkdir()
    accepted_ledger = nodi / "accepted.csv"
    write_csv_rows(
        accepted_ledger,
        [
            {
                "nodi_gate2d_acceptance_id": f"NODI-G2D-ACCEPT-{index:03d}",
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
            }
            for index in range(1, 5)
        ],
    )
    blockers = nodi / "blockers.csv"
    write_csv_rows(blockers, [{"blocker": "220 nm"}, {"blocker": "D1200"}, {"blocker": "UNBOUND"}])
    edge = nodi / "edge.csv"
    write_csv_rows(
        edge,
        [
            {"check_id": "EDGE-POL-001", "gate2c_policy_status": "PASS_REVIEW_FRAMEWORK"},
            {"check_id": "EDGE-POL-004", "gate2c_policy_status": "NOT_APPROVED"},
        ],
    )
    qch = nodi / "qch.csv"
    write_csv_rows(
        qch,
        [
            {
                "source_requirement_id": "QCH-REQ-001",
                "field_name": "route_key",
                "current_status": "GAP_PRESENT",
                "blocked_use": "q_ch weighting; JRC",
            },
            {
                "source_requirement_id": "QCH-REQ-002",
                "field_name": "q_ch_value",
                "current_status": "GAP_PRESENT",
                "blocked_use": "q_ch*eta; route_score",
            },
        ],
    )
    prs_verdict = nodi / "prs_verdict.csv"
    write_csv_rows(
        prs_verdict,
        [
            {"coverage_verdict": "BLOCKED_220NM_NO_DIRECT_PRS_MATCH"},
            {"coverage_verdict": "BLOCKED_D1200_DIAMETER_VIEW_GRAIN_ABSENT"},
        ],
    )
    report203 = nodi / "report203.md"
    report203.write_text("PASS_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER_NO_WEIGHTING_NO_JRC\n", encoding="utf-8")
    prs = nodi / "prs.csv"
    prs_sha = _write_prs(prs)

    monkeypatch.setattr(gate2e, "NODI_GATE2D_ACCEPTED_LEDGER", accepted_ledger)
    monkeypatch.setattr(gate2e, "NODI_GATE2D_BLOCKERS", blockers)
    monkeypatch.setattr(gate2e, "NODI_GATE2C_EDGE_CHECKLIST", edge)
    monkeypatch.setattr(gate2e, "NODI_GATE2C_QCH_CHECKLIST", qch)
    monkeypatch.setattr(gate2e, "NODI_GATE2C_PRS_VERDICT", prs_verdict)
    monkeypatch.setattr(gate2e, "NODI_REPORT_203", report203)
    monkeypatch.setattr(gate2e, "EXPECTED_PRS_SHA", prs_sha)
    return comsol_root, prs, tmp_path / "out"


def test_gate2e_receiver_policy_pass_keeps_gate2d_frozen(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2e.build_gate2e_payload(comsol_root=comsol_root, prs_artifact_path=prs)

    assert payload["status"] == gate2e.PASS_STATUS
    assert payload["gate2d_accepted_row_count"] == 4
    assert len(payload["edge20_definition_snapshot_rows"]) == 20
    assert all(row["accepted_row_expansion_authorized"] == "false" for row in payload["receiver_dashboard_rows"])
    assert gate2e.validate_gate2e_payload(payload, comsol_root=comsol_root, prs_artifact_path=prs) == []


def test_gate2e_edge_qch_binding_flags_fail_closed(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2e.build_gate2e_payload(comsol_root=comsol_root, prs_artifact_path=prs)

    assert all(row["direct_prs_bin_use_authorized"] == "false" for row in payload["edge_receiver_policy_verdict_rows"])
    assert all(row["formula_use_authorized"] == "false" for row in payload["edge_receiver_policy_verdict_rows"])
    assert payload["qch_receipt_schema_verdict_rows"][0]["formal_sidecar_present"] == "false"
    assert payload["qch_receipt_schema_verdict_rows"][0]["qch_weighting_authorized"] == "false"
    binding_statuses = {row["receiver_verdict"] for row in payload["binding_policy_verdict_rows"]}
    assert "BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP" in binding_statuses
    assert "BLOCKED_D1200_EXACT_GRAIN_ABSENT_OR_UNCERTAIN" in binding_statuses
    assert "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED" in binding_statuses


def test_gate2e_forbidden_fields_and_prs_hash_drift_hard_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2e.build_gate2e_payload(comsol_root=comsol_root, prs_artifact_path=prs)

    bad_edge = dict(payload)
    bad_edge["edge_receiver_policy_verdict_rows"] = [
        dict(payload["edge_receiver_policy_verdict_rows"][0], formula_use_authorized="true")
    ]
    assert any("formula_use_authorized" in issue for issue in gate2e.validate_gate2e_payload(bad_edge, comsol_root=comsol_root, prs_artifact_path=prs))

    bad_prs = dict(payload)
    bad_prs["nodi_prs_sha256"] = "bad"
    assert any("PRS hash drift" in issue for issue in gate2e.validate_gate2e_payload(bad_prs, comsol_root=comsol_root, prs_artifact_path=prs))


def test_gate2e_cli_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    comsol_root, prs, out = _stage_inputs(tmp_path, monkeypatch)
    report_dir = tmp_path / "reports"
    result = gate2e.main(
        [
            "--confirm-gate2e-receiver-policy-verdicts",
            "--comsol-root",
            str(comsol_root),
            "--prs-artifact",
            str(prs),
            "--output-dir",
            str(out),
            "--report-dir",
            str(report_dir),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert gate2e.PASS_STATUS in captured.out
    assert (out / gate2e.DASHBOARD).exists()
    assert (out / gate2e.EDGE_VERDICT).exists()
    assert (report_dir / gate2e.REPORT_204).exists()
