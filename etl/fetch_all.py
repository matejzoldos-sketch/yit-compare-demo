"""Fetch all sources, normalize into SQLite."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from etl.normalize import (
    connect_db,
    normalize_bory,
    normalize_green_atrium,
    normalize_slnecnice,
    normalize_yit,
    record_fetch_run,
)
from scrapers.bory import fetch_bory
from scrapers.green_atrium import fetch_green_atrium
from scrapers.slnecnice import fetch_slnecnice
from scrapers.yit_nuppu import fetch_yit_nuppu


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    conn = connect_db()
    try:
        print("Fetching Green Atrium…")
        ga = fetch_green_atrium()
        print(f"  saved {ga['path']} ({ga['units_count']} units)")
        n_ga = normalize_green_atrium(conn, ga["payload"])
        record_fetch_run(conn, "green_atrium", ga["path"], n_ga, started, True)
        print(f"  normalized {n_ga} units")

        print("Fetching YIT NUPPU…")
        yit = fetch_yit_nuppu()
        print(f"  saved {yit['path']} ({yit['units_count']} units)")
        n_yit = normalize_yit(conn, yit["payload"])
        record_fetch_run(conn, "yit_nuppu", yit["path"], n_yit, started, True)
        print(f"  normalized {n_yit} units")

        print("Fetching Bory…")
        bory = fetch_bory()
        print(f"  saved {bory['path']} ({bory['units_count']} units)")
        n_bory = normalize_bory(conn, bory["payload"])
        record_fetch_run(conn, "bory", bory["path"], n_bory, started, True)
        print(f"  normalized {n_bory} units")

        print("Fetching Slnečnice Nové viladomy…")
        sln = fetch_slnecnice()
        print(f"  saved {sln['path']} ({sln['units_count']} units)")
        n_sln = normalize_slnecnice(conn, sln["payload"])
        record_fetch_run(conn, "slnecnice_viladomy", sln["path"], n_sln, started, True)
        print(f"  normalized {n_sln} units")

        conn.commit()
        print("Done.")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
