"""Load Meta Ad Library manual insights for the dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from yit_paths import CONFIG_DIR

_META_ADS_PATH = CONFIG_DIR / "meta_ads_insights.yaml"


def load_meta_ads_insights(path: Path | None = None) -> dict[str, Any] | None:
    p = path or _META_ADS_PATH
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return None
    competitors = data.get("competitors") or []
    data["competitors"] = sorted(
        competitors,
        key=lambda c: int(c.get("active_ads_count") or 0),
        reverse=True,
    )
    return data
