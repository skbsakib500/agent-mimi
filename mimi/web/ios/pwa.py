"""iOS PWA assets: manifest + icon."""

MANIFEST = """{
  "name": "Mimi",
  "short_name": "Mimi",
  "description": "Personal Life OS — Nusrat + Council of 11 Brains",
  "start_url": "/app",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#f2f2f7",
  "theme_color": "#007aff",
  "icons": [
    {
      "src": "/app-icon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}"""


ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#007aff"/>
    <stop offset="1" stop-color="#af52de"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="112" fill="url(#g)"/>
<text x="256" y="330" font-size="260" text-anchor="middle"
      font-family="-apple-system, sans-serif" fill="#fff">◈</text>
</svg>"""
