# fruitotl.com

Uafhængig, flersproget SEO/GEO-guide om Fruit of the Loom i Europa. International søster til fruitoftheloom.dk.
Alle links leder videre til **marmaladeco.com** (Marmalade Co.) med UTM-sporing.

## Sådan hænger det sammen

```
content/languages.json          hvilke sprog der bygges (rækkefølge = sprogvælger)
content/<lang>/site.json        forside + alle UI-tekster for ét sprog
content/<lang>/articles/*.json  én artikel pr. fil (samme "key" på tværs af sprog)
assets/                         logo, favicon, og-billeder (kopieres til docs/)
build.py                        genererer hele sitet til docs/ (GitHub Pages)
scripts/bump_dates.py           freshness: sæt date_modified = i dag på udvalgte artikler
scripts/make_og.py              genererer og-image-<lang>.png
CONTENT-BRIEF.md                fakta, regler og JSON-skema for alt indhold (læs den før du skriver)
docs/                           FÆRDIGT SITE — genereres, ret aldrig i hånden
```

Sprog: en (rod), de, nl, fr, es, it, pl, pt, fi. Hvert sprog ligger i sin egen mappe (`/de/`, `/nl/` …), engelsk ligger i roden og er `x-default`.
Alle sider har hreflang-links til hinanden, sitemap.xml med alternates, robots.txt der tillader AI-crawlere, og llms.txt (rod + pr. sprog).

## Byg

```bash
python3 build.py --check   # valider indhold uden at skrive noget
python3 build.py           # byg docs/
```

Bygget fejler hårdt (exit 1) ved: ugyldig JSON, manglende felter, ukendte `{{LINK:…}}`-nøgler, døde interne links, uopløste placeholders.

## Deploy

GitHub Pages fra `main`, mappen `/docs`. Push til `main` = live inden for ca. 1 minut.
Custom domain: `fruitotl.com` (`docs/CNAME` skrives automatisk af build.py).

## Ny artikel

1. Skriv `content/en/articles/<key>.json` efter skemaet i CONTENT-BRIEF.md.
2. Lav samme `key` i alle andre sprog (lokaliseret `slug`, ikke ord-for-ord oversættelse).
3. `python3 build.py` → commit → push.

Artikler uden oversættelse i et sprog udelades bare fra det sprogs hreflang/sitemap — sitet bygger stadig.

## Automatik

Planlagt opgave `fruitotl-weekly` (Claude scheduled task, hver tirsdag kl. 10:08, kører når Claude-appen er åben):
1. udfylder manglende oversættelser (maks 8 filer pr. kørsel),
2. når alle sprog er komplette: skriver én ny artikel fra `TOPIC-BACKLOG.md` på alle sprog,
3. bumper `date_modified` på de 4 ældste artikler, bygger, validerer, pusher og tjekker det live site,
4. sender en kort dansk rapport.

Nye emner: tilføj en linje i `TOPIC-BACKLOG.md`.
