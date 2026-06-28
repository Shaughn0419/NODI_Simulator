from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2f_edge_policy_preflight as gate2f


def _edge_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    labels = (
        ("edge_norm_0p00_0p25", "edge20_01_05"),
        ("edge_norm_0p25_0p50", "edge20_06_10"),
        ("edge_norm_0p50_0p75", "edge20_11_15"),
        ("edge_norm_0p75_1p00", "edge20_16_20"),
    )
    index = 1
    for view in ("fixed_660_gold", "per_wavelength_gold"):
        for basis in ("residence_time_weighted", "velocity_weighted"):
            for label, candidate in labels:
                rows.append(
                    {
                        "edge_deliverable_row_id": f"G2E-EDGE-SKEL-{index:03d}",
                        "source_edge4_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
                        "source_sha256": "source-sha",
                        "source_row_identity": f"CHI_CTX_BIN_660/W800/D900_A85_300NM_{basis}_{label}_{view}",
                        "route_key_candidate": "660/W800/D900",
                        "NODI_view": view,
                        "diameter_nm": "300",
                        "edge4_bin_label": label,
                        "proposed_edge20_group_id_or_pending": f"PENDING__{candidate}",
                        "direct_prs_bin_use_authorized": "false",
                        "formula_use_authorized": "false",
                        "grain_level_ingestion_authorized": "false",
                    }
                )
                index += 1
    return rows


def _edge20_rows(*, omit_bin: str | None = None, prs_sha: str = "prs-sha") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(20):
        bin_id = f"edge_{index:02d}"
        if bin_id == omit_bin:
            continue
        rows.append(
            {
                "edge20_snapshot_id": f"NODI-G2E-EDGE20-{index + 1:02d}",
                "bin_index": str(index),
                "bin_id": bin_id,
                "edge_norm_min": f"{index / 20:.2f}".rstrip("0").rstrip(".") if index else "0",
                "edge_norm_max": f"{(index + 1) / 20:.2f}".rstrip("0").rstrip("."),
                "definition_status": "PASS_EDGE20_DEFINITION_HASHED",
                "source_prs_sha256": prs_sha,
                "edge20_definition_hash": "edge-hash",
            }
        )
    return rows


