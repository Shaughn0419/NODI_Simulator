from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2g_edge_evidence_receipt as gate2g


def _candidate_rows(*, edge_hash: str = "edge-hash", mutate_group: bool = False) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    labels = (
        ("edge_norm_0p00_0p25", "edge_00|edge_01|edge_02|edge_03|edge_04"),
        ("edge_norm_0p25_0p50", "edge_05|edge_06|edge_07|edge_08|edge_09"),
        ("edge_norm_0p50_0p75", "edge_10|edge_11|edge_12|edge_13|edge_14"),
        ("edge_norm_0p75_1p00", "edge_15|edge_16|edge_17|edge_18|edge_19"),
    )
    index = 1
    for view in ("fixed_660_gold", "per_wavelength_gold"):
        for basis in ("residence_time_weighted", "velocity_weighted"):
            for label, group in labels:
                if mutate_group and index == 1:
                    group = group.replace("edge_04", "edge_99")
                rows.append(
                    {
                        "gate2f_edge_evidence_id": f"G2F-EDGE-EVID-{index:03d}",
                        "source_edge_skeleton_row_id": f"G2E-EDGE-SKEL-{index:03d}",
                        "source_edge4_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
                        "source_sha256": "source-sha",
                        "source_row_identity": f"CHI_CTX_BIN_660/W800/D900_A85_300NM_{basis}_{label}_{view}",
                        "route_key_candidate": "660/W800/D900",
                        "NODI_view": view,
                        "diameter_nm": "300",
                        "tpd_proxy_aggregation_basis": basis,
                        "edge4_bin_label": label,
                        "nodi_edge20_definition_hash": edge_hash,
                        "proposed_edge20_group_id": f"REVIEW_ONLY_EDGE20_GROUP_{index:02d}",
                        "proposed_edge20_bins_covered": group,
                        "candidate_status": "EDGE_REVIEW_EVIDENCE_CANDIDATE_NOT_APPROVED",
                        "direct_prs_bin_use_authorized": "false",
                        "formula_use_authorized": "false",
                        "grain_level_ingestion_authorized": "false",
                        "accepted_row_expansion_authorized": "false",
                        "allowed_use": "review only",
                        "blocked_use": "formula; JRC",
                    }
                )
                index += 1
    return rows


def _nodi_grouping_rows(*, edge_hash: str = "edge-hash") -> list[dict[str, str]]:
    rows = []
    for candidate in _candidate_rows(edge_hash=edge_hash):
        rows.append(
            {
                "grouping_preflight_id": candidate["gate2f_edge_evidence_id"].replace("G2F-EDGE-EVID", "NODI-G2F-EDGE-GROUP"),
                "source_edge_deliverable_row_id": candidate["source_edge_skeleton_row_id"],
                "route_key": candidate["route_key_candidate"],
                "NODI_view": candidate["NODI_view"],
                "diameter_nm": candidate["diameter_nm"],
                "tpd_proxy_aggregation_basis": candidate["tpd_proxy_aggregation_basis"],
                "edge4_bin_label": candidate["edge4_bin_label"],
                "candidate_edge20_group": candidate["proposed_edge20_bins_covered"],
                "edge20_bins_covered": "5",
                "nodi_edge20_definition_hash": edge_hash,
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
            }
        )
    return rows


