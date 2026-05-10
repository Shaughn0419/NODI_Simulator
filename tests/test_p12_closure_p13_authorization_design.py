from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_p12_closure_p13_authorization_design import (
    P12_REVIEW_VERDICT,
    P13_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    build_p12_closure_artifact_manifest,
    build_p12_closure_review_record,
    build_p13_design_artifact_manifest,
    build_p13_next_authorization_gate_record,
    build_p13_p12_closure_binding_manifest,
    validate_p12_closure_artifact_manifest,
    validate_p12_closure_registry,
    validate_p12_closure_review_record,
    validate_p13_design_artifact_manifest,
    validate_p13_design_registry,
    validate_p13_next_authorization_gate_record,
    validate_p13_p12_closure_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


P12_CLOSURE_REGISTRY = "configs/realism_v2/fourth_bounded_solver_lane_closure_registry.yaml"
P13_DESIGN_REGISTRY = "configs/realism_v2/fifth_bounded_lane_authorization_design_registry.yaml"
P12_CLOSURE_REPORT = "reports/112_EV_NODI_P12_fourth_bounded_solver_lane_closure_note.md"
P13_DESIGN_REPORT = "reports/113_EV_NODI_P13_fifth_bounded_lane_authorization_design_plan.md"
P12_CLOSURE_README = "results/post_v2_fourth_bounded_solver_lane_closure/README.md"
P13_DESIGN_README = "results/post_v2_fifth_bounded_lane_authorization_design/README.md"
P12_CLOSURE_RECORD = (
    "results/post_v2_fourth_bounded_solver_lane_closure/p12_claude_review_closure_record.json"
)
P12_CLOSURE_ARTIFACT = (
    "results/post_v2_fourth_bounded_solver_lane_closure/p12_closure_artifact_manifest.json"
)
P13_BINDING = (
    "results/post_v2_fifth_bounded_lane_authorization_design/p13_p12_closure_binding_manifest.json"
)
P13_GATE = (
    "results/post_v2_fifth_bounded_lane_authorization_design/p13_next_authorization_gate_record.json"
)
P13_ARTIFACT = (
    "results/post_v2_fifth_bounded_lane_authorization_design/p13_next_authorization_design_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/p12_closure_review_record_schema.md",
    "docs/schemas/p12_closure_artifact_manifest_schema.md",
    "docs/schemas/p13_next_authorization_gate_record_schema.md",
    "docs/schemas/p13_next_authorization_design_artifact_manifest_schema.md",
)


def _json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p12_closure_records_no_blockers_without_new_execution() -> None:
    registry = validate_p12_closure_registry(rv2.load_json_yaml(P12_CLOSURE_REGISTRY))
    record = validate_p12_closure_review_record(build_p12_closure_review_record(root_path(".")))

    assert registry["closure_role"] == "review_closure_only_no_new_execution"
    assert record["claude_review_verdict"] == P12_REVIEW_VERDICT
    assert record["additional_solver_execution_authorized"] is False
    assert record["additional_solver_output_generated"] is False
    assert record["route_promotion_authorized"] is False


def test_p13_design_creates_future_gate_without_receiving_phrase() -> None:
    registry = validate_p13_design_registry(rv2.load_json_yaml(P13_DESIGN_REGISTRY))
    gate = validate_p13_next_authorization_gate_record(
        build_p13_next_authorization_gate_record(root_path("."))
    )

    assert registry["design_role"] == "next_authorization_design_only_no_solver_execution"
    assert gate["required_future_authorization_phrase"] == P13_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert gate["future_authorization_phrase_already_received"] is False
    assert gate["additional_solver_execution_authorized"] is False
    assert gate["additional_solver_output_generated"] is False


def test_p12_closure_and_p13_generated_artifacts_are_current() -> None:
    assert _json(P12_CLOSURE_RECORD) == build_p12_closure_review_record(root_path("."))
    assert _json(P12_CLOSURE_ARTIFACT) == build_p12_closure_artifact_manifest(root_path("."))
    assert _json(P13_BINDING) == build_p13_p12_closure_binding_manifest(root_path("."))
    assert _json(P13_GATE) == build_p13_next_authorization_gate_record(root_path("."))
    assert _json(P13_ARTIFACT) == build_p13_design_artifact_manifest(root_path("."))


def test_p13_binds_p12_closure_verdict() -> None:
    binding = validate_p13_p12_closure_binding_manifest(
        build_p13_p12_closure_binding_manifest(root_path("."))
    )

    assert binding["p12_review_verdict"] == P12_REVIEW_VERDICT
    assert binding["additional_solver_execution_authorized"] is False
    assert binding["additional_solver_output_generated"] is False


def test_p12_closure_p13_design_reject_tampering() -> None:
    record = build_p12_closure_review_record(root_path("."))
    record["claude_review_verdict"] = "P12 BLOCKERS FOUND"
    with pytest.raises(ValueError, match="review verdict drifted"):
        validate_p12_closure_review_record(record)

    record = build_p12_closure_review_record(root_path("."))
    record["additional_solver_output_generated"] = True
    with pytest.raises(ValueError, match="additional_solver_output_generated=false"):
        validate_p12_closure_review_record(record)

    gate = build_p13_next_authorization_gate_record(root_path("."))
    gate["future_authorization_phrase_already_received"] = True
    with pytest.raises(ValueError, match="already received drifted"):
        validate_p13_next_authorization_gate_record(gate)

    registry = deepcopy(rv2.load_json_yaml(P13_DESIGN_REGISTRY))
    registry["future_authorization_gate_contract"][
        "required_future_authorization_phrase"
    ] = "authorize everything"
    with pytest.raises(ValueError, match="future authorization phrase drifted"):
        validate_p13_design_registry(registry)

    manifest = build_p13_design_artifact_manifest(root_path("."))
    manifest["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p13_design_artifact_manifest(manifest, root_path("."))

    manifest = build_p12_closure_artifact_manifest(root_path("."))
    manifest["claim_boundary"]["calibrated_snr_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_snr_claim_allowed=false"):
        validate_p12_closure_artifact_manifest(manifest, root_path("."))


def test_p12_closure_p13_design_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (
        P12_CLOSURE_REGISTRY,
        P13_DESIGN_REGISTRY,
        P12_CLOSURE_REPORT,
        P13_DESIGN_REPORT,
        P12_CLOSURE_README,
        P13_DESIGN_README,
        *SCHEMA_DOCS,
    ):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p12_closure_p13_design_reports_and_readmes_are_claim_scanned() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert P12_CLOSURE_REPORT in paths
    assert P13_DESIGN_REPORT in paths
    assert P12_CLOSURE_README in paths
    assert P13_DESIGN_README in paths


def test_p12_closure_p13_registries_are_excluded_from_p0_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert P12_CLOSURE_REGISTRY not in paths
    assert P13_DESIGN_REGISTRY not in paths


def test_p12_closure_p13_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_p12_closure_p13_authorization_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS p12_closure_review_record_current" in result.stdout
    assert "PASS p13_next_authorization_gate_record_current" in result.stdout
    assert "PASS p12_closure_p13_design_no_new_execution" in result.stdout
