from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2h_edge_closure_review as gate2h


def _edge_groups() -> tuple[tuple[str, str], ...]:
    return (
        ("edge_norm_0p00_0p25", "edge_00|edge_01|edge_02|edge_03|edge_04"),
        ("edge_norm_0p25_0p50", "edge_05|edge_06|edge_07|edge_08|edge_09"),
        ("edge_norm_0p50_0p75", "edge_10|edge_11|edge_12|edge_13|edge_14"),
        ("edge_norm_0p75_1p00", "edge_15|edge_16|edge_17|edge_18|edge_19"),
    )


def _structural_rows(
    *, edge_hash: str = "edge-hash", noncontiguous: bool = False, formula_true: bool = False
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    index = 1
    for view in ("fixed_660_gold", "per_wavelength_gold"):
        for basis in ("residence_time_weighted", "velocity_weighted"):
            for label, bins in _edge_groups():
                rows.append(
                    {
                        "structural_coverage_proof_id": f"G2G-EDGE-COV-{index:03d}",
                        "source_gate2f_edge_evidence_id": f"G2F-EDGE-EVID-{index:03d}",
                        "source_edge_skeleton_row_id": f"G2E-EDGE-SKEL-{index:03d}",
                        "route_key_candidate": "660/W800/D900",
                        "NODI_view": view,
                        "diameter_nm": "300",
                        "tpd_proxy_aggregation_basis": basis,
                        "edge4_bin_label": label,
                        "edge20_definition_hash": edge_hash,
                        "proposed_edge20_bins_covered": bins if not noncontiguous or index != 1 else bins.replace("edge_04", "edge_06"),
                        "edge20_bin_count": "5",
                        "coverage_complete": "true",
                        "coverage_contiguous": "false" if noncontiguous and index == 1 else "true",
                        "structural_proof_status": "STRUCTURAL_COVERAGE_PROOF_PASS_REVIEW_ONLY",
                        "direct_prs_bin_use_authorized": "false",
                        "formula_use_authorized": "true" if formula_true and index == 1 else "false",
                        "grain_level_ingestion_authorized": "false",
                        "accepted_row_expansion_authorized": "false",
                        "production_ingestion_authorized": "false",
                        "runtime_configuration_authorized": "false",
                    }
                )
                index += 1
    return rows


def _nodi_recon_rows(edge_hash: str = "edge-hash") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for structural in _structural_rows(edge_hash=edge_hash):
        rows.append(
            {
                "source_edge_skeleton_row_id": structural["source_edge_skeleton_row_id"],
                "route_key": structural["route_key_candidate"],
                "NODI_view": structural["NODI_view"],
                "diameter_nm": structural["diameter_nm"],
                "tpd_proxy_aggregation_basis": structural["tpd_proxy_aggregation_basis"],
                "edge4_bin_label": structural["edge4_bin_label"],
                "nodi_edge20_definition_hash": edge_hash,
                "nodi_candidate_edge20_group": structural["proposed_edge20_bins_covered"],
            }
        )
    return rows


def _receipt_rows(edge_hash: str = "edge-hash") -> list[dict[str, str]]:
    return [
        {
            "source_edge_skeleton_row_id": row["source_edge_skeleton_row_id"],
            "loss_error_policy_approval_status": "NOT_APPROVED",
            "edge20_definition_hash": edge_hash,
            "coverage_complete": "true",
            "coverage_contiguous": "true",
            "direct_prs_bin_use_authorized": "false",
            "formula_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        }
        for row in _structural_rows(edge_hash=edge_hash)
    ]


def _loss_rows() -> list[dict[str, str]]:
    areas = (
        "information_loss",
        "coverage",
        "monotonicity",
        "conservativeness",
        "error_bounds",
        "reproducibility",
        "review_context_only",
        "formula_exclusion",
    )
    return [
        {
            "loss_error_requirement_id": f"G2G-EDGE-LOSSREQ-{index:03d}",
            "nodi_check_id": f"LOSS-{index}",
            "semantics_area": area,
            "comsol_gate2g_status": "MISSING_REQUIRED_FOR_POLICY_APPROVAL"
            if area in {"monotonicity", "conservativeness", "error_bounds"}
            else "STRUCTURAL_REVIEWABLE",
            "numeric_aggregation_error_bound_status": "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
            "monotonicity_status": "MISSING_NOT_EVALUABLE",
            "conservativeness_status": "MISSING_NOT_EVALUABLE",
            "reproducibility_status": "STRUCTURAL_REPRODUCIBILITY_ONLY",
            "formula_exclusion_active": "true",
            "policy_approval_status": "NOT_APPROVED",
            "direct_prs_bin_use_authorized": "false",
            "formula_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        }
        for index, area in enumerate(areas, start=1)
    ]


def _stage_inputs(
    tmp_path: Path,
    monkeypatch,
    *,
    edge_hash: str = "edge-hash",
    structural_hash: str | None = None,
    noncontiguous: bool = False,
    formula_true: bool = False,
    manifest_bad: bool = False,
) -> Path:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    write_csv_rows(
        roadmap / "COMSOL_GATE2G_EDGE4_EDGE20_STRUCTURAL_COVERAGE_PROOF_20260628.csv",
        _structural_rows(edge_hash=structural_hash or edge_hash, noncontiguous=noncontiguous, formula_true=formula_true),
    )
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_REQUIREMENTS_20260628.csv", _loss_rows())
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_POLICY_OPTION_MATRIX_20260628.csv", [{"policy": "not_approved"}])
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_BLOCKER_CARRY_FORWARD_20260628.csv", [{"excluded_class": "QCH", "carry_forward_status": "NO_CHANGE"}])
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_NODI_RECEIPT_SUPPORT_20260628.csv", _receipt_rows(edge_hash=edge_hash))
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_VALIDATION_20260628.csv", [{"status": "PASS"}])
    for name in (
        "COMSOL_GATE2G_EDGE4_EDGE20_STRUCTURAL_COVERAGE_PROOF_PACKET_20260628.md",
        "COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_REQUIREMENTS_PACKET_20260628.md",
        "COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_MASTER_PACKET_20260628.md",
    ):
        (roadmap / name).write_text("packet\n", encoding="utf-8")
    manifest_paths = [relative for _id, _role, relative in gate2h.COMSOL_ARTIFACTS if relative != gate2h.COMSOL_MANIFEST]
    manifest_rows = []
    for relative in manifest_paths:
        path = comsol_root / relative
        manifest_rows.append(
            {
                "artifact_id": relative.stem,
                "path": relative.as_posix(),
                "sha256": "bad" if manifest_bad and relative == gate2h.COMSOL_STRUCTURAL else sha256_file(path),
                "row_count": str(len(gate2h.read_csv_rows(path))) if path.suffix == ".csv" else "0",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_MANIFEST_20260628.csv", manifest_rows)

    nodi = tmp_path / "nodi"
    nodi.mkdir()
    write_csv_rows(nodi / "recon.csv", _nodi_recon_rows(edge_hash=edge_hash))
    write_csv_rows(nodi / "row_concordance.csv", [{"row_verdict": "unit"} for _ in range(16)])
    write_csv_rows(
        nodi / "loss_gap.csv",
        [{"semantics_area": row["semantics_area"], "received_status": "NOT_APPROVED"} for row in _loss_rows()],
    )
    write_csv_rows(nodi / "next_schema.csv", [{"field": "numeric_aggregation_error_bound"}])
    write_csv_rows(nodi / "blocker.csv", [{"blocker_class": "QCH", "gate2g_status": "UNCHANGED"}])
    write_csv_rows(nodi / "gate2d.csv", [{"id": str(index)} for index in range(4)])
    (nodi / "report206.md").write_text("PASS_GATE2G_EDGE_REVIEW_EVIDENCE_RECEIPT_POLICY_GAP_REGISTERED_NO_FORMULA_NO_JRC\n", encoding="utf-8")
    (nodi / "report.json").write_text("PASS_GATE2G_EDGE_REVIEW_EVIDENCE_RECEIPT_POLICY_GAP_REGISTERED_NO_FORMULA_NO_JRC\n", encoding="utf-8")

    monkeypatch.setattr(gate2h, "NODI_REPORT_206", nodi / "report206.md")
    monkeypatch.setattr(gate2h, "NODI_G2G_REPORT_JSON", nodi / "report.json")
    monkeypatch.setattr(gate2h, "NODI_G2G_RECON", nodi / "recon.csv")
    monkeypatch.setattr(gate2h, "NODI_G2G_ROW_CONCORDANCE", nodi / "row_concordance.csv")
    monkeypatch.setattr(gate2h, "NODI_G2G_LOSS_GAP", nodi / "loss_gap.csv")
    monkeypatch.setattr(gate2h, "NODI_G2G_NEXT_SCHEMA", nodi / "next_schema.csv")
    monkeypatch.setattr(gate2h, "NODI_G2G_BLOCKER", nodi / "blocker.csv")
    monkeypatch.setattr(gate2h, "NODI_G2D_LEDGER", nodi / "gate2d.csv")
    monkeypatch.setattr(gate2h, "EXPECTED_EDGE20_HASH", edge_hash)
    return comsol_root


def test_gate2h_gate2i_pass_policy_not_approved(tmp_path: Path, monkeypatch) -> None:
    comsol_root = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2h.build_payload(comsol_root=comsol_root)

    assert payload["gate2h_disposition"] == gate2h.GATE2H_PASS
    assert payload["gate2i_disposition"] == gate2h.GATE2I_PASS
    assert payload["structural_coverage_row_count"] == 16
    assert payload["receipt_support_row_count"] == 16
    assert payload["gate2d_accepted_row_count"] == 4
    assert payload["policy_decision_verdict_rows"][0]["policy_decision_verdict"] == "EDGE_POLICY_NOT_APPROVED_LOSS_ERROR_GAPS_REMAIN"
    assert gate2h.validate_payload(payload, comsol_root=comsol_root) == []


def test_gate2h_mismatch_cases_partial_or_validation_fail(tmp_path: Path, monkeypatch) -> None:
    hash_root = _stage_inputs(tmp_path / "hash", monkeypatch, structural_hash="bad")
    hash_payload = gate2h.build_payload(comsol_root=hash_root)
    assert hash_payload["gate2h_disposition"] == gate2h.GATE2H_PARTIAL
    assert any("structural mismatch" in issue or "edge20 hash mismatch" in issue for issue in gate2h.validate_payload(hash_payload, comsol_root=hash_root))

    contig_root = _stage_inputs(tmp_path / "contig", monkeypatch, noncontiguous=True)
    contig_payload = gate2h.build_payload(comsol_root=contig_root)
    assert any("coverage contiguity/count failed" in issue for issue in gate2h.validate_payload(contig_payload, comsol_root=contig_root))

    manifest_root = _stage_inputs(tmp_path / "manifest", monkeypatch, manifest_bad=True)
    manifest_payload = gate2h.build_payload(comsol_root=manifest_root)
    assert manifest_payload["gate2h_disposition"] == gate2h.GATE2H_PARTIAL
    assert any("manifest mismatch" in issue for issue in gate2h.validate_payload(manifest_payload, comsol_root=manifest_root))


def test_gate2h_authorization_true_and_negative_fixtures_fail(tmp_path: Path, monkeypatch) -> None:
    root = _stage_inputs(tmp_path, monkeypatch, formula_true=True)
    payload = gate2h.build_payload(comsol_root=root)

    assert any(row["audit_status"] == "FAIL_FORBIDDEN_FIELD_TRUE" for row in payload["gate2h_forbidden_claim_audit_rows"])
    assert any("forbidden field audit failed" in issue for issue in gate2h.validate_payload(payload, comsol_root=root))
    fixture_names = {row["fixture_name"] for row in payload["gate2i_negative_fixture_rows"]}
    assert {
        "missing_numeric_error_bound",
        "non_contiguous_edge20_bins",
        "edge20_hash_mismatch",
        "formula_flag_true",
        "direct_prs_bin_flag_true",
        "qch_weighting_flag_true",
        "accepted_row_expansion_true",
        "d1200_borrows_d900",
        "auto_map_220nm",
    }.issubset(fixture_names)


def test_gate2i_qch_binding_unchanged_and_cli_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _stage_inputs(tmp_path, monkeypatch)
    out = tmp_path / "out"
    reports = tmp_path / "reports"
    result = gate2h.main(
        [
            "--confirm-gate2h-gate2i-edge",
            "--comsol-root",
            str(root),
            "--output-dir",
            str(out),
            "--report-dir",
            str(reports),
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert gate2h.GATE2H_PASS in captured.out
    assert (out / gate2h.H_STRUCTURAL_REVIEW).exists()
    assert (out / gate2h.I_NEGATIVE_FIXTURES).exists()
    assert (reports / gate2h.REPORT_207).exists()
    assert (reports / gate2h.REPORT_208).exists()
