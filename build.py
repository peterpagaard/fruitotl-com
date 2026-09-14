#!/usr/bin/env python3
"""
build.py — static site generator for fruitotl.com

Reads content/languages.json + content/<lang>/site.json + content/<lang>/articles/*.json
and writes a complete static site into docs/ (GitHub Pages root).

Usage:
    python3 build.py            # build everything
    python3 build.py --check    # validate content only, no output

Placeholders allowed inside any *_html / body_html / a_html / p_html string:
    {{SHOP}}                      -> marmaladeco.com front page with UTM (utm_content=inline)
    {{SHOP:/collections/x}}       -> marmaladeco.com/collections/x with UTM (utm_content=inline)
    {{SHOP|Label}} / {{SHOP:/path|Label}} -> full <a> tag (rel="nofollow sponsored") with that label
    {{CTA|Lead text|Button text}} -> highlighted CTA box linking to marmaladeco.com front page
    {{CTA:/path|Lead text|Button text}} -> same, deep link
    {{LINK:article-key|Anchor text}}    -> internal link to the localized article with that key
"""
import json, os, re, sys, html, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "docs")
DOMAIN = "https://fruitotl.com"
SHOP = "https://marmaladeco.com"
CHECK_ONLY = "--check" in sys.argv
TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------- helpers
def read_json(path):
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"JSON error in {path}: {e}")

def esc(s):
    return html.escape(str(s), quote=True)

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).replace("\n", " ").strip()

