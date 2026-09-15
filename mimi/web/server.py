"""Minimal HTTP server for Mimi web dashboard."""
import json, socketserver, threading, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from .render import render_page, render_data_json, render_static

HOST = "127.0.0.1"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=30")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "/index.html":
            try:
                self._send(200, render_page())
            except Exception as e:
                self._send(500, f"render error: {type(e).__name__}: {e}")
            return

        if path == "/app" or path == "/app/":
            try:
                from .ios.shell import render_page as ios_page
                self._send(200, ios_page())
            except Exception as e:
                self._send(500, f"ios error: {type(e).__name__}: {e}")
            return

        if path == "/app-manifest.json":
            from .ios.pwa import MANIFEST
            self._send(200, MANIFEST,
                       "application/manifest+json; charset=utf-8")
            return
        if path == "/app-sw.js":
            from .ios.sw import SERVICE_WORKER
            self._send(200, SERVICE_WORKER,
                       "application/javascript; charset=utf-8")
            return
        if path == "/app-icon.svg":
            from .ios.pwa import ICON_SVG
            self._send(200, ICON_SVG, "image/svg+xml")
            return
        if path == "/data.json":
            try:
                self._send(200, render_data_json(), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}), "application/json")
            return
        if path == "/health":
            self._send(200, "ok", "text/plain")
            return
        if path == "/manifest.json":
            from .pwa import MANIFEST
            self._send(200, MANIFEST, "application/manifest+json; charset=utf-8")
            return
        if path == "/sw.js":
            from .pwa import SERVICE_WORKER
            self._send(200, SERVICE_WORKER, "application/javascript; charset=utf-8")
            return
        if path == "/icon.svg":
            from .pwa import ICON_SVG
            self._send(200, ICON_SVG, "image/svg+xml")
            return
        if path.startswith("/static/"):
            name = path.split("/", 2)[2]
            try:
                body, ctype = render_static(name)
                self._send(200, body, ctype)
            except Exception as e:
                self._send(404, f"not found: {e}")
            return
        self._send(404, "not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}
        path = parsed.path
        if path == "/api/council":
            try:
                from ..council.bootstrap import bootstrap
                bootstrap()
                from ..council.council import council
                depts = [{"name": d.NAME, "role": d.ROLE,
                          "priority": d.PRIORITY}
                         for d in council().all()]
                self._send(200, json.dumps({"ok": True,
                                             "departments": depts}),
                           "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False,
                                             "error": str(e)}),
                           "application/json")
            return
        if path == "/api/launch":
            try:
                params = parse_qs(parsed.query)
                p_name = (params.get("path") or [""])[0]
                if not p_name.startswith("mimi."):
                    self._send(400, json.dumps({"ok": False,
                                                 "error": "invalid path"}),
                               "application/json")
                    return
                # Editors are TUI-only; we just confirm the module exists.
                import importlib
                importlib.import_module(p_name)
                self._send(200, json.dumps({"ok": True,
                                             "path": p_name}),
                           "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False,
                                             "error": str(e)}),
                           "application/json")
            return
        if path == "/api/persona":
            try:
                from ..personas import list_all, current_name, set_persona
                if self.command == "GET":
                    self._send(200, json.dumps({
                        "ok": True,
                        "current": current_name(),
                        "all": [{"id": p["id"], "name": p["name"],
                                 "bn": p["bn"], "icon": p["icon"]}
                                for p in list_all()],
                    }), "application/json")
                else:
                    new_p = payload.get("persona")
                    ok = set_persona(new_p) if new_p else False
                    self._send(200, json.dumps({"ok": ok,
                                                 "current": current_name()}),
                               "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}),
                           "application/json")
            return
        if path == "/api/ai-status":
            try:
                from .ios.ai_chat_api import status
                self._send(200, json.dumps({"ok": True, **status()}),
                           "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}),
                           "application/json")
            return
        if path == "/api/ai-chat":
            try:
                from .ios.ai_chat_api import handle_chat
                result = handle_chat(payload)
                self._send(200, json.dumps(result), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}),
                           "application/json")
            return
        if path == "/api/ai-reset":
            try:
                from .ios.ai_chat_api import reset
                result = reset()
                self._send(200, json.dumps(result), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}),
                           "application/json")
            return
        if path == "/api/chat":
            try:
                from .chat_api import handle_chat
                result = handle_chat(payload)
                self._send(200, json.dumps(result), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}), "application/json")
            return
        if path == "/api/action":
            try:
                from .api import handle
                result = handle(payload)
                self._send(200, json.dumps(result), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}), "application/json")
            return
        # backwards-compat
        if path == "/api/add":
            try:
                from .actions import handle_add
                result = handle_add(payload)
                self._send(200, json.dumps(result), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}), "application/json")
            return
        self._send(404, "not found")


class _Server(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_server(host=HOST, port=PORT, open_browser=False):
    with _Server((host, port), Handler) as httpd:
        url = f"http://{host}:{port}/"
        print(f"\n  🌐 Mimi Web: {url}")
        print(f"  Press Ctrl+C to stop.\n")
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Web server stopped.")


def main():
    from ..ui import BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW
    from ..ui import c, clear, header, pause
    clear()
    header("🌐 WEB DASHBOARD", "Browser-based Mimi")
    print(f"\n  Starting on http://{HOST}:{PORT}/")
    print(f"  Open in your phone browser\n")
    print("  1. Start now")
    print("  2. Start + open browser")
    print("  0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "0":
        return
    if ch == "1":
        run_server(open_browser=False)
    elif ch == "2":
        run_server(open_browser=True)
    else:
        return


if __name__ == "__main__":
    main()

run = main
