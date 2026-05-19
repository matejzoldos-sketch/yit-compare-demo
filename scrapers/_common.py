"""Shared HTTP and config helpers."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

from yit_paths import CONFIG_DIR, RAW_DIR


def load_sources() -> dict[str, Any]:
    with (CONFIG_DIR / "sources.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manual_projects() -> dict[str, Any]:
    path = CONFIG_DIR / "projects_manual.yaml"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def raw_path(source: str, suffix: str = "json") -> Path:
    dest = RAW_DIR / source
    dest.mkdir(parents=True, exist_ok=True)
    return dest / f"{timestamp_slug()}.{suffix}"


def save_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def client(cfg: dict[str, Any]) -> httpx.Client:
    return httpx.Client(
        timeout=60.0,
        headers={"User-Agent": cfg.get("user_agent", "yit-comparison-local/1.0")},
        follow_redirects=True,
    )


def rate_sleep(cfg: dict[str, Any]) -> None:
    time.sleep(float(cfg.get("rate_limit_seconds", 1)))
