"""Validate: real dish photos + pizza-builder interactions in menu builder."""
import sys, time, subprocess, os
from playwright.sync_api import sync_playwright

ROOT = os.path.expanduser("~/workspace/tryeza")
PORT = 8940
fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

srv = subprocess.Popen(["python3","-m","http.server",str(PORT),"--directory",ROOT],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox","--disable-gpu"])
        errors, bad404 = [], []
        def run(vp, label):
            pg = b.new_page(viewport=vp)
            pg.on("pageerror", lambda e: errors.append(f"{label}: {e}"))
            pg.on("console", lambda m: errors.append(f"{label} console.{m.type}: {m.text}") if m.type=="error" else None)
            pg.on("response", lambda r: bad404.append(f"{label}: {r.status} {r.url}") if r.status>=400 else None)
            return pg

        # ---------- desktop: photos render ----------
        pg = run({"width":1440,"height":900}, "desk")
        pg.goto(f"http://localhost:{PORT}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
        pg.wait_for_timeout(2200)  # loader
        thumbs = pg.locator("img.mb-thumb").count()
        check("dish cards show real photos", thumbs >= 5, f"thumbs={thumbs}")
        broken = pg.evaluate("""[...document.querySelectorAll('img')].filter(i=>!i.complete||i.naturalWidth===0).length""")
        check("no broken images", broken == 0, f"broken={broken}")
        # hint initial
        h0 = pg.locator("#mbHint").inner_text()
        check("hint0 contextual", "Tërhiq" in h0, h0)

        # ---------- click-add flies PHOTO ----------
        pg.locator(".mb-dish .mb-add").first.click()
        pg.wait_for_timeout(300)
        fly_img = pg.evaluate("!!document.querySelector('.mb-fly img')")
        check("fly animation flies the photo", fly_img)
        pg.wait_for_timeout(900)
        on_table = pg.evaluate("document.querySelectorAll('#mbTableDishes image').length")
        check("dish lands on table as photo", on_table == 1, f"images={on_table}")
        h1 = pg.locator("#mbHint").inner_text()
        check("hint1 after first add", "ngadalë" in h1, h1)
        cta_txt = pg.locator("#mbCta").inner_text()
        check("CTA is 'Dërgo në kuzhinë'", "kuzhinë" in cta_txt, cta_txt)

        # ---------- drag & drop ----------
        card = pg.locator(".mb-dish").nth(1)
        tbox = pg.locator("#mbTableWrap").bounding_box()
        cbox = card.bounding_box()
        pg.mouse.move(cbox["x"]+cbox["width"]/2, cbox["y"]+cbox["height"]/2)
        pg.mouse.down()
        for i in range(1, 11):
            pg.mouse.move(cbox["x"]+cbox["width"]/2 + (tbox["x"]+tbox["width"]/2-cbox["x"]-cbox["width"]/2)*i/10,
                          cbox["y"]+cbox["height"]/2 + (tbox["y"]+tbox["height"]/2-cbox["y"]-cbox["height"]/2)*i/10)
            pg.wait_for_timeout(25)
        pg.mouse.up()
        pg.wait_for_timeout(1000)
        n2 = pg.evaluate("document.querySelectorAll('#mbTableDishes .mb-tdish').length")
        check("drag-and-drop adds dish", n2 == 2, f"n={n2}")
        h2 = pg.locator("#mbHint").inner_text()
        check("hint2 after 2 dishes", "Mbaj shtypur" in h2, h2)

        # ---------- hold-to-remove ----------
        td = pg.locator("#mbTableDishes .mb-tdish").first
        tdb = td.bounding_box()
        pg.mouse.move(tdb["x"]+tdb["width"]/2, tdb["y"]+tdb["height"]/2)
        pg.mouse.down(); pg.wait_for_timeout(800); pg.mouse.up()
        pg.wait_for_timeout(400)
        n3 = pg.evaluate("document.querySelectorAll('#mbTableDishes .mb-tdish').length")
        check("hold-to-remove removes dish", n3 == 1, f"n={n3}")

        # ---------- firing -> order screen ----------
        pg.locator("#mbCta").click()
        pg.wait_for_timeout(600)
        firing = pg.evaluate("!!document.querySelector('.mb-fire-ov')")
        check("firing overlay shows", firing)
        pg.wait_for_timeout(2600)
        ov_open = pg.evaluate("document.querySelector('#mbOrderOv').classList.contains('open')")
        check("order screen opens after firing", ov_open)
        cooked = pg.evaluate("document.querySelector('#mbTableWrap').classList.contains('cooked')")
        check("dishes get 'cooked' glow", cooked)
        # steppers
        tot0 = pg.locator("#mbOrderTotal").inner_text()
        pg.locator("#mbOrderLines .qstep button[data-act='inc']").first.click()
        pg.wait_for_timeout(300)
        tot1 = pg.locator("#mbOrderTotal").inner_text()
        check("stepper + changes total", tot0 != tot1, f"{tot0} -> {tot1}")
        pg.locator("#mbKitchen").fill("pa gluten")
        pg.screenshot(path=os.path.expanduser("~/workspace/tryeza/screenshots/dish-01-order.png"))
        # add to booking
        pg.locator("#mbOrderGo").click()
        pg.wait_for_timeout(1200)
        check("goes to restaurant page", "restorant.html" in pg.url, pg.url)
        summ = pg.locator("body").inner_text()
        check("menu in booking summary", "Menuja" in summ)
        pg.screenshot(path=os.path.expanduser("~/workspace/tryeza/screenshots/dish-02-summary.png"))

        # ---------- restaurant menu tab photos ----------
        pg.goto(f"http://localhost:{PORT}/restorant.html?id=durresi-meison-bistro", wait_until="networkidle")
        pg.wait_for_timeout(1800)
        pg.locator('.tab[data-pane="menu"]').click()
        pg.wait_for_timeout(400)
        mth = pg.locator("img.menu-thumb").count()
        check("restaurant menu tab shows photos", mth >= 8, f"menu-thumbs={mth}")

        # ---------- credits ----------
        pg.goto(f"http://localhost:{PORT}/kredite.html", wait_until="networkidle")
        pg.wait_for_timeout(1800)
        dc = pg.evaluate("document.querySelectorAll('#dishKreditList .credit-item').length")
        check("dish credits listed (33)", dc == 33, f"dc={dc}")

        # ---------- EN ----------
        pg.goto(f"http://localhost:{PORT}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
        pg.wait_for_timeout(2000)
        pg.evaluate("I18N.setLang('en')")
        pg.reload(wait_until="networkidle"); pg.wait_for_timeout(2000)
        he = pg.locator("#mbHint").inner_text()
        check("EN hint translated", "dish" in he.lower() and "pjatë" not in he, he)

        # ---------- mobile ----------
        m = run({"width":390,"height":844}, "mob")
        m.goto(f"http://localhost:{PORT}/menu-builder.html?id=tirana-era-blloku", wait_until="networkidle")
        m.wait_for_timeout(2200)
        mth2 = m.locator("img.mb-thumb").count()
        check("mobile: photos render", mth2 >= 5, f"thumbs={mth2}")
        m.locator(".mb-dish .mb-add").first.click()
        m.wait_for_timeout(1200)
        ovf = m.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        check("mobile: no horizontal overflow", not ovf)
        m.screenshot(path=os.path.expanduser("~/workspace/tryeza/screenshots/dish-03-mobile.png"))
        pg.screenshot(path=os.path.expanduser("~/workspace/tryeza/screenshots/dish-04-builder.png"))
        b.close()

        real404 = [x for x in bad404 if "favicon" not in x]
        check("zero 404s", len(real404) == 0, "; ".join(real404[:3]))
        check("zero console/page errors", len(errors) == 0, "; ".join(errors[:3]))
finally:
    srv.terminate()

print("\n==== %d FAILURES ====" % len(fails))
sys.exit(1 if fails else 0)
