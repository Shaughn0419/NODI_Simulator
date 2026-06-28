from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows
from tools.audits import build_nodi_comsol_gate2d_reduced_scope_acceptance_preflight as gate2d


ACTUAL_COUNTS = {
    "BLOCKED_220NM_NO_DIRECT_MATCH": 72,
    "BLOCKED_D1200_EXACT_GRAIN_UNCERTAIN": 36,
    "BLOCKED_UNBOUND_NODI_VIEW": 16,
    "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED": 4,
    "REVIEW_ONLY_EDGE_POLICY_REQUIRED": 16,
    "QUARANTINE_QCH_PROVENANCE_ONLY": 1,
}
DRIFTED_MASTER_COUNTS = {
    "BLOCKED_220NM_NO_DIRECT_MATCH": 40,
    "BLOCKED_D1200_EXACT_GRAIN_UNCERTAIN": 4,
    "BLOCKED_UNBOUND_NODI_VIEW": 64,
    "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED": 4,
    "REVIEW_ONLY_EDGE_POLICY_REQUIRED": 32,
    "QUARANTINE_QCH_PROVENANCE_ONLY": 1,
}


def _candidate_row(row_id: int, status: str, **overrides: str) -> dict[str, str]:
    row = {
        "candidate_export_row_id": f"G2C-CAND-{row_id:04d}",
        "gate2c_alignment_row_id": f"G2C-ALIGN-{row_id:04d}",
        "source_family": "TPD_PRS_PROXY_AGG",
        "source_artifact": "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
        "source_sha256": "a" * 64,
        "source_row_count": "16",
        "source_row_identity": f"ROW_{row_id}",
        "candidate_status": status,
        "route_key_candidate": "660/W800/D900",
        "NODI_view": "fixed_660_gold",
        "diameter_nm": "300",
        "bin_basis": "aggregate_proxy",
        "edge4_to_edge20_policy": "aggregate_proxy_not_direct_prs_bin",
        "PRS_exact_match_claim": "false_NODI_DECISION_REQUIRED",
        "artifact_level_context_candidate": "true",
        "grain_level_ingestion_authorized": "false",
        "qch_weighting_authorized": "false",
        "jrc_authorized": "false",
        "chi_selected_authorized": "false",
        "production_ingestion_authorized": "false",
        "runtime_configuration_authorized": "false",
        "allowed_use": "NODI review candidate/read-only context triage only",
        "blocked_use": "chi_selected; q_ch weighting; JRC; winner; yield; detection_probability",
        "required_next_gate": "NODI_PRS_HASH_COVERAGE_CONFIRMATION_GATE",
    }
    row.update(overrides)
    return row


def _candidate_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    reduced_specs = [
        ("fixed_660_gold", "residence_time_weighted"),
        ("fixed_660_gold", "velocity_weighted"),
        ("per_wavelength_gold", "residence_time_weighted"),
        ("per_wavelength_gold", "velocity_weighted"),
    ]
    row_id = 1
    for view, basis in reduced_specs:
        rows.append(
            _candidate_row(
                row_id,
                "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED",
                NODI_view=view,
                source_row_identity=f"CHI_CTX_AGG_660/W800/D900_A85_300_{view}_{basis}",
            )
        )
        row_id += 1
    for status, count in ACTUAL_COUNTS.items():
        if status == "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED":
            continue
        for _ in range(count):
            overrides: dict[str, str] = {}
            if status == "BLOCKED_220NM_NO_DIRECT_MATCH":
                overrides["diameter_nm"] = "220"
            elif status == "BLOCKED_D1200_EXACT_GRAIN_UNCERTAIN":
                overrides["route_key_candidate"] = "660/W800/D1200"
            elif status == "BLOCKED_UNBOUND_NODI_VIEW":
                overrides["NODI_view"] = "UNBOUND"
                overrides["source_family"] = "TPD_SOURCE"
            elif status == "REVIEW_ONLY_EDGE_POLICY_REQUIRED":
                overrides["bin_basis"] = "edge4_to_prs_edge20_proxy"
                overrides["source_family"] = "TPD_PRS_PROXY_BIN"
            elif status == "QUARANTINE_QCH_PROVENANCE_ONLY":
                overrides["source_family"] = "QCH_PROVENANCE"
            rows.append(_candidate_row(row_id, status, **overrides))
            row_id += 1
    assert len(rows) == 145
    return rows


def _master_text(counts: dict[str, int]) -> str:
    lines = [
        "# COMSOL Gate2C Binding Schema Alignment Master Packet - 2026-06-28",
        "",
        "## NODI-Bound Export Candidate Summary",
        "",
        "Candidate export rows: 145.",
        "",
    ]
    lines += [f"- `{status}`: {count}" for status, count in counts.items()]
    lines += ["", "## Validation Summary", "", "No validation check failed."]
    return "\n".join(lines) + "\n"


