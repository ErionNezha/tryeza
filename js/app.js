/* Created by Erion Nezha — © 2026 All rights reserved */
/* TRYEZA — shared engine: chrome, availability, bookings, reviews, generative art */
"use strict";
const TRY = (() => {
  const LS = {
    bookings: "tryeza.bookings.v1",
    reviews: "tryeza.reviews.v1",
    favs: "tryeza.favs.v1",
    sugg: "tryeza.suggestions.v1",
    dashRest: "tryeza.dashrest.v1",
  };
  const QYTETET = ["Tiranë", "Korçë", "Durrës", "Shkodër"];
  const DITET = ["E diel","E hënë","E martë","E mërkurë","E enjte","E premte","E shtunë"];
  const MUAJT = ["janar","shkurt","mars","prill","maj","qershor","korrik","gusht","shtator","tetor","nëntor","dhjetor"];
  const SLOTS = ["11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00",
                 "18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30"];

  /* ---------- helpers ---------- */
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const load = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } };
  const save = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const uid = () => Math.random().toString(36).slice(2, 10);
  const hashStr = s => { let h = 2166136261; for (let i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=Math.imul(h,16777619);} return h>>>0; };
  const rng = seed => () => { seed|=0; seed=seed+0x6D2B79F5|0; let t=Math.imul(seed^seed>>>15,1|seed); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; };
  const todayStr = (off=0) => { const d=new Date(); d.setDate(d.getDate()+off); return d.toISOString().slice(0,10); };
  const fmtDate = ds => { const [y,m,d]=ds.split("-").map(Number); const dt=new Date(y,m-1,d); return `${DITET[dt.getDay()]}, ${d} ${MUAJT[m-1]} ${y}`; };
  const cmimTxt = n => "€".repeat(n);
  const genCode = () => "TRZ-" + Array.from({length:6},()=>"ABCDEFGHJKMNPQRSTUVWXYZ23456789"[Math.floor(Math.random()*31)]).join("");

  /* ---------- toast ---------- */
  let toastT;
  function toast(html, ms=3200){
    let el = $("#toast");
    if(!el){ el=document.createElement("div"); el.id="toast"; document.body.appendChild(el); }
    el.innerHTML = html; el.classList.add("show");
    clearTimeout(toastT); toastT=setTimeout(()=>el.classList.remove("show"), ms);
  }

  /* ---------- brand mark ---------- */
  const markSVG = (sz=34) => `<svg class="mark" width="${sz}" height="${sz}" viewBox="0 0 40 40" fill="none" aria-hidden="true">
    <circle cx="20" cy="20" r="18.5" stroke="#d4af37" stroke-width="1.6"/>
    <circle cx="20" cy="20" r="14.5" stroke="#d4af37" stroke-width="0.7" opacity="0.55"/>
    <path d="M20 7 L24 20 L20 33 L16 20 Z" fill="#d4af37"/>
    <path d="M7 20 L20 16 L33 20 L20 24 Z" fill="#d4af37" opacity="0.75"/>
    <circle cx="20" cy="20" r="3" fill="#0a0e1a" stroke="#f0d47a" stroke-width="1"/></svg>`;

  /* ---------- generative cover art ---------- */
  function coverSVG(seed, w=800, h=420){
    const R = rng(hashStr("tryeza"+seed));
    const variant = Math.floor(R()*6);
    const hue = 38 + Math.floor(R()*10); // gold family
    const dark1 = "#070b16", dark2 = "#0d1530";
    let shapes = "";
    const gold = (o=1) => `hsla(${hue},62%,${52+R()*14}%,${o})`;
    if(variant===0){ // sunburst arches
      for(let i=0;i<14;i++){ const x=80+i*48; shapes+=`<path d="M${x-30} ${h} A30 30 0 0 1 ${x+30} ${h}" fill="none" stroke="${gold(.25+R()*.4)}" stroke-width="${1+R()*3}"/>`; }
      shapes += `<circle cx="${w/2}" cy="${h*0.72}" r="70" fill="${gold(.85)}" opacity=".9"/><circle cx="${w/2}" cy="${h*0.72}" r="86" fill="none" stroke="${gold(.5)}" stroke-width="1.5"/>`;
    } else if(variant===1){ // concentric diamonds
      for(let i=0;i<9;i++){ const s=26+i*30; shapes+=`<rect x="${w/2-s}" y="${h/2-s*0.62}" width="${s*2}" height="${s*1.24}" fill="none" stroke="${gold(.18+R()*.35)}" stroke-width="${1+R()*2.4}" transform="rotate(${R()*8-4} ${w/2} ${h/2})"/>`; }
      shapes += `<circle cx="${w/2}" cy="${h/2}" r="20" fill="${gold(.9)}"/>`;
    } else if(variant===2){ // waves
      for(let i=0;i<12;i++){ const y=40+i*32; let p=`M-20 ${y}`; for(let x=0;x<=w;x+=40) p+=` Q${x+20} ${y-18+R()*10} ${x+40} ${y}`; shapes+=`<path d="${p}" fill="none" stroke="${gold(.2+R()*.4)}" stroke-width="${1+R()*2.6}"/>`; }
      shapes += `<circle cx="${w*0.78}" cy="${h*0.3}" r="46" fill="${gold(.85)}"/>`;
    } else if(variant===3){ // columns / colonnade
      for(let i=0;i<8;i++){ const x=60+i*96; shapes+=`<rect x="${x}" y="${h*0.2}" width="26" height="${h*0.62}" fill="none" stroke="${gold(.3+R()*.35)}" stroke-width="2"/><rect x="${x-8}" y="${h*0.2-14}" width="42" height="10" fill="${gold(.5)}"/>`; }
      shapes += `<ellipse cx="${w/2}" cy="${h*0.16}" rx="52" ry="52" fill="${gold(.8)}"/>`;
    } else if(variant===4){ // scattered coins
      for(let i=0;i<46;i++){ const x=R()*w, y=R()*h, r=4+R()*22; shapes+=`<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="none" stroke="${gold(.14+R()*.4)}" stroke-width="${(0.8+R()*2).toFixed(1)}"/>`; }
      shapes += `<circle cx="${w*0.3}" cy="${h*0.62}" r="54" fill="${gold(.88)}"/><circle cx="${w*0.3}" cy="${h*0.62}" r="66" fill="none" stroke="${gold(.6)}" stroke-width="1.5" stroke-dasharray="6 5"/>`;
    } else { // mountain / table lines
      for(let i=0;i<7;i++){ const y=h*0.25+i*38; shapes+=`<path d="M0 ${y} L${w*0.35} ${y-90} L${w*0.6} ${y+20} L${w} ${y-70} L${w} ${y+200} L0 ${y+200} Z" fill="none" stroke="${gold(.2+R()*.3)}" stroke-width="1.6"/>`; }
      shapes += `<circle cx="${w*0.62}" cy="${h*0.24}" r="44" fill="${gold(.85)}"/>`;
    }
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="g${seed}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="${dark2}"/><stop offset="1" stop-color="${dark1}"/></linearGradient></defs>
      <rect width="${w}" height="${h}" fill="url(#g${seed})"/>${shapes}
      <rect width="${w}" height="${h}" fill="black" opacity="0.12"/></svg>`;
  }
  function citySVG(qytet){
    const seed = hashStr("city"+qytet)%97+1;
    const motifs = { "Tiranë":0, "Korçë":3, "Durrës":2, "Shkodër":5 };
    return coverSVG(seed + (motifs[qytet]??1)*13, 600, 380);
  }

  /* ---------- stars ---------- */
  function stars(r, n=0){
    if(r==null || !(r>0)){
      return `<span class="stars" title="Pa vlerësime ende"><span class="off">★★★★★</span></span>` +
        (n?` <span style="color:var(--muted2);font-size:.82rem">(${n})</span>`:`<span style="color:var(--muted2);font-size:.82rem"> · pa vlerësime</span>`);
    }
    const full = Math.round(r*2)/2;
    let s = "";
    for(let i=1;i<=5;i++){
      s += i<=Math.floor(full) ? "★" : (i-0.5===full ? "⯪" : `<span class="off">★</span>`);
    }
    return `<span class="stars" title="${r.toFixed(1)} / 5">${s}</span>` + (n?` <span style="color:var(--muted2);font-size:.82rem">(${n})</span>`:"");
  }

  /* ---------- cover: foto reale nëse ka, ndryshe art gjenerativ ---------- */
  function coverFor(r, w=800, h=420){
    if(r && r.fotot && r.fotot.length){
      const f = r.fotot[0];
      const cred = f.autor ? `Foto: ${f.autor}${f.license?` (${f.license})`:""}` : "Foto reale";
      return `<img class="cover-img" src="${esc(f.file)}" alt="${esc(r.emer)}" title="${esc(cred)}" loading="lazy" width="${w}" height="${h}"/>`;
    }
    return coverSVG(r ? (r.coverSeed||1) : 1, w, h);
  }
  function waLink(rest, msg){
    const digits = (rest.telefon||"").replace(/\D/g, "");
    if(!digits) return "";
    return `https://wa.me/${digits}?text=${encodeURIComponent(msg)}`;
  }

  /* ---------- data lookups ---------- */
  const dataArr = () => ((typeof RESTORANTET!=="undefined" && RESTORANTET) || window.RESTORANTET || []);
  const restById = id => dataArr().find(r=>r.id===id);
  const getReviews = id => {
    const seeds = (restById(id)?.vleresimetSeed||[]).map(v=>({...v, seed:true}));
    const user = load(LS.reviews, []).filter(r=>r.restId===id);
    return [...user, ...seeds].sort((a,b)=>b.data.localeCompare(a.data));
  };
  const liveRating = id => {
    const all = getReviews(id);
    const r0 = restById(id); if(!r0) return {r:0,n:0};
    if(!all.length) return {r:r0.rating, n:r0.nrVleresime};
    const sumSeed = r0.rating*r0.nrVleresime;
    const sum = sumSeed + all.filter(v=>!v.seed).reduce((s,v)=>s+v.yje,0);
    const n = r0.nrVleresime + all.filter(v=>!v.seed).length;
    return { r: sum/n, n };
  };
  const favs = () => load(LS.favs, []);
  const isFav = id => favs().includes(id);
  const toggleFav = id => {
    let f = favs(); const i = f.indexOf(id);
    if(i>=0){ f.splice(i,1); toast("U hoq nga të preferuarat"); }
    else { f.push(id); toast("<b>♥</b> U shtua te të preferuarat"); }
    save(LS.favs, f); return f.includes(id);
  };

  /* ---------- availability engine ---------- */
  const bookings = () => load(LS.bookings, []);
  function suitableTables(rest, persona, zonaId){
    return (rest.tavolina||[]).filter(t=>t.vende>=persona && (!zonaId || t.zona===zonaId));
  }
  function pseudoBusy(rest, date, time, persona, zonaId){
    const suit = suitableTables(rest, persona, zonaId);
    if(!suit.length) return 1; // no fitting table at all
    const R = rng(hashStr(rest.id+date+time+zonaId+persona));
    const peak = (time>="19:00"&&time<="22:00")||(time>="12:30"&&time<="14:30");
    const base = peak ? 0.55 : 0.30;
    const busyFrac = Math.min(0.95, base + R()*0.35);
    return Math.floor(suit.length * busyFrac);
  }
  function slotInfo(rest, date, time, persona, zonaId){
    const suit = suitableTables(rest, persona, zonaId);
    if(!suit.length) return { free:false, freeTables:0, total:suit.length, reason:"no-table" };
    const booked = bookings().filter(b=>b.restId===rest.id&&b.date===date&&b.time===time&&b.status!=="anuluar");
    const busy = pseudoBusy(rest,date,time,persona,zonaId);
    const taken = new Set();
    booked.forEach(b=>{ (b.tavolina||[]).forEach(t=>taken.add(t)); });
    const freeTables = suit.filter(t=>!taken.has(t.id));
    const stillFree = freeTables.length - busy;
    return { free: stillFree>0, freeTables: Math.max(0,stillFree), total: suit.length, freeList: freeTables };
  }
  function freeTablesList(rest, date, time, persona, zonaId){
    const s = slotInfo(rest,date,time,persona,zonaId);
    if(!s.free) return [];
    const R = rng(hashStr(rest.id+date+time+zonaId+persona+"tbl"));
    const shuffled = [...s.freeList].sort(()=>R()-0.5);
    return shuffled.slice(0, s.freeTables);
  }

  /* ---------- booking CRUD ---------- */
  function createBooking(b){
    const all = bookings();
    b.code = genCode(); b.status = "aktive"; b.createdAt = new Date().toISOString(); b.id = uid();
    all.push(b); save(LS.bookings, all); return b;
  }
  function findBooking(code){ return bookings().find(b=>b.code.toUpperCase()===String(code).toUpperCase().trim()); }
  function updateBooking(code, patch){
    const all = bookings(); const i = all.findIndex(b=>b.code===code);
    if(i<0) return null; Object.assign(all[i], patch); save(LS.bookings, all); return all[i];
  }

  /* ---------- chrome ---------- */
  const NAV = [
    ["index.html","Kreu"],["restorante.html","Restorante"],["rezervimet.html","Rezervimet e mia"],
    ["blog.html","Blog"],["faq.html","FAQ"],["kodi.html","Kodi burimor"],
  ];
  function renderChrome(active){
    document.title = document.title.includes("TRYEZA") ? document.title : document.title + " — TRYEZA";
    const h = $("header.site");
    if(h){
      h.innerHTML = `<div class="wrap nav">
        <a class="brand" href="index.html" aria-label="TRYEZA — kreu">${markSVG()}TRYEZA</a>
        <nav class="nav-links" id="navLinks">${NAV.map(([f,l])=>`<a href="${f}" class="${f===active?"active":""}">${l}</a>`).join("")}</nav>
        <div class="nav-right">
          <a class="btn btn-gold btn-sm" href="sugjero.html">＋ Sugjero restorant</a>
          <button class="burger" id="burger" aria-label="Menuja">☰</button>
        </div></div>`;
      $("#burger").addEventListener("click",()=>$("#navLinks").classList.toggle("open"));
      $$("#navLinks a").forEach(a=>a.addEventListener("click",()=>$("#navLinks").classList.remove("open")));
    }
    const f = $("footer.site");
    if(f){
      f.innerHTML = `<div class="wrap">
        <div class="foot-grid">
          <div><div class="foot-brand">TRYEZA</div>
            <p style="color:var(--muted);font-size:.9rem;max-width:320px;margin-top:.5rem">Rezervo tavolinën tënde në restorantet më të mira të Shqipërisë — në sekonda, pa telefonata, falas.</p></div>
          <div><h4>Zbulo</h4>${[["restorante.html","Të gjitha restorantet"],["restorante.html?qytet=Tiranë","Tiranë"],["restorante.html?qytet=Korçë","Korçë"],["restorante.html?qytet=Durrës","Durrës"],["restorante.html?qytet=Shkodër","Shkodër"]].map(([u,l])=>`<a href="${u}">${l}</a>`).join("")}</div>
          <div><h4>Llogaria</h4><a href="rezervimet.html">Rezervimet e mia</a><a href="sugjero.html">Sugjero restorant</a><a href="dashboard.html">Paneli i restorantit</a><a href="faq.html">Pyetje të shpeshta</a></div>
          <div><h4>Kompania</h4><a href="blog.html">Blog</a><a href="kodi.html">Kodi burimor</a><a href="kredite.html">Kreditë e fotove</a><a href="faq.html#kontakt">Kontakt</a></div>
        </div>
        <div class="foot-bottom"><span>© 2026 TRYEZA — Të gjitha të drejtat e rezervuara.</span><span>Krijuar nga <b style="color:var(--gold-lt)">Erion Nezha</b></span></div>
      </div>`;
    }
    if(!$("#toast")){ const t=document.createElement("div"); t.id="toast"; document.body.appendChild(t); }
  }

  function cardHTML(r){
    const {r:rt, n} = liveRating(r.id);
    const fav = isFav(r.id) ? "on" : "";
    return `<article class="rcard" data-id="${r.id}">
      <button class="fav ${fav}" data-fav="${r.id}" aria-label="Shto te të preferuarat">♥</button>
      <span class="citychip">${esc(r.qytet)}</span>
      <a class="cover" href="restorant.html?id=${r.id}" aria-label="${esc(r.emer)}">${coverFor(r)}</a>
      <div class="body">
        <h3><a href="restorant.html?id=${r.id}">${esc(r.emer)}</a></h3>
        <div class="meta">${stars(rt,n)}<span class="price">${cmimTxt(r.cmim)}</span><span>· ${esc(r.lagje)}</span></div>
        <div class="tags">${(r.kuzhina||[]).slice(0,3).map(k=>`<span class="tag">${esc(k)}</span>`).join("")}</div>
        <div style="margin-top:auto;padding-top:.6rem"><a class="btn btn-ghost btn-sm" style="width:100%" href="restorant.html?id=${r.id}#rezervo">Gjej orarin e lirë</a></div>
      </div></article>`;
  }
  function bindFavs(root=document){
    $$("[data-fav]", root).forEach(b=>{
      b.onclick = e => { e.preventDefault(); e.stopPropagation(); const on = toggleFav(b.dataset.fav); b.classList.toggle("on", on); };
    });
  }

  function trackPage(){ /* placeholder for analytics hook */ }

  return { LS, QYTETET, DITET, MUAJT, SLOTS, $, $$, esc, load, save, uid, todayStr, fmtDate,
    cmimTxt, genCode, toast, markSVG, coverSVG, coverFor, waLink, citySVG, stars, restById, getReviews,
    liveRating, favs, isFav, toggleFav, suitableTables, slotInfo, freeTablesList,
    bookings, createBooking, findBooking, updateBooking, renderChrome, cardHTML, bindFavs, trackPage };
})();
window.TRY = TRY;
