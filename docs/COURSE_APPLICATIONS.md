# Finance learning → portfolio improvements

This sprint extends the existing Python/Streamlit project. The purpose is to make
finance concepts visible in decisions and explanations, while checking that the
underlying calculations are correct. It does not recreate the project or claim
that a course certificate by itself establishes professional model validation.

## Implemented in this sprint

| Course concept | Product behaviour | Where to inspect |
| --- | --- | --- |
| BMC equities: indices and investment returns | A benchmark is selected separately and compared over aligned dates. SPY is not automatically a holding. Adjusted prices are required; unadjusted close is not silently substituted. | Performance tab; `benchmark_comparison` |
| Finance Fundamentals: diversification | Capital share is compared with covariance-based risk share. Effective holdings and a volatility-reduction diagnostic make concentration visible. | Diversification tab; `diversification_metrics` |
| Finance Fundamentals: risk and reward | Return, volatility, drawdown and tail loss are presented together; no claim that accepting more risk guarantees better realised returns. | Summary, Risk and Optimisation tabs |
| Finance Fundamentals: evidence and due diligence | Synthetic data is visibly flagged; missing assets and failed optimisers are disclosed. Exports retain provenance and assumptions. | Data tab; data loader |
| Research extension: test whether diversification helps | Chronological comparison of equal weight, minimum volatility and capped minimum volatility, including drift, costs and exploratory uncertainty. | Research Lab; `research.py`; [protocol](RESEARCH_PROTOCOL.md) |
| Python/statistics skills being developed | Aligned observations, explicit return calculations, covariance, finite-input validation and reproducible checks. This is an application of studied concepts, not a statement that the HKUST course is complete. | `src/` and `tests/` |

## Understand the calculations

### 1. Return and compounding

For an adjusted price moving from 100 to 102, the daily return is
`102 / 100 - 1 = 2%`. Portfolio return is `sum(weight × asset return)`.

A 10% loss followed by a 10% gain leaves `0.9 × 1.1 = 0.99`, a 1% loss.
An arithmetic average alone does not describe compounded wealth.

- CAGR: `product(1 + returns) ** (252 / observations) - 1`.
- Volatility: sample standard deviation of daily returns times `sqrt(252)`.
- The fixed-weight return series assumes daily rebalancing and no costs.

### 2. The number of holdings is not the number of independent risks

Six equally weighted stocks have effective holdings of six:
`1 / sum(weight²) = 6`. They can still share the same sector and market exposures.

Risk share uses both individual volatility and covariance:
`weight_i × (covariance × weights)_i / portfolio variance`.

For two equally weighted, perfectly correlated assets where A is twice as
volatile as B, A contributes two-thirds of portfolio variance, despite receiving
only half the capital. Their combined volatility receives no diversification
benefit relative to the same-volatility, perfectly correlated reference.

The displayed diversification reduction is
`1 - portfolio_volatility / weighted_average_individual_volatility`.
It is a sample covariance diagnostic, not protection against future losses.
Negative risk shares are possible for hedging assets. Risk shares are undefined
when portfolio variance is zero.

### 3. Sharpe and Sortino answer different questions

Convert the user-selected annual risk-free rate into a daily compounded rate.

- Sharpe = mean daily excess return / daily sample volatility × `sqrt(252)`.
- Sortino = mean daily excess return / daily downside deviation × `sqrt(252)`.
- Downside deviation = `sqrt(mean(min(return - daily_target, 0)²))`.

Downside deviation includes all observations in the denominator. Measuring only
the standard deviation of negative returns would incorrectly ignore the
frequency and level of shortfalls. Undefined ratios display as N/A.

### 4. Drawdown starts with the money initially invested

If the first two daily returns are −10% and −10%, wealth falls from 1 to 0.9 to
0.81. Drawdowns must include −10% and −19%; the first observed value is not a
new starting peak that erases the first loss.

### 5. Tail loss needs a horizon and an evidence count

At 95% confidence, historical VaR uses the negative 5th percentile of observed
daily returns, with linear interpolation. CVaR averages observed returns at or
below that threshold and reverses the sign into a loss convention. This is a
finite-sample estimator; ties can increase the count of included observations.

For a $100,000 portfolio, a one-day VaR of 2% is a $2,000 loss threshold estimate,
not a $2,000 worst-case limit. Higher confidence leaves fewer observations in the
tail. The dashboard flags counts below 20 as a learning heuristic, not a
regulatory minimum.

## What was corrected

- Sharpe now uses arithmetic daily excess return consistently with the optimiser.
- Sortino now measures downside deviation against the chosen target across all days.
- Drawdown now includes the initial investment.
- Long-only weights reject negative, non-finite, empty and zero-total allocations.
- Source metadata distinguishes adjusted downloads, synthetic fallback and legacy
  CSV files of unknown provenance.
- A random portfolio cloud is labelled as an opportunity set, not a solved frontier.
- The old Black-Litterman placeholder is exposed as a historical-return heuristic.
- Optimiser failures explicitly report the equal-weight fallback.

## A short learning exercise

1. Start with equal weights. Write down the largest risk contributor and its
   capital share. Explain why the two percentages differ.
2. Select minimum volatility. Explain the observed trade-off between historical
   return, concentration and volatility.
3. Change confidence to 99%. Explain why the tail estimate has less supporting data.
4. Compare with the benchmark. Explain why beating it within the same sample used
   to choose weights does not establish future outperformance.
5. Download the summary and identify the source, date range, weights and assumptions
   that another analyst would need to reproduce it.

## Next iterations across the existing projects

These are follow-up work, not implemented features or claims about completed courses.

| Existing project | Suitable next finance application |
| --- | --- |
| Institutional Portfolio Optimizer | Sector/country/currency exposure; inflation-adjusted returns; duration-based bond sensitivity and FX scenarios; point-in-time datasets and independent holdout evaluation beyond the first walk-forward experiment. |
| Credit Risk Analytics Platform | Borrower financial ratios, credit-quality explanations, PD calibration, and scenario-dependent loss assumptions. Statistical validation needs separate work beyond introductory finance learning. |
| Market Intelligence AI Platform | Distinguish earnings, inflation, interest-rate and currency news; keep source/date evidence beside each claim; compare actual earnings with expectations and valuation context. |

## References and limits

- [BIS market-risk terminology](https://www.bis.org/committees/bcbs/basel-framework/standard/mar/10/inforce/2022-01-01/published/2019-12-15): VaR and Expected Shortfall concepts.
- [NumPy quantile documentation](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html): finite-sample quantile conventions.

The exposition is original; it is not an official Bloomberg course document.
Sector exposure, FX conversion, a full Black-Litterman model and realistic execution
remain unimplemented. The new Research Lab adds periodic out-of-sample evaluation
and a proportional cost approximation; it does not eliminate universe selection
bias or prove a strategy works. Live provider availability was not a dependency of
the offline test suite.
