"""Point-in-time universe and confirmatory holdout controls.

The module validates research governance. It does not claim that a template
manifest is a verified point-in-time dataset or that a holdout was evaluated.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
from typing import Any, Mapping

import pandas as pd


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class UniverseManifest:
    as_of_date: date
    symbols: tuple[str, ...]
    membership_source: str
    selection_rule: str
    point_in_time_verified: bool
    sha256: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], require_verified: bool = True) -> "UniverseManifest":
        if payload.get("manifest_version") != 1:
            raise ValueError("manifest_version must equal 1")
        symbols = tuple(str(item).strip().upper() for item in payload.get("symbols", []))
        if len(symbols) < 2 or len(set(symbols)) != len(symbols) or any(not item for item in symbols):
            raise ValueError("symbols must contain at least two unique non-empty tickers")
        source = str(payload.get("membership_source", "")).strip()
        rule = str(payload.get("selection_rule", "")).strip()
        if not source or not rule:
            raise ValueError("membership_source and selection_rule are required")
        verified = payload.get("point_in_time_verified") is True
        if require_verified and not verified:
            raise ValueError("confirmatory use requires point_in_time_verified=true")
        return cls(_date(payload.get("as_of_date"), "as_of_date"), symbols, source, rule,
                   verified, canonical_sha256(payload))


@dataclass(frozen=True)
class ConfirmatoryProtocol:
    status: str
    locked_at: datetime | None
    development_end: date
    holdout_start: date
    holdout_end: date
    universe_sha256: str
    parameters: Mapping[str, Any]
    primary_outcomes: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ConfirmatoryProtocol":
        if payload.get("protocol_version") != 1:
            raise ValueError("protocol_version must equal 1")
        status = str(payload.get("status", ""))
        if status not in {"designed", "locked", "unblinded"}:
            raise ValueError("status must be designed, locked, or unblinded")
        development_end = _date(payload.get("development_end"), "development_end")
        holdout_start = _date(payload.get("holdout_start"), "holdout_start")
        holdout_end = _date(payload.get("holdout_end"), "holdout_end")
        if not development_end < holdout_start <= holdout_end:
            raise ValueError("require development_end < holdout_start <= holdout_end")
        locked_at = None if payload.get("locked_at") in {None, ""} else _timestamp(payload["locked_at"], "locked_at")
        if status in {"locked", "unblinded"} and locked_at is None:
            raise ValueError("locked and unblinded protocols require locked_at")
        if locked_at and locked_at.date() > holdout_start:
            raise ValueError("protocol must be locked no later than holdout_start")
        universe_hash = str(payload.get("universe_sha256", ""))
        if status in {"locked", "unblinded"} and len(universe_hash) != 64:
            raise ValueError("locked protocols require a universe_sha256")
        parameters = payload.get("parameters")
        outcomes = tuple(str(item).strip() for item in payload.get("primary_outcomes", []))
        if not isinstance(parameters, dict) or not parameters or not outcomes or any(not item for item in outcomes):
            raise ValueError("parameters and primary_outcomes must be pre-specified")
        return cls(status, locked_at, development_end, holdout_start, holdout_end,
                   universe_hash, parameters, outcomes)


def validate_protocol_binding(protocol: ConfirmatoryProtocol, universe: UniverseManifest) -> None:
    if protocol.status in {"locked", "unblinded"} and protocol.universe_sha256 != universe.sha256:
        raise ValueError("protocol is not bound to this universe manifest")
    if universe.as_of_date > protocol.development_end:
        raise ValueError("universe membership must be known by development_end")


def split_confirmatory_prices(
    prices: pd.DataFrame,
    protocol: ConfirmatoryProtocol,
    *,
    reveal_holdout: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        raise ValueError("prices require a non-empty DatetimeIndex")
    development = prices.loc[: str(protocol.development_end)].copy()
    if development.empty:
        raise ValueError("no development observations are available")
    if not reveal_holdout:
        return development, None
    if protocol.status != "unblinded":
        raise PermissionError("holdout remains sealed until protocol status is unblinded")
    holdout = prices.loc[str(protocol.holdout_start): str(protocol.holdout_end)].copy()
    if holdout.empty:
        raise ValueError("no holdout observations are available")
    return development, holdout
