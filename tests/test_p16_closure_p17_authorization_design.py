from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_p16_closure_p17_authorization_design import (
    P16_REVIEW_VERDICT,
    P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    P17_RANK_INSTABILITY_DELTA_VECTOR,
    P17_RANK_INSTABILITY_OBSERVATION,
    P17_RANK_INSTABILITY_ROLE,
    P17_REPORT_NUMBERING_NOTE,
    build_p16_closure_artifact_manifest,
    build_p16_closure_review_record,
    build_p17_design_artifact_manifest,
    build_p17_next_authorization_gate_record,
    build_p17_p16_closure_binding_manifest,
    validate_p16_closure_artifact_manifest,
    validate_p16_closure_registry,
    validate_p16_closure_review_record,
    validate_p17_design_artifact_manifest,
    validate_p17_design_registry,
    validate_p17_next_authorization_gate_record,
    validate_p17_p16_closure_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


P16_CLOSURE_REGISTRY = "configs/realism_v2/sixth_bounded_solver_lane_closure_registry.yaml"
P17_DESIGN_REGISTRY = "configs/realism_v2/seventh_bounded_lane_authorization_design_registry.yaml"
P16_CLOSURE_REPORT = "reports/118_EV_NODI_P16_sixth_bounded_solver_lane_closure_note.md"
P17_DESIGN_REPORT = "reports/119_EV_NODI_P17_seventh_bounded_lane_authorization_design_plan.md"
P16_CLOSURE_README = "results/post_v2_sixth_bounded_solver_lane_closure/README.md"
P17_DESIGN_README = "results/post_v2_seventh_bounded_lane_authorization_design/README.md"
P16_CLOSURE_RECORD = (
    "results/post_v2_sixth_bounded_solver_lane_closure/p16_claude_review_closure_record.json"
)
P16_CLOSURE_ARTIFACT = (
    "results/post_v2_sixth_bounded_solver_lane_closure/p16_closure_artifact_manifest.json"
)
P17_BINDING = (
    "results/post_v2_seventh_bounded_lane_authorization_design/p17_p16_closure_binding_manifest.json"
)
P17_GATE = (
    "results/post_v2_seventh_bounded_lane_authorization_design/p17_next_authorization_gate_record.json"
)
P17_ARTIFACT = (
    "results/post_v2_seventh_bounded_lane_authorization_design/p17_next_authorization_design_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/p16_closure_review_record_schema.md",
    "docs/schemas/p16_closure_artifact_manifest_schema.md",
    "docs/schemas/p17_next_authorization_gate_record_schema.md",
    "docs/schemas/p17_next_authorization_design_artifact_manifest_schema.md",
)


def _json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p16_closure_records_no_blockers_without_new_execution() -> None:
    registry = validate_p16_closure_registry(rv2.load_json_yaml(P16_CLOSURE_REGISTRY))
    record = validate_p16_closure_review_record(build_p16_closure_review_record(root_path(".")))

    assert registry["closure_role"] == "review_closure_only_no_new_execution"
    assert record["claude_review_verdict"] == P16_REVIEW_VERDICT
    assert record["additional_solver_execution_authorized"] is False
    assert record["additional_solver_output_generated"] is False
    assert record["route_promotion_authorized"] is False


def test_p17_design_creates_future_gate_without_receiving_phrase() -> None:
    registry = validate_p17_design_registry(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    gate = validate_p17_next_authorization_gate_record(
        build_p17_next_authorization_gate_record(root_path("."))
    )

    assert registry["design_role"] == "next_authorization_design_only_no_solver_execution"
    assert gate["required_future_authorization_phrase"] == P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE
    assert gate["future_authorization_phrase_already_received"] is False
    assert gate["additional_solver_execution_authorized"] is False
    assert gate["additional_solver_output_generated"] is False


def test_p16_closure_and_p17_generated_artifacts_are_current() -> None:
    assert _json(P16_CLOSURE_RECORD) == build_p16_closure_review_record(root_path("."))
    assert _json(P16_CLOSURE_ARTIFACT) == build_p16_closure_artifact_manifest(root_path("."))
    assert _json(P17_BINDING) == build_p17_p16_closure_binding_manifest(root_path("."))
    assert _json(P17_GATE) == build_p17_next_authorization_gate_record(root_path("."))
    assert _json(P17_ARTIFACT) == build_p17_design_artifact_manifest(root_path("."))


def test_p17_binds_p16_closure_verdict() -> None:
    binding = validate_p17_p16_closure_binding_manifest(
        build_p17_p16_closure_binding_manifest(root_path("."))
    )

    assert binding["p16_review_verdict"] == P16_REVIEW_VERDICT
    assert binding["additional_solver_execution_authorized"] is False
    assert binding["additional_solver_output_generated"] is False


def test_p17_records_recurring_rank_instability_without_route_promotion() -> None:
    registry = validate_p17_design_registry(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    gate = validate_p17_next_authorization_gate_record(
        build_p17_next_authorization_gate_record(root_path("."))
    )
    manifest = validate_p17_design_artifact_manifest(
        build_p17_design_artifact_manifest(root_path(".")),
        root_path("."),
        allow_missing_self_manifest=True,
    )

    for payload in (
        registry["rank_instability_governance"],
        gate["rank_instability_governance"],
        manifest["rank_instability_governance"],
    ):
        assert payload["instability_observation"] == P17_RANK_INSTABILITY_OBSERVATION
        assert payload["rank_delta_vector"] == list(P17_RANK_INSTABILITY_DELTA_VECTOR)
        assert [event["event_id"] for event in payload["recurrence_events"]] == [
            "p12_to_p14_main_660_swap",
            "p14_to_p16_main_660_swap",
        ]
        assert payload["governance_role"] == P17_RANK_INSTABILITY_ROLE
        assert payload["route_promotion_authorized"] is False
        assert payload["additional_solver_execution_authorized"] is False
        assert payload["additional_solver_output_generated"] is False


def test_p17_records_report_numbering_convention_without_scope_expansion() -> None:
    registry = validate_p17_design_registry(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    gate = validate_p17_next_authorization_gate_record(
        build_p17_next_authorization_gate_record(root_path("."))
    )
    manifest = validate_p17_design_artifact_manifest(
        build_p17_design_artifact_manifest(root_path(".")),
        root_path("."),
        allow_missing_self_manifest=True,
    )

    for payload in (
        registry["report_numbering_governance"],
        gate["report_numbering_governance"],
        manifest["report_numbering_governance"],
    ):
        assert payload["note_id"] == P17_REPORT_NUMBERING_NOTE
        assert payload["report_path"] == P17_DESIGN_REPORT
        assert payload["numbering_role"] == "sequential_report_numbering_not_stage_numbering"
        assert payload["additional_solver_execution_authorized"] is False
        assert payload["additional_solver_output_generated"] is False


def test_p16_closure_p17_design_reject_tampering() -> None:
    record = build_p16_closure_review_record(root_path("."))
    record["claude_review_verdict"] = "P16 BLOCKERS FOUND"
    with pytest.raises(ValueError, match="review verdict drifted"):
        validate_p16_closure_review_record(record)

    record = build_p16_closure_review_record(root_path("."))
    record["additional_solver_output_generated"] = True
    with pytest.raises(ValueError, match="additional_solver_output_generated=false"):
        validate_p16_closure_review_record(record)

    gate = build_p17_next_authorization_gate_record(root_path("."))
    gate["future_authorization_phrase_already_received"] = True
    with pytest.raises(ValueError, match="already received drifted"):
        validate_p17_next_authorization_gate_record(gate)

    registry = deepcopy(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    registry["future_authorization_gate_contract"][
        "required_future_authorization_phrase"
    ] = "authorize everything"
    with pytest.raises(ValueError, match="future authorization phrase drifted"):
        validate_p17_design_registry(registry)

    manifest = build_p17_design_artifact_manifest(root_path("."))
    manifest["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p17_design_artifact_manifest(manifest, root_path("."))

    manifest = build_p16_closure_artifact_manifest(root_path("."))
    manifest["claim_boundary"]["calibrated_snr_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_snr_claim_allowed=false"):
        validate_p16_closure_artifact_manifest(manifest, root_path("."))

    registry = deepcopy(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    registry["rank_instability_governance"]["rank_delta_vector"] = [0, 0, 0]
    with pytest.raises(ValueError, match="rank instability delta drifted"):
        validate_p17_design_registry(registry)

    gate = build_p17_next_authorization_gate_record(root_path("."))
    gate["rank_instability_governance"]["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p17_next_authorization_gate_record(gate)

    gate = build_p17_next_authorization_gate_record(root_path("."))
    gate["rank_instability_governance"]["recurrence_events"][1]["event_id"] = "other"
    with pytest.raises(ValueError, match="recurrence event ids drifted"):
        validate_p17_next_authorization_gate_record(gate)

    registry = deepcopy(rv2.load_json_yaml(P17_DESIGN_REGISTRY))
    registry["report_numbering_governance"]["report_path"] = "reports/17.md"
    with pytest.raises(ValueError, match="report numbering path drifted"):
        validate_p17_design_registry(registry)


def test_p16_closure_p17_design_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (
        P16_CLOSURE_REGISTRY,
        P17_DESIGN_REGISTRY,
        P16_CLOSURE_REPORT,
        P17_DESIGN_REPORT,
        P16_CLOSURE_README,
        P17_DESIGN_README,
        *SCHEMA_DOCS,
    ):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p16_closure_p17_design_reports_and_readmes_are_claim_scanned() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert P16_CLOSURE_REPORT in paths
    assert P17_DESIGN_REPORT in paths
    assert P16_CLOSURE_README in paths
    assert P17_DESIGN_README in paths


def test_p16_closure_p17_registries_are_excluded_from_p0_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert P16_CLOSURE_REGISTRY not in paths
    assert P17_DESIGN_REGISTRY not in paths


def test_p16_closure_p17_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_p16_closure_p17_authorization_design.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS p16_closure_review_record_current" in result.stdout
    assert "PASS p17_next_authorization_gate_record_current" in result.stdout
    assert "PASS p16_closure_p17_design_no_new_execution" in result.stdout
