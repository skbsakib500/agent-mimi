"""Shared HTTP helper for all APIs."""
import json, urllib.request, urllib.error, urllib.parse

TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"

def get_json(url, params=None, headers=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return {"_error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


def post_json(url, payload, headers=None):
    data = json.dumps(payload).encode("utf-8")
    h = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return {"_error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}
