"""Charts: bars, sparklines, heatmap."""
import os
from datetime import date, timedelta
from .database import fetch_all

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; BL="\033[94m"; GR="\033[92m"
YL="\033[93m"; MG="\033[95m"; WH="\033[97m"; RD="\033[91m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R

def _pad(s, n):
    return s + " " * max(0, n - len(s))

def hbar(value, max_value, width=40, color=GR):
    try:
        value = float(value); max_value = max(1.0, float(max_value))
    except (TypeError, ValueError):
        value, max_value = 0.0, 1.0
    ratio = max(0.0, min(1.0, value / max_value))
    filled = int(round(width * ratio))
    return c("█" * filled, color) + c("░" * (width - filled), D + WH)

def weekly_study_bars(days=7, width=40):
    rows = fetch_all("""SELECT study_date,
                        COALESCE(SUM(duration_minutes),0) AS m
                        FROM study_sessions
                        WHERE study_date >= date('now',?)
                        GROUP BY study_date
                        ORDER BY study_date""", (f"-{days-1} days",))
    by_date = {r["study_date"]: float(r["m"] or 0) for r in rows}
    today = date.today()
    labels = []
    values = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        iso = d.isoformat()
        labels.append(d.strftime("%a")[:3])
        values.append(by_date.get(iso, 0.0))
    mx = max(values + [1.0])
    lines = []
    for lab, val in zip(labels, values):
        bar = hbar(val, mx, width=width, color=GR)
        lines.append(f"  {lab}  {bar}  {val/60:.1f}h")
    return lines, values

def sparkline(values, color=CY):
    chars = " ▁▂▃▄▅▆▇█"
    if not values:
        return ""
    mx = max(values) or 1
    out = []
    for v in values:
        idx = int((v / mx) * (len(chars) - 1))
        out.append(chars[idx])
    return c("".join(out), color)

def life_score_gauge(score, width=40):
    score = max(0.0, min(100.0, float(score)))
    if score >= 70: color = GR
    elif score >= 40: color = YL
    else: color = RD
    filled = int(round(width * score / 100))
    bar = c("█" * filled, color) + c("░" * (width - filled), D + WH)
    return bar

def habit_heatmap(table="study_sessions", date_col="study_date", days=90):
    rows = fetch_all(f"""SELECT {date_col} AS d, COUNT(*) AS n
                         FROM {table}
                         WHERE {date_col} >= date('now', ?)
                         GROUP BY {date_col}""", (f"-{days-1} days",))
    active = {r["d"]: int(r["n"]) for r in rows}
    today = date.today()
    grid = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        grid.append((d, active.get(d.isoformat(), 0)))
    # 7 rows (weekday) x N columns
    weeks = (days + 6) // 7
    start_wd = grid[0][0].weekday()
    cells = [["·"] * weeks for _ in range(7)]
    for idx, (d, n) in enumerate(grid):
        col = (idx + start_wd) // 7
        row = d.weekday()
        if n == 0: ch, col_c = "·", D + WH
        elif n == 1: ch, col_c = "░", GR
        elif n == 2: ch, col_c = "▒", GR
        else: ch, col_c = "█", B + GR
        cells[row][col] = c(ch, col_c)
    lines = []
    wd = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for r in range(7):
        lines.append(f"  {wd[r]}  " + "".join(cells[r]))
    return lines
