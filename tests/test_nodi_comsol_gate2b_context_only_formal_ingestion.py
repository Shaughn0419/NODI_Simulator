from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import write_csv_rows
from tools.audits.build_nodi_comsol_gate2b_context_only_formal_ingestion import (
    ALLOWED_FORMAL_REGISTER_ROWS,
    PASS_STATUS,
    QCH_ROW,
    build_gate2b_payload,
    main,
    validate_gate2b_payload,
)


def _matrix_row(register_id: str, **overrides: object) -> dict[str, object]:
    base = {
        "nodi_register_row_id": register_id,
        "comsol_gate_id": "G2-CHI-PROXY",
        "comsol_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
        "comsol_status": "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY",
        "comsol_source_review_status": "COMSOL_READY_SOURCE_REVIEW_ONLY",
        "nodi_preflight_status": "GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH",
        "reconciled_status": "NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE",
        "route_key": "660/W800/D1200;660/W800/D900",
        "NODI_view": "fixed_660_gold;per_wavelength_gold",
        "diameter_nm": "220;300",
        "bin_basis": "not_position_binned",
        "matched_prs_grain_count": "2",
        "blocked_grain_count": "6",
        "allowed_use": "context proxy review only",
        "blocked_use": "chi_selected; q_ch*eta; JRC; yield; winner; detection_probability",
        "claim_boundary": "context_proxy_not_chi_selected_not_detection",
        "required_next_gate": "context-only review with blocked grains preserved",
        "blocker_reason": "context-only candidate",
        "can_enter_context_only_ingestion": "true",
        "can_enter_weighting": "false",
        "can_enter_jrc": "false",
    }
    base.update(overrides)
    return base


def _all_matrix_rows() -> list[dict[str, object]]:
    rows = [
        _matrix_row(
            "G2CTX-TPD-SOURCE-001",
            comsol_gate_id="G2-TPD-SOURCE-CONTEXT",
            comsol_artifact="roadmap/TRANSPORTED_POSITION_SOURCE_SMOKE_COMBINED_RETRY3_20260621.csv",
            reconciled_status="NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH",
            can_enter_context_only_ingestion="false",
            NODI_view="UNBOUND",
        ),
        _matrix_row(
            "G2CTX-TPD-ALIGN-002",
            comsol_gate_id="G2-TPD-PRS-ALIGNMENT",
            comsol_artifact="roadmap/TPD_TO_NODI_BRIDGE_ALIGNMENT_TABLE_20260621.csv",
            reconciled_status="NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH",
            can_enter_context_only_ingestion="false",
            NODI_view="UNBOUND",
        ),
        _matrix_row(
            QCH_ROW,
            comsol_gate_id="G2-QCH-SIDECAR",
            comsol_artifact="roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv",
            reconciled_status="NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT",
            can_enter_context_only_ingestion="false",
        ),
        _matrix_row("G2CTX-CHI-AGG-004"),
        _matrix_row(
            "G2CTX-CHI-BIN-005",
            comsol_artifact="roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
            bin_basis="TPD_edge4_to_PRS_edge20_group_context",
            blocked_grain_count="14",
        ),
        _matrix_row(
            "G2CTX-LQ-ANCHOR-006",
            comsol_gate_id="G2-LOCAL-Q-HYDRAULIC",
            comsol_artifact="roadmap/EV_PBS_ENTRANCE_LOCAL_Q_EFFECTIVE_APERTURE_LOCAL_Q_EVENT_TREE_BRIDGE_INPUT_20260623.csv",
            reconciled_status="NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT",
            can_enter_context_only_ingestion="false",
        ),
        _matrix_row(
            "G2CTX-LQ-SCREEN-007",
            comsol_gate_id="G2-LOCAL-Q-HYDRAULIC",
            comsol_artifact="roadmap/EV_PBS_LOCAL_Q_EVENT_TREE_BRIDGE_SCREENING_RESULTS_20260623.csv",
            reconciled_status="NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT",
            can_enter_context_only_ingestion="false",
        ),
        _matrix_row(
            "G2CTX-LQ-BRANCH-008",
            comsol_gate_id="G2-LOCAL-Q-HYDRAULIC",
            comsol_artifact="roadmap/EV_PBS_LOCAL_Q_BRANCH_ENVELOPE_REVIEW_GATE_BRANCH_DECISIONS_20260624.csv",
            reconciled_status="NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT",
            can_enter_context_only_ingestion="false",
        ),
        _matrix_row(
            "G2CTX-V4-CONTRACT-009",
            comsol_gate_id="G2-V4-NODI-REVIEW",
            comsol_artifact="roadmap/EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json",
            reconciled_status="NODI_RECONCILED_V4_REVIEW_ONLY",
            can_enter_context_only_ingestion="false",
        ),
        _matrix_row(
            "G2CTX-V4-SIDECAR-010",
            comsol_gate_id="G2-V4-NODI-REVIEW",
            comsol_artifact="roadmap/EV_PBS_V4_NON_NANO_NODI_REVIEW_CONTEXT_SIDECAR_ROWS_20260627.csv",
            reconciled_status="NODI_RECONCILED_V4_REVIEW_ONLY",
            can_enter_context_only_ingestion="false",
        ),
    ]
    return rows


