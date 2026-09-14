#!/usr/bin/env python3
"""
gsc_report.py — pull Google Search Console data for fruitotl.com and list concrete optimisation opportunities.

    python3 scripts/gsc_report.py [days]      (default 28)

Writes data/gsc.json (raw) and data/gsc-opportunities.md (what the weekly job should act on):
  1. CTR fixes   — pages with >= 50 impressions and CTR below the expected CTR for their position -> rewrite title/description
  2. Near wins   — queries at position 5–20 with >= 20 impressions -> strengthen the ranking page (FAQ, H2, internal links)
  3. Gaps        — queries with >= 10 impressions where no page's title contains the main words -> candidate new article
Uses the service-account key ~/.claude/secrets/gsc-fruitoftheloom.json (must be an owner/user of the fruitotl.com property).
Exits 0 with a message (no crash) when the property is not accessible yet.
"""
import os, sys, json, re, glob, datetime as dt, warnings
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.path.expanduser("~/.claude/secrets/gsc-fruitoftheloom.json")
SITES = ["sc-domain:fruitotl.com", "https://fruitotl.com/"]
days = int(sys.argv[1]) if len(sys.argv) > 1 else 28
end = dt.date.today() - dt.timedelta(days=2); start = end - dt.timedelta(days=days)
EXPECTED_CTR = {1: .28, 2: .15, 3: .10, 4: .07, 5: .05, 6: .04, 7: .03, 8: .025, 9: .02, 10: .018}

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    api = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    have = {s["siteUrl"] for s in api.sites().list().execute().get("siteEntry", [])}
except Exception as e:
    print(f"gsc: cannot connect ({str(e)[:120]}) — skipping"); sys.exit(0)
site = next((s for s in SITES if s in have), None)
if not site:
    print("gsc: fruitotl.com property not accessible to the service account yet — skipping"); sys.exit(0)

def q(dims, extra=None):
    rows, start_row = [], 0
    while True:
        body = {"startDate": str(start), "endDate": str(end), "dimensions": dims, "rowLimit": 25000, "startRow": start_row}
        if extra: body.update(extra)
        got = api.searchanalytics().query(siteUrl=site, body=body).execute().get("rows", [])
        rows += got
        if len(got) < 25000: return rows
        start_row += len(got)

pages = q(["page"]); queries = q(["query"]); pq = q(["page", "query"])
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump({"site": site, "from": str(start), "to": str(end), "pages": pages, "queries": queries, "page_query": pq},
          open(os.path.join(ROOT, "data", "gsc.json"), "w"), ensure_ascii=False)

titles = {}
for f in glob.glob(os.path.join(ROOT, "content", "*", "articles", "*.json")):
    d = json.load(open(f, encoding="utf-8")); titles[d["title"].lower()] = f
def covered(query):
    words = [w for w in re.findall(r"\w+", query.lower()) if w not in {"fruit", "of", "the", "loom", "de", "la", "le", "der", "die", "und", "en", "i", "w", "na"} and len(w) > 2]
    return not words or any(all(w in t for w in words) for t in titles)

lines = [f"# Search Console opportunities — {site} ({start} → {end})", ""]
tot_c = sum(r["clicks"] for r in pages); tot_i = sum(r["impressions"] for r in pages)
lines += [f"Total: {tot_c:.0f} clicks, {tot_i:.0f} impressions", "", "## 1. CTR fixes (rewrite title + description)"]
for r in sorted(pages, key=lambda r: -r["impressions"]):
    pos = max(1, min(10, round(r["position"]))); exp = EXPECTED_CTR.get(pos, .01)
    if r["impressions"] >= 50 and r["ctr"] < exp * 0.7:
        lines.append(f"- {r['keys'][0]} — {r['impressions']:.0f} impr, CTR {r['ctr']*100:.1f}% (expected ~{exp*100:.0f}%), pos {r['position']:.1f}")
lines += ["", "## 2. Near wins (position 5–20: strengthen page)"]
for r in sorted(pq, key=lambda r: -r["impressions"]):
    if 5 <= r["position"] <= 20 and r["impressions"] >= 20:
        lines.append(f"- \"{r['keys'][1]}\" → {r['keys'][0]} — {r['impressions']:.0f} impr, pos {r['position']:.1f}")
lines += ["", "## 3. Gaps (no dedicated page yet — candidate new articles)"]
for r in sorted(queries, key=lambda r: -r["impressions"]):
    if r["impressions"] >= 10 and not covered(r["keys"][0]):
        lines.append(f"- \"{r['keys'][0]}\" — {r['impressions']:.0f} impr, pos {r['position']:.1f}")
open(os.path.join(ROOT, "data", "gsc-opportunities.md"), "w").write("\n".join(lines) + "\n")
print(f"gsc: {tot_c:.0f} clicks / {tot_i:.0f} impressions — opportunities in data/gsc-opportunities.md")
