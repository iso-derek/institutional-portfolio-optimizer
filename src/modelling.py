"""Portfolio optimisation and simulation models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from analytics import TRADING_DAYS
from preprocessing import normalize_weights


def expected_returns(returns: pd.DataFrame) -> pd.Series:
    return returns.mean() * TRADING_DAYS


def expected_volatility(returns: pd.DataFrame, weights: np.ndarray) -> float:
    cov = returns.cov() * TRADING_DAYS
    return float(np.sqrt(weights.T @ cov @ weights))


def expected_portfolio_return(returns: pd.DataFrame, weights: np.ndarray) -> float:
    return float(np.dot(weights, expected_returns(returns)))


def expected_sharpe(returns: pd.DataFrame, weights: np.ndarray, risk_free_rate: float = 0.02) -> float:
    vol = expected_volatility(returns, weights)
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    return (expected_portfolio_return(returns, weights) - daily_rf * TRADING_DAYS) / vol if vol > 1e-12 else np.nan


def _optimize(returns: pd.DataFrame, objective, risk_free_rate: float = 0.02, max_weight: float = 1.0) -> dict[str, object]:
    n_assets = len(returns.columns)
    if n_assets == 0 or not np.isfinite(max_weight) or not 0 < max_weight <= 1 or n_assets * max_weight < 1 - 1e-10:
        raise ValueError("The maximum weight must be feasible: number of assets × cap must be at least 100%.")
    initial = np.repeat(1 / n_assets, n_assets)
    bounds = [(0, max_weight)] * n_assets
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    try:
        result = minimize(objective, initial, method="SLSQP", bounds=bounds, constraints=constraints)
        success = bool(result.success)
        message = str(result.message)
        weights = result.x if success else initial
    except Exception as exc:
        success = False
        message = str(exc)
        weights = initial
    weights = np.clip(weights, 0, 1)
    weights = weights / weights.sum() if weights.sum() else initial
    return {
        "weights": pd.Series(weights, index=returns.columns),
        "expected_return": expected_portfolio_return(returns, weights),
        "expected_volatility": expected_volatility(returns, weights),
        "expected_sharpe": expected_sharpe(returns, weights, risk_free_rate),
        "success": success,
        "message": message,
    }


def maximum_sharpe_portfolio(returns: pd.DataFrame, risk_free_rate: float = 0.02) -> dict[str, object]:
    return _optimize(returns, lambda w: -expected_sharpe(returns, w, risk_free_rate), risk_free_rate)


def minimum_volatility_portfolio(returns: pd.DataFrame, risk_free_rate: float = 0.02, max_weight: float = 1.0) -> dict[str, object]:
    return _optimize(returns, lambda w: expected_volatility(returns, w), risk_free_rate, max_weight=max_weight)


def monte_carlo_simulation(
    returns: pd.DataFrame,
    n_portfolios: int = 3000,
    risk_free_rate: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_portfolios):
        weights = rng.dirichlet(np.ones(len(returns.columns)))
        rows.append(
            {
                "expected_return": expected_portfolio_return(returns, weights),
                "expected_volatility": expected_volatility(returns, weights),
                "expected_sharpe": expected_sharpe(returns, weights, risk_free_rate),
                **{f"weight_{asset}": weight for asset, weight in zip(returns.columns, weights)},
            }
        )
    return pd.DataFrame(rows)


def black_litterman_placeholder(returns: pd.DataFrame, market_weights: pd.Series | None = None) -> pd.Series:
    """Simplified Black-Litterman style allocation placeholder.

    A production implementation would combine market-implied equilibrium
    returns with investor views. Here, the placeholder tilts equal weights
    toward assets with positive historical risk-adjusted returns.
    """
    base = normalize_weights(market_weights, returns.columns)
    signal = returns.mean() / returns.std().replace(0, np.nan)
    signal = signal.fillna(0).clip(lower=0)
    if signal.sum() == 0:
        return base
    tilted = 0.75 * base + 0.25 * (signal / signal.sum())
    return normalize_weights(tilted, returns.columns)
