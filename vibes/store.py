"""Reading and writing the JSON files the site reads, plus the per-day logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config


def _path(name: str) -> Path:
    return config.DATA_DIR / name


def read(name: str, default: Any = None) -> Any:
    p = _path(name)
    if not p.exists():
        return default
    return json.loads(p.read_text())


def write(name: str, data: Any) -> Path:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=False) + "\n")
    return p


def log_dir(day: str) -> Path:
    d = config.LOGS_DIR / day
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_log(day: str, name: str, data: Any) -> Path:
    p = log_dir(day) / name
    if isinstance(data, str):
        p.write_text(data)
    else:
        p.write_text(json.dumps(data, indent=1) + "\n")
    return p


def read_log(day: str, name: str, default: Any = None) -> Any:
    p = config.LOGS_DIR / day / name
    if not p.exists():
        return default
    return json.loads(p.read_text())


def write_work(name: str, data: Any) -> Path:
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    p = config.WORK_DIR / name
    p.write_text(json.dumps(data, indent=1) + "\n")
    return p


def read_work(name: str) -> Any:
    return json.loads((config.WORK_DIR / name).read_text())


def fund_state() -> dict:
    """fund.json: mode (dry_run or live), inception date, running honesty adjustments."""
    return read(
        "fund.json",
        {
            "mode": "dry_run",
            "inception": None,
            "slippage_reserve_total": 0.0,
            "dividends_credited_total": 0.0,
            "dividends_credited": [],
            "spy_dividends": [],
            "paused_names": [],
        },
    )


def save_fund_state(state: dict) -> None:
    write("fund.json", state)
