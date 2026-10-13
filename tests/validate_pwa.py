#!/usr/bin/env python3
"""Validimi PWA — manifest, service worker, offline, butoni i instalimit, regresion.
Server: python3 -m http.server 8933 (nga root-i i projektit)."""
import json, re, sys, time, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8933"
ROOT = __file__.rsplit("/tests/", 1)[0]
fails, passes = [], []
def check(name, cond, extra=""):
    (passes if cond else fails).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))

def PNG_size(path):
    with open(path, "rb") as f:
        d = f.read(24)
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")

# ---------- 1. Manifest (statik + HTTP) ----------
raw = urllib.request.urlopen(BASE + "/manifest.webmanifest", timeout=10).read()
man = json.loads(raw)
check("manifest parse JSON", True)
check("manifest name", man.get("name", "").startswith("TRYEZA"))
check("manifest short_name", man.get("short_name") == "TRYEZA")
check("manifest display standalone", man.get("display") == "standalone")
check("manifest theme/bg #0e0f12", man.get("theme_color") == "#0e0f12" and man.get("background_color") == "#0e0f12")
check("manifest lang sq", man.get("lang") == "sq")
exp = {"icons/icon-192.png": (192, 192), "icons/icon-512.png": (512, 512),
       "icons/icon-maskable-512.png": (512, 512), "icons/apple-touch-icon.png": (180, 180)}
by_src = {i["src"]: i for i in man["icons"]}
for src, wh in exp.items():
    check(f"manifest icon {src} deklaruar", src in by_src and by_src[src]["sizes"] == f"{wh[0]}x{wh[1]}")
    check(f"icon {src} madhësia reale {wh}", PNG_size(f"{ROOT}/{src}") == wh)
    code = urllib.request.urlopen(BASE + "/" + src, timeout=10).status
    check(f"icon {src} HTTP {code}", code == 200)
check("maskable purpose", by_src.get("icons/icon-maskable-512.png", {}).get("purpose") == "maskable")
for f in ["sw.js", "offline.html", "js/pwa.js"]:
    code = urllib.request.urlopen(BASE + "/" + f, timeout=10).status
    check(f"{f} HTTP {code}", code == 200)

