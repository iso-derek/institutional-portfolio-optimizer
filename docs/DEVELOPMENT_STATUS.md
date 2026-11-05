# Development status

**Updated:** 5 November 2026  
**Phase:** Project A, milestone A3 — benchmark diagnostics and reconciled attribution

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
- Benchmark comparison now includes aligned Jensen-style alpha and information ratio alongside beta and tracking error.
- Rolling 63-observation portfolio/benchmark volatility, beta, tracking error and maximum drawdown are visible in the Performance tab.
- Asset wealth-change attribution reconciles exactly to compounded portfolio return under the disclosed fixed-weight daily-rebalancing assumption.

## In progress

- Milestone A3 draft-PR review and CI confirmation.

## Tests

- Historical draft-PR CI: 34 tests passed on the inspected compatibility run; this is prior evidence, not a result from this branch.
- Current branch local result: 45 tests passed in 34.650 seconds on Python 3.12 with the tested direct dependency set; compilation passed, `pip check` reported no broken requirements, and the default dashboard was visually verified with benchmark alpha, rolling risk and reconciled attribution rendered correctly.

## Known issues and blockers

- Provider data is retained locally but not committed because redistribution rights have not been established.
- The real-data run recorded two disclosed shrinkage-risk-parity optimiser fallbacks.
- Real screenshots and deployment acceptance remain outstanding.

## Next three priorities

1. Capture genuine screenshots now that the core analytical surface is stable, then complete responsive and accessibility acceptance.
2. Rehearse a clean install and complete security/dependency review before deployment acceptance.
3. Design a confirmatory point-in-time universe and unseen holdout before making empirical performance claims.

## Remaining before a stable release

- Verified real-data research and confirmatory holdout design.
- Full README architecture/mathematics/usage/deployment sections, genuine screenshots and visual/accessibility review.
- Clean-install rehearsal, security/dependency review and user acceptance.
- Review and approval before merging to `main`; deployment requires separate approval.
