"""Research-design checks: chronology, constraints, costs and paired inference."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from research import walk_forward_study, paired_block_interval


class ResearchTests(unittest.TestCase):
    @staticmethod
    def sample():
        rng = np.random.default_rng(901)
        return pd.DataFrame(rng.normal([.0002, .0003, .0004], [.006, .012, .018], size=(160, 3)),
                            columns=["A", "B", "C"], index=pd.bdate_range("2025-01-01", periods=160))

    def test_caps_and_chronological_training(self):
        data = self.sample()
        study = walk_forward_study(data, lookback=63, rebalance_every=21, max_weight=.4)
        weights = study["target_weights"]
        self.assertTrue((weights["training_end"] < weights["Date"]).all())
        np.testing.assert_allclose(weights[["A", "B", "C"]].sum(axis=1), 1, atol=1e-8)
        capped = weights[weights["strategy"] == "Capped minimum volatility"]
        self.assertTrue((capped[["A", "B", "C"]] <= .4 + 1e-7).all().all())
        self.assertEqual(study["net_returns"].index[0], data.index[63])
        self.assertEqual(study["net_returns"].index[-1], data.index[-1])

    def test_future_changes_cannot_change_earlier_targets(self):
        data = self.sample()
        before = walk_forward_study(data, lookback=63, max_weight=.4)
        changed = data.copy()
        changed.iloc[100:] = changed.iloc[100:] * 3 + .02
        after = walk_forward_study(changed, lookback=63, max_weight=.4)
        def early(study):
            weights = study["target_weights"]
            return weights[weights["Date"] <= data.index[100]].reset_index(drop=True)
        pd.testing.assert_frame_equal(early(before), early(after))

    def test_costs_reduce_wealth_without_changing_targets(self):
        free = walk_forward_study(self.sample(), lookback=63, max_weight=.4, cost_bps=0)
        paid = walk_forward_study(self.sample(), lookback=63, max_weight=.4, cost_bps=25)
        pd.testing.assert_frame_equal(free["target_weights"], paid["target_weights"])
        pd.testing.assert_frame_equal(free["gross_returns"], free["net_returns"])
        self.assertTrue((paid["growth"].iloc[-1] < free["growth"].iloc[-1]).all())
        first_trade = paid["trades"].groupby("strategy").first()
        np.testing.assert_allclose(first_trade["traded_fraction"], 1)
        np.testing.assert_allclose(first_trade["cost_fraction"], .0025)

    def test_drift_is_not_accidentally_daily_rebalanced(self):
        data = pd.DataFrame({"A": [0, 0, .1, .1, 0, 0], "B": [0, 0, 0, 0, 0, 0]},
                            index=pd.bdate_range("2026-01-01", periods=6))
        study = walk_forward_study(data, lookback=2, rebalance_every=2, max_weight=.5, cost_bps=0)
        equal = study["gross_returns"]["Equal weight"]
        self.assertAlmostEqual(equal.iloc[0], .05)
        self.assertAlmostEqual(equal.iloc[1], (.55 / 1.05) * .1)
        # After the two gains, weights are 1.21/2.21 and 1/2.21.
        trades = study["trades"].query("strategy == 'Equal weight'")
        self.assertAlmostEqual(trades.iloc[1]["traded_fraction"], 2 * (1.21 / 2.21 - .5))

    def test_paired_interval_zero_and_constant_difference(self):
        self.assertEqual(paired_block_interval(pd.Series(np.zeros(50))), (0, 0))
        low, high = paired_block_interval(pd.Series(np.repeat(.001, 50)))
        self.assertAlmostEqual(low, .252)
        self.assertAlmostEqual(high, .252)
        self.assertTrue(all(np.isnan(x) for x in paired_block_interval(pd.Series(np.zeros(21)), block_size=21)))

    def test_infeasible_and_insufficient_data_fail(self):
        for args in [{"max_weight": .2}, {"lookback": 252}, {"cost_bps": -1}, {"rebalance_every": 0}]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                walk_forward_study(self.sample(), **args)


if __name__ == "__main__":
    unittest.main()
