"""Offline provenance, provider-failure and data-quality checks."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from data_generation import fetch_price_data, load_price_data, parse_tickers
from preprocessing import clean_prices
from modelling import minimum_volatility_portfolio


class DataTests(unittest.TestCase):
    def test_adjusted_prices_keep_source_and_sidecar(self):
        frame = pd.DataFrame({"Adj Close": np.arange(100., 145.)}, index=pd.bdate_range("2026-01-01", periods=45))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            with patch.dict(sys.modules, {"yfinance": SimpleNamespace(download=lambda *a, **k: frame)}):
                result = fetch_price_data(["AAPL"], "2026-01-01", "2026-03-01", save_path=path)
            self.assertFalse(result.attrs["synthetic"])
            self.assertEqual(result.attrs["price_basis"], "adjusted close")
            self.assertEqual(load_price_data(path).attrs, result.attrs)
            self.assertTrue(path.with_suffix(".metadata.json").exists())

    def test_failed_download_is_never_labelled_real(self):
        def fail(*args, **kwargs):
            raise ConnectionError("Offline test")
        with patch.dict(sys.modules, {"yfinance": SimpleNamespace(download=fail)}):
            result = fetch_price_data(["AAPL"], "2026-01-01", "2026-03-01", save_path=None)
        self.assertTrue(result.attrs["synthetic"])
        self.assertEqual(result.attrs["source"], "synthetic")
        self.assertIn("Offline test", result.attrs["fallback_reason"])

    def test_unadjusted_prices_are_not_silently_substituted(self):
        frame = pd.DataFrame({"Close": [100., 101.]})
        with patch.dict(sys.modules, {"yfinance": SimpleNamespace(download=lambda *a, **k: frame)}):
            result = fetch_price_data(["AAPL"], "2026-01-01", "2026-03-01", save_path=None)
        self.assertTrue(result.attrs["synthetic"])

    def test_legacy_csv_has_unknown_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            path.write_text("Date,A\n2026-01-01,100\n2026-01-02,101\n")
            self.assertEqual(load_price_data(path).attrs["source"], "unknown")

    def test_cleaning_bounds_fill_and_rejects_short_samples(self):
        prices = pd.DataFrame({"A": np.arange(100., 150.)}, index=pd.bdate_range("2026-01-01", periods=50))
        prices.iloc[10:14, 0] = np.nan
        cleaned = clean_prices(prices)
        self.assertIn(prices.index[12], cleaned.index)
        self.assertNotIn(prices.index[13], cleaned.index)
        self.assertFalse(cleaned.isna().any().any())
        with self.assertRaisesRegex(ValueError, "30 aligned"):
            clean_prices(prices.head(10))
        with self.assertRaisesRegex(ValueError, "unique"):
            clean_prices(pd.concat([prices, prices.tail(1)]))

    def test_duplicate_symbols_deduplicate(self):
        self.assertEqual(parse_tickers("aapl, AAPL msft"), ["AAPL", "MSFT"])

    def test_optimiser_failure_is_disclosed(self):
        returns = pd.DataFrame({"A": [.01, -.01, .02], "B": [.02, -.03, .01]})
        with patch("modelling.minimize", side_effect=RuntimeError("test failure")):
            result = minimum_volatility_portfolio(returns)
        self.assertFalse(result["success"])
        self.assertIn("test failure", result["message"])
        np.testing.assert_allclose(result["weights"], [.5, .5])


if __name__ == "__main__":
    unittest.main()