rest_id = re.search(r'"id":\s*"([^"]+)"', open(f"{ROOT}/js/data.js", encoding="utf-8").read()).group(1)
PAGES = ["index.html", "restorante.html", f"restorant.html?id={rest_id}", "menu-builder.html",
         "rezervimet.html", "blog.html", "faq.html", "kodi.html", "kredite.html", "dashboard.html",
         "sugjero.html", "renditja.html", "pune.html", "sherbime.html", "offline.html"]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])

    # ---------- 2. SW regjistrohet + shell në cache ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(BASE + "/index.html")
    try:
        pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller", timeout=15000)
        sw_ok = True
    except Exception:
        sw_ok = False
    check("SW regjistrohet + kontrollon faqen", sw_ok)
    keys = pg.evaluate("caches.keys()")
    check("cache tryeza-v1 ekziston", "tryeza-v1" in keys, str(keys))
    n_shell = pg.evaluate("caches.open('tryeza-v1').then(c => c.keys()).then(k => k.length)")
    check("shell i pre-cache-uar >= 10 hyrje", n_shell >= 10, str(n_shell))
    check("index pa gabime console (SW aktiv)", not errs, "; ".join(errs[:3]))
    pg.goto(BASE + "/restorante.html")  # vizitë e dytë (për offline)
    pg.wait_for_timeout(700)

    # ---------- 3. Offline: faqe e vizituar nga cache + e pavizituar -> offline.html ----------
    ctx.set_offline(True)
    pg.reload()
    pg.wait_for_timeout(600)
    body = pg.locator("body").inner_text()
    check("offline: index hapet nga cache", "TRYEZA" in body and "tryLoader" not in body[:0])
    check("offline: index pa gabime", not errs, "; ".join(errs[:3]))
    pg.goto(BASE + "/pune.html")
    pg.wait_for_timeout(500)
    check("offline: faqe e pavizituar -> offline.html", pg.locator("#retry").count() == 1)
    pg.screenshot(path=f"{ROOT}/screenshots/pwa-offline.png")
    ctx.set_offline(False)
    ctx.close()

    # ---------- 4. Butoni i instalimit (beforeinstallprompt i simuluar) ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/index.html")
    pg.wait_for_timeout(800)
    pg.evaluate("""() => {
      const e = new Event('beforeinstallprompt');
      e.prompt = () => { window.__promptCalled = true; };
      e.userChoice = Promise.resolve({ outcome: 'accepted', platform: 'web' });
      window.dispatchEvent(e);
    }""")
    pg.wait_for_timeout(600)
    check("install bar shfaqet", pg.locator("#pwaBar.show").count() == 1)
    check("butoni 'Instalo app-in' (SQ)", "Instalo app-in" in (pg.locator("#pwaInstall").inner_text() if pg.locator("#pwaInstall").count() else ""))
    pg.screenshot(path=f"{ROOT}/screenshots/pwa-install.png")
    pg.locator("#pwaInstall").click()
    pg.wait_for_timeout(900)
    check("kliku thërret prompt()", pg.evaluate("window.__promptCalled === true"))
    check("bar fshihet pas zgjedhjes", pg.locator("#pwaBar").count() == 0)
    ctx.close()

    # ---------- 5. Standalone: bar nuk shfaqet ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.add_init_script("""(() => {
      const orig = window.matchMedia.bind(window);
      window.matchMedia = (q) => q.includes('display-mode: standalone')
        ? { matches: true, media: q, addEventListener() {}, addListener() {}, removeEventListener() {}, removeListener() {} }
        : orig(q);
    })();""")
    pg.goto(BASE + "/index.html")
    pg.wait_for_timeout(500)
    pg.evaluate("""() => {
      const e = new Event('beforeinstallprompt');
      e.prompt = () => {}; e.userChoice = Promise.resolve({ outcome: 'dismissed' });
      window.dispatchEvent(e);
    }""")
    pg.wait_for_timeout(500)
    check("standalone: bar NUK shfaqet", pg.locator("#pwaBar").count() == 0)
    ctx.close()

    # ---------- 6. iOS Safari: hint një herë ----------
    ictx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
                         user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    ipg = ictx.new_page()
    ipg.goto(BASE + "/index.html")
    try:
        ipg.wait_for_selector("#pwaBar", timeout=6000)
        hint_ok = "Ekranin Kryesor" in ipg.locator("#pwaBar").inner_text()
    except Exception:
        hint_ok = False
    check("iOS: hint 'Shto në Ekranin Kryesor' shfaqet", hint_ok)
    if hint_ok:
        ipg.screenshot(path=f"{ROOT}/screenshots/pwa-ios-hint.png")
    flag = ipg.evaluate("localStorage.getItem('tryeza.pwa.ioshint.v1')")
    check("iOS: flag 'seen' u ruajt", flag == "1")
    ipg.reload()
    ipg.wait_for_timeout(3200)
    check("iOS: hint NUK rishfaqet", ipg.locator("#pwaBar").count() == 0)
    ictx.close()

    # ---------- 7. Regresion: të gjitha faqet x desktop/mobile x SQ/EN, 0 gabime ----------
    sweep_errs = []
    for lang in ["sq", "en"]:
        for vp, tag in [({"width": 1440, "height": 900}, "desktop"), ({"width": 390, "height": 844}, "mobile")]:
            ctx = b.new_context(viewport=vp)
            if lang == "en":
                ctx.add_init_script("localStorage.setItem('tryeza.lang.v1','en')")
            pg = ctx.new_page()
            pg.on("pageerror", lambda e, t=tag, l=lang: sweep_errs.append(f"{l}/{t} pageerror: {e}"))
            pg.on("console", lambda m, t=tag, l=lang: sweep_errs.append(f"{l}/{t} console: {m.text}") if m.type == "error" else None)
            for page in PAGES:
                pg.goto(BASE + "/" + page, wait_until="load", timeout=20000)
                pg.wait_for_timeout(250)
            ctx.close()
    check("regresion: 15 faqe x 2 viewport x SQ/EN = 0 gabime", not sweep_errs, " | ".join(sweep_errs[:5]))

    # ---------- 8. i18n: paritet SQ=EN + çelësat pwa ----------
    ctx = b.new_context()
    pg = ctx.new_page()
    pg.goto(BASE + "/index.html")
    par = pg.evaluate("""() => {
      const sq = Object.keys(I18N.STR.sq).sort(), en = Object.keys(I18N.STR.en).sort();
      return { same: JSON.stringify(sq) === JSON.stringify(en),
               pwaSq: ['pwa.install','pwa.installTxt','pwa.iosHint','pwa.close'].every(k => I18N.STR.sq[k]),
               pwaEn: ['pwa.install','pwa.installTxt','pwa.iosHint','pwa.close'].every(k => I18N.STR.en[k]) };
    }""")
    check("i18n paritet SQ=EN", par["same"])
    check("i18n çelësat pwa.* në SQ+EN", par["pwaSq"] and par["pwaEn"])
    ctx.close()
    b.close()

print(f"\n===== PWA: {len(passes)} PASS, {len(fails)} FAIL =====")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
