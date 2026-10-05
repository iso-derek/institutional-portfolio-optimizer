"""Chronological portfolio experiment: concentration caps, drift and trading costs.

At return index t, targets use rows [t-lookback:t] only. Targets apply before the
next return at t. Holdings drift between rebalances. Cost is an explicitly
approximate fee on the sum of absolute changes in risky-asset weights; initial
deployment from cash is charged too. Nothing here establishes causal or novel
academic findings without a suitable dataset and research design.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analytics import (TRADING_DAYS, annualized_return, annualized_volatility,
                       conditional_var, max_drawdown, sharpe_ratio)
from modelling import minimum_volatility_portfolio

STRATEGIES = ("Equal weight", "Minimum volatility", "Capped minimum volatility")


def paired_block_interval(difference: pd.Series, block_size: int = 21, draws: int = 500, seed: int = 42) -> tuple[float, float]:
    """Exploratory paired circular-block interval for annual mean return difference.

    Resample the SAME dates across strategies by resampling their difference.
    This preserves within-block dependence, not every aspect of the time series.
    It does not correct for repeated specification search or small-sample bias.
    """
    values = difference.to_numpy(dtype=float)
    if len(values) < 2 or not np.isfinite(values).all() or block_size < 1 or draws < 2:
        raise ValueError("Need finite paired observations, a positive block size and at least two draws.")
    rng = np.random.default_rng(seed)
    size = min(block_size, len(values))
    if len(values) < 2 * size:
        # A single circular block can only rotate the same sample, falsely
        # producing a zero-width interval for the mean.
        return (np.nan, np.nan)
    starts = rng.integers(0, len(values), size=(draws, int(np.ceil(len(values) / size))))
    indices = ((starts[..., None] + np.arange(size)) % len(values)).reshape(draws, -1)[:, :len(values)]
    estimates = values[indices].mean(axis=1) * TRADING_DAYS
    return tuple(float(x) for x in np.quantile(estimates, [.025, .975]))


def walk_forward_study(
    returns: pd.DataFrame,
    lookback: int = 126,
    rebalance_every: int = 21,
    max_weight: float = .35,
    cost_bps: float = 10.0,
    risk_free_rate: float = .02,
    confidence: float = .95,
) -> dict[str, object]:
    """Compare three strategies on exactly the same out-of-sample dates."""
    if returns.empty or returns.columns.has_duplicates or returns.index.has_duplicates or not returns.index.is_monotonic_increasing:
        raise ValueError("Supply chronological returns with unique dates and asset columns.")
    if not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError("Returns must be finite and greater than −100%.")
    if not isinstance(lookback, int) or lookback < 2 or not isinstance(rebalance_every, int) or rebalance_every < 1:
        raise ValueError("Use a training window of at least two observations and a positive rebalance interval.")
    if len(returns) < lookback + max(2, rebalance_every):
        raise ValueError("Need at least one full out-of-sample rebalance period after the training window.")
    n_assets = len(returns.columns)
    if not np.isfinite(max_weight) or not 0 < max_weight <= 1 or n_assets * max_weight < 1 - 1e-10:
        raise ValueError("Concentration cap is infeasible for the selected number of assets.")
    if not np.isfinite(cost_bps) or not 0 <= cost_bps <= 100:
        raise ValueError("Trading costs must be between 0 and 100 basis points per traded notional.")
    if not np.isfinite(risk_free_rate) or not 0 <= risk_free_rate <= .2 or not 0 < confidence < 1:
        raise ValueError("Use a risk-free rate between 0% and 20% and a confidence between 0 and 1.")

    test_index = returns.index[lookback:]
    net = pd.DataFrame(index=test_index, columns=STRATEGIES, dtype=float)
    gross = net.copy()
    current = {name: np.zeros(n_assets) for name in STRATEGIES}
    trade_records, weight_records, failures = [], [], []
    rate = cost_bps / 10000

    for offset in range(lookback, len(returns), rebalance_every):
        training = returns.iloc[offset - lookback:offset]
        targets = {STRATEGIES[0]: np.repeat(1 / n_assets, n_assets)}
        for name, cap in [(STRATEGIES[1], 1.0), (STRATEGIES[2], max_weight)]:
            fitted = minimum_volatility_portfolio(training, risk_free_rate, max_weight=cap)
            targets[name] = fitted["weights"].to_numpy()
            if not fitted["success"]:
                failures.append({"date": returns.index[offset], "strategy": name, "message": fitted["message"]})
        block = returns.iloc[offset:offset + rebalance_every]
        for name, target in targets.items():
            traded = float(np.abs(target - current[name]).sum())
            fee_fraction = rate * traded
            trade_records.append({"Date": block.index[0], "strategy": name,
                                  "training_end": training.index[-1], "traded_fraction": traded,
                                  "cost_fraction": fee_fraction, "largest_target_weight": float(target.max())})
            weight_records.append({"Date": block.index[0], "strategy": name,
                                   "training_end": training.index[-1],
                                   **{asset: float(w) for asset, w in zip(returns.columns, target)}})
            held = target.copy()
            for day, (timestamp, row) in enumerate(block.iterrows()):
                asset_return = row.to_numpy()
                gross_return = float(held @ asset_return)
                gross.loc[timestamp, name] = gross_return
                net.loc[timestamp, name] = (1 - (fee_fraction if day == 0 else 0)) * (1 + gross_return) - 1
                held = held * (1 + asset_return) / (1 + gross_return)
            current[name] = held

    trades = pd.DataFrame(trade_records)
    summary = []
    for name in STRATEGIES:
        r = net[name]
        difference = r - net[STRATEGIES[0]]
        low, high = paired_block_interval(difference, block_size=rebalance_every)
        strategy_trades = trades[trades["strategy"] == name]
        summary.append({"strategy": name, "net_cagr": annualized_return(r),
                        "gross_cagr": annualized_return(gross[name]),
                        "net_volatility": annualized_volatility(r), "net_sharpe": sharpe_ratio(r, risk_free_rate),
                        "max_drawdown": max_drawdown(r), "one_day_cvar": conditional_var(r, confidence),
                        "annual_traded_fraction": float(strategy_trades["traded_fraction"].sum() * TRADING_DAYS / len(r)),
                        "mean_largest_target_weight": float(strategy_trades["largest_target_weight"].mean()),
                        "annual_mean_excess_vs_equal": float(difference.mean() * TRADING_DAYS),
                        "mean_excess_ci_low": low, "mean_excess_ci_high": high})
    return {"summary": pd.DataFrame(summary).set_index("strategy"), "net_returns": net,
            "gross_returns": gross, "growth": (1 + net).cumprod() * 100,
            "trades": trades, "target_weights": pd.DataFrame(weight_records), "failures": failures,
            "settings": {"lookback": lookback, "rebalance_every": rebalance_every,
                         "max_weight": max_weight, "cost_bps": cost_bps,
                         "risk_free_rate": risk_free_rate, "confidence": confidence,
                         "bootstrap_draws": 500, "bootstrap_seed": 42, "bootstrap_block": rebalance_every}}
