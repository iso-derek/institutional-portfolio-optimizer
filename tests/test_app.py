"""Exercise the real Streamlit page with deterministic offline market data."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import streamlit as st
from streamlit.testing.v1 import AppTest
from data_generation import generate_synthetic_prices


def offline_prices(tickers, start=None, end=None, save_path=None):
    assert save_path is None, "Dashboard must not overwrite checked-in prices."
    frame = generate_synthetic_prices(list(tickers), "2026-01-01", "2026-05-01")
    frame.attrs.update(source="synthetic", synthetic=True, price_basis="fictional prices", fallback_reason="Offline UI test")
    return frame


class DashboardTests(unittest.TestCase):
    def test_workflow_and_empty_input(self):
        st.cache_data.clear()
        with patch("data_generation.fetch_price_data", side_effect=offline_prices):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual([tab.label for tab in app.tabs], ["Performance", "Risk", "Diversification", "Optimisation", "Research lab", "Stress lab", "Learning guide", "Data"])
            self.assertTrue(any("SYNTHETIC DEMONSTRATION" in warning.value for warning in app.warning))
            next(widget for widget in app.selectbox if widget.label == "One-day tail confidence").set_value(.99).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("99.0%" in metric.label for metric in app.metric))
            next(widget for widget in app.selectbox if widget.label == "Allocation method").set_value("Minimum Volatility").run()
            self.assertEqual(len(app.exception), 0)
            next(widget for widget in app.selectbox if widget.label == "Training observations").set_value(63)
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("research_run", app.session_state)
            self.assertGreater(len(app.session_state["research_run"]["result"]["net_returns"]), 0)
            app.text_input[1].set_value("").run()
            self.assertEqual(len(app.exception), 0)
            beta = next(metric for metric in app.metric if metric.label == "Beta vs benchmark")
            self.assertEqual(beta.value, "N/A")
            app.text_input[0].set_value("").run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("Enter between", app.error[0].value)


if __name__ == "__main__":
    unittest.main()
