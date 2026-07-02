# NODI COMSOL Package C Runtime Substep Policy Design

- Disposition: `NODI_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_AUTHORIZED_PACKET_GATED`
- Policy rows: `6`.
- Max required substeps: `526`.
- Prohibitive substep cost rows: `1`.
- Runtime policy authorization status: `authorized_by_user_ledger_execution_packet_required`.
- Boundary: runtime/substep policy path is authorized, but runtime output remains execution-packet-gated; no COMSOL launch, no .mph load, no numeric PRS/EAS, no solver/wet/route/yield/detection/fab/production claims from this packet.
