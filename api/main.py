"""JSON API for the Portfolio Lab web app.

All calculations come from the tested modules in ``src/``; this layer validates
the portfolio settings, caches results and shapes them for the screens.

Run for development:  .venv/Scripts/python -m uvicorn api.main:app --reload
"""
from __future__ import annotations

import sys
import threading
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analytics import portfolio_metrics  # noqa: E402
from data_generation import DEFAULT_TICKERS, fetch_price_data, generate_synthetic_prices  # noqa: E402
from modelling import (black_litterman_placeholder, efficient_frontier, maximum_sharpe_portfolio,  # noqa: E402
                       minimum_volatility_portfolio, monte_carlo_simulation)
from preprocessing import calculate_returns, clean_prices, normalize_weights  # noqa: E402
from research import walk_forward_study  # noqa: E402
from stress import stress_portfolio  # noqa: E402
from french_data import CITATION as FRENCH_CITATION, INDUSTRIES, LABELS as FRENCH_LABELS, MARKET, SOURCE_URL as FRENCH_URL, fetch_industry_prices  # noqa: E402

Method = Literal["equal", "max_sharpe", "min_vol", "tilt"]
Source = Literal["demo", "yahoo", "french"]
METHOD_NAMES = {"equal": "Equal weight", "max_sharpe": "Maximum Sharpe", "min_vol": "Minimum volatility",
                "tilt": "Historical-return tilt"}
MAX_POINTS = 400

app = FastAPI(title="Portfolio Lab API", version="1.0.0")
_lock = threading.Lock()


# ---------------------------------------------------------------- settings
class Portfolio(BaseModel):
    model_config = ConfigDict(frozen=True)

    tickers: tuple[str, ...]
    benchmark: str
    start: date
    end: date
    source: Source
    value: float
    risk_free: float
    confidence: float
    method: Method


def portfolio_settings(
    tickers: str = Query(",".join(DEFAULT_TICKERS), description="Comma-separated symbols"),
    benchmark: str = "SPY",
    start: date | None = None,
    end: date | None = None,
    source: Source = "demo",
    live: bool = False,
    value: float = Query(100_000, gt=0, le=1e12),
    risk_free: float = Query(0.02, ge=0, le=0.2),
    confidence: float = Query(0.95, ge=0.9, le=0.995),
    method: Method = "equal",
) -> Portfolio:
    symbols = tuple(dict.fromkeys(t.strip().upper() for t in tickers.replace(" ", ",").split(",") if t.strip()))
    benchmark = benchmark.strip().upper()
    if not symbols or len(symbols) > 20 or any(len(s) > 20 for s in symbols):
        raise HTTPException(400, "Enter between 1 and 20 ticker symbols.")
    if len(benchmark) > 20 or " " in benchmark or "," in benchmark:
        raise HTTPException(400, "Use a single benchmark symbol, or leave it blank.")
    if live and source == "demo":  # older clients sent live=true for Yahoo prices
        source = "yahoo"
    end = end or date.today()
    start = start or end - timedelta(days=365 * 5)
    if start >= end:
        raise HTTPException(400, "The start date must be before the end date.")
    return Portfolio(tickers=symbols, benchmark=benchmark, start=start, end=end, source=source, value=value,
                     risk_free=risk_free, confidence=confidence, method=method)


# ---------------------------------------------------------------- cached calculations
@lru_cache(maxsize=16)
def _prices(requested: tuple[str, ...], start: date, end: date, source: str) -> pd.DataFrame:
    if source == "french":
        return fetch_industry_prices(list(requested), start, end)
    if source == "yahoo":
        return fetch_price_data(list(requested), start=start, end=end, save_path=None)
    prices = generate_synthetic_prices(list(requested), start=start, end=end)
    prices.attrs.update(source="synthetic", synthetic=True, price_basis="fictional prices",
                        fallback_reason="Reproducible demonstration data.", requested_tickers=list(requested))
    return prices


