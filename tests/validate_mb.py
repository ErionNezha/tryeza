#!/usr/bin/env python3
"""Validate menu-builder.html: real menu, editorial fallback, totals, fly animation,
booking integration (summary + WhatsApp), i18n, responsive."""
import sys, re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8933"
fails, oks = [], []
def ok(name, cond, extra=""):
    (oks if cond else fails).append(name)
    print(("PASS " if cond else "FAIL ") + name + ((" | " + extra) if extra else ""))

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console-{m.type}: {m.text}") if m.type == "error" else None)

    # 1. builder with REAL menu (Era Blloku, 7 items)
    pg.goto(f"{BASE}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(2200)  # loader
    ok("real menu page loads", pg.locator(".mb-dish").count() == 18, f"dishes={pg.locator('.mb-dish').count()} (7 real + 11 editorial)")
    ok("real menu label", "Nga menuja e restorantit" in pg.content())
    ok("back link", pg.locator("#mbBack").get_attribute("href") == "restorant.html?id=tirana-era-blloku")

    # 2. add 3 dishes -> check live total math + fly animation executed
    prices = []
    for i in range(3):
        btn = pg.locator(".mb-add").nth(i)
        price_txt = pg.locator(".mb-dish").nth(i).locator(".nm span").inner_text()
        prices.append(int(re.search(r"(\d+)", price_txt).group(1)))
        btn.click()
        pg.wait_for_timeout(900)  # fly animation 680ms
    exp = sum(prices)
    tot_txt = pg.locator("#mbTotal").inner_text()
    tot = int(re.search(r"([\d,]+)", tot_txt).group(1).replace(",", ""))
    ok("live total correct (3 dishes)", tot == exp * 2, f"exp={exp*2} got={tot}")
    ok("per-person total", re.sub(r"\D", "", pg.locator("#mbPerP").inner_text()) == str(exp))
    cta_txt = pg.locator("#mbCta").inner_text()
    ok("cta shows fire label (firing flow)", "kuzhin" in cta_txt.lower(), f"cta={cta_txt!r}")
    ok("table filled with 3 dishes", pg.locator("#mbTableDishes .mb-tdish").count() == 3)
    ok("preview list 3 items", pg.locator(".mb-item").count() == 3)
    pg.screenshot(path="screenshots/mb-01-added.png")

    # 3. guests stepper changes total
    pg.locator("#gPlus").click(); pg.wait_for_timeout(300)
    tot3 = int(re.search(r"([\d,]+)", pg.locator("#mbTotal").inner_text()).group(1).replace(",", ""))
    ok("guests stepper x3", tot3 == exp * 3, f"exp={exp*3} got={tot3}")

    # 4. persistence: reload keeps selection
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(2000)
    ok("selection persists after reload", pg.locator(".mb-item").count() == 3)

    # 5. reset
    pg.locator("#mbReset").click(); pg.wait_for_timeout(400)
    ok("reset clears", pg.locator(".mb-item").count() == 0 and "0 L" in pg.locator("#mbTotal").inner_text())

    # 6. editorial fallback (Mullixhiu — no menu)
    pg.goto(f"{BASE}/menu-builder.html?id=tirana-mullixhiu", wait_until="networkidle")
    pg.wait_for_timeout(2000)
    ok("editorial suggestions shown", pg.locator(".mb-dish").count() == 15, f"count={pg.locator('.mb-dish').count()}")
    ok("editorial label clear", "Sugjerime të TRYEZA" in pg.content() and "jo menu zyrtare" in pg.content())

    # 7. CTA -> firing -> order screen -> "Shto te rezervimi" navigates, menu in booking summary
    pg.locator(".mb-add").first.click(); pg.wait_for_timeout(900)
    pg.locator("#mbCta").click()
    pg.wait_for_selector("#mbOrderOv.open", timeout=8000)
    ok("cta opens order screen (firing flow)", pg.locator("#mbOrderOv.open").count() == 1)
    pg.locator("#mbOrderGo").click(); pg.wait_for_timeout(1200)
    ok("order-go navigates to restaurant", "restorant.html?id=tirana-mullixhiu" in pg.url)
    pg.wait_for_timeout(1500)
    summ = pg.locator("#bkSummary").inner_text()
    ok("menu in booking summary", "Menuja:" in summ and "L/person" in summ, summ[:120])

    # 8. complete booking -> WhatsApp text contains dishes
    pg.goto(f"{BASE}/restorant.html?id=tirana-mullixhiu#rezervo", wait_until="networkidle")
    pg.wait_for_timeout(1800)
    tmr = pg.evaluate("new Date(Date.now()+86400000).toISOString().slice(0,10)")
    pg.fill("#bkDate", tmr); pg.wait_for_timeout(800)
    free = pg.locator("#bkSlots button.slot:not(:disabled)")
    if free.count():
        free.first.click(); pg.wait_for_timeout(800)
        zones = pg.locator("#bkZones button")
        if zones.count(): zones.last.click(); pg.wait_for_timeout(800)
        tbls = pg.locator("#bkFloor .tbl:not(.busy)")
        if tbls.count(): tbls.first.click(); pg.wait_for_timeout(400)
        pg.fill("#gEmer", "Test Testi")
        pg.fill("#gTel", "+355691234567")
        pg.check("#gKushtet")
        pg.click("#bkConfirm"); pg.wait_for_timeout(1200)
        code = pg.inner_text(".code") if pg.locator(".code").count() else ""
        ok("booking confirmed", bool(re.match(r"TRZ-[A-Z0-9]{6}", code.strip())), code)
        wa_href = pg.locator(".wa-btn").get_attribute("href") if pg.locator(".wa-btn").count() else ""
        from urllib.parse import unquote
        wa_txt = unquote(wa_href or "")
        ok("whatsapp contains menu", "Menuja:" in wa_txt and "Sallat" in wa_txt, wa_txt[:220])
        pg.screenshot(path="screenshots/mb-02-confirm.png")
    else:
        ok("slot available for booking test", False, "no free slots")

    # 9. EN language: no Albanian left in UI chrome
    pg.goto(f"{BASE}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(2000)
    pg.evaluate("I18N.setLang('en'); location.reload()")
    pg.wait_for_timeout(2600)
    body_en = pg.locator("body").inner_text()
    ok("EN: no Albanian UI strings", "Krijo menunë" not in body_en and "Anëparë" not in body_en and "Fillo nga e para" not in body_en, body_en[:200])
    ok("EN: english present", "Build your dinner menu" in body_en)
    pg.evaluate("I18N.setLang('sq'); location.reload()"); pg.wait_for_timeout(1500)
    pg.screenshot(path="screenshots/mb-03-en.png")

    # 10. mobile 390px: no overflow, sticky bar visible
    m = b.new_page(viewport={"width": 390, "height": 844})
    m.on("pageerror", lambda e: errors.append(f"mobile pageerror: {e}"))
    m.goto(f"{BASE}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    m.wait_for_timeout(2200)
    ov = m.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    ok("mobile no overflow", ov <= 1, f"overflow={ov}px")
    ok("mobile sticky bar visible", m.locator("#mbBar").is_visible())
    m.locator(".mb-add").first.click(); m.wait_for_timeout(900)
    ok("mobile add works", m.locator(".mb-item").count() == 1)
    m.screenshot(path="screenshots/mb-04-mobile.png")

    # 11. restaurant page has builder button
    pg.goto(f"{BASE}/restorant.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(2000)
    ok("builder button on restaurant page", pg.locator("#btnMenuBuilder").count() == 1)

    b.close()

real_errors = [e for e in errors if "favicon" not in e and "fonts" not in e.lower() and "ERR_" not in e]
ok("zero console/page errors", len(real_errors) == 0, "; ".join(real_errors[:3]))
print(f"\n{len(oks)} PASS, {len(fails)} FAIL")
sys.exit(1 if fails else 0)
