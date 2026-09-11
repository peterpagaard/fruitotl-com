#!/usr/bin/env python3
"""
bump_dates.py — freshness helper used by the bi-weekly automation.

    python3 scripts/bump_dates.py t-shirts hoodies cheapest      # bump these keys in ALL languages
    python3 scripts/bump_dates.py --set A                          # rotating set A
    python3 scripts/bump_dates.py --set B                          # rotating set B
    python3 scripts/bump_dates.py --oldest 5                       # the 5 keys with the oldest date_modified

Sets date_modified = today (YYYY-MM-DD) in content/<lang>/articles/<key>.json for every language,
and bumps index.date_modified in every site.json when --index is passed. Never touches date_published.
"""
import json, os, sys, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
TODAY = datetime.date.today().isoformat()
SETS = {
    "A": ["cheapest", "cheap-tshirts", "cheap-hoodies", "printing", "t-shirts"],
    "B": ["hoodies", "team-hoodies", "workwear", "tracksuit", "size-guide"],
    "C": ["sweatshirts", "sweatpants", "quality", "vs-gildan", "where-to-buy"],
}

def all_articles():
    out = {}
    for f in glob.glob(os.path.join(CONTENT, "*", "articles", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        out.setdefault(d["key"], []).append((f, d))
    return out

def main():
    args = sys.argv[1:]
    arts = all_articles()
    keys, bump_index = [], False
    if "--index" in args:
        bump_index = True; args.remove("--index")
    if args[:1] == ["--set"]:
        keys = SETS[args[1]]
    elif args[:1] == ["--oldest"]:
        n = int(args[1])
        oldest = sorted(arts.items(), key=lambda kv: min(d["date_modified"] for _, d in kv[1]))
        keys = [k for k, _ in oldest[:n]]
    else:
        keys = args
    if not keys:
        sys.exit(__doc__)
    touched = []
    for k in keys:
        if k not in arts:
            print(f"warn: key {k} not found"); continue
        for f, d in arts[k]:
            d["date_modified"] = TODAY
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            touched.append(os.path.relpath(f, ROOT))
    if bump_index:
        for f in glob.glob(os.path.join(CONTENT, "*", "site.json")):
            d = json.load(open(f, encoding="utf-8"))
            d["index"]["date_modified"] = TODAY
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            touched.append(os.path.relpath(f, ROOT))
    print(f"bumped date_modified -> {TODAY} in {len(touched)} files (keys: {', '.join(keys)})")

if __name__ == "__main__":
    main()
