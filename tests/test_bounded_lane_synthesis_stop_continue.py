from __future__ import annotations

from copy import deepcopy
import csv
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_bounded_lane_synthesis_stop_continue import (
    P18_DECISION,
    P18_NEXT_STAGE,
    build_artifact_manifest,
    build_rank_summary_rows,
    build_synthesis_record,
    validate_artifact_manifest,
    validate_rank_summary_rows,
    validate_synthesis_record,
    validate_synthesis_registry,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_scan_paths,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/bounded_lane_synthesis_stop_continue_registry.yaml"
REPORT_PATH = "reports/120_EV_NODI_P18_bounded_lane_synthesis_stop_continue_design.md"
README_PATH = "results/post_v2_bounded_lane_synthesis_stop_continue/README.md"
SUMMARY_PATH = "results/post_v2_bounded_lane_synthesis_stop_continue/bounded_lane_rank_behavior_summary.csv"
RECORD_PATH = (
    "results/post_v2_bounded_lane_synthesis_stop_continue/"
    "bounded_lane_synthesis_stop_continue_record.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_bounded_lane_synthesis_stop_continue/"
    "bounded_lane_synthesis_artifact_manifest.json"
)
SCHEMA_DOCS = (
    "docs/schemas/p18_bounded_lane_synthesis_record_schema.md",
    "docs/schemas/p18_bounded_lane_synthesis_artifact_manifest_schema.md",
)


def _json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def _csv_rows() -> list[dict[str, str]]:
    with root_path(SUMMARY_PATH).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p18_registry_stops_mechanical_lane_roll_forward() -> None:
    registry = validate_synthesis_registry(rv2.load_json_yaml(REGISTRY_PATH))

    assert registry["synthesis_role"] == "bounded_lane_synthesis_stop_continue_design_only"
    assert registry["stop_continue_decision"] == P18_DECISION
    assert registry["next_required_stage"] == P18_NEXT_STAGE
    assert registry["physical_solver_execution_authorized"] is False
    assert registry["seventh_bounded_solver_lane_execution_authorized"] is False
    assert registry["solver_output_generated"] is False
    assert registry["route_promotion_authorized"] is False
    assert registry["bounded_lanes_sufficient_for_route_promotion"] is False
    assert registry["continue_mechanical_lanes_without_acceptance_criteria"] is False
    assert registry["rank_instability_across_bounded_lanes_detected"] is True
    assert registry["p19_evidence_strategy_gate_required"] is True


def test_p18_rank_summary_captures_instability_without_promotion() -> None:
    rows = validate_rank_summary_rows(build_rank_summary_rows(root_path(".")))
    csv_rows = _csv_rows()

    assert len(rows) == 18
    assert len(csv_rows) == 18
    top_sequence = [
        min((row for row in rows if row["lane_stage"] == lane), key=lambda row: row["rank"])[
            "candidate_id"
        ]
        for lane in ("P6", "P8", "P10", "P12", "P14", "P16")
    ]
    assert top_sequence == [
        "main_660_W800_D1400",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "main_660_W800_D1500",
        "main_660_W800_D1400",
        "main_660_W800_D1500",
    ]
    assert {row["route_promotion_authorized"] for row in rows} == {False}
    assert {row["solver_output_generated"] for row in rows} == {False}


def test_p18_generated_artifacts_are_current() -> None:
    assert _json(RECORD_PATH) == build_synthesis_record(root_path("."))
    assert _json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p18_synthesis_record_blocks_route_promotion_and_next_execution() -> None:
    record = validate_synthesis_record(build_synthesis_record(root_path(".")))

    assert record["route_promotion_conclusion"] == "not_supported_by_bounded_trace_lanes"
    assert record["stop_continue_decision"] == P18_DECISION
    assert record["next_required_stage"] == P18_NEXT_STAGE
    assert record["main_660_swap_events"] == ["P8_to_P10", "P12_to_P14", "P14_to_P16"]
    assert record["route_promotion_authorized"] is False
    assert record["future_authorization_phrase_already_received"] is False


def test_p18_rejects_tampering() -> None:
    registry = deepcopy(rv2.load_json_yaml(REGISTRY_PATH))
    registry["stop_continue_decision"] = "continue_mechanical_lanes"
    with pytest.raises(ValueError, match="decision drifted"):
        validate_synthesis_registry(registry)

    registry = deepcopy(rv2.load_json_yaml(REGISTRY_PATH))
    registry["bounded_lanes_sufficient_for_route_promotion"] = True
    with pytest.raises(ValueError, match="bounded_lanes_sufficient_for_route_promotion=false"):
        validate_synthesis_registry(registry)

    registry = deepcopy(rv2.load_json_yaml(REGISTRY_PATH))
    registry["synthesis_conclusion"]["main_660_swap_events"] = []
    with pytest.raises(ValueError, match="swap events drifted"):
        validate_synthesis_registry(registry)

    record = build_synthesis_record(root_path("."))
    record["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_synthesis_record(record)

    manifest = build_artifact_manifest(root_path("."))
    manifest["claim_boundary"]["calibrated_snr_claim_allowed"] = True
    with pytest.raises(ValueError, match="calibrated_snr_claim_allowed=false"):
        validate_artifact_manifest(manifest, root_path("."))


def test_p18_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, REPORT_PATH, README_PATH, *SCHEMA_DOCS):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p18_report_and_readme_are_claim_scanned() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert REPORT_PATH in paths
    assert README_PATH in paths


def test_p18_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths


def test_p18_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_bounded_lane_synthesis_stop_continue.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS bounded_lane_synthesis_registry" in result.stdout
    assert "PASS bounded_lane_synthesis_route_promotion_blocked" in result.stdout
    assert "PASS bounded_lane_synthesis_p19_strategy_required" in result.stdout
