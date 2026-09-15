"""Location awareness - consent-based, on-device only.

Safety:
  - All reads audited (signed chain)
  - Data stored ONLY in local SQLite
  - Never uploaded to any external service
  - Only owner-identified actions trigger reads
"""
import json
import subprocess
import shutil
from datetime import datetime
from .database import execute, fetch_one, fetch_all
from .guardian import audit


def available():
    return shutil.which("termux-location") is not None


def ensure_tables():
    execute("""CREATE TABLE IF NOT EXISTS location_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        latitude REAL,
        longitude REAL,
        accuracy REAL,
        altitude REAL,
        provider TEXT,
        label TEXT,
        notes TEXT)""")
    execute("""CREATE TABLE IF NOT EXISTS geofences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius_m INTEGER DEFAULT 200,
        notify_enter INTEGER DEFAULT 1,
        notify_exit INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def get_current(provider="network", timeout=15):
    """Read one location fix. Returns dict or None."""
    if not available():
        return None
    try:
        r = subprocess.run(
            ["termux-location", "-p", provider],
            capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            audit.log("location_denied", actor="location",
                      payload={"reason": r.stderr[:100]})
            return None
        data = json.loads(r.stdout)
        loc = {
            "latitude":  data.get("latitude"),
            "longitude": data.get("longitude"),
            "accuracy":  data.get("accuracy"),
            "altitude":  data.get("altitude"),
            "provider":  data.get("provider", provider),
        }
        audit.log("location_read", actor="location",
                  payload={"lat": loc["latitude"],
                           "lon": loc["longitude"],
                           "provider": loc["provider"]})
        return loc
    except Exception as e:
        audit.log("location_error", actor="location",
                  payload={"error": f"{type(e).__name__}: {e}"})
        return None


def log_current(label=None, notes=None):
    """Read and store one location in local DB."""
    loc = get_current()
    if not loc:
        return None
    execute(
        """INSERT INTO location_log
           (latitude, longitude, accuracy, altitude, provider, label, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (loc["latitude"], loc["longitude"], loc["accuracy"],
         loc["altitude"], loc["provider"], label, notes))
    return loc


def recent(limit=20):
    ensure_tables()
    rows = fetch_all(
        """SELECT * FROM location_log
           ORDER BY id DESC LIMIT ?""", (limit,))
    return [dict(r) for r in rows]


def _haversine(lat1, lon1, lat2, lon2):
    """Distance between two coords in meters."""
    import math
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp/2)**2
         + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


def distance_to(lat, lon):
    """Distance from current location to a point."""
    cur = get_current()
    if not cur:
        return None
    return _haversine(cur["latitude"], cur["longitude"], lat, lon)


def add_geofence(name, lat, lon, radius=200,
                  notify_enter=True, notify_exit=True):
    ensure_tables()
    try:
        execute(
            """INSERT INTO geofences
               (name, latitude, longitude, radius_m, notify_enter, notify_exit)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, float(lat), float(lon), int(radius),
             1 if notify_enter else 0, 1 if notify_exit else 0))
        audit.log("geofence_added", actor="location",
                  payload={"name": name, "radius": radius})
        return {"ok": True, "name": name}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def add_geofence_from_current(name, radius=200):
    loc = get_current()
    if not loc:
        return {"ok": False, "error": "no location"}
    return add_geofence(name, loc["latitude"], loc["longitude"], radius)


def list_geofences():
    ensure_tables()
    rows = fetch_all("SELECT * FROM geofences ORDER BY name")
    return [dict(r) for r in rows]


def delete_geofence(name):
    ensure_tables()
    execute("DELETE FROM geofences WHERE name=?", (name,))
    audit.log("geofence_deleted", actor="location", payload={"name": name})
    return {"ok": True}


def check_geofences():
    """Read current location, compare against all fences.
    Sends notification on enter/exit transitions. Returns list of events."""
    loc = get_current()
    if not loc:
        return []
    events = []
    for fence in list_geofences():
        dist = _haversine(loc["latitude"], loc["longitude"],
                           fence["latitude"], fence["longitude"])
        inside = dist <= fence["radius_m"]
        # Check last state from local db (key in system_config)
        key = f"geofence_{fence['name']}_inside"
        last_row = fetch_one(
            "SELECT value FROM system_config WHERE key=?", (key,))
        last = bool(int(last_row["value"])) if last_row else False

        if inside and not last and fence["notify_enter"]:
            events.append(("enter", fence["name"]))
            _notify(f"📍 Arrived: {fence['name']}",
                    f"Within {int(dist)}m of {fence['name']}")
        elif not inside and last and fence["notify_exit"]:
            events.append(("exit", fence["name"]))
            _notify(f"🚶 Left: {fence['name']}",
                    f"{int(dist)}m from {fence['name']}")

        # Save current state
        execute("""INSERT INTO system_config (key, value)
                   VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                   value=excluded.value,
                   updated_at=CURRENT_TIMESTAMP""",
                (key, "1" if inside else "0"))
    return events


def _notify(title, content):
    try:
        from . import notify
        notify.send(title, content, priority="default")
    except Exception:
        pass