def _stage_inputs(tmp_path: Path, *, errata: bool = False) -> tuple[Path, Path, Path, Path]:
    comsol_root = tmp_path / "comsol"
    roadmap = comsol_root / "roadmap"
    roadmap.mkdir(parents=True)
    files: dict[str, Path] = {}
    files["master"] = roadmap / "COMSOL_GATE2C_BINDING_ALIGNMENT_MASTER_PACKET_20260628.md"
    files["master"].write_text(_master_text(DRIFTED_MASTER_COUNTS), encoding="utf-8")
    files["candidate"] = roadmap / "COMSOL_GATE2C_NODI_BOUND_CONTEXT_EXPORT_CANDIDATE_20260628.csv"
    write_csv_rows(files["candidate"], _candidate_rows())
    files["validation"] = roadmap / "COMSOL_GATE2C_BINDING_ALIGNMENT_VALIDATION_20260628.csv"
    write_csv_rows(
        files["validation"],
        [
            {
                "check_id": "G2C-VAL-006",
                "check_name": "candidate_export_status_coverage",
                "status": "PASS_BLOCKED_AS_EXPECTED",
                "observed": str(ACTUAL_COUNTS),
                "expected": "candidate statuses",
                "notes": "unit",
            }
        ],
    )
    for name, rows in {
        "COMSOL_GATE2C_REDUCED_SCOPE_DECISION_TABLE_20260628.csv": [{"decision": "unit"}],
        "COMSOL_GATE2C_TPD_BINDING_SCHEMA_ALIGNMENT_20260628.csv": [{"alignment": "unit"}],
    }.items():
        write_csv_rows(roadmap / name, rows)
    if errata:
        (roadmap / "COMSOL_GATE2C_BINDING_ALIGNMENT_ERRATA_20260628.md").write_text("errata\n", encoding="utf-8")
    manifest_rows = []
    for _role, relative in gate2d.COMSOL_FILES.items():
        path = comsol_root / relative
        if path.name == "COMSOL_GATE2C_BINDING_ALIGNMENT_MANIFEST_20260628.csv":
            continue
        manifest_rows.append(
            {
                "package_id": path.stem,
                "manifest_role": "unit",
                "path": relative.as_posix(),
                "row_count": str(len(gate2d.read_csv_rows(path))) if path.suffix == ".csv" else "0",
                "sha256": sha256_file(path),
                "status": "PASS",
                "notes": "unit",
            }
        )
    write_csv_rows(roadmap / "COMSOL_GATE2C_BINDING_ALIGNMENT_MANIFEST_20260628.csv", manifest_rows)

    nodi_dir = tmp_path / "nodi"
    nodi_dir.mkdir()
    prs = nodi_dir / "prs_verdict.csv"
    write_csv_rows(
        prs,
        [
            {
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
                "source_row_type": "proxy_aggregate",
                "exact_grain_present": "true",
                "coverage_verdict": "EXACT_GRAIN_PRESENT_CONTEXT_ONLY_REVIEW",
                "matched_prs_row_count": "467",
                "evidence_hash": "p" * 64,
            },
            {
                "route_key": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "per_wavelength_gold",
                "source_row_type": "proxy_aggregate",
                "exact_grain_present": "true",
                "coverage_verdict": "EXACT_GRAIN_PRESENT_CONTEXT_ONLY_REVIEW",
                "matched_prs_row_count": "467",
                "evidence_hash": "p" * 64,
            },
        ],
    )
    acceptance = nodi_dir / "acceptance.csv"
    allowed = nodi_dir / "allowed.csv"
    parent_child = nodi_dir / "parent_child.csv"
    report201 = nodi_dir / "report201.md"
    write_csv_rows(acceptance, [{"status": "PASS"}])
    write_csv_rows(allowed, [{"status": "PASS"}])
    write_csv_rows(parent_child, [{"status": "PASS"}])
    report201.write_text("PASS_GATE2C_REQUIREMENT_REVIEW_EVIDENCE_STABILIZED_NO_WEIGHTING_NO_JRC\n", encoding="utf-8")
    return comsol_root, prs, acceptance, allowed, parent_child, report201


