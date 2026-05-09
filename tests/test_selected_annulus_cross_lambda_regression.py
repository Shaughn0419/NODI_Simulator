from __future__ import annotations

import numpy as np
import pandas as pd

from tools.audits import tsuyama_selected_annulus_joint_fit as joint


def test_selected_annulus_real_sweep_is_count_subset_across_lambda_and_geometry():
    candidate = joint.build_joint_candidates(
        base_candidate_ids=["baseline_current_estimates"],
        variant_ids=["paper_10sigma"],
    )[0]

    rows = joint.run_joint_candidate_sweep(
        candidate,
        n_events=8,
        random_seed=17,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
        cases=joint.JOINT_CASES,
    )

    assert set(rows["wavelength_nm"].astype(int)) == {488, 532, 660}
    assert set(zip(rows["width_nm"].astype(int), rows["depth_nm"].astype(int))) == {
        (800, 550),
        (1200, 550),
    }

    selected_events = pd.to_numeric(
        rows["selected_detector_mode_annulus_n_events"],
        errors="raise",
    )
    all_events = pd.to_numeric(rows["n_events"], errors="raise")
    assert selected_events.gt(0).any()
    assert selected_events.le(all_events).all()

    selected_rate = pd.to_numeric(
        rows["selected_detector_mode_annulus_detection_rate"],
        errors="coerce",
    )
    selected_detected = np.rint(selected_rate.fillna(0.0) * selected_events).astype(int)
    all_detected = pd.to_numeric(rows["n_detected"], errors="raise")
    assert selected_detected.le(all_detected).all()
    assert selected_rate[selected_events.gt(0)].between(0.0, 1.0).all()
    assert selected_rate[selected_events.eq(0)].isna().all()
