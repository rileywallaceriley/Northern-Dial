const VERSION = 'v14';
const STATIC_CACHE = `northern-dial-static-${VERSION}`;
const PAGE_CACHE = `northern-dial-pages-${VERSION}`;
const IMAGE_CACHE = `northern-dial-images-${VERSION}`;
const DATA_CACHE = `northern-dial-data-${VERSION}`;

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
const DATA_PATHS = new Set([
  '/discovery-data.json',
  '/artist-profile-index.json',
  '/library_artist_images.tsv',
  '/artists.html'
]);

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
  const keep = new Set([STATIC_CACHE, PAGE_CACHE, IMAGE_CACHE, DATA_CACHE]);

  event.waitUntil(
    Promise.all([
      caches.keys().then(names => Promise.all(
        names.filter(name => !keep.has(name)).map(name => caches.delete(name))
      )),
      self.registration.navigationPreload
        ? self.registration.navigationPreload.enable()
        : Promise.resolve(),
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

async function navigationRace(request, preloadResponse, cacheName, delayMs = 350, event) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const network = (async () => {
    try {
      const preloaded = preloadResponse ? await preloadResponse : null;
      const response = preloaded || await fetch(request, { cache: 'no-store' });
      if (response && response.ok) {
        await cache.put(request, response.clone());
      }
      return response;
    } catch (_) {
      return null;
    }
  })();

  // Keep the refresh alive even when the cached page wins the race.
  if (event) event.waitUntil(network.then(() => undefined));

  if (!cached) {
    const response = await network;
    if (response) return response;
    throw new Error('Navigation failed and no cached page exists.');
  }

  const delayedCache = new Promise(resolve => {
    setTimeout(() => resolve(cached), delayMs);
  });

  const response = await Promise.race([
    network.then(result => result || cached),
    delayedCache
  ]);

  // The network promise keeps running after a cached response wins the race,
  // refreshing PAGE_CACHE for the next navigation.
  return response;
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

  if (request.mode === 'navigate' && url.pathname.endsWith('/discover.html')) {
    event.respondWith(networkFirst(request, PAGE_CACHE, {cache:'no-store'}));
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      navigationRace(request, event.preloadResponse, PAGE_CACHE, 350, event)
        .catch(() => caches.match(request))
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Discovery evidence and its ranking code must refresh together.
  if (url.origin === self.location.origin && url.pathname === '/discovery-data.json') {
    event.respondWith(networkFirst(request, DATA_CACHE, {cache:'no-store'}));
    return;
  }

  // Curated catalogue data changes much less often than live station state.
  // Serve it instantly from cache on repeat visits and refresh in the background.
  if (url.origin === self.location.origin && DATA_PATHS.has(url.pathname)) {
    event.respondWith(staleWhileRevalidate(request, DATA_CACHE));
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

  // Keep the navigation/player shell network-first while the persistent
  // listening experience is actively evolving. Other JS can remain SWR.
  if (['/nd-shell.js','/discover.js','/discover-engine.js'].includes(url.pathname)) {
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
