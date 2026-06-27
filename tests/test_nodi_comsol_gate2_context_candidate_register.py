from __future__ import annotations

from pathlib import Path

from nodi_simulator.nodi_comsol_next_artifacts import default_comsol_v4_readonly_context
from nodi_simulator.realism_v2_io import write_csv_rows
from tools.audits.build_nodi_comsol_gate2_context_candidate_register import (
    MISSING_SHA,
    PASS_STATUS,
    SCHEMA_VERSION,
    CandidateSpec,
    build_gate2_context_candidate_payload,
    validate_gate2_context_candidate_payload,
    validate_gate2_context_candidate_register_rows,
)


VALID_SHA = "a" * 64


def _register_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "register_row_id": "G2CTX-UNIT-001",
        "schema_version": SCHEMA_VERSION,
        "candidate_type": "TPD/PRS context proxy candidate",
        "source_artifact": "roadmap/unit_context.csv",
        "sha256": VALID_SHA,
        "row_count": "1",
        "producer": "COMSOL",
        "evidence_class": "unit_context_only",
        "route_key": "660/W800/D900",
        "diameter_basis": "300",
        "bin_basis": "edge_norm_1d",
        "claim_boundary": "context_only_not_detection",
        "allowed_use": "Gate2 context candidate review only",
        "blocked_use": (
            "PRS occupancy; q_ch*eta; chi_selected; route score; yield; winner; "
            "detection_probability; JOINT_ROUTE_CLASS"
        ),
        "required_next_gate": "formal Gate2 context review",
        "v4_context_binding": "not_v4_bound_chi_context_proxy",
        "candidate_status": "GATE2_CANDIDATE_CONTEXT_ONLY_REVIEWABLE",
        "grain_alignment_status": "MATCHED_CONTEXT_ONLY_NO_WEIGHTING",
        "matched_grain_count": "1",
        "blocked_grain_count": "0",
        "review_note": "unit context",
    }
    row.update(overrides)
    return row


def test_gate2_context_only_register_row_passes() -> None:
    assert validate_gate2_context_candidate_register_rows([_register_row()]) == []


def test_gate2_register_blocks_missing_qch_export_but_validates() -> None:
    row = _register_row(
        register_row_id="G2CTX-QCH-MISSING",
        candidate_type="q_ch / flow split candidate",
        source_artifact="UNAVAILABLE_FORMAL_QCH_FLOW_SPLIT_SIDECAR",
        sha256=MISSING_SHA,
        row_count="0",
        candidate_status="BLOCKED_MISSING_FORMAL_GATE2_EXPORT",
        grain_alignment_status="BLOCKED_NO_FORMAL_QCH_FLOW_SPLIT_ARTIFACT",
        matched_grain_count="0",
        blocked_grain_count="1",
        allowed_use="none beyond blocked-register documentation",
    )

    assert validate_gate2_context_candidate_register_rows([row]) == []


def test_gate2_register_rejects_forbidden_output_fields() -> None:
    row = _register_row(
        q_ch_eta_weighted_response="0.1",
        winner="route-a",
        detection_probability="0.2",
        JOINT_ROUTE_CLASS="JRC-001",
    )

    issues = validate_gate2_context_candidate_register_rows([row])

    assert any("q_ch_eta_weighted_response" in issue for issue in issues)
    assert any("winner" in issue for issue in issues)
    assert any("detection_probability" in issue for issue in issues)
    assert any("JOINT_ROUTE_CLASS" in issue for issue in issues)


def test_gate2_payload_rejects_v4_production_promotion() -> None:
    context = default_comsol_v4_readonly_context()
    context["nodi_production_ingestion_allowed"] = True
    payload = {
        "schema_version": "nodi_comsol_gate2_context_candidate_preflight_report_v1",
        "status": PASS_STATUS,
        "comsol_run_performed": False,
        "nodi_rerun_performed": False,
        "joint_route_class_generated": False,
        "q_ch_weighting_performed": False,
        "q_ch_eta_computed": False,
        "yield_computed": False,
        "winner_selected": False,
        "detection_probability_computed": False,
        "true_W_eff_claimed": False,
        "measured_geometry_claimed": False,
        "wet_pass_probability_computed": False,
        "clogging_rate_computed": False,
        "comsol_v4_context": context,
        "register_rows": [_register_row()],
        "blocked_grain_rows": [],
    }

    issues = validate_gate2_context_candidate_payload(payload)

    assert any("nodi_production_ingestion_allowed must remain false" in issue for issue in issues)


def test_gate2_builder_registers_route_diameter_bin_mismatch_as_blocked(
    tmp_path: Path,
) -> None:
    comsol_root = tmp_path / "comsol"
    source_dir = comsol_root / "roadmap"
    source_dir.mkdir(parents=True)
    source_path = source_dir / "unit_chi_bins.csv"
    write_csv_rows(
        source_path,
        [
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "220",
                "NODI_view": "fixed_660_gold",
                "prs_bin_count": "5",
                "claim_boundary": "chi_context_proxy_not_calibrated_not_detection",
            }
        ],
    )
    prs_path = tmp_path / "prs.csv"
    eas_path = tmp_path / "eas.csv"
    write_csv_rows(
        prs_path,
        [
            {
                "route_id_nodi": "660/W800/D900",
                "diameter_nm": "300",
                "NODI_view": "fixed_660_gold",
            }
        ],
    )
    write_csv_rows(
        eas_path,
        [
            {
                "route_id_nodi": "660/W800/D900",
                "NODI_view": "fixed_660_gold",
            }
        ],
    )
    spec = CandidateSpec(
        register_row_id="G2CTX-UNIT-MISMATCH",
        candidate_type="TPD/PRS context proxy candidate",
        source_artifact="roadmap/unit_chi_bins.csv",
        producer="COMSOL",
        evidence_class="unit_context_proxy",
        claim_boundary="chi_context_proxy_not_calibrated_not_detection",
        allowed_use="Gate2 context proxy review only",
        blocked_use="winner; detection_probability; JOINT_ROUTE_CLASS",
        required_next_gate="explicit blocked-grain review",
        v4_context_binding="not_v4_bound_chi_context_proxy",
        review_note="unit mismatch",
    )

    payload = build_gate2_context_candidate_payload(
        prs_rows=[{"route_id_nodi": "660/W800/D900", "diameter_nm": "300", "NODI_view": "fixed_660_gold"}],
        eas_rows=[{"route_id_nodi": "660/W800/D900", "NODI_view": "fixed_660_gold"}],
        comsol_root=comsol_root,
        prs_path=prs_path,
        eas_path=eas_path,
        candidate_specs=[spec],
    )

    assert payload["register_rows"][0]["candidate_status"] == "BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH"
    assert payload["blocked_grain_rows"]
    assert {
        row["alignment_status"] for row in payload["blocked_grain_rows"]
    } >= {
        "BLOCKED_MISSING_PRS_ROUTE_DIAMETER_VIEW_GRAIN",
        "REVIEW_ONLY_COARSE_TO_FINE_BIN_GROUP_NOT_DIRECT_PRS_BIN",
    }
    assert validate_gate2_context_candidate_payload(payload) == []
