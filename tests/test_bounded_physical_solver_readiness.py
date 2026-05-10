from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_bounded_physical_solver_readiness import (
    EXPECTED_LANE_IDS,
    build_readiness_artifact_manifest,
    build_readiness_route_universe_manifest,
    build_readiness_schema_manifest,
    build_readiness_source_binding_manifest,
    validate_readiness_route_universe_manifest,
    validate_readiness_registry,
    validate_readiness_source_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/bounded_physical_solver_readiness_registry.yaml"
PLAN_PATH = "reports/98_EV_NODI_P2_bounded_physical_solver_readiness_plan.md"
COMPLETION_NOTE_PATH = (
    "reports/99_EV_NODI_P2_bounded_physical_solver_readiness_completion_note.md"
)
README_PATH = "results/post_v2_bounded_physical_solver_readiness/README.md"
SCHEMA_MANIFEST_PATH = (
    "results/post_v2_bounded_physical_solver_readiness/"
    "bounded_physical_solver_readiness_schema_manifest.json"
)
SOURCE_BINDING_MANIFEST_PATH = (
    "results/post_v2_bounded_physical_solver_readiness/"
    "bounded_physical_solver_readiness_source_binding_manifest.json"
)
ROUTE_UNIVERSE_MANIFEST_PATH = (
    "results/post_v2_bounded_physical_solver_readiness/"
    "bounded_physical_solver_readiness_route_universe_manifest.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_bounded_physical_solver_readiness/"
    "bounded_physical_solver_readiness_artifact_manifest.json"
)
SCHEMA_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/bounded_physical_solver_readiness_schema_manifest_schema.md"
)
ARTIFACT_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/bounded_physical_solver_readiness_artifact_manifest_schema.md"
)
SOURCE_BINDING_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/bounded_physical_solver_readiness_source_binding_manifest_schema.md"
)
ROUTE_UNIVERSE_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/bounded_physical_solver_readiness_route_universe_manifest_schema.md"
)


def _registry() -> dict:
    return rv2.load_json_yaml("bounded_physical_solver_readiness_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p2_registry_is_bounded_readiness_only() -> None:
    registry = validate_readiness_registry(_registry())

    assert (
        registry["schema_version"]
        == "ev_nodi_p2_bounded_physical_solver_readiness_registry_v1"
    )
    assert registry["stage"] == "P2_bounded_physical_solver_readiness_complete"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["p1_surrogate_risk_role_preserved"] is True
    assert registry["physical_solver_execution_authorized"] is False
    assert registry["measured_data_ingest_authorized"] is False

    authority = registry["implementation_authority"]
    assert authority["readiness_schema_and_governance_authorized"] is True
    assert authority["artifact_manifest_generation_authorized"] is True
    assert authority["schema_manifest_generation_authorized"] is True
    assert authority["source_binding_manifest_generation_authorized"] is True
    assert authority["route_universe_manifest_generation_authorized"] is True
    assert authority["verifier_authorized"] is True
    for key, value in authority.items():
        if key.endswith("_authorized") and key not in {
            "readiness_schema_and_governance_authorized",
            "artifact_manifest_generation_authorized",
            "schema_manifest_generation_authorized",
            "source_binding_manifest_generation_authorized",
            "route_universe_manifest_generation_authorized",
            "verifier_authorized",
        }:
            assert value is False, key


def test_p2_registry_blocks_claim_families_and_route_promotion() -> None:
    claims = _registry()["claim_governance"]

    for key in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "absolute_event_probability_claim_allowed",
        "sample_count_claim_allowed",
        "measured_blank_safety_claim_allowed",
        "route_promotion_authorized",
    ):
        assert claims[key] is False
    assert claims["allowed_claim_level"] == "bounded_solver_readiness_only"


