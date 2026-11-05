"""Plotly chart builders for the portfolio optimizer."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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


def efficient_frontier_chart(frontier: pd.DataFrame, opportunities: pd.DataFrame | None = None):
    figure = go.Figure()
    if opportunities is not None and not opportunities.empty:
        figure.add_trace(go.Scatter(
            x=opportunities["expected_volatility"], y=opportunities["expected_return"],
            mode="markers", name="Random feasible allocations",
            marker={"size": 5, "color": "rgba(120, 130, 150, 0.25)"},
            hovertemplate="Volatility %{x:.2%}<br>Return %{y:.2%}<extra></extra>",
        ))
    ordered = frontier.sort_values("expected_return")
    figure.add_trace(go.Scatter(
        x=ordered["expected_volatility"], y=ordered["expected_return"],
        mode="lines+markers", name="Solved minimum-variance frontier",
        marker={"size": 7, "color": ordered["expected_sharpe"], "colorscale": "Viridis",
                "showscale": True, "colorbar": {"title": "Sharpe"}},
        line={"width": 3, "color": "#1f77b4"},
        customdata=ordered[["max_constraint_residual"]],
        hovertemplate="Volatility %{x:.2%}<br>Return %{y:.2%}<br>Max residual %{customdata[0]:.2e}<extra></extra>",
    ))
    figure.update_layout(title="Constrained Efficient Frontier", xaxis_title="Sample Annualised Volatility",
                         yaxis_title="Historical Mean Annual Return", legend_title="Allocation set")
    figure.update_xaxes(tickformat=".1%")
    figure.update_yaxes(tickformat=".1%")
    return figure
