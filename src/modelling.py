"""Portfolio optimisation and simulation models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from analytics import TRADING_DAYS
from preprocessing import normalize_weights


SOLUTION_TOLERANCE = 1e-7


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


def _validate_inputs(returns: pd.DataFrame, max_weight: float) -> None:
    n_assets = len(returns.columns)
    if returns.empty or n_assets == 0 or returns.columns.has_duplicates:
        raise ValueError("Returns need observations and uniquely named assets.")
    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Returns must be finite.")
    if not np.isfinite(max_weight) or not 0 < max_weight <= 1 or n_assets * max_weight < 1 - SOLUTION_TOLERANCE:
        raise ValueError("The maximum weight must be feasible: number of assets × cap must be at least 100%.")


def _solution_residuals(weights: np.ndarray, max_weight: float, target_return: float | None = None,
                        annual_returns: np.ndarray | None = None) -> dict[str, float]:
    residuals = {
        "sum_to_one": abs(float(weights.sum()) - 1.0),
        "lower_bound": max(0.0, -float(weights.min())),
        "upper_bound": max(0.0, float(weights.max()) - max_weight),
    }
    if target_return is not None and annual_returns is not None:
        residuals["target_return"] = abs(float(weights @ annual_returns) - target_return)
    return residuals


def _accepted_solution(result, max_weight: float, target_return: float | None = None,
                       annual_returns: np.ndarray | None = None) -> tuple[bool, str, np.ndarray, dict[str, float]]:
    weights = np.asarray(getattr(result, "x", []), dtype=float)
    residuals = ({"sum_to_one": np.inf, "lower_bound": np.inf, "upper_bound": np.inf}
                 if weights.ndim != 1 or weights.size == 0 or not np.isfinite(weights).all()
                 else _solution_residuals(weights, max_weight, target_return, annual_returns))
    objective_value = float(getattr(result, "fun", np.nan))
    valid = (bool(getattr(result, "success", False)) and np.isfinite(objective_value)
             and all(value <= SOLUTION_TOLERANCE for value in residuals.values()))
    message = str(getattr(result, "message", "Optimiser returned no diagnostic message."))
    if not valid:
        message += "; solution rejected because convergence, finiteness or constraint residual checks failed"
    return valid, message, weights, residuals


def _optimize(returns: pd.DataFrame, objective, risk_free_rate: float = 0.02, max_weight: float = 1.0) -> dict[str, object]:
    _validate_inputs(returns, max_weight)
    n_assets = len(returns.columns)
    initial = np.repeat(1 / n_assets, n_assets)
    bounds = [(0, max_weight)] * n_assets
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    try:
        result = minimize(objective, initial, method="SLSQP", bounds=bounds, constraints=constraints)
        success, message, candidate, residuals = _accepted_solution(result, max_weight)
        weights = candidate if success else initial
    except Exception as exc:
        success = False
        message = str(exc)
        weights = initial
        residuals = _solution_residuals(weights, max_weight)
    return {
        "weights": pd.Series(weights, index=returns.columns),
        "expected_return": expected_portfolio_return(returns, weights),
        "expected_volatility": expected_volatility(returns, weights),
        "expected_sharpe": expected_sharpe(returns, weights, risk_free_rate),
        "success": success,
        "message": message,
        "constraint_residuals": residuals,
    }


def maximum_sharpe_portfolio(returns: pd.DataFrame, risk_free_rate: float = 0.02) -> dict[str, object]:
    return _optimize(returns, lambda w: -expected_sharpe(returns, w, risk_free_rate), risk_free_rate)


def minimum_volatility_portfolio(returns: pd.DataFrame, risk_free_rate: float = 0.02, max_weight: float = 1.0) -> dict[str, object]:
    return _optimize(returns, lambda w: expected_volatility(returns, w), risk_free_rate, max_weight=max_weight)


def _extreme_return_weights(annual_returns: np.ndarray, max_weight: float, maximize: bool) -> np.ndarray:
    """Construct the exact long-only capped allocation at a return extreme."""
    order = np.argsort(annual_returns)
    if maximize:
        order = order[::-1]
    weights = np.zeros(len(annual_returns))
    remaining = 1.0
    for index in order:
        allocation = min(max_weight, remaining)
        weights[index] = allocation
        remaining -= allocation
        if remaining <= SOLUTION_TOLERANCE:
            break
    if remaining > SOLUTION_TOLERANCE:
        raise ValueError("The maximum weight does not permit a fully invested portfolio.")
    return weights


def efficient_frontier(
    returns: pd.DataFrame,
    n_points: int = 25,
    risk_free_rate: float = 0.02,
    max_weight: float = 1.0,
) -> pd.DataFrame:
    """Solve the long-only, capped minimum-variance frontier.

    Every point minimises annualised variance subject to full investment and a
    target sample mean return. Only solutions that pass explicit finiteness,
    weight-bound, sum and target-return residual checks are returned.
    """
    _validate_inputs(returns, max_weight)
    if not isinstance(n_points, int) or n_points < 2 or n_points > 200:
        raise ValueError("Frontier points must be an integer between 2 and 200.")
    annual_returns = expected_returns(returns).to_numpy(dtype=float)
    minimum = minimum_volatility_portfolio(returns, risk_free_rate, max_weight)
    if not minimum["success"]:
        raise RuntimeError("Cannot solve the efficient frontier because the global minimum-variance portfolio failed validation: " + str(minimum["message"]))
    low_weights = minimum["weights"].to_numpy(dtype=float)
    high_weights = _extreme_return_weights(annual_returns, max_weight, maximize=True)
    low_return = float(low_weights @ annual_returns)
    high_return = float(high_weights @ annual_returns)
    if high_return + SOLUTION_TOLERANCE < low_return:
        raise RuntimeError("Validated frontier endpoints have inconsistent expected returns.")
    if high_return - low_return <= SOLUTION_TOLERANCE:
        residuals = _solution_residuals(low_weights, max_weight, low_return, annual_returns)
        return pd.DataFrame([{
            "target_return": low_return,
            "expected_return": low_return,
            "expected_volatility": float(minimum["expected_volatility"]),
            "expected_sharpe": float(minimum["expected_sharpe"]),
            "success": True,
            "message": "All assets have the same sample mean return; the frontier reduces to the validated global minimum-variance portfolio.",
            "max_constraint_residual": max(residuals.values()),
            **{f"weight_{asset}": float(weight) for asset, weight in zip(returns.columns, low_weights)},
        }])
    targets = np.linspace(low_return, high_return, n_points)
    covariance = returns.cov().to_numpy(dtype=float) * TRADING_DAYS
    bounds = [(0, max_weight)] * len(annual_returns)
    rows = []
    for target in targets:
        fraction = 0.0 if high_return == low_return else (target - low_return) / (high_return - low_return)
        initial = (1 - fraction) * low_weights + fraction * high_weights
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, target=target: float(w @ annual_returns - target)},
        ]
        try:
            result = minimize(lambda w: float(w.T @ covariance @ w), initial, method="SLSQP",
                              bounds=bounds, constraints=constraints,
                              options={"ftol": 1e-12, "maxiter": 1000})
            success, message, weights, residuals = _accepted_solution(
                result, max_weight, target, annual_returns
            )
        except Exception as exc:
            success, message, weights = False, str(exc), initial
            residuals = _solution_residuals(weights, max_weight, target, annual_returns)
        if not success:
            continue
        volatility = float(np.sqrt(max(0.0, weights.T @ covariance @ weights)))
        expected_return = float(weights @ annual_returns)
        daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
        sharpe = ((expected_return - daily_rf * TRADING_DAYS) / volatility
                  if volatility > 1e-12 else np.nan)
        rows.append({
            "target_return": float(target),
            "expected_return": expected_return,
            "expected_volatility": volatility,
            "expected_sharpe": float(sharpe),
            "success": True,
            "message": message,
            "max_constraint_residual": max(residuals.values()),
            **{f"weight_{asset}": float(weight) for asset, weight in zip(returns.columns, weights)},
        })
    frontier = pd.DataFrame(rows)
    if frontier.empty:
        raise RuntimeError("No efficient-frontier point passed the numerical validation checks.")
    return frontier.sort_values(["expected_volatility", "expected_return"]).reset_index(drop=True)


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
