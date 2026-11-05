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
from preprocessing import calculate_returns, clean_prices
from modelling import efficient_frontier, minimum_volatility_portfolio


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

    def test_live_download_can_fail_closed_without_synthetic_substitution(self):
        def fail(*args, **kwargs):
            raise ConnectionError("offline")
        with patch.dict(sys.modules, {"yfinance": SimpleNamespace(download=fail)}):
            with self.assertRaisesRegex(RuntimeError, "synthetic substitution is disabled"):
                fetch_price_data(["AAPL"], "2026-01-01", "2026-03-01", save_path=None,
                                 allow_synthetic_fallback=False)

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

    def test_returns_do_not_bridge_a_removed_source_observation(self):
        prices = pd.DataFrame({"A": np.arange(100., 150.)}, index=pd.bdate_range("2026-01-01", periods=50))
        prices.iloc[10:14, 0] = np.nan
        returns = calculate_returns(prices)
        self.assertNotIn(prices.index[13], returns.index)
        self.assertNotIn(prices.index[14], returns.index)
        self.assertIn(prices.index[15], returns.index)

    def test_duplicate_symbols_deduplicate(self):
        self.assertEqual(parse_tickers("aapl, AAPL msft"), ["AAPL", "MSFT"])

    def test_optimiser_failure_is_disclosed(self):
        returns = pd.DataFrame({"A": [.01, -.01, .02], "B": [.02, -.03, .01]})
        with patch("modelling.minimize", side_effect=RuntimeError("test failure")):
            result = minimum_volatility_portfolio(returns)
        self.assertFalse(result["success"])
        self.assertIn("test failure", result["message"])
        np.testing.assert_allclose(result["weights"], [.5, .5])

    def test_solver_success_with_invalid_weights_is_rejected(self):
        returns = pd.DataFrame({"A": [.01, -.01, .02], "B": [.02, -.03, .01]})
        invalid = SimpleNamespace(success=True, message="claimed success", x=np.array([-0.2, 1.2]), fun=0.1)
        with patch("modelling.minimize", return_value=invalid):
            result = minimum_volatility_portfolio(returns)
        self.assertFalse(result["success"])
        self.assertIn("solution rejected", result["message"])
        np.testing.assert_allclose(result["weights"], [.5, .5])

    def test_frontier_solves_known_two_asset_target_and_constraints(self):
        returns = pd.DataFrame({
            "A": np.array([-.02, -.01, .01, .02]) + .001,
            "B": np.array([-.01, .02, -.02, .01]) + .002,
        })
        frontier = efficient_frontier(returns, n_points=3)
        self.assertEqual(len(frontier), 3)
        midpoint = frontier.iloc[(frontier.expected_return - .0015 * 252).abs().argmin()]
        self.assertAlmostEqual(midpoint["weight_A"], .5, places=6)
        self.assertAlmostEqual(midpoint["weight_B"], .5, places=6)
        self.assertLess(frontier.max_constraint_residual.max(), 1e-7)
        np.testing.assert_allclose(frontier[["weight_A", "weight_B"]].sum(axis=1), 1, atol=1e-7)

    def test_frontier_collapses_cleanly_when_asset_means_are_equal(self):
        returns = pd.DataFrame({
            "A": [-.02, -.01, .01, .02],
            "B": [-.01, .02, -.02, .01],
        })
        frontier = efficient_frontier(returns, n_points=5)
        self.assertEqual(len(frontier), 1)
        self.assertAlmostEqual(frontier.iloc[0]["expected_return"], 0.0, places=12)
        self.assertLess(frontier.iloc[0]["max_constraint_residual"], 1e-7)
        self.assertIn("reduces", frontier.iloc[0]["message"])


if __name__ == "__main__":
    unittest.main()
