#!/usr/bin/env python3
"""Validim SEO runtime: skema Restaurant (JSON-LD) për 21 restorantet kundrejt data.js
+ sweep regresioni faqe kryesore x desktop/mobile x SQ/EN (0 console/page errors)."""
import re, json, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8932"
ABS = "https://erionnezha.github.io/tryeza"

src = open("/home/hatch/workspace/tryeza/js/data.js", encoding="utf-8").read()
RESTS = json.loads(re.search(r"var RESTORANTET = (\[.*\])", src, re.S).group(1))
assert len(RESTS) == 21

DAYS = {"E Hënë": "Monday", "E Martë": "Tuesday", "E Mërkurë": "Wednesday",
        "E Enjte": "Thursday", "E Premte": "Friday", "E Shtunë": "Saturday", "E Diel": "Sunday"}
ORDER = list(DAYS)

def expand(key):
    p = [s.strip() for s in key.split(" - ")]
    if p[0] not in DAYS: return []
    if len(p) == 1 or p[1] not in DAYS: return [DAYS[p[0]]]
    out, k = [], ORDER.index(p[0])
    while True:
        out.append(DAYS[ORDER[k]])
        if k == ORDER.index(p[1]): break
        k = (k + 1) % 7
    return out

def expected_specs(r):
    specs = set()
    for key, val in (r.get("orare") or {}).items():
        days = expand(key)
        if not days: continue
        for iv in re.split(r"[,/]", str(val)):
            m = re.match(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$", iv)
            if m: specs.add((tuple(days), m.group(1), m.group(2)))
    return specs

fails, npass = [], 0
def check(name, cond, extra=""):
    global npass
    if cond: npass += 1
    else: fails.append(f"{name} {extra}")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
    errors = []
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)

    # ---- 21 restorantet: JSON-LD runtime kundrejt data.js ----
    for r in RESTS:
        pg.goto(f"{BASE}/restorant.html?id={r['id']}")
        pg.wait_for_selector("#ld-restorant", state="attached", timeout=8000)
        ld = json.loads(pg.eval_on_selector("#ld-restorant", "el => el.textContent"))
        tag = r["id"]
        check(tag + " name", ld.get("name") == r["emer"])
        check(tag + " telephone", ld.get("telephone") == (r.get("telefon") or ""))
        check(tag + " priceRange", ld.get("priceRange") == "€" * max(1, r.get("cmim") or 1))
        check(tag + " cuisine", ld.get("servesCuisine") == (r.get("kuzhina") or []))
        ad = ld.get("address", {})
        check(tag + " address", ad.get("streetAddress") == (r.get("adrese") or "")
              and ad.get("addressLocality") == (r.get("qytet") or "")
              and ad.get("addressCountry") == "AL")
        check(tag + " url", ld.get("url") == f"{ABS}/restorant.html?id={r['id']}")
        check(tag + " description", ld.get("description") == (r.get("pershkrim") or "").strip())
        if r.get("fotot"):
            check(tag + " image", ld.get("image") == ABS + "/" + r["fotot"][0]["file"])
        ar = ld.get("aggregateRating")
        if r.get("rating") is not None and r.get("nrVleresime"):
            check(tag + " rating", ar and ar.get("ratingValue") == r["rating"]
                  and ar.get("reviewCount") == r["nrVleresime"], str(ar))
        else:
            check(tag + " rating mungon (null)", ar is None)
        got = {(tuple(s["dayOfWeek"]), s["opens"], s["closes"])
               for s in ld.get("openingHoursSpecification", [])}
        exp = expected_specs(r)
        check(tag + " orare", got == exp, f"got={got} exp={exp}")
        # meta dinamike
        ogt = pg.get_attribute('meta[property="og:title"]', "content")
        check(tag + " og:title", ogt == r["emer"] + " — TRYEZA", str(ogt))
        can = pg.get_attribute('link[rel="canonical"]', "href")
        check(tag + " canonical", can == f"{ABS}/restorant.html?id={r['id']}", str(can))
    print(f"restorante JSON-LD: {npass} kalime, {len(fails)} deshtime")
    for f in fails: print("  FAIL", f)

    # ---- sweep regresioni ----
    pages = ["index.html", "restorante.html", "blog.html", "faq.html", "renditja.html",
             "pune.html", "sherbime.html", "rezervimet.html", "menu-builder.html",
             "sugjero.html", "dashboard.html", "kodi.html", "kredite.html", "offline.html"]
    sweep_fail = 0
    for vp in [{"width": 1440, "height": 900}, {"width": 390, "height": 844}]:
        for lang in ["sq", "en"]:
            ctx = b.new_context(viewport=vp)
            p2 = ctx.new_page()
            p2.on("pageerror", lambda e: errors.append(f"sweep pageerror: {e}"))
            p2.on("console", lambda m: errors.append(f"sweep console: {m.text}") if m.type == "error" else None)
            p2.add_init_script(f"localStorage.setItem('tryeza.lang','{lang}')")
            for f in pages:
                p2.goto(f"{BASE}/{f}")
                p2.wait_for_timeout(350)
                og = p2.evaluate("""() => ({
                    t: document.querySelector('meta[property="og:title"]')?.content || '',
                    i: document.querySelector('meta[property="og:image"]')?.content || '',
                    c: document.querySelector('link[rel="canonical"]')?.href || ''})""")
                if not og["t"] or "og-cover.jpg" not in og["i"] or "erionnezha.github.io/tryeza" not in og["c"]:
                    sweep_fail += 1
                    print("  SWEEP FAIL", vp["width"], lang, f, og)
            ctx.close()
    print(f"sweep: {sweep_fail} deshtime; gabime konsole/faqeje gjithsej: {len(errors)}")
    for e in errors[:10]: print("  ERR", e)
    b.close()

print("REZULTATI:", "OK" if not fails and not errors and sweep_fail == 0 else "KA PROBLEME")
sys.exit(1 if (fails or errors or sweep_fail) else 0)
