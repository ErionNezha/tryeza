#!/usr/bin/env python3
"""TRYEZA audit part 2: functional flows for the NEW code + regressions."""
import json, re, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8931/"
PASS, FAIL = [], []
def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name + (f" [{detail}]" if detail and not cond else ""))
    print(("PASS " if cond else "FAIL ") + name + (f" -> {detail}" if not cond else ""))

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu"])

    # ---------- openNow unit tests (mocked dates) ----------
    ctx = b.new_context(viewport={"width": 1280, "height": 800})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE + "index.html", wait_until="networkidle")
    on = pg.evaluate("""() => {
      const salt = TRY.restById('tirana-salt'), vila = TRY.restById('shkodra-vilabekteshi'),
            padam = TRY.restById('tirana-padam');
      // 2026-10-18 is a Sunday; 2026-10-19 Monday; 2026-10-20 Tuesday; 2026-10-13 Tuesday
      const D = (y,m,d,h,mi) => new Date(y, m-1, d, h, mi);
      return {
        saltSun0130: TRY.openNow(salt, D(2026,10,18,1,30)),   // Sat shift till 02:00 -> OPEN
        saltSun0030: TRY.openNow(salt, D(2026,10,18,0,30)),   // Sat shift -> OPEN
        saltMon0130: TRY.openNow(salt, D(2026,10,19,1,30)),   // Sun shift ended 01:00 -> CLOSED
        saltMon0030: TRY.openNow(salt, D(2026,10,19,0,30)),   // Sun shift till 01:00 -> OPEN
        saltTue1200: TRY.openNow(salt, D(2026,10,20,12,0)),   // OPEN
        saltTue0300: TRY.openNow(salt, D(2026,10,20,3,0)),    // CLOSED
        vilaTue1200: TRY.openNow(vila, D(2026,10,20,12,0)),   // 08-16 / 19-23 -> OPEN
        vilaTue1700: TRY.openNow(vila, D(2026,10,20,17,0)),   // between shifts -> CLOSED
        vilaTue2000: TRY.openNow(vila, D(2026,10,20,20,0)),   // OPEN
        padamAny0100: TRY.openNow(padam, D(2026,10,20,1,0)), // 07:00-02:00 daily -> OPEN
        padamAny0300: TRY.openNow(padam, D(2026,10,20,3,0)), // CLOSED
      };
    }""")
    exp = {"saltSun0130": True, "saltSun0030": True, "saltMon0130": False, "saltMon0030": True,
           "saltTue1200": True, "saltTue0300": False, "vilaTue1200": True, "vilaTue1700": False,
           "vilaTue2000": True, "padamAny0100": True, "padamAny0300": False}
    for k, v in exp.items():
        ok(f"openNow {k}", on.get(k) == v, f"got {on.get(k)} want {v}")
    ok("openNow: no pageerror", not errs, "; ".join(errs))

    # ---------- renditja ----------
    pg.goto(BASE + "renditja.html", wait_until="networkidle")
    pg.wait_for_timeout(400)
    lb = pg.evaluate("""() => {
      const board = TRY.leaderboard();
      const rows = [...document.querySelectorAll('#lbBody tr')];
      const names = rows.map(tr => tr.querySelector('.rn a').textContent.trim());
      const pts = rows.map(tr => parseInt(tr.querySelector('.pts').textContent.trim(), 10));
      const pod = [...document.querySelectorAll('.pod-card h3 a')].map(a => a.textContent.trim());
      const formula = document.querySelector('[data-i18n="lb.formula"]') ? 
        [...document.querySelectorAll('p')].map(p=>p.textContent).join(' ') : '';
      return { boardNames: board.map(x => x.r.emer), boardPts: board.map(x => x.pts),
               names, pts, pod, boardPod: board.slice(0,3).map(x => x.r.emer),
               formulaTxt: formula, rowCount: rows.length,
               nullRows: rows.filter(tr => tr.textContent.includes('—')).length };
    }""")
    ok("renditja: 21 rows", lb["rowCount"] == 21, str(lb["rowCount"]))
    ok("renditja: order == TRY.leaderboard()", lb["names"] == lb["boardNames"])
    ok("renditja: points == pointsFor", lb["pts"] == lb["boardPts"])
    ok("renditja: podium == top3", lb["pod"] == lb["boardPod"], f"{lb['pod']} vs {lb['boardPod']}")
    ok("renditja: null-rating guard '—' present (2 unrated)", lb["nullRows"] >= 2, str(lb["nullRows"]))
    ok("renditja: formula text mentions visits (vizita)", "vizit" in lb["formulaTxt"].lower(), lb["formulaTxt"][:160])

    # ---------- visits & scans ----------
    ctx2 = b.new_context(viewport={"width": 1280, "height": 800})
    p2 = ctx2.new_page()
    p2.goto(BASE + "restorant.html?id=tirana-era-blloku", wait_until="networkidle")
    v1 = p2.evaluate("TRY.visitCount('tirana-era-blloku')")
    p2.reload(wait_until="networkidle")
    v2 = p2.evaluate("TRY.visitCount('tirana-era-blloku')")
    ok("visits: +1 on first open", v1 == 1, str(v1))
    ok("visits: refresh does NOT double", v2 == 1, str(v2))
    pts_before = p2.evaluate("TRY.pointsFor('tirana-era-blloku')")
    p2.goto(BASE + "restorant.html?id=tirana-era-blloku&qr=1", wait_until="networkidle")
    p2.wait_for_timeout(300)
    sc = p2.evaluate("TRY.scanCount('tirana-era-blloku')")
    pts_after = p2.evaluate("TRY.pointsFor('tirana-era-blloku')")
    ok("qr: scan +1", sc == 1, str(sc))
    ok("qr: points +3 per scan", pts_after - pts_before == 3, f"{pts_before}->{pts_after}")
    p2.goto(BASE + "restorant.html?id=nonexistent", wait_until="networkidle")
    ok("visits: bad id page renders not-found", "notFound" in p2.content() or p2.locator(".empty").count() > 0)
    ctx2.close()

    # ---------- pune ----------
    pg.goto(BASE + "pune.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    n0 = pg.locator(".job-card").count()
    ok("pune: 21 cards initially", n0 == 21, str(n0))
    # search by name fragment without diacritics (target: Mullixhiu)
    pg.fill("#jobQ", "mullixhiu")
    pg.wait_for_timeout(300)
    ok("pune: search 'mullixhiu' -> 1", pg.locator(".job-card").count() == 1, str(pg.locator(".job-card").count()))
    # search by lagje term (use a real lagje from data)
    lagje = pg.evaluate("RESTORANTET[3].lagje")
    pg.fill("#jobQ", lagje.split(" ")[0].lower().replace("ë", "e").replace("ç", "c"))
    pg.wait_for_timeout(300)
    cnt_lagje = pg.locator(".job-card").count()
    ok("pune: search by lagje (no diacritics) finds >=1", cnt_lagje >= 1, f"lagje={lagje} cnt={cnt_lagje}")
    pg.fill("#jobQ", "zzzzzz")
    pg.wait_for_timeout(300)
    ok("pune: empty state", pg.locator(".job-card").count() == 0 and pg.locator("#jobGrid .hint").count() > 0)
    pg.fill("#jobQ", "")
    pg.select_option("#jobCity", "Korçë")
    pg.wait_for_timeout(300)
    ok("pune: city Korçë -> 5", pg.locator(".job-card").count() == 5, str(pg.locator(".job-card").count()))
    pg.select_option("#jobSort", "name")
    pg.wait_for_timeout(300)
    names = pg.locator(".job-card h3 a").all_inner_texts()
    ok("pune: sort A-Z", names == sorted(names, key=lambda s: s.lower()), str(names))
    wa = pg.locator(".job-card .btn-wa2").first.get_attribute("href")
    ok("pune: WA link wa.me/355", bool(wa and wa.startswith("https://wa.me/355")), str(wa))
    pg.select_option("#jobCity", "")
    pg.select_option("#jobSort", "reviews")
    pg.wait_for_timeout(300)
    rev_counts = pg.evaluate("""() => [...document.querySelectorAll('.job-card')].map(c => {
        const a = c.querySelector('h3 a'); const id = new URL(a.href).searchParams.get('id');
        return TRY.liveRating(id).n; })""")
    ok("pune: sort by reviews desc", rev_counts == sorted(rev_counts, reverse=True), str(rev_counts))

    # ---------- sherbime ----------
    pg.goto(BASE + "sherbime.html", wait_until="networkidle")
    hrefs = pg.locator(".pkg-card a.btn-wa2").evaluate_all("els => els.map(e => e.href)")
    ok("sherbime: 2 WA buttons to wa.link/om98rz", len(hrefs) == 2 and all(h == "https://wa.link/om98rz" for h in hrefs), str(hrefs))
    ok("sherbime: price 10 € shown", "10 €" in pg.locator(".pkg-card").first.inner_text())

    # ---------- hero tabs ----------
    for label, href, want in [("all", "restorante.html", 21),
                              ("tirane", "restorante.html?qytet=Tiran%C3%AB", 6),
                              ("korce", "restorante.html?qytet=Kor%C3%A7%C3%AB", 5),
                              ("durres", "restorante.html?qytet=Durr%C3%ABs", 5),
                              ("shkoder", "restorante.html?qytet=Shkod%C3%ABr", 5),
                              ("deti", "restorante.html?cat=deti", 6),
                              ("trad", "restorante.html?cat=tradicionale", 10)]:
        pg.goto(BASE + href, wait_until="networkidle")
        pg.wait_for_timeout(250)
        ok(f"tab {label} -> {want} cards", pg.locator(".rcard").count() == want, str(pg.locator(".rcard").count()))
    chip = pg.locator(".slotctx").inner_text() if pg.locator(".slotctx").count() else ""
    ok("tab trad: context chip visible", "tradicionale" in chip.lower(), chip)
    pg.click("#btnClear")
    pg.wait_for_timeout(300)
    ok("clear filters -> 21 cards", pg.locator(".rcard").count() == 21, str(pg.locator(".rcard").count()))
    ok("clear filters -> chip gone", pg.locator(".slotctx").count() == 0)

    # ---------- how toggle ----------
    pg.goto(BASE + "index.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    st = pg.evaluate("""() => ({ biz: document.querySelector('#howBiz').hidden,
                                 guest: document.querySelector('#howGuest').hidden })""")
    ok("how toggle: default biz visible", st == {"biz": False, "guest": True}, str(st))
    pg.click(".htog[data-how='guest']")
    pg.wait_for_timeout(300)
    st = pg.evaluate("""() => ({ biz: document.querySelector('#howBiz').hidden,
                                 guest: document.querySelector('#howGuest').hidden,
                                 guestVisible: document.querySelector('#howGuest').offsetParent !== null })""")
    ok("how toggle: guest panel shows", st["biz"] is True and st["guest"] is False and st["guestVisible"], str(st))
    pg.click(".htog[data-how='biz']")
    pg.wait_for_timeout(200)

    # ---------- hero parallax double-writer check ----------
    pg.evaluate("window.scrollTo(0, 400)")
    samples = pg.evaluate("""() => new Promise(res => {
      const el = document.querySelector('.hero-inner');
      const vals = new Set(); let n = 0;
      const iv = setInterval(() => { vals.add(el.style.transform); if(++n >= 30){ clearInterval(iv); res([...vals]); } }, 16);
    })""")
    ok("hero parallax: single stable transform", len(samples) <= 2, str(samples))

    # ---------- assistant ----------
    pg.goto(BASE + "index.html", wait_until="networkidle")
    pg.wait_for_timeout(300)
    ok("assistant: button exists", pg.locator(".asst-btn").count() == 1)
    pg.click(".asst-btn")
    pg.wait_for_timeout(400)
    ok("assistant: panel opens + greeting", pg.locator(".asst-panel.open").count() == 1 and pg.locator(".asst-msg.bot").count() >= 1)
    pg.fill("#asstInput", "Cili është restoranti më i mirë në Korçë?")
    pg.press("#asstInput", "Enter")
    pg.wait_for_timeout(700)
    cards = pg.evaluate("""() => [...document.querySelectorAll('.asst-card')].map(a => {
        const id = new URL(a.href).searchParams.get('id'); const r = TRY.restById(id);
        return { id, city: r.qytet, rating: TRY.liveRating(id).r }; })""")
    ok("assistant: best in Korçë -> only Korçë cards", len(cards) >= 1 and all(c["city"] == "Korçë" for c in cards), str(cards))
    ok("assistant: cards sorted by rating desc", [c["rating"] for c in cards] == sorted([c["rating"] for c in cards], reverse=True), str(cards))
    pg.fill("#asstInput", "Cilat janë të hapura tani?")
    pg.press("#asstInput", "Enter")
    pg.wait_for_timeout(700)
    openchk = pg.evaluate("""() => {
      const lists = [...document.querySelectorAll('.asst-msg.bot')];
      const last = lists[lists.length-1];
      return [...last.querySelectorAll('.asst-card')].map(a => {
        const id = new URL(a.href).searchParams.get('id');
        return { id, open: TRY.openNow(TRY.restById(id)) }; }); }""")
    ok("assistant: 'open now' cards are really open", all(c["open"] for c in openchk), str(openchk))
    first_card = pg.locator(".asst-card").first
    href = first_card.get_attribute("href")
    ok("assistant: card href -> restorant.html?id=", bool(href and href.startswith("restorant.html?id=")), str(href))
    pg.click(".asst-x")
    pg.wait_for_timeout(200)
    ok("assistant: closes with X", pg.locator(".asst-panel.open").count() == 0)
    # mobile: panel within viewport, button not covering booking CTA
    ctxm = b.new_context(viewport={"width": 390, "height": 844})
    pm = ctxm.new_page()
    pm.goto(BASE + "index.html", wait_until="networkidle")
    pm.wait_for_timeout(300)
    pm.click(".asst-btn")
    pm.wait_for_timeout(300)
    box = pm.locator(".asst-panel").bounding_box()
    ok("assistant mobile: panel inside viewport", box and box["x"] >= 0 and box["x"] + box["width"] <= 391, str(box))
    ctxm.close()
    ctx.close()

print(f"\n==== PART2: {len(PASS)} PASS, {len(FAIL)} FAIL ====")
for f in FAIL: print("FAILED:", f)
