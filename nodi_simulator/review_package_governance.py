"""Generated P1 governance files for the review package."""

from __future__ import annotations

from pathlib import Path

from .realism_v2_io import sha256_file, write_json_atomic
from .review_package_json import load_json_compatible as _load_json_compatible
from .review_package_v1 import V1_SUMMARY_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REASON_CODE_VOCABULARY: tuple[dict[str, str], ...] = (
    {"code": "BFP.RANK_SHIFT_MAJOR", "module": "BFP", "meaning": "BFP rank-percentile shift exceeds the pinned major threshold."},
    {"code": "PAIRWISE.RELATIVE_ORDER_DISAGREEMENT", "module": "PAIRWISE", "meaning": "One or more relative audit lenses disagree with scalar ordering."},
    {"code": "TSUYAMA.EXTRAPOLATED_GEOMETRY", "module": "TSUYAMA", "meaning": "Tsuyama phase-filter lane is outside paper geometry."},
    {"code": "NOISE.RELATIVE_FRAGILE", "module": "NOISE", "meaning": "Route rank-percentile is unstable versus the nominal R5 scenario."},
    {"code": "EV.SAMPLE_UNKNOWN", "module": "EV", "meaning": "EV sample profile is unknown and cannot support clean-main promotion."},
    {"code": "CLAIM.CALIBRATED_BLOCKED", "module": "CLAIM", "meaning": "Calibrated or absolute claim remains blocked."},
)

ROUTE_ROLE_INITIAL_VALUES: tuple[str, ...] = (
    "main_locked",
    "weak_reference_control",
    "optional_robustness_probe",
    "historical_v1_main",
    "shortwave_probe",
    "paper_proxy_sanity",
    "paper_sanity_audit_only",
    "context_route",
    "warning_route",
)

ROUTE_ROLE_FINAL_VALUES: tuple[str, ...] = (
    "relative_main_candidate",
    "relative_control_candidate",
    "optional_robustness_probe_only",
    "probe_only",
    "paper_sanity_only",
    "surrogate_sensitive_not_promoted",
    "audit_incomplete_blocked",
)


