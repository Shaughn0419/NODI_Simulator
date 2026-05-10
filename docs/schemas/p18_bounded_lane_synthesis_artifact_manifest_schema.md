# P18 Bounded-Lane Synthesis Artifact Manifest Schema

Required role: `bounded_lane_synthesis_artifact_manifest`.

The manifest enumerates the P18 registry, report, README, rank behavior summary CSV, synthesis record, and artifact manifest.

Required decision: `stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy`.

Required next stage: `P19_next_evidence_strategy_gate`.

The manifest must bind the six source trace CSV files by path and sha256. It is not a solver execution artifact and must keep route promotion blocked.
