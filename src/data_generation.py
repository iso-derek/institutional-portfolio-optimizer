"""Data loading utilities for the institutional portfolio optimizer.

The app attempts to use yfinance for real historical prices. If a network
download fails, it falls back to deterministic synthetic price data so the
repository remains runnable during demos and reviews.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import json

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_PRICE_PATH = RAW_DIR / "asset_prices.csv"
DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "JPM", "GS", "BLK"]


def parse_tickers(tickers: str | list[str] | None = None) -> list[str]:
    if tickers is None:
        return DEFAULT_TICKERS
    if isinstance(tickers, str):
        tickers = tickers.replace(",", " ").split()
    cleaned = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    return list(dict.fromkeys(cleaned)) or DEFAULT_TICKERS.copy()


def generate_synthetic_prices(
    tickers: list[str],
    start: str | date,
    end: str | date,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate correlated geometric random-walk price paths."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, end=end)
    n_assets = len(tickers)
    base_correlation = 0.35
    corr = np.full((n_assets, n_assets), base_correlation)
    np.fill_diagonal(corr, 1.0)
    vol = np.linspace(0.012, 0.022, n_assets)
    cov = np.outer(vol, vol) * corr
    returns = rng.multivariate_normal(
        mean=np.linspace(0.0002, 0.00045, n_assets),
        cov=cov,
        size=len(dates),
    )
    prices = pd.DataFrame(100 * np.exp(np.cumsum(returns, axis=0)), index=dates, columns=tickers)
    prices.index.name = "Date"
    return prices.round(2)


def fetch_price_data(
    tickers: str | list[str] | None = None,
    start: str | date | None = None,
    end: str | date | None = None,
    save_path: Path | None = RAW_PRICE_PATH,
) -> pd.DataFrame:
    """Fetch adjusted close prices and save them to CSV."""
    ticker_list = parse_tickers(tickers)
    end = end or date.today()
    start = start or (pd.to_datetime(end).date() - timedelta(days=365 * 5))
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"source": "yfinance", "synthetic": False, "price_basis": "adjusted close", "requested_tickers": ticker_list}

    try:
        import yfinance as yf

        downloaded = yf.download(
            ticker_list,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            group_by="column",
            threads=True,
        )
        if downloaded.empty:
            raise ValueError("No rows returned by yfinance.")
        if isinstance(downloaded.columns, pd.MultiIndex):
            if "Adj Close" not in downloaded.columns.get_level_values(0):
                raise ValueError("Adjusted close data is unavailable; refusing to silently use unadjusted close.")
            prices = downloaded["Adj Close"]
        else:
            if "Adj Close" not in downloaded.columns:
                raise ValueError("Adjusted close data is unavailable.")
            prices = downloaded[["Adj Close"]].rename(columns={"Adj Close": ticker_list[0]})
        prices = prices.dropna(axis=1, how="all")
        if prices.empty:
            raise ValueError("No valid price columns after cleaning.")
    except Exception as exc:
        print(f"Warning: using synthetic prices because market data download failed: {exc}")
        prices = generate_synthetic_prices(ticker_list, start=start, end=end)
        metadata.update({"source": "synthetic", "synthetic": True, "price_basis": "fictional prices", "fallback_reason": str(exc)})

    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "Date"
    metadata["unavailable_tickers"] = [ticker for ticker in ticker_list if ticker not in prices.columns]
    prices.attrs.update(metadata)
    if save_path is not None:
        prices.to_csv(save_path)
        save_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return prices


def load_price_data(path: Path = RAW_PRICE_PATH) -> pd.DataFrame:
    if not path.exists():
        return fetch_price_data(save_path=path)
    prices = pd.read_csv(path, index_col="Date", parse_dates=True)
    metadata_path = path.with_suffix(".metadata.json")
    prices.attrs.update(json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {"source": "unknown", "price_basis": "unverified", "synthetic": None})
    return prices


if __name__ == "__main__":
    df = fetch_price_data()
    print(f"Saved {df.shape[0]:,} rows and {df.shape[1]} assets to {RAW_PRICE_PATH}")