def jsonld(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

def shop_url(lang, path="/", content="inline"):
    path = path if path.startswith("/") else "/" + path
    sep = "&" if "?" in path else "?"
    return (f"{SHOP}{path}{sep}utm_source=fruitotl.com&utm_medium=referral"
            f"&utm_campaign=organic-{lang}&utm_content={content}")

def page_url(site, slug=""):
    d = site["dir"]
    base = f"{DOMAIN}/{d}/" if d else f"{DOMAIN}/"
    return base + slug

def rel_prefix(site):
    """path prefix from a page in this language dir back to site root"""
    return "../" if site["dir"] else ""

# ---------------------------------------------------------------- placeholders
def expand(text, lang, site, articles_by_key, ctx):
    if not isinstance(text, str):
        return text

    def cta(m):
        path = m.group(1) or "/"
        lead, btn = m.group(2), m.group(3)
        return (f'<div class="article-cta"><p>{lead}</p>'
                f'<a href="{shop_url(lang, path, "article-cta")}" rel="nofollow sponsored" '
                f'target="_blank" class="btn-red">{btn} →</a></div>')
    text = re.sub(r"\{\{CTA(?::([^|}]+))?\|([^|}]+)\|([^}]+)\}\}", cta, text)

    def shop(m):
        path = m.group(1) or "/"
        label = m.group(2)
        url = shop_url(lang, path, "inline")
        if label:
            return f'<a href="{url}" rel="nofollow sponsored" target="_blank">{label}</a>'
        return url
    text = re.sub(r"\{\{SHOP(?::([^|}]+))?(?:\|([^}]+))?\}\}", shop, text)

    def link(m):
        key, label = m.group(1), m.group(2)
        art = articles_by_key.get(key)
        if not art:
            (ctx["errors"] if lang == "en" else ctx["warnings"]).append(f"[{lang}] LINK key '{key}' has no article (yet)")
            return label
        return f'<a href="{art["slug"]}">{label}</a>'
    text = re.sub(r"\{\{LINK:([^|}]+)\|([^}]+)\}\}", link, text)

    if "{{" in text:
        ctx["errors"].append(f"[{lang}] unresolved placeholder near: {text[text.find('{{'):text.find('{{')+60]!r}")
    return text

# ---------------------------------------------------------------- CSS (shared, same look as fruitoftheloom.dk)
CSS_BASE = """
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
:root { --black:#111111; --white:#ffffff; --off-white:#f8f8f6; --border:#e5e5e0; --mid-gray:#888; --fruit-red:#CC2529; --fruit-green:#3A7D2C; --fruit-purple:#6B3FA0; --fruit-yellow:#E8C53A; }
html { scroll-behavior:smooth; }
body { font-family:'Jost',sans-serif; background:var(--white); color:var(--black); line-height:1.6; -webkit-font-smoothing:antialiased; }
header { background:var(--white); border-bottom:1px solid var(--border); position:sticky; top:0; z-index:100; }
.header-inner { max-width:1200px; margin:0 auto; padding:0 32px; height:68px; display:flex; align-items:center; justify-content:space-between; gap:16px; }
.logo { display:flex; align-items:center; gap:12px; text-decoration:none; color:var(--black); }
.logo-icon { height:44px; width:auto; flex-shrink:0; }
.logo-text { display:flex; flex-direction:column; line-height:1; }
.logo-text .brand { font-size:0.72rem; font-weight:800; letter-spacing:0.18em; text-transform:uppercase; }
.logo-text .sub { font-size:0.62rem; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--mid-gray); margin-top:3px; }
nav { display:flex; gap:28px; align-items:center; }
nav a { font-size:0.78rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--black); text-decoration:none; transition:color 0.2s; }
nav a:hover, nav a.active { color:var(--fruit-red); }
.lang-switch { position:relative; }
.lang-switch select { font-family:'Jost',sans-serif; font-size:0.72rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; border:1.5px solid var(--border); background:var(--white); padding:6px 10px; border-radius:3px; cursor:pointer; color:var(--black); }
.hero { background:var(--off-white); border-bottom:1px solid var(--border); padding:88px 32px 72px; text-align:center; }
.hero-eyebrow { font-size:0.7rem; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:var(--fruit-red); margin-bottom:22px; }
.hero h1 { font-size:clamp(1.9rem,4.5vw,3.2rem); font-weight:800; letter-spacing:-0.02em; line-height:1.08; text-transform:uppercase; max-width:900px; margin:0 auto 24px; }
.hero h1 .hl { color:var(--fruit-red); }
.hero p { font-size:1rem; color:#555; max-width:560px; margin:0 auto 40px; }
.fruit-dots { display:flex; justify-content:center; gap:10px; }
.fruit-dots span { width:11px; height:11px; border-radius:50%; display:block; }
.stat-bar { background:var(--black); color:var(--white); padding:20px 32px; }
.stat-bar-inner { max-width:1200px; margin:0 auto; display:flex; justify-content:center; gap:56px; flex-wrap:wrap; }
.stat { text-align:center; }
.stat-number { font-size:1.5rem; font-weight:800; color:var(--fruit-yellow); display:block; line-height:1; }
.stat-label { font-size:0.68rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; color:#aaa; margin-top:4px; display:block; }
.breadcrumb { max-width:1200px; margin:0 auto; padding:16px 32px; font-size:0.76rem; color:var(--mid-gray); font-weight:600; letter-spacing:0.06em; text-transform:uppercase; }
.breadcrumb a { color:var(--mid-gray); text-decoration:none; }
.breadcrumb a:hover { color:var(--fruit-red); }
.breadcrumb span { margin:0 8px; opacity:0.4; }
.intro { max-width:860px; margin:60px auto; padding:0 32px; }
.section-label { font-size:0.68rem; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:var(--fruit-green); margin-bottom:14px; }
.intro h2 { font-size:1.8rem; font-weight:800; letter-spacing:-0.01em; text-transform:uppercase; margin-bottom:20px; }
.intro p { color:#444; font-size:0.98rem; margin-bottom:16px; }
.intro strong { color:var(--black); }
.intro a, .seo-section a, .faq-item a, .about a { color:var(--fruit-red); font-weight:600; text-decoration:none; }
.intro a:hover, .seo-section a:hover, .faq-item a:hover, .about a:hover { text-decoration:underline; }
.top-pick { max-width:860px; margin:0 auto 60px; padding:0 32px; }
.top-pick-box { background:#fffbea; border:2px solid var(--fruit-yellow); border-radius:6px; padding:28px 32px; display:flex; align-items:flex-start; gap:20px; }
.top-pick-icon { font-size:2rem; line-height:1; flex-shrink:0; }
.top-pick-content h3 { font-size:1rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; }
.top-pick-content p { font-size:0.93rem; color:#555; margin-bottom:12px; }
.top-pick-content a.btn { display:inline-block; background:var(--black); color:var(--white); font-size:0.75rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; padding:10px 20px; text-decoration:none; border-radius:3px; transition:background 0.2s; }
.top-pick-content a.btn:hover { background:var(--fruit-red); }
.table-section { max-width:1200px; margin:0 auto 88px; padding:0 32px; }
.table-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; flex-wrap:wrap; gap:16px; }
.table-top h2 { font-size:1.5rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; }
#search { padding:10px 18px; border:1.5px solid var(--border); border-radius:3px; font-family:'Jost',sans-serif; font-size:0.85rem; font-weight:500; letter-spacing:0.04em; width:250px; outline:none; transition:border-color 0.2s; }
#search:focus { border-color:var(--black); }
#search::placeholder { color:#bbb; }
.supplier-count { font-size:0.72rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--mid-gray); margin-bottom:10px; }
table.retailers { width:100%; border-collapse:collapse; border:1.5px solid var(--border); }
table.retailers thead { background:var(--black); color:var(--white); }
table.retailers thead th { padding:14px 20px; text-align:left; font-size:0.68rem; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; }
table.retailers tbody tr { border-bottom:1px solid var(--border); transition:background 0.12s; }
table.retailers tbody tr:last-child { border-bottom:none; }
table.retailers tbody tr:hover { background:var(--off-white); }
table.retailers td { padding:17px 20px; font-size:0.92rem; vertical-align:top; }
table.retailers td:first-child { font-size:0.72rem; font-weight:700; letter-spacing:0.1em; color:var(--mid-gray); width:48px; padding-top:20px; }
table.retailers td strong { font-weight:700; display:block; margin-bottom:5px; }
.td-info { font-size:0.8rem; color:#666; line-height:1.5; max-width:380px; }
.td-address { font-size:0.75rem; color:#999; margin-top:4px; font-style:italic; }
.tags { margin-bottom:5px; }
.tag { display:inline-block; font-size:0.62rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:2px 8px; border-radius:2px; margin-right:4px; }
.tag-recommended { background:#fff3cd; color:#8a5c00; }
.tag-cheapest, .tag-lowprice { background:#e8f4e8; color:#2a6a2a; }
.tag-fast { background:#e8f0ff; color:#2a50a0; }
.tag-store { background:#fce8f0; color:#a02060; }
td a.site-link { color:var(--fruit-red); text-decoration:none; font-weight:600; font-size:0.87rem; word-break:break-all; }
td a.site-link:hover { text-decoration:underline; }
.badge { font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:4px 10px; border-radius:2px; white-space:nowrap; }
.b-online { background:#e8f0ff; color:#2a50a0; }
.b-store { background:#fce8f0; color:#a02060; }
.b-chain { background:#ede8f7; color:#5a2fa0; }
.seo-section { max-width:860px; margin:0 auto 60px; padding:0 32px; }
.seo-section h2 { font-size:1.5rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin-bottom:18px; }
.seo-section h3 { font-size:1rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin:24px 0 10px; color:var(--black); }
.seo-section p { color:#444; font-size:0.97rem; margin-bottom:14px; }
.seo-section strong { color:var(--black); }
.faq { background:var(--off-white); border-top:1px solid var(--border); border-bottom:1px solid var(--border); padding:88px 32px; }
.faq-inner { max-width:860px; margin:0 auto; }
.faq h2 { font-size:1.5rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin-bottom:44px; }
.faq-item { border-bottom:1px solid var(--border); padding:26px 0; }
.faq-item:last-child { border-bottom:none; }
.faq-item h3 { font-size:0.95rem; font-weight:700; letter-spacing:0.04em; margin-bottom:10px; }
.faq-item p { color:#555; font-size:0.95rem; }
.faq-item strong { color:var(--black); }
.about { max-width:860px; margin:80px auto; padding:0 32px; }
.about h2 { font-size:1.5rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin-bottom:20px; }
.about h3 { font-size:1rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin:24px 0 10px; }
.about p { color:#444; font-size:0.97rem; margin-bottom:14px; }
.privacy { background:var(--off-white); border-top:1px solid var(--border); padding:64px 32px; }
.privacy-inner { max-width:820px; margin:0 auto; }
.privacy h2 { font-size:1.4rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin-bottom:20px; }
.privacy p { color:#555; font-size:0.92rem; margin-bottom:12px; }
.privacy a { color:var(--fruit-red); text-decoration:none; font-weight:600; }
.privacy a:hover { text-decoration:underline; }
.articles-teaser { background:var(--off-white); border-top:1px solid var(--border); padding:64px 32px; }
.articles-teaser-inner { max-width:1200px; margin:0 auto; }
.articles-teaser h2 { font-size:1.5rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin-bottom:12px; }
.articles-teaser > .articles-teaser-inner > p { color:#555; font-size:0.95rem; margin-bottom:32px; max-width:600px; }
.teaser-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:14px; margin-bottom:28px; }
.teaser-card { background:var(--white); border:1px solid var(--border); padding:20px; text-decoration:none; color:var(--black); transition:box-shadow 0.2s,border-color 0.2s; display:flex; flex-direction:column; gap:8px; }
.teaser-card:hover { box-shadow:0 4px 16px rgba(0,0,0,0.08); border-color:#ccc; }
.teaser-tag { font-size:0.6rem; font-weight:800; letter-spacing:0.16em; text-transform:uppercase; color:var(--fruit-red); }
.teaser-card strong { font-size:0.88rem; font-weight:700; line-height:1.4; }
.btn-all-articles { display:inline-block; font-size:0.75rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase; color:var(--white); background:var(--black); padding:12px 24px; text-decoration:none; transition:opacity 0.2s; }
.btn-all-articles:hover { opacity:0.8; }
footer { background:var(--black); color:#666; padding:44px 32px; }
.footer-inner { max-width:1200px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px; }
.footer-brand { font-size:0.68rem; font-weight:800; letter-spacing:0.2em; text-transform:uppercase; color:#aaa; }
.footer-langs { display:flex; gap:14px; flex-wrap:wrap; }
.footer-langs a { font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#777; text-decoration:none; }
.footer-langs a:hover, .footer-langs a.active { color:#fff; }
.footer-copy { width:100%; margin-top:24px; padding-top:24px; border-top:1px solid #222; font-size:0.72rem; letter-spacing:0.04em; text-align:center; color:#555; }
.quick-answer { background:#fff8e6; border:1px solid #ead9a0; border-left:4px solid #e8c53a; padding:18px 22px; margin:0 auto 20px; max-width:820px; border-radius:2px; }
.quick-answer .qa-label { font-size:0.66rem; font-weight:800; letter-spacing:0.2em; text-transform:uppercase; color:#8a6a00; margin-bottom:6px; }
.quick-answer p { font-size:0.97rem; color:#3a2e00; line-height:1.65; margin:0; }
.nav-toggle { display:none; background:none; border:0; padding:6px; font-size:1.6rem; line-height:1; cursor:pointer; color:var(--black); }
.mobile-cta { display:none; }
/* article pages */
.article-wrap { max-width:820px; margin:0 auto; padding:56px 32px 80px; }
.back { font-size:0.72rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--fruit-red); text-decoration:none; display:inline-flex; align-items:center; gap:6px; margin-bottom:32px; }
.back:hover { opacity:0.7; }
.article-eyebrow { font-size:0.68rem; font-weight:700; letter-spacing:0.2em; text-transform:uppercase; color:var(--fruit-red); margin-bottom:14px; }
.article-wrap h1 { font-size:clamp(1.6rem,3.5vw,2.4rem); font-weight:800; text-transform:uppercase; letter-spacing:-0.02em; line-height:1.1; margin-bottom:24px; }
.article-intro { font-size:1.05rem; color:#444; border-left:4px solid var(--fruit-red); padding-left:20px; margin-bottom:40px; line-height:1.7; }
.article-wrap h2 { font-size:1.2rem; font-weight:800; text-transform:uppercase; letter-spacing:-0.01em; margin:36px 0 14px; }
.article-wrap h3 { font-size:1rem; font-weight:700; margin:24px 0 10px; }
.article-wrap p { font-size:0.95rem; color:#444; line-height:1.75; margin-bottom:16px; }
.article-wrap ul, .article-wrap ol { padding-left:20px; margin-bottom:16px; }
.article-wrap li { font-size:0.95rem; color:#444; line-height:1.75; margin-bottom:6px; }
.article-wrap a { color:var(--fruit-red); font-weight:600; text-decoration:none; }
.article-wrap a:hover { text-decoration:underline; }
.article-wrap .quick-answer { margin:0 0 36px; max-width:none; }
.article-cta { background:var(--off-white); border:1px solid var(--border); border-left:4px solid var(--fruit-red); padding:24px 28px; margin:32px 0; border-radius:2px; }
.article-cta p { margin-bottom:14px; font-weight:600; color:var(--black); }
.btn-red { display:inline-block; background:var(--fruit-red); color:#fff !important; font-size:0.75rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase; padding:12px 24px; text-decoration:none !important; transition:opacity 0.2s; }
.btn-red:hover { opacity:0.85; }
table.size { width:100%; border-collapse:collapse; margin:18px 0 26px; font-size:0.9rem; }
table.size caption { text-align:left; font-size:0.78rem; color:var(--mid-gray); margin-bottom:8px; }
table.size th, table.size td { border:1px solid var(--border); padding:9px 12px; text-align:center; }
table.size th { background:var(--off-white); font-weight:800; text-transform:uppercase; letter-spacing:0.04em; font-size:0.74rem; }
table.size td:first-child, table.size th:first-child { text-align:left; }
table.size tr:nth-child(even) td { background:#fbfbfa; }
.faq-q { font-weight:700; margin:22px 0 6px; font-size:1rem; }
.related { border-top:1px solid var(--border); margin-top:48px; padding-top:24px; }
.related h3 { margin-top:0; }
.article-meta { font-size:0.74rem; color:var(--mid-gray); letter-spacing:0.04em; margin-bottom:28px; }
/* article list */
.articles-section { max-width:1200px; margin:0 auto; padding:56px 32px 80px; }
.articles-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px; }
.article-card { background:var(--white); border:1px solid var(--border); display:flex; flex-direction:column; transition:box-shadow 0.2s,border-color 0.2s; }
.article-card:hover { box-shadow:0 4px 16px rgba(0,0,0,0.08); border-color:#ccc; }
.card-tag { display:block; font-size:0.62rem; font-weight:800; letter-spacing:0.18em; text-transform:uppercase; color:var(--fruit-red); padding:18px 22px 0; }
.card-body { padding:10px 22px 22px; display:flex; flex-direction:column; gap:10px; flex:1; }
.card-body h2 { font-size:1.02rem; font-weight:800; line-height:1.35; }
.card-body p { font-size:0.88rem; color:#555; line-height:1.6; flex:1; }
.card-link { font-size:0.72rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase; color:var(--fruit-red); text-decoration:none; }
.card-link:hover { text-decoration:underline; }
.notfound { max-width:720px; margin:0 auto; padding:96px 32px; text-align:center; }
.notfound h1 { font-size:2rem; font-weight:800; text-transform:uppercase; margin-bottom:16px; }
.notfound p { color:#555; margin-bottom:28px; }
@media (max-width:768px) {
  body { width:100%; overflow-x:hidden; padding-bottom:58px; }
  .header-inner { padding:0 16px; }
  .logo-icon { height:36px; }
  .logo-text .sub { display:none; }
  .nav-toggle { display:block; }
  header nav { display:none; position:absolute; top:100%; left:0; right:0; background:var(--white); border-bottom:1px solid var(--border); flex-direction:column; gap:0; padding:4px 16px 12px; box-shadow:0 10px 24px rgba(0,0,0,0.08); align-items:stretch; }
  header nav.open { display:flex; }
  header nav a { padding:14px 2px; border-top:1px solid var(--border); font-size:0.92rem; }
  header nav .lang-switch { padding:12px 0 4px; border-top:1px solid var(--border); }
  .hero { padding:40px 16px 36px; }
  .hero h1 { font-size:2rem; letter-spacing:-0.01em; }
  .hero p { font-size:0.95rem; }
  .stat-bar { padding:20px 16px; }
  .stat-bar-inner { gap:20px; justify-content:space-around; }
  .stat-number { font-size:1.3rem; }
  .stat-label { font-size:0.6rem; }
  .breadcrumb { padding:12px 16px; }
  .intro, .about, .seo-section, .top-pick { padding:0 16px; }
  .intro { margin:40px auto; }
  .intro h2 { font-size:1.4rem; }
  .seo-section h2 { font-size:1.3rem; }
  .top-pick-box { flex-direction:column; gap:12px; padding:20px; }
  .table-section { padding:0 16px; margin-bottom:56px; }
  .table-top { flex-direction:column; align-items:flex-start; gap:12px; }
  .table-top h2 { font-size:1.2rem; }
  #search { width:100%; }
  table.retailers { display:block; overflow-x:auto; -webkit-overflow-scrolling:touch; }
  table.retailers thead th:nth-child(3), table.retailers td:nth-child(3) { display:none; }
  table.retailers thead th { padding:12px 10px; font-size:0.6rem; letter-spacing:0.1em; }
  table.retailers td { padding:14px 10px; font-size:0.85rem; }
  table.retailers td:first-child { width:32px; font-size:0.65rem; padding:16px 6px; }
  .td-info { font-size:0.75rem; max-width:100%; }
  .faq { padding:48px 16px; }
  .faq h2 { font-size:1.3rem; margin-bottom:28px; }
  .faq-item { padding:20px 0; }
  .about { margin:48px auto; }
  .privacy { padding:48px 16px; }
  .articles-teaser { padding:48px 16px; }
  .teaser-grid { grid-template-columns:1fr 1fr; gap:12px; }
  footer { padding:32px 16px; }
  .footer-inner { flex-direction:column; gap:12px; }
  .quick-answer { margin:0 16px 18px; padding:16px 18px; }
  .quick-answer p { font-size:0.92rem; }
  .article-wrap { padding:40px 16px 56px; }
  .article-wrap table.size { display:block; overflow-x:auto; -webkit-overflow-scrolling:touch; font-size:0.8rem; }
  table.size th, table.size td { padding:7px 6px; }
  .articles-section { padding:40px 16px 56px; }
  .mobile-cta { display:flex; position:fixed; bottom:0; left:0; right:0; z-index:200; background:var(--fruit-red); align-items:center; justify-content:center; gap:8px; padding:13px 16px; box-shadow:0 -4px 16px rgba(0,0,0,0.14); }
  .mobile-cta a { color:#fff; font-weight:800; font-size:0.85rem; letter-spacing:0.04em; text-decoration:none; text-transform:uppercase; }
}
@media (max-width:400px) {
  .hero h1 { font-size:1.7rem; }
  .stat-bar-inner { flex-direction:column; gap:16px; align-items:center; }
  .teaser-grid { grid-template-columns:1fr; }
}
"""

FONTS = """  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
"""

# ---------------------------------------------------------------- shared fragments
def head(site, *, title, description, keywords, canonical, og_type, alternates, schemas, extra_meta=""):
    p = rel_prefix(site)
    og_img = f"{DOMAIN}/og-image-{site['lang']}.png" if os.path.exists(os.path.join(ASSETS, f"og-image-{site['lang']}.png")) else f"{DOMAIN}/og-image.png"
    alt = "".join(f'  <link rel="alternate" hreflang="{esc(hl)}" href="{esc(u)}" />\n' for hl, u in alternates)
    sch = "".join(f'  <script type="application/ld+json">{jsonld(s)}</script>\n' for s in schemas)
    return f"""<!DOCTYPE html>
<html lang="{esc(site['lang'])}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <meta name="keywords" content="{esc(keywords)}" />
  <link rel="canonical" href="{esc(canonical)}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <meta name="language" content="{esc(site['lang'])}" />
  <meta name="geo.region" content="{esc(site.get('geo_region',''))}" />
  <meta name="geo.placename" content="{esc(site.get('region_name',''))}" />
  <link rel="icon" type="image/x-icon" href="{p}favicon.ico" />
  <link rel="icon" type="image/png" href="{p}favicon.png" />
  <link rel="shortcut icon" href="{p}favicon.ico" />
  <link rel="apple-touch-icon" href="{p}apple-touch-icon.png" />
  <link rel="sitemap" type="application/xml" href="/sitemap.xml" />
{alt}  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:locale" content="{esc(site['og_locale'])}" />
  <meta property="og:site_name" content="fruitotl.com" />
  <meta property="og:image" content="{og_img}" />
  <meta property="og:image:secure_url" content="{og_img}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:type" content="image/png" />
  <meta property="og:image:alt" content="{esc(site['ui']['og_alt'])}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{og_img}" />
{extra_meta}{sch}{FONTS}  <style>{CSS_BASE}</style>
</head>
"""

def lang_options(languages, current, target_fn):
    opts = []
    for L in languages:
        sel = ' selected' if L["lang"] == current["lang"] else ""
        opts.append(f'<option value="{esc(target_fn(L))}"{sel}>{esc(L["language_name"])}</option>')
    return "".join(opts)

def header_html(site, languages, target_fn, active=""):
    ui = site["ui"]
    p = rel_prefix(site)
    home = f"/{site['dir']}/" if site["dir"] else "/"
    art = f"{home}{site['articles_slug']}"
    def cls(name): return ' class="active"' if active == name else ""
    return f"""<header>
  <div class="header-inner">
    <a class="logo" href="{home}">
      <img src="{p}logo.svg" class="logo-icon" alt="Fruit of the Loom logo" width="64" height="44" />
      <div class="logo-text">
        <span class="brand">Fruit of the Loom</span>
        <span class="sub">{esc(ui['logo_sub'])}</span>
      </div>
    </a>
    <nav>
      <a href="{home}#retailers"{cls('retailers')}>{esc(ui['nav_retailers'])}</a>
      <a href="{home}#prices"{cls('prices')}>{esc(ui['nav_prices'])}</a>
      <a href="{art}"{cls('articles')}>{esc(ui['nav_articles'])}</a>
      <a href="{home}#faq"{cls('faq')}>{esc(ui['nav_faq'])}</a>
      <div class="lang-switch"><select aria-label="{esc(ui['language_label'])}" onchange="location.href=this.value">{lang_options(languages, site, target_fn)}</select></div>
    </nav>
    <button class="nav-toggle" aria-label="{esc(ui['menu_open'])}" aria-expanded="false" onclick="var n=document.querySelector('header nav');n.classList.toggle('open');this.setAttribute('aria-expanded',n.classList.contains('open'))">☰</button>
  </div>
</header>
"""

def footer_html(site, languages, target_fn, lang):
    ui = site["ui"]
    parts = []
    for L in languages:
        cls = ' class="active"' if L["lang"] == site["lang"] else ""
        parts.append(f'<a href="{esc(target_fn(L))}"{cls}>{esc(L["language_name"])}</a>')
    links = "".join(parts)
    return f"""<footer>
  <div class="footer-inner">
    <div class="footer-brand">fruitotl.com</div>
    <div class="footer-langs">{links}</div>
    <div class="footer-copy">© {TODAY[:4]} fruitotl.com — {esc(ui['footer_tagline'])} {esc(ui['not_affiliated'])}</div>
  </div>
</footer>
<div class="mobile-cta"><a href="{shop_url(lang, '/', 'mobile-sticky-cta')}" rel="nofollow sponsored" target="_blank">{esc(ui['mobile_cta'])} →</a></div>
"""

def quick_answer(site, text):
    return f'<div class="quick-answer"><div class="qa-label">{esc(site["ui"]["quick_answer"])}</div><p>{text}</p></div>\n'

# ---------------------------------------------------------------- page builders
def alternates_for(languages, per_lang_url):
    """per_lang_url: dict lang->url (only langs that have the page)"""
    out = []
    for L in languages:
        if L["lang"] in per_lang_url:
            out.append((L["hreflang"], per_lang_url[L["lang"]]))
    if "en" in per_lang_url:
        out.append(("x-default", per_lang_url["en"]))
    return out

def build_index(site, languages, articles_by_key, all_sites, ctx):
    lang = site["lang"]; ui = site["ui"]; ix = site["index"]
    X = lambda s: expand(s, lang, site, articles_by_key, ctx)
    url = page_url(site)
    per = {L["lang"]: page_url(L) for L in languages}
    alts = alternates_for(languages, per) + [("da", "https://fruitoftheloom.dk/")]   # Danish sister site
    target = lambda L: (f"/{L['dir']}/" if L["dir"] else "/")

    retailers = ix["retailers"]
    items = [{"@type":"ListItem","position":i+1,"name":r["name"],"url":r["url"],"description":strip_tags(X(r.get("schema_desc") or r["info"]))} for i,r in enumerate(retailers)]
    schemas = [
        {"@context":"https://schema.org","@type":"WebPage","name":ix["title"],"description":ix["description"],"url":url,"inLanguage":lang,"dateModified":ix.get("date_modified", TODAY),
         "about":{"@type":"Brand","name":"Fruit of the Loom","description":ix["brand_desc"]},
         "mainEntity":{"@type":"ItemList","name":ix["table_heading"],"numberOfItems":len(retailers),"itemListElement":items}},
        {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q["q"],"acceptedAnswer":{"@type":"Answer","text":strip_tags(X(q["a_html"]))}} for q in ix["faq"]]},
        {"@context":"https://schema.org","@type":"WebSite","name":"fruitotl.com","url":f"{DOMAIN}/","inLanguage":lang,"description":ix["website_desc"],"publisher":{"@type":"Organization","name":"fruitotl.com","url":f"{DOMAIN}/"}},
        {"@context":"https://schema.org","@type":"Organization","name":"fruitotl.com","url":f"{DOMAIN}/","logo":f"{DOMAIN}/favicon.png","image":f"{DOMAIN}/og-image.png","description":ix["org_desc"],"areaServed":{"@type":"Place","name":site["region_name"]},"knowsAbout":ix["knows_about"]},
    ]
    h = head(site, title=ix["title"], description=ix["description"], keywords=ix["keywords"], canonical=url, og_type="website", alternates=alts, schemas=schemas)
    b = [ "<body>\n", header_html(site, languages, target) ]
    b.append(f"""<section class="hero">
  <div class="hero-eyebrow">{esc(ix['hero_eyebrow'])}</div>
  <h1>{ix['h1_html']}</h1>
  <p>{esc(ix['hero_p'])}</p>
  <div class="fruit-dots"><span style="background:var(--fruit-red)"></span><span style="background:var(--fruit-purple)"></span><span style="background:var(--fruit-green)"></span><span style="background:var(--fruit-yellow)"></span></div>
</section>
<div class="stat-bar"><div class="stat-bar-inner">
""" + "".join(f'<div class="stat"><span class="stat-number">{esc(s["n"])}</span><span class="stat-label">{esc(s["label"])}</span></div>\n' for s in ix["stats"]) + """</div></div>
""")
    b.append(f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="{"/"+site["dir"]+"/" if site["dir"] else "/"}">{esc(ui["breadcrumb_home"])}</a><span>›</span>{esc(ix["breadcrumb_current"])}</nav>\n')
    b.append(quick_answer(site, X(ix["quick_answer"])))
    b.append(f"""<section class="intro">
  <div class="section-label">{esc(ix['intro_label'])}</div>
  <h2>{esc(ix['intro_h2'])}</h2>
  {X(ix['intro_html'])}
</section>
<div class="top-pick"><div class="top-pick-box">
  <div class="top-pick-icon">⭐</div>
  <div class="top-pick-content">
    <h3>{esc(ix['top_pick']['h3'])}</h3>
    <p>{X(ix['top_pick']['p_html'])}</p>
    <a class="btn" href="{shop_url(lang, '/', 'homepage-top-pick')}" rel="sponsored nofollow" target="_blank">{esc(ix['top_pick']['btn'])} →</a>
  </div>
</div></div>
""")
    # retailer table
    rows = []
    badge_cls = {"online":"b-online","store":"b-store","chain":"b-chain"}
    tag_label = {"recommended":"⭐ "+ui["tag_recommended"],"cheapest":"💰 "+ui["tag_cheapest"],"fast":"⚡ "+ui["tag_fast"],"store":"📍 "+ui["tag_store"],"lowprice":"💰 "+ui["tag_lowprice"]}
    for i, r in enumerate(retailers):
        tags = "".join(f'<span class="tag tag-{t}">{esc(tag_label[t])}</span>' for t in r.get("tags", []))
        tags = f'<div class="tags">{tags}</div>' if tags else ""
        addr = f'<div class="td-address">{esc(r["address"])}</div>' if r.get("address") else ""
        href = shop_url(lang, "/", "homepage-retailer-row") if "marmaladeco.com" in r["url"] else r["url"]
        rows.append(f"""      <tr>
        <td>{i+1:02d}</td>
        <td><strong>{esc(r['name'])}</strong><div class="td-info">{tags}{X(r['info'])}{addr}</div></td>
        <td>{esc(r['area'])}</td>
        <td><a class="site-link" href="{esc(href)}" rel="nofollow sponsored" target="_blank">{esc(r['domain'])}</a></td>
        <td><span class="badge {badge_cls[r['type']]}">{esc(ui['badge_'+r['type']])}</span></td>
      </tr>
""")
    b.append(f"""<section class="table-section" id="retailers">
  <div class="table-top">
    <h2>{esc(ix['table_heading'])}</h2>
    <input type="text" id="search" placeholder="{esc(ui['search_placeholder'])}" aria-label="{esc(ui['search_label'])}" />
  </div>
  <div class="supplier-count" id="count">{esc(ui['showing_all'].replace('{n}', str(len(retailers))))}</div>
  <table class="retailers" id="supplierTable">
    <thead><tr><th>#</th><th>{esc(ui['col_retailer'])}</th><th>{esc(ui['col_area'])}</th><th>{esc(ui['col_website'])}</th><th>{esc(ui['col_type'])}</th></tr></thead>
    <tbody id="tableBody">
{''.join(rows)}    </tbody>
  </table>
</section>
""")
    for sec_id, sec in (("prices", ix["price_guide"]), ("quality", ix["quality_guide"])):
        b.append(f'<section class="seo-section" id="{sec_id}">\n  <div class="section-label">{esc(sec["label"])}</div>\n  <h2>{esc(sec["h2"])}</h2>\n  <p>{X(sec["intro"])}</p>\n')
        for s in sec["sections"]:
            b.append(f'  <h3>{esc(s["h3"])}</h3>\n  <p>{X(s["p"])}</p>\n')
        b.append('</section>\n')
    b.append(f'<section class="faq" id="faq"><div class="faq-inner">\n  <h2>{esc(ix["faq_h2"])}</h2>\n')
    for q in ix["faq"]:
        b.append(f'  <div class="faq-item"><h3>{esc(q["q"])}</h3><p>{X(q["a_html"])}</p></div>\n')
    b.append('</div></section>\n')
    ab = ix["about"]
    b.append(f"""<section class="about" id="about">
  <div class="section-label">{esc(ab['label'])}</div>
  <h2>{esc(ab['h2'])}</h2>
  <p>{X(ab['p1'])}</p>
  <p>{X(ab['p2'])}</p>
  <h3>{esc(ab['h3'])}</h3>
  <p>{X(ab['p3'])}</p>
</section>
""")
    pv = ix["privacy"]
    b.append(f"""<section class="privacy" id="privacy"><div class="privacy-inner">
  <div class="section-label">{esc(pv['label'])}</div>
  <h2>{esc(pv['h2'])}</h2>
  <p>{X(pv['p1'])}</p><p>{X(pv['p2'])}</p><p>{X(pv['p3'])}</p>
  <p>{X(pv['p4'])} <a href="mailto:contact@fruitotl.com">contact@fruitotl.com</a></p>
</div></section>
""")
    cards = []
    teaser_keys = list(ix["teaser_keys"])
    have = [k for k in teaser_keys if k in articles_by_key]
    if len(have) < 6:
        teaser_keys += [k for k in articles_by_key if k not in teaser_keys][: 10 - len(have)]
    for k in teaser_keys:
        a = articles_by_key.get(k)
        if not a:
            (ctx["errors"] if lang == "en" else ctx["warnings"]).append(f"[{lang}] teaser key '{k}' has no article (yet)"); continue
        cards.append(f'      <a href="{a["slug"]}" class="teaser-card"><span class="teaser-tag">{esc(a["card_tag"])}</span><strong>{esc(a["card_title"])}</strong></a>\n')
    b.append(f"""<section class="articles-teaser" id="articles"><div class="articles-teaser-inner">
  <div class="section-label">{esc(ui['articles_teaser_label'])}</div>
  <h2>{esc(ui['articles_teaser_heading'])}</h2>
  <p>{esc(ui['articles_teaser_p'].replace('{n}', str(len(articles_by_key))))}</p>
  <div class="teaser-grid">
{''.join(cards)}  </div>
  <a href="{site['articles_slug']}" class="btn-all-articles">{esc(ui['all_articles'])} →</a>
</div></section>
""")
    b.append(footer_html(site, languages, target, lang))
    b.append(f"""<script>
  var s=document.getElementById('search'),tb=document.getElementById('tableBody'),c=document.getElementById('count');
  var rows=Array.prototype.slice.call(tb.querySelectorAll('tr')),total=rows.length;
  s.addEventListener('input',function(){{var q=s.value.toLowerCase().trim(),n=0;rows.forEach(function(r){{var show=!q||r.textContent.toLowerCase().indexOf(q)>-1;r.style.display=show?'':'none';if(show)n++;}});c.textContent=q?{json.dumps(ui['showing_n'])}.replace('{{n}}',n).replace('{{total}}',total):{json.dumps(ui['showing_all'])}.replace('{{n}}',total);}});
</script>
</body>
</html>
""")
    return h + "".join(b)

def build_articles_list(site, languages, articles, articles_by_key, all_sites, ctx):
    lang = site["lang"]; ui = site["ui"]
    url = page_url(site, site["articles_slug"])
    per = {L["lang"]: page_url(L, L["articles_slug"]) for L in languages}
    alts = alternates_for(languages, per)
    target = lambda L: (f"/{L['dir']}/" if L["dir"] else "/") + L["articles_slug"]
    home = f"/{site['dir']}/" if site["dir"] else "/"
    schemas = [
        {"@context":"https://schema.org","@type":"CollectionPage","name":ui["articles_title"],"description":ui["articles_description"],"url":url,"inLanguage":lang,
         "hasPart":[{"@type":"Article","headline":a["h1"],"url":page_url(site, a["slug"])} for a in articles]},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":ui["breadcrumb_home"],"item":page_url(site)},{"@type":"ListItem","position":2,"name":ui["nav_articles"],"item":url}]},
    ]
    h = head(site, title=ui["articles_title"], description=ui["articles_description"], keywords=ui["articles_keywords"], canonical=url, og_type="website", alternates=alts, schemas=schemas)
    cards = "".join(f"""    <div class="article-card">
      <span class="card-tag">{esc(a['card_tag'])}</span>
      <div class="card-body">
        <h2>{esc(a['card_title'])}</h2>
        <p>{esc(a['card_desc'])}</p>
        <a href="{a['slug']}" class="card-link">{esc(ui['read_article'])} →</a>
      </div>
    </div>
""" for a in articles)
    body = f"""<body>
{header_html(site, languages, target, active='articles')}<section class="hero">
  <div class="hero-eyebrow">{esc(ui['articles_hero_eyebrow'])}</div>
  <h1>{ui['articles_h1_html']}</h1>
  <p>{esc(ui['articles_hero_p'])}</p>
</section>
<nav class="breadcrumb" aria-label="Breadcrumb"><a href="{home}">{esc(ui['breadcrumb_home'])}</a><span>›</span>{esc(ui['nav_articles'])}</nav>
<div class="articles-section">
  <div class="articles-grid">
{cards}  </div>
</div>
{footer_html(site, languages, target, lang)}</body>
</html>
"""
    return h + body

def build_article(site, languages, a, articles_by_key, all_sites, ctx):
    lang = site["lang"]; ui = site["ui"]
    X = lambda s: expand(s, lang, site, articles_by_key, ctx)
    url = page_url(site, a["slug"])
    per = {}
    for L in languages:
        other = all_sites[L["lang"]]["articles_by_key"].get(a["key"])
        if other: per[L["lang"]] = page_url(L, other["slug"])
    alts = alternates_for(languages, per)
    def target(L):
        other = all_sites[L["lang"]]["articles_by_key"].get(a["key"])
        base = f"/{L['dir']}/" if L["dir"] else "/"
        return base + (other["slug"] if other else "")
    home = f"/{site['dir']}/" if site["dir"] else "/"
    art_list = home + site["articles_slug"]
    faq = a.get("faq", [])
    schemas = [
        {"@context":"https://schema.org","@type":"Article","headline":a["h1"],"description":a["description"],"url":url,"inLanguage":lang,
         "datePublished":a["date_published"],"dateModified":a["date_modified"],
         "author":{"@type":"Organization","name":"fruitotl.com","url":f"{DOMAIN}/"},
         "publisher":{"@type":"Organization","name":"fruitotl.com","logo":{"@type":"ImageObject","url":f"{DOMAIN}/favicon.png"}},
         "image":f"{DOMAIN}/og-image.png","mainEntityOfPage":url},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":ui["breadcrumb_home"],"item":page_url(site)},
            {"@type":"ListItem","position":2,"name":ui["nav_articles"],"item":page_url(site, site["articles_slug"])},
            {"@type":"ListItem","position":3,"name":a["card_title"],"item":url}]},
    ]
    if faq:
        schemas.append({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q["q"],"acceptedAnswer":{"@type":"Answer","text":strip_tags(X(q["a"]))}} for q in faq]})
    extra = f'  <meta property="article:published_time" content="{a["date_published"]}" />\n  <meta property="article:modified_time" content="{a["date_modified"]}" />\n'
    h = head(site, title=a["title"], description=a["description"], keywords=a.get("keywords",""), canonical=url, og_type="article", alternates=alts, schemas=schemas, extra_meta=extra)
    faq_html = ""
    if faq:
        faq_html = f'  <h2>{esc(ui["faq_heading"])}</h2>\n' + "".join(f'  <div class="faq-q">{esc(q["q"])}</div>\n  <p>{X(q["a"])}</p>\n' for q in faq)
    rel_items = []
    for k in a.get("related", []):
        r = articles_by_key.get(k)
        if not r:
            (ctx["errors"] if lang == "en" else ctx["warnings"]).append(f"[{lang}] {a['key']}: related key '{k}' missing (yet)"); continue
        if r["key"] != a["key"]:
            rel_items.append(f'      <li><a href="{r["slug"]}">{esc(r["card_title"])}</a></li>\n')
    related = f'  <div class="related"><h3>{esc(ui["related_guides"])}</h3><ul>\n{"".join(rel_items)}    </ul></div>\n' if rel_items else ""
    body = f"""<body>
{header_html(site, languages, target, active='articles')}<div class="article-wrap">
  <a href="{art_list}" class="back">← {esc(ui['back_to_articles'])}</a>
  <div class="article-eyebrow">{esc(a['eyebrow'])}</div>
  <h1>{esc(a['h1'])}</h1>
  <div class="article-meta">{esc(ui['updated_label'])}: <time datetime="{a['date_modified']}">{a['date_modified']}</time></div>
  <p class="article-intro">{X(a['intro'])}</p>
{quick_answer(site, X(a['quick_answer']))}{X(a['body_html'])}
{faq_html}{related}</div>
{footer_html(site, languages, target, lang)}</body>
</html>
"""
    return h + body

