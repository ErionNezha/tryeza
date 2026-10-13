/* Created by Erion Nezha — © 2026 All rights reserved */
/* TRYEZA — PWA: regjistrimi i Service Worker + butoni i instalimit. */
"use strict";
(function () {
  if (!("serviceWorker" in navigator)) return;
  var secure = location.protocol === "https:" ||
    location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if (!secure) return;

  /* ---------- Service Worker ---------- */
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function () { /* hesht */ });
  });

  function T(key, fallback) {
    try {
      if (typeof I18N !== "undefined" && I18N.t) {
        var v = I18N.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    return fallback;
  }
  function isStandalone() {
    return (window.matchMedia && matchMedia("(display-mode: standalone)").matches) ||
      window.navigator.standalone === true;
  }
  if (isStandalone()) return; // tashmë i instaluar — s'ka banner

  var LS_DISMISS = "tryeza.pwa.dismissed.v1";
  var LS_IOS = "tryeza.pwa.ioshint.v1";
  function dismissed() {
    try {
      var t = +localStorage.getItem(LS_DISMISS) || 0;
      return Date.now() - t < 30 * 24 * 3600 * 1000; // 30 ditë qetësi
    } catch (e) { return false; }
  }

  /* ---------- Stili (i injektuar, sipas paletës TRYEZA) ---------- */
  var css = [
    "#pwaBar{position:fixed;left:50%;bottom:18px;transform:translate(-50%,90px);z-index:90;",
    "display:flex;align-items:center;gap:.7rem;background:rgba(22,23,27,.94);backdrop-filter:blur(12px);",
    "border:1px solid rgba(197,168,128,.45);border-radius:999px;padding:.5rem .55rem .5rem .95rem;",
    "box-shadow:0 14px 40px rgba(0,0,0,.55);transition:transform .45s cubic-bezier(.2,.8,.2,1);max-width:calc(100vw - 24px)}",
    "#pwaBar.above{bottom:80px}",
    "#pwaBar.show{transform:translate(-50%,0)}",
    "#pwaBar .pwa-txt{color:#ece7dd;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    "#pwaInstall{background:linear-gradient(135deg,#ecd9b8,#c5a880 55%,#a8895e);color:#191304;border:0;",
    "border-radius:999px;padding:.55rem 1.05rem;font-weight:700;font-size:.9rem;cursor:pointer;white-space:nowrap}",
    "#pwaInstall:active{transform:scale(.96)}",
    "#pwaClose{background:none;border:0;color:#a7a296;font-size:1.05rem;line-height:1;cursor:pointer;padding:.3rem .45rem}",
    "@media (max-width:560px){#pwaBar{flex-wrap:wrap;justify-content:center;border-radius:22px;padding:.6rem .7rem}",
    "#pwaBar .pwa-txt{white-space:normal;overflow:visible;text-overflow:clip;font-size:.86rem;line-height:1.35;text-align:center;flex:1 1 150px}}"
  ].join("");
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var bar = null;
  function buildBar(text, btnLabel, onBtn) {
    if (bar) return bar;
    bar = document.createElement("div");
    bar.id = "pwaBar";
    bar.setAttribute("role", "dialog");
    bar.setAttribute("aria-label", "TRYEZA app");
    if (document.querySelector(".asst-btn")) bar.classList.add("above"); // mos u përplas me asistentin
    var span = document.createElement("span");
    span.className = "pwa-txt";
    span.textContent = text;
    bar.appendChild(span);
    if (btnLabel) {
      var btn = document.createElement("button");
      btn.id = "pwaInstall";
      btn.type = "button";
      btn.textContent = btnLabel;
      btn.addEventListener("click", onBtn);
      bar.appendChild(btn);
    }
    var x = document.createElement("button");
    x.id = "pwaClose";
    x.type = "button";
    x.setAttribute("aria-label", T("pwa.close", "Mbyll"));
    x.textContent = "✕";
    x.addEventListener("click", function () {
      hideBar();
      try { localStorage.setItem(LS_DISMISS, String(Date.now())); } catch (e) {}
    });
    bar.appendChild(x);
    document.body.appendChild(bar);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { bar.classList.add("show"); });
    });
    return bar;
  }
  function hideBar() {
    if (!bar) return;
    bar.classList.remove("show");
    var b = bar; bar = null;
    setTimeout(function () { b.remove(); }, 500);
  }

  /* ---------- Android / desktop: beforeinstallprompt ---------- */
  var deferred = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    if (dismissed()) return;
    buildBar(
      T("pwa.installTxt", "Instalo TRYEZA-n si aplikacion"),
      T("pwa.install", "📲 Instalo app-in"),
      function () {
        if (!deferred) return;
        deferred.prompt();
        deferred.userChoice.then(function () { deferred = null; hideBar(); });
      }
    );
  });
  window.addEventListener("appinstalled", function () {
    deferred = null;
    hideBar();
    try { localStorage.removeItem(LS_IOS); } catch (e) {}
  });

  /* ---------- iOS Safari: hint "Shto në Ekranin Kryesor" (vetëm 1 herë) ---------- */
  var ua = navigator.userAgent || "";
  var isIOS = /iphone|ipad|ipod/i.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var isSafari = /safari/i.test(ua) && !/crios|fxios|edgios/i.test(ua);
  if (isIOS && isSafari) {
    var seen = false;
    try { seen = !!localStorage.getItem(LS_IOS); } catch (e) {}
    if (!seen && !dismissed()) {
      setTimeout(function () {
        if (bar || isStandalone()) return;
        buildBar(T("pwa.iosHint", "Për instalim: Ndaj ⬆ → «Shto në Ekranin Kryesor»"), null, null);
        try { localStorage.setItem(LS_IOS, "1"); } catch (e) {}
      }, 2500);
    }
  }
})();
