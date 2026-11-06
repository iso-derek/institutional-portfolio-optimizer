import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from confirmatory import ConfirmatoryProtocol, UniverseManifest, split_confirmatory_prices, validate_protocol_binding


def universe_payload(verified=True):
    return {"manifest_version": 1, "as_of_date": "2024-12-31", "symbols": ["AAA", "BBB"],
            "membership_source": "archived fixture", "selection_rule": "members on the stated date",
            "point_in_time_verified": verified}


def protocol_payload(status="locked", universe_sha256="0" * 64):
    return {"protocol_version": 1, "status": status, "locked_at": "2024-12-30T12:00:00Z",
            "development_end": "2024-12-31", "holdout_start": "2025-01-01", "holdout_end": "2025-01-03",
            "universe_sha256": universe_sha256, "parameters": {"lookback": 126, "rebalance_every": 21},
            "primary_outcomes": ["net_volatility", "maximum_drawdown"]}


class ConfirmatoryControlsTests(unittest.TestCase):
    def test_unverified_or_duplicate_universe_is_rejected(self):
        with self.assertRaises(ValueError):
            UniverseManifest.from_mapping(universe_payload(False))
        payload = universe_payload()
        payload["symbols"] = ["AAA", "aaa"]
        with self.assertRaises(ValueError):
            UniverseManifest.from_mapping(payload)

    def test_protocol_must_precede_holdout_and_bind_universe(self):
        universe = UniverseManifest.from_mapping(universe_payload())
        protocol = ConfirmatoryProtocol.from_mapping(protocol_payload(universe_sha256=universe.sha256))
        validate_protocol_binding(protocol, universe)
        bad = protocol_payload(universe.sha256)
        bad["locked_at"] = "2025-01-02T00:00:00Z"
        with self.assertRaises(ValueError):
            ConfirmatoryProtocol.from_mapping(bad)

    def test_holdout_is_sealed_until_explicit_unblinding(self):
        prices = pd.DataFrame({"AAA": [1, 2, 3, 4], "BBB": [2, 3, 4, 5]},
                              index=pd.to_datetime(["2024-12-30", "2024-12-31", "2025-01-01", "2025-01-02"]))
        locked = ConfirmatoryProtocol.from_mapping(protocol_payload())
        development, holdout = split_confirmatory_prices(prices, locked)
        self.assertIsNone(holdout)
        self.assertEqual(development.index.max(), pd.Timestamp("2024-12-31"))
        with self.assertRaises(PermissionError):
            split_confirmatory_prices(prices, locked, reveal_holdout=True)
        unblinded = ConfirmatoryProtocol.from_mapping(protocol_payload(status="unblinded"))
        _, revealed = split_confirmatory_prices(prices, unblinded, reveal_holdout=True)
        self.assertEqual(list(revealed.index), [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-02")])


if __name__ == "__main__":
    unittest.main()
