// Progressive Web App (PWA) Service Worker Configuration

const CACHE_NAME = 'agentflow-v1.1';
const RUNTIME_CACHE = 'agentflow-runtime-v1.1';
const IMAGE_CACHE = 'agentflow-images-v1';
const API_CACHE = 'agentflow-api-v1';

// Cache duration in seconds
const CACHE_DURATION = {
  static: 7 * 24 * 60 * 60, // 7 days
  api: 5 * 60, // 5 minutes
  images: 30 * 24 * 60 * 60, // 30 days
};

// Assets to cache on install
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png'
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        if (self.location.hostname === 'localhost') {
          console.log('Opened cache');
        }
        return cache.addAll(PRECACHE_URLS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME, RUNTIME_CACHE, IMAGE_CACHE, API_CACHE];
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!cacheWhitelist.includes(cacheName)) {
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Helper: Check if response is cacheable
function isCacheable(request, response) {
  // Don't cache if not a success response
  if (!response || response.status !== 200 || response.type === 'error') {
    return false;
  }
  
  // Don't cache POST requests
  if (request.method !== 'GET') {
    return false;
  }
  
  return true;
}

// Helper: Get cache name based on URL
function getCacheName(url) {
  if (url.includes('/api/')) {
    return API_CACHE;
  }
  if (url.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/)) {
    return IMAGE_CACHE;
  }
  if (url.match(/\.(js|css|woff|woff2|ttf|eot)$/)) {
    return CACHE_NAME;
  }
  return RUNTIME_CACHE;
}

// Helper: Get cache expiry based on cache name
function getCacheExpiry(cacheName) {
  switch (cacheName) {
    case IMAGE_CACHE:
      return CACHE_DURATION.images;
    case API_CACHE:
      return CACHE_DURATION.api;
    default:
      return CACHE_DURATION.static;
  }
}

// Helper: Check if cached response is expired
function isCacheExpired(response, cacheName) {
  const cachedTime = response.headers.get('sw-cache-time');
  if (!cachedTime) {
    return true;
  }
  
  const age = (Date.now() - parseInt(cachedTime, 10)) / 1000;
  return age > getCacheExpiry(cacheName);
}

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - network first, cache fallback with expiry
  if (request.url.includes('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  // Images - cache first with long expiry
  if (request.url.match(/\.(png|jpg|jpeg|svg|gif|webp|ico)$/)) {
    event.respondWith(cacheFirst(request, IMAGE_CACHE));
    return;
  }

  // Static assets - cache first, network fallback
  if (request.url.match(/\.(js|css|woff|woff2|ttf|eot)$/)) {
    event.respondWith(cacheFirst(request, CACHE_NAME));
    return;
  }

  // HTML pages - network first, cache fallback
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, RUNTIME_CACHE));
    return;
  }

  // Default - network first
  event.respondWith(networkFirst(request, RUNTIME_CACHE));
});

// Cache first strategy with expiry check
async function cacheFirst(request, cacheName = CACHE_NAME) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {
    // Check if cache is expired
    if (!isCacheExpired(cached, cacheName)) {
      // Update in background if needed
      updateCacheInBackground(request, cache);
      return cached;
    }
  }

  try {
    const response = await fetch(request);
    if (isCacheable(request, response)) {
      // Add timestamp header before caching
      const clonedResponse = response.clone();
      const responseToCache = new Response(clonedResponse.body, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: new Headers({
          ...Object.fromEntries(clonedResponse.headers),
          'sw-cache-time': Date.now().toString(),
        }),
      });
      cache.put(request, responseToCache);
    }
    return response;
  } catch (error) {
    if (cached) {
      // Return expired cache if network fails
      return cached;
    }
    throw error;
  }
}

// Update cache in background (stale-while-revalidate)
function updateCacheInBackground(request, cache) {
  fetch(request)
    .then((response) => {
      if (response.ok) {
        const responseToCache = new Response(response.clone().body, {
          status: response.status,
          statusText: response.statusText,
          headers: new Headers({
            ...Object.fromEntries(response.headers),
            'sw-cache-time': Date.now().toString(),
          }),
        });
        cache.put(request, responseToCache);
      }
    })
    .catch(() => {
      // Silently fail background updates
    });
}

// Network first strategy with cache fallback
async function networkFirst(request, cacheName = RUNTIME_CACHE) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request);
    if (isCacheable(request, response)) {
      const responseToCache = new Response(response.clone().body, {
        status: response.status,
        statusText: response.statusText,
        headers: new Headers({
          ...Object.fromEntries(response.headers),
          'sw-cache-time': Date.now().toString(),
        }),
      });
      cache.put(request, responseToCache);
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    throw error;
  }
}

// Background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  // Implement data synchronization logic
  if (self.location.hostname === 'localhost') {
    console.log('Background sync initiated');
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'AgentFlow Notification';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/logo192.png',
    badge: '/badge.png',
    data: data.data || {},
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

// Message handling
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});
