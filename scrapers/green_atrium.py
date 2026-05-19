"""Fetch Green Atrium pricelist API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scrapers._common import client, load_sources, rate_sleep, raw_path, save_json


def fetch_green_atrium(include_duplex: bool = True) -> dict[str, Any]:
    cfg = load_sources()
    ga = cfg["green_atrium"]
    fetched_at = datetime.now(timezone.utc).isoformat()

    with client(cfg) as http:
        r = http.get(ga["pricelist_url"])
        r.raise_for_status()
        pricelist = r.json()
        if not pricelist.get("success"):
            raise RuntimeError("Green Atrium pricelist API returned success=false")

        duplex = None
        if include_duplex:
            rate_sleep(cfg)
            rd = http.get(ga["duplex_pricelist_url"])
            if rd.status_code == 200:
                duplex = rd.json()

    flats = pricelist.get("flats") or []
    duplex_flats = []
    if isinstance(duplex, dict) and duplex.get("success"):
        duplex_flats = duplex.get("flats") or []

    payload = {
        "source": "green_atrium",
        "fetched_at": fetched_at,
        "pricelist_url": ga["pricelist_url"],
        "flats": flats,
        "duplex_flats": duplex_flats,
        "units_count": len(flats) + len(duplex_flats),
    }
    path = raw_path("green_atrium")
    save_json(path, payload)
    return {"path": str(path), "units_count": payload["units_count"], "payload": payload}
