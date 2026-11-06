"""Integrity checks for frozen research inputs."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from research_artifacts import load_frozen_prices, write_frozen_prices


class ResearchArtifactTests(unittest.TestCase):
    def setUp(self):
        self.prices = pd.DataFrame(
            {
                "SPY": [100.12345678901234, 101.98765432109876],
                "IEF": [99.11111111111111, 98.55555555555556],
            },
            index=pd.to_datetime(["2025-01-02", "2025-01-03"]),
        )

    def test_round_trip_verifies_exact_frozen_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            metadata = write_frozen_prices(self.prices, path, {"source": "fixture", "synthetic": False})
            loaded, verified = load_frozen_prices(path, require_real=True)
            expected = self.prices.copy()
            expected.index.name = "Date"
            pd.testing.assert_frame_equal(loaded, expected, check_freq=False)
            self.assertEqual(verified["frozen_artifact"]["sha256"], metadata["frozen_artifact"]["sha256"])

    def test_tampered_frozen_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            write_frozen_prices(self.prices, path, {"source": "fixture", "synthetic": False})
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                load_frozen_prices(path, require_real=True)

    def test_synthetic_input_cannot_masquerade_as_real_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            write_frozen_prices(self.prices, path, {"source": "synthetic", "synthetic": True})
            with self.assertRaisesRegex(ValueError, "non-synthetic"):
                load_frozen_prices(path, require_real=True)


if __name__ == "__main__":
    unittest.main()
