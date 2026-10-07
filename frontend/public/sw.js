// ─────────────────────────────────────────────────────────────
// JAGRAT Service Worker — v4 (safe caching)
// ─────────────────────────────────────────────────────────────
// IMPORTANT: Never cache /_next/static/chunks — Next.js/Turbopack
// content-hashes every chunk so stale entries break the module graph.
// ─────────────────────────────────────────────────────────────
const CACHE_NAME = 'jagrat-v4';

// Only cache true static assets that don't change per-build
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

// ── Install ───────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(STATIC_ASSETS).catch(() => {})
    )
  );
  self.skipWaiting();
});

// ── Activate: purge ALL old caches immediately ────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: NEVER intercept Next.js chunks or API calls ────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Pass through: non-GET, cross-origin, API calls, Next.js chunks/HMR
  if (
    request.method !== 'GET' ||
    url.origin !== self.location.origin ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/_next/') ||
    url.pathname.startsWith('/__nextjs') ||
    url.search.includes('_rsc') ||
    url.search.includes('HMR')
  ) {
    return; // Let the browser handle it normally
  }

  // Only cache the known static files listed above
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (
          response.ok &&
          response.type === 'basic' &&
          STATIC_ASSETS.some(a => url.pathname === a)
        ) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});
