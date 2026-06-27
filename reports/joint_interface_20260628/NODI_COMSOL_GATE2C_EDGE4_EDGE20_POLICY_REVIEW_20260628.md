# Gate2C Edge4 To Edge20 Policy Review

COMSOL proxy-bin rows use edge4 quarter bins over edge_norm_1d. NODI PRS edge20 uses 20 bins over edge_norm_1d at 0.05 increments.

A candidate coarse-to-fine review grouping is five PRS edge20 bins per COMSOL quarter bin. This is review-only and not a direct PRS bin mapping.

Policy is not approved. Approval would require error bounds, coverage checks, monotonicity or conservatism criteria, explicit loss semantics, and all decision-use flags remaining false until a future gate.