@lru_cache(maxsize=16)
def _inputs(p: Portfolio):
    requested = tuple(dict.fromkeys(p.tickers + ((p.benchmark,) if p.benchmark else ())))
    raw = _prices(requested, p.start, p.end, p.source)
    provenance = dict(raw.attrs)
    all_returns = calculate_returns(raw)
    prices = clean_prices(raw)
    available = [t for t in p.tickers if t in all_returns]
    if not available:
        raise ValueError("None of these assets have enough price history for the chosen dates.")
    returns = all_returns[available]
    benchmark_returns = all_returns[p.benchmark] if p.benchmark and p.benchmark in all_returns else None
    if p.source == "french":  # show industry names, not library codes, everywhere downstream
        prices, returns = prices.rename(columns=FRENCH_LABELS), returns.rename(columns=FRENCH_LABELS)
        if benchmark_returns is not None:
            benchmark_returns = benchmark_returns.rename(FRENCH_LABELS.get(p.benchmark, p.benchmark))
    return prices, returns, benchmark_returns, provenance


def display_name(p: Portfolio, ticker: str) -> str:
    return FRENCH_LABELS.get(ticker, ticker) if p.source == "french" else ticker


@lru_cache(maxsize=16)
def _optimised(p: Portfolio):
    _, returns, _, _ = _inputs(p)
    return {"max_sharpe": maximum_sharpe_portfolio(returns, p.risk_free),
            "min_vol": minimum_volatility_portfolio(returns, p.risk_free)}


def _weights(p: Portfolio) -> tuple[pd.Series, list[str]]:
    _, returns, _, _ = _inputs(p)
    notes = []
    if p.method in ("max_sharpe", "min_vol"):
        result = _optimised(p)[p.method]
        if not result["success"]:
            notes.append("The optimiser did not converge, so equal weights are shown. " + result["message"])
        return result["weights"], notes
    if p.method == "tilt":
        notes.append("Historical-return tilt is a simple heuristic, not a Black–Litterman model.")
        return black_litterman_placeholder(returns), notes
    return normalize_weights(None, returns.columns), notes


@lru_cache(maxsize=16)
def _analysis(p: Portfolio):
    prices, returns, benchmark_returns, provenance = _inputs(p)
    weights, notes = _weights(p)
    metrics = portfolio_metrics(returns, weights, p.risk_free, benchmark=display_name(p, p.benchmark),
                                benchmark_returns=benchmark_returns, confidence=p.confidence)
    return prices, returns, benchmark_returns, provenance, weights, notes, metrics


def run(fn, *args):
    with _lock:
        try:
            return fn(*args)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except (OSError, RuntimeError) as exc:
            raise HTTPException(503, f"Market data is unavailable right now: {exc}") from exc


# ---------------------------------------------------------------- helpers
def num(value) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def thin(frame: pd.DataFrame | pd.Series) -> pd.DataFrame:
    """Down-sample a daily series for charting, always keeping the last point."""
    frame = frame.to_frame() if isinstance(frame, pd.Series) else frame
    if len(frame) <= MAX_POINTS:
        return frame
    step = int(np.ceil(len(frame) / MAX_POINTS))
    picked = frame.iloc[::step]
    return pd.concat([picked, frame.iloc[[-1]]]) if picked.index[-1] != frame.index[-1] else picked


def series(frame: pd.DataFrame | pd.Series, names: dict[str, str] | None = None) -> list[dict]:
    frame = thin(frame)
    rows = []
    for stamp, row in frame.iterrows():
        item = {"date": pd.Timestamp(stamp).strftime("%Y-%m-%d")}
        for column, value in row.items():
            item[(names or {}).get(str(column), str(column))] = num(value)
        rows.append(item)
    return rows


