from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_p14_closure_p15_authorization_design import (
    P14_REVIEW_VERDICT,
    P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    P15_RANK_INSTABILITY_DELTA_VECTOR,
    P15_RANK_INSTABILITY_OBSERVATION,
    P15_RANK_INSTABILITY_ROLE,
    build_p14_closure_artifact_manifest,
    build_p14_closure_review_record,
    build_p15_design_artifact_manifest,
    build_p15_next_authorization_gate_record,
    build_p15_p14_closure_binding_manifest,
    validate_p14_closure_artifact_manifest,
    validate_p14_closure_registry,
    validate_p14_closure_review_record,
    validate_p15_design_artifact_manifest,
    validate_p15_design_registry,
    validate_p15_next_authorization_gate_record,
    validate_p15_p14_closure_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


P14_CLOSURE_REGISTRY = "configs/realism_v2/fifth_bounded_solver_lane_closure_registry.yaml"
P15_DESIGN_REGISTRY = "configs/realism_v2/sixth_bounded_lane_authorization_design_registry.yaml"
P14_CLOSURE_REPORT = "reports/115_EV_NODI_P14_fifth_bounded_solver_lane_closure_note.md"
P15_DESIGN_REPORT = "reports/116_EV_NODI_P15_sixth_bounded_lane_authorization_design_plan.md"
P14_CLOSURE_README = "results/post_v2_fifth_bounded_solver_lane_closure/README.md"
P15_DESIGN_README = "results/post_v2_sixth_bounded_lane_authorization_design/README.md"
P14_CLOSURE_RECORD = (
    "results/post_v2_fifth_bounded_solver_lane_closure/p14_claude_review_closure_record.json"
)
P14_CLOSURE_ARTIFACT = (
    "results/post_v2_fifth_bounded_solver_lane_closure/p14_closure_artifact_manifest.json"
)
P15_BINDING = (
    "results/post_v2_sixth_bounded_lane_authorization_design/p15_p14_closure_binding_manifest.json"
)
P15_GATE = (
    "results/post_v2_sixth_bounded_lane_authorization_design/p15_next_authorization_gate_record.json"
)
P15_ARTIFACT = (
    "results/post_v2_sixth_bounded_lane_authorization_design/p15_next_authorization_design_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/p14_closure_review_record_schema.md",
    "docs/schemas/p14_closure_artifact_manifest_schema.md",
    "docs/schemas/p15_next_authorization_gate_record_schema.md",
    "docs/schemas/p15_next_authorization_design_artifact_manifest_schema.md",
)


def _json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p14_closure_records_no_blockers_without_new_execution() -> None:
    registry = validate_p14_closure_registry(rv2.load_json_yaml(P14_CLOSURE_REGISTRY))
    record = validate_p14_closure_review_record(build_p14_closure_review_record(root_path(".")))

    assert registry["closure_role"] == "review_closure_only_no_new_execution"
    assert record["claude_review_verdict"] == P14_REVIEW_VERDICT
    assert record["additional_solver_execution_authorized"] is False
    assert record["additional_solver_output_generated"] is False
    assert record["route_promotion_authorized"] is False


def test_p15_design_creates_future_gate_without_receiving_phrase() -> None:
    registry = validate_p15_design_registry(rv2.load_json_yaml(P15_DESIGN_REGISTRY))
    gate = validate_p15_next_authorization_gate_record(
        build_p15_next_authorization_gate_record(root_path("."))
    )

    assert registry["design_role"] == "next_authorization_design_only_no_solver_execution"
    assert gate["required_future_authorization_phrase"] == P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert gate["future_authorization_phrase_already_received"] is False
    assert gate["additional_solver_execution_authorized"] is False
    assert gate["additional_solver_output_generated"] is False


def test_p14_closure_and_p15_generated_artifacts_are_current() -> None:
    assert _json(P14_CLOSURE_RECORD) == build_p14_closure_review_record(root_path("."))
    assert _json(P14_CLOSURE_ARTIFACT) == build_p14_closure_artifact_manifest(root_path("."))
    assert _json(P15_BINDING) == build_p15_p14_closure_binding_manifest(root_path("."))
    assert _json(P15_GATE) == build_p15_next_authorization_gate_record(root_path("."))
    assert _json(P15_ARTIFACT) == build_p15_design_artifact_manifest(root_path("."))


def test_p15_binds_p14_closure_verdict() -> None:
    binding = validate_p15_p14_closure_binding_manifest(
        build_p15_p14_closure_binding_manifest(root_path("."))
    )

    assert binding["p14_review_verdict"] == P14_REVIEW_VERDICT
    assert binding["additional_solver_execution_authorized"] is False
    assert binding["additional_solver_output_generated"] is False


def test_p15_records_p12_to_p14_rank_instability_without_route_promotion() -> None:
    registry = validate_p15_design_registry(rv2.load_json_yaml(P15_DESIGN_REGISTRY))
    gate = validate_p15_next_authorization_gate_record(
        build_p15_next_authorization_gate_record(root_path("."))
    )
    manifest = validate_p15_design_artifact_manifest(
        build_p15_design_artifact_manifest(root_path(".")),
        root_path("."),
        allow_missing_self_manifest=True,
    )

    for payload in (
        registry["rank_instability_governance"],
        gate["rank_instability_governance"],
        manifest["rank_instability_governance"],
    ):
        assert payload["instability_observation"] == P15_RANK_INSTABILITY_OBSERVATION
        assert payload["rank_delta_vector"] == list(P15_RANK_INSTABILITY_DELTA_VECTOR)
        assert payload["governance_role"] == P15_RANK_INSTABILITY_ROLE
        assert payload["route_promotion_authorized"] is False
        assert payload["additional_solver_execution_authorized"] is False
        assert payload["additional_solver_output_generated"] is False


def test_p14_closure_p15_design_reject_tampering() -> None:
    record = build_p14_closure_review_record(root_path("."))
    record["claude_review_verdict"] = "P14 BLOCKERS FOUND"
    with pytest.raises(ValueError, match="review verdict drifted"):
        validate_p14_closure_review_record(record)

    record = build_p14_closure_review_record(root_path("."))
    record["additional_solver_output_generated"] = True
    with pytest.raises(ValueError, match="additional_solver_output_generated=false"):
        validate_p14_closure_review_record(record)

    gate = build_p15_next_authorization_gate_record(root_path("."))
    gate["future_authorization_phrase_already_received"] = True
    with pytest.raises(ValueError, match="already received drifted"):
        validate_p15_next_authorization_gate_record(gate)

    registry = deepcopy(rv2.load_json_yaml(P15_DESIGN_REGISTRY))
    registry["future_authorization_gate_contract"][
        "required_future_authorization_phrase"
    ] = "authorize everything"
    with pytest.raises(ValueError, match="future authorization phrase drifted"):
        validate_p15_design_registry(registry)

    manifest = build_p15_design_artifact_manifest(root_path("."))
    manifest["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p15_design_artifact_manifest(manifest, root_path("."))

    manifest = build_p14_closure_artifact_manifest(root_path("."))
    manifest["claim_boundary"]["calibrated_snr_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_snr_claim_allowed=false"):
        validate_p14_closure_artifact_manifest(manifest, root_path("."))

    registry = deepcopy(rv2.load_json_yaml(P15_DESIGN_REGISTRY))
    registry["rank_instability_governance"]["rank_delta_vector"] = [0, 0, 0]
    with pytest.raises(ValueError, match="rank instability delta drifted"):
        validate_p15_design_registry(registry)

    gate = build_p15_next_authorization_gate_record(root_path("."))
    gate["rank_instability_governance"]["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p15_next_authorization_gate_record(gate)


def test_p14_closure_p15_design_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (
        P14_CLOSURE_REGISTRY,
        P15_DESIGN_REGISTRY,
        P14_CLOSURE_REPORT,
        P15_DESIGN_REPORT,
        P14_CLOSURE_README,
        P15_DESIGN_README,
        *SCHEMA_DOCS,
    ):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p14_closure_p15_design_reports_and_readmes_are_claim_scanned() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert P14_CLOSURE_REPORT in paths
    assert P15_DESIGN_REPORT in paths
    assert P14_CLOSURE_README in paths
    assert P15_DESIGN_README in paths


def test_p14_closure_p15_registries_are_excluded_from_p0_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert P14_CLOSURE_REGISTRY not in paths
    assert P15_DESIGN_REGISTRY not in paths


def test_p14_closure_p15_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_p14_closure_p15_authorization_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS p14_closure_review_record_current" in result.stdout
    assert "PASS p15_next_authorization_gate_record_current" in result.stdout
    assert "PASS p14_closure_p15_design_no_new_execution" in result.stdout
