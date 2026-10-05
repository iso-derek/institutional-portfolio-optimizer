"""Plotly chart builders for the portfolio optimizer."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def line_chart(series: pd.Series, title: str, y_label: str):
    frame = series.reset_index()
    frame.columns = ["Date", y_label]
    return px.line(frame, x="Date", y=y_label, title=title)


def allocation_chart(weights: pd.Series):
    frame = weights.reset_index()
    frame.columns = ["Asset", "Weight"]
    return px.pie(frame, names="Asset", values="Weight", title="Portfolio Allocation")


def correlation_heatmap(correlation: pd.DataFrame):
    return px.imshow(correlation, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="Correlation Heatmap")


def efficient_frontier_chart(frontier: pd.DataFrame):
    return px.scatter(
        frontier,
        x="expected_volatility",
        y="expected_return",
        color="expected_sharpe",
        title="Simulated Long-Only Allocations",
        labels={"expected_volatility": "Sample Annualised Volatility", "expected_return": "Historical Mean Annual Return", "expected_sharpe": "Sample Sharpe"},
    )
