"""Compute YIT-focused market insights at dashboard build time."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

import yaml

from yit_paths import CONFIG_DIR

OFFER_MODES = {
    "free": ("free",),
    "available": ("free", "reserved"),
    "all": ("free", "reserved", "sold", "in_preparation", "unknown"),
}

OFFER_LABELS_SK = {
    "free": "voľné",
    "available": "voľné a rezervované",
    "all": "všetky stavy",
}


def _load_config() -> dict[str, Any]:
    path = CONFIG_DIR / "insights.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _unit_ppm(unit: dict[str, Any]) -> float | None:
    price = unit.get("price_total_eur") or 0
    area = unit.get("area_interior_m2") or 0
    if price > 0 and area > 0:
        return float(price) / float(area)
    ppm = unit.get("price_per_m2_eur")
    if ppm and float(ppm) > 0:
        return float(ppm)
    return None


def _rooms_value(unit: dict[str, Any]) -> float | None:
    rooms = unit.get("rooms")
    if rooms is None:
        return None
    try:
        return float(rooms)
    except (TypeError, ValueError):
        return None


def _in_segment(unit: dict[str, Any], segment: dict[str, Any]) -> bool:
    rooms = _rooms_value(unit)
    if rooms is None:
        return False
    return float(segment["room_min"]) <= rooms <= float(segment["room_max"])


def _matches_offer(unit: dict[str, Any], offer_mode: str) -> bool:
    allowed = OFFER_MODES.get(offer_mode, OFFER_MODES["free"])
    return (unit.get("status") or "unknown") in allowed


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def _project_names(projects: list[dict[str, Any]]) -> dict[str, str]:
    return {p["slug"]: p["name"] for p in projects}


def project_total_count(
    units: list[dict[str, Any]], slug: str, offer_mode: str
) -> int:
    return sum(
        1
        for u in units
        if u.get("project_slug") == slug and _matches_offer(u, offer_mode)
    )


def segment_stats_for_project(
    units: list[dict[str, Any]],
    slug: str,
    segment: dict[str, Any],
    offer_mode: str,
) -> dict[str, Any]:
    subset = [
        u
        for u in units
        if u.get("project_slug") == slug
        and _matches_offer(u, offer_mode)
        and _in_segment(u, segment)
        and (u.get("price_total_eur") or 0) > 0
    ]
    ppms = [p for p in (_unit_ppm(u) for u in subset) if p is not None and p > 0]
    prices = [float(u["price_total_eur"]) for u in subset if u.get("price_total_eur")]
    areas = [float(u["area_interior_m2"]) for u in subset if u.get("area_interior_m2")]

    return {
        "count": len(subset),
        "median_ppm": round(_median(ppms), 0) if ppms else None,
        "median_price": round(_median(prices), 0) if prices else None,
        "min_price": round(min(prices), 0) if prices else None,
        "max_price": round(max(prices), 0) if prices else None,
        "median_area": round(_median(areas), 1) if areas else None,
    }


def _fmt_eur(n: float | None) -> str:
    if n is None:
        return "—"
    return f"{int(round(n)):,}".replace(",", " ") + " €"


def _fmt_ppm(n: float | None) -> str:
    if n is None:
        return "—"
    return f"{int(round(n)):,}".replace(",", " ") + " €/m²"


def _ppm_advantage_pct(focus_ppm: float, competitor_ppm: float) -> float:
    """Kladné % = NUPPU (focus) je lacnejší na m² oproti konkurentovi."""
    if competitor_ppm <= 0:
        return 0.0
    return ((competitor_ppm - focus_ppm) / competitor_ppm) * 100.0


def _run_rules(
    cfg: dict[str, Any],
    segment: dict[str, Any],
    matrix: dict[str, dict[str, Any]],
    names: dict[str, str],
) -> list[dict[str, Any]]:
    focus = cfg["focus_project"]
    competitors = cfg.get("competitors") or []
    min_focus_ppm = int(cfg.get("min_focus_units_for_ppm", cfg.get("min_units_for_ppm", 3)))
    min_competitor = int(cfg.get("min_competitor_units", 5))
    min_supply = int(cfg.get("min_units_for_supply", 2))
    threshold = float(cfg.get("ppm_threshold_pct", 3.0))
    focus_name = cfg.get("focus_name") or "NUPPU"

    focus_stats = matrix.get(focus) or {}
    items: list[dict[str, Any]] = []

    if focus_stats.get("count", 0) < min_supply:
        return items

    for comp_slug in competitors:
        comp_stats = matrix.get(comp_slug) or {}
        comp_name = names.get(comp_slug, comp_slug)
        seg_label = segment["label"]
        c_cnt = comp_stats.get("count", 0)

        if c_cnt < min_competitor:
            continue

        # €/m² — príležitosť / riziko
        f_ppm = focus_stats.get("median_ppm")
        c_ppm = comp_stats.get("median_ppm")
        if (
            f_ppm is not None
            and c_ppm is not None
            and focus_stats.get("count", 0) >= min_focus_ppm
        ):
            advantage_pct = _ppm_advantage_pct(f_ppm, c_ppm)
            if advantage_pct >= threshold:
                score = min(10, int(advantage_pct / 2) + 3)
                items.append(
                    {
                        "kind": "opportunity",
                        "score": score,
                        "segment_id": segment["id"],
                        "segment_label": seg_label,
                        "competitor_slug": comp_slug,
                        "title": f"Nižší medián €/m² oproti {comp_name} ({seg_label})",
                        "body": (
                            f"{focus_name} má medián {_fmt_ppm(f_ppm)} vs {comp_name} {_fmt_ppm(c_ppm)} "
                            f"(o {advantage_pct:.1f} % nižšie, n={focus_stats['count']} vs {comp_stats['count']})."
                        ),
                    }
                )
            elif advantage_pct <= -threshold:
                disadvantage_pct = abs(advantage_pct)
                score = min(10, int(disadvantage_pct / 2) + 3)
                items.append(
                    {
                        "kind": "risk",
                        "score": score,
                        "segment_id": segment["id"],
                        "segment_label": seg_label,
                        "competitor_slug": comp_slug,
                        "title": f"Vyšší medián €/m² oproti {comp_name} ({seg_label})",
                        "body": (
                            f"{focus_name} {_fmt_ppm(f_ppm)} vs {comp_name} {_fmt_ppm(c_ppm)} "
                            f"(o {disadvantage_pct:.1f} % vyššie, n={focus_stats['count']} vs {comp_stats['count']}). "
                            f"Zvážte argumentáciu hodnotou / financovaním."
                        ),
                    }
                )

        # Vstupná cena
        f_min = focus_stats.get("min_price")
        c_min = comp_stats.get("min_price")
        if (
            f_min is not None
            and c_min is not None
            and focus_stats.get("count", 0) >= min_supply
            and f_min < c_min * 0.98
        ):
            items.append(
                {
                    "kind": "opportunity",
                    "score": 6,
                    "segment_id": segment["id"],
                    "segment_label": seg_label,
                    "competitor_slug": comp_slug,
                    "title": f"Nižšia vstupná cena vs {comp_name} ({seg_label})",
                    "body": (
                        f"Od {_fmt_eur(f_min)} ({focus_name}) vs od {_fmt_eur(c_min)} ({comp_name})."
                    ),
                }
            )

        # Hĺbka ponuky
        f_cnt = focus_stats.get("count", 0)
        if f_cnt >= min_supply:
            if f_cnt >= c_cnt * 1.4 and f_cnt >= 5:
                items.append(
                    {
                        "kind": "opportunity",
                        "score": 5,
                        "segment_id": segment["id"],
                        "segment_label": seg_label,
                        "competitor_slug": comp_slug,
                        "title": f"Väčší výber voľných jednotiek ({seg_label})",
                        "body": (
                            f"{focus_name}: {f_cnt} jednotiek vs {comp_name}: {c_cnt} — lepšia šanca nájsť dispozíciu."
                        ),
                    }
                )
            elif c_cnt >= f_cnt * 1.4 and f_cnt >= 2:
                items.append(
                    {
                        "kind": "risk",
                        "score": 5,
                        "segment_id": segment["id"],
                        "segment_label": seg_label,
                        "competitor_slug": comp_slug,
                        "title": f"Užší výber oproti {comp_name} ({seg_label})",
                        "body": (
                            f"{focus_name}: {f_cnt} vs {comp_name}: {c_cnt} voľných v segmente."
                        ),
                    }
                )

    # Green Atrium — tenká vzorka
    ga = matrix.get("green_atrium") or {}
    if ga.get("count", 0) > 0 and ga.get("count", 0) < min_competitor:
        items.append(
            {
                "kind": "risk",
                "score": 4,
                "segment_id": segment["id"],
                "segment_label": segment["label"],
                "competitor_slug": "green_atrium",
                "title": f"Green Atrium: málo porovnateľných jednotiek ({segment['label']})",
                "body": (
                    f"V API je len {ga['count']} jednotka(y) — porovnanie €/m² môže byť nereprezentatívne."
                ),
            }
        )

    return items


def _total_availability_insights(
    cfg: dict[str, Any],
    units: list[dict[str, Any]],
    names: dict[str, str],
    offer_mode: str,
) -> list[dict[str, Any]]:
    focus = cfg["focus_project"]
    focus_name = cfg.get("focus_name") or "NUPPU"
    competitors = cfg.get("competitors") or []
    min_comp = int(cfg.get("min_total_competitor_units", 5))
    min_delta = int(cfg.get("total_availability_min_delta", 10))
    ratio = float(cfg.get("total_availability_ratio", 1.15))
    offer_label = OFFER_LABELS_SK.get(offer_mode, offer_mode)

    f_cnt = project_total_count(units, focus, offer_mode)
    items: list[dict[str, Any]] = []

    totals_line = " · ".join(
        f"{names.get(slug, slug)} {project_total_count(units, slug, offer_mode)}"
        for slug in [focus] + list(competitors)
    )
    items.append(
        {
            "kind": "opportunity",
            "score": 4,
            "segment_id": None,
            "segment_label": None,
            "competitor_slug": None,
            "title": f"Celková ponuka ({offer_label}) — prehľad",
            "body": (
                f"Počet jednotiek v aktuálnej ponuke: {totals_line}. "
                f"{focus_name}: {f_cnt} celkom."
            ),
        }
    )

    for comp_slug in competitors:
        c_cnt = project_total_count(units, comp_slug, offer_mode)
        if c_cnt < min_comp:
            continue
        comp_name = names.get(comp_slug, comp_slug)
        delta = f_cnt - c_cnt

        if f_cnt >= c_cnt * ratio and delta >= min_delta:
            items.append(
                {
                    "kind": "opportunity",
                    "score": 7,
                    "segment_id": None,
                    "segment_label": None,
                    "competitor_slug": comp_slug,
                    "title": f"Väčšia celková dostupnosť oproti {comp_name}",
                    "body": (
                        f"{focus_name}: {f_cnt} vs {comp_name}: {c_cnt} jednotiek ({offer_label}), "
                        f"o {delta} viac (+{100 * delta / c_cnt:.0f} % oproti {comp_name})."
                    ),
                }
            )
        elif c_cnt >= f_cnt * ratio and (c_cnt - f_cnt) >= min_delta:
            diff = c_cnt - f_cnt
            items.append(
                {
                    "kind": "risk",
                    "score": 7,
                    "segment_id": None,
                    "segment_label": None,
                    "competitor_slug": comp_slug,
                    "title": f"Menšia celková dostupnosť oproti {comp_name}",
                    "body": (
                        f"{focus_name}: {f_cnt} vs {comp_name}: {c_cnt} jednotiek ({offer_label}), "
                        f"o {diff} menej (−{100 * diff / c_cnt:.0f} % oproti {comp_name})."
                    ),
                }
            )

    return items


def _financing_insights(
    cfg: dict[str, Any], projects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    focus = cfg["focus_project"]
    focus_name = cfg.get("focus_name") or "NUPPU"
    names = _project_names(projects)
    focus_proj = next((p for p in projects if p["slug"] == focus), None)
    if not focus_proj:
        return []

    focus_fin = focus_proj.get("financing") or []
    if not focus_fin:
        return []

    rivals_without = []
    for c in cfg.get("competitors") or []:
        rival = next((p for p in projects if p["slug"] == c), None)
        if rival and not (rival.get("financing") or []):
            rivals_without.append(names.get(c, c))
    if not rivals_without:
        return []

    return [
        {
            "kind": "opportunity",
            "score": 7,
            "segment_id": None,
            "segment_label": None,
            "competitor_slug": None,
            "title": "Financovanie v ponuke YIT",
            "body": (
                f"{focus_name} ponúka: {', '.join(focus_fin)}. "
                f"Konkurenti bez explicitného financovania v metadátach: {', '.join(rivals_without)}."
            ),
        }
    ]


def compute_insights(data: dict[str, Any]) -> dict[str, Any]:
    cfg = _load_config()
    units = data.get("units") or []
    projects = data.get("projects") or []
    names = _project_names(projects)
    all_slugs = [cfg["focus_project"]] + list(cfg.get("competitors") or [])
    segments_cfg = cfg.get("segments") or []

    by_offer: dict[str, Any] = {}

    for offer_mode in OFFER_MODES:
        segment_rows: list[dict[str, Any]] = []
        all_items: list[dict[str, Any]] = []

        for segment in segments_cfg:
            matrix: dict[str, dict[str, Any]] = {}
            for slug in all_slugs:
                matrix[slug] = segment_stats_for_project(units, slug, segment, offer_mode)

            segment_rows.append(
                {
                    "id": segment["id"],
                    "label": segment["label"],
                    "projects": {
                        slug: {
                            "name": names.get(slug, slug),
                            **matrix[slug],
                        }
                        for slug in all_slugs
                    },
                }
            )
            all_items.extend(_run_rules(cfg, segment, matrix, names))

        all_items.extend(_total_availability_insights(cfg, units, names, offer_mode))
        if offer_mode == "free":
            all_items.extend(_financing_insights(cfg, projects))

        # Deduplicate similar titles (keep highest score)
        seen: dict[str, dict[str, Any]] = {}
        for item in all_items:
            key = f"{item['kind']}:{item.get('title')}"
            if key not in seen or item["score"] > seen[key]["score"]:
                seen[key] = item

        sorted_items = sorted(seen.values(), key=lambda x: (-x["score"], x.get("title") or ""))

        by_offer[offer_mode] = {
            "segments": segment_rows,
            "items": sorted_items[:20],
            "opportunities": [i for i in sorted_items if i["kind"] == "opportunity"][:8],
            "risks": [i for i in sorted_items if i["kind"] == "risk"][:8],
        }

    return {
        "focus_project": cfg["focus_project"],
        "focus_name": cfg.get("focus_name") or "NUPPU",
        "competitor_names": {s: names.get(s, s) for s in cfg.get("competitors") or []},
        "offer_modes": by_offer,
        "methodology": (
            "Insighty sa počítajú pri generovaní dashboardu z rovnakých dát ako tabuľka. "
            "Porovnanie je po segmentoch izieb; €/m² z ceny a obytnej plochy. "
            f"Konkurent musí mať aspoň {int(cfg.get('min_competitor_units', 5))} jednotiek v segmente, "
            f"NUPPU aspoň {int(cfg.get('min_focus_units_for_ppm', 3))} na €/m². "
            f"Celková dostupnosť: porovnanie súčtu jednotiek v ponuke, konkurent ≥ "
            f"{int(cfg.get('min_total_competitor_units', 5))}, rozdiel ≥ "
            f"{int(cfg.get('total_availability_min_delta', 10))}. "
            "Green Atrium API často obsahuje len zvyšok ponuky."
        ),
    }