def _stage_inputs(tmp_path: Path, monkeypatch, *, omit_bin: str | None = None, prs_sha: str = "prs-sha") -> Path:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    write_csv_rows(roadmap / "COMSOL_GATE2E_EDGE4_EDGE20_MINIMAL_DELIVERABLE_SKELETON_20260628.csv", _edge_rows())
    write_csv_rows(roadmap / "COMSOL_GATE2E_MINIMAL_DELIVERABLE_DASHBOARD_20260628.csv", [{"workstream": "EDGE"}])
    write_csv_rows(roadmap / "COMSOL_GATE2E_MINIMAL_DELIVERABLE_VALIDATION_20260628.csv", [{"check": "PASS"}])
    (roadmap / "COMSOL_GATE2E_EDGE4_EDGE20_MINIMAL_DELIVERABLE_PACKET_20260628.md").write_text("edge\n", encoding="utf-8")
    manifest_targets = [
        gate2f.COMSOL_EDGE_SKELETON,
        gate2f.COMSOL_EDGE_PACKET,
        gate2f.COMSOL_MINIMAL_DASHBOARD,
        gate2f.COMSOL_MINIMAL_VALIDATION,
    ]
    manifest_rows = []
    for relative in manifest_targets:
        path = comsol_root / relative
        manifest_rows.append(
            {
                "artifact_id": relative.stem,
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "row_count": str(len(gate2f.read_csv_rows(path))) if path.suffix == ".csv" else "0",
                "evidence_class": "unit",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2E_MINIMAL_DELIVERABLE_MANIFEST_20260628.csv", manifest_rows)

    nodi = tmp_path / "nodi"
    nodi.mkdir()
    accepted = nodi / "accepted.csv"
    write_csv_rows(accepted, [{"id": str(index)} for index in range(4)])
    edge_verdict = nodi / "edge_verdict.csv"
    write_csv_rows(
        edge_verdict,
        [
            {
                "receiver_verdict": "EDGE_REVIEW_CAN_START_WITH_NODI_EDGE20_HASHED_DEFINITION",
                "edge20_definition_hash": "edge-hash",
            }
        ],
    )
    edge20 = nodi / "edge20.csv"
    write_csv_rows(edge20, _edge20_rows(omit_bin=omit_bin, prs_sha=prs_sha))
    dashboard = nodi / "dashboard.csv"
    write_csv_rows(
        dashboard,
        [
            {"gate": "Gate2E-QCH", "receiver_status": "QCH_FORMAL_RECEIPT_SCHEMA_READY_BUT_NO_FORMAL_SIDECAR_PRESENT"},
            {"gate": "Gate2E-BINDING", "receiver_status": "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED"},
        ],
    )
    report = nodi / "report204.md"
    report.write_text("PASS_GATE2E_RECEIVER_POLICY_VERDICTS_NO_ACCEPTED_ROW_EXPANSION_NO_WEIGHTING_NO_JRC\n", encoding="utf-8")
    monkeypatch.setattr(gate2f, "NODI_GATE2D_ACCEPTED_LEDGER", accepted)
    monkeypatch.setattr(gate2f, "NODI_GATE2E_EDGE_VERDICT", edge_verdict)
    monkeypatch.setattr(gate2f, "NODI_GATE2E_EDGE20_SNAPSHOT", edge20)
    monkeypatch.setattr(gate2f, "NODI_GATE2E_DASHBOARD", dashboard)
    monkeypatch.setattr(gate2f, "NODI_REPORT_204", report)
    monkeypatch.setattr(gate2f, "EXPECTED_EDGE20_DEFINITION_HASH", "edge-hash")
    monkeypatch.setattr(gate2f, "EXPECTED_PRS_SHA", "prs-sha")
    return comsol_root


def test_gate2f_edge_pass_reads_16_skeleton_rows_and_keeps_gate2d_frozen(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2f.build_gate2f_edge_payload(comsol_root=comsol_root)

    assert payload["status"] == gate2f.PASS_STATUS
    assert payload["gate2d_accepted_row_count"] == 4
    assert payload["comsol_edge_skeleton_row_count"] == 16
    assert len(payload["grouping_candidate_preflight_rows"]) == 16
    assert {row["edge20_bins_covered"] for row in payload["grouping_candidate_preflight_rows"]} == {"5"}
    assert gate2f.validate_gate2f_payload(payload, comsol_root=comsol_root) == []


def test_gate2f_grouping_is_review_only_and_non_edge_unchanged(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2f.build_gate2f_edge_payload(comsol_root=comsol_root)

    assert all(row["direct_prs_bin_use_authorized"] == "false" for row in payload["grouping_candidate_preflight_rows"])
    assert all(row["formula_use_authorized"] == "false" for row in payload["grouping_candidate_preflight_rows"])
    assert all(row["grain_level_ingestion_authorized"] == "false" for row in payload["grouping_candidate_preflight_rows"])
    carry = {row["workstream"]: row["gate2f_status"] for row in payload["non_edge_carry_forward_rows"]}
    assert carry["Gate2E-QCH"] == "UNCHANGED_SCHEMA_READY_NO_FORMAL_SIDECAR"
    assert carry["Gate2E-BINDING"] == "UNCHANGED_220_D1200_UNBOUND_FAIL_CLOSED"


def test_gate2f_missing_edge20_boundary_returns_partial_not_silent_mapping(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch, omit_bin="edge_04")
    payload = gate2f.build_gate2f_edge_payload(comsol_root=comsol_root)

    assert payload["status"] == gate2f.PARTIAL_STATUS
    assert any(
        row["review_only_status"] == "BLOCKED_MISSING_EDGE20_GROUP_BOUNDARY"
        for row in payload["grouping_candidate_preflight_rows"]
    )
    assert gate2f.validate_gate2f_payload(payload, comsol_root=comsol_root) == []


def test_gate2f_forbidden_fields_and_prs_hash_drift_hard_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2f.build_gate2f_edge_payload(comsol_root=comsol_root)

    bad_payload = dict(payload)
    bad_payload["grouping_candidate_preflight_rows"] = [
        dict(payload["grouping_candidate_preflight_rows"][0], formula_use_authorized="true")
    ]
    assert any("formula_use_authorized" in issue for issue in gate2f.validate_gate2f_payload(bad_payload, comsol_root=comsol_root))

    drift_root = _stage_inputs(tmp_path / "drift", monkeypatch, prs_sha="drifted")
    drift_payload = gate2f.build_gate2f_edge_payload(comsol_root=drift_root)
    assert any("PRS hash drift" in issue for issue in gate2f.validate_gate2f_payload(drift_payload, comsol_root=drift_root))


def test_gate2f_cli_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    output_dir = tmp_path / "out"
    report_dir = tmp_path / "reports"
    result = gate2f.main(
        [
            "--confirm-gate2f-edge-preflight",
            "--comsol-root",
            str(comsol_root),
            "--output-dir",
            str(output_dir),
            "--report-dir",
            str(report_dir),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert gate2f.PASS_STATUS in captured.out
    assert (output_dir / gate2f.GROUPING_PREFLIGHT).exists()
    assert (output_dir / gate2f.ROW_VERDICT).exists()
    assert (report_dir / gate2f.REPORT_205).exists()
