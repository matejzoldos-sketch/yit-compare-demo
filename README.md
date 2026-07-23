# Marketing Intelligence Radar NUPPU

Porovnanie developerských projektov (byty, ceny €/m², Meta Ad Library). Fokus: **NUPPU (YIT) vs konkurencia**.

Live demo: [marketing-intelligence-radar-nuppu.vercel.app](https://marketing-intelligence-radar-nuppu.vercel.app/)  
Repo: [github.com/matejzoldos-sketch/yit-compare-demo](https://github.com/matejzoldos-sketch/yit-compare-demo)

Lokálny Python nástroj: stiahne verejné API/JSON, normalizuje do **SQLite**, vygeneruje **statický HTML** dashboard.

Zdroje:

- [Green Atrium](https://www.bytygreenatrium.sk/cennik) (Haberl)
- [NUPPU](https://www.yit.sk/predaj-bytov/bratislava/ruzinov/nuppu) (YIT)
- [Bory](https://borybyvanie.sk/byty) (Penta Real Estate)
- [Slnečnice Nové viladomy](https://www.slnecnice.sk/projekty/nove-viladomy) (CRESCO)

## Požiadavky

- Python **3.9+** (odporúčané 3.10+)
- Sieť pri sťahovaní dát
- Žiadne API secrets — `.env` nie je potrebné

## Inštalácia

```bash
cd yit-compare-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Použitie

### 1. Stiahnuť dáta a naplniť SQLite

```bash
python -m etl.fetch_all
```

Uloží raw JSON do `data/raw/` a normalizované záznamy do `data/yit.db`. Schéma (`schema/init.sql`) sa aplikuje automaticky pri prvom connecte.

Po čistom clone ešte nemáš `data/yit.db` ani `data/raw/` (sú v `.gitignore`) — bez tohto kroku nemáš čerstvé dáta.

### 2. Vygenerovať dashboard

```bash
python -m etl.build_dashboard
```

Vytvorí:

- `data/export.json` — export pre ďalšie spracovanie
- `dashboard/compare.html` — stránka s vloženými dátami (+ trhové insighty z `etl/insights.py`)

### 3. Prehliadanie

```bash
open dashboard/compare.html
# alebo:
python -m http.server 8080 --directory dashboard
```

## Štruktúra

| Cesta | Účel |
|-------|------|
| `config/sources.yaml` | URL API, PageId, AreaIds pre YIT |
| `config/projects_manual.yaml` | Metadáta projektov |
| `config/insights.yaml` | Pravidlá automatic insight engine |
| `config/meta_ads_competitors.yaml` | Odkazy na Ad Library |
| `config/meta_ads_insights.yaml` | Manuálne Meta dáta pre UI |
| `scrapers/` | Sťahovanie raw dát |
| `etl/fetch_all.py` | Fetch + normalize |
| `etl/normalize.py` | Raw → SQLite |
| `etl/build_dashboard.py` | SQLite → `compare.html` + export |
| `etl/insights.py` | Trhové insighty (NUPPU fokus) |
| `etl/meta_ads_insights.py` | Meta Ads do dashboardu |
| `yit_paths.py` | Centrálne cesty |
| `schema/init.sql` | SQLite schéma |
| `dashboard/compare.template.html` | Šablóna UI |
| `dashboard/vercel.json` | Rewrite `/` → `compare.html` |
| `docs/` | Meta Ads manuál |

## Deploy na Vercel

1. Vercel projekt: Root Directory = **`dashboard/`**
2. Po zmene dát: `python -m etl.build_dashboard` a commitni aktualizovaný `dashboard/compare.html`
3. Push na `main` → auto-deploy (bez server-side buildu)

## Obnova dát

Spúšťaj `python -m etl.fetch_all` manuálne (odporúčané max. ~1× denne). História v tabuľke `fetch_runs`. Žiadne GitHub Actions.

## Meta Ad Library (manuálne)

1. Export podľa [`docs/META_ADS_MANUAL.md`](docs/META_ADS_MANUAL.md)
2. Uprav `config/meta_ads_insights.yaml`
3. `python -m etl.build_dashboard`

Ďalej: [`docs/META_ADS_PASTE_DEMO.md`](docs/META_ADS_PASTE_DEMO.md), `config/meta_ads_competitors.yaml`. Záložka **Meta reklamy** na dashboarde.

## Rozšírenie o ďalší projekt

1. Pridaj zdroj do `config/sources.yaml`
2. Implementuj `scrapers/<projekt>.py`
3. Rozšír `etl/normalize.py` a `etl/fetch_all.py`
4. Doplň `config/projects_manual.yaml`
5. Podľa potreby `config/insights.yaml` a `config/meta_ads_competitors.yaml`
6. Rebuild dashboardu

## Právna poznámka

Dáta sú verejne dostupné na weboch developerov. Projekt je na **osobnú analýzu a porovnanie** — bez redistribúcie tretím stranám. Pri zmene podmienok používania webov prispôsob frekvenciu sťahovania.
