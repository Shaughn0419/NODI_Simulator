from __future__ import annotations

from nodi_simulator.pressure_flow_validation import (
    PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY,
    build_pressure_flow_comparison_rows,
    context_row_from_comsol_summary,
)


def _qch_rows() -> list[dict[str, str]]:
    return [
        {
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_sidecar_status": "candidate_qch_sidecar_row",
            "source_case_id": "rectangle_limit_theta90_D900_W500",
            "pressure_drop_Pa": "1000",
            "q_ch_candidate_m3_s": "1e-15",
        },
        {
            "qch_sidecar_id": "QCH-CAND-002",
            "qch_sidecar_status": "candidate_qch_sidecar_row",
            "source_case_id": "taper_theta85_D900_W500",
            "pressure_drop_Pa": "1000",
            "q_ch_candidate_m3_s": "2e-15",
        },
        {
            "qch_sidecar_id": "QCH-CAND-003",
            "qch_sidecar_status": "blocked_source_solver_not_open",
            "source_case_id": "closed_theta70_D900_W500",
            "pressure_drop_Pa": "1000",
            "q_ch_candidate_m3_s": "0",
        },
    ]


def test_context_row_from_comsol_summary_normalizes_pressure_flow() -> None:
    row = context_row_from_comsol_summary(
        {
            "p_top_left_pa": "5000",
            "p_out_pa": "0",
            "q_upper_ports_m3_s": "5e-15",
            "q_lower_ports_m3_s": "4e-15",
            "port_balance_rel": "0.001",
            "quality_gate": "pass",
        },
        comsol_context_id="sw85_d0p9_w800",
        source_match_level="geometry_family_context_only",
        sidewall_deg_comsol=85.0,
        depth_nm=900.0,
        top_width_nm=800.0,
        route_family="p1b_w800",
    )

    assert row["pressure_drop_Pa"] == 5000.0
    assert row["comsol_reference_flow_m3_s"] == 9e-15
    assert row["quality_gate"] == "pass"
    assert row["source_match_level"] == "geometry_family_context_only"


def test_geometry_family_context_does_not_promote_formal_qch() -> None:
    context = [
        {
            "comsol_context_id": "sw85_d0p9_w800",
            "source_match_level": "geometry_family_context_only",
            "sidewall_deg_comsol": "85.0",
            "pressure_drop_Pa": "5000",
            "comsol_reference_flow_m3_s": "9e-15",
            "quality_gate": "pass",
        }
    ]
    rows = build_pressure_flow_comparison_rows(_qch_rows(), context)

    assert len(rows) == 2
    tapered = rows[1]
    assert tapered.qch_source_case_id == "taper_theta85_D900_W500"
    assert tapered.validation_status == "context_only_not_formal_validation"
    assert tapered.formal_qch_sidecar_current is False
    assert tapered.route_score_current is False
    assert tapered.claim_boundary == PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY


def test_exact_context_can_be_marked_formal_validation_candidate_without_route_claim() -> None:
    context = [
        {
            "comsol_context_id": "exact_w500_d900_theta85",
            "source_match_level": "exact_geometry_and_route",
            "sidewall_deg_comsol": "85.0",
            "pressure_drop_Pa": "5000",
            "comsol_reference_flow_m3_s": "1.0e-14",
            "quality_gate": "pass",
        }
    ]
    rows = build_pressure_flow_comparison_rows(_qch_rows()[1:2], context)

    assert rows[0].validation_status == "formal_validation_candidate"
    assert rows[0].formal_qch_sidecar_current is False
    assert rows[0].route_score_current is False
    assert rows[0].winner_current is False
    assert rows[0].yield_detection_probability_current is False
