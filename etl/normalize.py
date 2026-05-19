"""Normalize raw JSON snapshots into SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scrapers._common import load_manual_projects, load_sources
from yit_paths import DB_PATH, RAW_DIR, SCHEMA_PATH


MAPPED_GA_KEYS = {
    "id",
    "name",
    "slug",
    "rooms",
    "floor",
    "orientation",
    "area_netto",
    "area_brutto",
    "area_total",
    "area_cellar",
    "price",
    "price_per_m2",
    "cena_s_flexibilnym_financovanim",
    "state",
    "blueprint",
    "pdf",
    "flat_pdf",
}

MAPPED_BORY_KEYS = {
    "flat_internal_id",
    "flat_penta_internal_id",
    "flat_area",
    "flat_area_total",
    "flat_area_other",
    "flat_price",
    "flat_price_before_discount_vat",
    "flat_status",
    "flat_status_penta",
    "flat_number_of_rooms",
    "flat_type",
    "flat_entrance",
    "building",
    "url_link_to_the_vr_apartments_tour",
}

MAPPED_SLNECNICE_KEYS = {
    "id",
    "internal_id",
    "project",
    "building",
    "rooms",
    "disposition",
    "floor",
    "orientation",
    "area",
    "area_exterior",
    "area_total",
    "area_balcony",
    "area_terrace",
    "area_garden",
    "price",
    "price_discounted",
    "price_without_vat",
    "price_discounted_without_vat",
    "status_code",
    "status_name",
    "date_of_completion",
    "finished_indicator",
    "under_construction",
    "plan",
    "pdf",
    "type_code",
    "type_name",
    "zone",
}

MAPPED_YIT_KEYS = {
    "ApartmentNumber",
    "NumberOfRooms",
    "FloorNumber",
    "WindowsOrientation",
    "ApartmentSize",
    "TotalAreaSize",
    "OtherAreaSize",
    "SalesPrice",
    "SalesPricePerSquare",
    "NonDebtPrice",
    "ReservationStatusKey",
    "ReservationStatus",
    "ProjectShortTitle",
    "ProjectTitle",
    "_Url",
    "FloorPlanUrl",
    "PdfUrl",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def map_status_ga(state: str | None) -> str:
    mapping = {
        "free": "free",
        "reserved": "reserved",
        "sold": "sold",
        "inpreparation": "in_preparation",
    }
    return mapping.get((state or "").lower(), "unknown")


def map_status_yit(key: str | None) -> str:
    mapping = {
        "Free": "free",
        "Reserved": "reserved",
        "Sold": "sold",
    }
    return mapping.get(key or "", "unknown")


def map_status_bory(code: str | int | None) -> str:
    mapping = {
        "0": "free",
        "1": "reserved",
        "2": "reserved",
        "3": "sold",
        "4": "reserved",
        "5": "in_preparation",
    }
    return mapping.get(str(code) if code is not None else "", "unknown")


def map_status_slnecnice(code: str | None) -> str:
    mapping = {
        "Y": "free",
        "P": "reserved",
        "S": "sold",
    }
    return mapping.get((code or "").upper(), "unknown")


def _float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _rooms(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def _price_per_m2_interior(price: Any, area_interior: Any) -> float | None:
    """Cena za m² z obytnej plochy (pre porovnanie medzi developermi)."""
    p, a = _float(price), _float(area_interior)
    if p is None or a is None or a <= 0 or p <= 0:
        return None
    return round(p / a, 2)


def attr_type(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    return "string"


def attr_value(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def upsert_project(
    conn: sqlite3.Connection,
    slug: str,
    name: str,
    developer: str,
    website_url: str,
    scraped_at: str,
) -> int:
    manual = (load_manual_projects().get("projects") or {}).get(slug) or {}
    financing = manual.get("financing")
    amenities = manual.get("amenities")
    conn.execute(
        """
        INSERT INTO projects (
            slug, name, developer, address, city, district, delivery_note,
            website_url, contact_phone, contact_email, financing_json,
            amenities_json, notes, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            name=excluded.name,
            developer=excluded.developer,
            address=excluded.address,
            city=excluded.city,
            district=excluded.district,
            delivery_note=excluded.delivery_note,
            website_url=excluded.website_url,
            contact_phone=excluded.contact_phone,
            contact_email=excluded.contact_email,
            financing_json=excluded.financing_json,
            amenities_json=excluded.amenities_json,
            notes=excluded.notes,
            scraped_at=excluded.scraped_at
        """,
        (
            slug,
            name,
            developer,
            manual.get("address"),
            manual.get("city"),
            manual.get("district"),
            manual.get("delivery_note"),
            website_url,
            manual.get("contact_phone"),
            manual.get("contact_email"),
            json.dumps(financing, ensure_ascii=False) if financing else None,
            json.dumps(amenities, ensure_ascii=False) if amenities else None,
            manual.get("notes"),
            scraped_at,
        ),
    )
    row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
    return int(row["id"])


def insert_attributes(
    conn: sqlite3.Connection,
    unit_id: int,
    attrs: Iterable[tuple[str, Any]],
) -> None:
    for key, val in attrs:
        if val is None or val == "":
            continue
        conn.execute(
            """
            INSERT INTO unit_attributes (unit_id, key, value, value_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(unit_id, key) DO UPDATE SET
                value=excluded.value,
                value_type=excluded.value_type
            """,
            (unit_id, key, attr_value(val), attr_type(val)),
        )


def normalize_green_atrium(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cfg = load_sources()["green_atrium"]
    scraped_at = payload.get("fetched_at") or _now()
    project_id = upsert_project(
        conn,
        cfg["slug"],
        cfg["name"],
        cfg["developer"],
        cfg["website_url"],
        scraped_at,
    )
    base = cfg["base_url"].rstrip("/")
    count = 0

    for flat in list(payload.get("flats") or []) + list(payload.get("duplex_flats") or []):
        external_id = str(flat.get("id") or flat.get("unit_id") or flat.get("slug"))
        floor_obj = flat.get("floor") or {}
        block = (floor_obj.get("block") or {}).get("name")
        building = f"Blok {block}" if block else None
        blueprint = flat.get("blueprint") or flat.get("flat_image")
        pdf = flat.get("flat_pdf") or flat.get("pdf")
        if blueprint and str(blueprint).startswith("/"):
            blueprint = base + blueprint
        if pdf and str(pdf).startswith("/"):
            pdf = base + pdf

        area_netto = _float(flat.get("area_netto"))
        price = _float(flat.get("price"))
        price_per_m2 = _price_per_m2_interior(price, area_netto)
        if price_per_m2 is None:
            price_per_m2 = _float(flat.get("price_per_m2"))

        conn.execute(
            """
            INSERT INTO units (
                project_id, source, external_id, unit_code, building_name,
                rooms, floor, orientation, area_interior_m2, area_exterior_m2,
                area_total_m2, area_cellar_m2, price_total_eur, price_per_m2_eur,
                price_with_financing_eur, price_non_debt_eur, price_label, status,
                detail_url, floorplan_url, pdf_url, scraped_at
            ) VALUES (?, 'green_atrium', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                project_id=excluded.project_id,
                unit_code=excluded.unit_code,
                building_name=excluded.building_name,
                rooms=excluded.rooms,
                floor=excluded.floor,
                orientation=excluded.orientation,
                area_interior_m2=excluded.area_interior_m2,
                area_exterior_m2=excluded.area_exterior_m2,
                area_total_m2=excluded.area_total_m2,
                area_cellar_m2=excluded.area_cellar_m2,
                price_total_eur=excluded.price_total_eur,
                price_per_m2_eur=excluded.price_per_m2_eur,
                price_with_financing_eur=excluded.price_with_financing_eur,
                price_non_debt_eur=excluded.price_non_debt_eur,
                price_label=excluded.price_label,
                status=excluded.status,
                detail_url=excluded.detail_url,
                floorplan_url=excluded.floorplan_url,
                pdf_url=excluded.pdf_url,
                scraped_at=excluded.scraped_at
            """,
            (
                project_id,
                external_id,
                flat.get("name") or flat.get("slug"),
                building,
                _rooms(flat.get("rooms")),
                str(floor_obj.get("format_floor") or floor_obj.get("floor_number") or ""),
                flat.get("orientation"),
                area_netto,
                _float(flat.get("area_brutto")),
                _float(flat.get("area_total")),
                _float(flat.get("area_cellar")),
                price,
                price_per_m2,
                _float(flat.get("cena_s_flexibilnym_financovanim")),
                None,
                "Cena; €/m² z obytnej plochy (netto)",
                map_status_ga(flat.get("state")),
                f"{base}/ponuka-bytov/{flat.get('slug')}" if flat.get("slug") else None,
                blueprint,
                pdf,
                scraped_at,
            ),
        )
        row = conn.execute(
            "SELECT id FROM units WHERE source = 'green_atrium' AND external_id = ?",
            (external_id,),
        ).fetchone()
        unit_id = int(row["id"])
        extra = [(k, flat[k]) for k in flat if k not in MAPPED_GA_KEYS]
        if flat.get("price_per_m2") is not None:
            extra.append(("api_price_per_m2_brutto", flat.get("price_per_m2")))
        insert_attributes(conn, unit_id, extra)
        count += 1
    return count


def normalize_yit(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cfg = load_sources()["yit_nuppu"]
    scraped_at = payload.get("fetched_at") or _now()
    project_id = upsert_project(
        conn,
        cfg["slug"],
        cfg["name"],
        cfg["developer"],
        cfg["website_url"],
        scraped_at,
    )
    count = 0
    for hit in payload.get("hits") or []:
        fields = hit.get("Fields") or {}
        external_id = str(hit.get("Id") or fields.get("CrmId") or fields.get("ApartmentNumber"))
        url = fields.get("_Url")
        detail = f"https://www.yit.sk{url}" if url and url.startswith("/") else url
        floorplan = fields.get("FloorPlanUrl") or fields.get("FloorplanUrl")
        pdf = fields.get("PdfUrl")

        conn.execute(
            """
            INSERT INTO units (
                project_id, source, external_id, unit_code, building_name,
                rooms, floor, orientation, area_interior_m2, area_exterior_m2,
                area_total_m2, area_cellar_m2, price_total_eur, price_per_m2_eur,
                price_with_financing_eur, price_non_debt_eur, price_label, status,
                detail_url, floorplan_url, pdf_url, scraped_at
            ) VALUES (?, 'yit_nuppu', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                project_id=excluded.project_id,
                unit_code=excluded.unit_code,
                building_name=excluded.building_name,
                rooms=excluded.rooms,
                floor=excluded.floor,
                orientation=excluded.orientation,
                area_interior_m2=excluded.area_interior_m2,
                area_exterior_m2=excluded.area_exterior_m2,
                area_total_m2=excluded.area_total_m2,
                area_cellar_m2=excluded.area_cellar_m2,
                price_total_eur=excluded.price_total_eur,
                price_per_m2_eur=excluded.price_per_m2_eur,
                price_with_financing_eur=excluded.price_with_financing_eur,
                price_non_debt_eur=excluded.price_non_debt_eur,
                price_label=excluded.price_label,
                status=excluded.status,
                detail_url=excluded.detail_url,
                floorplan_url=excluded.floorplan_url,
                pdf_url=excluded.pdf_url,
                scraped_at=excluded.scraped_at
            """,
            (
                project_id,
                external_id,
                fields.get("ApartmentNumber"),
                fields.get("ProjectShortTitle") or fields.get("ProjectTitle"),
                _rooms(fields.get("NumberOfRooms")),
                str(fields.get("FloorNumber") or ""),
                fields.get("WindowsOrientation"),
                _float(fields.get("ApartmentSize")),
                _float(fields.get("OtherAreaSize")),
                _float(fields.get("TotalAreaSize")),
                None,
                _float(fields.get("SalesPrice")),
                _float(fields.get("SalesPricePerSquare")),
                None,
                _float(fields.get("NonDebtPrice")),
                "Predajná cena s DPH / NonDebt",
                map_status_yit(fields.get("ReservationStatusKey")),
                detail,
                floorplan,
                pdf,
                scraped_at,
            ),
        )
        row = conn.execute(
            "SELECT id FROM units WHERE source = 'yit_nuppu' AND external_id = ?",
            (external_id,),
        ).fetchone()
        unit_id = int(row["id"])
        extra = [(k, fields[k]) for k in fields if k not in MAPPED_YIT_KEYS]
        insert_attributes(conn, unit_id, extra)
        count += 1
    return count


def normalize_bory(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cfg = load_sources()["bory"]
    scraped_at = payload.get("fetched_at") or _now()
    project_id = upsert_project(
        conn,
        cfg["slug"],
        cfg["name"],
        cfg["developer"],
        cfg["website_url"],
        scraped_at,
    )
    base = cfg["base_url"].rstrip("/")
    count = 0

    for flat in payload.get("flats") or []:
        external_id = str(
            flat.get("flat_internal_id") or flat.get("flat_penta_internal_id") or ""
        )
        if not external_id:
            continue

        building = flat.get("building") or {}
        stage = building.get("building_stage") or ""
        bname = building.get("building_name") or ""
        building_label = f"{stage} / budova {bname}".strip(" /") if stage or bname else None

        area_interior = _float(flat.get("flat_area"))
        area_other = _float(flat.get("flat_area_other"))
        area_total = _float(flat.get("flat_area_total")) or area_interior
        area_exterior = (
            area_other
            if area_interior and area_other and area_other < area_interior
            else None
        )
        price = _float(flat.get("flat_price"))
        price_per_m2 = _price_per_m2_interior(price, area_interior)

        floorplan = building.get("floor_plan")
        detail = f"{base}/byty"
        if stage:
            detail = f"{base}/byty?etapa={stage.replace('bory', '')}"

        conn.execute(
            """
            INSERT INTO units (
                project_id, source, external_id, unit_code, building_name,
                rooms, floor, orientation, area_interior_m2, area_exterior_m2,
                area_total_m2, area_cellar_m2, price_total_eur, price_per_m2_eur,
                price_with_financing_eur, price_non_debt_eur, price_label, status,
                detail_url, floorplan_url, pdf_url, scraped_at
            ) VALUES (?, 'bory', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                project_id=excluded.project_id,
                unit_code=excluded.unit_code,
                building_name=excluded.building_name,
                rooms=excluded.rooms,
                floor=excluded.floor,
                orientation=excluded.orientation,
                area_interior_m2=excluded.area_interior_m2,
                area_exterior_m2=excluded.area_exterior_m2,
                area_total_m2=excluded.area_total_m2,
                area_cellar_m2=excluded.area_cellar_m2,
                price_total_eur=excluded.price_total_eur,
                price_per_m2_eur=excluded.price_per_m2_eur,
                price_with_financing_eur=excluded.price_with_financing_eur,
                price_non_debt_eur=excluded.price_non_debt_eur,
                price_label=excluded.price_label,
                status=excluded.status,
                detail_url=excluded.detail_url,
                floorplan_url=excluded.floorplan_url,
                pdf_url=excluded.pdf_url,
                scraped_at=excluded.scraped_at
            """,
            (
                project_id,
                external_id,
                flat.get("flat_penta_internal_id") or flat.get("flat_internal_id"),
                building_label,
                _rooms(flat.get("flat_number_of_rooms")),
                str(building.get("floor_number") or ""),
                flat.get("flat_entrance"),
                area_interior,
                area_exterior,
                area_total,
                None,
                price,
                price_per_m2,
                None,
                None,
                "Cena s DPH (flat_price); m² z flat_area",
                map_status_bory(flat.get("flat_status")),
                detail,
                floorplan,
                None,
                scraped_at,
            ),
        )
        row = conn.execute(
            "SELECT id FROM units WHERE source = 'bory' AND external_id = ?",
            (external_id,),
        ).fetchone()
        unit_id = int(row["id"])
        extra = [(k, flat[k]) for k in flat if k not in MAPPED_BORY_KEYS]
        if flat.get("url_link_to_the_vr_apartments_tour"):
            extra.append(("vr_tour_url", flat.get("url_link_to_the_vr_apartments_tour")))
        insert_attributes(conn, unit_id, extra)
        count += 1
    return count


def normalize_slnecnice(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cfg = load_sources()["slnecnice_viladomy"]
    scraped_at = payload.get("fetched_at") or _now()
    project_id = upsert_project(
        conn,
        cfg["slug"],
        cfg["name"],
        cfg["developer"],
        cfg["website_url"],
        scraped_at,
    )
    base = cfg["base_url"].rstrip("/")
    flats_path = cfg.get("flats_path", "/byvanie")
    count = 0

    for flat in payload.get("flats") or []:
        external_id = str(flat.get("internal_id") or flat.get("id") or "")
        if not external_id:
            continue

        area_interior = _float(flat.get("area"))
        area_exterior = _float(flat.get("area_exterior"))
        area_total = _float(flat.get("area_total")) or area_interior
        price_raw = _float(flat.get("price"))
        price_disc = _float(flat.get("price_discounted"))
        price = price_disc if price_disc and price_raw and price_disc != price_raw else price_raw
        price_per_m2 = _price_per_m2_interior(price, area_interior)
        building = flat.get("building")
        building_label = f"Budova {building}" if building else None
        detail = f"{base}{flats_path}/{external_id}"

        conn.execute(
            """
            INSERT INTO units (
                project_id, source, external_id, unit_code, building_name,
                rooms, floor, orientation, area_interior_m2, area_exterior_m2,
                area_total_m2, area_cellar_m2, price_total_eur, price_per_m2_eur,
                price_with_financing_eur, price_non_debt_eur, price_label, status,
                detail_url, floorplan_url, pdf_url, scraped_at
            ) VALUES (?, 'slnecnice_viladomy', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                project_id=excluded.project_id,
                unit_code=excluded.unit_code,
                building_name=excluded.building_name,
                rooms=excluded.rooms,
                floor=excluded.floor,
                orientation=excluded.orientation,
                area_interior_m2=excluded.area_interior_m2,
                area_exterior_m2=excluded.area_exterior_m2,
                area_total_m2=excluded.area_total_m2,
                area_cellar_m2=excluded.area_cellar_m2,
                price_total_eur=excluded.price_total_eur,
                price_per_m2_eur=excluded.price_per_m2_eur,
                price_with_financing_eur=excluded.price_with_financing_eur,
                price_non_debt_eur=excluded.price_non_debt_eur,
                price_label=excluded.price_label,
                status=excluded.status,
                detail_url=excluded.detail_url,
                floorplan_url=excluded.floorplan_url,
                pdf_url=excluded.pdf_url,
                scraped_at=excluded.scraped_at
            """,
            (
                project_id,
                external_id,
                flat.get("internal_id"),
                building_label,
                _rooms(flat.get("rooms")),
                str(flat.get("floor") or ""),
                flat.get("orientation"),
                area_interior,
                area_exterior,
                area_total,
                None,
                price,
                price_per_m2,
                None,
                None,
                "Cena s DPH (price / price_discounted); m² z area (interiér)",
                map_status_slnecnice(flat.get("status_code")),
                detail,
                flat.get("plan"),
                flat.get("pdf"),
                scraped_at,
            ),
        )
        row = conn.execute(
            "SELECT id FROM units WHERE source = 'slnecnice_viladomy' AND external_id = ?",
            (external_id,),
        ).fetchone()
        unit_id = int(row["id"])
        extra = [(k, flat[k]) for k in flat if k not in MAPPED_SLNECNICE_KEYS]
        insert_attributes(conn, unit_id, extra)
        count += 1
    return count


def record_fetch_run(
    conn: sqlite3.Connection,
    source: str,
    path_raw: str,
    units_count: int,
    started_at: str,
    success: bool,
) -> None:
    conn.execute(
        """
        INSERT INTO fetch_runs (source, path_raw, units_count, started_at, finished_at, success)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source, path_raw, units_count, started_at, _now(), 1 if success else 0),
    )


def _latest_raw(source: str) -> Path | None:
    folder = RAW_DIR / source
    if not folder.is_dir():
        return None
    files = sorted(folder.glob("*.json"), reverse=True)
    return files[0] if files else None


def normalize_from_latest_raw() -> dict[str, int]:
    """Re-normalize DB from newest raw snapshots (no network)."""
    ga = _latest_raw("green_atrium")
    yit = _latest_raw("yit_nuppu")
    bory = _latest_raw("bory")
    sln = _latest_raw("slnecnice_viladomy")
    if not ga or not yit or not bory or not sln:
        raise FileNotFoundError("Missing raw snapshots in data/raw/. Run: python -m etl.fetch_all")
    return normalize_from_files(ga, yit, bory, sln)


def normalize_from_files(
    green_path: Path | None = None,
    yit_path: Path | None = None,
    bory_path: Path | None = None,
    slnecnice_path: Path | None = None,
) -> dict[str, int]:
    conn = connect_db()
    counts: dict[str, int] = {}
    try:
        if green_path:
            payload = json.loads(green_path.read_text(encoding="utf-8"))
            counts["green_atrium"] = normalize_green_atrium(conn, payload)
        if yit_path:
            payload = json.loads(yit_path.read_text(encoding="utf-8"))
            counts["yit_nuppu"] = normalize_yit(conn, payload)
        if bory_path:
            payload = json.loads(bory_path.read_text(encoding="utf-8"))
            counts["bory"] = normalize_bory(conn, payload)
        if slnecnice_path:
            payload = json.loads(slnecnice_path.read_text(encoding="utf-8"))
            counts["slnecnice_viladomy"] = normalize_slnecnice(conn, payload)
        conn.commit()
    finally:
        conn.close()
    return counts
