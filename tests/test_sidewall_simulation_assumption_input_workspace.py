from __future__ import annotations

import csv
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_headers, read_csv_rows
from nodi_simulator.sidewall_simulation_assumption_input_workspace import (
    TARGET_HEADER_ONLY_STATUS,
    TARGET_SIMULATION_ROWS_PRESENT_STATUS,
    SidewallSimulationAssumptionInputWorkspaceSpec,
    build_simulation_assumption_input_workspace,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_workspace_creates_header_only_target_without_evidence_rows(tmp_path: Path) -> None:
    template = tmp_path / "template.csv"
    target = tmp_path / "target.csv"
    _write_csv(
        template,
        [
            {"route_candidate_id": "ROUTE-CAND-001", "source_artifact_sha256": ""},
            {"route_candidate_id": "ROUTE-CAND-002", "source_artifact_sha256": ""},
        ],
    )

    rows = build_simulation_assumption_input_workspace(
        [
            SidewallSimulationAssumptionInputWorkspaceSpec(
                input_branch="detection_probability_value",
                template_artifact_path=str(template),
                target_input_path=str(target),
                accepted_status_required="detection_probability_value_accepted",
            )
        ],
        create_missing_targets=True,
    )

    assert rows[0].target_created_now is True
    assert rows[0].target_data_rows == 0
    assert rows[0].target_validation_status == TARGET_HEADER_ONLY_STATUS
    assert rows[0].evidence_current is False
    assert "eleven-step chain" in rows[0].required_next_action
    assert read_csv_headers(target) == ["route_candidate_id", "source_artifact_sha256"]
    assert read_csv_rows(target) == []


def test_workspace_does_not_rewrite_existing_simulation_rows(tmp_path: Path) -> None:
    template = tmp_path / "template.csv"
    target = tmp_path / "target.csv"
    _write_csv(template, [{"route_candidate_id": "ROUTE-CAND-001", "value": ""}])
    _write_csv(target, [{"route_candidate_id": "ROUTE-CAND-001", "value": "0.5"}])

    rows = build_simulation_assumption_input_workspace(
        [
            SidewallSimulationAssumptionInputWorkspaceSpec(
                input_branch="yield_wet_value",
                template_artifact_path=str(template),
                target_input_path=str(target),
                accepted_status_required="yield_wet_value_bundle_accepted",
            )
        ],
        create_missing_targets=True,
    )

    assert rows[0].target_preexisting is True
    assert rows[0].target_created_now is False
    assert rows[0].target_data_rows == 1
    assert rows[0].target_validation_status == TARGET_SIMULATION_ROWS_PRESENT_STATUS
    assert read_csv_rows(target)[0]["value"] == "0.5"


def test_workspace_allows_existing_simulation_rows_with_extended_schema(
    tmp_path: Path,
) -> None:
    template = tmp_path / "template.csv"
    target = tmp_path / "target.csv"
    _write_csv(template, [{"route_candidate_id": "ROUTE-CAND-001", "value": ""}])
    _write_csv(
        target,
        [
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "value": "0.5",
                "source_kind": "simulation_manifest",
            }
        ],
    )

    rows = build_simulation_assumption_input_workspace(
        [
            SidewallSimulationAssumptionInputWorkspaceSpec(
                input_branch="yield_wet_value",
                template_artifact_path=str(template),
                target_input_path=str(target),
                accepted_status_required="yield_wet_value_bundle_accepted",
            )
        ],
        create_missing_targets=True,
    )

    assert rows[0].target_header_matches_template is False
    assert rows[0].target_data_rows == 1
    assert rows[0].target_validation_status == TARGET_SIMULATION_ROWS_PRESENT_STATUS
    assert read_csv_rows(target)[0]["source_kind"] == "simulation_manifest"
