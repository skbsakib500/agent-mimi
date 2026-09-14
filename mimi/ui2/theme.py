"""Nova UI - theme engine with truecolor support."""
import os

# ─── truecolor detection ───
_TRUE = os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")
_NO_COLOR = os.environ.get("MIMI_NO_COLOR") == "1"
_FORCE_256 = os.environ.get("MIMI_256") == "1"


def has_truecolor():
    return _TRUE and not _NO_COLOR


# ─── low-level escape emitters ───
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
I = "\033[3m"
U = "\033[4m"


def fg256(n):
    return f"\033[38;5;{n}m"


def bg256(n):
    return f"\033[48;5;{n}m"


def fg_rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def bg_rgb(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"


def hex_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def c(text, *codes):
    if _NO_COLOR:
        return str(text)
    return "".join(codes) + str(text) + R


# ─── theme definitions ───
# Each theme = dict of semantic color keys -> hex or 256 code.

THEMES = {
    "aurora": {
        # deep navy + magenta + cyan — like a real aurora
        "bg":       "#0a0e1a",
        "surface":  "#111827",
        "surface2": "#1a2233",
        "border":   "#1f2937",
        "text":     "#e5e7eb",
        "muted":    "#9ca3af",
        "dim":      "#4b5563",
        "primary":  "#c084fc",   # violet
        "accent":   "#22d3ee",   # cyan
        "success":  "#4ade80",
        "warning":  "#fbbf24",
        "danger":   "#f87171",
        "info":     "#60a5fa",
    },
    "nebula": {
        "bg":       "#0d0616",
        "surface":  "#1a0f2e",
        "surface2": "#2a1a44",
        "border":   "#3a2854",
        "text":     "#f5f3ff",
        "muted":    "#a78bfa",
        "dim":      "#6b7280",
        "primary":  "#ec4899",
        "accent":   "#8b5cf6",
        "success":  "#10b981",
        "warning":  "#f59e0b",
        "danger":   "#ef4444",
        "info":     "#06b6d4",
    },
    "carbon": {
        "bg":       "#0f0f0f",
        "surface":  "#1a1a1a",
        "surface2": "#262626",
        "border":   "#333333",
        "text":     "#fafafa",
        "muted":    "#a3a3a3",
        "dim":      "#525252",
        "primary":  "#fbbf24",
        "accent":   "#f87171",
        "success":  "#4ade80",
        "warning":  "#fb923c",
        "danger":   "#dc2626",
        "info":     "#60a5fa",
    },
    "forest": {
        "bg":       "#0a1410",
        "surface":  "#132a1f",
        "surface2": "#1c3a2b",
        "border":   "#2a4a38",
        "text":     "#ecfdf5",
        "muted":    "#86efac",
        "dim":      "#4b5563",
        "primary":  "#22c55e",
        "accent":   "#14b8a6",
        "success":  "#84cc16",
        "warning":  "#eab308",
        "danger":   "#ef4444",
        "info":     "#0ea5e9",
    },
    "midnight": {
        "bg":       "#000000",
        "surface":  "#0a0a0a",
        "surface2": "#141414",
        "border":   "#1f1f1f",
        "text":     "#e0e0e0",
        "muted":    "#888888",
        "dim":      "#444444",
        "primary":  "#00d4ff",
        "accent":   "#ff00ea",
        "success":  "#00ff88",
        "warning":  "#ffcc00",
        "danger":   "#ff0044",
        "info":     "#0088ff",
    },
    "sunset": {
        "bg":       "#1a0e05",
        "surface":  "#2d1810",
        "surface2": "#3f2418",
        "border":   "#5a3425",
        "text":     "#fef3c7",
        "muted":    "#fbbf24",
        "dim":      "#78350f",
        "primary":  "#f97316",
        "accent":   "#ef4444",
        "success":  "#84cc16",
        "warning":  "#fbbf24",
        "danger":   "#dc2626",
        "info":     "#0ea5e9",
    },
    "ocean": {
        "bg":       "#04121a",
        "surface":  "#0a2130",
        "surface2": "#0f3044",
        "border":   "#1a4459",
        "text":     "#e0f2fe",
        "muted":    "#7dd3fc",
        "dim":      "#0c4a6e",
        "primary":  "#06b6d4",
        "accent":   "#0891b2",
        "success":  "#10b981",
        "warning":  "#f59e0b",
        "danger":   "#ef4444",
        "info":     "#3b82f6",
    },
    "royal": {
        "bg":       "#0b0620",
        "surface":  "#1a0f3d",
        "surface2": "#281a5c",
        "border":   "#3d2980",
        "text":     "#ede9fe",
        "muted":    "#c4b5fd",
        "dim":      "#5b21b6",
        "primary":  "#a78bfa",
        "accent":   "#f0abfc",
        "success":  "#34d399",
        "warning":  "#fbbf24",
        "danger":   "#f87171",
        "info":     "#60a5fa",
    },
}

DEFAULT = "aurora"
_CURRENT = os.environ.get("MIMI_THEME", DEFAULT)


def current_name():
    return _CURRENT


def get(name=None):
    """Return theme dict for name (or current)."""
    return THEMES.get(name or _CURRENT, THEMES[DEFAULT])


def set_theme(name):
    global _CURRENT
    if name in THEMES:
        _CURRENT = name
        try:
            _save_to_db(name)
        except Exception:
            pass
        return True
    return False


def cycle():
    keys = list(THEMES.keys())
    idx = keys.index(_CURRENT) if _CURRENT in keys else 0
    nxt = keys[(idx + 1) % len(keys)]
    set_theme(nxt)
    return nxt


def _save_to_db(name):
    from ..database import execute
    execute("""INSERT INTO system_config (key, value, description)
               VALUES ('theme', ?, 'UI theme')
               ON CONFLICT(key) DO UPDATE SET
               value=excluded.value,
               updated_at=CURRENT_TIMESTAMP""", (name,))


def load_from_db():
    global _CURRENT
    try:
        from ..database import fetch_one
        r = fetch_one("SELECT value FROM system_config WHERE key='theme'")
        if r and r["value"] in THEMES:
            _CURRENT = r["value"]
    except Exception:
        pass
    return _CURRENT


# ─── semantic color helpers ───
def col(key, name=None):
    """Return ANSI escape for a semantic color key."""
    t = get(name)
    hx = t.get(key)
    if not hx:
        return ""
    if has_truecolor():
        r, g, b = hex_rgb(hx)
        return fg_rgb(r, g, b)
    return fg256(hex_to_256(hx))


def bcol(key, name=None):
    t = get(name)
    hx = t.get(key)
    if not hx:
        return ""
    if has_truecolor():
        r, g, b = hex_rgb(hx)
        return bg_rgb(r, g, b)
    return bg256(hex_to_256(hx))


def hex_to_256(hx):
    r, g, b = hex_rgb(hx)
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return 232 + (r - 8) // 10
    ri = r // 43 if r < 48 else 16 + (r - 35) // 40
    gi = g // 43 if g < 48 else 16 + (g - 35) // 40
    bi = b // 43 if b < 48 else 16 + (b - 35) // 40
    return 16 + 36 * ri + 6 * gi + bi


# Auto-load saved theme
try:
    load_from_db()
except Exception:
    pass
