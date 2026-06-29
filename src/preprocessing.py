"""Preprocessing helpers for portfolio analytics."""

from __future__ import annotations

import pandas as pd


def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill missing values and remove assets with insufficient history."""
    prices = prices.copy()
    prices = prices.apply(pd.to_numeric, errors="coerce")
    prices = prices.dropna(axis=1, thresh=max(30, int(len(prices) * 0.75)))
    prices = prices.ffill().dropna()
    return prices


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily simple returns from cleaned price data."""
    return clean_prices(prices).pct_change().dropna()


def normalize_weights(weights: dict[str, float] | pd.Series | None, assets: list[str] | pd.Index) -> pd.Series:
    assets = list(assets)
    if weights is None:
        return pd.Series(1 / len(assets), index=assets)
    weights = pd.Series(weights, dtype=float).reindex(assets).fillna(0)
    if weights.sum() <= 0:
        return pd.Series(1 / len(assets), index=assets)
    return weights / weights.sum()
