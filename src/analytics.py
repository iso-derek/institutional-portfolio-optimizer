"""Portfolio analytics and risk metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from preprocessing import normalize_weights


TRADING_DAYS = 252


def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    weights = normalize_weights(weights, returns.columns)
    return returns.dot(weights)


def cumulative_returns(returns: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return (1 + returns).cumprod() - 1


def annualized_return(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    years = len(returns) / TRADING_DAYS
    return float((1 + returns).prod() ** (1 / years) - 1) if years else 0.0


def annualized_volatility(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Arithmetic daily excess return over sample volatility, annualised."""
    vol = annualized_volatility(returns)
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    return float((returns.mean() - daily_rf) * TRADING_DAYS / vol) if vol > 1e-12 else np.nan


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Downside deviation uses ALL observations and the daily risk-free target."""
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    excess = returns - daily_rf
    downside = float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2) * TRADING_DAYS))
    return float(excess.mean() * TRADING_DAYS / downside) if downside > 1e-12 else np.nan


def drawdown_series(returns: pd.Series) -> pd.Series:
    value = (1 + returns).cumprod()
    # Include starting wealth=1: a loss on the first day is a real drawdown.
    return value / value.cummax().clip(lower=1.0) - 1


def max_drawdown(returns: pd.Series) -> float:
    return float(drawdown_series(returns).min())


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    return float(-np.percentile(returns.dropna(), (1 - confidence) * 100))


def parametric_var(returns: pd.Series, confidence: float = 0.95) -> float:
    return float(-(returns.mean() + returns.std() * norm.ppf(1 - confidence)))


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    threshold = historical_var(returns, confidence)
    tail = returns[returns <= -threshold]
    return float(-tail.mean()) if len(tail) else 0.0


def beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned = pd.concat([asset_returns, benchmark_returns], axis=1).dropna()
    if aligned.empty or aligned.iloc[:, 1].var() == 0:
        return np.nan
    return float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / aligned.iloc[:, 1].var())


def jensen_alpha(
    portfolio: pd.Series,
    benchmark: pd.Series,
    risk_free_rate: float = 0.02,
) -> float:
    """Annualised arithmetic CAPM residual on aligned daily observations."""
    aligned = pd.concat([portfolio.rename("portfolio"), benchmark.rename("benchmark")], axis=1).dropna()
    if len(aligned) < 2:
        return np.nan
    beta_value = beta(aligned["portfolio"], aligned["benchmark"])
    if not np.isfinite(beta_value):
        return np.nan
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    residual = ((aligned["portfolio"] - daily_rf)
                - beta_value * (aligned["benchmark"] - daily_rf))
    return float(residual.mean() * TRADING_DAYS)


def rolling_benchmark_metrics(
    portfolio: pd.Series,
    benchmark: pd.Series,
    window: int = 63,
) -> pd.DataFrame:
    """Rolling annualised risk and market-sensitivity diagnostics."""
    if not isinstance(window, int) or window < 2:
        raise ValueError("Rolling window must be an integer of at least two observations.")
    aligned = pd.concat([portfolio.rename("portfolio"), benchmark.rename("benchmark")], axis=1).dropna()
    active = aligned["portfolio"] - aligned["benchmark"]
    benchmark_variance = aligned["benchmark"].rolling(window).var()
    output = pd.DataFrame(index=aligned.index)
    output["portfolio_volatility"] = aligned["portfolio"].rolling(window).std() * np.sqrt(TRADING_DAYS)
    output["benchmark_volatility"] = aligned["benchmark"].rolling(window).std() * np.sqrt(TRADING_DAYS)
    output["tracking_error"] = active.rolling(window).std() * np.sqrt(TRADING_DAYS)
    output["beta"] = (aligned["portfolio"].rolling(window).cov(aligned["benchmark"])
                      / benchmark_variance.replace(0, np.nan))
    output["maximum_drawdown"] = aligned["portfolio"].rolling(window).apply(
        lambda sample: max_drawdown(pd.Series(sample)), raw=False
    )
    return output.dropna(how="all")


def return_attribution(returns: pd.DataFrame, weights: pd.Series) -> dict[str, object]:
    """Reconcile asset wealth changes to compounded portfolio total return.

    The identity follows the dashboard assumption of fixed weights rebalanced
    each observation, with no costs or tax.
    """
    weights = normalize_weights(weights, returns.columns)
    portfolio = portfolio_returns(returns, weights)
    wealth_before = (1 + portfolio).cumprod().shift(1, fill_value=1.0)
    daily_arithmetic = returns.mul(weights, axis=1)
    wealth_contribution = daily_arithmetic.mul(wealth_before, axis=0).sum()
    total_return = float((1 + portfolio).prod() - 1)
    table = pd.DataFrame({
        "asset": returns.columns,
        "weight": weights.reindex(returns.columns).to_numpy(),
        "arithmetic_return_contribution": daily_arithmetic.sum().to_numpy(),
        "compounded_return_contribution": wealth_contribution.reindex(returns.columns).to_numpy(),
    })
    return {
        "by_asset": table,
        "portfolio_total_return": total_return,
        "reconciliation_residual": float(total_return - table["compounded_return_contribution"].sum()),
    }


def risk_contribution(returns: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    weights = normalize_weights(weights, returns.columns)
    cov = returns.cov() * TRADING_DAYS
    variance = float(weights.T @ cov @ weights)
    if variance <= 0:
        contribution = pd.Series(0.0, index=returns.columns)
    else:
        contribution = weights * (cov @ weights) / variance
    output = contribution.rename("risk_contribution").reset_index()
    output.columns = ["asset", "risk_contribution"]
    return output


def diversification_metrics(returns: pd.DataFrame, weights: pd.Series) -> dict[str, object]:
    """Describe holding concentration and covariance-based diversification.

    These are sample diagnostics, not investment recommendations. Effective
    holdings measures weight concentration; it is not a count of independent risks.
    """
    weights = normalize_weights(weights, returns.columns)
    held = weights[weights > 1e-10]
    individual_vol = returns.std() * np.sqrt(TRADING_DAYS)
    standalone_vol = float(weights.dot(individual_vol))
    portfolio_vol = annualized_volatility(portfolio_returns(returns, weights))
    risk = risk_contribution(returns, weights).set_index("asset")["risk_contribution"]
    if portfolio_vol <= 1e-12:
        risk[:] = np.nan
    comparison = pd.DataFrame({"weight": weights, "risk_contribution": risk})
    comparison["risk_minus_weight"] = comparison["risk_contribution"] - comparison["weight"]
    corr = returns[held.index].corr().to_numpy()
    pairwise = corr[np.triu_indices(len(held), k=1)]
    finite_pairs = pairwise[np.isfinite(pairwise)]
    return {
        "effective_holdings": float(1 / weights.pow(2).sum()),
        "largest_weight": float(weights.max()),
        "weighted_standalone_volatility": standalone_vol,
        "portfolio_volatility": portfolio_vol,
        "diversification_reduction": float(1 - portfolio_vol / standalone_vol) if standalone_vol > 1e-12 else np.nan,
        "average_pairwise_correlation": float(finite_pairs.mean()) if len(finite_pairs) else np.nan,
        "allocation_vs_risk": comparison.rename_axis("asset").reset_index(),
    }


def benchmark_comparison(
    portfolio: pd.Series,
    benchmark: pd.Series | None,
    risk_free_rate: float = 0.02,
    rolling_window: int = 63,
) -> dict[str, object]:
    """Compare the same dates; the benchmark is not added to the allocation."""
    if benchmark is None:
        return {}
    aligned = pd.concat([portfolio.rename("Portfolio"), benchmark.rename("Benchmark")], axis=1).dropna()
    if len(aligned) < 2:
        return {}
    active = aligned["Portfolio"] - aligned["Benchmark"]
    tracking_error = annualized_volatility(active)
    return {
        "growth": (1 + aligned).cumprod() * 100,
        "portfolio_total_return": float((1 + aligned["Portfolio"]).prod() - 1),
        "benchmark_total_return": float((1 + aligned["Benchmark"]).prod() - 1),
        "tracking_error": tracking_error,
        "information_ratio": float(active.mean() * TRADING_DAYS / tracking_error) if tracking_error > 1e-12 else np.nan,
        "beta": beta(aligned["Portfolio"], aligned["Benchmark"]),
        "alpha": jensen_alpha(aligned["Portfolio"], aligned["Benchmark"], risk_free_rate),
        "rolling": rolling_benchmark_metrics(aligned["Portfolio"], aligned["Benchmark"], rolling_window),
    }


def portfolio_metrics(
    returns: pd.DataFrame,
    weights: pd.Series,
    risk_free_rate: float = 0.02,
    benchmark: str = "SPY",
    benchmark_returns: pd.Series | None = None,
    confidence: float = 0.95,
) -> dict[str, object]:
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1.")
    weights = normalize_weights(weights, returns.columns)
    port = portfolio_returns(returns, weights)
    if benchmark_returns is None and benchmark in returns.columns:
        benchmark_returns = returns[benchmark]
    beta_value = beta(port, benchmark_returns) if benchmark_returns is not None else np.nan
    return {
        "portfolio_returns": port,
        "cumulative_returns": cumulative_returns(port),
        "asset_cumulative_returns": cumulative_returns(returns),
        "annualized_return": annualized_return(port),
        "annualized_volatility": annualized_volatility(port),
        "sharpe_ratio": sharpe_ratio(port, risk_free_rate),
        "sortino_ratio": sortino_ratio(port, risk_free_rate),
        "beta": beta_value,
        "max_drawdown": max_drawdown(port),
        "historical_var": historical_var(port, confidence),
        "parametric_var": parametric_var(port, confidence),
        "conditional_var": conditional_var(port, confidence),
        "drawdown": drawdown_series(port),
        "correlation": returns.corr(),
        "risk_contribution": risk_contribution(returns, weights),
        "weights": weights,
        "confidence": confidence,
        "tail_observations": int((port <= -historical_var(port, confidence)).sum()),
        "diversification": diversification_metrics(returns, weights),
        "return_attribution": return_attribution(returns, weights),
        "benchmark_comparison": benchmark_comparison(port, benchmark_returns, risk_free_rate),
    }
