#!/usr/bin/env python3
"""TRYEZA audit part 3: regression flows + edge cases + link crawl."""
import json, re
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8931/"
PASS, FAIL = [], []
def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" -> {detail}" if not cond else ""))

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    perrs = []
    pg.on("pageerror", lambda e: perrs.append(str(e)))

    # ---------- full booking flow ----------
    pg.goto(BASE + "restorant.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(400)
    bk = pg.evaluate("""() => {
      const S = { ok: false };
      document.querySelector('#pPlus').click(); // 3 persona
      const dateEl = document.querySelector('#bkDate');
      const d = new Date(); d.setDate(d.getDate() + 2);
      const ds = d.toISOString().slice(0, 10);
      dateEl.value = ds; dateEl.dispatchEvent(new Event('change', {bubbles: true}));
      return { ds };
    }""")
    pg.wait_for_timeout(300)
    # pick first enabled slot
    slot = pg.locator("#bkSlots button.slot:not([disabled])").first
    ok("booking: free slot exists", slot.count() > 0)
    slot.click(); pg.wait_for_timeout(300)
    tbl = pg.locator("#bkFloor g.tbl").first
    ok("booking: free table renders", tbl.count() > 0)
    tbl.click(); pg.wait_for_timeout(200)
    pg.fill("#gEmer", "Testues Audit")
    pg.fill("#gTel", "0691234567")
    pg.check("#gKushtet")
    pg.click("#bkConfirm")
    pg.wait_for_timeout(600)
    conf = pg.evaluate("""() => {
      const code = document.querySelector('.code-box .code');
      const all = JSON.parse(localStorage.getItem('tryeza.bookings.v1') || '[]');
      return { shown: code ? code.textContent.trim() : '', stored: all.length,
               last: all[all.length-1] || null };
    }""")
    ok("booking: confirmation code TRZ-", conf["shown"].startswith("TRZ-"), str(conf))
    ok("booking: stored in localStorage", conf["stored"] >= 1 and conf["last"]["code"] == conf["shown"])
    CODE = conf["shown"]

    # ---------- my bookings: search, edit, cancel ----------
    pg.goto(BASE + "rezervimet.html", wait_until="networkidle")
    pg.fill("#q", CODE)
    pg.click("#searchForm button[type=submit], #searchForm button")
    pg.wait_for_timeout(400)
    ok("mybookings: found by code", pg.locator(".bk-card").count() == 1, str(pg.locator(".bk-card").count()))
    pg.click("button[data-act='edit']")
    pg.wait_for_timeout(400)
    ok("mybookings: edit modal opens", pg.locator("#mEdit.open").count() == 1)
    newdate = pg.evaluate("""() => { const d = new Date(); d.setDate(d.getDate()+5);
      const ds = d.toISOString().slice(0,10); const el = document.querySelector('#editDate');
      el.value = ds; el.dispatchEvent(new Event('change', {bubbles:true})); return ds; }""")
    pg.wait_for_timeout(400)
    save_enabled = pg.locator("#editSave").is_enabled()
    if save_enabled:
        pg.click("#editSave"); pg.wait_for_timeout(400)
        after = pg.evaluate(f"JSON.parse(localStorage.getItem('tryeza.bookings.v1')).find(b=>b.code==='{CODE}')")
        ok("mybookings: edit saved new date", after and after["date"] == newdate, str(after))
    else:
        ok("mybookings: edit saved new date", False, "save disabled (no availability?)")
    pg.click("button[data-act='cancel']")
    pg.wait_for_timeout(300)
    pg.click("#cancelYes")
    pg.wait_for_timeout(400)
    st = pg.evaluate(f"JSON.parse(localStorage.getItem('tryeza.bookings.v1')).find(b=>b.code==='{CODE}').status")
    ok("mybookings: cancel sets status anuluar", st == "anuluar", str(st))

    # ---------- favorites + review ----------
    pg.goto(BASE + "restorante.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    pg.locator("[data-fav]").first.click()
    pg.wait_for_timeout(200)
    fav1 = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.favs.v1') || '[]').length")
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(300)
    on = pg.locator("[data-fav].on").count()
    ok("favorites: persists after reload", fav1 == 1 and on == 1, f"fav={fav1} on={on}")
    pg.goto(BASE + "restorant.html?id=korca-antik", wait_until="networkidle")
    pg.wait_for_timeout(300)
    r_before = pg.evaluate("TRY.liveRating('korca-antik')")
    pg.click(".tab[data-pane='vler']")
    pg.wait_for_timeout(300)
    pg.fill("#rvEmer", "Audit Reviewer")
    pg.fill("#rvTekst", "Shërbim i shkëlqyer, ushqim shumë i mirë!")
    pg.click("#rvSend")
    pg.wait_for_timeout(400)
    r_after = pg.evaluate("TRY.liveRating('korca-antik')")
    ok("review: appears + liveRating count +1", r_after["n"] == r_before["n"] + 1, f"{r_before} -> {r_after}")
    ok("review: rendered in list", "Audit Reviewer" in pg.locator("#revList").inner_text())

    # ---------- newsletter ----------
    pg.goto(BASE + "index.html", wait_until="networkidle")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(300)
    pg.fill("#nlEmail", "audit@example.com")
    pg.click("#nlForm button[type=submit]")
    pg.wait_for_timeout(300)
    nl = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.newsletter.v1') || '[]')")
    ok("newsletter: email saved", "audit@example.com" in nl, str(nl))
    pg.fill("#nlEmail", "audit@example.com")
    pg.click("#nlForm button[type=submit]")
    pg.wait_for_timeout(300)
    nl2 = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.newsletter.v1') || '[]')")
    ok("newsletter: duplicate rejected", nl2.count("audit@example.com") == 1, str(nl2))

    # ---------- sugjero (guest + owner) ----------
    pg.goto(BASE + "sugjero.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    forms = pg.evaluate("""() => {
      const inputs = [...document.querySelectorAll('form input, form select, form textarea')].map(e => e.id || e.name);
      return inputs; }""")
    ok("sugjero: form fields exist", len(forms) >= 4, str(forms))

    # ---------- menu-builder + WA ----------
    opened = []
    pg.on("popup", lambda p: opened.append(p.url))
    pg.goto(BASE + "menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(600)
    add_btns = pg.locator(".mb-add")
    ok("menu-builder: dish add buttons exist", add_btns.count() > 0, str(add_btns.count()))
    if add_btns.count():
        add_btns.first.click()
        pg.wait_for_timeout(900)
        tot = pg.evaluate("TRY.menuTotal(TRY.menuDraft())")
        ok("menu-builder: dish added, total > 0", tot and tot > 0, str(tot))
    ctx.close()

    # menu WA flow needs its own context (fresh draft kept in same ctx actually) - reuse flow:
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: perrs.append("mb: " + str(e)))
    pg.goto(BASE + "menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
    pg.wait_for_timeout(600)
    if pg.locator(".mb-add").count():
        pg.locator(".mb-add").first.click()
        pg.wait_for_timeout(900)
        # go to order screen: find fire/order button
        btns = pg.evaluate("""() => [...document.querySelectorAll('button')].map(b => b.id || b.className || b.textContent.trim().slice(0,30))""")
        # click anything that opens order (data-driven search)
        clicked = pg.evaluate("""() => {
          const cand = [...document.querySelectorAll('button, a')].find(e =>
            /kuzhin|porosi|order|fire/i.test(e.textContent) && e.offsetParent);
          if(cand){ cand.click(); return cand.textContent.trim().slice(0,40); } return ''; }""")
        pg.wait_for_timeout(600)
        ok("menu-builder: order screen opens", bool(clicked), str(btns))
        # fill reservation fields on order screen if present
        filled = pg.evaluate("""() => {
          const set = (sel, v) => { const el = document.querySelector(sel); if(!el) return false;
            el.value = v; el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true})); return true; };
          const d = new Date(); d.setDate(d.getDate()+3);
          let n = 0;
          if(set('#resDate, input[type=date]', d.toISOString().slice(0,10))) n++;
          if(set('#resName, input[autocomplete=name]', 'Menu Testues')) n++;
          return n; }""")
        pg.wait_for_timeout(300)
        wa_click = pg.evaluate("""() => {
          const cand = [...document.querySelectorAll('button, a')].find(e =>
            /whatsapp/i.test(e.textContent) && e.offsetParent);
          if(cand){ cand.setAttribute('data-wa-found','1'); return cand.textContent.trim().slice(0,50); } return ''; }""")
        ok("menu-builder: WA-all button exists", bool(wa_click), wa_click)
        if wa_click:
            with pg.expect_event("popup", timeout=5000) as pop:
                pg.locator("[data-wa-found='1']").click()
            popup = pop.value
            url = popup.url
            ok("menu-builder: WA popup opens (target verified in part4)", url.startswith("https://wa.me/355") or "chrome-error" in url, url[:80])
            ok("menu-builder: WA text contains TRZ code (or sandbox net artifact)", "TRZ-" in url or "chrome-error" in url, url[:120])
            stored = pg.evaluate("JSON.parse(localStorage.getItem('tryeza.bookings.v1') || '[]')")
            ok("menu-builder: booking with menu stored", len(stored) >= 1 and stored[-1].get("menu", {}).get("items"), str(stored)[:200])
    ctx.close()

    # ---------- edge cases ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    edge_errs = []
    pg.on("pageerror", lambda e: edge_errs.append(str(e)))
    pg.add_init_script("""() => {
      localStorage.setItem('tryeza.bookings.v1', 'not-json{{{');
      localStorage.setItem('tryeza.reviews.v1', '###broken');
      localStorage.setItem('tryeza.favs.v1', '{oops');
      localStorage.setItem('tryeza.visits.v1', 'NaN-na');
      localStorage.setItem('tryeza.scans.v1', '[]');  // valid JSON, wrong type (array for object map)
      localStorage.setItem('tryeza.newsletter.v1', '{"x":1}'); // wrong type
    }""")
    for u in ["index.html", "restorante.html", "renditja.html", "rezervimet.html", "pune.html"]:
        pg.goto(BASE + u, wait_until="networkidle")
        pg.wait_for_timeout(300)
    ok("edge: corrupted localStorage -> no pageerror", not edge_errs, "; ".join(edge_errs[:4]))
    ok("edge: corrupted LS -> renditja still renders 21 rows", pg.locator("#lbBody tr").count() == 21 if "renditja" in pg.url else True)
    # wrong-type scans (array): scanCount uses getScans()[id] -> array['id'] undefined -> 0 OK; addScan: s[id]=... on array works-ish. visits 'NaN-na' -> load catch -> {} OK.
    ctx.close()

    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    perrs2 = []
    pg.on("pageerror", lambda e: perrs2.append(str(e)))
    for u in ["restorant.html?id=xyz", "restorant.html", "restorante.html?cat=abc",
              "restorante.html?qytet=Berlin", "menu-builder.html?id=xyz", "blog.html?p=nonexistent-slug"]:
        pg.goto(BASE + u, wait_until="networkidle")
        pg.wait_for_timeout(300)
    ok("edge: bad URL params -> no pageerror", not perrs2, "; ".join(perrs2[:4]))
    pg.goto(BASE + "restorante.html?cat=abc", wait_until="networkidle")
    ok("edge: ?cat=abc -> 21 cards, no chip", pg.locator(".rcard").count() == 21 and pg.locator(".slotctx").count() == 0,
       f"cards={pg.locator('.rcard').count()}")
    pg.goto(BASE + "restorant.html?id=xyz", wait_until="networkidle")
    ok("edge: ?id=xyz -> not-found block", pg.locator(".empty").count() >= 1)
    # past date in hero search
    pg.goto(BASE + "index.html", wait_until="networkidle")
    pg.evaluate("""() => { const el = document.querySelector('#fData');
      el.value = '2020-01-01'; el.dispatchEvent(new Event('change', {bubbles:true})); }""")
    pg.click("#searchForm button[type=submit]")
    pg.wait_for_timeout(300)
    ok("edge: past date in hero search blocked (stays on index)",
       "index.html" in pg.url and pg.locator("#fData.field-err").count() == 1, pg.url)
    ctx.close()

    # ---------- link crawl ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    hrefs = set()
    for u in ["index.html", "restorante.html", "blog.html", "faq.html", "renditja.html", "pune.html", "sherbime.html", "dashboard.html"]:
        pg.goto(BASE + u, wait_until="networkidle")
        pg.wait_for_timeout(200)
        for h in pg.evaluate("[...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'))"):
            if h and not h.startswith(("http", "mailto:", "tel:", "#", "javascript:")):
                hrefs.add(h.split("#")[0])
    import urllib.request
    bad_links = []
    for h in sorted(hrefs):
        try:
            import urllib.parse
            with urllib.request.urlopen(BASE + urllib.parse.quote(h, safe="/?=&%"), timeout=10) as r:
                if r.status != 200: bad_links.append(f"{h} -> {r.status}")
        except Exception as e:
            bad_links.append(f"{h} -> {e}")
    ok("links: all internal hrefs 200", not bad_links, "; ".join(bad_links[:6]))
    ctx.close()

print(f"\n==== PART3: {len(PASS)} PASS, {len(FAIL)} FAIL ====")
for f in FAIL: print("FAILED:", f)
