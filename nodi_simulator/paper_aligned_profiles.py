from __future__ import annotations

"""
Package-local paper-aligned profile helpers for validation lanes.

These profiles are not intended to replace the engineering mainline. They are
scoped comparison profiles that bring selected parts of the simulator closer to
the experimental semantics used in specific papers.
"""

from copy import deepcopy
from dataclasses import dataclass

from .data_objects import SimulationConfig, apply_readout_preset


@dataclass(frozen=True)
class PaperAlignedProfile:
    name: str
    description: str
    scope: str
    status: str
    notes: tuple[str, ...]
    reference_route: str | None = None
    reference_solver_route: str | None = None
    unavailable_reason: str | None = None


PAPER_ALIGNED_PROFILES: dict[str, PaperAlignedProfile] = {
    "diffraction_2020": PaperAlignedProfile(
        name="diffraction_2020",
        description=(
            "Tsuyama 2020 diffraction comparison profile. Keeps depth as phase "
            "thickness and removes the extra depth-aperture term from the "
            "reference-side surrogate."
        ),
        scope="reference / width-depth semantics audit",
        status="available",
        notes=(
            "Reference-only comparison lane.",
            "tsuyama_phase_filter_1d is available for complex-field regression; "
            "the existing reference_model remains paper_aligned_phase_filter "
            "until solver-to-detector integration is complete.",
            "Not intended as a full event-level POD validation profile.",
        ),
        reference_route="paper_aligned_comparison",
        reference_solver_route="tsuyama_phase_filter_1d",
    ),
    "nodi_2022": PaperAlignedProfile(
        name="nodi_2022",
        description=(
            "Tsuyama 2022 NODI comparison profile. Aligns illumination, "
            "reference-depth semantics, readout observable, and single-channel "
            "decision semantics closer to the paper."
        ),
        scope="single-channel NODI detectability / size-signal comparison",
        status="available",
        notes=(
            "Uses overfill illumination semantics.",
            "Uses magnitude-like readout and disables phase-flip as a hard gate.",
            "Still relies on current transport and collection surrogates.",
        ),
        reference_route="paper_aligned_comparison",
        reference_solver_route="paper_aligned_angular_surrogate",
    ),
    "paired_2024": PaperAlignedProfile(
        name="paired_2024",
        description=(
            "Tsuyama 2024 paired POD/NODI comparison profile. Aligns the two "
            "lock-in frequencies, paired-channel decision semantics, and "
            "5σ magnitude-like counting observable closer to the paper."
        ),
        scope="paired absorption+scattering validation lane",
        status="available",
        notes=(
            "Uses 4.1/1.2 kHz POD/NODI frequency split.",
            "Uses paired-channel decision mode with wider pairing tolerance.",
            "Still relies on a surrogate POD source model rather than a full thermal model.",
        ),
        reference_route="paper_aligned_comparison",
        reference_solver_route="paper_aligned_angular_surrogate",
    ),
    "paired_2024_10sigma": PaperAlignedProfile(
        name="paired_2024_10sigma",
        description=(
            "Tsuyama 2024 paired POD/NODI comparison profile using the 10σ "
            "paper-counting readout preset."
        ),
        scope="paired absorption+scattering validation lane / 10sigma counting",
        status="available",
        notes=(
            "Uses 4.1/1.2 kHz POD/NODI frequency split.",
            "Uses paired-channel decision mode with wider pairing tolerance.",
            "Keeps shared POD/NODI threshold fields until lane-specific "
            "thresholds are introduced.",
            "Still relies on a surrogate POD source model rather than a full thermal model.",
        ),
        reference_route="paper_aligned_comparison",
        reference_solver_route="paper_aligned_angular_surrogate",
    ),
    "pod_2019_2020": PaperAlignedProfile(
        name="pod_2019_2020",
        description=(
            "Placeholder for a future paper-aligned POD profile spanning the "
            "2019 POD paper (Tsuyama & Mawatari, Anal. Chem. 2019) and the "
            "2020 POD papers (counting-mode POD and solvent-enhanced POD)."
        ),
        scope="thermal POD / solvent-enhanced POD",
        status="unavailable",
        notes=(
            # What these papers actually require (and the current engine lacks):
            #
            # 2019 POD (Anal. Chem. 91:9741):
            #   • photothermal excitation source Q(r,z,t) driving dn/dT
            #   • heat diffusion to glass substrate (substrate contributes signal)
            #   • diffracted-light intensity ΔP_D ∝ P_0 · (Δn_s − Δn_g)
            #
            # 2020 solvent-enhanced POD (Anal. Chem. 92:14366):
            #   • solvent-dependent dn/dT and diffraction factor (1/Δn)
            #   • signal sign flip when n_solvent crosses n_glass
            #   • optimal initial diffracted-light P_D (~15 mV at 1.1 kHz)
            #   • sensitivity > 30× water achievable with organic solvents
            #
            # 2020 counting POD (Anal. Chem. 92:3434):
            #   • photothermal absorption path (signal ∝ d³, volume)
            #   • 100 kPa → 0.17 mm/s flow, ~10 ms transit, counting threshold
            #
            # None of these are implemented; the current POD lane is a
            # frequency-separation / leakage surrogate only.
            "CURRENT: photothermal_pod diagnostics expose this unavailable "
            "boundary, but they do not implement the thermal field.",
            "MISSING: photothermal source term Q(r,z,t) and heat-diffusion model.",
            "MISSING: solvent-dependent dn/dT lane and signal sign-flip logic.",
            "MISSING: optimal P_D calculation and substrate heat contribution.",
            "MISSING: counting-mode absorption amplitude model (signal ∝ volume).",
            "DO NOT compare current POD lane signal amplitudes quantitatively "
            "against 2019/2020 POD paper figures — the physical model is absent.",
        ),
        reference_route=None,
        reference_solver_route=None,
        unavailable_reason=(
            "A true paper-aligned POD profile requires explicit thermal-POD "
            "physics (photothermal source, heat diffusion, solvent dn/dT, "
            "substrate contribution, P_D optimum) that are not currently "
            "implemented in any engine module."
        ),
    ),
}


