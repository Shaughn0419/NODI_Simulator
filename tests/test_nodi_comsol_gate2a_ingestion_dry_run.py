from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import write_csv_rows
from tools.audits.build_nodi_comsol_gate2a_ingestion_dry_run import (
    PASS_STATUS,
    STATUS_BLOCKED_GRAIN,
    STATUS_BLOCKED_QCH,
    STATUS_CONTEXT_CANDIDATE,
    build_gate2a_payload,
    main,
    reconcile_status,
    validate_gate2a_payload,
    validate_grain_rows,
    validate_reconciliation_rows,
)


def _nodi_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "register_row_id": "G2CTX-CHI-BIN-005",
        "candidate_type": "TPD/PRS context proxy candidate",
        "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
        "sha256": "a" * 64,
        "row_count": "1",
        "candidate_status": "GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH",
        "route_key": "660/W800/D900",
        "diameter_basis": "220;300",
        "bin_basis": "TPD_edge4_to_PRS_edge20_group_context",
        "matched_grain_count": "1",
        "blocked_grain_count": "1",
        "allowed_use": "Gate2 context proxy review only",
        "blocked_use": "q_ch*eta; JRC; yield; winner; detection_probability",
        "claim_boundary": "context_proxy_not_chi_selected_not_detection",
        "required_next_gate": "explicit coarse-to-fine review",
        "review_note": "unit row",
    }
    row.update(overrides)
    return row


def _index_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "artifact_id": "TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622",
        "path": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
        "sha256": "a" * 64,
        "row_count": "1",
        "readiness_status": "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY",
        "allowed_use": "context proxy review only",
        "blocked_use": "chi_selected; q_ch*eta; detection_probability; yield; winner; JRC",
        "claim_boundary": "context_proxy_not_chi_selected_not_detection",
        "blocker_if_any": "BLOCKED_NOT_WEIGHTING_AUTHORIZED",
    }
    row.update(overrides)
    return row


def _gate_row(gate_id: str, gate_status: str) -> dict[str, str]:
    return {
        "gate_id": gate_id,
        "gate_status": gate_status,
        "evidence": "unit",
        "allowed": "context review",
        "blocked": "weighting; JRC; yield; winner",
        "next_action": "unit",
    }


def _minimal_payload(tmp_path: Path, nodi_rows: list[dict[str, object]], index_rows: list[dict[str, object]]) -> dict[str, object]:
    comsol_root = tmp_path / "comsol"
    (comsol_root / "roadmap").mkdir(parents=True)
    source = comsol_root / "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv"
    write_csv_rows(
        source,
        [
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "220",
                "NODI_view": "fixed_660_gold",
                "prs_bin_count": "5",
            },
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
                "prs_bin_count": "5",
            },
        ],
    )
    packet = comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_PACKET_20260627.md"
    packet.write_text("packet\n", encoding="utf-8")
    for name in (
        "COMSOL_GATE2_NODI_CONTEXT_EXPORT_INDEX_20260627.csv",
        "COMSOL_GATE2_NODI_CONTEXT_EXPORT_GATES_20260627.csv",
        "COMSOL_GATE2_NODI_CONTEXT_EXPORT_VALIDATION_20260627.csv",
        "COMSOL_GATE2_NODI_CONTEXT_EXPORT_MANIFEST_20260627.csv",
    ):
        write_csv_rows(comsol_root / "roadmap" / name, [{"unit": "row"}])

    return build_gate2a_payload(
        nodi_register_rows=nodi_rows,
        nodi_blocked_rows=[
            {
                "register_row_id": "G2CTX-CHI-BIN-005",
                "route_key": "660/W800/D900",
                "diameter_nm": "220",
                "NODI_view": "fixed_660_gold",
                "bin_basis": "prs_edge20_group_count_5",
                "alignment_status": "BLOCKED_MISSING_PRS_ROUTE_DIAMETER_VIEW_GRAIN",
                "reason": "220 nm must remain blocked",
            }
        ],
        nodi_schema_rows=[{"field": "source_artifact"}],
        comsol_index_rows=index_rows,
        comsol_gate_rows=[
            _gate_row("G2-CHI-PROXY", "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY"),
            _gate_row("G2-WEIGHTING-AUTHORIZATION", "BLOCKED_NOT_WEIGHTING_AUTHORIZED"),
            _gate_row("G2-JRC-STRONG-CLAIMS", "BLOCKED_STRONG_CLAIMS_FORBIDDEN"),
        ],
        comsol_validation_rows=[{"check_id": "VAL-001", "status": "PASS"}],
        comsol_manifest_rows=[{"package_id": "unit"}],
        prs_rows=[
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
            }
        ],
        eas_rows=[
            {
                "route_id_nodi": "660/W800/D900",
                "NODI_view": "fixed_660_gold",
            }
        ],
        comsol_root=comsol_root,
        source_paths={
            "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv": source,
        },
    )


def test_ready_for_review_context_only_is_not_production_ready() -> None:
    status = reconcile_status(
        _nodi_row(candidate_status="BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH"),
        "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY",
    )

    assert status == STATUS_BLOCKED_GRAIN
    assert "PRODUCTION" not in status


