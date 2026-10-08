#!/usr/bin/env python3
"""TRYEZA QA kirurgjikal responsive: overflow + console errors + screenshots."""
import sys, json, subprocess, time, os
from playwright.sync_api import sync_playwright

ROOT = "/home/hatch/workspace/tryeza"
SHOT = os.path.join(ROOT, "screenshots")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8932
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else "before"
ONLY = sys.argv[3] if len(sys.argv) > 3 else None  # optional substring filter

BASE = f"http://127.0.0.1:{PORT}"
VPS = {"mob": (390, 844), "tab": (768, 1024), "desk": (1440, 900)}
PAGES = [
    ("index", "index.html"),
    ("restorante", "restorante.html"),
    ("restorant", "restorant.html?id=tirana-mullixhiu"),
    ("rezervimet", "rezervimet.html"),
    ("blog", "blog.html"),
    ("faq", "faq.html"),
    ("kodi", "kodi.html"),
    ("kredite", "kredite.html"),
    ("dashboard", "dashboard.html"),
    ("sugjero", "sugjero.html"),
]
TABS = ["perm", "pjata", "menu", "foto", "vler", "det"]
LANGS = ["sq", "en"]

report = {"overflow": [], "console": [], "errors": []}

def wait_loaded(page):
    try:
        page.wait_for_selector("#tryLoader.done", timeout=9000)
    except Exception:
        pass
    page.wait_for_timeout(600)

def check_overflow(page, name):
    ov = page.evaluate("""() => {
        const bad = [];
        const docW = document.documentElement.scrollWidth, winW = window.innerWidth;
        if (docW > winW + 1) bad.push('DOC:'+docW+'>'+winW);
        document.querySelectorAll('body *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && (r.right > winW + 2 || r.left < -2)) {
                const id = el.id ? '#'+el.id : '';
                const cls = el.className && el.className.baseVal === undefined
                    ? String(el.className).split(' ').slice(0,2).join('.') : '';
                bad.push(el.tagName + id + (cls?'.'+cls:'') + '@'+Math.round(r.left)+':'+Math.round(r.right));
                if (bad.length > 12) return;
            }
        });
        return bad.slice(0, 12);
    }""")
    if ov:
        report["overflow"].append({"page": name, "issues": ov})