def sample_info(prices: pd.DataFrame, returns: pd.DataFrame, provenance: dict, p: Portfolio) -> dict:
    missing = sorted(display_name(p, t) for t in p.tickers if display_name(p, t) not in set(returns.columns))
    return {
        "synthetic": bool(provenance.get("synthetic")),
        "source": ("Simulated demonstration prices" if provenance.get("synthetic")
                   else FRENCH_CITATION if provenance.get("source") == "french" else "Yahoo Finance adjusted close prices"),
        "source_url": provenance.get("source_url"),
        "data_through": provenance.get("data_through"),
        "average_risk_free": provenance.get("average_risk_free"),
        "benchmark_name": display_name(p, p.benchmark) if p.benchmark else None,
        "fallback_reason": provenance.get("fallback_reason") if provenance.get("synthetic") and p.source == "yahoo" else None,
        "start": prices.index[0].strftime("%Y-%m-%d"),
        "end": prices.index[-1].strftime("%Y-%m-%d"),
        "observations": int(len(returns)),
        "assets": list(returns.columns),
        "missing": missing,
    }


# ---------------------------------------------------------------- endpoints
@app.get("/api/defaults")
def defaults():
    today = date.today()
    return {"tickers": list(DEFAULT_TICKERS), "benchmark": "SPY", "start": str(today - timedelta(days=365 * 5)),
            "end": str(today), "value": 100_000, "risk_free": 0.02, "confidence": 0.95, "method": "equal",
            "methods": [{"key": key, "label": label} for key, label in METHOD_NAMES.items()],
            "sources": [
                {"key": "demo", "label": "Demo (simulated)", "note": "Reproducible fictional prices."},
                {"key": "french", "label": "Real US industries", "note": FRENCH_CITATION, "url": FRENCH_URL},
                {"key": "yahoo", "label": "Yahoo Finance", "note": "Live adjusted prices via yfinance; Yahoo data is for personal use only."},
            ],
            "industries": [{"key": key, "label": label} for key, label in INDUSTRIES.items()],
            "market": MARKET}


@app.get("/api/analysis")
def analysis(p: Portfolio = Depends(portfolio_settings)):
    prices, returns, benchmark_returns, provenance, weights, notes, m = run(_analysis, p)
    comparison = m["benchmark_comparison"] or {}
    benchmark_ok = benchmark_returns is not None
    if p.benchmark and not benchmark_ok:
        notes.append(f"Benchmark {display_name(p, p.benchmark)} has no usable prices for these dates, so benchmark comparisons are hidden.")
    growth = None
    if comparison:
        growth = series(comparison["growth"].rename(columns={"Benchmark": "benchmark", "Portfolio": "portfolio"}))
    else:
        growth = series((1 + m["portfolio_returns"]).cumprod().mul(100).rename("portfolio"))
    attribution = m["return_attribution"]
    diversification = m["diversification"]
    allocation = diversification["allocation_vs_risk"]
    correlation = m["correlation"]
    return {
        "sample": sample_info(prices, returns, provenance, p),
        "notes": notes,
        "method": METHOD_NAMES[p.method],
        "weights": [{"asset": a, "weight": num(w)} for a, w in weights.items()],
        "kpis": {
            "cagr": num(m["annualized_return"]), "volatility": num(m["annualized_volatility"]),
            "sharpe": num(m["sharpe_ratio"]), "sortino": num(m["sortino_ratio"]),
            "max_drawdown": num(m["max_drawdown"]), "cvar": num(m["conditional_var"]),
            "beta": num(m["beta"]) if benchmark_ok else None,
            "alpha": num(comparison.get("alpha")) if comparison else None,
            "total_return": num(attribution["portfolio_total_return"]),
            "benchmark_total_return": num(comparison.get("benchmark_total_return")) if comparison else None,
            "tracking_error": num(comparison.get("tracking_error")) if comparison else None,
            "information_ratio": num(comparison.get("information_ratio")) if comparison else None,
        },
        "growth": growth,
        "assets_growth": series(m["asset_cumulative_returns"]),
        "drawdown": series(m["drawdown"].rename("drawdown")),
        "rolling": series(comparison["rolling"]) if comparison else None,
        "attribution": [{"asset": r.asset, "weight": num(r.weight), "contribution": num(r.compounded_return_contribution)}
                        for r in attribution["by_asset"].itertuples(index=False)],
        "tail": {
            "confidence": p.confidence, "observations": int(m["tail_observations"]),
            "rows": [{"label": label, "fraction": num(m[key]), "dollars": num(m[key] * p.value)}
                     for label, key in [("Historical value at risk", "historical_var"),
                                        ("Normal-model value at risk", "parametric_var"),
                                        ("Expected shortfall (CVaR)", "conditional_var")]],
        },
        "correlation": {"assets": list(correlation.columns),
                        "values": [[num(v) for v in row] for row in correlation.to_numpy()]},
        "diversification": {
            "effective_holdings": num(diversification["effective_holdings"]),
            "largest_weight": num(diversification["largest_weight"]),
            "reduction": num(diversification["diversification_reduction"]),
            "average_correlation": num(diversification["average_pairwise_correlation"]),
            "rows": [{"asset": r.asset, "capital": num(r.weight), "risk": num(r.risk_contribution)}
                     for r in allocation.itertuples(index=False)],
        },
    }