def test_gate2d_detects_master_count_drift_and_requires_errata(tmp_path: Path) -> None:
    comsol_root, prs, acceptance, allowed, parent_child, report201 = _stage_inputs(tmp_path)
    payload = gate2d.build_gate2d_payload(
        comsol_root=comsol_root,
        output_dir=tmp_path / "out",
        nodi_prs_verdict_path=prs,
        nodi_acceptance_path=acceptance,
        nodi_allowed_acceptance_path=allowed,
        nodi_parent_child_path=parent_child,
        nodi_report_201_path=report201,
    )

    assert payload["status"] == gate2d.PARTIAL_STATUS
    assert payload["comsol_errata_exists"] is False
    assert payload["actual_candidate_status_counts"] == ACTUAL_COUNTS
    assert any(row["reconciliation_status"] == "FAIL_MASTER_PACKET_COUNT_DRIFT_REQUIRES_COMSOL_ERRATA" for row in payload["status_reconciliation_rows"])
    assert gate2d.validate_gate2d_payload(payload) == []


def test_gate2d_identifies_only_four_reduced_scope_rows(tmp_path: Path) -> None:
    comsol_root, prs, acceptance, allowed, parent_child, report201 = _stage_inputs(tmp_path)
    payload = gate2d.build_gate2d_payload(
        comsol_root=comsol_root,
        output_dir=tmp_path / "out",
        nodi_prs_verdict_path=prs,
        nodi_acceptance_path=acceptance,
        nodi_allowed_acceptance_path=allowed,
        nodi_parent_child_path=parent_child,
        nodi_report_201_path=report201,
    )

    rows = payload["reduced_scope_candidate_rows"]
    assert len(rows) == 4
    assert {row["route_key"] for row in rows} == {"660/W800/D900"}
    assert {row["diameter_nm"] for row in rows} == {"300"}
    assert {row["bin_basis"] for row in rows} == {"aggregate_proxy"}
    assert {row["tpd_proxy_aggregation_basis"] for row in rows} == {"velocity_weighted", "residence_time_weighted"}
    assert all(row["can_enter_context_only_acceptance_ledger"] == "false" for row in rows)
    assert all(row["acceptance_status"] == "PENDING_COMSOL_GATE2C_ERRATA_PRS_COVERAGE_PRESENT" for row in rows)


def test_gate2d_forbidden_flags_hard_fail(tmp_path: Path) -> None:
    comsol_root, prs, acceptance, allowed, parent_child, report201 = _stage_inputs(tmp_path)
    payload = gate2d.build_gate2d_payload(
        comsol_root=comsol_root,
        output_dir=tmp_path / "out",
        nodi_prs_verdict_path=prs,
        nodi_acceptance_path=acceptance,
        nodi_allowed_acceptance_path=allowed,
        nodi_parent_child_path=parent_child,
        nodi_report_201_path=report201,
    )

    bad_payload = dict(payload)
    bad_payload["reduced_scope_candidate_rows"] = [
        dict(payload["reduced_scope_candidate_rows"][0], can_enter_weighting="true")
    ]
    assert any("forbidden flag can_enter_weighting" in issue for issue in gate2d.validate_gate2d_payload(bad_payload))


def test_gate2d_cli_writes_partial_report(tmp_path: Path, capsys) -> None:
    comsol_root, prs, acceptance, allowed, parent_child, report201 = _stage_inputs(tmp_path)
    original_paths = (
        gate2d.NODI_GATE2C_PRS_VERDICT,
        gate2d.NODI_GATE2C_ACCEPTANCE,
        gate2d.NODI_GATE2C_ALLOWED_ACCEPTANCE,
        gate2d.NODI_GATE2C_PARENT_CHILD,
        gate2d.NODI_REPORT_201,
    )
    try:
        gate2d.NODI_GATE2C_PRS_VERDICT = prs
        gate2d.NODI_GATE2C_ACCEPTANCE = acceptance
        gate2d.NODI_GATE2C_ALLOWED_ACCEPTANCE = allowed
        gate2d.NODI_GATE2C_PARENT_CHILD = parent_child
        gate2d.NODI_REPORT_201 = report201
        result = gate2d.main(
            [
                "--confirm-gate2d-acceptance-preflight",
                "--comsol-root",
                str(comsol_root),
                "--output-dir",
                str(tmp_path / "out"),
                "--report-dir",
                str(tmp_path / "reports"),
            ]
        )
    finally:
        (
            gate2d.NODI_GATE2C_PRS_VERDICT,
            gate2d.NODI_GATE2C_ACCEPTANCE,
            gate2d.NODI_GATE2C_ALLOWED_ACCEPTANCE,
            gate2d.NODI_GATE2C_PARENT_CHILD,
            gate2d.NODI_REPORT_201,
        ) = original_paths

    captured = capsys.readouterr()
    assert result == 0
    assert gate2d.PARTIAL_STATUS in captured.out
    assert (tmp_path / "out" / gate2d.REPORT_JSON).exists()
    assert (tmp_path / "reports" / gate2d.REPORT_202).exists()
