"""PWA assets: manifest + service worker + icon."""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#c084fc"/>
    <stop offset="1" stop-color="#22d3ee"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="96" fill="#0f1115"/>
<rect x="40" y="40" width="432" height="432" rx="80" fill="url(#g)" opacity=".15"/>
<text x="256" y="330" font-size="260" text-anchor="middle" font-family="sans-serif">🤖</text>
<text x="256" y="430" font-size="56" text-anchor="middle"
      font-family="sans-serif" fill="#c084fc" font-weight="bold">MIMI</text>
</svg>"""

MANIFEST = """{
  "name": "Agent Mimi",
  "short_name": "Mimi",
  "description": "Personal Life Agent — dashboard, tasks, study, finance",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0f1115",
  "theme_color": "#0f1115",
  "icons": [
    {
      "src": "/icon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}"""

SERVICE_WORKER = """/* Mimi PWA service worker */
const CACHE = 'mimi-v7-1';
const ASSETS = ['/', '/manifest.json', '/icon.svg', '/data.json'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS).catch(()=>{})).then(()=>self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // API: network first, cache fallback
  if (url.pathname === '/data.json') {
    e.respondWith(
      fetch(e.request).then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return r;
      }).catch(()=> caches.match(e.request))
    );
    return;
  }
  // Shell: cache first, network fallback
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return r;
    })).catch(()=> caches.match('/'))
  );
});
"""

INSTALL_BANNER = """
<div id="pwa-install" style="display:none;position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:var(--card2);border:1px solid var(--accent);padding:10px 16px;border-radius:12px;font-size:13px;z-index:60;gap:10px;align-items:center">
  <span>📱 Install Mimi on home screen?</span>
  <button onclick="installPWA()" style="background:var(--accent);color:#000;border:none;border-radius:6px;padding:6px 12px;font-weight:600;cursor:pointer">Install</button>
  <button onclick="document.getElementById('pwa-install').style.display='none'" style="background:transparent;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:6px 10px;cursor:pointer">Later</button>
</div>
<script>
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;
  const b = document.getElementById('pwa-install');
  if (b) b.style.display = 'flex';
});
function installPWA() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then(() => {
    deferredPrompt = null;
    document.getElementById('pwa-install').style.display = 'none';
  });
}
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
</script>
"""
