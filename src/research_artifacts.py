"""Frozen research-input artifacts with integrity and provenance checks."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def provenance_path_for(price_path: Path) -> Path:
    return Path(price_path).with_suffix(".provenance.json")


def write_frozen_prices(prices: pd.DataFrame, path: Path, source: dict[str, object]) -> dict[str, object]:
    """Write canonical prices plus a sidecar that identifies the exact bytes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frozen = prices.copy().sort_index()
    frozen.index = pd.to_datetime(frozen.index)
    frozen.index.name = "Date"
    frozen.to_csv(path, date_format="%Y-%m-%d", float_format="%.17g")
    metadata = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": dict(source),
        "frozen_artifact": {
            "path": path.name,
            "sha256": file_sha256(path),
            "rows": int(len(frozen)),
            "columns": list(frozen.columns),
            "first_observation": str(frozen.index.min().date()),
            "last_observation": str(frozen.index.max().date()),
        },
        "limitations": [
            "The hash verifies these frozen bytes; it does not independently certify vendor accuracy or adjustment methodology.",
            "Provider terms and redistribution rights must be checked before sharing the frozen input.",
            "The fixed universe can contain survivorship and availability bias.",
        ],
    }
    provenance_path_for(path).write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    return metadata


def load_frozen_prices(
    path: Path,
    provenance_path: Path | None = None,
    *,
    require_real: bool = False,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load only when the sidecar and the exact CSV bytes agree."""
    path = Path(path)
    sidecar = Path(provenance_path) if provenance_path else provenance_path_for(path)
    if not path.is_file() or not sidecar.is_file():
        raise ValueError("Frozen prices require both the CSV and its provenance sidecar.")
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    expected = metadata.get("frozen_artifact", {}).get("sha256")
    actual = file_sha256(path)
    if not expected or actual != expected:
        raise ValueError("Frozen price hash does not match the provenance sidecar.")
    source = metadata.get("source", {})
    if require_real and source.get("synthetic") is not False:
        raise ValueError("This study requires a provenance-confirmed non-synthetic input.")
    prices = pd.read_csv(
        path,
        index_col="Date",
        parse_dates=True,
        dtype=float,
        float_precision="round_trip",
    )
    artifact = metadata["frozen_artifact"]
    if len(prices) != artifact.get("rows") or list(prices.columns) != artifact.get("columns"):
        raise ValueError("Frozen price shape does not match the provenance sidecar.")
    prices.attrs.update(source)
    return prices, metadata
