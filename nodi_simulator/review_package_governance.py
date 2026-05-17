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
        "Report 88 is the current full-data reader-facing analysis. From v5.0 (2026-05-11) onward "
        "it is a **reader-centric full restructure**: rather than layering amendments on top of v3.0 / "
        "v4.0 / v4.1 / v4.2, v5.0 reorganizes the content into a problem → physics → variables → "
        "data → analysis → recommendations → boundaries → provenance narrative. It carries "
        "**two parallel reader lenses of equal priority**:\n\n"
        "- 口径 A — all-crossing engineering main route (§10 recommendation; data in §6.4 表 6.4.A; "
        "provenance in §17.1)\n"
        "- 口径 B — selected-annulus Tsuyama-anchored EV application framework (§11 recommendation; "
        "B1 anchor target-fitting in §11.2–§11.3; B2 EV+gold full-grid application in §11.3–§11.8; "
        "raw provenance in §17.2)\n\n"
        "§12 is the dual-lens integration. Neither lens supersedes the other; supersession entries below "
        "name v5.0+ as the current consolidation target. From report 88 v5.2.6 onward, lens B must be "
        "read as B1 Tsuyama Au/Ag anchor target-fitting plus B2 frozen-B-lens EV+gold full-grid "
        "application. B2 is now completed for one seed (`seed=42`, `10000 events/case`, `32,032 rows`): "
        "EV recommendations use EV/exosome rows only, gold rows are anchor / Tsuyama diagnostics only, "
        "488/532 remain trend/control in recommendation conclusions, and 660/404 are the only "
        "recommendation-eligible wavelengths. Raw comparison tables and figures remain unfiltered. "
        "Current B2 full-grid interpretation is one-seed synthetic relative evidence, not 3-seed "
        "consensus or calibrated SNR/LOD.\n\n"
        "| historical_report_path | superseded_by | supersession_reason | current_claim_level |\n"
        "|---|---|---|---|\n"
        "| reports/47_EV_NODI全量结果分层分析报告.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.2.6) | Report 47 remains the historical all-crossing full-grid analysis; report 88 v5.2.6 is the current full-data reader report after merging realism v2, post-v2 P0-P18, and the selected-annulus Tsuyama-anchored EV+gold full-grid application lens, reorganized into a reader-centric narrative. | current_truth_in_report_88_v5_2_6_dual_lens |\n"
        "| reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.2.6) §11 + §17.2 | Report 49 remains raw provenance for the Tsuyama Phase 2 / Phase 2.5-2.11 selected-annulus B1 target-fitting lane; B2 EV full-grid provenance is now `results/lens_b_ev_gold_fullgrid_1seed_20260513/`, and reader-facing conclusions are consolidated into report 88 v5.2.6 §11 as B1 anchor diagnostics plus B2 EV-only full-grid recommendation filtering. | selected_annulus_anchor_target_fitting_and_b2_fullgrid_provenance |\n"
        "| reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.0) §12.2 | Report 71 remains raw provenance for the R5.2 bounded scenario-prior audit and selected-annulus / 404 sidecar guardrail; its reader-facing conclusions are now consolidated into report 88 v5.0 §12.2 (dual-lens evidence comparison). | selected_annulus_sidecar_guardrail_provenance |\n"
        "| reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.0) §12.2 | R5.2 external-review plan is stage provenance; reader-facing conclusions are consolidated into report 88 v5.0 §12.2. | selected_annulus_sidecar_guardrail_provenance |\n"
        "| reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md | results/post_v2_mandatory_audit/ | P0 package and mandatory audit artifacts are now generated and tested. | no_measured_data_relative_audit_only |\n"
        "| reports/9[1-9]_*.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.0) | P1/P2 stage reports are now historical and consolidated into report 88 v5.0 (lens-A study design §5.3 + recommendation §10). | trace_only_provenance |\n"
        "| reports/1[0-1][0-9]_*.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.0) | P3-P18 stage reports remain provenance for authorization and bounded trace lanes; their conclusions are consolidated into report 88 v5.0 (§5.3 study design + §10.5 governance ledger). | trace_only_provenance |\n"
        "| reports/120_*.md | reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md (v5.0) | P120 trace/design report is stage provenance; conclusions are consolidated into report 88 v5.0 (§5.3 + §10.5). | trace_only_provenance |\n"
        "| reports/[0-8][0-9]_*.md | REVIEW_PACKAGE_MANIFEST.json | Frozen historical notes remain advisory and are superseded for current claims by the review package manifest. Reports 49 and 71 are the exceptions: they remain selected-annulus / R5.2 raw provenance for report 88 v5.0 §11 + §17.2 and §12.2 respectively. | frozen_history_advisory_only |\n",
        encoding="utf-8",
    )
    outputs.append(supersession_path)
    return outputs
