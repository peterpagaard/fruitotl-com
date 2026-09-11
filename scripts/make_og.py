#!/usr/bin/env python3
"""Generate og-image.png (+ per-language variants) in the site's look: black band, red accent, Fruit dots."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
FONT_CANDIDATES = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf","/System/Library/Fonts/HelveticaNeue.ttc","/System/Library/Fonts/Helvetica.ttc","/Library/Fonts/Arial Bold.ttf"]
def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size, index=1 if p.endswith(".ttc") else 0)
            except Exception: pass
    return ImageFont.load_default()
TEXTS = {
  "en": ("FRUIT OF THE LOOM", "IN EUROPE", "Cheapest prices · Best retailers · Guides 2026"),
  "de": ("FRUIT OF THE LOOM", "IN DEUTSCHLAND", "Günstigste Preise · Beste Händler · Ratgeber 2026"),
  "nl": ("FRUIT OF THE LOOM", "IN NEDERLAND", "Laagste prijzen · Beste winkels · Gidsen 2026"),
  "fr": ("FRUIT OF THE LOOM", "EN FRANCE", "Meilleurs prix · Meilleurs revendeurs · Guides 2026"),
  "es": ("FRUIT OF THE LOOM", "EN ESPAÑA", "Mejores precios · Mejores tiendas · Guías 2026"),
  "it": ("FRUIT OF THE LOOM", "IN ITALIA", "Prezzi più bassi · Migliori rivenditori · Guide 2026"),
  "pl": ("FRUIT OF THE LOOM", "W POLSCE", "Najniższe ceny · Najlepsze sklepy · Poradniki 2026"),
  "pt": ("FRUIT OF THE LOOM", "EM PORTUGAL", "Preços mais baixos · Melhores lojas · Guias 2026"),
  "fi": ("FRUIT OF THE LOOM", "SUOMESSA", "Halvimmat hinnat · Parhaat kaupat · Oppaat 2026"),
}
def make(lang, out):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#f8f8f6"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill="#CC2529")
    d.rectangle([0, H-120, W, H], fill="#111111")
    l1, l2, sub = TEXTS[lang]
    f1, f2, f3, f4 = font(78), font(78), font(30), font(22)
    d.text((80, 130), l1, font=f1, fill="#111111")
    d.text((80, 220), l2, font=f2, fill="#CC2529")
    d.text((80, 330), sub, font=f3, fill="#444444")
    x = 80
    for c in ("#CC2529", "#6B3FA0", "#3A7D2C", "#E8C53A"):
        d.ellipse([x, 400, x+26, 426], fill=c); x += 40
    d.text((80, 560), "fruitotl.com", font=f4, fill="#E8C53A")
    d.text((W-80-d.textlength("Independent retailer & price guide", font=f4), 560), "Independent retailer & price guide", font=f4, fill="#aaaaaa")
    im.save(out, optimize=True)
os.makedirs(OUT, exist_ok=True)
make("en", os.path.join(OUT, "og-image.png"))
for lang in TEXTS:
    make(lang, os.path.join(OUT, f"og-image-{lang}.png"))
print("og images written:", sorted(f for f in os.listdir(OUT) if f.startswith("og-image")))
