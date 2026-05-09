"""Case-level recompute manifest and hash provenance diagnostics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, cast

from .data_objects import Channel, OpticalSystem, Particle, SimulationConfig


RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS = (
    "manifest_id",
    "sweep_manifest_id",
    "config_hash",
    "particle_hash",
    "channel_hash",
    "optical_hash",
    "case_hash",
    "case_count",
    "estimated_memory_GB",
    "estimated_runtime_proxy",
    "worker_count",
    "chunk_size",
    "checkpoint_interval",
    "failed_case_count",
    "resume_from_checkpoint_supported",
    "random_seed_policy",
    "rng_stream_id",
    "recompute_manifest_gate_passed",
)


def _to_stable_jsonable(value: Any) -> Any:
    if not isinstance(value, type) and is_dataclass(value):
        return _to_stable_jsonable(asdict(cast(Any, value)))
    if isinstance(value, dict):
        return {str(key): _to_stable_jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_to_stable_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_to_stable_jsonable(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"), default=str),
        )
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def _stable_hash(payload: Any) -> str:
    stable = json.dumps(
        _to_stable_jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]


def build_recompute_manifest_diagnostics(
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Return deterministic per-case manifest provenance fields."""
    particle_hash = _stable_hash(particle)
    channel_hash = _stable_hash(channel)
    optical_hash = _stable_hash(optical)
    config_hash = _stable_hash(sim_cfg)
    case_hash = _stable_hash(
        {
            "particle": particle_hash,
            "channel": channel_hash,
            "optical": optical_hash,
            "config": config_hash,
        }
    )
    manifest_id = f"manifest_{case_hash}"
    random_seed_policy = (
        "fixed_seed" if sim_cfg.random_seed is not None else "numpy_default_rng_entropy"
    )
    rng_stream_id = (
        f"seed_{int(sim_cfg.random_seed)}"
        if sim_cfg.random_seed is not None
        else f"entropy_case_{case_hash}"
    )
    estimated_runtime_proxy = int(sim_cfg.n_events) * int(sim_cfg.n_samples)
    estimated_memory_GB = (
        estimated_runtime_proxy
        * 8.0
        * 6.0
        / 1.0e9
    )

    return {
        "manifest_id": manifest_id,
        "sweep_manifest_id": manifest_id,
        "config_hash": f"config_{config_hash}",
        "particle_hash": f"particle_{particle_hash}",
        "channel_hash": f"channel_{channel_hash}",
        "optical_hash": f"optical_{optical_hash}",
        "case_hash": f"case_{case_hash}",
        "case_count": 1,
        "estimated_memory_GB": estimated_memory_GB,
        "estimated_runtime_proxy": estimated_runtime_proxy,
        "worker_count": 1,
        "chunk_size": None,
        "checkpoint_interval": None,
        "failed_case_count": 0,
        "resume_from_checkpoint_supported": False,
        "random_seed_policy": random_seed_policy,
        "rng_stream_id": rng_stream_id,
        "recompute_manifest_gate_passed": True,
    }
