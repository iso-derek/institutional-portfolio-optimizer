# Development status

**Updated:** 5 November 2026  
**Phase:** Project A, milestone A1 — ready for draft-PR review

## Completed and present on this development branch

- Existing walk-forward allocation research, costs, drift, shrinkage/risk-parity comparisons and stress scenarios retained.
- Existing reproducible launcher, run-history and compatibility-CI work from draft PR #3 retained as the branch baseline.
- Solved long-only, fully invested minimum-variance frontier across feasible target returns.
- Explicit solver validation for finite objectives and weights, weight bounds, full investment and target-return residuals.
- Price-return calculation excludes transitions that bridge rows removed by bounded-fill/common-date cleaning.
- Dashboard launches with a responsive deterministic demonstration; live provider access is an explicit mode.
- Focused regression fixtures cover invalid solver output, a known two-asset frontier solution, equal-return degeneracy and removed-row transitions.
- Desktop visual verification confirms the default demonstration mode, disclosure banner and solved-frontier presentation render correctly.

## In progress

- Draft-PR review and CI validation for this milestone.

## Tests

- Historical draft-PR CI: 34 tests passed on the inspected compatibility run; this is prior evidence, not a result from this branch.
- Current branch local result: 38 tests passed in 41.010 seconds on Python 3.12 with the tested direct dependency set; `pip check` reported no broken requirements.

## Known issues and blockers

- The recorded market experiment remains synthetic because the earlier live provider request was rate-limited.
- Real screenshots, a locked real-data study and deployment acceptance remain outstanding.

## Next three priorities

1. Reproduce a provenance-recorded real-data walk-forward study with a frozen input artifact and honest provider/licensing notes.
2. Add alpha, rolling risk metrics and reconciled return attribution before the documentation/UI acceptance milestone.
3. Capture genuine screenshots after the analytical surface is stable, then complete responsive and accessibility acceptance.

## Remaining before a stable release

- Verified real-data research and confirmatory holdout design.
- Rolling/benchmark metrics and return attribution.
- Full README architecture/mathematics/usage/deployment sections, genuine screenshots and visual/accessibility review.
- Clean-install rehearsal, security/dependency review and user acceptance.
- Review and approval before merging to `main`; deployment requires separate approval.
