<!-- Created by Erion Nezha — © 2026 All rights reserved -->
# TRYEZA — Rezervo tavolinën tënde në sekonda

Platformë shqiptare për zbulimin e restoranteve dhe **rezervimin e tavolinave online me konfirmim të menjëhershëm** — pa telefonata, falas për mysafirët.

**Live demo:** https://erionnezha.github.io/tryeza/

---

## 🇦🇱 Shqip

TRYEZA (tryezë = tavolinë në gegërisht) është një aplikacion web statik, ultra-premium, i ndërtuar me HTML/CSS/JS vanilla — pa build step, pa varësi serveri.

### Çfarë bën
- **Kërkim i zgjuar** — qytet (Tiranë, Korçë, Durrës, Shkodër), datë, orë, numër personash → badge disponueshmërie reale për çdo restorant
- **28 restorante fiktive** me menu, çmime, orare, zona (sallë/tarracë), plan tavolinash dhe vlerësime
- **Rezervim me 6 hapa** — persona → datë → orë (slot-e të lira të llogaritura) → zonë → tavolinë (planimetri SVG interaktive) → të dhënat e mysafirit → konfirmim me kod `TRZ-XXXXXX` + shkarkim ftese `.ics`
- **Rezervimet e mia** — kërkim me kod/telefon/emër, modifikim date/ore, anulim, ftesë kalendari
- **Vlerësime** — shkruaj vlerësim, rating-u përditësohet live; **të preferuarat** (♥) ruhen lokalisht
- **Sugjero restorant** — me votim komunitar
- **Paneli i restorantit (demo)** — statistika, grafik rezervimesh/orë (canvas), no-show, gjenerim të dhënash demo, eksport CSV
- **Blog + FAQ** — përmbajtje origjinale shqip
- **Faqja "Kodi burimor"** — kodi i plotë i shfaqur me syntax highlighting të brendshëm

### Teknologjitë
HTML5 · CSS3 (design system dark premium + gold `#D4AF37`) · JavaScript vanilla · `localStorage` (namespace `tryeza.*`) · art gjenerativ SVG (asnjë imazh ekstern që thyhet) · i testuar me Playwright (39 kontrolle, 0 dështime).

### Si ta ekzekutosh lokalisht
```bash
cd tryeza
python3 -m http.server 8000
# hap http://127.0.0.1:8000
```

### Testet
```bash
python3 tests/validate.py   # rrjedha reale: kërkim → rezervim → modifikim → anulim → vlerësim → favorite
```

---

## 🇬🇧 English

TRYEZA ("tryeza" = table in Gheg Albanian) is an ultra-premium static web app for discovering restaurants and **booking tables online with instant confirmation** — no phone calls, free for guests.

### Features
- **Smart search** — city (Tirana, Korçë, Durrës, Shkodër), date, time, party size → real availability badge per restaurant
- **28 fictional restaurants** with menus, prices, hours, zones (hall/terrace), table floor plans and reviews
- **6-step booking** — party → date → time (computed free slots) → zone → table (interactive SVG floor plan) → guest details → confirmation with `TRZ-XXXXXX` code + downloadable `.ics` invite
- **My bookings** — lookup by code/phone/name, reschedule, cancel, calendar invite
- **Reviews** — write a review, rating updates live; **favorites** (♥) stored locally
- **Suggest a restaurant** — with community voting
- **Restaurant dashboard (demo)** — stats, bookings/hour chart (canvas), no-show marking, demo data generator, CSV export
- **Blog + FAQ** — original Albanian content
- **"Source code" page** — full source displayed with a built-in syntax highlighter

### Tech
HTML5 · CSS3 (dark premium + gold `#D4AF37` design system) · vanilla JavaScript · `localStorage` (`tryeza.*` namespace) · generative SVG art (zero external images) · tested with Playwright (39 checks, 0 failures).

### Run locally
```bash
cd tryeza
python3 -m http.server 8000
# open http://127.0.0.1:8000
```

---

## Struktura / Structure

```
tryeza/
├── index.html          # Kreu — hero + kërkim + karusel + qytete
├── restorante.html     # Lista me filtra, renditje, badge disponueshmërie
├── restorant.html      # Detaji + widget rezervimi (6 hapa)
├── rezervimet.html     # Rezervimet e mia (kërkim/modifiko/anulo)
├── sugjero.html        # Sugjero restorant + votim
├── dashboard.html      # Paneli i restorantit (demo)
├── blog.html           # Blog (6 artikuj origjinalë)
├── faq.html            # Pyetje të shpeshta
├── kodi.html           # Kodi burimor me highlighting
├── css/style.css       # Design system
├── js/data.js          # 28 restorante (të dhëna fiktive)
├── js/app.js           # Motori: disponueshmëri, rezervime, vlerësime, art SVG
└── tests/validate.py   # Testet Playwright
```

## Licenca / License
MIT — shih `LICENSE`. Krijuar nga **Erion Nezha** — © 2026 All rights reserved.