def build_404(site, languages):
    ui = site["ui"]
    target = lambda L: (f"/{L['dir']}/" if L["dir"] else "/")
    h = head(site, title=ui["not_found_title"], description=ui["not_found_p"], keywords="", canonical=f"{DOMAIN}/404", og_type="website", alternates=[], schemas=[])
    h = h.replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />', '<meta name="robots" content="noindex" />')
    return h + f"""<body>
{header_html(site, languages, target)}<div class="notfound">
  <h1>{esc(ui['not_found_title'])}</h1>
  <p>{esc(ui['not_found_p'])}</p>
  <a href="/" class="btn-all-articles">{esc(ui['not_found_btn'])} →</a>
</div>
{footer_html(site, languages, target, site['lang'])}</body>
</html>
"""

# ---------------------------------------------------------------- validation
REQ_ARTICLE = ["key","slug","title","description","eyebrow","h1","intro","quick_answer","body_html","card_tag","card_title","card_desc","date_published","date_modified"]
REQ_SITE = ["lang","hreflang","og_locale","dir","language_name","region_name","articles_slug","ui","index"]
REQ_UI = ["nav_retailers","nav_prices","nav_articles","nav_faq","menu_open","back_to_articles","quick_answer","read_article","all_articles","related_guides","faq_heading","search_placeholder","search_label","showing_all","showing_n","col_retailer","col_area","col_website","col_type","badge_online","badge_store","badge_chain","tag_recommended","tag_cheapest","tag_fast","tag_store","tag_lowprice","mobile_cta","footer_tagline","not_affiliated","breadcrumb_home","logo_sub","language_label","articles_teaser_label","articles_teaser_heading","articles_teaser_p","articles_hero_eyebrow","articles_h1_html","articles_hero_p","articles_title","articles_description","articles_keywords","not_found_title","not_found_p","not_found_btn","og_alt","updated_label"]
REQ_INDEX = ["title","description","keywords","hero_eyebrow","h1_html","hero_p","stats","breadcrumb_current","quick_answer","intro_label","intro_h2","intro_html","top_pick","retailers","table_heading","price_guide","quality_guide","faq_h2","faq","about","privacy","teaser_keys","brand_desc","website_desc","org_desc","knows_about"]

