<!-- Created by Erion Nezha — © 2026 All rights reserved -->
# TRYEZA — Rezervo tavolinën tënde në sekonda

Platformë shqiptare për zbulimin e restoranteve dhe **rezervimin e tavolinave online me konfirmim të menjëhershëm** — pa telefonata, falas për mysafirët.

**Live demo:** https://erionnezha.github.io/tryeza/

---

## 🇦🇱 Shqip

TRYEZA (tryezë = tavolinë në gegërisht) është një aplikacion web statik, ultra-premium, i ndërtuar me HTML/CSS/JS vanilla — pa build step, pa varësi serveri.

### Çfarë bën
- **Kërkim i zgjuar** — qytet (Tiranë, Korçë, Durrës, Shkodër), datë, orë, numër personash → badge disponueshmërie reale për çdo restorant
- **21 restorante REALE** (6 Tiranë, 5 Korçë, 5 Durrës, 5 Shkodër) me **foto të vërteta** (42 foto lokale, me kredite autor/burim/licencë në faqen "Kreditë e fotove"), numra telefoni realë të verifikuar, orare, zona (sallë/tarracë), plan tavolinash
- **Rezervim me 6 hapa** — persona → datë → orë (slot-e të lira të llogaritura) → zonë → tavolinë (planimetri SVG interaktive) → të dhënat e mysafirit → konfirmim me kod `TRZ-XXXXXX` + shkarkim ftese `.ics`
- **Kontakt real me restorantin** — numri i telefonit i dukshëm në faqen e restorantit DHE në ekranin e konfirmimit ("Për konfirmim telefono: ...") + buton **"Dërgo me WhatsApp"** që hap `wa.me` me tekst të plotësuar automatikisht (emër, datë, orë, persona, zonë/tavolinë, kod TRZ, shënime) — rezervimi i shkon restorantit direkt, pa backend
- **Rezervimet e mia** — kërkim me kod/telefon/emër, modifikim date/ore, anulim, ftesë kalendari
- **Vlerësime** — shkruaj vlerësim, rating-u përditësohet live; **të preferuarat** (♥) ruhen lokalisht
- **Sugjero restorant** — me votim komunitar
- **Paneli i restorantit (demo)** — statistika, grafik rezervimesh/orë (canvas), no-show, gjenerim të dhënash demo, eksport CSV
- **Blog + FAQ** — përmbajtje origjinale shqip
- **Faqja "Kodi burimor"** — kodi i plotë i shfaqur me syntax highlighting të brendshëm

### Teknologjitë
HTML5 · CSS3 (design system dark premium + gold `#D4AF37`) · JavaScript vanilla · `localStorage` (namespace `tryeza.*`) · foto reale lokale (zero hotlink) + art gjenerativ SVG si fallback · i testuar me Playwright (rruga reale: kërkim → rezervim → WhatsApp → modifikim → anulim, 0 gabime).

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
- **21 REAL restaurants** (6 Tirana, 5 Korçë, 5 Durrës, 5 Shkodër) with **real photos** (42 local photos, credited author/source/license on the "Photo credits" page), verified real phone numbers, hours, zones (hall/terrace), table floor plans
- **6-step booking** — party → date → time (computed free slots) → zone → table (interactive SVG floor plan) → guest details → confirmation with `TRZ-XXXXXX` code + downloadable `.ics` invite
- **Real restaurant contact** — phone number visible on the restaurant page AND on the confirmation screen ("Për konfirmim telefono: ...") + **"Send via WhatsApp"** button opening `wa.me` with prefilled text (name, date, time, guests, zone/table, TRZ code, notes) — the booking reaches the restaurant directly, no backend needed
- **My bookings** — lookup by code/phone/name, reschedule, cancel, calendar invite
- **Reviews** — write a review, rating updates live; **favorites** (♥) stored locally
- **Suggest a restaurant** — with community voting
- **Restaurant dashboard (demo)** — stats, bookings/hour chart (canvas), no-show marking, demo data generator, CSV export
- **Blog + FAQ** — original Albanian content
- **"Source code" page** — full source displayed with a built-in syntax highlighter

### Tech
HTML5 · CSS3 (dark premium + gold `#D4AF37` design system) · vanilla JavaScript · `localStorage` (`tryeza.*` namespace) · real local photos (zero hotlinking) + generative SVG art as fallback · tested with Playwright (real path: search → booking → WhatsApp → reschedule → cancel, 0 errors).

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
├── kredite.html        # Kreditë e fotove (autor/burim/licencë)
├── img/<id>/           # Fotot reale të restoranteve (lokale, 42)
├── css/style.css       # Design system
├── js/data.js          # 21 restorante REALE me foto e telefona të verifikuar
├── js/app.js           # Motori: disponueshmëri, rezervime, vlerësime, art SVG
└── tests/validate.py   # Testet Playwright
```

## Licenca / License
MIT — shih `LICENSE`. Krijuar nga **Erion Nezha** — © 2026 All rights reserved.
