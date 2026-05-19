PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    developer TEXT,
    address TEXT,
    city TEXT,
    district TEXT,
    delivery_note TEXT,
    website_url TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    financing_json TEXT,
    amenities_json TEXT,
    notes TEXT,
    scraped_at TEXT
);

CREATE TABLE IF NOT EXISTS fetch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    path_raw TEXT NOT NULL,
    units_count INTEGER,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    success INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    unit_code TEXT,
    building_name TEXT,
    rooms REAL,
    floor TEXT,
    orientation TEXT,
    area_interior_m2 REAL,
    area_exterior_m2 REAL,
    area_total_m2 REAL,
    area_cellar_m2 REAL,
    price_total_eur REAL,
    price_per_m2_eur REAL,
    price_with_financing_eur REAL,
    price_non_debt_eur REAL,
    price_label TEXT,
    status TEXT NOT NULL,
    detail_url TEXT,
    floorplan_url TEXT,
    pdf_url TEXT,
    scraped_at TEXT NOT NULL,
    UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS unit_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT,
    value_type TEXT NOT NULL DEFAULT 'string',
    UNIQUE(unit_id, key)
);

CREATE INDEX IF NOT EXISTS idx_units_project ON units(project_id);
CREATE INDEX IF NOT EXISTS idx_units_status ON units(status);
CREATE INDEX IF NOT EXISTS idx_unit_attributes_unit ON unit_attributes(unit_id);
