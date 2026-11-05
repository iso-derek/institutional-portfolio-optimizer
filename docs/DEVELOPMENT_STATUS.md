# Development status

**Updated:** 5 November 2026  
**Phase:** Project A, milestone A2 — provenance-locked real-data study

## Completed and present on this development branch

- Existing walk-forward allocation research, costs, drift, shrinkage/risk-parity comparisons and stress scenarios retained.
- Existing reproducible launcher, run-history and compatibility-CI work from draft PR #3 retained as the branch baseline.
- Solved long-only, fully invested minimum-variance frontier across feasible target returns.
- Explicit solver validation for finite objectives and weights, weight bounds, full investment and target-return residuals.
- Price-return calculation excludes transitions that bridge rows removed by bounded-fill/common-date cleaning.
- Dashboard launches with a responsive deterministic demonstration; live provider access is an explicit mode.
- Focused regression fixtures cover invalid solver output, a known two-asset frontier solution, equal-return degeneracy and removed-row transitions.
- Desktop visual verification confirms the default demonstration mode, disclosure banner and solved-frontier presentation render correctly.
- Live SPY/IEF/GLD adjusted-price study completed from 2,011 observations spanning 2 January 2018 through 31 December 2025.
- Frozen-input sidecar records the exact SHA-256, acquisition request, source, date coverage, limitations and provider-usage links.
- Live acquisition fails closed; replay rejects missing, changed or synthetic inputs and reproduces from the exact frozen bytes.

## In progress

- Milestone A2 test, documentation and draft-PR review.

## Tests

- Historical draft-PR CI: 34 tests passed on the inspected compatibility run; this is prior evidence, not a result from this branch.
- Current branch local result: 42 tests passed in 21.806 seconds on Python 3.12 with the tested direct dependency set; compilation passed and `pip check` reported no broken requirements.

## Known issues and blockers

- Provider data is retained locally but not committed because redistribution rights have not been established.
- The real-data run recorded two disclosed shrinkage-risk-parity optimiser fallbacks.
- Real screenshots and deployment acceptance remain outstanding.

## Next three priorities

1. Add alpha, rolling risk metrics and reconciled return attribution before the documentation/UI acceptance milestone.
2. Capture genuine screenshots after the analytical surface is stable, then complete responsive and accessibility acceptance.
3. Rehearse a clean install and complete security/dependency review before deployment acceptance.

## Remaining before a stable release

- Verified real-data research and confirmatory holdout design.
- Rolling/benchmark metrics and return attribution.
- Full README architecture/mathematics/usage/deployment sections, genuine screenshots and visual/accessibility review.
- Clean-install rehearsal, security/dependency review and user acceptance.
- Review and approval before merging to `main`; deployment requires separate approval.
