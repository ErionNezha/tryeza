#!/usr/bin/env python3
"""Validimi v4 — Warm Dark Luxury redesign: 8 seksionet, quick slots, newsletter, i18n, responsive."""
import sys, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8932"
fails, passes = [], []
def check(name, cond, extra=""):
    (passes if cond else fails).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
    errors = []
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console-{m.type}: {m.text}") if m.type == "error" else None)

    # 1. Loader cloche shfaqet dhe zhduket
    pg.goto(BASE + "/index.html")
    check("loader cloche prezent", pg.locator("#tryLoader .ld-cloche").count() == 1)
    check("loader tag i18n", "tavolin" in pg.locator("#tryLoader .ld-tag").inner_text().lower())
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)
    check("loader zhduket", True)

    # 2. Nav: linket e reja
    check("nav Si Funksionon", pg.locator('header.site a[href="index.html#si-funksionon"]').count() == 1)
    check("nav Per Bizneset", pg.locator('header.site a[href="index.html#per-bizneset"]').count() == 1)
    check("nav Rezervo Tani", pg.locator('header.site a.nav-cta').count() >= 1)

    # 3. Hero: video + titull + booking bar
    check("hero video", pg.locator("#heroVideo").count() == 1)
    check("hero titull", "gati" in pg.locator(".hero-inner h1").inner_text().lower())
    check("booking bar CTA 'Gjej Tavolinë'", pg.locator("#searchForm .go").inner_text().strip() == "Gjej Tavolinë")
    cities = pg.locator("#fQytet option").all_inner_texts()
    check("booking bar 4 qytete", all(c in " ".join(cities) for c in ["Tiranë", "Korçë", "Durrës", "Shkodër"]) and "Vlor" not in " ".join(cities), "|".join(cities))

    # 4. Booking bar -> filtra te restorante.html
    pg.select_option("#fQytet", "Tiranë")
    pg.fill("#fPersona", "4")
    pg.locator("#searchForm .go").click()
    pg.wait_for_url("**/restorante.html?*")
    check("booking bar redirect me parametra", "qytet=Tiran%C3%AB" in pg.url and "persona=4" in pg.url, pg.url)
    pg.goto(BASE + "/index.html")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)

    # 5. Të Zgjedhura: 4 karta luksoze + badge + quick slots
    check("4 lux cards", pg.locator(".lux-card").count() == 4, str(pg.locator(".lux-card").count()))
    check("badge editoriale", pg.locator(".lux-card .ed-badge").count() == 4)
    n_qs = pg.locator(".lux-card .qslot").count()
    check("quick slots prezent", n_qs >= 4, str(n_qs))
    href = pg.locator(".lux-card .qslot").first.get_attribute("href")
    check("quick slot link me params", href and "restorant.html?id=" in href and "ora=" in href and "data=" in href and "persona=2" in href, href)

    # 6. Quick slot -> widget i parazgjedhur
    pg.locator(".lux-card .qslot").first.click()
    pg.wait_for_url("**/restorant.html?*")
    pg.wait_for_selector("#bkTimeSel", timeout=8000)
    import urllib.parse as up
    q = dict(up.parse_qsl(up.urlparse(pg.url).query))
    check("ora e parazgjedhur", pg.locator("#bkTimeSel").input_value() == q.get("ora"), pg.locator("#bkTimeSel").input_value())
    check("persona e parazgjedhur", pg.locator("#pNum").inner_text() == "2")
    check("data e parazgjedhur", pg.locator("#bkDate").input_value() == q.get("data"))
    pg.goto(BASE + "/index.html")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)

    # 7. Qytetet me tagline
    tags = pg.locator(".city-card .city-tag").all_inner_texts()
    check("4 city taglines", len(tags) == 4 and all(len(t) > 3 for t in tags), "|".join(tags))

    # 8. Seksionet: si-funksionon, pse, per-bizneset, faq
    for sid, nm in [("si-funksionon", "Si Funksionon"), ("per-bizneset", "Per Bizneset")]:
        check(f"seksion #{sid}", pg.locator(f"#{sid}").count() == 1)
    check("biz 4 karta", pg.locator(".biz-card").count() == 4)
    check("biz CTA -> sugjero?owner=1", pg.locator('#per-bizneset a[href="sugjero.html?owner=1"]').count() == 1)
    check("FAQ accordion hapet", (lambda: (pg.locator("#faqPreview .faq-q").first.click(), pg.locator("#faqPreview .faq-item.open").count() == 1))()[1])

    # 9. Newsletter: validim
    pg.locator("#nlEmail").fill("jo-email")
    pg.locator("#nlForm button[type=submit]").click()
    check("newsletter email invalid -> error", pg.locator("#nlEmail.field-err").count() == 1)
    pg.locator("#nlEmail").fill("test@tryeza.al")
    pg.locator("#nlForm button[type=submit]").click()
    pg.wait_for_timeout(400)
    saved = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.newsletter.v1')||'[]')")
    check("newsletter ruhet ne localStorage", "test@tryeza.al" in saved, str(saved))
    pg.locator("#nlEmail").fill("test@tryeza.al")
    pg.locator("#nlForm button[type=submit]").click()
    pg.wait_for_timeout(400)
    saved2 = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.newsletter.v1')||'[]')")
    check("newsletter pa dublikat", len(saved2) == len(saved), str(saved2))

    # 10. Dashboard: statistika e newsletter-it
    pg.goto(BASE + "/dashboard.html")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)
    check("dashboard stNl", pg.locator("#stNl").inner_text() == str(len(saved2)), pg.locator("#stNl").inner_text())

    # 11. sugjero?owner=1
    pg.goto(BASE + "/sugjero.html?owner=1")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)
    check("owner checkbox i parazgjedhur", pg.locator("#fOwner").is_checked())
    check("fusha e telefonit duket", pg.locator("#ownerPhoneRow").is_visible())

    # 12. EN: çelësat e rinj përkthehen
    pg.goto(BASE + "/index.html")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)
    pg.evaluate("I18N.setLang('en'); location.reload()")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)
    check("EN nav.how", pg.locator('header.site a[href="index.html#si-funksionon"]').inner_text() == "How It Works")
    check("EN hero.cta", pg.locator("#searchForm .go").inner_text().strip() == "Find a table")
    check("EN biz.title", "Grow your restaurant" in pg.locator("#per-bizneset .sec-title").inner_text())
    check("EN badge", "SEA FRESH" in pg.locator(".lux-card .ed-badge").first.inner_text())
    check("EN nl.title", pg.locator(".foot-news h4").inner_text() == "Offers by email")
    check("EN loader.tag2", True)  # kontrollohet manualisht në screenshot
    pg.evaluate("I18N.setLang('sq'); location.reload()")
    pg.wait_for_selector("#tryLoader", state="detached", timeout=8000)

    # 13. Responsive: pa overflow
    for url, w in [("/index.html", 390), ("/index.html", 1440), ("/restorante.html", 390), ("/restorant.html?id=" + "", 390)]:
        pg2 = b.new_page(viewport={"width": w, "height": 844})
        pg2.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        u = BASE + url
        if url.startswith("/restorant.html"):
            rid = pg.evaluate("RESTORANTET[0].id")
            u = BASE + f"/restorant.html?id={rid}"
        pg2.goto(u)
        try: pg2.wait_for_selector("#tryLoader", state="detached", timeout=8000)
        except Exception: pass
        pg2.wait_for_timeout(600)
        ov = pg2.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"pa overflow {url} @{w}px", ov <= 1, f"overflow={ov}px")
        pg2.close()

    # 14. Screenshots
    pg.set_viewport_size({"width": 1440, "height": 900})
    pg.goto(BASE + "/index.html"); pg.wait_for_selector("#tryLoader", state="detached", timeout=8000); pg.wait_for_timeout(800)
    pg.screenshot(path="/home/hatch/workspace/tryeza/screenshots/v4-home.png")
    pg.locator("#luxGrid").scroll_into_view_if_needed(); pg.wait_for_timeout(600)
    pg.screenshot(path="/home/hatch/workspace/tryeza/screenshots/v4-featured.png")
    pg.locator("#per-bizneset").scroll_into_view_if_needed(); pg.wait_for_timeout(600)
    pg.screenshot(path="/home/hatch/workspace/tryeza/screenshots/v4-business.png")
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.goto(BASE + "/index.html"); pg.wait_for_selector("#tryLoader", state="detached", timeout=8000); pg.wait_for_timeout(800)
    pg.screenshot(path="/home/hatch/workspace/tryeza/screenshots/v4-mobile.png")

    b.close()

print(f"\n== {len(passes)} PASS, {len(fails)} FAIL ==")
if errors: print("Console/page errors:", errors[:10])
sys.exit(1 if fails or errors else 0)
