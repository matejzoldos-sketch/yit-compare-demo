"""Fetch Bory Bývanie apartments via public API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scrapers._common import client, load_sources, raw_path, save_json


def fetch_bory() -> dict[str, Any]:
    cfg = load_sources()
    bory = cfg["bory"]
    fetched_at = datetime.now(timezone.utc).isoformat()

    with client(cfg) as http:
        r = http.get(bory["api_url"])
        r.raise_for_status()
        body = r.json()

    flats = body.get("data") if isinstance(body, dict) else body
    if not isinstance(flats, list):
        raise RuntimeError("Bory API: unexpected response shape (expected data array)")

    payload = {
        "source": "bory",
        "fetched_at": fetched_at,
        "api_url": bory["api_url"],
        "flats": flats,
        "units_count": len(flats),
    }
    path = raw_path("bory")
    save_json(path, payload)
    return {"path": str(path), "units_count": len(flats), "payload": payload}
