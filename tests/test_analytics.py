"""Numerical checks for financially meaningful identities and edge cases."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analytics import (TRADING_DAYS, benchmark_comparison, diversification_metrics,
                       drawdown_series, portfolio_metrics, sharpe_ratio, sortino_ratio)
from modelling import expected_sharpe
from preprocessing import normalize_weights


class AnalyticsTests(unittest.TestCase):
    def test_first_day_loss_is_in_drawdown(self):
        result = drawdown_series(pd.Series([-0.1, -0.1, 0.5]))
        np.testing.assert_allclose(result, [-0.1, -0.19, 0.0], atol=1e-12)

    def test_sharpe_matches_daily_excess_and_optimiser(self):
        returns = pd.Series([0.10, -0.05, 0.03, -0.02])
        daily_rf = 1.04 ** (1 / 252) - 1
        expected = (0.015 - daily_rf) / np.std(returns, ddof=1) * np.sqrt(252)
        self.assertAlmostEqual(sharpe_ratio(returns, 0.04), expected)
        self.assertAlmostEqual(expected_sharpe(returns.to_frame("A"), np.array([1.0]), 0.04), expected)

    def test_sortino_uses_all_periods_not_std_of_losses(self):
        returns = pd.Series([0.10, -0.05, 0.03, -0.02])
        downside = np.sqrt((0.05**2 + 0.02**2) / 4)
        self.assertAlmostEqual(sortino_ratio(returns, 0.0), 0.015 / downside * np.sqrt(TRADING_DAYS))
        target = 1.04 ** (1 / 252) - 1
        expected = (returns.mean() - target) / np.sqrt(np.minimum(returns - target, 0).pow(2).mean()) * np.sqrt(252)
        self.assertAlmostEqual(sortino_ratio(returns, 0.04), expected)

    def test_zero_risk_ratios_are_undefined(self):
        self.assertTrue(np.isnan(sharpe_ratio(pd.Series([0.01] * 5), 0)))
        self.assertTrue(np.isnan(sortino_ratio(pd.Series([0.01] * 5), 0)))

    def test_more_holdings_do_not_ensure_diversification(self):
        base = pd.Series([-0.02, 0.02, -0.02, 0.02])
        result = diversification_metrics(pd.DataFrame({"A": 2 * base, "B": base}), pd.Series({"A": .5, "B": .5}))
        self.assertAlmostEqual(result["effective_holdings"], 2)
        self.assertAlmostEqual(result["diversification_reduction"], 0)
        np.testing.assert_allclose(result["allocation_vs_risk"]["risk_contribution"], [2/3, 1/3])

    def test_uncorrelated_assets_reduce_volatility(self):
        returns = pd.DataFrame({"A": [-.02, .02, -.02, .02], "B": [-.02, -.02, .02, .02]})
        result = diversification_metrics(returns, pd.Series({"A": .5, "B": .5}))
        self.assertAlmostEqual(result["diversification_reduction"], 1 - 1/np.sqrt(2))
        self.assertAlmostEqual(result["allocation_vs_risk"]["risk_contribution"].sum(), 1)
        self.assertAlmostEqual(result["average_pairwise_correlation"], 0)

    def test_separate_benchmark_does_not_become_a_holding(self):
        index = pd.date_range("2026-01-01", periods=4)
        returns = pd.DataFrame({"A": [.01, -.02, .03, .02]}, index=index)
        benchmark = pd.Series([.02, -.04, .06, .04], index=index, name="SPY")
        metrics = portfolio_metrics(returns, pd.Series({"A": 1.0}), benchmark_returns=benchmark)
        self.assertEqual(list(metrics["weights"].index), ["A"])
        self.assertAlmostEqual(metrics["beta"], .5)
        self.assertAlmostEqual(metrics["benchmark_comparison"]["benchmark_total_return"], np.prod(1 + benchmark) - 1)

    def test_identical_benchmark_has_zero_tracking_error(self):
        returns = pd.Series([.01, -.02, .03])
        result = benchmark_comparison(returns, returns)
        self.assertEqual(result["tracking_error"], 0)
        self.assertTrue(np.isnan(result["information_ratio"]))

    def test_tail_confidence_changes_loss_and_count(self):
        returns = pd.DataFrame({"A": np.linspace(-.2, .2, 101)})
        low = portfolio_metrics(returns, pd.Series({"A": 1}), confidence=.95)
        high = portfolio_metrics(returns, pd.Series({"A": 1}), confidence=.99)
        self.assertGreaterEqual(high["historical_var"], low["historical_var"])
        self.assertGreaterEqual(high["conditional_var"], high["historical_var"])
        self.assertLess(high["tail_observations"], low["tail_observations"])

    def test_invalid_long_only_allocations_fail_explicitly(self):
        for weights in [{"A": -1, "B": 2}, {"A": np.inf}, {"A": np.nan}, {"A": 0}, {"MISSING": 1}]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                normalize_weights(weights, ["A", "B"])
        with self.assertRaises(ValueError):
            normalize_weights(None, [])


if __name__ == "__main__":
    unittest.main()
