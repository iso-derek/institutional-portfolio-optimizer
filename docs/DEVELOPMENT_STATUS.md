# Development status

**Updated:** 5 November 2026  
**Phase:** Project A, milestone A4 — visual and accessibility acceptance

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
- Genuine desktop (1440 × 1100) and mobile (390 × 844 CSS pixels at 2× scale) screenshots are committed from the running deterministic application.
- Every chart, dataframe and editable grid now has an explicit accessible name, enforced by a static regression test.
- Desktop and mobile acceptance confirm readable disclosure, responsive KPI wrapping, usable navigation and no horizontal page overflow in the captured views.

## In progress

- Milestone A4 draft-PR review and CI confirmation.

## Tests

- Historical draft-PR CI: 34 tests passed on the inspected compatibility run; this is prior evidence, not a result from this branch.
- Current branch local result: 46 tests passed in 44.738 seconds on Python 3.12 with the tested direct dependency set; compilation and the screenshot-script syntax check passed, `pip check` reported no broken requirements, and genuine desktop/mobile captures were inspected after rendering.

## Known issues and blockers

- Provider data is retained locally but not committed because redistribution rights have not been established.
- The real-data run recorded two disclosed shrinkage-risk-parity optimiser fallbacks.
- Deployment acceptance remains outstanding.

## Next three priorities

1. Rehearse a clean install and complete security/dependency review before deployment acceptance.
2. Design a confirmatory point-in-time universe and unseen holdout before making empirical performance claims.
3. Complete final user acceptance and obtain explicit approval before merge or deployment.

## Remaining before a stable release

- Verified real-data research and confirmatory holdout design.
- Full README architecture/mathematics/usage/deployment sections.
- Clean-install rehearsal, security/dependency review and user acceptance.
- Review and approval before merging to `main`; deployment requires separate approval.
