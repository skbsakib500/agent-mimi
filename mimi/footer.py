"""Bottom status bar: time + life score."""
import os
from datetime import datetime, timedelta, timezone
from .database import fetch_one
from .term import cols
from .xp import level_info

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; GR="\033[92m"; YL="\033[93m"; RD="\033[91m"

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = timezone(timedelta(hours=6))

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R

def _life_score():
    try:
        g = fetch_one("SELECT COALESCE(AVG(progress),0) AS a FROM goals WHERE status='active'")
        m = fetch_one("SELECT COALESCE(AVG(progress),0) AS a FROM missions WHERE status='active'")
        s = fetch_one("""SELECT COALESCE(SUM(duration_minutes),0)/60.0 AS h
                         FROM study_sessions WHERE study_date>=date('now','-6 days')""")
        t = fetch_one("SELECT COUNT(*) AS n FROM tasks")["n"]
        d = fetch_one("SELECT COUNT(*) AS n FROM tasks WHERE status='completed'")["n"]
        gp = float(g["a"] or 0); mp = float(m["a"] or 0)
        sh = min(100.0, float(s["h"] or 0) / 7.0 * 100.0)
        tr = (d / t * 100.0) if t else 0.0
        return round(gp*0.35 + mp*0.35 + sh*0.20 + tr*0.10, 1)
    except Exception:
        return 0.0

def render(width=None):
    width = width or cols()
    now = datetime.now(TZ)
    t = now.strftime("%H:%M:%S")
    d = now.strftime("%a %d %b")
    score = _life_score()
    if score >= 70: sc = GR
    elif score >= 40: sc = YL
    else: sc = RD

    try:
        lv = level_info()
        lv_str = f"Lv{lv['level']}"
    except Exception:
        lv_str = "Lv1"
    left = f" {d}  {t}  {lv_str} "
    right = f" Life {score:.0f}/100 "
    gap = max(1, width - len(left) - len(right) - 2)
    line = c("─" * width, D + CY)
    mid = c(left, B + CY) + " " * gap + c(right, B + sc)
    return line, " " + mid

def show(width=None):
    l1, l2 = render(width)
    print(l1)
    print(l2)
