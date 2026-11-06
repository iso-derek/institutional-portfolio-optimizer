# Development status

**Updated:** 6 November 2026
**Phase:** Project A, milestone A9 — release-candidate assurance

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
- Clean installation succeeded from a short Windows environment path after the nested checkout exposed a documented legacy path-length failure.
- All eight direct dependencies used by compatibility CI are pinned in `requirements-tested.txt`; the fresh environment passes `pip check`.
- Security policy, continuous dependency audit, changelog and release-evidence gate are present.
- Point-in-time universe manifests require dated, sourced, unique and explicitly verified membership records.
- Confirmatory protocols bind a universe hash, require a pre-holdout lock and keep holdout rows sealed until explicit unblinding.
- README architecture, data/licensing, installation, deployment and responsible-use sections now meet the release-candidate documentation scope.

## In progress

- Milestones A5–A9 draft-PR review and CI confirmation.

## Tests

- Current fresh-environment result: 51 tests passed in 39.830 seconds on Python 3.12; compilation and the release gate passed and `pip check` reported no broken requirements.
- The 6 November 2026 `pip-audit` found 39 advisories in transitive Pillow 12.3.0. All list Pillow 13.0.0 as the fix, while Streamlit 1.65.0 constrains Pillow below 13. This is documented in `SECURITY.md` and remains visible in non-blocking CI.

## Known issues and blockers

- Provider data is retained locally but not committed because redistribution rights have not been established.
- The real-data run recorded two disclosed shrinkage-risk-parity optimiser fallbacks.
- The committed point-in-time universe and protocol are templates; no confirmatory holdout result exists yet.
- Deployment acceptance remains blocked by the unresolved Pillow advisories and by the need to choose a hosting/privacy/cost configuration.

## Next three priorities

1. Replace the universe template with a licensed, archived point-in-time membership source and lock the protocol before acquiring holdout outcomes.
2. Upgrade when Streamlit supports the fixed Pillow release, then rerun the blocking dependency audit.
3. Review the release candidate and approve or reject a specific deployment target with its privacy and cost settings.

## Remaining before a stable release

- Verified point-in-time universe acquisition and one-time confirmatory holdout evaluation.
- Resolution or explicit risk acceptance for the current Pillow advisories.
- Final review and deployment approval for a named target; no public deployment has been performed.
