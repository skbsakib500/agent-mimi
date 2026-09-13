"""Google OAuth device flow + token management."""
import time, json
from .api_manager import get as get_key, set_key
from .api_http import post_json, get_json
from .database import fetch_one, execute

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL       = "https://oauth2.googleapis.com/token"

SCOPES = " ".join([
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/gmail.readonly",
])


def _ensure():
    from .database import db
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS google_tokens (
                id INTEGER PRIMARY KEY CHECK (id=1),
                access_token TEXT,
                refresh_token TEXT,
                expires_at INTEGER,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def has_client():
    return bool(get_key("google_client_id") and get_key("google_client_secret"))


def has_token():
    _ensure()
    r = fetch_one("SELECT refresh_token FROM google_tokens WHERE id=1")
    return bool(r and r["refresh_token"])


def _save_tokens(access, refresh, expires_in):
    _ensure()
    exp = int(time.time()) + int(expires_in) - 60
    execute("""INSERT INTO google_tokens
               (id, access_token, refresh_token, expires_at)
               VALUES (1, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               access_token=excluded.access_token,
               refresh_token=COALESCE(excluded.refresh_token, google_tokens.refresh_token),
               expires_at=excluded.expires_at,
               updated_at=CURRENT_TIMESTAMP""",
            (access, refresh, exp))


def get_access_token():
    """Return valid access token, refreshing if needed."""
    if not has_token():
        return None
    _ensure()
    r = fetch_one("SELECT access_token, refresh_token, expires_at FROM google_tokens WHERE id=1")
    if not r:
        return None
    if r["expires_at"] and r["expires_at"] > int(time.time()):
        return r["access_token"]
    # refresh
    cid = get_key("google_client_id")
    csec = get_key("google_client_secret")
    if not cid or not csec or not r["refresh_token"]:
        return None
    out = post_json(TOKEN_URL, {
        "client_id": cid,
        "client_secret": csec,
        "refresh_token": r["refresh_token"],
        "grant_type": "refresh_token",
    })
    if "_error" in out or "access_token" not in out:
        return None
    _save_tokens(out["access_token"], None, out.get("expires_in", 3600))
    return out["access_token"]


def login_flow(ui_pause=None):
    """Interactive device flow login."""
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause)
    clear()
    header("🔐 GOOGLE LOGIN", "Device flow")
    if not has_client():
        print(c("\n  Missing google_client_id or google_client_secret.", RED))
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Enable Calendar + Tasks + Gmail APIs")
        print("  3. OAuth consent screen -> External -> add yourself as test user")
        print("  4. Credentials -> Create -> 'TVs and Limited Input devices'")
        print("  5. Add client_id + client_secret in API Keys menu")
        if ui_pause: ui_pause()
        return False

    cid = get_key("google_client_id")
    out = post_json(DEVICE_CODE_URL, {"client_id": cid, "scope": SCOPES})
    if "_error" in out or "device_code" not in out:
        print(c(f"\n  Device code request failed: {out.get('_error','unknown')}", RED))
        if ui_pause: ui_pause()
        return False

    print()
    print(c(f"  1. Visit: {out['verification_url']}", BOLD + CYAN))
    print(c(f"  2. Enter code: {out['user_code']}", BOLD + GREEN))
    print(c(f"  (expires in {out['expires_in']}s)", DIM + WHITE))
    print()
    input(c("  Press Enter once done, then we poll...", DIM + WHITE))

    interval = out.get("interval", 5)
    device_code = out["device_code"]
    csec = get_key("google_client_secret")
    deadline = time.time() + int(out.get("expires_in", 300))

    print(c("  Waiting for you to approve...", DIM + WHITE))
    while time.time() < deadline:
        time.sleep(interval)
        tok = post_json(TOKEN_URL, {
            "client_id": cid,
            "client_secret": csec,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        if "access_token" in tok:
            _save_tokens(tok["access_token"], tok.get("refresh_token"),
                         tok.get("expires_in", 3600))
            print(c("\n  ✅ Login successful.", GREEN))
            if ui_pause: ui_pause()
            return True
        err = tok.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 2; continue
        print(c(f"\n  X {err or tok.get('_error','unknown')}", RED))
        if ui_pause: ui_pause()
        return False
    print(c("\n  Timed out.", RED))
    if ui_pause: ui_pause()
    return False


def logout():
    _ensure()
    execute("DELETE FROM google_tokens WHERE id=1")


def call_api(url, params=None):
    """GET an authenticated Google API."""
    tok = get_access_token()
    if not tok:
        return {"_error": "not logged in"}
    headers = {"Authorization": f"Bearer {tok}"}
    return get_json(url, params=params, headers=headers)


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    while True:
        clear()
        header("🔐 GOOGLE", "OAuth device flow")
        cid = "OK" if get_key("google_client_id") else "MISSING"
        csec = "OK" if get_key("google_client_secret") else "MISSING"
        logged = "OK" if has_token() else "NO"
        print(f"\n  Client ID:     {cid}")
        print(f"  Client Secret: {csec}")
        print(f"  Logged in:     {logged}")
        print()
        print("  1. Login   2. Logout   0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "0": break
        if ch == "1":
            login_flow(ui_pause=pause)
        elif ch == "2":
            logout()
            print(c("  Logged out.", GREEN))
            pause()

run = main