def _grain_rows() -> list[dict[str, object]]:
    return [
        {
            "nodi_register_row_id": "G2CTX-CHI-AGG-004",
            "comsol_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
            "route_key": "660/W800/D900",
            "NODI_view": "fixed_660_gold",
            "diameter_nm": "300",
            "bin_basis": "not_position_binned",
            "prs_grain_present": "true",
            "eas_route_view_present": "true",
            "direct_prs_bin_compatible": "true",
            "grain_reconciled_status": "NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE",
            "blocker_reason": "exact context proxy grain matches current PRS/EAS",
            "can_enter_context_only_ingestion": "true",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
        },
        {
            "nodi_register_row_id": "G2CTX-CHI-BIN-005",
            "comsol_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
            "route_key": "660/W800/D900",
            "NODI_view": "fixed_660_gold",
            "diameter_nm": "300",
            "bin_basis": "prs_edge20_group_count_5",
            "prs_grain_present": "true",
            "eas_route_view_present": "true",
            "direct_prs_bin_compatible": "false",
            "grain_reconciled_status": "NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT",
            "blocker_reason": "edge4/edge20 grouped bin is review-only, not direct PRS bin",
            "can_enter_context_only_ingestion": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
        },
        {
            "nodi_register_row_id": "G2CTX-CHI-AGG-004",
            "comsol_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
            "route_key": "660/W800/D900",
            "NODI_view": "fixed_660_gold",
            "diameter_nm": "220",
            "bin_basis": "not_position_binned",
            "prs_grain_present": "false",
            "eas_route_view_present": "true",
            "direct_prs_bin_compatible": "true",
            "grain_reconciled_status": "NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH",
            "blocker_reason": "220 nm COMSOL context has no current NODI PRS production diameter grain",
            "can_enter_context_only_ingestion": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
        },
    ]


def _crosswalk_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path, count, sha in (
        ("roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv", "16", "a" * 64),
        ("roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv", "64", "b" * 64),
    ):
        rows.append(
            {
                "comsol_artifact_id": f"artifact_{count}",
                "comsol_artifact_path": path,
                "sha256": sha,
                "row_count": count,
                "comsol_gate_id": "G2-CHI-PROXY",
                "recommended_nodi_reconciled_status": "GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH",
            }
        )
    return rows


def _payload() -> dict[str, object]:
    source_hashes = {
        "roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv": "c" * 64,
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv": "d" * 64,
    }
    source_counts = {
        "roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv": "92",
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv": "10",
    }
    return build_gate2b_payload(
        gate2a_matrix_rows=_all_matrix_rows(),
        gate2a_grain_rows=_grain_rows(),
        gate2a_blocker_rows=[
            {
                "nodi_register_row_id": "*",
                "comsol_gate_id": "G2-JRC-STRONG-CLAIMS",
                "blocker_status": "NODI_RECONCILED_BLOCKED_STRONG_CLAIMS",
                "blocker_reason": "JOINT_ROUTE_CLASS, yield, winner, detection_probability",
                "required_next_gate": "future explicit authorization",
            }
        ],
        comsol_crosswalk_rows=_crosswalk_rows(),
        comsol_blocker_rows=[{"blocker_id": "G2A-BLOCK-001"}],
        qch_provenance_rows=[
            {
                "provenance_row_id": "QCHPROV-0001",
                "is_formal_gate2_qch_sidecar": "false",
                "qch_weighting_authorized": "false",
                "qch_eta_authorized": "false",
                "qch_chi_eta_authorized": "false",
                "recommended_nodi_reconciled_status": "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR",
            }
        ],
        comsol_validation_rows=[{"check_id": "G2A-VAL-001", "status": "PASS"}],
        comsol_manifest_rows=[{"manifest_role": "gate2a_crosswalk"}],
        source_hashes=source_hashes,
        source_row_counts=source_counts,
    )


def test_only_tpd_prs_proxy_context_enters_formal_ingestion() -> None:
    payload = _payload()

    assert payload["status"] == PASS_STATUS
    assert {row["nodi_register_row_id"] for row in payload["formal_register_rows"]} == set(ALLOWED_FORMAL_REGISTER_ROWS)
    assert {row["nodi_register_row_id"] for row in payload["ingested_context_rows"]} == set(ALLOWED_FORMAL_REGISTER_ROWS)
    assert all(row["context_only_formal_ingestion_allowed"] == "true" for row in payload["ingested_context_rows"])
    assert validate_gate2b_payload(payload) == []


