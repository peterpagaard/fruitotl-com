# Topic backlog — new articles for the automation

The scheduled job takes the FIRST unchecked line, writes it as a new article (EN first, then every language that
already has a site.json), and changes `[ ]` to `[x]` with the date. Keys must be new, lowercase, hyphens only.
Each new article gets `order` = highest existing order + 1. Research facts with WebFetch; follow CONTENT-BRIEF.md.

**Priority: commercial search intent** — people who want to BUY Fruit of the Loom cheaply, in bulk, or for printing.
Every article must answer "what does it cost for N pieces" with a concrete table (1 / 10 / 50 / 100 / 250 pcs)
using Marmalade Co. prices incl. the 5 % (3+) and 10 % (5+) quantity discounts and €7 shipping.
When Search Console data exists (see scripts/gsc_report.py), topics with real impressions go to the TOP of this list.

## Bulk & wholesale (highest priority)
- [x] (2026-09-15) `wholesale` — Fruit of the Loom wholesale in Europe: who can buy wholesale, minimums, VAT, cheapest route for small businesses
- [ ] `bulk-hoodies` — Buying hoodies in bulk (10–500 pcs): price per piece, colours, sizes mix, delivery time
- [ ] `price-per-100` — What do 100 Fruit of the Loom t-shirts cost? Full price breakdown blank vs printed
- [ ] `blank-t-shirts` — Blank t-shirts for printing: best Fruit of the Loom blanks and where to buy them cheap
- [ ] `event-t-shirts` — T-shirts for events and festivals: quantities, colours, lead times, cost per guest

## Print & custom
- [ ] `custom-hoodies-cheap` — Cheap custom printed hoodies: blank + print cost, minimum orders, DIY vs print shop
- [ ] `screen-print-vs-dtg` — Screen printing vs DTG vs vinyl vs embroidery: price per piece at 10, 50, 250 pcs
- [ ] `print-on-demand` — Print on demand with Fruit of the Loom blanks: margins, when bulk buying beats POD
- [ ] `diy-printing` — DIY printing at home (iron-on, vinyl, screen kit) on Fruit of the Loom tees
- [ ] `sports-club-kit` — Sports club and training kit with logo: tees, hoodies, joggers — cost per player
- [ ] `staff-uniform-restaurant` — Staff t-shirts and polos for cafés, restaurants and shops
- [ ] `hen-party-shirts` — Hen / stag party t-shirts: ordering printed tees cheaply for groups
- [ ] `festival-merch` — Band & festival merch on a budget: blanks, print methods, minimum quantities
- [ ] `charity-run-shirts` — Charity-run t-shirts: cheapest way to kit out participants

## Cheap / comparison
- [ ] `vs-b-and-c` — Fruit of the Loom vs B&C: quality, fit, price and print results
- [ ] `vs-stanley-stella` — Fruit of the Loom vs Stanley/Stella: conventional vs organic, price per piece
- [ ] `vs-russell` — Fruit of the Loom vs Russell: sweats and polos compared
- [ ] `white-t-shirt` — Best plain white t-shirt 2026: see-through test, weight, price per piece
- [ ] `black-hoodie` — Best black hoodie under €25: colour fastness, weight, price
- [ ] `hoodie-vs-sweatshirt` — Hoodie vs crewneck: which to buy, weights and prices compared
- [ ] `cotton-weights-explained` — g/m² explained: 145, 165, 195 and 280 g/m² for tees and sweats

## Fit & care
- [ ] `plus-size` — Fruit of the Loom in 3XL–5XL: models, measurements, where to buy
- [ ] `womens-fit` — Lady-Fit vs unisex: sizing and prices
- [ ] `oversized-hoodie` — How to get an oversized fit (size up, which models, measurements)
- [ ] `care-guide` — Washing Fruit of the Loom so it doesn't shrink or pill (incl. printed items)
- [ ] `school-uniform-basics` — PE kit and uniform basics: which items and sizes

## Seasonal (only publish in season)
- [ ] `christmas-jumper-diy` — DIY Christmas sweatshirt with print (publish Oct–Nov)
- [ ] `back-to-school` — Back-to-school basics on a budget (publish Jul–Aug)
- [ ] `summer-event-tees` — Lightweight event tees for summer heat (publish Apr–Jun)
