"""Contract tests for the JSON API behind the Portfolio Lab web app (demo data only)."""
import unittest

from fastapi.testclient import TestClient

from api.main import app


class PortfolioApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_analysis_weights_and_attribution_reconcile(self):
        data = self.get("/api/analysis")
        self.assertTrue(data["sample"]["synthetic"])
        self.assertAlmostEqual(sum(w["weight"] for w in data["weights"]), 1.0, places=9)
        contributions = sum(row["contribution"] for row in data["attribution"])
        self.assertAlmostEqual(contributions, data["kpis"]["total_return"], places=9)
        self.assertLessEqual(len(data["growth"]), 402)
        self.assertEqual(data["growth"][-1]["date"], data["sample"]["end"])

    def test_every_method_returns_valid_weights(self):
        for method in ["equal", "max_sharpe", "min_vol", "tilt"]:
            with self.subTest(method=method):
                weights = self.get(f"/api/analysis?method={method}")["weights"]
                self.assertAlmostEqual(sum(w["weight"] for w in weights), 1.0, places=6)
                self.assertTrue(all(w["weight"] >= -1e-9 for w in weights))

    def test_missing_benchmark_hides_benchmark_figures(self):
        data = self.get("/api/analysis?benchmark=")
        self.assertIsNone(data["kpis"]["beta"])
        self.assertIsNone(data["rolling"])

    def test_invalid_settings_are_rejected_with_plain_messages(self):
        self.assertEqual(self.client.get("/api/analysis?tickers=").status_code, 400)
        self.assertEqual(self.client.get("/api/analysis?start=2026-01-01&end=2025-01-01").status_code, 400)
        self.assertEqual(self.client.get("/api/analysis?method=magic").status_code, 422)

    def test_optimise_returns_frontier_and_three_allocations(self):
        data = self.get("/api/optimise")
        returns = [point["return"] for point in data["frontier"]]
        self.assertEqual(returns, sorted(returns))
        self.assertEqual({row["key"] for row in data["allocations"]}, {"equal", "max_sharpe", "min_vol"})

    def test_stress_with_no_shocks_changes_nothing(self):
        body = {"exposures": [], "equity_shock": 0, "yield_shift_bps": 0, "fx_shock": 0, "inflation": 0, "other_shock": 0}
        response = self.client.post("/api/stress", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertAlmostEqual(response.json()["pnl"], 0.0, places=9)

    def test_research_runs_walk_forward_study(self):
        response = self.client.post("/api/research", json={"extended": False, "rebalance_every": 63})
        self.assertEqual(response.status_code, 200, response.text)
        names = [row["name"] for row in response.json()["strategies"]]
        self.assertEqual(names[0], "Equal weight")


if __name__ == "__main__":
    unittest.main()