@lru_cache(maxsize=8)
def _optimisation(p: Portfolio):
    _, returns, _, _ = _inputs(p)
    frontier = efficient_frontier(returns, n_points=30, risk_free_rate=p.risk_free)
    cloud = monte_carlo_simulation(returns, n_portfolios=2000, risk_free_rate=p.risk_free)
    return frontier, cloud


@app.get("/api/optimise")
def optimise(p: Portfolio = Depends(portfolio_settings)):
    frontier, cloud = run(_optimisation, p)
    _, returns, _, _ = run(_inputs, p)
    optimised = run(_optimised, p)
    candidates = {"equal": normalize_weights(None, returns.columns),
                  **{key: result["weights"] for key, result in optimised.items()}}
    rows = []
    for key, weights in candidates.items():
        m = run(lambda: portfolio_metrics(returns, weights, p.risk_free, confidence=p.confidence))
        rows.append({"key": key, "label": METHOD_NAMES[key], "cagr": num(m["annualized_return"]),
                     "volatility": num(m["annualized_volatility"]), "sharpe": num(m["sharpe_ratio"]),
                     "max_drawdown": num(m["max_drawdown"]),
                     "converged": key == "equal" or bool(optimised[key]["success"]),
                     "weights": [{"asset": a, "weight": num(w)} for a, w in weights.items()]})
    solved = frontier.sort_values("expected_return")
    sample = cloud.sample(min(len(cloud), 700), random_state=7)
    return {
        "frontier": [{"volatility": num(r.expected_volatility), "return": num(r.expected_return), "sharpe": num(r.expected_sharpe)}
                     for r in solved.itertuples(index=False)],
        "cloud": [{"volatility": num(r.expected_volatility), "return": num(r.expected_return)} for r in sample.itertuples(index=False)],
        "allocations": rows,
    }


class ResearchSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    lookback: Literal[63, 126, 252] = 126
    rebalance_every: Literal[1, 5, 21, 63] = 21
    max_weight: float = Field(0.35, gt=0, le=1)
    cost_bps: float = Field(10, ge=0, le=100)
    extended: bool = True
    trigger: float = Field(1.25, ge=0.5, le=3)
    defensive: float = Field(0.5, ge=0, le=1)


@lru_cache(maxsize=8)
def _research(p: Portfolio, s: ResearchSettings):
    _, returns, _, _ = _inputs(p)
    cap = max(s.max_weight, 1 / len(returns.columns))
    return walk_forward_study(returns, s.lookback, s.rebalance_every, cap, s.cost_bps, p.risk_free, p.confidence,
                              s.extended, s.trigger, s.defensive)