def validate(site, articles, ctx):
    lang = site.get("lang","?")
    for k in REQ_SITE:
        if k not in site: ctx["errors"].append(f"[{lang}] site.json missing '{k}'")
    for k in REQ_UI:
        if k not in site.get("ui", {}): ctx["errors"].append(f"[{lang}] site.json ui missing '{k}'")
    for k in REQ_INDEX:
        if k not in site.get("index", {}): ctx["errors"].append(f"[{lang}] site.json index missing '{k}'")
    for r in site.get("index", {}).get("retailers", []):
        for k in ["name","info","area","url","domain","type"]:
            if k not in r: ctx["errors"].append(f"[{lang}] retailer {r.get('name','?')} missing '{k}'")
        if r.get("type") not in ("online","store","chain"): ctx["errors"].append(f"[{lang}] retailer {r.get('name')} bad type")
    seen_slugs, seen_keys = set(), set()
    for a in articles:
        for k in REQ_ARTICLE:
            if k not in a: ctx["errors"].append(f"[{lang}] article {a.get('key','?')} missing '{k}'")
        if a.get("slug") in seen_slugs: ctx["errors"].append(f"[{lang}] duplicate slug {a['slug']}")
        if a.get("key") in seen_keys: ctx["errors"].append(f"[{lang}] duplicate key {a['key']}")
        seen_slugs.add(a.get("slug")); seen_keys.add(a.get("key"))
        if not re.fullmatch(r"[a-z0-9-]+", a.get("slug","")): ctx["errors"].append(f"[{lang}] slug '{a.get('slug')}' must be ascii lowercase/hyphens")
        for d in ("date_published","date_modified"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(a.get(d,""))): ctx["errors"].append(f"[{lang}] {a.get('key')}: bad {d}")
        if len(a.get("body_html","")) < 2500: ctx["warnings"].append(f"[{lang}] {a.get('key')}: body_html is short ({len(a.get('body_html',''))} chars)")
        if len(a.get("title","")) > 70: ctx["warnings"].append(f"[{lang}] {a.get('key')}: title > 70 chars")
        if len(a.get("description","")) > 165: ctx["warnings"].append(f"[{lang}] {a.get('key')}: description > 165 chars")