def test_qch_provenance_only_does_not_become_sidecar() -> None:
    payload = _payload()
    qch_rows = [row for row in payload["quarantine_review_only_rows"] if row["nodi_register_row_id"] == QCH_ROW]

    assert len(qch_rows) == 1
    assert qch_rows[0]["qch_sidecar_status"] == "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR"
    assert qch_rows[0]["context_only_formal_ingestion_allowed"] == "false"


def test_source_ready_tpd_rows_do_not_enter_formal_ingestion() -> None:
    payload = _payload()
    ingested_ids = {row["nodi_register_row_id"] for row in payload["ingested_context_rows"]}

    assert "G2CTX-TPD-SOURCE-001" not in ingested_ids
    assert "G2CTX-TPD-ALIGN-002" not in ingested_ids


def test_220_nm_and_edge4_dispositions_are_preserved() -> None:
    payload = _payload()
    blocked_rows = payload["blocked_grain_disposition_rows"]

    row_220 = [row for row in blocked_rows if row["diameter_nm"] == "220"][0]
    edge_row = [row for row in blocked_rows if "edge20_group" in row["bin_basis"]][0]
    assert row_220["gate2b_grain_disposition"] == "blocked_or_review_only_preserved"
    assert edge_row["direct_prs_bin_compatible"] == "false"
    assert edge_row["gate2b_grain_disposition"] == "blocked_or_review_only_preserved"


def test_forbidden_fields_and_v4_promotion_hard_fail() -> None:
    payload = _payload()
    payload["ingested_context_rows"][0]["can_enter_weighting"] = "true"
    payload["quarantine_review_only_rows"][0]["nodi_runtime_configuration_allowed"] = "true"

    issues = validate_gate2b_payload(payload)
    assert any("weighting allowed" in issue or "can_enter_weighting" in issue for issue in issues)
    assert any("nodi_runtime_configuration_allowed" in issue for issue in issues)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    write_csv_rows(path, rows)


def test_gate2b_main_writes_pass_disposition(tmp_path: Path, capsys) -> None:
    nodi = tmp_path / "nodi"
    comsol = tmp_path / "comsol"
    output = nodi / "joint"
    report_dir = nodi / "reports"
    roadmap = comsol / "roadmap"
    roadmap.mkdir(parents=True)
    report_dir.mkdir(parents=True)

    matrix = nodi / "matrix.csv"
    grain = nodi / "grain.csv"
    blockers = nodi / "blockers.csv"
    report = nodi / "report.json"
    report.write_text("{}", encoding="utf-8")
    _write_csv(matrix, _all_matrix_rows())
    _write_csv(grain, _grain_rows())
    _write_csv(
        blockers,
        [
            {
                "nodi_register_row_id": "*",
                "comsol_gate_id": "G2-JRC-STRONG-CLAIMS",
                "blocker_status": "NODI_RECONCILED_BLOCKED_STRONG_CLAIMS",
                "blocker_reason": "JOINT_ROUTE_CLASS",
                "required_next_gate": "future explicit authorization",
            }
        ],
    )
    (roadmap / "COMSOL_GATE2A_NODI_BINDING_PACKET_20260627.md").write_text("packet\n", encoding="utf-8")
    _write_csv(roadmap / "COMSOL_GATE2A_NODI_BINDING_CROSSWALK_20260627.csv", _crosswalk_rows())
    _write_csv(roadmap / "COMSOL_GATE2A_NODI_BINDING_BLOCKERS_20260627.csv", [{"blocker_id": "G2A-BLOCK-001"}])
    _write_csv(
        roadmap / "COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv",
        [
            {
                "provenance_row_id": "QCHPROV-0001",
                "is_formal_gate2_qch_sidecar": "false",
                "qch_weighting_authorized": "false",
                "qch_eta_authorized": "false",
                "qch_chi_eta_authorized": "false",
                "recommended_nodi_reconciled_status": "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR",
            }
        ],
    )
    _write_csv(roadmap / "COMSOL_GATE2A_NODI_BINDING_VALIDATION_20260627.csv", [{"check_id": "G2A-VAL-001", "status": "PASS"}])
    _write_csv(roadmap / "COMSOL_GATE2A_NODI_BINDING_MANIFEST_20260627.csv", [{"manifest_role": "gate2a_crosswalk"}])

    rc = main(
        [
            "--confirm-gate2b-formal-context-only",
            "--comsol-root",
            str(comsol),
            "--gate2a-matrix",
            str(matrix),
            "--gate2a-grain",
            str(grain),
            "--gate2a-blockers",
            str(blockers),
            "--gate2a-report",
            str(report),
            "--output-dir",
            str(output),
            "--report-dir",
            str(report_dir),
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert PASS_STATUS in captured.out
    assert (output / "NODI_COMSOL_GATE2B_FORMAL_CONTEXT_INGEST_REGISTER_20260627.csv").exists()
    assert (report_dir / "200_NODI_COMSOL_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_20260627.md").exists()
