"""Streamlit dashboard for institutional portfolio optimisation."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import hashlib
import io
import json
import zipfile

import numpy as np
import pandas as pd
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
from research import walk_forward_study  # noqa: E402
from visualisation import allocation_chart, correlation_heatmap, efficient_frontier_chart, line_chart  # noqa: E402

st.set_page_config(page_title="Institutional Portfolio Optimizer", layout="wide")


@st.cache_data(show_spinner=False, ttl=3600)
def load_data(tickers: tuple[str, ...], start: date, end: date):
    # Dashboard views must not overwrite the checked-in dataset.
    return fetch_price_data(list(tickers), start=start, end=end, save_path=None)


@st.cache_data(show_spinner=False)
def compare_allocations(returns: pd.DataFrame, risk_free_rate: float):
    return {"Maximum Sharpe": maximum_sharpe_portfolio(returns, risk_free_rate),
            "Minimum Volatility": minimum_volatility_portfolio(returns, risk_free_rate)}


@st.cache_data(show_spinner=False)
def simulate_allocations(returns: pd.DataFrame, risk_free_rate: float):
    return monte_carlo_simulation(returns, n_portfolios=2000, risk_free_rate=risk_free_rate)


@st.cache_data(show_spinner=False)
def run_research(returns: pd.DataFrame, lookback: int, rebalance_every: int, cap: float, cost: float, risk_free_rate: float, confidence: float):
    return walk_forward_study(returns, lookback, rebalance_every, cap, cost, risk_free_rate, confidence)


def fmt_pct(value: float) -> str:
    return f"{value:.2%}" if np.isfinite(value) else "N/A"


def fmt_num(value: float) -> str:
    return f"{value:.2f}" if np.isfinite(value) else "N/A"


st.title("Institutional Portfolio Optimizer")
st.caption("Portfolio construction, diversification and historical risk. Educational analysis, not investment advice.")

with st.sidebar:
    st.header("Portfolio Inputs")
    tickers_text = st.text_input("Portfolio tickers", ", ".join(DEFAULT_TICKERS))
    benchmark = st.text_input("Benchmark ticker", "SPY", help="Compared separately. Only invested in if also entered under portfolio tickers. Leave blank for no benchmark.").strip().upper()
    start_date = st.date_input("Start date", date.today() - timedelta(days=365 * 5))
    end_date = st.date_input("End date", date.today())
    initial_value = st.number_input("Portfolio value (USD)", min_value=1.0, max_value=1e12, value=100000.0, step=1000.0)
    risk_free_rate = st.number_input("Assumed annual risk-free rate (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.25) / 100
    confidence = st.selectbox("One-day tail confidence", [0.95, 0.975, 0.99], format_func=lambda x: f"{x:.1%}")
    method = st.selectbox("Allocation method", ["Equal weight", "Maximum Sharpe", "Minimum Volatility", "Historical-return tilt (heuristic)"])
    st.caption("Use USD-quoted assets on a common trading calendar. No currency conversion is applied.")

tickers = tuple(dict.fromkeys(t.strip().upper() for t in tickers_text.replace(",", " ").split() if t.strip()))
if not tickers or len(tickers) > 20:
    st.error("Enter between 1 and 20 portfolio tickers.")
    st.stop()
if any(len(t) > 20 for t in tickers) or len(benchmark) > 20 or len(benchmark.split()) > 1 or "," in benchmark:
    st.error("Use individual ticker symbols and a single benchmark ticker.")
    st.stop()
if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

requested = tuple(dict.fromkeys(tickers + ((benchmark,) if benchmark else ())))
try:
    raw_prices = load_data(requested, start_date, end_date)
    provenance = raw_prices.attrs.copy()
    prices = clean_prices(raw_prices)
    all_returns = calculate_returns(prices)
    available = [ticker for ticker in tickers if ticker in all_returns]
    if not available:
        raise ValueError("None of the portfolio assets have enough aligned observations.")
    returns = all_returns[available]
    benchmark_returns = all_returns[benchmark] if benchmark and benchmark in all_returns else None
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if provenance.get("synthetic") is True:
    st.warning("SYNTHETIC DEMONSTRATION: the market-data download failed. All prices and results below are simulated, not historical market performance.")
    with st.expander("Why is synthetic data being used?"):
        st.write(provenance.get("fallback_reason", "The provider did not supply usable adjusted prices."))
else:
    st.info("Source: Yahoo Finance via yfinance · adjusted close prices. Confirm provider data before relying on the analysis.")
missing = sorted(set(tickers) - set(available))
if missing:
    st.warning("Excluded due to missing or insufficient price history: " + ", ".join(missing))
if benchmark and benchmark_returns is None:
    st.warning(f"Benchmark {benchmark} is unavailable for this sample; benchmark metrics are omitted.")
st.caption(f"{len(returns):,} aligned daily returns · {prices.index[0]:%d %b %Y}–{prices.index[-1]:%d %b %Y} · 252 observations/year · fixed weights rebalanced daily · no costs or tax. Missing quotes are forward-filled for at most 3 observations before common-date alignment.")

optimised = compare_allocations(returns, risk_free_rate)
if method in optimised:
    result = optimised[method]
    weights = result["weights"]
    if not result["success"]:
        st.warning("The optimiser did not converge; equal weights are shown. " + result["message"])
elif method == "Historical-return tilt (heuristic)":
    weights = black_litterman_placeholder(returns)
    st.info("This is a historical-return tilt heuristic, not a Black–Litterman model.")
else:
    weights = normalize_weights(None, returns.columns)

metrics = portfolio_metrics(returns, weights, risk_free_rate, benchmark=benchmark, benchmark_returns=benchmark_returns, confidence=confidence)
frontier = simulate_allocations(returns, risk_free_rate)
st.subheader("Executive Summary")
kpis = [
    ("Historical CAGR", fmt_pct(metrics["annualized_return"])),
    ("Annualised volatility", fmt_pct(metrics["annualized_volatility"])),
    ("Sharpe ratio", fmt_num(metrics["sharpe_ratio"])),
    ("Sortino ratio", fmt_num(metrics["sortino_ratio"])),
    ("Beta vs benchmark", fmt_num(metrics["beta"])),
    ("Maximum drawdown", fmt_pct(metrics["max_drawdown"])),
    (f"1-day CVaR ({confidence:.1%})", fmt_pct(metrics["conditional_var"])),
]
for col, (label, value) in zip(st.columns(7), kpis):
    col.metric(label, value)
st.caption("Higher risk does not guarantee higher realised return. These are sample estimates, not forecasts.")

tab1, tab2, tab3, tab4, research_tab, tab5, tab6 = st.tabs(["Performance", "Risk", "Diversification", "Optimisation", "Research lab", "Learning guide", "Data"])
with tab1:
    left, right = st.columns(2)
    comparison = metrics["benchmark_comparison"]
    if comparison:
        growth = comparison["growth"].rename(columns={"Benchmark": benchmark})
        frame = growth.rename_axis("Date").reset_index().melt("Date", var_name="Series", value_name="Value")
        left.plotly_chart(px.line(frame, x="Date", y="Value", color="Series", title="Growth of $100 — same dates"), width="stretch")
        bench_cols = st.columns(3)
        bench_cols[0].metric("Portfolio total return", fmt_pct(comparison["portfolio_total_return"]))
        bench_cols[1].metric(f"{benchmark} total return", fmt_pct(comparison["benchmark_total_return"]))
        bench_cols[2].metric("Annualised tracking error", fmt_pct(comparison["tracking_error"]))
        st.caption("The benchmark is not automatically a holding. Tracking error measures volatility of daily portfolio-minus-benchmark returns.")
    else:
        left.plotly_chart(line_chart(metrics["cumulative_returns"], "Portfolio Cumulative Return", "Cumulative Return"), width="stretch")
    right.plotly_chart(allocation_chart(weights), width="stretch")
    frame = metrics["asset_cumulative_returns"].rename_axis("Date").reset_index().melt("Date", var_name="Asset", value_name="Cumulative Return")
    st.plotly_chart(px.line(frame, x="Date", y="Cumulative Return", color="Asset", title="Asset Cumulative Returns"), width="stretch")

with tab2:
    loss_rows = pd.DataFrame([{"Measure": label, "Loss fraction": metrics[key], "USD equivalent": metrics[key] * initial_value}
        for label, key in [("Historical VaR", "historical_var"), ("Normal-model VaR", "parametric_var"), ("Historical CVaR / Expected Shortfall", "conditional_var")]])
    st.write(f"**One-day loss estimates at {confidence:.1%} confidence**")
    st.dataframe(loss_rows.style.format({"Loss fraction": "{:.2%}", "USD equivalent": "$"+"{:,.2f}"}), width="stretch", hide_index=True)
    st.caption(f"Positive values represent losses; negative values represent gains. VaR is a threshold, not a maximum loss. CVaR averages the {metrics['tail_observations']} sample returns at or below the historical quantile. Normal-model VaR assumes normally distributed returns.")
    if metrics["tail_observations"] < 20:
        st.warning("Fewer than 20 observations support this tail estimate. Treat it as statistically fragile, especially at high confidence.")
    left, right = st.columns(2)
    left.plotly_chart(line_chart(metrics["drawdown"], "Portfolio Drawdown", "Drawdown"), width="stretch")
    right.plotly_chart(correlation_heatmap(metrics["correlation"]), width="stretch")
    st.caption("Drawdown includes losses from the initial investment. Historical relationships can change during market stress.")

with tab3:
    st.subheader("Capital allocation is not risk allocation")
    diagnostic = metrics["diversification"]
    div_cols = st.columns(3)
    div_cols[0].metric("Largest holding", fmt_pct(diagnostic["largest_weight"]))
    div_cols[1].metric("Effective holdings", fmt_num(diagnostic["effective_holdings"]))
    div_cols[2].metric("Diversification reduction", fmt_pct(diagnostic["diversification_reduction"]))
    allocation_risk = diagnostic["allocation_vs_risk"]
    bars = allocation_risk[["asset", "weight", "risk_contribution"]].rename(columns={"weight": "Capital share", "risk_contribution": "Risk share"}).melt("asset", var_name="Measure", value_name="Share")
    fig = px.bar(bars, x="asset", y="Share", color="Measure", barmode="group", title="Share of capital versus share of portfolio variance")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(allocation_risk.style.format({"weight": "{:.2%}", "risk_contribution": "{:.2%}", "risk_minus_weight": "{:+.2%}"}), width="stretch", hide_index=True)
    finite_risk = allocation_risk.dropna(subset=["risk_contribution"])
    if not finite_risk.empty:
        top = finite_risk.loc[finite_risk["risk_contribution"].idxmax()]
        st.info(f"{top['asset']} holds {top['weight']:.1%} of capital and contributes {top['risk_contribution']:.1%} of sample portfolio variance. The difference reflects volatility and co-movement.")
    st.write(f"Average pairwise correlation among held assets: **{fmt_num(diagnostic['average_pairwise_correlation'])}**.")
    st.caption("Effective holdings = 1 / sum(weight²); this is not a count of independent risks. Diversification reduction compares portfolio volatility with the weighted average of individual volatilities, a hypothetical perfectly correlated reference. Risk contributions may be negative and are N/A at zero portfolio variance.")
    st.warning("More stocks alone do not ensure diversification. Sector, country, currency and shared business drivers can leave a portfolio concentrated. This version does not yet classify those economic exposures.")

with tab4:
    st.plotly_chart(efficient_frontier_chart(frontier), width="stretch")
    st.caption("Each point is a randomly sampled long-only allocation, not a solved efficient frontier.")
    rows = []
    candidates = {"Equal weight": normalize_weights(None, returns.columns), **{name: result["weights"] for name, result in optimised.items()}}
    for name, candidate in candidates.items():
        m = portfolio_metrics(returns, candidate, risk_free_rate, confidence=confidence)
        rows.append({"Allocation": name, "Historical CAGR": m["annualized_return"], "Annualised volatility": m["annualized_volatility"], "Sharpe": m["sharpe_ratio"], "Max drawdown": m["max_drawdown"]})
    st.dataframe(pd.DataFrame(rows).style.format({"Historical CAGR": "{:.2%}", "Annualised volatility": "{:.2%}", "Sharpe": "{:.2f}", "Max drawdown": "{:.2%}"}), width="stretch", hide_index=True)
    for col, (name, result) in zip(st.columns(2), optimised.items()):
        col.write(f"**{name}**")
        if not result["success"]:
            col.warning("Optimisation failed; equal-weight fallback. " + result["message"])
        col.dataframe(result["weights"].rename("weight").rename_axis("asset").reset_index().style.format({"weight": "{:.2%}"}), width="stretch", hide_index=True)
    st.warning("Optimised weights use the full displayed sample and are evaluated on that same sample. This is in-sample research, not an out-of-sample trading backtest.")

with research_tab:
    st.subheader("Does a concentration cap improve out-of-sample risk after costs?")
    st.write("Compare equal weight, minimum volatility and capped minimum volatility. Each rebalance learns from earlier observations and is scored on later returns. Holdings drift between rebalances.")
    if provenance.get("synthetic"):
        st.warning("This is a synthetic demonstration of the experiment, not empirical evidence about financial markets.")
    with st.form("research_settings"):
        controls = st.columns(4)
        lookback = controls[0].selectbox("Training observations", [63, 126, 252], index=1)
        rebalance_every = controls[1].selectbox("Rebalance every N observations", [1, 5, 21, 63], index=2)
        minimum_cap = 100.0 / len(returns.columns)
        cap = controls[2].number_input("Maximum target weight (%)", min_value=minimum_cap, max_value=100.0, value=max(35.0, minimum_cap), step=1.0) / 100
        cost = controls[3].number_input("Cost per traded notional (bps)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        submitted = st.form_submit_button("Run walk-forward study")
    st.caption("Choose the specification before examining test results. Changing parameters after seeing results is exploratory tuning and consumes the holdout. The cap applies at rebalancing, not continuously as prices drift.")
    signature = (hashlib.sha256(returns.to_csv().encode()).hexdigest(), lookback, rebalance_every, cap, cost, risk_free_rate, confidence, provenance.get("source"))
    if submitted:
        try:
            with st.spinner("Evaluating chronological holdout periods…"):
                study = run_research(returns, lookback, rebalance_every, cap, cost, risk_free_rate, confidence)
            st.session_state["research_run"] = {"signature": signature, "result": study}
        except ValueError as exc:
            st.error(str(exc))
    saved_study = st.session_state.get("research_run")
    if saved_study and saved_study["signature"] == signature:
        study = saved_study["result"]
        summary = study["summary"]
        dates = study["net_returns"].index
        st.caption(f"Out-of-sample period: {dates[0]:%d %b %Y}–{dates[-1]:%d %b %Y} · {len(dates)} observations · {len(study['trades']) // 3} allocation decisions per strategy.")
        if len(dates) < 252:
            st.warning("Less than one trading year of holdout observations. Treat results and uncertainty intervals as exploratory.")
        chart = study["growth"].rename_axis("Date").reset_index().melt("Date", var_name="Strategy", value_name="Value")
        st.plotly_chart(px.line(chart, x="Date", y="Value", color="Strategy", title="Out-of-sample growth of $100 after assumed costs"), width="stretch")
        display = summary[["gross_cagr", "net_cagr", "net_volatility", "net_sharpe", "max_drawdown", "one_day_cvar", "annual_traded_fraction", "mean_largest_target_weight"]].rename(columns={"gross_cagr": "Gross CAGR", "net_cagr": "Net CAGR", "net_volatility": "Net volatility", "net_sharpe": "Net Sharpe", "max_drawdown": "Max drawdown", "one_day_cvar": "1-day CVaR", "annual_traded_fraction": "Annual traded notional / wealth", "mean_largest_target_weight": "Mean largest target weight"})
        formats = {column: "{:.2%}" for column in display if column != "Net Sharpe"}
        formats["Net Sharpe"] = "{:.2f}"
        st.dataframe(display.style.format(formats, na_rep="N/A"), width="stretch")
        st.caption("Trading volume counts buys plus sells, including initial deployment from cash. Cost is a proportional approximation: cost rate × absolute weight changes, applied before the next return. There are no taxes, market impact, borrow costs or execution delays.")
        st.write("**Return trade-off and uncertainty versus equal weight**")
        intervals = summary[["annual_mean_excess_vs_equal", "mean_excess_ci_low", "mean_excess_ci_high"]].rename(columns={"annual_mean_excess_vs_equal": "Annual mean return difference", "mean_excess_ci_low": "Exploratory 95% interval lower", "mean_excess_ci_high": "Exploratory 95% interval upper"})
        st.dataframe(intervals.style.format("{:+.2%}", na_rep="N/A"), width="stretch")
        st.caption(f"Paired circular-block bootstrap: 500 draws, {rebalance_every}-observation blocks, seed 42. N/A when fewer than two blocks are available. Differences are annualised arithmetic mean returns, not CAGR differences. Intervals do not establish causality, account for repeated tuning or quantify uncertainty in CVaR/drawdown.")
        st.caption("The user-chosen universe and full-period data-availability filtering can introduce selection and survivorship bias. Research conclusions require a fixed study universe and verified historical data.")
        if study["failures"]:
            st.warning(f"{len(study['failures'])} optimisation fits failed and used equal weights. Inspect these before interpreting the experiment.")
            st.dataframe(pd.DataFrame(study["failures"]), hide_index=True)
        with st.expander("Audit the training dates and target allocations"):
            st.dataframe(study["target_weights"], hide_index=True, width="stretch")
        metadata = {**study["settings"], "source": provenance, "portfolio_assets": list(returns.columns),
                    "dataset_sha256": signature[0], "test_start": str(dates[0]), "test_end": str(dates[-1]),
                    "assumptions": "Daily returns; 252 observations/year; target weights use strictly prior data; costs on buys plus sells incl. initial deployment; weights drift; chosen asset universe may create survivorship/selection bias."}
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for filename, frame in [("summary.csv", summary), ("input_returns.csv", returns), ("net_returns.csv", study["net_returns"]), ("gross_returns.csv", study["gross_returns"]), ("trades.csv", study["trades"]), ("target_weights.csv", study["target_weights"])]:
                bundle.writestr(filename, frame.to_csv())
            bundle.writestr("settings.json", json.dumps(metadata, indent=2, default=str))
            bundle.writestr("optimiser_failures.json", json.dumps(study["failures"], indent=2, default=str))
        st.download_button("Download reproducible research bundle", archive.getvalue(), "portfolio-research-study.zip", "application/zip")
    else:
        st.info("Run the study to see results for the current inputs. Research results are kept separate from the in-sample dashboard.")

with tab5:
    st.subheader("Apply the finance behind the dashboard")
    st.markdown("""
