# EV/NODI realism v2 no-measured-data consolidated roadmap

## Prime directive

v2 is a no-measured-data modeling lane.

It may use deterministic forward models, bounded priors, scenario bundles, posthoc audits, route-prior sensitivity, and artifact-gap registers. It must not start or plan in-v2 bench acquisition, experimental validation, solver export as new evidence, or empirical calibration.

The correct current decision is:

```text
PASS_TO_V2_NO_MEASURED_DATA_CLOSURE_ONLY
```

This supersedes the R7.2/R7.3 wording that implied an in-v2 acquisition runway. Those artifacts remain useful only as an artifact-gap register and chain-of-custody requirement sketch. They are not an authorization path for v2 acquisition.

## What v2 is allowed to claim

Allowed:

```text
relative proxy evidence
relative-with-priors scenario evidence
route-role stability under named priors
mesh/sign/route-model consistency within the synthetic model
bounded route-prior sensitivity
mechanistic-prior plausibility hypotheses
artifact gaps blocking physical calibration
```

Forbidden:

```text
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
bench-validated detector behavior
measured blank safety
empirical route promotion
main-660 redefinition by measured or unmeasured data
selected-annulus replacement of all-crossing ranking
```

## Current stage map

| Stage | Status | Meaning | Boundary |
|---|---:|---|---|
| v1 | complete | Relative/proxy full-grid engineering library. | Not overwritten by v2. |
| R2/R3 | complete | Anchor smoke, reduced grid, uncertainty expansion. | Scenario-prior only. |
| R4 | complete | Representative full-wave and route-model revision. | No R5 until gates were recovered. |
| R4.2 | complete | Main-660 near-wall coarse-screen adjudication. | Coarse-screen is warning-only; validation-grade recovered. |
| R5 | complete | Deterministic full-grid v2 scenario-prior expansion. | 256,256 rows, 8 named scenarios, no seeds. |
| R5.1 | complete | Route-role stability interpretation. | Warnings, not promotion. |
| R5.2 | complete | Bounded scenario-prior audit of 33 routes. | Systematic weak-reference/context warning found. |
| R5.3 | complete | Route-prior model revision audit. | Width-family explanation candidate found; not calibration. |
| R6 | complete | Route-prior sensitivity audit. | Width-family explanation robust over nearby candidates. |
| R7 | complete | Mechanistic decomposition audit. | Mechanistic hypotheses and artifact gaps identified. |
| R7.1 | acceptable as gap register | Operator artifact requirement protocol. | Requirements only; no measurement. |
| R7.2/R7.3 | reframed | Artifact-gap and chain-of-custody planning language. | Must not become v2 acquisition. |

## Corrected interpretation of late-stage outputs

R7.1 should be read as:

```text
operator artifact requirement register
```

R7.2 should be read as:

```text
artifact gap register with required fields and chain-of-custody expectations
```

R7.3 should be read as:

```text
post-v2 validation dependency envelope
```

They should not be read as:

```text
v2 acquisition plan
v2 acquisition protocol
v2 bench measurement runway
v2 experimental validation runway
```

## Main scientific storyline

The scientific path is now much cleaner:

1. v1 produced a relative engineering library.
2. v2 added instrument-aware priors and guardrails without measured data.
3. R4/R4.2 resolved main-660 near-wall/coarse-screen ambiguity at validation-grade mesh.
4. R5 showed full-grid scenario-prior route-role stability and warnings.
5. R5.1/R5.2 showed weak-reference and narrow/deep context-route warnings were systematic, not isolated.
6. R5.3/R6 showed those warnings are explainable by a low-dimensional width-family prior band, not by route-specific fitting.
7. R7 decomposed that prior into plausible mechanism families and identified which physical/operator artifacts would be needed before any empirical or calibrated claim.

The strongest no-measured-data conclusion is:

```text
Within the bounded v2 prior model, main-660 remains governance-locked and the R5.2 warning is plausibly explained by underweighted narrow-channel route risk. This is a relative, synthetic-prior conclusion, not an experimental validation.
```

## Current v2 closure target

The next and final v2-internal step should be a closure bundle, not R8 and not acquisition:

```text
V2_NO_MEASURED_DATA_CLOSURE
```

Required closure outputs:

```text
v2_no_measured_data_claim_boundary_summary
v2_route_role_final_status_table
v2_main660_status_summary
v2_width_prior_hypothesis_summary
v2_artifact_gap_register
v2_post_v2_validation_dependency_backlog
v2_forbidden_claim_guardrail_summary
v2_final_self_review_report
```

The closure bundle should answer:

```text
What is supported by v2 alone?
What remains only a hypothesis?
What claims are blocked without measured artifacts?
What would post-v2 validation need, if a separate empirical program is ever started?
```

## Decision rules from here

Continue within v2 only if the work is one of:

```text
consolidating existing results
correcting misleading wording
freezing claim boundaries
summarizing artifact gaps
checking consistency of existing artifacts
```

Stop or mark out-of-scope if the work requires:

```text
new measured data
bench acquisition
experimental validation
new solver exports as evidence
new scenario bundles
new stochastic seeds
new case rows
route promotion
main-660 redefinition
selected-annulus replacement
calibration or absolute claims
```

## Review cadence without external review

Since external review is paused, self-review should happen at decision-class boundaries, not after every small document:

```text
Small wording/config cleanup -> local self-check only
New closure bundle -> focused tests + self-review
Any proposed evidence-generation step -> stop as out-of-scope for v2
Any proposed calibrated/absolute claim -> stop as forbidden
```

## Final roadmap

The v2 roadmap is now:

```text
1. Freeze completed R2-R7 synthetic-prior evidence.
2. Correct R7.2/R7.3 acquisition wording into artifact-gap wording.
3. Prepare V2_NO_MEASURED_DATA_CLOSURE bundle.
4. End v2.
5. Treat any real artifact acquisition or experiment as a separate post-v2 program.
```

This keeps the model honest: v2 can be scientifically useful as a no-measured-data, instrument-aware, relative-prior decision model, but it cannot become a hidden calibration program.
