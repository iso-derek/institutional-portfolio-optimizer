# Concentration, risk and the cost of diversification

## Question and contribution

Do concentration limits improve the out-of-sample risk of minimum-volatility
allocations after costs? When do the risk and concentration benefits come at the
expense of return or additional trading?

The project-specific contribution is an auditable decision study: connect the
finance intuition of diversification to a controlled comparison, explain the
trade-offs and preserve enough information for another analyst to reproduce it.
This is not a claim that concentration caps, minimum variance or walk-forward
testing are academically new.

## Hypothesis and controls

**Working hypothesis:** a cap may limit unstable concentration in estimated
minimum-volatility allocations, but may also force exposure to less attractive
assets or increase trading. Improvement is an empirical question.

Compare the same asset universe, return dates, training window and execution
assumptions across:

1. Equal weight: a simple, interpretable baseline.
2. Uncapped long-only minimum volatility: the optimisation control.
3. Capped long-only minimum volatility: change only the target-weight constraint.

The cap constrains individual holdings, not sectors or correlated groups. It is
enforced when rebalancing; prices can move weights beyond the cap between trades.

## Initial specification

| Choice | Starting specification |
| --- | --- |
| Training window | Latest 126 daily return observations |
| Evaluation | Apply targets to later observations only |
| Rebalance interval | 21 return observations |
| Concentration cap | 35% per target holding, raised to 1/N if necessary for feasibility |
| Trading cost | 10 basis points of assumed traded notional |
| Shorting/leverage | Neither; fully invested long-only weights |
| Primary risk outcomes | Net volatility, maximum drawdown, one-day CVaR |
| Trade-offs | Gross/net CAGR, Sharpe, traded notional, largest target holding |
| Return uncertainty | Paired circular-block bootstrap, 500 draws, seed 42 |

These are chosen research assumptions, not estimates of current transaction costs.
Commit the specification before examining a confirmatory holdout. The interactive
controls are for exploration; repeated tuning is not independent confirmation.

## Chronology and accounting

At index `t`, fit targets using `returns.iloc[t-lookback:t]`, excluding the
return at t. The target is applied before observing that next return. Keep
asset shares invested and allow portfolio weights to drift until the next
scheduled rebalance. Never hold the fitted weights artificially constant every
day between research rebalances.

At rebalancing, traded fraction is `sum(abs(target - pretrade_weights))`.
It counts buys plus sells. Initial cash deployment incurs traded fraction 1.
The approximation for cost fraction is `(cost_bps / 10_000) × traded_fraction`.
Apply it before the next return: `(1 - cost_fraction) × (1 + gross_return) - 1`.
It ignores the small effect of funding fees on executed trade notional as well as
spread variation, market impact, liquidity constraints, taxes and execution delay.

An optimiser failure is recorded and uses equal weights. Inspect failures instead
of treating such a run as the intended optimisation strategy.

## Uncertainty and interpretation

For each strategy, subtract equal-weight net returns on the same dates. Resample
that paired difference in fixed-length blocks with circular wrapping. This keeps
the comparison paired and preserves some within-block serial dependence. The
reported percentile interval is for annualised arithmetic mean return difference,
not CAGR, volatility or drawdown. Fewer than two blocks yields N/A rather than a
misleading zero-width interval.

Block length equals the rebalance interval as a transparent initial convention;
it is not an optimally estimated block length. Later work should examine block
length sensitivity, structural breaks, larger replication counts and separate
uncertainty for downside-risk differences. Daily rebalancing implies block length
one and therefore does not retain serial dependence in that setting.

An interval crossing zero is compatible with no mean-return advantage under these
assumptions. An interval excluding zero is not proof of causality or a tradable
edge. The analysis does not adjust for searching many settings or strategies.

## Data and threats to validity

- A synthetic run demonstrates mechanics only. It supplies no evidence about
  actual markets. Do not write a result claiming outperformance from a demo.
- Use verified, appropriately licensed adjusted prices. This implementation does
  not independently audit vendor dividend adjustments, splits or currencies.
- The current user-selected universe may include only today's survivors. Full-
  period availability filtering also conditions the sample on later information.
  Chronological fitting alone does not eliminate these sources of bias.
- Annualisation assumes 252 daily observations. Common-date filtering and missing
  price fills can distort this assumption and must be reviewed for the dataset.
- Small samples, non-stationary correlations and stale quotes can invalidate
  appealing conclusions. The UI flags holdouts shorter than one trading year.
- Choosing a favourable period or cap after seeing results overfits the evaluation.
  Confirmatory work needs a locked, point-in-time universe and unseen holdout.

## Reproduce a run

The Research Lab export includes `settings.json`, `input_returns.csv`,
`summary.csv`, `net_returns.csv`, `gross_returns.csv`, `trades.csv`,
`target_weights.csv` and `optimiser_failures.json`.

From a checkout with dependencies installed:

```python
import json
import sys
import pandas as pd

sys.path.insert(0, "src")
from research import walk_forward_study

settings = json.load(open("settings.json", encoding="utf-8"))
returns = pd.read_csv("input_returns.csv", index_col=0, parse_dates=True)
keys = ("lookback", "rebalance_every", "max_weight", "cost_bps", "risk_free_rate", "confidence")
study = walk_forward_study(returns, **{key: settings[key] for key in keys})
print(study["summary"])
```

Preserve the Git commit and dependency versions with any report. Numeric results
can vary slightly with optimiser/library versions. The dataset hash identifies
the in-memory input used by the dashboard, not an independent source certification.

## Tests and a research write-up

Tests verify that training ends before the next evaluated return, later data
changes cannot alter earlier target weights, caps hold, positions drift, costs
reduce wealth and initial cash deployment incurs costs. These checks validate
mechanics, not the hypothesis.

A future write-up should contain the motivation, fixed specification, data
provenance, results, uncertainty, cost sensitivity, failure cases and limitations.
Report negative findings. Do not select a "winner" simply because it has the
highest realised return in one sample.

## Method references

- [scikit-learn: time-ordered train/test splits](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) — the chronology principle; this project implements its own rolling allocation loop.
- [arch: circular block bootstrap](https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html) — resampling equal-length blocks with circular wrapping; the small paired-mean implementation here uses NumPy.