**Returns and benchmarks — BMC equities**

Equity returns can include capital gains and dividends. Adjusted prices aim to account for corporate actions and distributions. A broad index offers context; it is not a guaranteed return or an automatically suitable benchmark for every portfolio.

**Diversification — Finance Fundamentals**

Weights show where capital sits. Covariance describes how holdings move together. Compare capital share with risk share before treating the number of holdings as diversification.

**Risk versus reward — Finance Fundamentals**

Higher risk offers possible reward, not a promise. Read return, volatility, drawdown and tail losses together. A positive average can coexist with severe losses.

**Evidence quality — Finance Fundamentals**

Check the source, date window, missing assets and assumptions. Synthetic demonstrations and optimiser failures are labelled.

**Try this:** compare equal weight with minimum volatility. Identify which asset loses weight and how its risk share changes. Raise confidence from 95% to 99% and inspect the number of observations supporting CVaR.
""")
    with st.expander("Calculation conventions"):
        st.markdown("""
- **Daily return:** adjusted_price_today / adjusted_price_previous − 1.
- **CAGR:** product(1 + daily_returns) ** (252 / observations) − 1.
- **Volatility:** daily sample standard deviation × sqrt(252).
- **Sharpe:** mean daily excess return / daily sample volatility × sqrt(252). Convert the annual risk-free assumption to a compounded daily rate.
- **Sortino:** mean daily excess return / daily downside deviation × sqrt(252). The daily risk-free rate is the target; squared shortfalls are averaged over ALL observations.
- **VaR:** negative linearly interpolated return quantile at 1 − confidence.
- **CVaR:** negative mean of observed returns at or below that quantile. Ties can change the tail count.
- **Risk share:** weight_i × (covariance × weights)_i / portfolio variance.
- **Undefined ratios:** N/A. No tax, trading costs, slippage or FX conversion is modelled.
""")

with tab6:
    st.write({"source": provenance.get("source", "unknown"), "price_basis": provenance.get("price_basis", "unverified"), "benchmark": benchmark or None, "portfolio_assets": list(returns.columns)})
    st.dataframe(prices.tail(20), width="stretch")
    record = {
        "source": provenance.get("source", "unknown"), "synthetic": provenance.get("synthetic"),
        "price_basis": provenance.get("price_basis", "unverified"),
        "start": str(prices.index[0].date()), "end": str(prices.index[-1].date()),
        "return_observations": len(returns), "allocation": method,
        "benchmark": benchmark if benchmark_returns is not None else "",
        "confidence": confidence, "annual_risk_free_rate": risk_free_rate,
        "portfolio_value_usd": initial_value, "tail_observations": metrics["tail_observations"],
        **{k: metrics[k] for k in ["annualized_return", "annualized_volatility", "sharpe_ratio", "sortino_ratio", "max_drawdown", "historical_var", "conditional_var"]},
        **{f"weight_{asset}": weight for asset, weight in weights.items()},
    }
    st.download_button("Download analysis summary (CSV)", pd.DataFrame([record]).to_csv(index=False).encode("utf-8"), "portfolio-analysis-summary.csv", "text/csv")
    st.caption("Export includes source, synthetic flag, weights and assumptions. The CLI can save prices with a provenance sidecar; dashboard views do not overwrite files.")
