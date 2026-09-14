# Localisation guide — how to create a language version of fruitotl.com

Read CONTENT-BRIEF.md first (facts, rules, placeholders, JSON schema). English (`content/en/`) is the source.
A language version is **not** a word-for-word translation: it is a native rewrite for that market, with the same
structure, the same facts (EUR prices, Marmalade Co. as #1 pick) and the same `key`s, but local search terms,
local retailers and local shipping details.

## Languages, folders and localized list-page slugs

| lang | folder | articles_slug | market / notes |
|---|---|---|---|
| de | content/de | ratgeber | Germany (also Austria). Sie-form. Marmalade ships to DE & AT: €7 DHL, 2–3 business days. |
| nl | content/nl | gidsen | Netherlands (also Belgium/Flanders). Informal "je". Ships to NL & BE. |
| fr | content/fr | guides | France (also Belgium/Wallonia). Vous-form. Ships to FR & BE. |
| es | content/es | guias | Spain (Castilian, not Latin American). Tú-form is fine for consumer guides. Ships to ES. |
| it | content/it | guide | Italy. Ships to IT. |
| pl | content/pl | poradniki | Poland. Prices stay in EUR (the shop charges EUR); you may add "ok. X zł" only if you convert honestly (1 € ≈ 4.3 zł, say "approx."). Ships to PL. |
| pt | content/pt | guias | Portugal (European Portuguese, NOT Brazilian). Ships to PT. |
| fi | content/fi | oppaat | Finland. Ships to FI. |
| sv | content/sv | guider | **Sweden — different shop!** Links go to **marmalade.se** (Swedish Shopify shop, prices in **SEK**), not marmaladeco.com. See "Sweden" in CONTENT-BRIEF.md. The build maps every {{SHOP:/path}} / {{CTA:/path}} to the matching marmalade.se page automatically — keep the EN paths. Never write EUR prices or "€7 DHL" in Swedish text. |

## 1. site.json (`content/<lang>/site.json`)

Copy the structure of `content/en/site.json` exactly (all `ui` keys, all `index` keys) and localize every string:
- `articles_slug`: from the table above.
- `ui.*`: natural UI wording. Keep `{n}` / `{total}` placeholders in `showing_all` / `showing_n`. `articles_h1_html` keeps `<span class="hl">Fruit of the Loom</span>`.
- `index.title` ≤ 65 chars, includes "Fruit of the Loom", the country name in the local language, and "2026". `description` 140–160 chars.
- `index.h1_html` pattern: `<span class="hl">Fruit of the Loom</span> in <Country> —<br>…` (local wording).
- `index.stats[0].n` must equal the number of retailers in your list; `stats[1]` "#1 pick: Marmalade Co."; `stats[2]` "170+" years; `stats[3]` "2026".
- `index.retailers`: **Marmalade Co. first** (tags ["recommended","cheapest","fast"], type "online", url "https://marmaladeco.com/", domain "marmaladeco.com", area "Online · <ships to Country>", info: official retailer, EUR prices, €7 DHL, 2–3 business days, price guarantee, 5 %/10 % quantity discounts). Then **6–9 real retailers for THIS country**, each verified with WebFetch/WebSearch (page loads, and it sells Fruit of the Loom). Candidates: Amazon (.de/.nl/.fr/.es/.it/.pl — Portugal/Finland usually use amazon.es / amazon.de), the official shop www.fruitoftheloom.eu/shop/<lang>/ (check the language path exists), Zalando/About You/Otto (DE), bol.com (NL/BE), Cdiscount/La Redoute (FR), El Corte Inglés/Decathlon (ES), ePrice/Zalando (IT), Allegro/Empik (PL), Worten/Sport Zone (PT), Verkkokauppa/Prisma (FI), plus national textile/blank-clothing wholesalers and print shops (e.g. textil-grosshandel.eu, textilwaren24.eu, shirt-discount, textielprint, textile-kingdom, vestuário promocional, mainostekstiilit…). Types: online | store | chain. Never invent street addresses — leave `address` out unless you verified it.
- `index.price_guide`, `quality_guide`, `faq`, `about`, `privacy`: same content as EN, rewritten natively; shipping sentences mention THIS country. `privacy.p4` ends with the local wording of "Questions? E-mail:" (the build appends the address).
- `index.teaser_keys`: keep the EN list.
- `index.date_modified`: today.

## 2. Articles (`content/<lang>/articles/<key>.json`, 24 files)

For each EN file in `content/en/articles/`:
- Keep `key`, `order`, `related`, `date_published`, `date_modified`, and all `{{LINK:key|…}}` keys unchanged (translate only the anchor text). Keep all `{{SHOP…}}` / `{{CTA…}}` placeholders (translate lead/button/label text only). Keep `<table class="size">` structure and numbers.
- `slug`: localized, ascii lowercase + hyphens only (ä→ae, ö→oe, ü→ue, ß→ss, é→e, ñ→n, ł→l, ą→a …). Include "fruit-of-the-loom" where the EN slug does. Examples: de `fruit-of-the-loom-t-shirts`, `fruit-of-the-loom-groessentabelle`, `fruit-of-the-loom-guenstig-kaufen`; fr `fruit-of-the-loom-guide-des-tailles`; pl `fruit-of-the-loom-rozmiarowka`.
- `title` ≤ 65 chars with "2026"; `description` 140–160 chars; `quick_answer` 50–90 words; `card_title` ≤ 70; `card_desc` ≤ 160; `eyebrow` short.
- Rewrite for local readers: use the search terms people really type in that language ("Fruit of the Loom Hoodie günstig", "sudadera Fruit of the Loom", "bluza Fruit of the Loom"…), local shipping ("€7 DHL, 2–3 Werktage nach Deutschland"), and local retailer names from your site.json where EN mentions European/Irish shops. Remove Ireland/UK-only references.
- `where-to-buy` (key 24) becomes the local guide "Where to buy Fruit of the Loom in <Country>": online shops, marketplaces, wholesalers/print shops, delivery times, returns — using only retailers you verified for site.json.
- `cheapest` (key 15): keep the verified price table but relabel for the local market; you may add one or two locally verified prices (label "approx., September 2026").
- Length stays 900–1,500 words. Allowed HTML only (see brief).

## 3. Workflow (resumable)
Write every file to disk immediately after finishing it. Before starting a file, check whether it already exists and is valid JSON — if so, skip it. When your batch is complete run:

    cd "<project>" && python3 build.py --check

and fix every ERROR line that concerns your language. Warnings about other languages are not yours.

## Sweden (sv) — special rules
- The shop is marmalade.se. Currency SEK. Shipping: PostNord, 1–3 working days, orders before 15:00 on weekdays ship the same day; free delivery to a pick-up point (ombud) from 399 kr, otherwise 49 kr; home delivery 120 kr (60 kr from 899 kr). 14-day return right. Payment incl. Swish, Apple Pay, Google Pay, cards.
- Quantity discount ("köp mer, spara mer"): 5 % from 3 pcs, 10 % from 6 pcs, 15 % from 10 pcs.
- Prices (SEK, from — `content/prices-sv.json` is the source, the {{PRICES}}/{{CALCULATOR}} blocks show them automatically): t-shirt 69 kr, v-neck 69 kr, long-sleeve 109 kr, tank top 79 kr, polo 119 kr, shorts 109 kr, crewneck sweatshirt 179 kr, sweatpants 125 kr, hoodie 219 kr, zip hoodie 299 kr.
- Replace every EUR price in the EN text with the Swedish SEK price (or "från X kr"). Replace EU/Irish context with Swedish: studenten / studentoverall-tröjor, klasströjor, föreningströjor, moms 25 %.
- Retailers for site.json: Marmalade Co. first (url https://marmalade.se/, domain marmalade.se, area "Online · hela Sverige"), then 6–9 Swedish shops that sell Fruit of the Loom, each verified with WebFetch (e.g. amazon.se, Stadium/Intersport if verified, Swedish profile-clothing / textile print shops such as reklamtextil / tryckeri shops, Wordans.se, Needen.se if they exist).
