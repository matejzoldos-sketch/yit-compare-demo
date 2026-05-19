"""Fetch Slnečnice apartments via public API (paginated)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from scrapers._common import client, load_sources, rate_sleep, raw_path, save_json

PAGE_SIZE = 15


def _fetch_page(http: Any, base_url: str, params: dict[str, Any], page: int) -> dict[str, Any]:
    q = {**params, "page": page}
    url = f"{base_url}?{urlencode(q, doseq=True)}"
    r = http.get(url)
    r.raise_for_status()
    return r.json()


def fetch_slnecnice() -> dict[str, Any]:
    cfg = load_sources()
    sln = cfg["slnecnice_viladomy"]
    fetched_at = datetime.now(timezone.utc).isoformat()
    base_url = sln["api_url"]
    params: dict[str, Any] = {"project": sln["api_project"]}

    all_flats: list[dict[str, Any]] = []
    total_count: int | None = None

    with client(cfg) as http:
        page = 1
        while True:
            body = _fetch_page(http, base_url, params, page)
            batch = body.get("data") or []
            if not isinstance(batch, list):
                raise RuntimeError("Slnečnice API: unexpected data shape")

            if total_count is None:
                try:
                    total_count = int(body.get("count") or 0)
                except (TypeError, ValueError):
                    total_count = 0

            all_flats.extend(batch)
            if not batch or len(all_flats) >= total_count:
                break
            page += 1
            rate_sleep(cfg)

    payload = {
        "source": "slnecnice_viladomy",
        "fetched_at": fetched_at,
        "api_url": base_url,
        "api_project": sln["api_project"],
        "flats": all_flats,
        "units_count": len(all_flats),
        "api_reported_count": total_count,
    }
    path = raw_path("slnecnice_viladomy")
    save_json(path, payload)
    return {"path": str(path), "units_count": len(all_flats), "payload": payload}
