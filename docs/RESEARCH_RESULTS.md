# Phase 2 experiment — 2026-10-05

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
