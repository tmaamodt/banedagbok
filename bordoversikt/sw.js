/* Service worker: lagrer appen lokalt så den virker uten nett.
   Øk VERSJON når filene endres, så iPaden henter ny versjon. */
var VERSJON = 'bordoversikt-v1';
var FILER = [
  './',
  './index.html',
  './stil.css',
  './app.js',
  './manifest.webmanifest',
  './ikoner/ikon-192.png',
  './ikoner/ikon-512.png',
  './ikoner/apple-touch-icon.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSJON).then(function (c) { return c.addAll(FILER); }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (navn) {
      return Promise.all(navn.filter(function (n) { return n !== VERSJON; })
        .map(function (n) { return caches.delete(n); }));
    }).then(function () { return self.clients.claim(); })
  );
});

// Nett først (så endringer kommer fram når iPaden er på nett), ellers lagret kopi.
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(function (svar) {
      if (svar && svar.ok && new URL(e.request.url).origin === location.origin) {
        var kopi = svar.clone();
        caches.open(VERSJON).then(function (c) { c.put(e.request, kopi); });
      }
      return svar;
    }).catch(function () {
      return caches.match(e.request, { ignoreSearch: true }).then(function (treff) {
        return treff || caches.match('./index.html');
      });
    })
  );
});
