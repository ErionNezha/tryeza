/* Created by Erion Nezha — © 2026 All rights reserved */
/* TRYEZA — Service Worker: offline-first shell, network-first pages. */
"use strict";

var CACHE = "tryeza-v1";
var SCOPE_URL = self.registration.scope; // p.sh. https://erionnezha.github.io/tryeza/
var U = function (p) { return new URL(p, SCOPE_URL).toString(); };

/* Shell-i minimal — NUK pre-cache-ohen fotot (janë shumë); ato ruhen në runtime. */
var SHELL = [
  U("./"),
  U("index.html"),
  U("offline.html"),
  U("css/style.css"),
  U("js/data.js"),
  U("js/i18n.js"),
  U("js/app.js"),
  U("js/assistant.js"),
  U("js/pwa.js"),
  U("manifest.webmanifest"),
  U("icons/icon-192.png"),
  U("icons/icon-512.png"),
  U("icons/apple-touch-icon.png")
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE)
      .then(function (cache) { return cache.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) {
          return k === CACHE ? null : caches.delete(k);
        }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  var req = event.request;

  /* Vetëm GET pa Range (video/audio me range kalojnë direkt në rrjet). */
  if (req.method !== "GET" || req.headers.has("range")) return;

  var url;
  try { url = new URL(req.url); } catch (e) { return; }
  var sameOrigin = url.origin === self.location.origin;

  /* --- Navigimet: network-first, fallback cache, pastaj offline.html --- */
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then(function (res) {
          if (res && res.ok) {
            var copy = res.clone();
            caches.open(CACHE).then(function (c) { c.put(req, copy); });
          }
          return res;
        })
        .catch(function () {
          return caches.match(req, { ignoreSearch: true }).then(function (hit) {
            return hit || caches.match(U("offline.html"));
          });
        })
    );
    return;
  }

  if (!sameOrigin) return; // cross-origin: rrjet i zakonshëm, pa cache

  /* --- Asset-et statike (CSS/JS/fonte/imazhe): stale-while-revalidate --- */
  var dest = req.destination;
  if (["style", "script", "font", "image", ""].indexOf(dest) !== -1) {
    event.respondWith(
      caches.match(req, { ignoreSearch: true }).then(function (hit) {
        var net = fetch(req).then(function (res) {
          if (res && res.status === 200) {
            var copy = res.clone();
            caches.open(CACHE).then(function (c) { c.put(req, copy); });
          }
          return res;
        }).catch(function () { return hit; });
        return hit || net;
      })
    );
  }
});
