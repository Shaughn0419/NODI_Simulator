"""P0a review-package scaffolding for the post-v2 relative audit.

The helpers in this module deliberately package no-measured-data audit
evidence. They do not convert v2 sidecars into calibration artifacts.
"""

from __future__ import annotations

import json
import platform
import sys
import zipfile
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .realism_v2_io import sha256_file, write_json_atomic
from .review_package_claims import (
    ClaimFinding as ClaimFinding,
    build_forbidden_claims_lexicon as build_forbidden_claims_lexicon,
    claim_scan_paths as claim_scan_paths,
    claim_text_passes as claim_text_passes,
    load_forbidden_claims_lexicon as load_forbidden_claims_lexicon,
    scan_claim_files as scan_claim_files,
    scan_forbidden_claims as scan_forbidden_claims,
    write_forbidden_claims_lexicon as write_forbidden_claims_lexicon,
)
from .review_package_audit_schema import (
    AUDIT_SCHEMA_COLUMNS as AUDIT_SCHEMA_COLUMNS,
    POST_V2_GENERATED_ROLES as POST_V2_GENERATED_ROLES,
    V1_SOURCE_FIELD_MAPPING as V1_SOURCE_FIELD_MAPPING,
    build_audit_schema_manifest as build_audit_schema_manifest,
    write_audit_schema_manifest as write_audit_schema_manifest,
)
from .review_package_docs import (
    write_review_package_readme as write_review_package_readme,
    write_schema_docs as write_schema_docs,
)
from .review_package_git import (
    git_commit as git_commit,
    git_commit_is_ancestor as git_commit_is_ancestor,
    git_dirty as git_dirty,
    git_tracked_paths as git_tracked_paths,
)
from .review_package_governance import (
    REASON_CODE_VOCABULARY as REASON_CODE_VOCABULARY,
    ROUTE_ROLE_FINAL_VALUES as ROUTE_ROLE_FINAL_VALUES,
    ROUTE_ROLE_INITIAL_VALUES as ROUTE_ROLE_INITIAL_VALUES,
    write_p1_governance_files as write_p1_governance_files,
)
from .review_package_json import (
    load_json_compatible as _load_json_compatible,
    stable_json_bytes as stable_json_bytes,
)
from .review_package_papers import (
    ensure_paper_overrides as ensure_paper_overrides,
    generate_paper_provenance as generate_paper_provenance,
    load_paper_overrides as load_paper_overrides,
    paper_id_for_path as paper_id_for_path,
    scan_paper_files as scan_paper_files,
    validate_paper_overrides as validate_paper_overrides,
)
from .review_package_paths import normalize_relpath as normalize_relpath
from .review_package_v1 import (
    V1_REQUIRED_BOUNDARY_FIELDS as V1_REQUIRED_BOUNDARY_FIELDS,
    V1_SUMMARY_PATH as V1_SUMMARY_PATH,
    count_csv_data_rows as count_csv_data_rows,
    csv_header as csv_header,
    v1_hash_drift_is_authorized as v1_hash_drift_is_authorized,
    v1_summary_contract as v1_summary_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POST_V2_AUDIT_DIR = Path("results/post_v2_mandatory_audit")
PAPER_PROVENANCE_DIR = Path("papers/provenance")

CALIBRATION_SCAFFOLD_FILES: tuple[str, ...] = (
    "calibration/bfp_roi_mask_template.json",
    "calibration/blank_false_positive_template.csv",
    "calibration/blank_false_positive_template_manifest.json",
    "calibration/calibration_manifest_template.json",
    "calibration/collection_operator_template.csv",
    "calibration/collection_operator_template_manifest.json",
    "calibration/raw_blank_trace_manifest_template.json",
    "calibration/reference_blank_channel_template.csv",
    "calibration/reference_blank_channel_template_manifest.json",
    "calibration/standard_particle_template.csv",
    "calibration/standard_particle_template_manifest.json",
)

EXISTING_V2_ROLE_PATHS: tuple[tuple[str, str, str], ...] = (
    (
        "claim_boundary_summary",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_final_claim_boundary_summary.csv",
        "v2 closure",
    ),
    (
        "route_governance_summary",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_route_governance_closure_summary.csv",
        "v2 closure",
    ),
    (
        "artifact_gap_register",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_artifact_gap_closure_register.csv",
        "v2 closure",
    ),
    (
        "unmodeled_realism_register",
        "reports/89_EV_NODI_post_v2_unmodeled_realism_register.md",
        "post-v2 register",
    ),
    (
        "mie_to_power_guardrail_summary",
        "results/ev_nodi_realism_v2_anchor_smoke/mie_to_power_unit_check.csv",
        "upstream v2 evidence",
    ),
    (
        "noise_readout_scenario_manifest",
        "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
        "R5 v2 evidence",
    ),
    (
        "noise_readout_scenario_summary",
        "results/ev_nodi_realism_v2_full_grid_R5_v2/scenario_bundle_sensitivity_summary.csv",
        "R5 v2 evidence",
    ),
    (
        "selected_annulus_summary",
        "results/ev_nodi_realism_v2_full_grid_R5_v2/selected_annulus_parallel_lens_summary.csv",
        "R5 v2 evidence",
    ),
)

POST_V2_DIAGNOSTIC_ROLES: tuple[tuple[str, str, str], ...] = (
    (
        "top_candidate_extended_pairwise_stability",
        "results/post_v2_mandatory_audit/top_candidate_extended_pairwise_stability.csv",
        "P1.extended_pairwise_stability",
    ),
)

NON_P0_SIDECAR_P0_PACKAGE_EXCLUDED_CONFIGS: tuple[str, ...] = (
    "configs/realism_v2/physical_ceiling_extension_registry.yaml",
    "configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml",
    "configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml",
    "configs/realism_v2/roughness_leakage_diagnostic_contract.yaml",
    "configs/realism_v2/transport_residence_time_diagnostic_contract.yaml",
    "configs/realism_v2/bounded_physical_solver_readiness_registry.yaml",
    "configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml",
    "configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml",
    "configs/realism_v2/bounded_solver_authorization_gate_registry.yaml",
    "configs/realism_v2/minimal_bounded_solver_execution_registry.yaml",
    "configs/realism_v2/second_lane_authorization_design_registry.yaml",
    "configs/realism_v2/second_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/second_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/next_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/third_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/third_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/fourth_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/fourth_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/fourth_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/fifth_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/fifth_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/fifth_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/sixth_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/sixth_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/sixth_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/seventh_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/bounded_lane_synthesis_stop_continue_registry.yaml",
)

def file_entry(project_root: Path, relpath: str, *, role: str, source_lane: str) -> dict[str, Any]:
    path = project_root / relpath
    exists = path.exists()
    return {
        "role": role,
        "path": normalize_relpath(relpath),
        "path_status": "exists" if exists else "missing",
        "source_lane": source_lane,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
    }


def _config_entries(project_root: Path) -> list[dict[str, Any]]:
    paths = sorted((project_root / "configs/realism_v2").glob("*"))
    excluded = set(NON_P0_SIDECAR_P0_PACKAGE_EXCLUDED_CONFIGS)
    return [
        file_entry(
            project_root,
            normalize_relpath(path.relative_to(project_root)),
            role=path.name,
            source_lane="configs_realism_v2",
        )
        for path in paths
        if path.is_file()
        and not path.name.startswith("._")
        and normalize_relpath(path.relative_to(project_root)) not in excluded
    ]


def _paper_provenance_entries(project_root: Path) -> list[dict[str, Any]]:
    paths = sorted((project_root / PAPER_PROVENANCE_DIR).glob("*"))
    return [
        file_entry(
            project_root,
            normalize_relpath(path.relative_to(project_root)),
            role=path.name,
            source_lane="paper_provenance",
        )
        for path in paths
        if path.is_file() and not path.name.startswith("._")
    ]


def _artifact_groups(project_root: Path, *, include_generated_missing: bool) -> list[dict[str, Any]]:
    all_post_v2_roles_exist = all(
        (project_root / path).is_file() for _, path, _ in POST_V2_GENERATED_ROLES
    )
    groups: list[dict[str, Any]] = [
        {
            "group": "code_tests_tools_docs_reports",
            "artifacts": [
                file_entry(project_root, "README.md", role="repo_readme", source_lane="docs"),
                file_entry(
                    project_root,
                    "reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md",
                    role="roadmap",
                    source_lane="reports",
                ),
                file_entry(
                    project_root,
                    "reports/91_EV_NODI_post_v2_P0_release_completion_note.md",
                    role="p0_release_completion_note",
                    source_lane="reports",
                ),
                file_entry(
                    project_root,
                    "tools/generate_review_package_manifest.py",
                    role="review_package_manifest_generator",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/generate_paper_provenance.py",
                    role="paper_provenance_generator",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/verify_review_package.py",
                    role="review_package_verifier",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/export_review_package.py",
                    role="review_package_exporter",
                    source_lane="tools",
                ),
            ],
        },
        {"group": "configs_realism_v2", "artifacts": _config_entries(project_root)},
        {
            "group": "calibration_scaffold_all_files",
            "calibration_template_role": "schema_placeholder_no_measured_data",
            "artifacts": [
                file_entry(
                    project_root,
                    relpath,
                    role=Path(relpath).name,
                    source_lane="calibration_scaffold",
                )
                for relpath in CALIBRATION_SCAFFOLD_FILES
            ],
        },
        {
            "group": "v1_key_result_artifacts",
            "v1_summary_mode": "existing_single_summary_csv",
            "contract": v1_summary_contract(project_root),
            "artifacts": [
                file_entry(project_root, V1_SUMMARY_PATH, role="v1_summary_csv", source_lane="v1")
            ],
        },
        {
            "group": "v2_closure_artifacts",
            "artifacts": [
                file_entry(project_root, path, role=role, source_lane=source_lane)
                for role, path, source_lane in EXISTING_V2_ROLE_PATHS
            ],
        },
        {
            "group": "post_v2_mandatory_audit_schema",
            "artifacts": [
                file_entry(
                    project_root,
                    "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json",
                    role="top_candidate_mandatory_audit_manifest",
                    source_lane="P0a.v1_v2_artifact_mapping",
                )
            ],
        },
        {"group": "paper_provenance", "artifacts": _paper_provenance_entries(project_root)},
        {
            "group": "claim_language_lexicon",
            "artifacts": [
                file_entry(
                    project_root,
                    "configs/realism_v2/forbidden_claims_lexicon.yaml",
                    role="forbidden_claims_lexicon",
                    source_lane="claim_language_lexicon",
                )
            ],
        },
        {
            "group": "review_package_root",
            "artifacts": [
                file_entry(
                    project_root,
                    "REVIEW_PACKAGE_README.md",
                    role="review_package_readme",
                    source_lane="review_package_root",
                ),
                file_entry(
                    project_root,
                    "HISTORICAL_REPORT_SUPERSESSION.md",
                    role="historical_report_supersession",
                    source_lane="P1.governance",
                ),
            ],
        },
        {
            "group": "p1_governance_configs",
            "artifacts": [
                file_entry(
                    project_root,
                    "configs/realism_v2/reason_code_vocabulary.yaml",
                    role="reason_code_vocabulary",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/route_role_vocabulary.yaml",
                    role="route_role_vocabulary",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/ev_sample_profiles.yaml",
                    role="ev_sample_profiles",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/noise_readout_scenario_bundle.yaml",
                    role="noise_readout_scenario_bundle_config",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/v1_summary_hash_pin.json",
                    role="v1_summary_hash_pin",
                    source_lane="P1.governance",
                ),
            ],
        },
        {
            "group": "schema_docs",
            "artifacts": [
                file_entry(
                    project_root,
                    f"docs/schemas/{filename}",
                    role=Path(filename).stem,
                    source_lane="P2.schema_docs",
                )
                for filename in (
                    "post_v2_mandatory_audit_schema.md",
                    "review_package_manifest_schema.md",
                    "noise_readout_scenario_bundle_schema.md",
                    "ev_sample_profiles_schema.md",
                    "forbidden_claims_lexicon_schema.md",
                )
            ],
        },
    ]
    if include_generated_missing or all_post_v2_roles_exist:
        groups.append(
            {
                "group": "post_v2_mandatory_audit_artifacts",
                "artifacts": [
                    {
                        "role": role,
                        "path": path,
                        "path_status": "exists"
                        if (project_root / path).exists()
                        else "must_be_generated",
                        "source_lane": "post-v2 mandatory audit",
                        "sha256": sha256_file(project_root / path)
                        if (project_root / path).exists()
                        else None,
                        "generation_task_id": task
                        if include_generated_missing and not (project_root / path).exists()
                        else "",
                    }
                    for role, path, task in POST_V2_GENERATED_ROLES
                    if include_generated_missing or (project_root / path).exists()
                ],
            }
        )
    diagnostic_artifacts = [
        file_entry(project_root, path, role=role, source_lane=task)
        for role, path, task in POST_V2_DIAGNOSTIC_ROLES
        if (project_root / path).exists()
    ]
    if diagnostic_artifacts:
        groups.append(
            {
                "group": "post_v2_optional_diagnostic_artifacts",
                "release_blocker": False,
                "artifacts": diagnostic_artifacts,
            }
        )
    return groups


def iter_release_artifact_paths(manifest: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []
    for group in manifest.get("artifact_groups", []):
        paths.extend(
            str(artifact["path"])
            for artifact in group.get("artifacts", [])
            if artifact.get("path_status") == "exists"
        )
    return sorted(set(paths))


def write_hash_manifest(
    project_root: Path,
    artifact_paths: Iterable[str],
    *,
    output_relpath: str = "REVIEW_PACKAGE_HASHES.sha256",
) -> str:
    excluded = {
        output_relpath,
        "REVIEW_PACKAGE_MANIFEST.json",
        "REVIEW_BUILD_MANIFEST.json",
    }
    lines = []
    for relpath in sorted({normalize_relpath(path) for path in artifact_paths}):
        if relpath in excluded:
            continue
        path = project_root / relpath
        if path.is_file():
            lines.append(f"{sha256_file(path)}  {relpath}\n")
    output = project_root / output_relpath
    output.write_text("".join(lines), encoding="utf-8")
    return sha256_file(output)


def build_review_manifests(
    project_root: Path = PROJECT_ROOT,
    *,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    package_id = f"ev_nodi_post_v2_review_package_{datetime.now(UTC).strftime('%Y%m%d')}_p0b"
    base = {
        "package_id": package_id,
        "generated_at": generated_at,
        "git_commit": git_commit(project_root),
        "git_dirty": git_dirty(project_root),
        "calibrated_claim_allowed": False,
        "hashes_manifest_path": "REVIEW_PACKAGE_HASHES.sha256",
    }
    release_manifest = {
        **base,
        "review_package_manifest_schema": "ev_nodi_review_package_manifest_v1",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "package_role": "external_review_relative_audit",
        "release_readiness": "p0_p0b_review_ready_relative_audit",
        "v1_summary_mode": "existing_single_summary_csv",
        "artifact_groups": _artifact_groups(project_root, include_generated_missing=False),
        "deferred_p0b_roles": [
            {"role": role, "path": path, "deferred_to": task}
            for role, path, task in POST_V2_GENERATED_ROLES
            if not (project_root / path).exists()
        ],
    }
    hashes_manifest_sha256 = write_hash_manifest(
        project_root,
        iter_release_artifact_paths(release_manifest),
    )
    release_manifest["hashes_manifest_sha256"] = hashes_manifest_sha256
    build_manifest = {
        **base,
        "review_build_manifest_schema": "ev_nodi_review_build_manifest_v1",
        "package_role": "internal_build_tracking",
        "release_manifest_path": "REVIEW_PACKAGE_MANIFEST.json",
        "hashes_manifest_sha256": hashes_manifest_sha256,
        "artifact_groups": _artifact_groups(project_root, include_generated_missing=True),
    }
    return build_manifest, release_manifest


def write_review_manifests(project_root: Path = PROJECT_ROOT) -> tuple[Path, Path, Path]:
    generate_paper_provenance(project_root)
    write_forbidden_claims_lexicon(project_root)
    write_p1_governance_files(project_root)
    write_schema_docs(project_root)
    write_audit_schema_manifest(project_root)
    write_review_package_readme(project_root)
    build_manifest, release_manifest = build_review_manifests(project_root)
    build_path = project_root / "REVIEW_BUILD_MANIFEST.json"
    release_path = project_root / "REVIEW_PACKAGE_MANIFEST.json"
    write_json_atomic(build_path, build_manifest, sort_keys=True)
    write_json_atomic(release_path, release_manifest, sort_keys=True)
    return build_path, release_path, project_root / "REVIEW_PACKAGE_HASHES.sha256"


def verify_review_package(project_root: Path = PROJECT_ROOT, *, allow_dirty: bool = False) -> list[str]:
    release_path = project_root / "REVIEW_PACKAGE_MANIFEST.json"
    hash_path = project_root / "REVIEW_PACKAGE_HASHES.sha256"
    manifest = _load_json_compatible(release_path)
    if manifest.get("review_package_manifest_schema") != "ev_nodi_review_package_manifest_v1":
        raise ValueError("unexpected REVIEW_PACKAGE_MANIFEST schema")
    if not allow_dirty and manifest.get("git_dirty"):
        raise ValueError("dirty worktree cannot be verified as an external release")
    recorded_commit = manifest.get("git_commit")
    current_commit = git_commit(project_root)
    if (
        isinstance(recorded_commit, str)
        and recorded_commit
        and current_commit
        and not git_commit_is_ancestor(recorded_commit, current_commit, project_root)
    ):
        raise ValueError("manifest git_commit is not reachable from current HEAD")
    encoded = json.dumps(manifest, ensure_ascii=False)
    if "must_be_generated" in encoded:
        raise ValueError("release manifest must not contain must_be_generated")
    if sha256_file(hash_path) != manifest.get("hashes_manifest_sha256"):
        raise ValueError("hashes_manifest_sha256 mismatch")
    v1_contract = next(
        group for group in manifest["artifact_groups"] if group["group"] == "v1_key_result_artifacts"
    )["contract"]
    if not v1_hash_drift_is_authorized(v1_contract):
        raise ValueError("V1_SUMMARY_DRIFT_UNAUTHORIZED")
    hash_entries: dict[str, str] = {}
    for line in hash_path.read_text(encoding="utf-8").splitlines():
        digest, relpath = line.split("  ", 1)
        if relpath in {"REVIEW_PACKAGE_HASHES.sha256", "REVIEW_PACKAGE_MANIFEST.json"}:
            raise ValueError("hash manifest contains a no-cycle excluded path")
        hash_entries[relpath] = digest
    for relpath in iter_release_artifact_paths(manifest):
        if relpath in {"REVIEW_PACKAGE_HASHES.sha256", "REVIEW_PACKAGE_MANIFEST.json"}:
            continue
        path = project_root / relpath
        if not path.exists():
            raise ValueError(f"required release artifact missing: {relpath}")
        if hash_entries.get(relpath) != sha256_file(path):
            raise ValueError(f"artifact hash mismatch: {relpath}")
    violations = scan_claim_files(project_root)
    if violations:
        raise ValueError(f"claim-language violations: {violations[:5]}")
    return [
        "PASS required_paths",
        "PASS hashes",
        "PASS v1_summary_contract",
        "PASS v2_closure_contract",
        "PASS post_v2_audit_schema"
        if not manifest.get("deferred_p0b_roles")
        else "SKIP post_v2_audit_tables declared_P0b_deferred",
        "PASS claim_blockers",
    ]


def export_review_package(
    project_root: Path = PROJECT_ROOT,
    *,
    output_path: Path | None = None,
) -> Path:
    write_review_manifests(project_root)
    manifest = _load_json_compatible(project_root / "REVIEW_PACKAGE_MANIFEST.json")
    if output_path is None:
        output_path = (
            project_root
            / "exports"
            / f"{manifest['package_id']}_review_package.zip"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    package_paths = sorted(
        {
            "REVIEW_PACKAGE_MANIFEST.json",
            "REVIEW_PACKAGE_HASHES.sha256",
            *iter_release_artifact_paths(manifest),
        }
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for relpath in package_paths:
            if relpath.startswith("._") or "/._" in relpath or relpath == "REVIEW_BUILD_MANIFEST.json":
                continue
            path = project_root / relpath
            if not path.is_file():
                raise ValueError(f"cannot export missing package artifact: {relpath}")
            info = zipfile.ZipInfo(relpath)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, path.read_bytes())
    return output_path
