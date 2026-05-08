from __future__ import annotations

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.calibration_models import load_calibration_rows
from nodi_simulator.dashboard import safe_pickle
from nodi_simulator.data_objects import Channel, OpticalSystem, Particle, SimulationConfig
from nodi_simulator.design_claim_governance import (
    CLAIM_LEVELS,
    PAPER_ALIGNMENT_TARGETS,
    governance_to_jsonable,
)
from nodi_simulator.design_postprocess import _EV_GATE_PASS_FRACTION_FIELD
from nodi_simulator.particle_design_library import (
    STANDARD_PARTICLE_PRESETS,
    _particle_family,
)
from nodi_simulator.recompute_manifest import build_recompute_manifest_diagnostics
from nodi_simulator.seed_robustness import _SEED_GATE_PASS_FRACTION_FIELD
from nodi_simulator.structured_particles import equivalent_uniform_permittivity_core_shell


def test_maxwell_garnett_denominator_pole_fails_fast():
    with pytest.raises(ValueError, match="Maxwell-Garnett denominator near zero"):
        equivalent_uniform_permittivity_core_shell(
            epsilon_core=1.0 + 0.0j,
            epsilon_shell=-2.0 + 0.0j,
            epsilon_medium=1.0 + 0.0j,
            core_radius_ratio=0.0,
        )


def test_pickle_and_governance_allowlists_are_immutable():
    assert not hasattr(safe_pickle._ALLOWED_PICKLE_GLOBALS, "add")
    with pytest.raises(TypeError):
        PAPER_ALIGNMENT_TARGETS["new_target"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        CLAIM_LEVELS["new_claim"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        STANDARD_PARTICLE_PRESETS["new_standard"] = next(iter(STANDARD_PARTICLE_PRESETS.values()))  # type: ignore[index]


def test_frozen_governance_tables_can_be_exported_to_json_containers():
    payload = governance_to_jsonable(PAPER_ALIGNMENT_TARGETS)

    assert isinstance(payload, dict)
    assert isinstance(
        payload["tsuyama_2022_nodi_table_s1"]["required_metadata_fields"],
        dict,
    )


def test_calibration_relative_traversal_is_rejected():
    with pytest.raises(ValueError, match="Calibration path outside project root"):
        load_calibration_rows("../outside.csv")


def test_gate_fraction_fields_are_plain_literals():
    assert _EV_GATE_PASS_FRACTION_FIELD == "ev_gate_pass_fraction"
    assert _SEED_GATE_PASS_FRACTION_FIELD == "seed_gate_pass_fraction"


def test_recompute_manifest_hashes_are_128_bit_hex_prefixes():
    diagnostics = build_recompute_manifest_diagnostics(
        Particle("gold_40nm", 20e-9, 0.2),
        Channel(800e-9, 1400e-9),
        OpticalSystem(660e-9, 1.0e8, 1.0e-6, 1.0e-6, 1.0e-6),
        SimulationConfig(1.0e-3, 10_000.0, 2.0e-4),
    )

    for key in ("config_hash", "particle_hash", "channel_hash", "optical_hash", "case_hash"):
        prefix, value = str(diagnostics[key]).split("_", maxsplit=1)
        assert prefix
        assert len(value) == 32
        int(value, 16)


def test_particle_family_ev_match_uses_tokens_not_substrings():
    assert _particle_family(Particle("level_sphere", 25e-9, 1.45)) == "unknown"
    assert _particle_family(Particle("ev_like_particle", 25e-9, 1.45)) == "EV_sEV"


def test_run_manifest_exposes_manifest_schema_version(tmp_path):
    manifest = rv2.build_run_manifest(
        output_directory=tmp_path,
        event_budget={"stage": "test", "R2_anchor_smoke_started": False},
        scenario_budget={"scenario_bundle": "micro_anchor_nominal_sanity"},
    )

    assert manifest["manifest_schema_version"] == "1"
