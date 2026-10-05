"""Preprocessing helpers for portfolio analytics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill missing values and remove assets with insufficient history."""
    prices = prices.copy()
    prices = prices.sort_index()
    if prices.index.has_duplicates or prices.columns.has_duplicates:
        raise ValueError("Prices need unique dates and asset names.")
    prices = prices.apply(pd.to_numeric, errors="coerce")
    prices = prices.replace([np.inf, -np.inf], np.nan)
    prices = prices.where(prices > 0)
    prices = prices.dropna(axis=1, thresh=max(30, int(len(prices) * 0.75)))
    prices = prices.ffill(limit=3).dropna()
    if prices.empty or len(prices) < 30:
        raise ValueError("At least 30 aligned price observations are required. Try a longer date range.")
    return prices


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily simple returns from cleaned price data."""
    return clean_prices(prices).pct_change(fill_method=None).dropna()


def normalize_weights(weights: dict[str, float] | pd.Series | None, assets: list[str] | pd.Index) -> pd.Series:
    assets = list(assets)
    if not assets or len(set(assets)) != len(assets):
        raise ValueError("Select at least one asset, with no duplicate symbols.")
    if weights is None:
        return pd.Series(1 / len(assets), index=assets)
    weights = pd.Series(weights, dtype=float)
    if weights.index.has_duplicates or not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError("Weights must be finite, non-negative and uniquely named.")
    if not weights.index.isin(assets).all():
        raise ValueError("Weights contain assets outside the selected portfolio.")
    weights = weights.reindex(assets).fillna(0)
    if weights.sum() <= 0:
        raise ValueError("At least one allocation must be greater than zero.")
    return weights / weights.sum()
