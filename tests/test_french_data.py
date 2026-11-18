"""Parser tests for the Kenneth R. French Data Library loader (no network needed)."""
import io
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import french_data  # noqa: E402

INDUSTRY_TEXT = """This file was created using the 202609 CRSP database.

  Average Value Weighted Returns -- Daily
,NoDur,Durbl,Manuf,Enrgy,Chems,BusEq,Telcm,Utils,Shops,Hlth,Money,Other
20260928,   1.00,   0.00,   0.00,   2.00,   0.00,   0.00,   0.00,   0.00,   0.00,   0.00,   0.00,   0.00
20260929,  -1.00,   0.00,   0.00,   1.00,   0.00,   0.00,   0.00,   0.00,   0.00,-99.99,   0.00,   0.00

  Average Equal Weighted Returns -- Daily
,NoDur,Durbl,Manuf,Enrgy,Chems,BusEq,Telcm,Utils,Shops,Hlth,Money,Other
20260928,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00,   9.00
"""
FACTOR_TEXT = """The Tbill return is the simple daily rate.

,Mkt-RF,SMB,HML,RF
20260928,    0.50,    0.00,    0.00,    0.01
20260929,   -0.20,    0.00,    0.00,    0.01

Copyright 2026 Eugene F. Fama and Kenneth R. French
"""


def zipped(name: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


def fake_download(name: str) -> bytes:
    return zipped("industry.csv", INDUSTRY_TEXT) if name == french_data.INDUSTRY_FILE else zipped("factors.csv", FACTOR_TEXT)


class FrenchDataTests(unittest.TestCase):
    def test_reads_only_the_value_weighted_block_and_builds_the_market(self):
        with mock.patch.object(french_data, "_download", side_effect=fake_download):
            returns = french_data.daily_returns()
        self.assertEqual(len(returns), 2)                      # equal-weighted block ignored
        self.assertAlmostEqual(returns.loc["2026-09-28", "ENRGY"], 0.02)
        self.assertAlmostEqual(returns.loc["2026-09-28", "MARKET"], 0.0051)  # Mkt-RF + RF
        self.assertTrue(returns.loc["2026-09-29", "HLTH"] != returns.loc["2026-09-29", "HLTH"])  # -99.99 → missing

    def test_price_index_and_provenance(self):
        with mock.patch.object(french_data, "_download", side_effect=fake_download):
            prices = french_data.fetch_industry_prices(["ENRGY", "MARKET", "NOPE"], "2026-09-01", "2026-09-30")
        self.assertAlmostEqual(prices.ENRGY.iloc[-1], 100 * 1.02 * 1.01)
        self.assertEqual(prices.attrs["unavailable_tickers"], ["NOPE"])
        self.assertFalse(prices.attrs["synthetic"])
        self.assertIn("French", prices.attrs["citation"])

    def test_dates_outside_the_library_are_explained(self):
        with mock.patch.object(french_data, "_download", side_effect=fake_download):
            with self.assertRaisesRegex(ValueError, "covers July 1926"):
                french_data.fetch_industry_prices(["ENRGY"], "1900-01-01", "1901-01-01")


if __name__ == "__main__":
    unittest.main()
