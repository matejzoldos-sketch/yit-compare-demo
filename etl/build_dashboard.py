"""Export SQLite data and build compare.html dashboard."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from etl.insights import compute_insights
from etl.meta_ads_insights import load_meta_ads_insights
from yit_paths import DASHBOARD_OUT, DASHBOARD_TEMPLATE, DB_PATH, EXPORT_JSON


def export_data(conn: sqlite3.Connection) -> dict[str, Any]:
    projects = [
        dict(r)
        for r in conn.execute(
            """
            SELECT slug, name, developer, address, city, district, delivery_note,
                   website_url, contact_phone, contact_email, financing_json,
                   amenities_json, notes, scraped_at
            FROM projects ORDER BY name
            """
        ).fetchall()
    ]
    for p in projects:
        for key in ("financing_json", "amenities_json"):
            if p.get(key):
                try:
                    p[key.replace("_json", "")] = json.loads(p[key])
                except json.JSONDecodeError:
                    p[key.replace("_json", "")] = []
            else:
                p[key.replace("_json", "")] = []
            del p[key]

    units = [
        dict(r)
        for r in conn.execute(
            """
            SELECT u.id, p.slug AS project_slug, p.name AS project_name,
                   u.source, u.external_id, u.unit_code, u.building_name,
                   u.rooms, u.floor, u.orientation,
                   u.area_interior_m2, u.area_exterior_m2, u.area_total_m2,
                   u.area_cellar_m2, u.price_total_eur, u.price_per_m2_eur,
                   u.price_with_financing_eur, u.price_non_debt_eur,
                   u.price_label, u.status, u.detail_url, u.floorplan_url,
                   u.pdf_url, u.scraped_at
            FROM units u
            JOIN projects p ON p.id = u.project_id
            ORDER BY p.name, u.status, u.rooms, u.area_interior_m2
            """
        ).fetchall()
    ]

    attrs_by_unit: dict[int, list[dict[str, str]]] = {}
    for row in conn.execute(
        "SELECT unit_id, key, value, value_type FROM unit_attributes ORDER BY key"
    ).fetchall():
        uid = int(row["unit_id"])
        attrs_by_unit.setdefault(uid, []).append(
            {"key": row["key"], "value": row["value"], "type": row["value_type"]}
        )

    for u in units:
        u["attributes"] = attrs_by_unit.get(int(u["id"]), [])

    runs = [
        dict(r)
        for r in conn.execute(
            """
            SELECT source, path_raw, units_count, started_at, finished_at, success
            FROM fetch_runs ORDER BY id DESC LIMIT 20
            """
        ).fetchall()
    ]

    payload = {
        "projects": projects,
        "units": units,
        "fetch_runs": runs,
        "generated_at": runs[0]["finished_at"] if runs else None,
    }
    payload["insights"] = compute_insights(payload)
    payload["meta_ads"] = load_meta_ads_insights()
    return payload


def build_html(data: dict[str, Any]) -> str:
    template = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False)
    return template.replace("/*__DATA__*/", payload)


def main() -> int:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}. Run: python -m etl.fetch_all")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        data = export_data(conn)
    finally:
        conn.close()

    EXPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with EXPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    html = build_html(data)
    DASHBOARD_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {EXPORT_JSON}")
    print(f"Wrote {DASHBOARD_OUT} ({len(data['units'])} units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