@app.post("/api/research")
def research(settings: ResearchSettings, p: Portfolio = Depends(portfolio_settings)):
    study = run(_research, p, settings)
    summary = study["summary"]
    dates = study["net_returns"].index
    strategies = []
    for name, row in summary.iterrows():
        strategies.append({"name": name, "net_cagr": num(row.net_cagr), "gross_cagr": num(row.gross_cagr),
                           "volatility": num(row.net_volatility), "sharpe": num(row.net_sharpe),
                           "max_drawdown": num(row.max_drawdown), "cvar": num(row.one_day_cvar),
                           "turnover": num(row.annual_traded_fraction), "largest_weight": num(row.mean_largest_target_weight),
                           "excess": num(row.annual_mean_excess_vs_equal), "excess_low": num(row.mean_excess_ci_low),
                           "excess_high": num(row.mean_excess_ci_high)})
    return {"start": dates[0].strftime("%Y-%m-%d"), "end": dates[-1].strftime("%Y-%m-%d"),
            "observations": int(len(dates)), "growth": series(study["growth"]), "strategies": strategies,
            "failures": [{"date": pd.Timestamp(f["date"]).strftime("%Y-%m-%d"), "strategy": f["strategy"], "message": f["message"]}
                         for f in study["failures"]]}


class Exposure(BaseModel):
    asset: str
    asset_class: Literal["Equity", "Bond", "Cash", "Other"] = "Equity"
    currency: str = Field("USD", min_length=3, max_length=3)
    duration: float = Field(0, ge=0, le=50)


class StressRequest(BaseModel):
    exposures: list[Exposure]
    equity_shock: float = Field(-0.2, ge=-0.95, le=1)
    yield_shift_bps: float = Field(200, ge=-500, le=1000)
    fx_shock: float = Field(-0.1, ge=-0.95, le=1)
    inflation: float = Field(0.03, ge=-0.2, le=1)
    other_shock: float = Field(-0.1, ge=-0.95, le=1)


@app.post("/api/stress")
def stress(request: StressRequest, p: Portfolio = Depends(portfolio_settings)):
    *_, weights, _, _ = run(_analysis, p)
    chosen = {e.asset: e for e in request.exposures}
    frame = pd.DataFrame([{"asset": asset, "weight": float(weight),
                           "asset_class": chosen[asset].asset_class if asset in chosen else "Equity",
                           "currency": (chosen[asset].currency if asset in chosen else "USD").upper(),
                           "modified_duration": chosen[asset].duration if asset in chosen else 0.0}
                          for asset, weight in weights.items()])
    shocks = {currency: (0.0 if currency == "USD" else request.fx_shock) for currency in frame.currency.unique()}
    result = run(stress_portfolio, frame, request.equity_shock, request.yield_shift_bps, shocks,
                 request.inflation, p.value, request.other_shock)
    return {"nominal_return": num(result["nominal_return"]), "real_return": num(result["real_return"]),
            "pnl": num(result["pnl_usd"]), "real_pnl": num(result["real_pnl_usd"]), "limitations": result["limitations"],
            "assets": [{"asset": r.asset, "weight": num(r.weight), "asset_class": r.asset_class, "currency": r.currency,
                        "local_return": num(r.local_return), "fx_return": num(r.fx_return), "return": num(r.usd_return),
                        "contribution": num(r.portfolio_contribution), "pnl": num(r.pnl_usd)}
                       for r in result["assets"].itertuples(index=False)]}


@app.get("/api/prices")
def prices(p: Portfolio = Depends(portfolio_settings)):
    frame, *_ = run(_inputs, p)
    recent = frame.tail(15).iloc[::-1]
    return {"assets": list(recent.columns),
            "rows": [{"date": stamp.strftime("%Y-%m-%d"), "prices": [num(v) for v in row]} for stamp, row in recent.iterrows()]}


@app.get("/api/downloads/prices")
def download_prices(p: Portfolio = Depends(portfolio_settings)):
    frame, *_ = run(_inputs, p)
    return Response(frame.to_csv(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="portfolio_prices.csv"'})


@app.get("/api/health")
def health():
    return {"status": "ok"}


WEB_DIST = ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (WEB_DIST / path).resolve()
        if path and candidate.is_file() and WEB_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
