const CACHE = "events-v1";

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE).then(cache => cache.addAll([
            "/events",
            "/static/events_manifest.json",
            "/static/web-app-manifest-192x192.png",
            "/static/web-app-manifest-512x512.png"
        ]))
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(r => r || fetch(event.request))
    );
});