def write_p1_governance_files(project_root: Path = PROJECT_ROOT) -> list[Path]:
    outputs: list[Path] = []
    reason_path = project_root / "configs/realism_v2/reason_code_vocabulary.yaml"
    write_json_atomic(
        reason_path,
        {
            "schema": "ev_nodi_reason_code_vocabulary_v1",
            "code_pattern": "^[A-Z_]+\\.[A-Z0-9_]+$",
            "legacy_underscore_codes_allowed": False,
            "reason_codes": list(REASON_CODE_VOCABULARY),
        },
        sort_keys=True,
    )
    outputs.append(reason_path)
    role_path = project_root / "configs/realism_v2/route_role_vocabulary.yaml"
    write_json_atomic(
        role_path,
        {
            "schema": "ev_nodi_route_role_vocabulary_v1",
            "route_role_initial": list(ROUTE_ROLE_INITIAL_VALUES),
            "route_role_final": list(ROUTE_ROLE_FINAL_VALUES),
        },
        sort_keys=True,
    )
    outputs.append(role_path)
    ev_profiles_path = project_root / "configs/realism_v2/ev_sample_profiles.yaml"
    write_json_atomic(
        ev_profiles_path,
        {
            "schema": "ev_nodi_ev_sample_profiles_v1",
            "claim_level": "relative_sample_uncertainty_profiles_only",
            "profiles": {
                "unknown": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "IEX_MSC_EV": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "UF_MSC_EV": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "PEG_like": {"min_risk_label": "high", "biological_specificity_claim_allowed": False},
                "SEC_like": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
            },
        },
        sort_keys=True,
    )
    outputs.append(ev_profiles_path)
    noise_path = project_root / "configs/realism_v2/noise_readout_scenario_bundle.yaml"
    r5_manifest = _load_json_compatible(project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml")
    scenario_ids = [row["scenario_id"] for row in r5_manifest["scenario_bundles"]]
    write_json_atomic(
        noise_path,
        {
            "schema": "ev_nodi_noise_readout_scenario_bundle_v1",
            "extends_scenario_bundle_id": r5_manifest["schema_version"],
            "source_scenario_manifest_path": "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
            "source_scenario_manifest_sha256": sha256_file(project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml"),
            "required_scenario_ids": scenario_ids,
            "scenario_alias_map": {},
            "forked_scenario_ids_allowed": False,
            "pass_criterion_id": "relative_rank_percentile_stability_vs_nominal_v1",
        },
        sort_keys=True,
    )
    outputs.append(noise_path)
    v1_pin_path = project_root / "configs/realism_v2/v1_summary_hash_pin.json"
    if not v1_pin_path.exists():
        write_json_atomic(
            v1_pin_path,
            {
                "schema": "ev_nodi_v1_summary_hash_pin_v1",
                "summary_csv_path": V1_SUMMARY_PATH,
                "summary_csv_sha256": sha256_file(project_root / V1_SUMMARY_PATH),
                "approved_v1_summary_drift_evidence_path": None,
                "drift_without_evidence_blocks_release": True,
            },
            sort_keys=True,
        )
    outputs.append(v1_pin_path)
    supersession_path = project_root / "HISTORICAL_REPORT_SUPERSESSION.md"
    supersession_path.write_text(
        "# Historical Report Supersession\n\n"
        "Reports 140, 147, and 148 are the current no-data closure set. "
        "Report 140 is the reader-facing Lens-B EV+gold 3seed × 10000e full-grid post-run analysis, "
        "while reports 147/148 define the narrowed sealing gate and Stage-1/T3/T4 audit closure. "
        "Report 88 remains the consolidated v1/v2/post-v2 background analysis, but its Lens-B "
        "B6/B7 single-seed language is now superseded/qualified by the 140/147/148 closure set. From report 88 "
        "v5.0 (2026-05-11) onward it is a **reader-centric full restructure**: rather than layering amendments on top of v3.0 / "
        "v4.0 / v4.1 / v4.2, v5.0 reorganizes the content into a problem → physics → variables → "
        "data → analysis → recommendations → boundaries → provenance narrative. It carries "
        "**two parallel reader lenses of equal priority**:\n\n"
        "- 口径 A — all-crossing engineering main route (§10 recommendation; data in §6.4 表 6.4.A; "
        "provenance in §17.1)\n"
        "- 口径 B — selected-annulus Tsuyama-anchored EV application framework (§11 recommendation; "
        "B1 anchor target-fitting in §11.2–§11.3; B2 EV+gold full-grid application in §11.3–§11.8; "
        "raw provenance in §17.2)\n\n"
        "§12 is the dual-lens integration. Neither historical lens supersedes the other. For current Lens-B B2, "
        "use reports 140/147/148: `fixed_660_gold` and `per_wavelength_gold` are normalization views over shared "
        "physical events, not independent physical event campaigns. EV recommendations use EV/exosome "
        "rows only, gold rows are anchor / Tsuyama diagnostics only, 488/532 remain trend/control in "
        "recommendation conclusions, and the current conclusion is `404/W500` fixed-view candidate plus "
        "`660/W800` per-wavelength-view candidate with no detector-resolved or absolute winner. Raw "
        "comparison tables and figures remain unfiltered. Current interpretation is still no-measured-data "
        "Level-1 relative/proxy evidence only; R1 and C/D×V2 are deferred outside the narrowed gate.\n\n"
        "| historical_report_path | superseded_by | supersession_reason | current_claim_level |\n"
        "|---|---|---|---|\n"
        "| reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md §11 Lens-B B6/B7 language | reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md + reports/147_* + reports/148_* | Report 88 remains historical background, but its one-seed 1000e Lens-B overlay is superseded for current no-data closure by the shared-dual 3seed × 10000e post-run analysis and Stage-1 audit. | no_measured_data_level1_relative_proxy |\n"
        "| reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md | reports/140_* + reports/147_* + reports/148_* | Report 100 remains historical B6/B7 method provenance; the current conclusion is dual candidate families under detector surrogate, not a single route winner. | historical_single_seed_method_overlay |\n"
        "| reports/47_EV_NODI全量结果分层分析报告.md | reports/140_* + reports/147_* + reports/148_* | Report 47 remains the historical all-crossing full-grid analysis; report 140 is the current reader-facing full-grid conclusion and reports 147/148 define the sealing/audit boundary. | historical_all_crossing_background |\n"
        "| reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md | reports/140_* + reports/147_* + reports/148_* | Report 49 remains raw provenance for the Tsuyama Phase 2 / Phase 2.5-2.11 selected-annulus B1 target-fitting lane; current reader-facing conclusions are no-data candidate-family closure. | selected_annulus_anchor_target_fitting_provenance |\n"
        "| reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md | reports/140_* + reports/147_* + reports/148_* | Report 71 remains raw provenance for the R5.2 bounded scenario-prior audit and selected-annulus guardrail; current conclusions are no-data candidate-family closure. | selected_annulus_guardrail_provenance |\n"
        "| reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md | reports/140_* + reports/147_* + reports/148_* | R5.2 external-review plan is stage provenance; current reader-facing closure is in reports 140/147/148. | selected_annulus_guardrail_provenance |\n"
        "| reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md | results/post_v2_mandatory_audit/ | P0 package and mandatory audit artifacts are now generated and tested. | no_measured_data_relative_audit_only |\n"
        "| reports/9[1-9]_*.md | reports/140_* + reports/147_* + reports/148_* | P1/P2 stage reports are historical provenance; their background was consolidated through report 88 and is now superseded for current closure by reports 140/147/148. | trace_only_provenance |\n"
        "| reports/1[0-1][0-9]_*.md | reports/140_* + reports/147_* + reports/148_* | P3-P18 stage reports remain provenance for authorization and bounded trace lanes; current closure wording belongs to reports 140/147/148. | trace_only_provenance |\n"
        "| reports/120_*.md | reports/140_* + reports/147_* + reports/148_* | P120 trace/design report is stage provenance; current closure wording belongs to reports 140/147/148. | trace_only_provenance |\n"
        "| reports/[0-8][0-9]_*.md | REVIEW_PACKAGE_MANIFEST.json + reports/140_* + reports/147_* + reports/148_* | Frozen historical notes remain advisory and are superseded for current claims by the review package manifest and current no-data closure. Reports 49 and 71 remain raw provenance only. | frozen_history_advisory_only |\n",
        encoding="utf-8",
    )
    outputs.append(supersession_path)
    return outputs
