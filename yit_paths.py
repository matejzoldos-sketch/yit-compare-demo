"""Shared paths for the yit comparison project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "yit.db"
SCHEMA_PATH = ROOT / "schema" / "init.sql"
DASHBOARD_DIR = ROOT / "dashboard"
DASHBOARD_TEMPLATE = DASHBOARD_DIR / "compare.template.html"
DASHBOARD_OUT = DASHBOARD_DIR / "compare.html"
EXPORT_JSON = DATA_DIR / "export.json"
