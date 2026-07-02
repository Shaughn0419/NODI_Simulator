from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file
from nodi_simulator.sidewall_wet_surface_contract import WET_SURFACE_ENDPOINTS
from nodi_simulator.sidewall_wet_surface_observation_intake import (
    OBSERVATION_ACCEPTED_STATUS,
    ROUTE_MATRIX_ACCEPTED_STATUS,
    build_wet_surface_observation_intake,
)
from nodi_simulator.sidewall_wet_surface_observation_manifest_import import (
    IMPORT_READY_STATUS,
    build_wet_observation_rows_from_manifest,
)


def _contract_rows(route_id: str = "ROUTE-CAND-002") -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": route_id,
            "route_key": "route_taper_theta85_D900_W500",
            "source_case_id": "taper_theta85_D900_W500",
            "qch_sidecar_id": "QCH-CAND-002",
            "endpoint_id": endpoint["endpoint_id"],
            "target_claim": endpoint["target_claim"],
            "required_artifact_class": endpoint["required_artifact_class"],
            "required_fields": endpoint["required_fields"],
            "minimum_controls": endpoint["minimum_controls"],
            "hard_fail_if_missing": endpoint["hard_fail_if_missing"],
        }
        for endpoint in WET_SURFACE_ENDPOINTS
    ]


def _source_file(tmp_path: Path, endpoint_id: str) -> Path:
    path = tmp_path / "wet_sources" / f"{endpoint_id}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("endpoint,value\n" f"{endpoint_id},1\n", encoding="utf-8")
    return path


def _manifest_rows(tmp_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for contract in _contract_rows():
        endpoint_id = contract["endpoint_id"]
        source_path = _source_file(tmp_path, endpoint_id)
        prereg = (
            "pre_registered"
            if endpoint_id in {"wet_pass_probability", "yield_bridge", "clogging_time_series"}
            else "not_required_for_endpoint"
        )
        rows.append(
            {
                "route_candidate_id": contract["route_candidate_id"],
                "endpoint_id": endpoint_id,
                "observation_artifact_id": f"OBS-{endpoint_id}",
                "observation_artifact_class": contract["required_artifact_class"],
                "observation_source_artifact": str(source_path.relative_to(tmp_path)),
                "source_geometry_match_level": "sidewall_specific",
                "provided_fields": contract["required_fields"],
                "controls_status": "controls_pass",
                "replicate_count": (
                    "1"
                    if endpoint_id in {"material_surface_identity", "ev_sample_panel"}
                    else "3"
                ),
                "uncertainty_interval_status": (
                    "uncertainty_interval_missing"
                    if endpoint_id in {"material_surface_identity", "ev_sample_panel"}
                    else "uncertainty_interval_present"
                ),
                "pre_registered_rule_status": prereg,
            }
        )
    return rows


def test_manifest_import_binds_hashes_and_passes_existing_wet_intake(tmp_path: Path) -> None:
    observation_rows, audit_rows = build_wet_observation_rows_from_manifest(
        contract_rows=_contract_rows(),
        manifest_rows=_manifest_rows(tmp_path),
        artifact_root=tmp_path,
    )

    assert len(observation_rows) == len(WET_SURFACE_ENDPOINTS)
    assert {row.import_status for row in audit_rows} == {IMPORT_READY_STATUS}
    for row in observation_rows:
        assert row["observation_source_sha256"] == sha256_file(
            tmp_path / row["observation_source_artifact"]
        )

    intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=_contract_rows(),
        observation_rows=observation_rows,
        artifact_root=tmp_path,
    )

    assert {row.observation_validation_status for row in intake_rows} == {
        OBSERVATION_ACCEPTED_STATUS
    }
    assert matrix_rows[0].route_wet_observation_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
    assert matrix_rows[0].yield_current is False
    assert matrix_rows[0].detection_probability_current is False


def test_manifest_import_rejects_missing_source_artifact(tmp_path: Path) -> None:
    manifest_rows = _manifest_rows(tmp_path)
    manifest_rows[0]["observation_source_artifact"] = "missing.csv"

    observation_rows, audit_rows = build_wet_observation_rows_from_manifest(
        contract_rows=_contract_rows(),
        manifest_rows=manifest_rows,
        artifact_root=tmp_path,
    )

    assert len(observation_rows) == len(WET_SURFACE_ENDPOINTS) - 1
    rejected = [
        row for row in audit_rows if row.import_rejection_reason == "source_artifact_missing"
    ]
    assert len(rejected) == 1
