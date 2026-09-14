#!/usr/bin/env python3
"""
update_prices.py — refresh content/prices.json from marmaladeco.com product pages (JSON-LD offers).

    python3 scripts/update_prices.py          # update prices, print changes
Prices are the LOWEST in-stock-or-not variant price in EUR incl. VAT. Quantity discounts and shipping are
shop-wide rules kept in prices.json ("discounts", "shipping_eur"); re-check them by hand if the shop changes them.
Never fails the pipeline: a product whose page can't be parsed keeps its old price and is reported.
"""
import os, re, json, datetime, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "content", "prices.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

DEFAULT = {
  "currency": "EUR", "shipping_eur": 7.0,
  "discounts": [{"min_qty": 3, "pct": 5}, {"min_qty": 5, "pct": 10}],
  "quantities": [1, 10, 50, 100, 250],
  "products": [
    {"id": "t-shirt",      "path": "/products/fruit-of-the-loom-t-shirt",               "price": 6.95},
    {"id": "v-neck",       "path": "/products/fruit-of-the-loom-v-neck-t-shirt",        "price": 6.95},
    {"id": "long-sleeve",  "path": "/products/fruit-of-the-loom-langaermet-t-shirt",    "price": 8.95},
    {"id": "tank-top",     "path": "/products/fruit-of-the-loom-tank-top-herre",        "price": 5.95},
    {"id": "polo",         "path": "/products/fruit-of-the-loom-original-poloshirt",    "price": 10.95},
    {"id": "shorts",       "path": "/products/fruit-of-the-loom-shorts",                "price": 9.95},
    {"id": "sweatshirt",   "path": "/products/fruit-of-the-loom-crewneck-sweatshirt",   "price": 16.95},
    {"id": "sweatpants",   "path": "/products/fruit-of-the-loom-sweatpants-med-elastik","price": 16.95},
    {"id": "hoodie",       "path": "/products/fruit-of-the-loom-hoodie",                "price": 20.95},
    {"id": "zip-hoodie",   "path": "/products/fruit-of-the-loom-zip-hoodie",            "price": 27.95}
  ]
}

def fetch_price(path):
    html = urllib.request.urlopen(urllib.request.Request("https://marmaladeco.com" + path, headers=UA), timeout=25).read().decode("utf-8", "ignore")
    prices = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try: d = json.loads(m.group(1))
        except Exception: continue
        def walk(x):
            if isinstance(x, dict):
                if x.get("@type") == "Offer" and x.get("priceCurrency") == "EUR" and x.get("price") not in (None, ""):
                    prices.append(float(x["price"]))
                for v in x.values(): walk(v)
            elif isinstance(x, list):
                for v in x: walk(v)
        walk(d)
    return min(prices) if prices else None

data = json.load(open(P)) if os.path.exists(P) else DEFAULT
changes, failed = [], []
for pr in data["products"]:
    try: new = fetch_price(pr["path"])
    except Exception as e: new = None
    if new is None: failed.append(pr["id"]); continue
    if abs(new - pr["price"]) > 0.001: changes.append(f"{pr['id']}: {pr['price']} -> {new}")
    pr["price"] = round(new, 2)
data["checked"] = datetime.date.today().isoformat()
json.dump(data, open(P, "w"), indent=2)
print("prices:", "; ".join(changes) if changes else "no changes", ("| FAILED: " + ", ".join(failed)) if failed else "")
