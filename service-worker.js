const VERSION = 'v5';
const STATIC_CACHE = `northern-dial-static-${VERSION}`;
const PAGE_CACHE = `northern-dial-pages-${VERSION}`;
const IMAGE_CACHE = `northern-dial-images-${VERSION}`;

const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './nd-shell.css',
  './nd-shell.js',
  './nd-banner.css',
  './nd-i18n.js',
  'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap',
  'https://i.imgur.com/XIAPd0N.png'
];

const LIVE_HOSTS = new Set([
  'a10.asurahosting.com'
]);

const CSS_EXTENSIONS = /\.css$/i;
const STATIC_EXTENSIONS = /\.(?:js|woff2?|ttf|otf)$/i;
const IMAGE_EXTENSIONS = /\.(?:png|jpe?g|gif|webp|avif|svg)$/i;

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(STATIC_CACHE).then(async cache => {
      await Promise.allSettled(
        APP_SHELL.map(asset => cache.add(asset))
      );
    })
  );
});

self.addEventListener('activate', event => {
  const keep = new Set([STATIC_CACHE, PAGE_CACHE, IMAGE_CACHE]);

  event.waitUntil(
    Promise.all([
      caches.keys().then(names => Promise.all(
        names.filter(name => !keep.has(name)).map(name => caches.delete(name))
      )),
      self.clients.claim()
    ])
  );
});

async function networkFirst(request, cacheName, fetchOptions = {}) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request, fetchOptions);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw error;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const network = fetch(request)
    .then(response => {
      if (response && (response.ok || response.type === 'opaque')) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  if (cached) {
    network.catch(() => null);
    return cached;
  }

  const response = await network;
  if (response) return response;
  throw new Error('Network unavailable and no cached response exists.');
}

self.addEventListener('fetch', event => {
  const request = event.request;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Never cache the live stream, now-playing metadata, song requests or other
  // AzuraCast traffic. These responses need to stay current at all times.
  if (LIVE_HOSTS.has(url.hostname)) return;

  // Range requests are commonly used by audio/video. Leave them untouched.
  if (request.headers.has('range')) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      networkFirst(request, PAGE_CACHE, { cache: 'no-store' })
        .catch(() => caches.match(request))
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  // CSS changes are frequent while the site is actively developed.
  // Always check the network first so old layout rules do not reappear.
  if (CSS_EXTENSIONS.test(url.pathname)) {
    event.respondWith(
      networkFirst(request, STATIC_CACHE, { cache: 'no-store' })
        .catch(() => caches.match(request))
    );
    return;
  }

  if (STATIC_EXTENSIONS.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  if (IMAGE_EXTENSIONS.test(url.pathname) || request.destination === 'image') {
    event.respondWith(staleWhileRevalidate(request, IMAGE_CACHE));
    return;
  }

  // Keep JSON/API-style data fresh unless it is explicitly part of the app shell.
  if (request.destination === '' && /\.(?:json|xml)$/i.test(url.pathname)) {
    return;
  }

  // For everything else, prefer the browser/network. The service worker only
  // takes responsibility for resources where caching clearly helps.
});
