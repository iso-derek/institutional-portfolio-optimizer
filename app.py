"""Streamlit dashboard for institutional portfolio optimisation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

import streamlit as st
import plotly.express as px


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from analytics import portfolio_metrics  # noqa: E402
from data_generation import DEFAULT_TICKERS, fetch_price_data  # noqa: E402
from modelling import black_litterman_placeholder, maximum_sharpe_portfolio, minimum_volatility_portfolio, monte_carlo_simulation  # noqa: E402
from preprocessing import calculate_returns, clean_prices, normalize_weights  # noqa: E402
from visualisation import allocation_chart, correlation_heatmap, efficient_frontier_chart, line_chart  # noqa: E402


st.set_page_config(page_title="Institutional Portfolio Optimizer", layout="wide")


@st.cache_data(show_spinner=False)
def load_data(tickers: tuple[str, ...], start: date, end: date):
    return fetch_price_data(list(tickers), start=start, end=end)


def fmt_pct(value: float) -> str:
    return f"{value:.2%}" if value == value else "N/A"


st.title("Institutional Portfolio Optimizer")
st.caption("Educational analytics tool only. This dashboard does not provide investment advice.")

with st.sidebar:
    st.header("Portfolio Inputs")
    tickers_text = st.text_input("Tickers", ", ".join(DEFAULT_TICKERS))
    start_date = st.date_input("Start date", date.today() - timedelta(days=365 * 5))
    end_date = st.date_input("End date", date.today())
    risk_free_rate = st.number_input("Risk-free rate", min_value=0.0, max_value=0.20, value=0.02, step=0.005)
    method = st.selectbox("Allocation method", ["Equal weight", "Maximum Sharpe", "Minimum Volatility", "Black-Litterman style tilt"])

tickers = tuple(t.strip().upper() for t in tickers_text.replace(",", " ").split() if t.strip())
if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

prices = clean_prices(load_data(tickers, start_date, end_date))
returns = calculate_returns(prices)

if method == "Maximum Sharpe":
    weights = maximum_sharpe_portfolio(returns, risk_free_rate)["weights"]
elif method == "Minimum Volatility":
    weights = minimum_volatility_portfolio(returns, risk_free_rate)["weights"]
elif method == "Black-Litterman style tilt":
    weights = black_litterman_placeholder(returns)
else:
    weights = normalize_weights(None, returns.columns)

metrics = portfolio_metrics(returns, weights, risk_free_rate)
frontier = monte_carlo_simulation(returns, n_portfolios=2000, risk_free_rate=risk_free_rate)

st.subheader("Executive Summary")
cols = st.columns(7)
kpis = [
    ("Annual Return", fmt_pct(metrics["annualized_return"])),
    ("Volatility", fmt_pct(metrics["annualized_volatility"])),
    ("Sharpe", f"{metrics['sharpe_ratio']:.2f}"),
    ("Sortino", f"{metrics['sortino_ratio']:.2f}"),
    ("Beta", f"{metrics['beta']:.2f}" if metrics["beta"] == metrics["beta"] else "N/A"),
    ("Max Drawdown", fmt_pct(metrics["max_drawdown"])),
    ("CVaR", fmt_pct(metrics["conditional_var"])),
]
for col, (label, value) in zip(cols, kpis):
    col.metric(label, value)

tab1, tab2, tab3, tab4 = st.tabs(["Performance", "Risk", "Optimisation", "Data"])

with tab1:
    left, right = st.columns(2)
    left.plotly_chart(line_chart(metrics["cumulative_returns"], "Portfolio Cumulative Return", "Cumulative Return"), width="stretch")
    right.plotly_chart(allocation_chart(weights), width="stretch")
    asset_frame = metrics["asset_cumulative_returns"].reset_index().melt("Date", var_name="Asset", value_name="Cumulative Return")
    st.plotly_chart(px.line(asset_frame, x="Date", y="Cumulative Return", color="Asset", title="Asset Cumulative Returns"), width="stretch")

with tab2:
    left, right = st.columns(2)
    left.plotly_chart(line_chart(metrics["drawdown"], "Portfolio Drawdown", "Drawdown"), width="stretch")
    right.plotly_chart(correlation_heatmap(metrics["correlation"]), width="stretch")
    st.dataframe(metrics["risk_contribution"].style.format({"risk_contribution": "{:.2%}"}), width="stretch", hide_index=True)

with tab3:
    st.plotly_chart(efficient_frontier_chart(frontier), width="stretch")
    opt_cols = st.columns(2)
    opt_cols[0].dataframe(maximum_sharpe_portfolio(returns, risk_free_rate)["weights"].reset_index().rename(columns={"index": "asset", 0: "weight"}), width="stretch", hide_index=True)
    opt_cols[1].dataframe(minimum_volatility_portfolio(returns, risk_free_rate)["weights"].reset_index().rename(columns={"index": "asset", 0: "weight"}), width="stretch", hide_index=True)

with tab4:
    st.dataframe(prices.tail(20), width="stretch")
    st.write("Downloaded/fallback prices are saved under `data/raw/asset_prices.csv`.")
