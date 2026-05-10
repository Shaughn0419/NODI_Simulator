from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_p10_closure_p11_authorization_design import (
    P10_REVIEW_VERDICT,
    P11_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    build_p10_closure_artifact_manifest,
    build_p10_closure_review_record,
    build_p11_design_artifact_manifest,
    build_p11_next_authorization_gate_record,
    build_p11_p10_closure_binding_manifest,
    validate_p10_closure_artifact_manifest,
    validate_p10_closure_registry,
    validate_p10_closure_review_record,
    validate_p11_design_artifact_manifest,
    validate_p11_design_registry,
    validate_p11_next_authorization_gate_record,
    validate_p11_p10_closure_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


P10_CLOSURE_REGISTRY = "configs/realism_v2/third_bounded_solver_lane_closure_registry.yaml"
P11_DESIGN_REGISTRY = "configs/realism_v2/fourth_bounded_lane_authorization_design_registry.yaml"
P10_CLOSURE_REPORT = "reports/109_EV_NODI_P10_third_bounded_solver_lane_closure_note.md"
P11_DESIGN_REPORT = "reports/110_EV_NODI_P11_fourth_bounded_lane_authorization_design_plan.md"
P10_CLOSURE_README = "results/post_v2_third_bounded_solver_lane_closure/README.md"
P11_DESIGN_README = "results/post_v2_fourth_bounded_lane_authorization_design/README.md"
P10_CLOSURE_RECORD = (
    "results/post_v2_third_bounded_solver_lane_closure/p10_claude_review_closure_record.json"
)
P10_CLOSURE_ARTIFACT = (
    "results/post_v2_third_bounded_solver_lane_closure/p10_closure_artifact_manifest.json"
)
P11_BINDING = (
    "results/post_v2_fourth_bounded_lane_authorization_design/p11_p10_closure_binding_manifest.json"
)
P11_GATE = (
    "results/post_v2_fourth_bounded_lane_authorization_design/p11_next_authorization_gate_record.json"
)
P11_ARTIFACT = (
    "results/post_v2_fourth_bounded_lane_authorization_design/p11_next_authorization_design_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/p10_closure_review_record_schema.md",
    "docs/schemas/p10_closure_artifact_manifest_schema.md",
    "docs/schemas/p11_next_authorization_gate_record_schema.md",
    "docs/schemas/p11_next_authorization_design_artifact_manifest_schema.md",
)


def _json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p10_closure_records_no_blockers_without_new_execution() -> None:
    registry = validate_p10_closure_registry(rv2.load_json_yaml(P10_CLOSURE_REGISTRY))
    record = validate_p10_closure_review_record(build_p10_closure_review_record(root_path(".")))

    assert registry["closure_role"] == "review_closure_only_no_new_execution"
    assert record["claude_review_verdict"] == P10_REVIEW_VERDICT
    assert record["additional_solver_execution_authorized"] is False
    assert record["additional_solver_output_generated"] is False
    assert record["route_promotion_authorized"] is False


def test_p11_design_creates_future_gate_without_receiving_phrase() -> None:
    registry = validate_p11_design_registry(rv2.load_json_yaml(P11_DESIGN_REGISTRY))
    gate = validate_p11_next_authorization_gate_record(
        build_p11_next_authorization_gate_record(root_path("."))
    )

    assert registry["design_role"] == "next_authorization_design_only_no_solver_execution"
    assert gate["required_future_authorization_phrase"] == P11_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert gate["future_authorization_phrase_already_received"] is False
    assert gate["additional_solver_execution_authorized"] is False
    assert gate["additional_solver_output_generated"] is False


def test_p10_closure_and_p11_generated_artifacts_are_current() -> None:
    assert _json(P10_CLOSURE_RECORD) == build_p10_closure_review_record(root_path("."))
    assert _json(P10_CLOSURE_ARTIFACT) == build_p10_closure_artifact_manifest(root_path("."))
    assert _json(P11_BINDING) == build_p11_p10_closure_binding_manifest(root_path("."))
    assert _json(P11_GATE) == build_p11_next_authorization_gate_record(root_path("."))
    assert _json(P11_ARTIFACT) == build_p11_design_artifact_manifest(root_path("."))


def test_p11_binds_p10_closure_verdict() -> None:
    binding = validate_p11_p10_closure_binding_manifest(
        build_p11_p10_closure_binding_manifest(root_path("."))
    )

    assert binding["p10_review_verdict"] == P10_REVIEW_VERDICT
    assert binding["additional_solver_execution_authorized"] is False
    assert binding["additional_solver_output_generated"] is False


def test_p10_closure_p11_design_reject_tampering() -> None:
    record = build_p10_closure_review_record(root_path("."))
    record["claude_review_verdict"] = "P10 BLOCKERS FOUND"
    with pytest.raises(ValueError, match="review verdict drifted"):
        validate_p10_closure_review_record(record)

    record = build_p10_closure_review_record(root_path("."))
    record["additional_solver_output_generated"] = True
    with pytest.raises(ValueError, match="additional_solver_output_generated=false"):
        validate_p10_closure_review_record(record)

    gate = build_p11_next_authorization_gate_record(root_path("."))
    gate["future_authorization_phrase_already_received"] = True
    with pytest.raises(ValueError, match="already received drifted"):
        validate_p11_next_authorization_gate_record(gate)

    registry = deepcopy(rv2.load_json_yaml(P11_DESIGN_REGISTRY))
    registry["future_authorization_gate_contract"][
        "required_future_authorization_phrase"
    ] = "authorize everything"
    with pytest.raises(ValueError, match="future authorization phrase drifted"):
        validate_p11_design_registry(registry)

    manifest = build_p11_design_artifact_manifest(root_path("."))
    manifest["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p11_design_artifact_manifest(manifest, root_path("."))

    manifest = build_p10_closure_artifact_manifest(root_path("."))
    manifest["claim_boundary"]["calibrated_snr_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_snr_claim_allowed=false"):
        validate_p10_closure_artifact_manifest(manifest, root_path("."))


def test_p10_closure_p11_design_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (
        P10_CLOSURE_REGISTRY,
        P11_DESIGN_REGISTRY,
        P10_CLOSURE_REPORT,
        P11_DESIGN_REPORT,
        P10_CLOSURE_README,
        P11_DESIGN_README,
        *SCHEMA_DOCS,
    ):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p10_closure_p11_design_reports_and_readmes_are_claim_scanned() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert P10_CLOSURE_REPORT in paths
    assert P11_DESIGN_REPORT in paths
    assert P10_CLOSURE_README in paths
    assert P11_DESIGN_README in paths


def test_p10_closure_p11_registries_are_excluded_from_p0_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert P10_CLOSURE_REGISTRY not in paths
    assert P11_DESIGN_REGISTRY not in paths


def test_p10_closure_p11_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_p10_closure_p11_authorization_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS p10_closure_review_record_current" in result.stdout
    assert "PASS p11_next_authorization_gate_record_current" in result.stdout
    assert "PASS p10_closure_p11_design_no_new_execution" in result.stdout
