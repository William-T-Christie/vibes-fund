"""Command line entry points used by the GitHub workflows.

    vibes morning-prepare   (Alpaca keys)
    vibes morning-decide    (Claude token)
    vibes morning-trade     (Alpaca keys)
    vibes evening           (Alpaca keys)
    vibes healthcheck       (Claude token)
    vibes scrub
    vibes replay --name NAME [--days 100] [--end DATE] [--start DATE]   (Alpaca keys + Claude; private)
    vibes reset --confirm   (dry run only; refuses once the fund is live)
    vibes go-live --confirm
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys

from . import config, decide, morning, record, scrub, store


def _out(obj) -> None:
    print(json.dumps(obj, indent=1, default=str))


def _github_output(key: str, value: str) -> None:
    import os
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="vibes")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("morning-prepare", "morning-decide", "morning-trade", "evening", "healthcheck", "scrub"):
        sub.add_parser(name)
    rp = sub.add_parser("replay", help="Private replay of past days (results stay in .replays/, never published)")
    rp.add_argument("--name", required=True, help="folder under .replays/; rerun the same name to resume")
    rp.add_argument("--days", type=int, default=100)
    rp.add_argument("--end", help="last day to replay (default: yesterday)")
    rp.add_argument("--start", help="first day to replay (overrides counting back from --end)")
    for name in ("reset", "go-live"):
        sp = sub.add_parser(name)
        sp.add_argument("--confirm", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "morning-prepare":
        from .alpaca import Alpaca
        r = morning.prepare(Alpaca())
        _out({k: v for k, v in r.items() if k not in ("headlines", "book")})
        _github_output("proceed", "true" if r.get("proceed") else "false")
        return 0
    if a.cmd == "morning-decide":
        r = morning.decide()
        _out({k: v for k, v in r.items() if k not in ("headlines", "book")})
        _github_output("proceed", "true" if r.get("proceed") else "false")
        return 0
    if a.cmd == "morning-trade":
        from .alpaca import Alpaca
        _out(morning.run_trades(Alpaca()))
        return 0
    if a.cmd == "evening":
        from .alpaca import Alpaca
        _out(record.run(Alpaca()))
        return 0
    if a.cmd == "healthcheck":
        raw = decide.call_claude('Reply with only this JSON: {"mood": {"label": "fine", "score": 0}, '
                                 '"summary": "ok", "trades": []}')
        decide.parse(raw)
        print("healthcheck: Claude token works")
        return 0
    if a.cmd == "replay":
        from .alpaca import Alpaca
        from . import replay
        rep = replay.run(Alpaca(), name=a.name, days=a.days, end=a.end, start=a.start)
        print(f"\nReport: {replay.replays_dir() / a.name / 'report.md'}")
        b = rep["behavior"]
        print(f"Average cash {b['avg_cash_pct']}%, {b['trades_filled']} trades filled, {b['declined']} declined.")
        return 0
    if a.cmd == "scrub":
        return scrub.main()
    if a.cmd == "reset":
        state = store.fund_state()
        if state.get("mode") == "live":
            print("Refusing: the fund is live. One fund, one inception date, never reset.", file=sys.stderr)
            return 2
        if not a.confirm:
            print("Dry run reset wipes data/vibes. Re-run with --confirm.", file=sys.stderr)
            return 2
        shutil.rmtree(config.DATA_DIR, ignore_errors=True)
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        (config.LOGS_DIR / ".gitkeep").touch()
        print("Dry run data wiped. Reset the Alpaca paper account to $100,000 in its dashboard too.")
        return 0
    if a.cmd == "go-live":
        state = store.fund_state()
        if state.get("inception") or any(config.LOGS_DIR.glob("20*")):
            print("Refusing: dry run data is still present. Run `vibes reset --confirm` first.", file=sys.stderr)
            return 2
        if not a.confirm:
            print("Go live marks the fund live; the next fill sets inception day. Re-run with --confirm.",
                  file=sys.stderr)
            return 2
        state["mode"] = "live"
        store.save_fund_state(state)
        print("The fund is live. The next filled trade sets inception day.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
