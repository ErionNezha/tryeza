#!/usr/bin/env python3
"""TRYEZA audit part 4: WA URL capture, i18n spot checks, sugjero submit, assistant EN."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8931/"
PASS, FAIL = [], []
def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" -> {detail}" if not cond else ""))

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])

    # ---------- dashboard stat label SQ / EN ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "dashboard.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    lbl_sq = pg.locator('[data-i18n="db.stNoshow"]').first.inner_text()
    ok("dashboard SQ: stat label is Albanian 'No-show gjithsej'", lbl_sq == "No-show gjithsej", repr(lbl_sq))
    ctx.close()
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script("localStorage.setItem('tryeza.lang.v1','en')")
    pg = ctx.new_page()
    pg.goto(BASE + "dashboard.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    lbl_en = pg.locator('[data-i18n="db.stNoshow"]').first.inner_text()
    ok("dashboard EN: stat label is 'No-shows total'", lbl_en == "No-shows total", repr(lbl_en))
    nav_en = pg.locator(".nav-links a").first.inner_text()
    ok("dashboard EN: nav translated", nav_en == "Home", repr(nav_en))
    ctx.close()

    # ---------- menu-builder rm aria-label ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(500)
    if pg.locator(".mb-add").count():
        pg.locator(".mb-add").first.click()
        pg.wait_for_timeout(900)
        # open order/preview where .rm buttons live
        pg.evaluate("""() => { const c = [...document.querySelectorAll('button,a')].find(e =>
            /kuzhin|porosi|order|fire|shiko/i.test(e.textContent) && e.offsetParent); if(c) c.click(); }""")
        pg.wait_for_timeout(600)
        rm = pg.locator("button.rm")
        if rm.count():
            al = rm.first.get_attribute("aria-label")
            ok("menu-builder: rm aria-label is human text (not 'mb.remove')", al not in (None, "", "mb.remove"), repr(al))
        else:
            ok("menu-builder: rm aria-label is human text (not 'mb.remove')", False, "no .rm buttons found")
    ctx.close()

    # ---------- WA URL capture via route interception ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    captured = []
    def handle(route):
        captured.append(route.request.url)
        route.fulfill(status=200, content_type="text/html", body="<html><body>wa</body></html>")
    ctx.route("**://wa.me/**", handle)
    pg.goto(BASE + "menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(500)
    pg.locator(".mb-add").first.click()
    pg.wait_for_timeout(900)
    pg.evaluate("""() => { const c = [...document.querySelectorAll('button,a')].find(e =>
        /kuzhin|porosi|order|fire/i.test(e.textContent) && e.offsetParent); if(c) c.click(); }""")
    pg.wait_for_timeout(500)
    pg.evaluate("""() => {
      const set = (sel, v) => { const el = document.querySelector(sel); if(!el) return;
        el.value = v; el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true})); };
      const d = new Date(); d.setDate(d.getDate()+3);
      set('#resDate, input[type=date]', d.toISOString().slice(0,10));
      set('#resName, input[autocomplete=name]', 'Menu Testues');
      const timeSel = document.querySelector('#resTime, select');
      if(timeSel && timeSel.tagName === 'SELECT' && timeSel.options.length > 1) timeSel.selectedIndex = 1;
      const guest = document.querySelector('#resGuests, input[type=number]');
      if(guest) guest.value = 2;
    }""")
    pg.wait_for_timeout(300)
    clicked = pg.evaluate("""() => { const c = [...document.querySelectorAll('button,a')].find(e =>
        /whatsapp/i.test(e.textContent) && e.offsetParent); if(c){ c.click(); return true; } return false; }""")
    pg.wait_for_timeout(1200)
    wa_urls = [u for u in captured if u.startswith("https://wa.me/")]
    ok("mb WA: click opens wa.me", bool(clicked) and len(wa_urls) >= 1, str(captured))
    if wa_urls:
        u = wa_urls[-1]
        ok("mb WA: number is the restaurant's (Era Blloku +355 69 406 6662)", u.split("?")[0] == "https://wa.me/355694066662", u[:60])
        import urllib.parse
        txt = urllib.parse.unquote(u)
        ok("mb WA: message contains TRZ code", "TRZ-" in txt, txt[:150])
        ok("mb WA: message contains a dish + total", ("lek" in txt.lower() or "L" in txt) and len(txt) > 80, txt[:200])
    ctx.close()

    # ---------- sugjero submit ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "sugjero.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    pg.fill("#fEmer", "Restoranti Audit Test")
    pg.select_option("#fQytet", "Tiranë")
    pg.fill("#fArsye", "Arsye testimi per audit te plote te formes se sugjerimit.")
    pg.click("#suggForm button[type=submit]")
    pg.wait_for_timeout(400)
    saved = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.suggestions.v1') || '[]')")
    ok("sugjero: suggestion saved + rendered",
       any(s.get("emer") == "Restoranti Audit Test" for s in saved) and "Restoranti Audit Test" in pg.locator("#suggList").inner_text(),
       str(saved)[:150])
    # owner mode
    pg.goto(BASE + "sugjero.html?owner=1", wait_until="networkidle")
    pg.wait_for_timeout(300)
    vis = pg.evaluate("!document.querySelector('#ownerPhoneRow').hidden && document.querySelector('#fOwner').checked")
    ok("sugjero: ?owner=1 checks owner + shows phone row", bool(vis))
    ctx.close()

    # ---------- assistant EN + more intents SQ ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script("localStorage.setItem('tryeza.lang.v1','en')")
    pg = ctx.new_page()
    perrs = []
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(BASE + "restorante.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    pg.click(".asst-btn")
    pg.wait_for_timeout(300)
    greet = pg.locator(".asst-msg.bot").first.inner_text()
    ok("assistant EN: greeting in English", any(w in greet for w in ["Hello", "Hi", "help"]), repr(greet[:80]))
    pg.fill("#asstInput", "What is the best restaurant in Tirana?")
    pg.press("#asstInput", "Enter")
    pg.wait_for_timeout(700)
    cities = pg.evaluate("""() => [...document.querySelectorAll('.asst-card')].map(a => {
        const id = new URL(a.href).searchParams.get('id'); return TRY.restById(id).qytet; })""")
    ok("assistant EN: best in Tirana -> only Tirana", len(cities) >= 1 and all(c == "Tiranë" for c in cities), str(cities))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(200)
    ok("assistant: Escape closes panel", pg.locator(".asst-panel.open").count() == 0)
    ok("assistant EN: no pageerror", not perrs, "; ".join(perrs))
    ctx.close()

    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "index.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    pg.click(".asst-btn"); pg.wait_for_timeout(300)
    pg.fill("#asstInput", "Ku ka ushqim deti?")
    pg.press("#asstInput", "Enter"); pg.wait_for_timeout(700)
    sea = pg.evaluate("""() => [...document.querySelectorAll('.asst-card')].map(a => {
        const id = new URL(a.href).searchParams.get('id'); return TRY.restById(id).kuzhina; })""")
    SEA = ["Seafood", "Peshk", "Fruta deti"]
    ok("assistant SQ: seafood intent -> seafood restaurants",
       len(sea) >= 1 and all(any(k in SEA for k in ks) for ks in sea), str(sea))
    pg.fill("#asstInput", "Dua diçka tradicionale")
    pg.press("#asstInput", "Enter"); pg.wait_for_timeout(700)
    trad = pg.evaluate("""() => { const lists=[...document.querySelectorAll('.asst-msg.bot')];
        const last=lists[lists.length-1];
        return [...last.querySelectorAll('.asst-card')].map(a => {
          const id=new URL(a.href).searchParams.get('id'); return TRY.restById(id).kuzhina; }); }""")
    ok("assistant SQ: traditional intent -> traditional cuisine",
       len(trad) >= 1 and all(any("tradicionale" in k.lower() for k in ks) for ks in trad), str(trad))
    ctx.close()

    # ---------- pune EN ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script("localStorage.setItem('tryeza.lang.v1','en')")
    pg = ctx.new_page()
    pg.goto(BASE + "pune.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    h1 = pg.locator("h1").inner_text()
    ok("pune EN: h1 translated", "Jobs" in h1 or "restaurants" in h1.lower(), repr(h1))
    pg.fill("#jobQ", "era")
    pg.wait_for_timeout(300)
    ok("pune EN: search works", pg.locator(".job-card").count() >= 1, str(pg.locator(".job-card").count()))
    ctx.close()

print(f"\n==== PART4: {len(PASS)} PASS, {len(FAIL)} FAIL ====")
for f in FAIL: print("FAILED:", f)