def tap_targets(page, name, vp):
    if vp != "mob":
        return
    small = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('a,button,input,select,textarea,[role=button]').forEach(el => {
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            if (r.width === 0 || cs.display === 'none' || cs.visibility === 'hidden') return;
            if (r.height < 30 || r.width < 30) out.push(el.tagName + (el.id?'#'+el.id:'') + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
        });
        return out.slice(0, 15);
    }""")
    if small:
        report["overflow"].append({"page": name + " TAP<30px", "issues": small})

def run():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        for vpname, (w, h) in VPS.items():
            for lang in LANGS:
                for pname, ppath in PAGES:
                    name = f"{pname}-{vpname}-{lang}"
                    if ONLY and ONLY not in name:
                        continue
                    ctx = b.new_context(viewport={"width": w, "height": h})
                    ctx.add_init_script(f"try{{localStorage.setItem('tryeza.lang.v1','{lang}')}}catch(e){{}}")
                    page = ctx.new_page()
                    errs = []
                    page.on("pageerror", lambda e: errs.append(str(e)[:160]))
                    page.on("console", lambda m: errs.append("console." + m.type + ": " + m.text[:160]) if m.type == "error" else None)
                    try:
                        page.goto(f"{BASE}/{ppath}", wait_until="domcontentloaded", timeout=20000)
                        wait_loaded(page)
                        check_overflow(page, name)
                        tap_targets(page, name, vpname)
                        if errs:
                            report["console"].append({"page": name, "errs": errs[:6]})
                    except Exception as e:
                        report["errors"].append({"page": name, "err": str(e)[:200]})
                    ctx.close()
        # tab screenshots (SQ, mob+desk)
        for vpname, (w, h) in [("mob", VPS["mob"]), ("desk", VPS["desk"])]:
            for i, tab in enumerate(TABS):
                name = f"restorant-tab-{tab}-{vpname}"
                if ONLY and ONLY not in name:
                    continue
                ctx = b.new_context(viewport={"width": w, "height": h})
                ctx.add_init_script("try{localStorage.setItem('tryeza.lang.v1','sq')}catch(e){}")
                page = ctx.new_page()
                try:
                    page.goto(f"{BASE}/restorant.html?id=tirana-mullixhiu", wait_until="domcontentloaded", timeout=20000)
                    wait_loaded(page)
                    page.click(f'.tab[data-pane="{tab}"]')
                    page.wait_for_timeout(500)
                    page.screenshot(path=f"{SHOT}/fix-{name}-{SUFFIX}.png")
                    check_overflow(page, name)
                except Exception as e:
                    report["errors"].append({"page": name, "err": str(e)[:200]})
                ctx.close()
        # key page screenshots (SQ, all vps)
        for vpname, (w, h) in VPS.items():
            for pname, ppath in [("index", "index.html"), ("restorante", "restorante.html"),
                                 ("restorant", "restorant.html?id=tirana-mullixhiu"),
                                 ("rezervimet", "rezervimet.html")]:
                name = f"{pname}-{vpname}"
                if ONLY and ONLY not in name:
                    continue
                ctx = b.new_context(viewport={"width": w, "height": h})
                ctx.add_init_script("try{localStorage.setItem('tryeza.lang.v1','sq')}catch(e){}")
                page = ctx.new_page()
                try:
                    page.goto(f"{BASE}/{ppath}", wait_until="domcontentloaded", timeout=20000)
                    wait_loaded(page)
                    page.screenshot(path=f"{SHOT}/fix-{name}-{SUFFIX}.png", full_page=(pname != "index"))
                except Exception as e:
                    report["errors"].append({"page": name, "err": str(e)[:200]})
                ctx.close()
        b.close()

def book_flow(vpname, lang):
    """Walk booking steps with screenshots; returns True on success."""
    w, h = VPS[vpname]
    from playwright.sync_api import sync_playwright
    ok = True
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        ctx = b.new_context(viewport={"width": w, "height": h})
        ctx.add_init_script(f"try{{localStorage.setItem('tryeza.lang.v1','{lang}')}}catch(e){{}}")
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)[:200]))
        try:
            page.goto(f"{BASE}/restorant.html?id=tirana-mullixhiu", wait_until="domcontentloaded", timeout=20000)
            wait_loaded(page)
            page.evaluate("document.getElementById('rezervo').scrollIntoView({block:'start'})")
            page.wait_for_timeout(700)
            page.screenshot(path=f"{SHOT}/fix-bk-1init-{vpname}-{lang}-{SUFFIX}.png")
            # tomorrow's date
            page.evaluate("""() => {
                const d = new Date(); d.setDate(d.getDate()+1);
                const s = d.toISOString().slice(0,10);
                const el = document.getElementById('bkDate');
                el.value = s; el.dispatchEvent(new Event('change',{bubbles:true}));
            }""")
            page.wait_for_timeout(700)
            btn = page.query_selector("button.slot:not(:disabled)")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
            page.screenshot(path=f"{SHOT}/fix-bk-2slots-{vpname}-{lang}-{SUFFIX}.png")
            tbl = page.query_selector("#bkFloor g.tbl:not(.busy)")
            if tbl:
                tbl.click()
                page.wait_for_timeout(400)
            page.evaluate("document.getElementById('rezervo').scrollIntoView({block:'start'})")
            page.wait_for_timeout(400)
            page.screenshot(path=f"{SHOT}/fix-bk-3table-{vpname}-{lang}-{SUFFIX}.png")
            page.fill("#gEmer", "Test Testi")
            page.fill("#gTel", "0691234567")
            page.check("#gKushtet")
            page.wait_for_timeout(300)
            page.screenshot(path=f"{SHOT}/fix-bk-4guest-{vpname}-{lang}-{SUFFIX}.png", full_page=False)
            page.click("#bkConfirm")
            page.wait_for_timeout(900)
            page.screenshot(path=f"{SHOT}/fix-bk-5confirm-{vpname}-{lang}-{SUFFIX}.png")
            check_overflow(page, f"booking-{vpname}-{lang}")
            if errs:
                report["console"].append({"page": f"booking-{vpname}-{lang}", "errs": errs[:6]})
        except Exception as e:
            report["errors"].append({"page": f"booking-{vpname}-{lang}", "err": str(e)[:200]})
            ok = False
        ctx.close(); b.close()
    return ok

if __name__ == "__main__":
    mode = sys.argv[4] if len(sys.argv) > 4 else "all"
    if mode in ("all", "scan"):
        run()
    if mode in ("all", "book"):
        for vp in ["mob", "desk"]:
            book_flow(vp, "sq")
        book_flow("mob", "en")
    with open(os.path.join(ROOT, "tests", f"qa_report_{SUFFIX}.json"), "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: len(v) for k, v in report.items()}, indent=1))
