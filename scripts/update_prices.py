#!/usr/bin/env python3
"""
update_prices.py — refresh every content/prices*.json from its shop's product pages (JSON-LD offers).

    python3 scripts/update_prices.py
prices.json     -> marmaladeco.com (EUR)   used by en, de, nl, fr, es, it, pl, pt, fi
prices-sv.json  -> marmalade.se   (SEK)   used by sv
Price = LOWEST variant price in the file's currency, incl. VAT. Discount tiers and shipping rules are shop-wide
settings kept in each file; re-check them by hand if a shop changes them.
Never fails the pipeline: a product whose page can't be parsed keeps its old price and is reported.
"""
import os, re, json, glob, datetime, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

class _Follow308(urllib.request.HTTPRedirectHandler):
    # Python 3.9's urllib does not follow 308 (marmaladeco.com redirects
    # Danish product handles to English ones with 308 since Oct 2026).
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_302(req, fp, 302, msg, headers)

_opener = urllib.request.build_opener(_Follow308)

def fetch_price(shop, path, cur):
    html = _opener.open(urllib.request.Request(shop + path, headers=UA), timeout=25).read().decode("utf-8", "ignore")
    prices = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try: d = json.loads(m.group(1))
        except Exception: continue
        def walk(x):
            if isinstance(x, dict):
                if x.get("@type") == "Offer" and x.get("priceCurrency") == cur and x.get("price") not in (None, ""):
                    prices.append(float(x["price"]))
                for v in x.values(): walk(v)
            elif isinstance(x, list):
                for v in x: walk(v)
        walk(d)
    return min(prices) if prices else None

for P in sorted(glob.glob(os.path.join(ROOT, "content", "prices*.json"))):
    data = json.load(open(P))
    shop, cur = data.get("shop", "https://marmaladeco.com"), data.get("currency", "EUR")
    changes, failed = [], []
    for pr in data["products"]:
        try: new = fetch_price(shop, pr["path"], cur)
        except Exception: new = None
        if new is None: failed.append(pr["id"]); continue
        if abs(new - pr["price"]) > 0.001: changes.append(f"{pr['id']}: {pr['price']} -> {new}")
        pr["price"] = round(new, 2)
    data["checked"] = datetime.date.today().isoformat()
    json.dump(data, open(P, "w"), indent=2)
    print(f"{os.path.basename(P)} ({cur}):", "; ".join(changes) if changes else "no changes", ("| FAILED: " + ", ".join(failed)) if failed else "")
