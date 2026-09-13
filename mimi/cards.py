"""Colored category cards, adaptive width."""
import os
from .term import card_w

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; BL="\033[94m"; GR="\033[92m"
YL="\033[93m"; MG="\033[95m"; WH="\033[97m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R


STYLES_BN = {
    "1": ("আদেশ",       "🎯", BL),
    "2": ("বৃদ্ধি",      "📚", GR),
    "3": ("অর্থ",        "💰", YL),
    "4": ("জীবন",        "🧬", CY),
    "5": ("মন",          "🧠", MG),
    "6": ("বুদ্ধিমত্তা", "📊", WH),
}

STYLES = {
    "1": ("COMMAND",      "🎯", BL),
    "2": ("GROWTH",       "📚", GR),
    "3": ("FINANCE",      "💰", YL),
    "4": ("LIFE",         "🧬", CY),
    "5": ("MIND",         "🧠", MG),
    "6": ("INTELLIGENCE", "📊", WH),
}

def _truncate(s, n):
    return s if len(s) <= n else s[:n-1] + "…"

def _pad(s, n):
    return s + " " * max(0, n - len(s))

def render(categories, width=None):
    width = width or card_w()
    inner = width - 4
    lines = []
    try:
        from . import lang
        use_bn = lang._current() == "bn"
    except Exception:
        use_bn = False
    table = STYLES_BN if use_bn else STYLES
    for key in sorted(categories.keys()):
        title, icon, color = table.get(key, ("?", "?", WH))
        head = f"[{key}] {icon} {title}"
        names = " · ".join(n for n, _ in categories[key]["items"])
        lines.append("  " + c("╭" + "─" * (width - 2) + "╮", color))
        lines.append("  " + c("│", color) + " "
                     + c(_pad(_truncate(head, inner), inner), B + color)
                     + " " + c("│", color))
        lines.append("  " + c("│", color) + " "
                     + c(_pad(_truncate(names, inner), inner), D + WH)
                     + " " + c("│", color))
        lines.append("  " + c("╰" + "─" * (width - 2) + "╯", color))
        lines.append("")
    return lines

def show(categories, width=None):
    for ln in render(categories, width):
        print(ln)

def show_two_columns(categories, width=None):
    """Two cards side by side on wide terminals."""
    width = width or card_w()
    if width < 88:
        show(categories, width); return
    half = (width - 4) // 2
    inner = half - 4
    keys = sorted(categories.keys())
    for i in range(0, len(keys), 2):
        left_key = keys[i]
        right_key = keys[i+1] if i+1 < len(keys) else None
        for row in range(4):
            lline = _row_for(left_key, categories, row, half, inner)
            rline = _row_for(right_key, categories, row, half, inner) if right_key else ""
            print("  " + lline + "  " + rline)
        print()

def _row_for(key, categories, row, half, inner):
    if key is None:
        return " " * (half)
    title, icon, color = STYLES.get(key, ("?", "?", WH))
    head = f"[{key}] {icon} {title}"
    names = " · ".join(n for n, _ in categories[key]["items"])
    if row == 0:
        return c("╭" + "─" * (half - 2) + "╮", color)
    if row == 1:
        return c("│", color) + " " + c(_pad(_truncate(head, inner), inner), B + color) + " " + c("│", color)
    if row == 2:
        return c("│", color) + " " + c(_pad(_truncate(names, inner), inner), D + WH) + " " + c("│", color)
    return c("╰" + "─" * (half - 2) + "╯", color)
