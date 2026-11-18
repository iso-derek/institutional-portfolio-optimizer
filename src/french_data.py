"""Real US industry returns from the Kenneth R. French Data Library.

The library publishes daily value-weighted returns for 12 US industry portfolios
(built from CRSP data, July 1926 onward) and the market and one-month T-bill
returns. It is freely available for research and is widely cited; we download
it on demand, cache it locally and never redistribute the files.

Returns are converted to total-return indexes (start = 100) so the rest of the
optimiser can treat each industry like an asset price series.
"""
from __future__ import annotations

import io
import time
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
INDUSTRY_FILE = "12_Industry_Portfolios_daily_CSV.zip"
FACTOR_FILE = "F-F_Research_Data_Factors_daily_CSV.zip"
CACHE = Path(__file__).resolve().parents[1] / "data" / "cache" / "french"
CACHE_DAYS = 7
MARKET = "MARKET"
INDUSTRIES = {
    "NODUR": "Consumer staples", "DURBL": "Consumer durables", "MANUF": "Manufacturing", "ENRGY": "Energy",
    "CHEMS": "Chemicals", "BUSEQ": "Technology & business equipment", "TELCM": "Telecoms", "UTILS": "Utilities",
    "SHOPS": "Retail & wholesale", "HLTH": "Healthcare", "MONEY": "Finance", "OTHER": "Other industries",
}
LABELS = {**INDUSTRIES, MARKET: "US stock market"}
CITATION = "Kenneth R. French Data Library, Tuck School of Business at Dartmouth (returns built from CRSP data)."
SOURCE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"


def _download(name: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_DAYS * 86400:
        return path.read_bytes()
    request = urllib.request.Request(f"{BASE}/{name}", headers={"User-Agent": "portfolio-lab/1.0 (educational research)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
    path.with_suffix(".part").write_bytes(body)
    path.with_suffix(".part").replace(path)
    return body


def _first_block(text: str) -> pd.DataFrame:
    """Parse the first daily table in a French CSV (the value-weighted returns)."""
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith(","))
    rows = []
    for line in lines[header + 1:]:
        if not line.strip() or not line.strip()[0].isdigit():
            break
        rows.append(line)
    frame = pd.read_csv(io.StringIO("\n".join([lines[header]] + rows)), skipinitialspace=True)
    frame = frame.rename(columns={frame.columns[0]: "date"})
    frame["date"] = pd.to_datetime(frame.date.astype(str), format="%Y%m%d")
    return frame.set_index("date")


def daily_returns() -> pd.DataFrame:
    """Daily decimal returns: 12 industries plus MARKET, and the risk-free rate as RF."""
    industries = _first_block(zipfile.ZipFile(io.BytesIO(_download(INDUSTRY_FILE))).read(
        zipfile.ZipFile(io.BytesIO(_download(INDUSTRY_FILE))).namelist()[0]).decode("latin-1"))
    factors = _first_block(zipfile.ZipFile(io.BytesIO(_download(FACTOR_FILE))).read(
        zipfile.ZipFile(io.BytesIO(_download(FACTOR_FILE))).namelist()[0]).decode("latin-1"))
    industries.columns = [column.upper() for column in industries.columns]
    returns = industries.join(factors[["Mkt-RF", "RF"]], how="inner")
    returns[MARKET] = returns["Mkt-RF"] + returns["RF"]
    returns = returns.drop(columns="Mkt-RF")
    returns = returns.mask(returns <= -99.99)  # the library marks missing data as -99.99 or -999
    return returns / 100


def fetch_industry_prices(tickers: list[str], start: str | date, end: str | date) -> pd.DataFrame:
    """Total-return indexes (first day = 100) for the requested industries and MARKET."""
    returns = daily_returns()
    unknown = [ticker for ticker in tickers if ticker not in LABELS]
    window = returns.loc[pd.Timestamp(start):pd.Timestamp(end)]
    if window.empty:
        raise ValueError(f"The French data library covers July 1926 to {returns.index[-1]:%d %B %Y}. Choose dates in that range.")
    chosen = [ticker for ticker in tickers if ticker in LABELS]
    prices = (1 + window[chosen].fillna(0)).cumprod() * 100
    prices.index.name = "Date"
    prices.attrs.update(
        source="french", synthetic=False, price_basis="total-return index from daily value-weighted industry returns",
        citation=CITATION, source_url=SOURCE_URL, requested_tickers=list(tickers), unavailable_tickers=unknown,
        data_through=str(returns.index[-1].date()), average_risk_free=float(window.RF.mean() * 252),
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    return prices
