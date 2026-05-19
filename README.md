# Marketing Intelligence Radar NUPPU

Porovnanie developerských projektov (byty, ceny, Meta Ad Library). Fokus: NUPPU vs konkurencia.

Lokálny nástroj na zber, normalizáciu a porovnanie ponuky bytov z verejných API:

- [Green Atrium](https://www.bytygreenatrium.sk/cennik) (Haberl)
- [NUPPU](https://www.yit.sk/predaj-bytov/bratislava/ruzinov/nuppu) (YIT)
- [Bory](https://borybyvanie.sk/byty) (Penta Real Estate)
- [Slnečnice Nové viladomy](https://www.slnecnice.sk/projekty/nove-viladomy) (CRESCO)

## Požiadavky

- Python 3.10+
- Sieťové pripojenie pri sťahovaní dát

## Inštalácia

```bash
cd yit
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Použitie

### 1. Stiahnuť dáta a naplniť SQLite

```bash
python -m etl.fetch_all
```

Uloží raw JSON do `data/raw/` a normalizované záznamy do `data/yit.db`.

### 2. Vygenerovať dashboard

```bash
python -m etl.build_dashboard
```

Vytvorí:

- `data/export.json` — export pre ďalšie spracovanie
- `dashboard/compare.html` — samostatná stránka s vloženými dátami (otvorte priamo v prehliadači)

### 3. Prehliadanie

```bash
open dashboard/compare.html
```

Prípadne lokálny server:

```bash
python -m http.server 8080 --directory dashboard
# http://localhost:8080/compare.html
```

## Štruktúra

| Cesta | Účel |
|-------|------|
| `config/sources.yaml` | URL API, PageId, AreaIds pre YIT |
| `config/projects_manual.yaml` | Metadáta projektov (adresa, vybavenie, financovanie) |
| `scrapers/` | Sťahovanie raw dát |
| `etl/normalize.py` | Raw → SQLite |
| `schema/init.sql` | Schéma databázy |
| `dashboard/compare.template.html` | Šablóna UI |

## Obnova dát

Spúšťajte `python -m etl.fetch_all` manuálne podľa potreby (odporúčané max. cca 1× denne). História fetchov je v tabuľke `fetch_runs`.

## Právna poznámka

Dáta sú verejne dostupné na weboch developerov. Tento projekt je určený na **osobnú analýzu a porovnanie** — bez redistribúcie získaných dát tretím stranám. Pri zmene podmienok používania webov prispôsobte frekvenciu sťahovania alebo kontaktujte developera.

## Meta Ad Library (manuálny demo export)

Konkurenčné reklamy pre rovnaké projekty ako na [demo dashboarde](https://marketing-intelligence-radar-nuppu.vercel.app/):

- **Dashboard:** záložka **Meta reklamy** (dáta z `config/meta_ads_insights.yaml`, po `python -m etl.build_dashboard`)
- Návod: [`docs/META_ADS_MANUAL.md`](docs/META_ADS_MANUAL.md) — odkazy, postup, CSV šablóna
- Paste demo: [`docs/META_ADS_PASTE_DEMO.md`](docs/META_ADS_PASTE_DEMO.md)
- Konfigurácia odkazov: `config/meta_ads_competitors.yaml`
- **Insight dáta pre UI:** `config/meta_ads_insights.yaml` — upravte počty/texty po novom exporte z Ad Library

## Rozšírenie o ďalší projekt

1. Pridajte zdroj do `config/sources.yaml`
2. Implementujte `scrapers/<projekt>.py`
3. Rozšírte `etl/normalize.py` a `etl/fetch_all.py`
4. Doplňte `config/projects_manual.yaml`
