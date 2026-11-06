import ast
from pathlib import Path
import unittest


APP_PATH = Path(__file__).parents[1] / "app.py"
DISPLAY_METHODS = {
    "area_chart",
    "audio",
    "bar_chart",
    "data_editor",
    "dataframe",
    "echarts_chart",
    "iframe",
    "image",
    "line_chart",
    "pdf",
    "plotly_chart",
    "pyplot",
    "scatter_chart",
    "table",
    "vega_lite_chart",
    "video",
}


class AccessibilityContractTests(unittest.TestCase):
    def test_every_visual_and_grid_has_an_accessible_name(self):
        tree = ast.parse(APP_PATH.read_text(encoding="utf-8"), filename=str(APP_PATH))
        missing = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in DISPLAY_METHODS:
                continue
            if not any(keyword.arg == "alt" for keyword in node.keywords):
                missing.append(f"{node.func.attr} at line {node.lineno}")

        self.assertEqual([], missing, "Missing alt= accessible names: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
