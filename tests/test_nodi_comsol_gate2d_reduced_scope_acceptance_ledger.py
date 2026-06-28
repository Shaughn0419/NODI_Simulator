from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2d_reduced_scope_acceptance_ledger as ledger


def _candidate_rows(source_sha: str) -> list[dict[str, str]]:
    specs = [
        ("G2D-RS-CAND-001", "G2C-CAND-0077", "fixed_660_gold", "residence_time_weighted"),
        ("G2D-RS-CAND-002", "G2C-CAND-0078", "fixed_660_gold", "velocity_weighted"),
        ("G2D-RS-CAND-003", "G2C-CAND-0079", "per_wavelength_gold", "residence_time_weighted"),
        ("G2D-RS-CAND-004", "G2C-CAND-0080", "per_wavelength_gold", "velocity_weighted"),
    ]
    return [
        {
            "gate2d_candidate_row_id": gate2d_id,
            "source_candidate_export_row_id": gate2c_id,
            "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
            "source_sha256": source_sha,
            "source_row_count": "16",
            "source_row_identity": f"CHI_CTX_AGG_660/W800/D900_A85_300_{view}_{basis}",
            "route_key_candidate": "660/W800/D900",
            "NODI_view": view,
            "diameter_nm": "300",
            "tpd_proxy_aggregation_basis": basis,
            "bin_basis": "aggregate_proxy",
            "candidate_status": "PROPOSED_FOR_NODI_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_REVIEW_NOT_ACCEPTED",
            "exact_prs_match_claim_by_comsol": "false",
            "requires_nodi_prs_verdict": "true",
            "artifact_level_context_candidate": "true",
            "grain_level_ingestion_authorized": "false",
            "formula_use_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "chi_selected_authorized": "false",
            "production_ingestion_authorized": "false",
            "runtime_configuration_authorized": "false",
            "allowed_use": "context-only",
            "blocked_use": "q_ch weighting; JRC; winner; yield; detection_probability",
            "required_next_gate": "NODI_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_PRS_VERDICT",
        }
        for gate2d_id, gate2c_id, view, basis in specs
    ]