def test_220_nm_and_edge4_are_not_auto_mapped(tmp_path: Path) -> None:
    payload = _minimal_payload(tmp_path, [_nodi_row()], [_index_row()])

    grain_rows = payload["grain_compatibility_rows"]
    row_220 = [row for row in grain_rows if row["diameter_nm"] == "220"][0]
    row_300 = [row for row in grain_rows if row["diameter_nm"] == "300"][0]

    assert row_220["grain_reconciled_status"] == STATUS_BLOCKED_GRAIN
    assert row_220["prs_grain_present"] == "false"
    assert row_300["direct_prs_bin_compatible"] == "false"
    assert row_300["grain_reconciled_status"] != STATUS_CONTEXT_CANDIDATE
    assert validate_gate2a_payload(payload) == []


def test_qch_missing_reconciles_to_hard_block() -> None:
    row = _nodi_row(
        register_row_id="G2CTX-QCH-MISSING-003",
        candidate_type="q_ch / flow split candidate",
        source_artifact="UNAVAILABLE_FORMAL_QCH_FLOW_SPLIT_SIDECAR",
        candidate_status="BLOCKED_MISSING_FORMAL_GATE2_EXPORT",
    )

    assert reconcile_status(row, "BLOCKED_NOT_QCH_SIDECAR") == STATUS_BLOCKED_QCH


def test_forbidden_positive_fields_hard_fail() -> None:
    issues = validate_reconciliation_rows(
        [
            {
                "comsol_status": "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY",
                "reconciled_status": STATUS_CONTEXT_CANDIDATE,
                "allowed_use": "context review only",
                "can_enter_context_only_ingestion": "true",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "q_ch_eta_weighted_response": "0.1",
                "winner": "route-a",
                "detection_probability": "0.2",
                "JOINT_ROUTE_CLASS": "JRC-001",
            }
        ]
    )

    assert any("q_ch_eta_weighted_response" in issue for issue in issues)
    assert any("winner" in issue for issue in issues)
    assert any("detection_probability" in issue for issue in issues)
    assert any("JOINT_ROUTE_CLASS" in issue for issue in issues)


def test_v4_runtime_promotion_hard_fails() -> None:
    issues = validate_grain_rows(
        [
            {
                "nodi_register_row_id": "G2CTX-V4-SIDECAR-010",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "diameter_nm": "not_diameter_binned",
                "bin_basis": "not_position_binned",
                "direct_prs_bin_compatible": "false",
                "nodi_runtime_configuration_allowed": "true",
            }
        ]
    )

    assert any("V4/runtime production promotion" in issue for issue in issues)


def test_gate2a_main_writes_pass_disposition(tmp_path: Path, capsys) -> None:
    comsol_root = tmp_path / "comsol"
    nodi_root = tmp_path / "nodi"
    output_dir = nodi_root / "reports"
    (comsol_root / "roadmap").mkdir(parents=True)
    (nodi_root / "reports").mkdir(parents=True)
    packet = comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_PACKET_20260627.md"
    packet.write_text("packet\n", encoding="utf-8")
    source = comsol_root / "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv"
    write_csv_rows(
        source,
        [
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
                "prs_bin_count": "5",
            }
        ],
    )
    index = comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_INDEX_20260627.csv"
    write_csv_rows(index, [_index_row(row_count="1")])
    write_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_GATES_20260627.csv",
        [
            _gate_row("G2-CHI-PROXY", "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY"),
            _gate_row("G2-WEIGHTING-AUTHORIZATION", "BLOCKED_NOT_WEIGHTING_AUTHORIZED"),
            _gate_row("G2-JRC-STRONG-CLAIMS", "BLOCKED_STRONG_CLAIMS_FORBIDDEN"),
        ],
    )
    write_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_VALIDATION_20260627.csv",
        [{"check_id": "VAL-001", "status": "PASS"}],
    )
    write_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_MANIFEST_20260627.csv",
        [{"package_id": "unit", "path": "packet"}],
    )
    nodi_register = nodi_root / "register.csv"
    write_csv_rows(nodi_register, [_nodi_row(diameter_basis="300", matched_grain_count="1", blocked_grain_count="0")])
    nodi_blocked = nodi_root / "blocked.csv"
    write_csv_rows(
        nodi_blocked,
        [
            {
                "register_row_id": "G2CTX-CHI-BIN-005",
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
                "bin_basis": "prs_edge20_group_count_5",
                "alignment_status": "REVIEW_ONLY_COARSE_TO_FINE_BIN_GROUP_NOT_DIRECT_PRS_BIN",
                "reason": "edge4 review only",
            }
        ],
    )
    nodi_schema = nodi_root / "schema.csv"
    write_csv_rows(nodi_schema, [{"field": "source_artifact"}])
    prs = nodi_root / "prs.csv"
    eas = nodi_root / "eas.csv"
    write_csv_rows(prs, [{"route_id_nodi": "660/W800/D900", "diameter_nm": "300", "NODI_view": "fixed_660_gold"}])
    write_csv_rows(eas, [{"route_id_nodi": "660/W800/D900", "NODI_view": "fixed_660_gold"}])

    exit_code = main(
        [
            "--confirm-gate2a-dry-run",
            "--comsol-root",
            str(comsol_root),
            "--nodi-register",
            str(nodi_register),
            "--nodi-blocked-register",
            str(nodi_blocked),
            "--nodi-register-schema",
            str(nodi_schema),
            "--prs",
            str(prs),
            "--eas",
            str(eas),
            "--output-dir",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert PASS_STATUS in captured.out
    assert (output_dir / "NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.json").exists()
