#!/usr/bin/env python3
"""TRYEZA audit part 1: page sweep — errors, 404, overflow, dup IDs, bad text."""
import json, re, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8931/"
FIRST = "tirana-era-blloku"
PAGES = [
    "index.html", "restorante.html",
    f"restorant.html?id={FIRST}", "restorant.html?id=shkodra-tradita",
    f"menu-builder.html?id={FIRST}",
    "rezervimet.html", "blog.html", "faq.html", "kodi.html", "kredite.html",
    "dashboard.html", "sugjero.html", "renditja.html", "pune.html", "sherbime.html",
]
VIEWPORTS = [(1440, 900), (768, 1024), (390, 844)]
KEYISH = re.compile(r"\b(?:nav|hero|bk|det|my|lb|job|svc|asst|flt|lst|home|how|biz|db|bl|nl|card|slot|share|mb|pg|cat|tab|city|badge|footer|loader|terms|scan)\.[a-zA-Z][a-zA-Z0-9_.]*\b")

results = []
def run(pw, lang):
    b = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
    for (w, h) in VIEWPORTS:
        ctx = b.new_context(viewport={"width": w, "height": h})
        if lang == "en":
            ctx.add_init_script("localStorage.setItem('tryeza.lang.v1','en')")
        pg = ctx.new_page()
        for url in PAGES:
            errs, perrs, bad = [], [], []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: perrs.append(str(e)))
            pg.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
            try:
                pg.goto(BASE + url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                results.append({"page": url, "vp": w, "lang": lang, "FATAL": str(e)[:200]})
                continue
            pg.wait_for_timeout(700)
            chk = pg.evaluate("""() => {
              const de = document.documentElement;
              const overflow = de.scrollWidth - window.innerWidth;
              const ids = {};
              document.querySelectorAll('[id]').forEach(el => { ids[el.id] = (ids[el.id]||0)+1; });
              const dupIds = Object.entries(ids).filter(([k,v]) => v>1).map(([k]) => k);
              const text = document.body ? document.body.innerText : '';
              return { overflow, dupIds, text };
            }""")
            badtext = []
            for pat in ["undefined", "NaN", "[object Object]", "null persona"]:
                if pat in chk["text"]:
                    badtext.append(pat)
            keyish = list({m.group(0) for m in KEYISH.finditer(chk["text"])})
            row = {"page": url, "vp": w, "lang": lang,
                   "console_err": errs, "page_err": perrs, "http_bad": bad,
                   "overflow": chk["overflow"], "dupIds": chk["dupIds"],
                   "badtext": badtext, "keyish": keyish}
            if errs or perrs or bad or chk["overflow"] > 1 or chk["dupIds"] or badtext or keyish:
                results.append(row)
        ctx.close()
    b.close()

with sync_playwright() as pw:
    run(pw, "sq")
    run(pw, "en")

print(json.dumps(results, ensure_ascii=False, indent=1))
print("TOTAL PROBLEM ROWS:", len(results))
