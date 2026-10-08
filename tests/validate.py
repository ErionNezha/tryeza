#!/usr/bin/env python3
"""TRYEZA — 360° functional validation with Playwright (real user path)."""
import sys, re, time, subprocess, os, signal
from playwright.sync_api import sync_playwright

ROOT = "/home/hatch/workspace/tryeza"
SHOT = os.path.join(ROOT, "screenshots")
os.makedirs(SHOT, exist_ok=True)
PORT = 8941
BASE = f"http://127.0.0.1:{PORT}"

errors, fails = [], []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {extra}" if extra and not cond else ""))
    if not cond: fails.append(name + (" | "+extra if extra else ""))

# --- start server (PID file, never pkill -f) ---
srv = subprocess.Popen(["python3","-m","http.server",str(PORT),"--bind","127.0.0.1"],
                       cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
open("/tmp/tryeza_srv.pid","w").write(str(srv.pid))
time.sleep(1.2)

console_errs = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox","--disable-gpu"])
        pg = b.new_page(viewport={"width":1440,"height":900})
        pg.on("pageerror", lambda e: console_errs.append(f"pageerror: {e}"))
        pg.on("console", lambda m: console_errs.append(f"console.{m.type}: {m.text}") if m.type=="error" else None)

        # 1. HOME
        pg.goto(BASE+"/index.html"); pg.wait_for_timeout(900)
        check("home title", "TRYEZA" in pg.title(), pg.title())
        check("home cards", pg.locator(".rcard").count() >= 8, str(pg.locator(".rcard").count()))
        check("home cities", pg.locator(".city-card").count() == 4)
        pg.screenshot(path=f"{SHOT}/01-home.png")

        # 2. SEARCH -> list
        pg.select_option("#fQytet", "Korçë")
        pg.fill("#fPersona", "4")
        pg.select_option("#fOra", "20:00")
        pg.locator("#searchForm button[type=submit], #searchForm .go").first.click()
        pg.wait_for_timeout(700)
        check("search navigates", "restorante.html" in pg.url and "qytet=Kor%C3%A7%C3%AB" in pg.url, pg.url)
        n = pg.locator(".rcard").count()
        check("korca results = 6", n == 6, str(n))
        check("availability badge", pg.locator(".slotbadge, .slotctx").count() > 0)
        pg.screenshot(path=f"{SHOT}/02-lista.png")

        # 3. filters
        pg.select_option("select#rendit, #fRendit", "cmim-asc") if pg.locator("#fRendit").count() else None
        pg.screenshot(path=f"{SHOT}/02b-lista.png")

        # 4. DETAIL page
        rid = pg.locator(".rcard").first.get_attribute("data-id")
        pg.goto(f"{BASE}/restorant.html?id={rid}#rezervo"); pg.wait_for_timeout(900)
        check("detail banner", pg.locator(".banner").count() == 1)
        check("tabs = 6", pg.locator(".tab").count() == 6, str(pg.locator(".tab").count()))
        pg.screenshot(path=f"{SHOT}/03-detaj.png")

        # tabs
        for i, name in enumerate(["Përmbledhje","Pjata popullore","Menu","Foto","Vlerësime","Detaje"]):
            pg.locator(".tab").nth(i).click(); pg.wait_for_timeout(200)
            check(f"tab {name} active", pg.locator(".tabpane.active").count()==1)
        pg.screenshot(path=f"{SHOT}/04-vleresime-tab.png")

        # 5. REVIEW submit
        pg.locator(".tab").nth(4).click(); pg.wait_for_timeout(300)  # back to Vlerësime
        before = pg.locator("#revList .review").count()
        pg.fill("#rvEmer", "Testuesi Shqiptar")
        pg.locator('#rvStars button[data-y="5"]').click()
        pg.fill("#rvTekst", "Atmosferë fantastike dhe shërbim i shkëlqyer. Do kthehem patjetër!")
        pg.click("#rvSend"); pg.wait_for_timeout(600)
        after = pg.locator("#revList .review").count()
        check("review added", after == before + 1, f"{before}->{after}")
        check("review persisted", "Testuesi Shqiptar" in (pg.evaluate("localStorage.getItem('tryeza.reviews.v1')") or ""))
        pg.screenshot(path=f"{SHOT}/05-review.png")

        # 6. FAVORITE toggle + persistence
        pg.click("#favBtn"); pg.wait_for_timeout(300)
        on = pg.evaluate("document.getElementById('favBtn').classList.contains('on')")
        pg.reload(); pg.wait_for_timeout(700)
        on2 = pg.evaluate("document.getElementById('favBtn').classList.contains('on')")
        check("fav toggle + persist", on and on2, f"{on}/{on2}")
        pg.click("#favBtn"); pg.wait_for_timeout(200)  # back off

        # 7. BOOKING FLOW
        pg.goto(f"{BASE}/restorant.html?id={rid}#rezervo"); pg.wait_for_timeout(800)
        pg.click("#pPlus"); pg.wait_for_timeout(200)
        check("persona=3", pg.inner_text("#pNum").strip()=="3", pg.inner_text("#pNum"))
        tmr = pg.evaluate("new Date(Date.now()+86400000).toISOString().slice(0,10)")
        pg.fill("#bkDate", tmr); pg.wait_for_timeout(600)
        free = pg.locator("#bkSlots button.slot:not(:disabled)")
        check("has free slots", free.count() > 0, str(free.count()))
        free.first.click(); pg.wait_for_timeout(600)
        sel_time = pg.evaluate("document.querySelector('#bkSlots button.slot.sel')?.dataset.slot")
        check("slot selected", bool(sel_time), str(sel_time))
        pg.locator("#bkZones button").last.click(); pg.wait_for_timeout(600)
        tbls = pg.locator("#bkFloor .tbl:not(.busy)")
        check("free tables shown", tbls.count() > 0, str(tbls.count()))
        tbls.first.click(); pg.wait_for_timeout(300)
        check("table selected", pg.locator("#bkFloor .tbl.sel").count()==1)
        pg.fill("#gEmer", "Erion Testi")
        pg.fill("#gTel", "+355 69 123 4567")
        pg.check("#gKushtet")
        pg.screenshot(path=f"{SHOT}/06-booking-gati.png")
        pg.click("#bkConfirm"); pg.wait_for_timeout(800)
        code = pg.inner_text(".code") if pg.locator(".code").count() else ""
        check("booking confirmed, code TRZ-", bool(re.match(r"TRZ-[A-Z0-9]{6}", code.strip())), code)
        pg.screenshot(path=f"{SHOT}/07-konfirmim.png")
        pg.click("#cfIcs"); pg.wait_for_timeout(500)

        # 8. MY BOOKINGS: search -> modify -> cancel
        pg.goto(BASE+"/rezervimet.html"); pg.wait_for_timeout(700)
        pg.fill("#q", code.strip()); pg.click("#searchForm button[type=submit], #searchForm .btn"); pg.wait_for_timeout(600)
        check("booking found", pg.locator(".bk-card").count() >= 1, str(pg.locator(".bk-card").count()))
        pg.screenshot(path=f"{SHOT}/08-rezervimet.png")
        # modify
        pg.locator("[data-act=edit]").first.click(); pg.wait_for_timeout(400)
        tmr2 = pg.evaluate("new Date(Date.now()+2*86400000).toISOString().slice(0,10)")
        pg.fill("#editDate", tmr2); pg.wait_for_timeout(400)
        pg.select_option("#editTime", "19:30"); pg.wait_for_timeout(400)
        pg.click("#editSave"); pg.wait_for_timeout(600)
        check("booking modified", "19:30" in pg.inner_text("#results"), pg.inner_text("#results")[:120])
        # cancel
        pg.locator("[data-act=cancel]").first.click(); pg.wait_for_timeout(300)
        pg.click("#cancelYes"); pg.wait_for_timeout(500)
        check("booking cancelled", "anuluar" in pg.inner_text("#results").lower())
        pg.screenshot(path=f"{SHOT}/09-anuluar.png")

        # 9. SUGGEST
        pg.goto(BASE+"/sugjero.html"); pg.wait_for_timeout(600)
        pg.fill("#fEmer", "Sofra e Re"); pg.select_option("#fQytet", "Tiranë")
        pg.fill("#fArsye", "Kuzhinë fantastike tradicionale, e provuar personalisht.")
        pg.locator("#suggForm button[type=submit]").click(); pg.wait_for_timeout(500)
        check("suggestion added", "Sofra e Re" in pg.inner_text("body"))
        pg.locator(".sugg .votes button").first.click(); pg.wait_for_timeout(300)
        pg.screenshot(path=f"{SHOT}/10-sugjero.png")

        # 10. DASHBOARD
        pg.goto(BASE+"/dashboard.html"); pg.wait_for_timeout(700)
        pg.click("#genDemo"); pg.wait_for_timeout(700)
        check("demo generated", pg.locator("#dashTableBody tr, .dtable tbody tr").count() > 0)
        check("chart drawn", pg.evaluate("document.querySelector('canvas') ? true : false"))
        pg.screenshot(path=f"{SHOT}/11-dashboard.png")

        # 11. BLOG + article
        pg.goto(BASE+"/blog.html"); pg.wait_for_timeout(600)
        check("blog posts", pg.locator(".post").count() == 6, str(pg.locator(".post").count()))
        slug = pg.evaluate("document.querySelector('.post a').getAttribute('href')")
        pg.goto(BASE+"/"+slug); pg.wait_for_timeout(500)
        check("article view", pg.locator(".article").count()==1)
        pg.screenshot(path=f"{SHOT}/12-blog.png")

        # 12. FAQ
        pg.goto(BASE+"/faq.html"); pg.wait_for_timeout(500)
        pg.locator(".faq-q").first.click(); pg.wait_for_timeout(300)
        check("faq accordion", pg.locator(".faq-item.open").count()==1)
        pg.screenshot(path=f"{SHOT}/13-faq.png")

        # 13. SOURCE page
        pg.goto(BASE+"/kodi.html"); pg.wait_for_timeout(600)
        pg.locator(".code-file .code-head button").first.click(); pg.wait_for_timeout(800)
        check("code loads", pg.locator(".code-body pre").first.inner_text().__len__() > 500)
        check("highlight tokens", pg.locator(".tok-k, .tok-s, .tok-c").count() > 0)
        pg.screenshot(path=f"{SHOT}/14-kodi.png")

        # 14. mobile viewport smoke
        pg.set_viewport_size({"width":390,"height":844})
        pg.goto(BASE+"/index.html"); pg.wait_for_timeout(700)
        pg.screenshot(path=f"{SHOT}/15-mobile.png")
        check("mobile renders", pg.locator(".rcard").count() >= 4)

        b.close()
finally:
    try: os.kill(srv.pid, signal.SIGTERM)
    except Exception: pass

print("\n--- console/page errors:", len(console_errs))
for e in console_errs[:20]: print("  !", e[:220])
print("--- FAILED:", len(fails))
for f in fails: print("  X", f[:220])
sys.exit(1 if fails or console_errs else 0)
