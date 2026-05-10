from __future__ import annotations

import pytest

from nodi_simulator.review_package import CALIBRATION_SCAFFOLD_FILES, verify_review_package

from ._review_package_test_helpers import load_json, root_path


pytestmark = pytest.mark.review_package_required


def _group(manifest: dict, name: str) -> dict:
    groups = {group["group"]: group for group in manifest["artifact_groups"]}
    return groups[name]


def _artifacts(group: dict) -> list[dict]:
    return list(group["artifacts"])


def test_release_manifest_schema_and_no_must_be_generated() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")

    assert manifest["review_package_manifest_schema"] == "ev_nodi_review_package_manifest_v1"
    assert manifest["package_role"] == "external_review_relative_audit"
    assert manifest["release_readiness"] == "p0_p0b_review_ready_relative_audit"
    assert manifest["deferred_p0b_roles"] == []
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["v1_summary_mode"] == "existing_single_summary_csv"
    assert "must_be_generated" not in root_path("REVIEW_PACKAGE_MANIFEST.json").read_text(
        encoding="utf-8"
    )


def test_build_manifest_tracks_p0b_generation_roles() -> None:
    manifest = load_json("REVIEW_BUILD_MANIFEST.json")
    group = _group(manifest, "post_v2_mandatory_audit_artifacts")
    artifacts = _artifacts(group)

    assert manifest["review_build_manifest_schema"] == "ev_nodi_review_build_manifest_v1"
    assert "candidate_universe_manifest" in {artifact["role"] for artifact in artifacts}
    assert {artifact["path_status"] for artifact in artifacts}.issubset(
        {"exists", "must_be_generated"}
    )


def test_required_p0a_paths_exist_by_manifest() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")

    for group in manifest["artifact_groups"]:
        for artifact in group["artifacts"]:
            assert artifact["path_status"] == "exists", artifact
            assert root_path(artifact["path"]).exists(), artifact
            assert artifact["sha256"], artifact


def test_configs_realism_v2_and_all_calibration_scaffolds_are_packaged() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    configs = _group(manifest, "configs_realism_v2")
    calibration = _group(manifest, "calibration_scaffold_all_files")

    config_paths = {artifact["path"] for artifact in _artifacts(configs)}
    calibration_paths = {artifact["path"] for artifact in _artifacts(calibration)}

    assert "configs/realism_v2/r5_scenario_bundle_manifest.yaml" in config_paths
    assert "configs/realism_v2/forbidden_claims_lexicon.yaml" in config_paths
    assert calibration["calibration_template_role"] == "schema_placeholder_no_measured_data"
    assert calibration_paths == set(CALIBRATION_SCAFFOLD_FILES)


def test_v1_summary_contract_and_v2_roles_are_declared() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    v1_group = _group(manifest, "v1_key_result_artifacts")
    v2_roles = {
        artifact["role"] for artifact in _artifacts(_group(manifest, "v2_closure_artifacts"))
    }

    contract = v1_group["contract"]
    assert contract["n_cases"] == 32032
    assert contract["required_v1_boundary_fields_present"] is True
    assert contract["v1_boundary_expected"]["bfp_to_angle_jacobian_applied"] is False
    assert {
        "claim_boundary_summary",
        "route_governance_summary",
        "artifact_gap_register",
        "noise_readout_scenario_manifest",
        "noise_readout_scenario_summary",
        "selected_annulus_summary",
    }.issubset(v2_roles)


def test_local_verifier_passes_with_allow_dirty() -> None:
    result = verify_review_package(root_path("."), allow_dirty=True)

    assert "PASS required_paths" in result
    assert "PASS hashes" in result
    assert "PASS post_v2_audit_schema" in result
