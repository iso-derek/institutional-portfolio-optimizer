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
    vol = annualized_volatility(returns)
    return float((annualized_return(returns) - risk_free_rate) / vol) if vol else 0.0


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    downside = returns[returns < 0].std() * np.sqrt(TRADING_DAYS)
    return float((annualized_return(returns) - risk_free_rate) / downside) if downside else 0.0


def drawdown_series(returns: pd.Series) -> pd.Series:
    value = (1 + returns).cumprod()
    return value / value.cummax() - 1


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
        return 0.0
    return float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / aligned.iloc[:, 1].var())


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


def portfolio_metrics(
    returns: pd.DataFrame,
    weights: pd.Series,
    risk_free_rate: float = 0.02,
    benchmark: str = "SPY",
) -> dict[str, object]:
    weights = normalize_weights(weights, returns.columns)
    port = portfolio_returns(returns, weights)
    benchmark_returns = returns[benchmark] if benchmark in returns.columns else None
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
        "historical_var": historical_var(port),
        "parametric_var": parametric_var(port),
        "conditional_var": conditional_var(port),
        "drawdown": drawdown_series(port),
        "correlation": returns.corr(),
        "risk_contribution": risk_contribution(returns, weights),
        "weights": weights,
    }
