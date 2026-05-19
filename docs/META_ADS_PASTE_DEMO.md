# Rýchle demo: copy-paste z Meta Ad Library

Žiadny CSV. Otvoríte 4 odkazy → skopírujete obsah stránky → vložíte do chatu (alebo sem do súboru) → vygenerujeme trendy / príležitosti / riziká.

## Odkazy (SK, aktívne reklamy — ako pri Bory)

1. **Bory** — https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=SK&media_type=all&q=Bory%20B%C3%BDvanie&search_type=keyword_unordered  
2. **YIT / NUPPU** — https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=SK&media_type=all&q=YIT%20Slovakia&search_type=keyword_unordered  
3. **Green Atrium** — https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=SK&media_type=all&q=Green%20Atrium&search_type=keyword_unordered  
4. **Slnečnice / CRESCO** — https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=SK&media_type=all&q=Slne%C4%8Dnice&search_type=keyword_unordered  

**Tip:** Po otvorení kliknite na správnu **stránku** (Page) → „Zobraziť všetky reklamy“ → potom kopírujte (menej odpadu).

## Ako kopírovať (30–60 s / firma)

1. Na stránke: `Cmd+A` → `Cmd+C` (celá stránka), alebo označte len zoznam reklám.  
2. Ak je veľa reklám: raz scroll dole, znova `Cmd+A` → `Cmd+C` (stačí prvá obrazovka + scroll).  
3. Vložte do chatu pod hlavičku `### BORY` atď. (šablóna nižšie).

## Šablóna na vloženie (4 bloky)

Skopírujte tento skeleton a nahraďte obsah pod každou hlavičkou:

```
### BORY
Počet reklám (odhad z UI): 
Poznámka (voliteľné):

[paste z Ad Library]

### YIT
Počet reklám: 

[paste]

### GREEN_ATRIUM
Počet reklám: 

[paste]

### SLNECNICE
Počet reklám: 

[paste]
```

## Čo z toho dostanete

- Porovnanie **intenzity** (kto koľko aktívnych reklám)  
- **Messaging** — hypotéka, 10/90, posledné byty, lokality, segment izieb  
- **Príležitosti** pre NUPPU (voči [demo dashboardu](https://marketing-intelligence-radar-nuppu.vercel.app/))  
- **Riziká** — agresívna komunikácia, launch signály  
- Voliteľne: návrh 3–5 bulletov do prezentácie / Slacku  

## Obmedzenia

- Paste môže obsahovať šum z UI (menu, pätička) — to nevadí.  
- Ak je výsledok prázdny, napíšte „0 reklám“ — to je tiež insight.  
- Zoradenie podľa `total_impressions` pri komerčných reklamách často nefunguje — ignorujte.