def _stage_inputs(
    tmp_path: Path,
    monkeypatch,
    *,
    edge_hash: str = "edge-hash",
    mutate_group: bool = False,
    manifest_bad: bool = False,
) -> Path:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    write_csv_rows(
        roadmap / "COMSOL_GATE2F_EDGE4_EDGE20_REVIEW_EVIDENCE_CANDIDATE_20260628.csv",
        _candidate_rows(edge_hash=edge_hash, mutate_group=mutate_group),
    )
    write_csv_rows(
        roadmap / "COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_CANDIDATE_20260628.csv",
        [
            {
                "semantics_row_id": f"SEM-{index}",
                "edge4_bin_label": label,
                "nodi_edge20_definition_hash": edge_hash,
                "candidate_edge20_bins_covered": group,
                "information_loss_description": "coarse group",
                "aggregation_error_bound_status": "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
                "numeric_error_bound_value": "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
                "monotonicity_check_required": "true",
                "conservativeness_check_required": "true",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
            }
            for index, (label, group) in enumerate(
                (
                    ("edge_norm_0p00_0p25", "edge_00|edge_01|edge_02|edge_03|edge_04"),
                    ("edge_norm_0p25_0p50", "edge_05|edge_06|edge_07|edge_08|edge_09"),
                    ("edge_norm_0p50_0p75", "edge_10|edge_11|edge_12|edge_13|edge_14"),
                    ("edge_norm_0p75_1p00", "edge_15|edge_16|edge_17|edge_18|edge_19"),
                ),
                start=1,
            )
        ],
    )
    write_csv_rows(
        roadmap / "COMSOL_GATE2F_EDGE_EXCLUSIONS_CARRY_FORWARD_20260628.csv",
        [{"excluded_class": "QCH", "carry_forward_status": "NO_CHANGE", "row_count_or_scope": "gap"}],
    )
    write_csv_rows(roadmap / "COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_VALIDATION_20260628.csv", [{"status": "PASS"}])
    for name in (
        "COMSOL_GATE2F_EDGE4_EDGE20_REVIEW_EVIDENCE_PACKET_20260628.md",
        "COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_PACKET_20260628.md",
        "COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_MASTER_PACKET_20260628.md",
    ):
        (roadmap / name).write_text("packet\n", encoding="utf-8")
    manifest_paths = [relative for _id, _role, relative in gate2g.COMSOL_ARTIFACTS if relative != gate2g.COMSOL_MANIFEST]
    manifest_rows = []
    for relative in manifest_paths:
        path = comsol_root / relative
        manifest_rows.append(
            {
                "artifact_id": relative.stem,
                "path": relative.as_posix(),
                "sha256": "bad" if manifest_bad and relative == gate2g.COMSOL_CANDIDATE else sha256_file(path),
                "row_count": str(len(gate2g.read_csv_rows(path))) if path.suffix == ".csv" else "0",
                "evidence_class": "unit",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_MANIFEST_20260628.csv", manifest_rows)

    nodi = tmp_path / "nodi"
    nodi.mkdir()
    grouping = nodi / "grouping.csv"
    write_csv_rows(grouping, _nodi_grouping_rows(edge_hash=edge_hash))
    write_csv_rows(nodi / "row_verdict.csv", [{"row_verdict": "unit"}])
    write_csv_rows(
        nodi / "loss.csv",
        [
            {"check_id": "LOSS-001", "semantics_area": "information_loss"},
            {"check_id": "LOSS-002", "semantics_area": "coverage"},
            {"check_id": "LOSS-003", "semantics_area": "monotonicity"},
            {"check_id": "LOSS-004", "semantics_area": "conservativeness"},
            {"check_id": "LOSS-005", "semantics_area": "error_bounds"},
            {"check_id": "LOSS-006", "semantics_area": "reproducibility"},
            {"check_id": "LOSS-007", "semantics_area": "review_context_only"},
            {"check_id": "LOSS-008", "semantics_area": "formula_exclusion"},
        ],
    )
    write_csv_rows(
        nodi / "non_edge.csv",
        [{"workstream": "Gate2E-QCH", "gate2f_status": "UNCHANGED_SCHEMA_READY_NO_FORMAL_SIDECAR"}],
    )
    write_csv_rows(nodi / "gate2d.csv", [{"id": str(index)} for index in range(4)])
    report205 = nodi / "report205.md"
    report205.write_text("PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC\n", encoding="utf-8")
    report_json = nodi / "report.json"
    report_json.write_text("PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC\n", encoding="utf-8")
    monkeypatch.setattr(gate2g, "NODI_REPORT_205", report205)
    monkeypatch.setattr(gate2g, "NODI_GATE2F_GROUPING", grouping)
    monkeypatch.setattr(gate2g, "NODI_GATE2F_ROW_VERDICT", nodi / "row_verdict.csv")
    monkeypatch.setattr(gate2g, "NODI_GATE2F_LOSS_CHECKLIST", nodi / "loss.csv")
    monkeypatch.setattr(gate2g, "NODI_GATE2F_NON_EDGE", nodi / "non_edge.csv")
    monkeypatch.setattr(gate2g, "NODI_GATE2F_REPORT_JSON", report_json)
    monkeypatch.setattr(gate2g, "NODI_GATE2D_ACCEPTED_LEDGER", nodi / "gate2d.csv")
    monkeypatch.setattr(gate2g, "EXPECTED_EDGE20_HASH", edge_hash)
    return comsol_root


def test_gate2g_concordance_passes_with_16_rows(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2g.build_gate2g_payload(comsol_root=comsol_root)

    assert payload["status"] == gate2g.PASS_STATUS
    assert payload["comsol_candidate_row_count"] == 16
    assert payload["nodi_gate2f_grouping_row_count"] == 16
    assert payload["gate2d_accepted_row_count"] == 4
    assert all(row["concordance_status"] == "EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED" for row in payload["grouping_cross_reconciliation_rows"])
    assert gate2g.validate_gate2g_payload(payload, comsol_root=comsol_root) == []


def test_gate2g_grouping_mismatch_is_partial(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch, mutate_group=True)
    payload = gate2g.build_gate2g_payload(comsol_root=comsol_root)

    assert payload["status"] == gate2g.PARTIAL_STATUS
    assert any(row["concordance_status"] == "BLOCKED_EDGE_GROUPING_MISMATCH" for row in payload["grouping_cross_reconciliation_rows"])
    assert any("grouping mismatch" in issue for issue in gate2g.validate_gate2g_payload(payload, comsol_root=comsol_root))


def test_gate2g_manifest_mismatch_is_partial(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch, manifest_bad=True)
    payload = gate2g.build_gate2g_payload(comsol_root=comsol_root)

    assert payload["status"] == gate2g.PARTIAL_STATUS
    assert any(row["manifest_audit_status"] == "FAIL_MANIFEST_MISMATCH" for row in payload["manifest_audit_rows"])
    assert any("manifest mismatch" in issue for issue in gate2g.validate_gate2g_payload(payload, comsol_root=comsol_root))


def test_gate2g_hash_mismatch_and_forbidden_field_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch, edge_hash="edge-hash")
    payload = gate2g.build_gate2g_payload(comsol_root=comsol_root)

    bad_hash = dict(payload)
    bad_hash["nodi_edge20_definition_hash"] = "bad"
    assert any("NODI edge20 hash mismatch" in issue for issue in gate2g.validate_gate2g_payload(bad_hash, comsol_root=comsol_root))

    bad_flag = dict(payload)
    bad_flag["grouping_cross_reconciliation_rows"] = [
        dict(payload["grouping_cross_reconciliation_rows"][0], formula_use_authorized="true")
    ]
    assert any("formula_use_authorized" in issue for issue in gate2g.validate_gate2g_payload(bad_flag, comsol_root=comsol_root))


def test_gate2g_cli_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    output_dir = tmp_path / "out"
    report_dir = tmp_path / "reports"
    result = gate2g.main(
        [
            "--confirm-gate2g-edge-receipt",
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
    assert gate2g.PASS_STATUS in captured.out
    assert (output_dir / gate2g.GROUPING_RECON).exists()
    assert (output_dir / gate2g.LOSS_GAP).exists()
    assert (report_dir / gate2g.REPORT_206).exists()
