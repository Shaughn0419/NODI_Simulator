from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import write_top_candidate_mandatory_audit

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_every_candidate_has_required_next_artifact_binding() -> None:
    path = root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv")
    write_top_candidate_mandatory_audit(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    allowed = {
        "measured_blank_bfp",
        "slit_roi_scan",
        "raw_blank_trace",
        "detector_gain_chain",
        "standard_particle_transfer",
        "pressure_flow_trace",
        "ev_sample_characterization",
        "fullwave_spot_check",
        "polarization_transfer_artifact",
        "fabrication_roughness_blank_artifact",
        "time_resolved_alignment_blank_artifact",
        "coincidence_event_overlap_artifact",
        "transport_wall_interaction_artifact",
    }

    assert rows
    for row in rows:
        assert row["required_next_artifact"] in allowed
        assert row["required_next_artifact_priority"] in {"P0", "P1", "P2"}
        assert row["required_next_artifact_blocks"]