def list_paper_aligned_profiles() -> dict[str, dict[str, object]]:
    return {
        name: {
            "description": profile.description,
            "scope": profile.scope,
            "status": profile.status,
            "notes": list(profile.notes),
            "reference_route": profile.reference_route,
            "reference_solver_route": profile.reference_solver_route,
            "unavailable_reason": profile.unavailable_reason,
        }
        for name, profile in PAPER_ALIGNED_PROFILES.items()
    }


def apply_paper_aligned_profile(
    base_cfg: SimulationConfig,
    profile_name: str,
) -> SimulationConfig:
    if profile_name not in PAPER_ALIGNED_PROFILES:
        raise ValueError(
            f"Unknown paper-aligned profile: {profile_name}. "
            f"Available: {sorted(PAPER_ALIGNED_PROFILES)}"
        )
    profile = PAPER_ALIGNED_PROFILES[profile_name]
    if profile.status != "available":
        raise ValueError(
            f"paper-aligned profile '{profile_name}' is not available: "
            f"{profile.unavailable_reason or 'no additional reason provided'}"
        )

    cfg = deepcopy(base_cfg)

    if profile_name == "diffraction_2020":
        cfg.reference_model = "paper_aligned_phase_filter"
        cfg.reference_route = "paper_aligned_comparison"
        cfg.illumination_mode = "overfill"
        cfg.collection_integration_mode = "pupil_slit_surrogate"
        return cfg

    if profile_name == "nodi_2022":
        cfg.reference_model = "paper_aligned_phase_filter"
        cfg.reference_route = "paper_aligned_comparison"
        cfg.illumination_mode = "overfill"
        cfg = apply_readout_preset(cfg, "tsuyama_2022_counting_10sigma")
        return cfg

    if profile_name in {"paired_2024", "paired_2024_10sigma"}:
        cfg.reference_model = "paper_aligned_phase_filter"
        cfg.reference_route = "paper_aligned_comparison"
        cfg.illumination_mode = "overfill"
        readout_preset = (
            "tsuyama_2024_paired_10sigma"
            if profile_name == "paired_2024_10sigma"
            else "tsuyama_2024_paired_5sigma"
        )
        cfg = apply_readout_preset(cfg, readout_preset)
        return cfg

    raise AssertionError(f"Unhandled available paper-aligned profile: {profile_name}")
