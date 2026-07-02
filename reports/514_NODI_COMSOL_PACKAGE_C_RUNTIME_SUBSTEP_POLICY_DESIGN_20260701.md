# NODI COMSOL Package C Runtime Substep Policy Design

- Disposition: `NODI_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_AUTHORIZED_PACKET_GATED`
- Source head: `84faf70b62acb66adf2a3527607df76c51965833`
- This packet maps the dt-refinement requirements into fail-closed runtime/substep policy classes.
- Policy rows: `6`.
- Low/moderate/high/prohibitive rows: `4` / `1` / `0` / `1`.
- Max required substeps to meet threshold: `526`.
- Runtime policy authorization status: `authorized_by_user_ledger_execution_packet_required`.
- GitHub visibility: `local_worktree_pre_commit_urls_valid_after_publish`.
- Boundary: policy path authorized; guarded runtime output requires execution packet pass and case-level guard evidence.
- Machine-readable support: `reports/joint_interface_20260701`.
