from __future__ import annotations

from pathlib import Path

from nodi_simulator import nodi_comsol_gate2_interface_contracts as lib
from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2s_to_gate2w_deep_acceptance as gate2s


def test_library_fingerprint_template_and_mutation_behaviour(tmp_path: Path) -> None:
    csv_path = tmp_path / "edge.csv"
    write_csv_rows(csv_path, [{"route_key": "660/W800/D900", "NODI_view": "fixed_660_gold"}])
    headers = lib.csv_headers_safe(csv_path)

    assert lib.csv_row_count(csv_path) == 1
    assert lib.schema_fingerprint(headers) == lib.schema_fingerprint(headers)
    assert lib.classify_workstream(Path("roadmap/EDGE20_QCH_BINDING.csv"), headers) == "QCH"

    template_rows = [{"template_only": "true", "not_evidence": "true", "formula_use_authorized": "false"}]
    assert lib.validate_template_not_evidence(template_rows)[0]["validation_status"] == "PASS_TEMPLATE_NOT_EVIDENCE"

    mutation = {
        "mutation_id": "M1",
        "mutation_family": "authorization_true",
        "mutation_name": "formula_true",
        "mutated_value": "true",
        "expected_fail_reason": "hard fail",
    }
    assert lib.validate_mutation_fixture(mutation)["validation_status"] == "PASS_EXPECTED_FAIL"

    bad_ledger = [{"context_only_acceptance_allowed": "true"} for _ in range(5)]
    assert lib.validate_gate2d_accepted_ledger(bad_ledger)

    large = tmp_path / "large.csv"
    large.write_text("a,b\n" + ("x,y\n" * 2500000), encoding="utf-8")
    assert lib.csv_headers_safe(large, safe_read_bytes=16) == []


def _stage_minimal_inputs(tmp_path: Path, monkeypatch) -> Path:
    nodi_joint = tmp_path / "nodi" / "reports" / "joint_interface_20260628"
    nodi_joint.mkdir(parents=True)
    write_csv_rows(nodi_joint / "gate2d.csv", [{"context_only_acceptance_allowed": "true"} for _ in range(4)])
    write_csv_rows(nodi_joint / "nodi_fields.csv", [{"field_name": "formula_use_authorized"}, {"field_name": "route_key"}])
    write_csv_rows(nodi_joint / "nodi_state.csv", [{"workstream": "EDGE"}])
    monkeypatch.setattr(gate2s, "NODI_GATE2D_LEDGER", nodi_joint / "gate2d.csv")
    monkeypatch.setattr(gate2s, "NODI_RC1_FIELDS", nodi_joint / "nodi_fields.csv")
    monkeypatch.setattr(gate2s, "NODI_RC1_STATE", nodi_joint / "nodi_state.csv")
    monkeypatch.setattr(gate2s, "OUTPUT_DIR", nodi_joint)

    comsol = tmp_path / "comsol"
    roadmap = comsol / "roadmap"
    dwg = comsol / "full_chip" / "dwg_analysis"
    roadmap.mkdir(parents=True)
    dwg.mkdir(parents=True)
    write_csv_rows(roadmap / "COMSOL_GATE2_EDGE20_SAMPLE_20260628.csv", [{"edge20_bin_id": "edge_00", "template_only": "true", "not_evidence": "true"}])
    (roadmap / "COMSOL_GATE2_QCH_PACKET_20260628.md").write_text("QCH NO_FORMAL_QCH_SIDECAR_PRESENT\n", encoding="utf-8")
    write_csv_rows(dwg / "NODI_BINDING_GATE2_SAMPLE_20260628.csv", [{"diameter_nm": "220", "auto_map_authorized": "false"}])
    write_csv_rows(comsol / gate2s.COMSOL_RC1_FIELDS, [{"field_name": "formula_use_authorized"}, {"field_name": "edge20_bin_id"}])
    write_csv_rows(comsol / gate2s.COMSOL_RC1_STATE, [{"workstream": "EDGE"}, {"workstream": "QCH"}])
    validation_path = comsol / gate2s.COMSOL_RC1_VALIDATION
    write_csv_rows(validation_path, [{"check_id": "V1", "status": "PASS"}])
    manifest_rows = []
    for relative in (
        gate2s.COMSOL_RC1_FIELDS,
        gate2s.COMSOL_RC1_STATE,
        gate2s.COMSOL_RC1_VALIDATION,
        Path("roadmap/COMSOL_GATE2_EDGE20_SAMPLE_20260628.csv"),
        Path("roadmap/COMSOL_GATE2_QCH_PACKET_20260628.md"),
        Path("full_chip/dwg_analysis/NODI_BINDING_GATE2_SAMPLE_20260628.csv"),
    ):
        path = comsol / relative
        manifest_rows.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "row_count": str(len(gate2s.read_csv_rows(path))) if path.suffix == ".csv" else "0",
            }
        )
    write_csv_rows(comsol / gate2s.COMSOL_RC1_MANIFEST, manifest_rows)
    return comsol


def test_gate2s_to_gate2w_payload_and_no_auth_validation(tmp_path: Path, monkeypatch) -> None:
    comsol = _stage_minimal_inputs(tmp_path, monkeypatch)
    payload = gate2s.build_payload(comsol_root=comsol, census_limit=20)

    assert payload["gate2s_disposition"] == gate2s.GATE2S_PASS
    assert payload["mutation_total"] >= 80
    assert payload["mutation_unexpected_pass"] == 0
    assert payload["gate2d_accepted_row_count"] == 4
    assert any(row["candidate_workstream"] == "EDGE" for row in payload["census_rows"])
    assert gate2s.validate_payload(payload) == []

    payload["mutation_unexpected_pass"] = 1
    assert any("unexpected pass" in issue for issue in gate2s.validate_payload(payload))


def test_gate2s_manifest_and_auth_drift_detection(tmp_path: Path, monkeypatch) -> None:
    comsol = _stage_minimal_inputs(tmp_path, monkeypatch)
    payload = gate2s.build_payload(comsol_root=comsol, census_limit=20)
    payload["auth_drift_rows"][0]["drift_status"] = "FAIL_AUTHORIZATION_TRUE"
    assert any("authorization drift" in issue for issue in gate2s.validate_payload(payload))

    rows = gate2s.read_csv_rows(comsol / gate2s.COMSOL_RC1_MANIFEST)
    rows[0]["sha256"] = "bad"
    write_csv_rows(comsol / gate2s.COMSOL_RC1_MANIFEST, rows)
    payload = gate2s.build_payload(comsol_root=comsol, census_limit=20)
    assert payload["comsol_rc1_manifest_status"] == "PARTIAL"
