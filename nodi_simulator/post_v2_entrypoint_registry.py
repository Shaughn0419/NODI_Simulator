"""Lifecycle registry for post-v2 generator and verifier entrypoints.

The post-v2 files look archival, but most are still imported by tests and
paired CLI wrappers. This registry makes that status explicit so cleanup work
can distinguish active review-package contracts from genuinely removable
scratch files.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostV2ModuleEntry:
    module: str
    lifecycle: str
    generator: str | None = None
    verifier: str | None = None
    notes: str = ""


POST_V2_MODULE_ENTRIES: tuple[PostV2ModuleEntry, ...] = (
    PostV2ModuleEntry(
        "post_v2_audit",
        "active_review_package_contract",
        notes="Mandatory audit writers are imported directly by tests and legacy generator wrappers.",
    ),
    PostV2ModuleEntry(
        "post_v2_physical_ceiling",
        "active_review_package_contract",
        generator="tools/generate_post_v2_physical_ceiling_contract_manifest.py",
        verifier="tools/verify_post_v2_physical_ceiling_contracts.py",
    ),
    PostV2ModuleEntry(
        "post_v2_bounded_physical_solver_readiness",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_bounded_physical_solver_readiness.py",
        verifier="tools/verify_post_v2_bounded_physical_solver_readiness.py",
    ),
    PostV2ModuleEntry(
        "post_v2_bounded_solver_authorization_pilot_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_bounded_solver_authorization_pilot_design.py",
        verifier="tools/verify_post_v2_bounded_solver_authorization_pilot_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_bounded_solver_dry_run_preflight",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_bounded_solver_dry_run_preflight.py",
        verifier="tools/verify_post_v2_bounded_solver_dry_run_preflight.py",
    ),
    PostV2ModuleEntry(
        "post_v2_bounded_solver_authorization_gate",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_bounded_solver_authorization_gate.py",
        verifier="tools/verify_post_v2_bounded_solver_authorization_gate.py",
    ),
    PostV2ModuleEntry(
        "post_v2_minimal_bounded_solver_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_minimal_bounded_solver_execution.py",
        verifier="tools/verify_post_v2_minimal_bounded_solver_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_second_lane_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_second_lane_authorization_design.py",
        verifier="tools/verify_post_v2_second_lane_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_second_bounded_solver_lane_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_second_bounded_solver_lane_execution.py",
        verifier="tools/verify_post_v2_second_bounded_solver_lane_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_p8_closure_p9_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_p8_closure_p9_authorization_design.py",
        verifier="tools/verify_post_v2_p8_closure_p9_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_third_bounded_solver_lane_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_third_bounded_solver_lane_execution.py",
        verifier="tools/verify_post_v2_third_bounded_solver_lane_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_p10_closure_p11_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_p10_closure_p11_authorization_design.py",
        verifier="tools/verify_post_v2_p10_closure_p11_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_fourth_bounded_solver_lane_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_fourth_bounded_solver_lane_execution.py",
        verifier="tools/verify_post_v2_fourth_bounded_solver_lane_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_p12_closure_p13_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_p12_closure_p13_authorization_design.py",
        verifier="tools/verify_post_v2_p12_closure_p13_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_fifth_bounded_solver_lane_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_fifth_bounded_solver_lane_execution.py",
        verifier="tools/verify_post_v2_fifth_bounded_solver_lane_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_p14_closure_p15_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_p14_closure_p15_authorization_design.py",
        verifier="tools/verify_post_v2_p14_closure_p15_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_sixth_bounded_solver_lane_execution",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_sixth_bounded_solver_lane_execution.py",
        verifier="tools/verify_post_v2_sixth_bounded_solver_lane_execution.py",
    ),
    PostV2ModuleEntry(
        "post_v2_p16_closure_p17_authorization_design",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_p16_closure_p17_authorization_design.py",
        verifier="tools/verify_post_v2_p16_closure_p17_authorization_design.py",
    ),
    PostV2ModuleEntry(
        "post_v2_bounded_lane_synthesis_stop_continue",
        "active_bounded_solver_program",
        generator="tools/generate_post_v2_bounded_lane_synthesis_stop_continue.py",
        verifier="tools/verify_post_v2_bounded_lane_synthesis_stop_continue.py",
    ),
)

POST_V2_AUDIT_GENERATORS: tuple[str, ...] = (
    "tools/generate_post_v2_bfp_roi_audit.py",
    "tools/generate_post_v2_candidate_universe.py",
    "tools/generate_post_v2_ev_audit.py",
    "tools/generate_post_v2_final_audit.py",
    "tools/generate_post_v2_noise_audit.py",
    "tools/generate_post_v2_p1_extensions.py",
    "tools/generate_post_v2_tsuyama_audit.py",
)


def indexed_post_v2_modules() -> frozenset[str]:
    return frozenset(entry.module for entry in POST_V2_MODULE_ENTRIES)


def indexed_post_v2_tools() -> frozenset[str]:
    return frozenset(
        path
        for entry in POST_V2_MODULE_ENTRIES
        for path in (entry.generator, entry.verifier)
        if path is not None
    ) | frozenset(POST_V2_AUDIT_GENERATORS)
