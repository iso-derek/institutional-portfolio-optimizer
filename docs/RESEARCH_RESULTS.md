# Phase 2 real-data experiment — 2026-11-05

The fixed SPY/IEF/GLD request succeeded through yfinance with complete adjusted-price columns. The frozen input contains 2,011 rows from 2 January 2018 through 31 December 2025 and has SHA-256 `8ed6089e95cd70d584da170351cb942004383986871673140887416d286945ac`. A second run loaded those exact bytes through the provenance sidecar and reproduced the aggregate results and recorded failure set.

| Rule | Net CAGR | Annual volatility | Maximum drawdown |
|---|---:|---:|---:|
| Equal weight | 11.67% | 9.18% | -17.02% |
| Minimum volatility | 4.01% | 6.51% | -19.86% |
| Capped minimum volatility | 11.18% | 8.98% | -17.37% |
| Shrunk minimum volatility | 6.07% | 6.85% | -18.98% |
| Shrinkage risk parity | 8.97% | 7.80% | -17.60% |
| Static defensive risk parity | 5.52% | 3.89% | -8.37% |
| Volatility-adaptive risk parity | 8.24% | 6.98% | -16.57% |

Equal weight had the highest sample CAGR and Sharpe ratio. The static defensive rule had the smallest drawdown, but also substantially lower return. Adaptive minus static annual arithmetic mean return was 2.72 percentage points with an exploratory paired block interval [0.15, 5.11] percentage points. That interval is not corrected for strategy selection and does not establish causality, market timing skill or a tradable edge.

Two shrinkage-risk-parity optimisation fallbacks were recorded, on 3 December 2020 and 7 June 2023. They are retained as failure evidence rather than silently discarded. The fixed current-fund universe is exposed to survivorship and availability bias; the provider adjustment method and currency treatment were not independently audited.

The frozen price CSV remains local and ignored because redistribution rights have not been established. The committed record contains the input identity and aggregates, not Yahoo observations. See the [yfinance disclaimer](https://ranaroussi.github.io/yfinance/) and [Yahoo's regional terms selector](https://legal.yahoo.com/index.html).

Reproduce a fresh acquisition with `python launch.py research --live`. Replay an authorised local artifact with `python scripts/run_research.py --input outputs/study_prices.csv`; the command refuses a missing sidecar, changed hash or synthetic source.

## Archived synthetic experiment — 2026-10-05

The attempted real SPY/IEF/GLD adjusted-price download returned HTTP 429 rate-limit errors. The live benchmark stopped without substituting data. The following run deliberately uses fictional correlated price paths bearing those column labels, seed 42, from 2018-01-01 through 2025-12-31. They do not model the actual economics of those assets.

| Rule | Net CAGR | Annual volatility | Maximum drawdown |
|---|---:|---:|---:|
| Equal weight | 15.20% | 20.38% | -30.47% |
| Minimum volatility | 14.22% | 18.03% | -20.59% |
| Capped minimum volatility | 14.62% | 20.03% | -30.41% |
| Shrunk minimum volatility | 14.35% | 18.08% | -21.64% |
| Shrinkage risk parity | 14.71% | 19.27% | -26.84% |
| Static defensive risk parity | 8.69% | 9.66% | -13.58% |
| Volatility-adaptive risk parity | 14.99% | 19.19% | -26.68% |

The static cash allocation reduces both return and risk. The adaptive rule remains mostly invested on these paths: its higher return than static defence comes with almost twice the volatility. This does not establish successful market timing. The adaptive/equal-weight annual mean return difference is -0.42 percentage points, with exploratory block interval [-2.26, 1.69] percentage points.

Adaptive minus static annual mean return is 7.01 percentage points, with an exploratory paired block interval [0.47, 13.91]. These are arithmetic mean-return differences, not CAGR differences. Neither synthetic interval establishes a financial investment advantage. No solver fallbacks occurred.

Settings: lookback 126, rebalance 21, cost 10 bps, constant assumed cash rate 2%, volatility trigger 1.25, defensive risky exposure 50%, bootstrap 500 draws/seed 42/block 21.

Input price hash: `61248504c56aadba836ac68fee6ebe677d71f380f3a85db1744c2085421a9fdb`.

Reproduce with `python scripts/run_research.py`; use `--live` only when complete real prices can be fetched. Tests verify seven-strategy accounting, future-data invariance, equal risk contributions, degenerate inputs and FX/inflation compounding.
