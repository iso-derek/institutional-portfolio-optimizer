"""Validate a point-in-time universe and confirmatory protocol without revealing data."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from confirmatory import ConfirmatoryProtocol, UniverseManifest, validate_protocol_binding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("universe", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--allow-template", action="store_true")
    args = parser.parse_args()
    universe = UniverseManifest.from_mapping(json.loads(args.universe.read_text(encoding="utf-8")),
                                             require_verified=not args.allow_template)
    protocol = ConfirmatoryProtocol.from_mapping(json.loads(args.protocol.read_text(encoding="utf-8")))
    validate_protocol_binding(protocol, universe)
    print(json.dumps({"universe_sha256": universe.sha256, "status": protocol.status,
                      "holdout_start": str(protocol.holdout_start), "holdout_end": str(protocol.holdout_end)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
