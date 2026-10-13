#!/usr/bin/env python3
"""Validimi GAP — vizitat në renditje + kërkim/renditje te Punë + linku i hartës.
Boshllëqet e fundit nga krahasimi me platformën tjetër. Audit-grade."""
import sys, json, urllib.parse
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8933"
fails, passes = [], []
def check(name, cond, extra=""):
    (passes if cond else fails).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))

def new_page(b, w=1440, h=900, lang=None):
    ctx = b.new_context(viewport={"width": w, "height": h})
    if lang:
        ctx.add_init_script(f"localStorage.setItem('tryeza.lang.v1','{lang}')")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errs.append(f"console-{m.type}: {m.text}") if m.type == "error" else None)
    pg.on("requestfailed", lambda r: errs.append(f"reqfail: {r.url}"))
    pg.on("response", lambda r: errs.append(f"http{r.status}: {r.url}") if r.status >= 400 else None)
    return ctx, pg, errs

def settle(pg):
    try:
        pg.wait_for_selector("#tryLoader", state="detached", timeout=9000)
    except Exception:
        pass
    pg.wait_for_timeout(350)

def overflow(pg):
    return pg.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")

REST = "tirana-mullixhiu"

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])

    # ============ 1. Sweep: 3 faqet × 2 viewports × 2 gjuhë — gabime & overflow ============
    for lang in ("sq", "en"):
        for w in (1440, 390):
            for path in (f"restorant.html?id={REST}", "renditja.html", "pune.html"):
                ctx, pg, errs = new_page(b, w=w, lang=lang)
                pg.goto(BASE + "/" + path)
                settle(pg)
                check(f"sweep {path} {w}px {lang}: 0 gabime", not errs, "; ".join(errs[:3]))
                ov = overflow(pg)
                check(f"sweep {path} {w}px {lang}: 0 overflow", ov <= 1, f"overflow={ov}")
                ctx.close()

    # ============ 2. Vizitat: +1 / refresh guard / sesion i ri +1 / pikët ============
    ctx, pg, errs = new_page(b)
    pg.goto(BASE + f"/restorant.html?id={REST}")
    settle(pg)
    v1 = pg.evaluate(f"() => TRY.visitCount('{REST}')")
    check("vizita: hapja e parë +1", v1 == 1, f"visitCount={v1}")
    p1 = pg.evaluate(f"() => TRY.pointsFor('{REST}')")
    pg.reload(); settle(pg)
    v2 = pg.evaluate(f"() => TRY.visitCount('{REST}')")
    p2 = pg.evaluate(f"() => TRY.pointsFor('{REST}')")
    check("vizita: refresh NUK e rrit (session guard)", v2 == 1, f"visitCount={v2}")
    check("vizita: pikët të pandryshuara pas refresh", p2 == p1, f"{p1}->{p2}")
    pg.evaluate("() => sessionStorage.clear()")
    pg.reload(); settle(pg)
    v3 = pg.evaluate(f"() => TRY.visitCount('{REST}')")
    p3 = pg.evaluate(f"() => TRY.pointsFor('{REST}')")
    check("vizita: sesion i ri +1 tjetër", v3 == 2, f"visitCount={v3}")
    check("vizita: pikët +1 me vizitën e re", p3 == p1 + 1, f"{p1}->{p3}")
    ls = pg.evaluate("() => JSON.parse(localStorage.getItem('tryeza.visits.v1') || '{}')")
    check("vizita: ruhet në tryeza.visits.v1", ls.get(REST) == 2, json.dumps(ls))
    check("vizita: 0 gabime gjatë rrjedhës", not errs, "; ".join(errs[:3]))

    # renditja tregon vizitat/skanimet e mbjella
    pg.evaluate(f"""() => {{
        const v = JSON.parse(localStorage.getItem('tryeza.visits.v1') || '{{}}');
        v['{REST}'] = 7; localStorage.setItem('tryeza.visits.v1', JSON.stringify(v));
        localStorage.setItem('tryeza.scans.v1', JSON.stringify({{'{REST}': 3}}));
    }}""")
    pg.goto(BASE + "/renditja.html"); settle(pg)
    rows = pg.evaluate(f"""() => [...document.querySelectorAll('#lbBody tr')].map(tr => {{
        const a = tr.querySelector('td.rn a');
        const id = new URL(a.href).searchParams.get('id');
        const tds = [...tr.querySelectorAll('td')].map(td => td.textContent.trim());
        return {{ id, tds }};
    }})""")
    check("renditja: 21 rreshta", len(rows) == 21, f"rows={len(rows)}")
    row = next((r for r in rows if r["id"] == REST), None)
    check("renditja: kolona Vizita = 7", row and row["tds"][4] == "7", json.dumps(row))
    check("renditja: kolona Skanime QR = 3", row and row["tds"][5] == "3", json.dumps(row))
    exp_pts = pg.evaluate(f"() => TRY.pointsFor('{REST}')")
    check("renditja: pikët = formula", row and row["tds"][7] == str(exp_pts), f"td={row and row['tds'][7]} exp={exp_pts}")
    heads = [h.lower() for h in pg.locator(".lb-table thead th").all_inner_texts()]
    check("renditja: header-at SQ (Vizita/Skanime QR)", any("vizita" in x for x in heads) and any("skanime qr" in x for x in heads), "|".join(heads))
    ctx.close()

    # renditja EN headers
    ctx, pg, errs = new_page(b, lang="en")
    pg.goto(BASE + "/renditja.html"); settle(pg)
    heads = [h.lower() for h in pg.locator(".lb-table thead th").all_inner_texts()]
    check("renditja EN: header-at (Visits/QR scans)", any("visits" in x for x in heads) and any("qr scans" in x for x in heads), "|".join(heads))
    ctx.close()

    # ============ 3. Linku i hartës te restorant.html ============
    ctx, pg, errs = new_page(b)
    pg.goto(BASE + f"/restorant.html?id={REST}")
    settle(pg)
    pg.locator('#tabs .tab[data-pane="det"]').click()
    pg.wait_for_timeout(200)
    maplink = pg.locator('#pane-det a[href*="google.com/maps"]')
    check("harta: linku ekziston te Detaje", maplink.count() == 1)
    if maplink.count():
        href = maplink.get_attribute("href")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("query", [""])[0]
        emer = pg.evaluate(f"() => TRY.restById('{REST}').emer")
        check("harta: query përmban emrin e restorantit", emer in q, q)
        check("harta: target _blank", maplink.get_attribute("target") == "_blank")
        check("harta: teksti i linkut", "hartë" in maplink.inner_text().lower(), maplink.inner_text())
    ctx.close()

    # ============ 4. Punë: kërkim + renditje + qytet + WA ============
    ctx, pg, errs = new_page(b)
    pg.goto(BASE + "/pune.html"); settle(pg)
    n0 = pg.locator(".job-card").count()
    check("punë: 21 karta në fillim", n0 == 21, f"n={n0}")
    check("punë: fusha e kërkimit + renditja ekzistojnë",
          pg.locator("#jobQ").count() == 1 and pg.locator("#jobSort").count() == 1)

    def dom_ids():
        return pg.evaluate("""() => [...document.querySelectorAll('.job-card a.cover')].map(a =>
            new URL(a.href).searchParams.get('id'))""")

    # kërkim sipas emrit (pa ndjeshmëri ndaj shkronjave/diakritikës)
    target = pg.evaluate("""() => { const r = RESTORANTET[5]; return {emer: r.emer, lagje: r.lagje, qytet: r.qytet}; }""")
    frag = target["emer"][:4].lower()
    exp_n = pg.evaluate(f"""() => {{
        const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        const q = norm('{frag}');
        return RESTORANTET.filter(r => norm(r.emer).includes(q) || norm(r.lagje).includes(q)).length;
    }}""")
    pg.fill("#jobQ", frag)
    pg.wait_for_timeout(250)
    got = pg.locator(".job-card").count()
    check(f"punë: kërkimi '{frag}' filtron saktë", got == exp_n and 0 < got < 21, f"got={got} exp={exp_n}")

    # kërkim sipas lagjes
    lag = target["lagje"].split(" ")[0]
    exp_l = pg.evaluate(f"""() => {{
        const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        const q = norm('{lag}');
        return RESTORANTET.filter(r => norm(r.emer).includes(q) || norm(r.lagje).includes(q)).length;
    }}""")
    pg.fill("#jobQ", lag)
    pg.wait_for_timeout(250)
    got = pg.locator(".job-card").count()
    check(f"punë: kërkimi sipas lagjes '{lag}'", got == exp_l and got >= 1, f"got={got} exp={exp_l}")

    # kombinim: qytet + kërkim
    pg.fill("#jobQ", frag)
    pg.select_option("#jobCity", target["qytet"])
    pg.wait_for_timeout(250)
    exp_c = pg.evaluate(f"""() => {{
        const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        const q = norm('{frag}');
        return RESTORANTET.filter(r => r.qytet === '{target["qytet"]}' &&
            (norm(r.emer).includes(q) || norm(r.lagje).includes(q))).length;
    }}""")
    got = pg.locator(".job-card").count()
    check("punë: qytet + kërkim të kombinuara", got == exp_c, f"got={got} exp={exp_c}")

    # pastro filtrat për renditjet
    pg.fill("#jobQ", "")
    pg.select_option("#jobCity", "")
    pg.wait_for_timeout(250)

    # renditja Emri A–Z
    pg.select_option("#jobSort", "name")
    pg.wait_for_timeout(250)
    names_dom = pg.locator(".job-card h3 a").all_inner_texts()
    names_exp = pg.evaluate("() => RESTORANTET.map(r => r.emer).sort((a,b) => a.localeCompare(b, 'sq'))")
    check("punë: renditja Emri A–Z e saktë", names_dom == names_exp,
          f"dom[:3]={names_dom[:3]} exp[:3]={names_exp[:3]}")

    # renditja Vlerësimi më i lartë
    pg.select_option("#jobSort", "rating")
    pg.wait_for_timeout(250)
    ids = dom_ids()
    seq = pg.evaluate(f"""() => {{
        const ids = [...document.querySelectorAll('.job-card a.cover')].map(a => new URL(a.href).searchParams.get('id'));
        return ids.map(id => {{ const l = TRY.liveRating(id); return {{ r: l.r || 0, n: l.n }}; }});
    }}""")
    check("punë: renditja sipas vlerësimit zbritëse",
          all(seq[i]["r"] > seq[i+1]["r"] or (seq[i]["r"] == seq[i+1]["r"] and seq[i]["n"] >= seq[i+1]["n"])
              for i in range(len(seq)-1)), json.dumps(seq[:4]))

    # renditja Më shumë vlerësime
    pg.select_option("#jobSort", "reviews")
    pg.wait_for_timeout(250)
    seq = pg.evaluate("""() => {
        const ids = [...document.querySelectorAll('.job-card a.cover')].map(a => new URL(a.href).searchParams.get('id'));
        return ids.map(id => { const l = TRY.liveRating(id); return { r: l.r || 0, n: l.n }; });
    }""")
    check("punë: renditja sipas nr. vlerësimeve zbritëse",
          all(seq[i]["n"] > seq[i+1]["n"] or (seq[i]["n"] == seq[i+1]["n"] and seq[i]["r"] >= seq[i+1]["r"])
              for i in range(len(seq)-1)), json.dumps(seq[:4]))

    # WA apply në numrin real
    wa = pg.locator(".job-card .btn-wa2").first
    href = wa.get_attribute("href")
    first_id = pg.evaluate("() => new URL(document.querySelector('.job-card a.cover').href).searchParams.get('id')")
    digits = pg.evaluate(f"() => (TRY.restById('{first_id}').telefon || '').replace(/\\D/g, '')")
    check("punë: butoni WA te numri real i restorantit",
          href.startswith(f"https://wa.me/{digits}?text="), href[:60])
    check("punë: mesazhi WA i paraplotësuar", "TRYEZA" in urllib.parse.unquote(href), href[:80])

    # pa rezultate
    pg.fill("#jobQ", "zzzzqqq")
    pg.wait_for_timeout(250)
    check("punë: kërkim pa rezultate → mesazh bosh",
          pg.locator(".job-card").count() == 0 and "Asnjë restorant" in pg.locator("#jobGrid").inner_text())
    check("punë: 0 gabime gjatë rrjedhës", not errs, "; ".join(errs[:3]))
    ctx.close()

    # ============ 5. Regresion i shpejtë: booking + menu-builder ============
    ctx, pg, errs = new_page(b)
    pg.goto(BASE + f"/restorant.html?id={REST}")
    settle(pg)
    pg.locator("#bkTimeSel").select_option(index=1)
    pg.wait_for_timeout(300)
    # zgjidh orën e parë të lirë nga slot-et nëse select-i s'mjafton
    free_slot = pg.locator("#bkSlots button.slot:not(:disabled)").first
    if free_slot.count():
        free_slot.click(); pg.wait_for_timeout(300)
    tbl = pg.locator("#bkFloor g.tbl").first
    check("regresion booking: ka tavolinë të lirë", tbl.count() == 1)
    if tbl.count():
        tbl.click(); pg.wait_for_timeout(200)
    pg.fill("#gEmer", "Testues Gap")
    pg.fill("#gTel", "0691234567")
    pg.check("#gKushtet")
    pg.locator("#bkConfirm").click()
    pg.wait_for_timeout(600)
    code = pg.locator(".code-box .code")
    check("regresion booking: konfirmim me kod TRZ",
          code.count() == 1 and code.inner_text().startswith("TRZ-"),
          code.inner_text() if code.count() else "no code box")
    saved = pg.evaluate("() => JSON.parse(localStorage.getItem('tryeza.bookings.v1') || '[]').length")
    check("regresion booking: rezervimi u ruajt", saved >= 1, f"bookings={saved}")
    ctx.close()

    ctx, pg, errs = new_page(b)
    pg.goto(BASE + f"/menu-builder.html?id={REST}")
    settle(pg)
    add = pg.locator(".mb-add").first
    check("regresion menu-builder: ka butona shtimi", add.count() == 1)
    if add.count():
        add.click(); pg.wait_for_timeout(500)
        tot = pg.locator("#mbBarTotal").inner_text() if pg.locator("#mbBarTotal").count() else ""
        check("regresion menu-builder: totali përditësohet pas shtimit", bool(tot.strip()), tot)
    check("regresion menu-builder: 0 gabime", not errs, "; ".join(errs[:3]))
    ctx.close()

    b.close()

print(f"\n===== GAP TEST: {len(passes)} PASS / {len(fails)} FAIL =====")
if fails:
    print("FAILED:", *fails, sep="\n  - ")
    sys.exit(1)
