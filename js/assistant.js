/* Created by Erion Nezha — © 2026 All rights reserved */
/* TRYEZA — Asistenti: widget pyetjesh me rregulla (keyword matching mbi data.js).
   Pa backend, pa API — përgjigjet ndërtohen lokalisht nga të dhënat reale. */
"use strict";
(function(){
  if(typeof TRY === "undefined") return;
  const R = ((typeof RESTORANTET !== "undefined" && RESTORANTET) || window.RESTORANTET || []);
  if(!R.length) return;

  const SEAFOOD = ["Seafood", "Peshk", "Fruta deti"];
  const norm = s => String(s || "").toLowerCase()
    .replace(/ë/g, "e").replace(/ç/g, "c")
    .replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();

  /* ---------- ndërtimi i widget-it ---------- */
  const btn = document.createElement("button");
  btn.className = "asst-btn";
  btn.type = "button";
  btn.setAttribute("aria-haspopup", "dialog");
  btn.setAttribute("aria-expanded", "false");
  btn.innerHTML = `<span class="asst-ic" aria-hidden="true">✦</span><span>${TRY.esc(TRY.t("asst.open"))}</span>`;

  const panel = document.createElement("div");
  panel.className = "asst-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", TRY.t("asst.title"));
  panel.innerHTML = `
    <div class="asst-head">${TRY.markSVG(26)}<b>${TRY.esc(TRY.t("asst.title"))}</b>
      <button class="asst-x" type="button" aria-label="${TRY.esc(TRY.t("asst.close"))}">✕</button></div>
    <div class="asst-msgs" id="asstMsgs"></div>
    <div class="asst-chips">
      ${["asst.q1","asst.q2","asst.q3","asst.q4"].map(k =>
        `<button class="asst-chip" type="button">${TRY.esc(TRY.t(k))}</button>`).join("")}
    </div>
    <form class="asst-form" id="asstForm">
      <input type="text" id="asstInput" placeholder="${TRY.esc(TRY.t("asst.ph"))}" autocomplete="off" aria-label="${TRY.esc(TRY.t("asst.ph"))}">
      <button class="btn btn-gold btn-sm" type="submit">${TRY.esc(TRY.t("asst.send"))}</button>
    </form>`;
  document.body.append(btn, panel);

  const msgs = TRY.$("#asstMsgs", panel);
  const input = TRY.$("#asstInput", panel);
  let greeted = false;

  function addMsg(html, cls){
    const d = document.createElement("div");
    d.className = "asst-msg " + cls;
    d.innerHTML = html;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }
  function cardFor(r){
    const { r: rt, n } = TRY.liveRating(r.id);
    return `<a class="asst-card" href="restorant.html?id=${r.id}">
      <span class="ac-img">${TRY.coverFor(r, 200, 140)}</span>
      <span class="ac-t"><b>${TRY.esc(r.emer)}</b>
      <span>${TRY.stars(rt, n)} · ${TRY.esc(r.qytet)} · ${TRY.cmimTxt(r.cmim)}</span></span></a>`;
  }
  function replyWith(title, list){
    const cards = list.length
      ? `<div class="asst-cards">${list.map(cardFor).join("")}</div>` : "";
    addMsg(`${TRY.esc(title)}${cards}
      <a class="asst-all" href="restorante.html">${TRY.esc(TRY.t("asst.browseAll"))} →</a>`, "bot");
  }

  /* ---------- motori i rregullave ---------- */
  function cityOf(q){
    if(q.includes("tiran")) return "Tiranë";
    if(q.includes("korc")) return "Korçë";
    if(q.includes("durres")) return "Durrës";
    if(q.includes("shkod")) return "Shkodër";
    return "";
  }
  const byRating = list => {
    const ids = new Set(list.map(r => r.id));
    return TRY.leaderboard().filter(x => ids.has(x.r.id)).map(x => x.r);
  };
  const inCity = (list, city) => city ? list.filter(r => r.qytet === city) : list;

  function answer(raw){
    const q = norm(raw);
    const city = cityOf(q);
    const citySuffix = city ? TRY.t("asst.inCity", { city }) : "";
    const pool = inCity(R, city);

    if(/^(pershendetje|hello|hi|hej|tung)\b/.test(q) && q.length < 24){
      addMsg(TRY.esc(TRY.t("asst.hello")), "bot");
      return;
    }
    if(q.includes("hapur") || q.includes("open now") || q === "open"){
      const open = byRating(pool.filter(r => TRY.openNow(r)));
      replyWith(TRY.t("asst.openNow") + citySuffix + ":", open.slice(0, 3));
      return;
    }
    if(q.includes("det") || q.includes("seafood") || q.includes("peshk") || q.includes("fish")){
      const list = byRating(pool.filter(r => (r.kuzhina || []).some(k => SEAFOOD.includes(k))));
      replyWith(TRY.t("asst.seafood"), list.slice(0, 3));
      return;
    }
    if(q.includes("tradicional") || q.includes("traditional")){
      const list = byRating(pool.filter(r =>
        (r.kuzhina || []).some(k => k.toLowerCase().includes("tradicionale"))));
      replyWith(TRY.t("asst.trad"), list.slice(0, 3));
      return;
    }
    if(q.includes("lir") || q.includes("cheap") || q.includes("affordable") || q.includes("buxhet")){
      const list = [...pool].sort((a, b) =>
        (a.cmim - b.cmim) || (TRY.liveRating(b.id).r - TRY.liveRating(a.id).r));
      replyWith(TRY.t("asst.cheap") + citySuffix + ":", list.slice(0, 3));
      return;
    }
    if(q.includes("mir") || q.includes("best") || q.includes("top") ||
       q.includes("vleres") || q.includes("rated") || city){
      replyWith(TRY.t("asst.best") + citySuffix + ":", byRating(pool).slice(0, 3));
      return;
    }
    addMsg(TRY.esc(TRY.t("asst.none")) +
      ` <a class="asst-all" href="restorante.html">${TRY.esc(TRY.t("asst.browseAll"))} →</a>`, "bot");
  }

  /* ---------- ndërveprimi ---------- */
  function openPanel(){
    panel.classList.add("open");
    btn.setAttribute("aria-expanded", "true");
    if(!greeted){ greeted = true; addMsg(TRY.esc(TRY.t("asst.hello")), "bot"); }
    setTimeout(() => input.focus(), 60);
  }
  function closePanel(){
    panel.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
  }
  btn.addEventListener("click", () =>
    panel.classList.contains("open") ? closePanel() : openPanel());
  TRY.$(".asst-x", panel).addEventListener("click", closePanel);
  document.addEventListener("keydown", e => { if(e.key === "Escape") closePanel(); });

  function ask(text){
    const v = String(text || "").trim();
    if(!v) return;
    addMsg(TRY.esc(v), "me");
    input.value = "";
    setTimeout(() => answer(v), 180);
  }
  TRY.$("#asstForm", panel).addEventListener("submit", e => { e.preventDefault(); ask(input.value); });
  TRY.$$(".asst-chip", panel).forEach(ch =>
    ch.addEventListener("click", () => ask(ch.textContent)));
})();
