"""Fetch YIT NUPPU apartments via productsearch API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scrapers._common import client, load_sources, rate_sleep, raw_path, save_json


def _base_query(yit: dict[str, Any]) -> dict[str, Any]:
    return {
        "QueryString": "*",
        "UILanguage": yit.get("ui_language", "sk"),
        "PageSize": int(yit.get("page_size", 500)),
        "StartPage": 0,
        "PageId": int(yit["page_id"]),
        "BlockId": 0,
        "SiteId": yit["site_id"],
        "Attrs": [],
        "Fields": None,
        "ProjectOrderMode": 0,
        "Filter": {
            "Field": "Locale",
            "Value": "sk",
            "Operator": "Equals",
            "AndConditions": [
                {
                    "Field": "AreaIds",
                    "Value": yit["area_ids"],
                    "Operator": "Any",
                    "AndConditions": [],
                    "OrConditions": [],
                },
                {
                    "Field": "BuildingTypeKey",
                    "Value": ["BlockOfFlats"],
                    "Operator": "In",
                    "AndConditions": [],
                    "OrConditions": [],
                },
            ],
            "OrConditions": [],
        },
        "CacheMaxAge": 0,
    }


def fetch_yit_nuppu() -> dict[str, Any]:
    cfg = load_sources()
    yit = cfg["yit_nuppu"]
    fetched_at = datetime.now(timezone.utc).isoformat()
    all_hits: list[dict[str, Any]] = []
    start_page = 0
    total_hits = 0
    pages: list[dict[str, Any]] = []

    with client(cfg) as http:
        while True:
            body = _base_query(yit)
            body["StartPage"] = start_page
            r = http.post(yit["api_url"], json=body)
            r.raise_for_status()
            page = r.json()
            pages.append(page)
            hits = page.get("Hits") or []
            all_hits.extend(hits)
            total_hits = int(page.get("TotalHits") or 0)
            if not page.get("IsMoreAvailable"):
                break
            start_page += 1
            rate_sleep(cfg)

    if total_hits and len(all_hits) == 0:
        raise RuntimeError("YIT API reported hits but returned empty Hits array")
    if total_hits == 0:
        raise RuntimeError(
            "YIT API returned 0 apartments — check PageId/AreaIds in config/sources.yaml"
        )

    payload = {
        "source": "yit_nuppu",
        "fetched_at": fetched_at,
        "api_url": yit["api_url"],
        "query": _base_query(yit),
        "total_hits": total_hits,
        "hits": all_hits,
        "units_count": len(all_hits),
        "pages_fetched": len(pages),
    }
    path = raw_path("yit_nuppu")
    save_json(path, payload)
    return {"path": str(path), "units_count": len(all_hits), "payload": payload}
