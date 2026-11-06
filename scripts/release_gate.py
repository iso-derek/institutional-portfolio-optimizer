"""Deterministic repository-level release-candidate checks."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md", "SECURITY.md", "CHANGELOG.md", "requirements-tested.txt",
    "docs/CLEAN_INSTALL.md", "docs/CONFIRMATORY_STUDY.md",
    "docs/RELEASE_ACCEPTANCE.md", "docs/VISUAL_ACCEPTANCE.md",
    "research/universe_manifest.template.json",
    "research/confirmatory_protocol.template.json",
)
PINNED_DIRECT_DEPENDENCIES = {
    "numpy", "pandas", "scipy", "scikit-learn", "streamlit", "plotly",
    "yfinance", "python-dateutil",
}


def check_release_files(root: Path = ROOT) -> list[str]:
    errors = [f"missing {name}" for name in REQUIRED_FILES if not (root / name).is_file()]
    requirements_path = root / "requirements-tested.txt"
    if requirements_path.is_file():
        requirements = requirements_path.read_text(encoding="utf-8").splitlines()
        pinned = {line.split("==", 1)[0] for line in requirements if "==" in line and not line.startswith("#")}
        missing_pins = sorted(PINNED_DIRECT_DEPENDENCIES - pinned)
        if missing_pins:
            errors.append("unpinned direct dependencies: " + ", ".join(missing_pins))
    app_path = root / "app.py"
    if app_path.is_file():
        try:
            ast.parse(app_path.read_text(encoding="utf-8"), filename="app.py")
        except SyntaxError as exc:
            errors.append(f"app.py syntax error: {exc}")
    return errors


def main() -> int:
    errors = check_release_files()
    if errors:
        print("Release gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Release gate passed: required evidence exists and direct dependencies are pinned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
