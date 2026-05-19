# Manuálny export z Meta Ad Library (demo konkurenti)

Pre [demo porovnanie projektov](https://yit-compare-demo.vercel.app/) — rovnakí hráči ako v `config/insights.yaml`:

| Projekt | Developer | Slug |
|---------|-----------|------|
| **NUPPU** (fokus) | YIT Slovakia | `nuppu` |
| Green Atrium | Haberl | `green_atrium` |
| Bory | Penta Real Estate | `bory` |
| Slnečnice Nové viladomy | CRESCO | `slnecnice_viladomy` |

Oficiálny nástroj: [Meta Ad Library](https://www.facebook.com/ads/library/). API neskôr: [Ad Library API](https://www.facebook.com/ads/library/api/).

---

## Rýchly štart (≈ 45 min na prvý prehľad)

1. Skopírujte šablónu:  
   `cp data/raw/meta_ads/manual/ads_template.csv data/raw/meta_ads/manual/ads_YYYY-MM-DD.csv`
2. Otvorte odkazy z tabuľky nižšie (krajina **Slovensko**, stav **Všetky**).
3. Pre každého konkurenta zapíšte **10–15 najrelevantnejších** inzerátov (byty / projekt, nie generický employer branding — ten môžete tagovať `brand`).
4. Uložte CSV; voliteľne screenshoty do `data/raw/meta_ads/manual/screenshots/<slug>/`.

---

## Priame odkazy (Slovensko, všetky stavy)

### NUPPU / YIT

- [YIT Slovakia — kľúčové slovo](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=YIT%20Slovakia&search_type=keyword_unordered)
- [NUPPU — kľúčové slovo](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=NUPPU&search_type=keyword_unordered)

**Tip:** V výsledkoch vyberte stránku **YIT Slovakia** (alebo projektovú stránku) → *Zobraziť všetky reklamy tejto stránky* — menej šumu než čisté keyword.

### Green Atrium

- [Green Atrium](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=Green%20Atrium&search_type=keyword_unordered)
- [bytygreenatrium](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=bytygreenatrium&search_type=keyword_unordered)

### Bory

- [Bory Bývanie — kľúčové slovo](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=Bory%20B%C3%BDvanie&search_type=keyword_unordered)
- FB stránka (overenie identity): [facebook.com/Borybyvanie](https://www.facebook.com/Borybyvanie) → v Ad Library hľadať podľa názvu stránky

### Slnečnice / CRESCO

- [Slnečnice](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=Slne%C4%8Dnice&search_type=keyword_unordered)
- [CRESCO Slnečnice](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=CRESCO%20Slne%C4%8Dnice&search_type=keyword_unordered)
- FB stránka developera: [facebook.com/crescorealestatesk](https://www.facebook.com/crescorealestatesk)

### Voliteľne (materská značka)

- [Penta Real Estate](https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=SK&media_type=all&q=Penta%20Real%20Estate&search_type=keyword_unordered) — môže obsahovať aj nebytové kampane

Konfigurácia s rovnakými odkazmi: `config/meta_ads_competitors.yaml`.

---

## Postup v Ad Library (krok za krokom)

### A. Nastavenie filtrov

V ľavom paneli (alebo hornej lište):

| Pole | Hodnota |
|------|---------|
| Krajina | **Slovensko** (SK) |
| Stav reklamy | **Všetky** (pre históriu) alebo **Aktívne** (aktuálna ponuka) |
| Typ médií | Všetky |
| Dátum | Posledných 12 mesiacov (ak UI ponúka) |

Pre komerčné reklamy v EÚ/SK platí: vidíte reklamy **doručené na Slovensko** za posledný rok ([dokumentácia](https://www.facebook.com/ads/library/api/)).

### B. Nájdenie správnej stránky (Page)

1. Zadajte kľúčové slovo alebo názov projektu.
2. Kliknite na **názov stránky** inzerenta (nie len na kreatívu).
3. Zvoľte **„Zobraziť všetky reklamy“** / *See all ads from this Page*.
4. Do `config/meta_ads_competitors.yaml` doplňte `page_id` (z URL, parameter `view_all_page_id=…`).

### C. Čo skopírovať do CSV (jeden riadok = jeden inzerát)

| Stĺpec | Kde to nájdete |
|--------|----------------|
| `ad_library_id` | V detaile inzerátu / URL (ID knižnice) |
| `ad_status` | Aktívna / Neaktívna |
| `start_date`, `end_date` | „Spustené“, „Naposledy aktívne“ |
| `platforms` | Facebook, Instagram, … |
| `primary_text` | Hlavný text reklamy |
| `headline`, `link_description` | Ak sú zobrazené |
| `landing_url` | Cieľová URL (yit.sk, borybyvanie.sk, …) |
| `snapshot_url` | Odkaz „Zobraziť v knižnici“ / share |
| `format_notes` | video / carousel / statický |
| `segment_guess` | 1–1.5 / 2 / 3 / 4+ izby (odhad z textu) |
| `topic_tags` | hypotéka, 10/90, posledné byty, Ružinov, … |
| `opportunity_risk_notes` | Vaša poznámka pre insight |

Šablóna: `data/raw/meta_ads/manual/ads_template.csv`.

### D. Tagovanie (pre neskoršie trendy)

Odporúčané hodnoty v `topic_tags` (čiarkou oddelené):

- `financovanie` — hypotéka, 10/90, splátka, úrok
- `urgentnost` — posledné byty, limitovaná ponuka
- `lokalita` — Ružinov, Petržalka, Bory, Slnečnice
- `cena` — €/m², od X €, zľava
- `brand` — employer / firemná značka (nie priamy predaj bytu)
- `launch` — nová etapa, predpredaj

---

## Čo sledovať (príležitosti / riziká)

Po vyplnení CSV si v Exceli / Numbers spravte pivot alebo ručne spočítajte:

| Signál | Príležitosť | Riziko |
|--------|-------------|--------|
| Konkurent má 0 aktívnych reklám, vy máte ponuku | Menej tlaku na SOV | — |
| Nárast aktívnych reklám za 2 týždne | — | Agresívna mediálna fáza |
| Opakovaný angle (hypotéka, 10/90) u 2+ konkurentov | Trh testuje financovanie | NUPPU musí mať jasnú odpoveď v kreatíve |
| Dlhý beh (>30 dní) rovnakej kreatívy | Pravdepodobne funguje — inšpirácia formátu | Konkurent našiel winning message |
| Kampane na 2-izbové + váš segment 2 izby slabý v ponuke | Doplniť messaging / cenu v segmente | Strata entry buyers |
| Nová landing URL / nový projekt v texte | Sledovať ponuku na webe (`python -m etl.fetch_all`) | Launch konkurencie |

Spojenie s cenami z demo: [yit-compare-demo.vercel.app](https://yit-compare-demo.vercel.app/) — záložka **Insighty (NUPPU)** + tabuľka bytov.

---

## Obmedzenia manuálneho režimu

- Ad Library **neukáže** CTR, konverzie ani presný rozpočet (pri bežných komerčných reklamách).
- Keyword search môže zachytiť **sponzorované príspevky iných značiek** s podobným slovom — vždy filtrujte podľa **Page**.
- Nie každý developer cieli Meta reklamy na SK; prázdny výsledok ≠ žiadny marketing (môžu ísť Google, billboards, RK).

---

## Ďalší krok (automatizácia)

Keď budete mať `page_id` pre každú stránku v `config/meta_ads_competitors.yaml`, dá sa pridať `etl/fetch_meta_ads.py` (Ad Library API) a diff oproti predchádzajúcemu CSV.

---

## Súbory

```
config/meta_ads_competitors.yaml   # odkazy a search queries
data/raw/meta_ads/manual/
  ads_template.csv                 # hlavička CSV
  ads_YYYY-MM-DD.csv               # váš export (vytvoríte)
  screenshots/<slug>/              # voliteľné
docs/META_ADS_MANUAL.md            # tento návod
```