def _stage_inputs(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    source = roadmap / "TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv"
    write_csv_rows(source, [{"row": str(index)} for index in range(16)])
    source_sha = sha256_file(source)
    candidate = roadmap / "COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_CANDIDATE_20260628.csv"
    write_csv_rows(candidate, _candidate_rows(source_sha))
    validation = roadmap / "COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_VALIDATION_20260628.csv"
    write_csv_rows(validation, [{"check_id": "G2D-VAL-001", "status": "PASS"}])
    exclusions = roadmap / "COMSOL_GATE2D_REDUCED_SCOPE_EXCLUSIONS_20260628.csv"
    write_csv_rows(
        exclusions,
        [
            {
                "excluded_status": "BLOCKED_220NM_NO_DIRECT_MATCH",
                "source_rows_covered": "72",
                "excluded_category": "220_nm_rows",
                "why_excluded": "blocked",
                "required_next_gate": "future",
            }
        ],
    )
    for name in (
        "COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_CANDIDATE_PACKET_20260628.md",
        "COMSOL_GATE2C_BINDING_ALIGNMENT_ERRATA_20260628.md",
    ):
        (roadmap / name).write_text("unit\n", encoding="utf-8")
    write_csv_rows(roadmap / "COMSOL_GATE2C_CANDIDATE_EXPORT_STATUS_RECONCILIATION_20260628.csv", [{"status": "unit"}])
    manifest_paths = [
        ledger.COMSOL_GATE2D_CANDIDATE,
        ledger.COMSOL_GATE2D_PACKET,
        ledger.COMSOL_GATE2D_VALIDATION,
        ledger.COMSOL_GATE2D_EXCLUSIONS,
        ledger.COMSOL_GATE2C_ERRATA,
        ledger.COMSOL_GATE2C_STATUS_RECON,
    ]
    manifest_rows = []
    for relative in manifest_paths:
        path = comsol_root / relative
        manifest_rows.append(
            {
                "package_id": path.stem,
                "manifest_role": "unit",
                "path": relative.as_posix(),
                "row_count": str(len(ledger.read_csv_rows(path))) if path.suffix == ".csv" else "0",
                "sha256": sha256_file(path),
                "status": "PASS",
                "notes": "unit",
            }
        )
    manifest = roadmap / "COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_MANIFEST_20260628.csv"
    write_csv_rows(manifest, manifest_rows)

    nodi = tmp_path / "nodi"
    nodi.mkdir()
    verdict = nodi / "verdict.csv"
    write_csv_rows(
        verdict,
        [
            {
                "source_candidate_row_id": gate2c_id,
                "matched_prs_row_count_from_report201": "467",
                "prs_evidence_hash": ledger.EXPECTED_PRS_SHA,
                "exact_prs_grain_present_from_report201": "true",
            }
            for gate2c_id in ledger.EXPECTED_GATE2C_IDS
        ],
    )
    prs = nodi / "prs.csv"
    write_csv_rows(
        prs,
        [
            {
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
                "source_row_type": "proxy_aggregate",
                "prs_artifact": "tmp/PRS.csv",
                "prs_sha256": ledger.EXPECTED_PRS_SHA,
                "evidence_hash": ledger.EXPECTED_PRS_SHA,
            },
            {
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "per_wavelength_gold",
                "source_row_type": "proxy_aggregate",
                "prs_artifact": "tmp/PRS.csv",
                "prs_sha256": ledger.EXPECTED_PRS_SHA,
                "evidence_hash": ledger.EXPECTED_PRS_SHA,
            },
        ],
    )
    preflight = nodi / "preflight.csv"
    nodi_exclusions = nodi / "exclusions.csv"
    status_recon = nodi / "status_recon.csv"
    report202 = nodi / "report202.md"
    write_csv_rows(preflight, [{"status": "PASS"}])
    write_csv_rows(nodi_exclusions, [{"source_candidate_status": "BLOCKED_220NM_NO_DIRECT_MATCH", "source_candidate_row_count": "72"}])
    write_csv_rows(status_recon, [{"status": "PASS"}])
    report202.write_text("PASS_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_NO_WEIGHTING_NO_JRC\n", encoding="utf-8")
    monkeypatch.setattr(ledger, "NODI_GATE2D_VERDICT", verdict)
    monkeypatch.setattr(ledger, "NODI_GATE2D_PREFLIGHT", preflight)
    monkeypatch.setattr(ledger, "NODI_GATE2D_EXCLUSIONS", nodi_exclusions)
    monkeypatch.setattr(ledger, "NODI_GATE2D_STATUS_RECON", status_recon)
    monkeypatch.setattr(ledger, "NODI_GATE2C_PRS_VERDICT", prs)
    monkeypatch.setattr(ledger, "NODI_REPORT_202", report202)
    return comsol_root, tmp_path / "out"


def test_gate2d_acceptance_ledger_exactly_four_rows(tmp_path: Path, monkeypatch) -> None:
    comsol_root, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = ledger.build_gate2d_acceptance_payload(comsol_root=comsol_root)

    assert payload["status"] == ledger.PASS_STATUS
    assert len(payload["ledger_rows"]) == 4
    assert tuple(row["source_comsol_gate2d_candidate_row_id"] for row in payload["ledger_rows"]) == ledger.EXPECTED_GATE2D_IDS
    assert all(row["route_key"] == "660/W800/D900" for row in payload["ledger_rows"])
    assert all(row["diameter_nm"] == "300" for row in payload["ledger_rows"])
    assert all(row["bin_basis"] == "aggregate_proxy" for row in payload["ledger_rows"])
    assert all(row["context_only_acceptance_allowed"] == "true" for row in payload["ledger_rows"])
    assert ledger.validate_acceptance_payload(payload, comsol_root=comsol_root) == []


def test_gate2d_acceptance_forbidden_fields_and_v4_hard_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = ledger.build_gate2d_acceptance_payload(comsol_root=comsol_root)

    bad_payload = dict(payload)
    bad_payload["ledger_rows"] = [dict(payload["ledger_rows"][0], qch_weighting_authorized="true")]
    assert any("forbidden field qch_weighting_authorized" in issue for issue in ledger.validate_acceptance_payload(bad_payload, comsol_root=comsol_root))

    bad_v4_payload = dict(payload)
    bad_v4 = dict(payload["comsol_v4_context"])
    bad_v4["nodi_production_ingestion_allowed"] = True
    bad_v4_payload["comsol_v4_context"] = bad_v4
    assert ledger.validate_acceptance_payload(bad_v4_payload, comsol_root=comsol_root)


def test_gate2d_acceptance_hash_and_scope_mismatch_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root, _out = _stage_inputs(tmp_path, monkeypatch)
    payload = ledger.build_gate2d_acceptance_payload(comsol_root=comsol_root)

    bad_hash = dict(payload)
    bad_hash["ledger_rows"] = [dict(payload["ledger_rows"][0], prs_sha256="bad")]
    assert any("PRS hash drifted" in issue for issue in ledger.validate_acceptance_payload(bad_hash, comsol_root=comsol_root))

    bad_scope = dict(payload)
    bad_scope["ledger_rows"] = [dict(payload["ledger_rows"][0], diameter_nm="220")]
    assert any("not 300 nm" in issue for issue in ledger.validate_acceptance_payload(bad_scope, comsol_root=comsol_root))


def test_gate2d_acceptance_cli_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    comsol_root, out = _stage_inputs(tmp_path, monkeypatch)
    report_dir = tmp_path / "reports"
    result = ledger.main(
        [
            "--confirm-gate2d-acceptance-ledger",
            "--comsol-root",
            str(comsol_root),
            "--output-dir",
            str(out),
            "--report-dir",
            str(report_dir),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert ledger.PASS_STATUS in captured.out
    assert (out / ledger.ACCEPTED_LEDGER).exists()
    assert (out / ledger.REPORT_JSON).exists()
    assert (report_dir / ledger.REPORT_203).exists()
