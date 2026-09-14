#!/usr/bin/env python3
"""
indexnow.py — tell Bing / Yandex / Seznam / Naver (IndexNow) which URLs changed.
Bing's index also feeds ChatGPT search and Copilot, so this matters for GEO.

    python3 scripts/indexnow.py            # URLs whose <lastmod> in docs/sitemap.xml is today
    python3 scripts/indexnow.py --all      # every URL in the sitemap (use once after launch)
    python3 scripts/indexnow.py URL ...    # specific URLs

The key file docs/<key>.txt must be live on https://fruitotl.com/ before pinging.
"""
import os, sys, re, json, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = open(os.path.join(ROOT, "scripts", ".indexnow-key")).read().strip()
HOST = "fruitotl.com"
TODAY = datetime.date.today().isoformat()

def sitemap_urls(only_today):
    xml = open(os.path.join(ROOT, "docs", "sitemap.xml"), encoding="utf-8").read()
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1)
        lm = re.search(r"<lastmod>(.*?)</lastmod>", block)
        if not only_today or (lm and lm.group(1) == TODAY):
            out.append(loc)
    return out

args = sys.argv[1:]
if args == ["--all"]:
    urls = sitemap_urls(False)
elif args:
    urls = args
else:
    urls = sitemap_urls(True)
if not urls:
    print("indexnow: nothing changed today"); sys.exit(0)

body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"indexnow: {r.status} for {len(urls)} URLs")
except urllib.error.HTTPError as e:
    print(f"indexnow: HTTP {e.code} {e.read()[:200]!r} for {len(urls)} URLs"); sys.exit(1)