def test_p2_score_optional_660_and_jacobian_governance() -> None:
    registry = _registry()
    score = registry["score_governance"]
    authority = registry["implementation_authority"]
    jacobian = registry["jacobian_governance"]

    assert set(score["final_gate_metric_family"]) == {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }
    assert score["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert authority["optional_660_W900_D1400_redefines_main_660"] is False
    assert jacobian["v1_bfp_to_angle_jacobian_applied"] is False
    assert jacobian["audit_bfp_jacobian_applied"] is True


def test_p2_lanes_are_schema_only_and_fail_closed() -> None:
    lanes = _registry()["readiness_lanes"]

    assert {lane["lane_id"] for lane in lanes} == set(EXPECTED_LANE_IDS)
    for lane in lanes:
        assert lane["readiness_status"] == "schema_governance_only_not_executable"
        assert lane["calibrated_claim_allowed"] is False
        assert lane["p0_release_conclusion_changed"] is False
        assert lane["p1_surrogate_risk_role_preserved"] is True
        assert lane["physical_solver_execution_authorized"] is False
        assert lane["measured_data_ingest_authorized"] is False
        assert all(value is False for value in lane["execution_authority"].values())
        assert lane["readiness_output_contract"]["solver_output_path"] is None
        assert (
            lane["readiness_output_contract"]["artifact_status"]
            == "planned_readiness_schema_only"
        )
        assert set(lane["gate_policy"]["allowed_gate_metric_families"]) == {
            "rank",
            "rank_percentile",
            "pairwise_inversion",
        }
        assert lane["gate_policy"]["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False


def test_p2_artifact_manifest_schema_requires_guard_fields() -> None:
    registry = _registry()
    schema = registry["artifact_manifest_schema"]

    assert (
        schema["schema_name"]
        == "ev_nodi_p2_bounded_physical_solver_readiness_artifact_manifest_v1"
    )
    assert set(schema["required_false_fields"]) == {
        "calibrated_claim_allowed",
        "p0_release_conclusion_changed",
        "physical_solver_execution_authorized",
        "measured_data_ingest_authorized",
    }
    assert schema["required_true_fields"] == ["p1_surrogate_risk_role_preserved"]
    for artifact in registry["planned_artifacts"]:
        assert set(schema["required_artifact_fields"]).issubset(artifact)
        assert root_path(artifact["path"]).exists(), artifact["path"]
        assert artifact["calibrated_claim_allowed"] is False
        assert artifact["p0_release_conclusion_changed"] is False
        assert artifact["p1_surrogate_risk_role_preserved"] is True
        assert artifact["physical_solver_execution_authorized"] is False
        assert artifact["measured_data_ingest_authorized"] is False


def test_p2_generated_manifests_are_current() -> None:
    assert _load_json(SOURCE_BINDING_MANIFEST_PATH) == build_readiness_source_binding_manifest(
        root_path(".")
    )
    assert _load_json(ROUTE_UNIVERSE_MANIFEST_PATH) == build_readiness_route_universe_manifest(
        root_path(".")
    )
    assert _load_json(SCHEMA_MANIFEST_PATH) == build_readiness_schema_manifest(root_path("."))
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_readiness_artifact_manifest(
        root_path(".")
    )


def test_p2_source_binding_manifest_uses_only_p0_p1_sources() -> None:
    manifest = validate_readiness_source_binding_manifest(
        build_readiness_source_binding_manifest(root_path("."))
    )

    assert manifest["source_count"] == 5
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["p1_surrogate_risk_role_preserved"] is True
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["measured_data_ingest_authorized"] is False
    for binding in manifest["bindings"]:
        assert binding["source_exists"] is True
        assert binding["source_sha256"]
        assert binding["required_fields_present"] is True
        assert binding["missing_required_fields"] == []
        assert binding["source_row_count"] > 0
        assert binding["measured_data_ingest_authorized"] is False


def test_p2_route_universe_manifest_bounds_future_solver_preflight() -> None:
    manifest = validate_readiness_route_universe_manifest(
        build_readiness_route_universe_manifest(root_path("."))
    )

    assert manifest["route_universe_row_count"] == 572
    assert manifest["comparison_strata"] == ["all_ranked_routes"]
    assert manifest["high_surrogate_risk_route_count"] > 0
    assert manifest["pairwise_inversion_route_count"] > 0
    assert manifest["calibrated_claim_allowed"] is False
    assert manifest["p0_release_conclusion_changed"] is False
    assert manifest["p1_surrogate_risk_role_preserved"] is True
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["measured_data_ingest_authorized"] is False

    first = manifest["routes"][0]
    assert first["bounded_route_universe_role"] == "future_solver_preflight_only"
    assert first["physical_solver_execution_authorized"] is False
    assert first["measured_data_ingest_authorized"] is False
    assert first["raw_magnitude_final_gate_allowed"] is False
    assert first["route_promotion_authorized"] is False
    assert not any(
        key.startswith("raw_") and key != "raw_magnitude_final_gate_allowed"
        for key in first
    )


def test_p2_registry_rejects_solver_authority_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["full_wave_solver_execution_authorized"] = True

    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_readiness_registry(registry)


def test_p2_registry_rejects_p1_role_tampering() -> None:
    registry = deepcopy(_registry())
    registry["p1_surrogate_risk_role_preserved"] = False

    with pytest.raises(ValueError, match="P1 surrogate-risk role"):
        validate_readiness_registry(registry)


def test_p2_route_universe_rejects_raw_proxy_tampering() -> None:
    manifest = build_readiness_route_universe_manifest(root_path("."))
    manifest["routes"][0]["raw_complex_field_proxy_diagnostic_only"] = "0.1"

    with pytest.raises(ValueError, match="must not carry raw proxy fields"):
        validate_readiness_route_universe_manifest(manifest)


def test_p2_route_universe_rejects_route_promotion_tampering() -> None:
    manifest = build_readiness_route_universe_manifest(root_path("."))
    manifest["routes"][0]["route_promotion_authorized"] = True

    with pytest.raises(ValueError, match="route promotion drifted"):
        validate_readiness_route_universe_manifest(manifest)


def test_p2_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, COMPLETION_NOTE_PATH, README_PATH):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p2_manifest_schema_docs_preserve_boundaries() -> None:
    manifest_docs = [
        (
            root_path(SCHEMA_MANIFEST_SCHEMA_DOC),
            build_readiness_schema_manifest(root_path(".")),
            [
                "readiness_status = schema_governance_only_not_executable",
                "artifact_status = planned_readiness_schema_only",
                "solver_output_path = null",
            ],
        ),
        (
            root_path(ARTIFACT_MANIFEST_SCHEMA_DOC),
            build_readiness_artifact_manifest(root_path(".")),
            ["schema_governance_artifact_manifest_no_solver_execution"],
        ),
        (
            root_path(SOURCE_BINDING_MANIFEST_SCHEMA_DOC),
            build_readiness_source_binding_manifest(root_path(".")),
            ["source_exists = true", "required_fields_present = true"],
        ),
        (
            root_path(ROUTE_UNIVERSE_MANIFEST_SCHEMA_DOC),
            build_readiness_route_universe_manifest(root_path(".")),
            ["bounded_route_universe_role = future_solver_preflight_only"],
        ),
    ]

    for path, manifest, expected_snippets in manifest_docs:
        text = path.read_text(encoding="utf-8")
        assert manifest["manifest_role"] in text
        assert "calibrated_claim_allowed = false" in text
        assert "p0_release_conclusion_changed = false" in text
        assert "p1_surrogate_risk_role_preserved = true" in text
        assert "physical_solver_execution_authorized = false" in text
        assert "measured_data_ingest_authorized = false" in text
        for snippet in expected_snippets:
            assert snippet in text


def test_p2_completion_note_preserves_stop_rule() -> None:
    text = root_path(COMPLETION_NOTE_PATH).read_text(encoding="utf-8")

    assert "does not change the P0 release conclusion" in text
    assert "surrogate_risk_reduction_only" in text
    assert "calibrated_claim_allowed = false" in text
    assert "p0_release_conclusion_changed = false" in text
    assert "p1_surrogate_risk_role_preserved = true" in text
    assert "physical_solver_execution_authorized = false" in text
    assert "measured_data_ingest_authorized = false" in text
    assert "bounded route-universe manifest" in text
    assert "Heavy solver implementation remains unauthorized" in text


def test_p2_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_bounded_physical_solver_readiness.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS bounded_physical_solver_readiness_registry" in result.stdout
    assert (
        "PASS bounded_physical_solver_readiness_source_binding_manifest_current"
        in result.stdout
    )
    assert (
        "PASS bounded_physical_solver_readiness_route_universe_manifest_current"
        in result.stdout
    )
    assert "PASS bounded_physical_solver_execution_blocked" in result.stdout
    assert "PASS bounded_physical_solver_measured_data_ingest_blocked" in result.stdout


def test_p2_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths
