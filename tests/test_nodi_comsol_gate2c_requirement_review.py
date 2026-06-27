from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2c_requirement_review as gate2c


def _allowed_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    views = ["fixed_660_gold", "per_wavelength_gold"]
    for view in views:
        for diameter in ["220", "300"]:
            for route in ["660/W800/D900", "660/W800/D1200"]:
                for support_slice in ["low_context", "high_context"]:
                    rows.append(
                        {
                            "gate2b_context_row_id": f"AGG-{len(rows) + 1:03d}",
                            "source_row_type": "proxy_aggregate",
                            "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
                            "source_row_identity": f"{route}|{diameter}|{view}|{support_slice}",
                            "route_key": route,
                            "NODI_view": view,
                            "diameter_nm": diameter,
                            "bin_basis": "not_position_binned",
                            "tpd_bin_label": "aggregate",
                            "gate2b_artifact_level_context_candidate": "true",
                            "gate2b_grain_level_context_ingestion_authorized": "false",
                            "allowed_use": "artifact-level context support only",
                            "blocked_use": "weighting; JRC; chi_selected",
                        }
                    )
    for view in views:
        for diameter in ["220", "300"]:
            for route in ["660/W800/D900", "660/W800/D1200"]:
                for edge4 in ["q1", "q2", "q3", "q4"]:
                    for support_slice in ["low_context", "high_context"]:
                        rows.append(
                            {
                                "gate2b_context_row_id": f"BIN-{len(rows) + 1:03d}",
                                "source_row_type": "proxy_bin",
                                "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
                                "source_row_identity": f"{route}|{diameter}|{view}|{edge4}|{support_slice}",
                                "route_key": route,
                                "NODI_view": view,
                                "diameter_nm": diameter,
                                "bin_basis": "edge4_quarter_bin",
                                "tpd_bin_label": edge4,
                                "gate2b_artifact_level_context_candidate": "true",
                                "gate2b_grain_level_context_ingestion_authorized": "false",
                                "allowed_use": "artifact-level bin proxy support only",
                                "blocked_use": "direct PRS edge20 bin; weighting; JRC; chi_selected",
                            }
                        )
    assert len(rows) == 80
    return rows


def _write_support_file(path: Path, rows: list[dict[str, str]] | None = None) -> None:
    if path.suffix == ".csv":
        write_csv_rows(path, rows or [{"status": "unit"}])
    else:
        path.write_text("unit evidence\n", encoding="utf-8")


def _stage_inputs(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path, Path, Path]:
    nodi_dir = tmp_path / "nodi"
    nodi_dir.mkdir()
    register = nodi_dir / "register.csv"
    ingested = nodi_dir / "ingested.csv"
    quarantine = nodi_dir / "quarantine.csv"
    blocked = nodi_dir / "blocked.csv"
    schema = nodi_dir / "schema.csv"
    report_200 = nodi_dir / "report_200.md"
    write_csv_rows(
        register,
        [
            {
                "nodi_register_row_id": "G2CTX-CHI-AGG-004",
                "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
                "source_row_count": "16",
            },
            {
                "nodi_register_row_id": "G2CTX-CHI-BIN-005",
                "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
                "source_row_count": "64",
            },
        ],
    )
    write_csv_rows(ingested, [{"lane": "context_only"}])
    write_csv_rows(quarantine, [{"lane": "qch_provenance_only"}])
    write_csv_rows(blocked, [{"route_key": "660/W800/D1200", "diameter_nm": "300"}])
    write_csv_rows(schema, [{"field_name": "route_key"}])
    report_200.write_text("PASS_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_PARTIAL_NO_WEIGHTING_NO_JRC\n", encoding="utf-8")

    monkeypatch.setattr(gate2c, "NODI_GATE2B_REGISTER", register)
    monkeypatch.setattr(gate2c, "NODI_GATE2B_INGESTED", ingested)
    monkeypatch.setattr(gate2c, "NODI_GATE2B_QUARANTINE", quarantine)
    monkeypatch.setattr(gate2c, "NODI_GATE2B_BLOCKED_GRAIN", blocked)
    monkeypatch.setattr(gate2c, "NODI_GATE2B_SCHEMA", schema)
    monkeypatch.setattr(gate2c, "NODI_REPORT_200", report_200)

    prs = tmp_path / "prs.csv"
    eas = tmp_path / "eas.csv"
    write_csv_rows(
        prs,
        [
            {"route_id_nodi": "660/W800/D900", "diameter_nm": "300", "NODI_view": "fixed_660_gold"},
            {"route_id_nodi": "660/W800/D900", "diameter_nm": "300", "NODI_view": "per_wavelength_gold"},
        ],
    )
    write_csv_rows(
        eas,
        [
            {"route_id_nodi": "660/W800/D900", "NODI_view": "fixed_660_gold"},
            {"route_id_nodi": "660/W800/D900", "NODI_view": "per_wavelength_gold"},
        ],
    )
    monkeypatch.setattr(gate2c, "EXPECTED_PRS_SHA", sha256_file(prs))
    monkeypatch.setattr(gate2c, "EXPECTED_EAS_SHA", sha256_file(eas))

    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    file_rows = {
        "COMSOL_GATE2B_NODI_ALLOWED_CONTEXT_ROWS_20260627.csv": _allowed_rows(),
        "COMSOL_GATE2B_NODI_QUARANTINE_REVIEW_ONLY_ROWS_20260627.csv": [
            {"lane": "qch_provenance_only", "NODI_view": "UNBOUND"}
        ],
        "COMSOL_GATE2B_TPD_BINDING_REPAIR_PLAN_20260627.csv": [
            {"repair": "missing_NODI_view", "status": "required"}
        ],
        "COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv": [
            {
                "requirement_id": "QCH-REQ-001",
                "field_name": "q_ch",
                "requirement_level": "required",
                "missing_from_gate2a_provenance_export": "true",
                "allowed_use": "future schema review only",
                "blocked_use": "q_ch weighting",
            }
        ],
        "COMSOL_GATE2B_NODI_SUPPORT_VALIDATION_20260627.csv": [{"status": "PASS"}],
    }
    for name, rows in file_rows.items():
        _write_support_file(roadmap / name, rows)
    for name in (
        "COMSOL_GATE2B_NODI_CONTEXT_ONLY_SUPPORT_PACKET_20260627.md",
        "COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.md",
    ):
        _write_support_file(roadmap / name)
    manifest_rows = []
    for _evidence_id, _role, relative in gate2c.COMSOL_EVIDENCE_FILES:
        path = comsol_root / relative
        if path.name == "COMSOL_GATE2B_NODI_SUPPORT_MANIFEST_20260627.csv":
            continue
        manifest_rows.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "row_count": str(len(file_rows.get(path.name, []))) if path.suffix == ".csv" else "0",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2B_NODI_SUPPORT_MANIFEST_20260627.csv", manifest_rows)
    return comsol_root, prs, eas, tmp_path / "out", tmp_path / "reports"


def test_gate2c_payload_parent_child_and_grain_authorization(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, eas, out, _reports = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2c.build_gate2c_payload(
        comsol_root=comsol_root,
        output_dir=out,
        prs_path=prs,
        eas_path=eas,
        mirror_evidence=True,
    )

    assert gate2c.validate_gate2c_payload(payload) == []
    assert payload["status"] == gate2c.PASS_STATUS
    assert payload["parent_child_counts"] == {"G2CTX-CHI-AGG-004": 16, "G2CTX-CHI-BIN-005": 64}
    assert all(
        row["grain_level_authorization_status"] == "GRAIN_LEVEL_AUTHORIZATION_FALSE"
        for row in payload["allowed_support_acceptance_rows"]
    )
    assert all(row["can_enter_weighting"] == "false" for row in payload["allowed_support_acceptance_rows"])
    assert all(row["can_enter_jrc"] == "false" for row in payload["allowed_support_acceptance_rows"])


def test_gate2c_prs_and_edge_semantics_fail_closed(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, eas, out, _reports = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2c.build_gate2c_payload(
        comsol_root=comsol_root,
        output_dir=out,
        prs_path=prs,
        eas_path=eas,
        mirror_evidence=False,
    )
    verdicts = payload["prs_coverage_verdict_rows"]

    assert any(
        row["diameter_nm"] == "220" and row["coverage_verdict"] == "BLOCKED_220NM_NO_DIRECT_PRS_MATCH"
        for row in verdicts
    )
    assert any(
        row["route_key"] == "660/W800/D1200"
        and row["diameter_nm"] == "300"
        and row["exact_grain_present"] == "false"
        for row in verdicts
    )
    assert {
        row["NODI_view"]
        for row in verdicts
        if row["route_key"] == "660/W800/D900"
        and row["diameter_nm"] == "300"
        and row["source_row_type"] == "proxy_aggregate"
        and row["coverage_verdict"] == "EXACT_GRAIN_PRESENT_CONTEXT_ONLY_REVIEW"
    } == {"fixed_660_gold", "per_wavelength_gold"}
    assert all(
        row["direct_prs_bin_compatible"] == "false"
        for row in verdicts
        if row["source_row_type"] == "proxy_bin"
    )
    assert all(row["policy_approved"] == "false" for row in payload["edge_policy_checklist_rows"])


def test_gate2c_qch_and_forbidden_fields_hard_fail(tmp_path: Path, monkeypatch) -> None:
    comsol_root, prs, eas, out, _reports = _stage_inputs(tmp_path, monkeypatch)
    payload = gate2c.build_gate2c_payload(
        comsol_root=comsol_root,
        output_dir=out,
        prs_path=prs,
        eas_path=eas,
        mirror_evidence=False,
    )

    assert all(row["is_formal_gate2_qch_sidecar"] == "false" for row in payload["qch_acceptance_checklist_rows"])
    assert all(row["qch_weighting_authorized"] == "false" for row in payload["qch_acceptance_checklist_rows"])

    bad_payload = dict(payload)
    bad_payload["allowed_support_acceptance_rows"] = [
        dict(payload["allowed_support_acceptance_rows"][0], can_enter_jrc="true")
    ]
    assert any("forbidden flag can_enter_jrc" in issue for issue in gate2c.validate_gate2c_payload(bad_payload))

    bad_v4_payload = dict(payload)
    bad_v4_context = dict(payload["comsol_v4_context"])
    bad_v4_context["nodi_runtime_configuration_allowed"] = True
    bad_v4_payload["comsol_v4_context"] = bad_v4_context
    assert gate2c.validate_gate2c_payload(bad_v4_payload)


def test_gate2c_cli_writes_pass_report(tmp_path: Path, monkeypatch, capsys) -> None:
    comsol_root, prs, eas, out, reports = _stage_inputs(tmp_path, monkeypatch)
    result = gate2c.main(
        [
            "--confirm-gate2c-requirement-review",
            "--comsol-root",
            str(comsol_root),
            "--prs",
            str(prs),
            "--eas",
            str(eas),
            "--output-dir",
            str(out),
            "--report-dir",
            str(reports),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert gate2c.PASS_STATUS in captured.out
    report = json.loads((out / gate2c.REPORT_JSON).read_text(encoding="utf-8"))
    assert report["status"] == gate2c.PASS_STATUS
    assert report["edge4_edge20_policy_approved"] is False
    assert report["qch_formal_sidecar_exists"] is False
    assert (reports / gate2c.REPORT_201).exists()