# ---------------------------------------------------------------- main
def main():
    ctx = {"errors": [], "warnings": []}
    languages = read_json(os.path.join(CONTENT, "languages.json"))
    all_sites = {}
    languages = [L for L in languages if os.path.exists(os.path.join(CONTENT, L["lang"], "site.json"))
                 or print(f"skip  language '{L['lang']}' has no site.json yet")]
    for L in languages:
        d = os.path.join(CONTENT, L["lang"])
        site = read_json(os.path.join(d, "site.json"))
        for k, v in L.items(): site.setdefault(k, v)
        arts = []
        adir = os.path.join(d, "articles")
        for fn in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
            if fn.endswith(".json"): arts.append(read_json(os.path.join(adir, fn)))
        if not arts:
            print(f"skip  language '{L['lang']}' has no articles yet"); continue
        validate(site, arts, ctx)
        arts.sort(key=lambda a: (a.get("order", 999), a.get("date_published","")), reverse=False)
        all_sites[L["lang"]] = {"site": site, "articles": arts, "articles_by_key": {a["key"]: a for a in arts}}
    languages = [L for L in languages if L["lang"] in all_sites]
    langs = [all_sites[L["lang"]]["site"] for L in languages]

    if ctx["errors"]:
        print("\n".join("ERROR " + e for e in ctx["errors"])); sys.exit(1)

    pages = {}   # out path -> html
    urls = []    # (loc, lastmod, priority, changefreq, alternates)
    for L in langs:
        s = all_sites[L["lang"]]
        site, arts, abk = s["site"], s["articles"], s["articles_by_key"]
        d = site["dir"]
        prefix = f"{d}/" if d else ""
        pages[f"{prefix}index.html"] = build_index(site, langs, abk, all_sites, ctx)
        urls.append((page_url(site), site["index"].get("date_modified", TODAY), "1.0", "weekly", alternates_for(langs, {x["lang"]: page_url(x) for x in langs}) + [("da", "https://fruitoftheloom.dk/")]))
        pages[f"{prefix}{site['articles_slug']}.html"] = build_articles_list(site, langs, arts, abk, all_sites, ctx)
        urls.append((page_url(site, site["articles_slug"]), max([a["date_modified"] for a in arts] or [TODAY]), "0.9", "weekly", alternates_for(langs, {x["lang"]: page_url(x, x["articles_slug"]) for x in langs})))
        for a in arts:
            pages[f"{prefix}{a['slug']}.html"] = build_article(site, langs, a, abk, all_sites, ctx)
            per = {x["lang"]: page_url(x, all_sites[x["lang"]]["articles_by_key"][a["key"]]["slug"]) for x in langs if a["key"] in all_sites[x["lang"]]["articles_by_key"]}
            urls.append((page_url(site, a["slug"]), a["date_modified"], "0.8", "monthly", alternates_for(langs, per)))
    en = all_sites["en"]["site"]
    pages["404.html"] = build_404(en, langs)

    # internal link check
    known = set(p[:-5] for p in pages) | set(p for p in pages)
    for path, htmls in pages.items():
        base = os.path.dirname(path)
        for m in re.finditer(r'href="([^"#?]+)', htmls):
            href = m.group(1)
            if href.startswith(("http", "mailto:", "/")) or href.endswith((".svg", ".png", ".ico", ".xml", ".txt")):
                if href.startswith("/") and not href.startswith("//") and not href.endswith((".xml",".txt",".png",".svg",".ico")):
                    tgt = href.strip("/")
                    if tgt and tgt not in known and tgt + "/index.html" not in known and tgt + "/index" not in known:
                        ctx["errors"].append(f"dead root link {href} in {path}")
                continue
            tgt = os.path.normpath(os.path.join(base, href)).replace("\\", "/")
            if tgt not in known:
                ctx["errors"].append(f"dead link {href} in {path}")
    if ctx["errors"]:
        print("\n".join("ERROR " + e for e in ctx["errors"])); sys.exit(1)

    for w in ctx["warnings"]: print("warn  " + w)
    if CHECK_ONLY:
        print(f"OK — {len(pages)} pages validated, {len(langs)} languages."); return

    # write output
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    for path, htmls in pages.items():
        full = os.path.join(OUT, path); os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f: f.write(htmls)
    for fn in os.listdir(ASSETS):
        shutil.copy(os.path.join(ASSETS, fn), os.path.join(OUT, fn))
    with open(os.path.join(OUT, "CNAME"), "w") as f: f.write("fruitotl.com\n")
    with open(os.path.join(OUT, ".nojekyll"), "w") as f: f.write("")

    # sitemap
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc, lastmod, prio, freq, alts in urls:
        sm.append(f"  <url>\n    <loc>{esc(loc)}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>")
        for hl, u in alts: sm.append(f'    <xhtml:link rel="alternate" hreflang="{hl}" href="{esc(u)}" />')
        sm.append("  </url>")
    sm.append("</urlset>\n")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f: f.write("\n".join(sm))

    bots = ["GPTBot","OAI-SearchBot","ChatGPT-User","PerplexityBot","Perplexity-User","ClaudeBot","Claude-Web","Claude-SearchBot","Anthropic-AI","Google-Extended","Applebot","Applebot-Extended","Bingbot","CCBot","Amazonbot","meta-externalagent","DuckAssistBot","YouBot"]
    robots = "# robots.txt — fruitotl.com\nUser-agent: *\nAllow: /\n\n# AI search / LLM crawlers (GEO) — explicitly allowed\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"Sitemap: {DOMAIN}/sitemap.xml\n"
    with open(os.path.join(OUT, "robots.txt"), "w") as f: f.write(robots)

    # llms.txt (root, all languages) + per-language llms.txt
    def llms_for(site, arts):
        ix = site["index"]
        lines = [f"# fruitotl.com ({site['language_name']})", f"> {strip_tags(expand(ix['quick_answer'], site['lang'], site, {a['key']:a for a in arts}, {'errors':[]}))}", "",
                 f"## {site['ui']['nav_retailers']}"]
        for r in ix["retailers"]:
            lines.append(f"- {r['name']} ({r['url']}): {strip_tags(expand(r.get('schema_desc') or r['info'], site['lang'], site, {}, {'errors':[]}))}")
        lines += ["", f"## {site['ui']['nav_articles']}", f"- [{ix['title']}]({page_url(site)})", f"- [{site['ui']['articles_title']}]({page_url(site, site['articles_slug'])})"]
        for a in arts:
            lines.append(f"- [{a['card_title']}]({page_url(site, a['slug'])}): {a['card_desc']}")
        return "\n".join(lines) + "\n"
    root_llms = []
    for L in langs:
        s = all_sites[L["lang"]]
        txt = llms_for(s["site"], s["articles"])
        d = s["site"]["dir"]
        if d:
            with open(os.path.join(OUT, d, "llms.txt"), "w", encoding="utf-8") as f: f.write(txt)
        root_llms.append(txt)
    with open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(root_llms))

    print(f"Built {len(pages)} pages in {len(langs)} languages -> docs/")

if __name__ == "__main__":
    main()
