"""Run the fixed allocation study from synthetic, live, or frozen prices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_generation import fetch_price_data, generate_synthetic_prices  # noqa: E402
from preprocessing import calculate_returns  # noqa: E402
from research import paired_block_interval, walk_forward_study  # noqa: E402
from research_artifacts import load_frozen_prices, write_frozen_prices  # noqa: E402


ASSETS = ["SPY", "IEF", "GLD"]
START = "2018-01-01"
END_EXCLUSIVE = "2026-01-01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--live", action="store_true", help="Fetch complete real adjusted prices; never substitute synthetic data.")
    source.add_argument("--input", type=Path, help="Replay a frozen CSV after verifying its provenance sidecar.")
    parser.add_argument("--provenance", type=Path, help="Sidecar for --input; defaults to <input>.provenance.json.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    return parser.parse_args()


def acquire_prices(args: argparse.Namespace):
    if args.input:
        return load_frozen_prices(args.input, args.provenance, require_real=True)
    if args.live:
        prices = fetch_price_data(
            ASSETS,
            START,
            END_EXCLUSIVE,
            save_path=None,
            allow_synthetic_fallback=False,
        )
        missing = sorted(set(ASSETS) - set(prices.columns))
        if prices.attrs.get("synthetic") is not False or missing:
            raise SystemExit(f"Complete real adjusted-price data unavailable; missing={missing}.")
        return prices, None
    prices = generate_synthetic_prices(ASSETS, START, "2025-12-31")
    prices.attrs.update(
        source="synthetic",
        synthetic=True,
        seed=42,
        price_basis="fictional prices",
        requested_tickers=ASSETS,
        usage_note="Deterministic demonstration only; not evidence about actual markets.",
    )
    return prices, None


def main() -> int:
    args = parse_args()
    prices, input_provenance = acquire_prices(args)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    if args.input:
        provenance = input_provenance
    else:
        frozen_path = output / "study_prices.csv"
        provenance = write_frozen_prices(prices, frozen_path, prices.attrs)
        prices, provenance = load_frozen_prices(
            frozen_path,
            require_real=prices.attrs.get("synthetic") is False,
        )

    returns = calculate_returns(prices)
    study = walk_forward_study(returns, extended=True)
    for key in ["summary", "net_returns", "trades", "target_weights"]:
        study[key].to_csv(output / f"{key}.csv")
    difference = (study["net_returns"]["Volatility-adaptive risk parity"]
                  - study["net_returns"]["Static defensive risk parity"])
    metadata = {
        "schema_version": 2,
        "settings": study["settings"],
        "input_provenance": provenance,
        "replayed_from": str(args.input) if args.input else None,
        "verified_replay_input": input_provenance is not None,
        "adaptive_vs_static_annual_mean": float(difference.mean() * 252),
        "adaptive_vs_static_block_ci": paired_block_interval(difference),
        "failures": study["failures"],
        "interpretation": "Exploratory historical comparison, not a forecast or evidence of a tradable edge.",
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(study["summary"].to_string())
    print(json.dumps(metadata, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
