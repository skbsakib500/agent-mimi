"""Weekly HTML report generator."""
from datetime import datetime, timedelta
from pathlib import Path
from .database import DB_PATH, db
from .ui import GREEN, RED, c, clear, header, pause

def _dir():
    d = Path(DB_PATH).parent.parent / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _q(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchone()
    except Exception:
        return None

def _rows(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []

def build_html():
    with db() as conn:
        study = _q(conn, """SELECT COALESCE(SUM(duration_minutes),0) AS m,
                            COUNT(*) AS n FROM study_sessions
                            WHERE study_date >= date('now','-6 days')""")
        goals = _q(conn, """SELECT COUNT(*) AS t,
                            COALESCE(AVG(progress),0) AS a FROM goals""")
        missions = _q(conn, """SELECT COUNT(*) AS t,
                              COALESCE(AVG(progress),0) AS a FROM missions""")
        tasks = _q(conn, """SELECT COUNT(*) AS t,
                            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS d
                            FROM tasks""")
        fin = _q(conn, """SELECT
            COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) AS inc,
            COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) AS exp
            FROM finance""")
        sleep = _q(conn, """SELECT COALESCE(AVG(duration_minutes),0) AS m
                            FROM sleep WHERE sleep_date >= date('now','-6 days')""")
        daily = _rows(conn, """SELECT study_date AS d,
                              COALESCE(SUM(duration_minutes),0) AS m
                              FROM study_sessions
                              WHERE study_date >= date('now','-6 days')
                              GROUP BY study_date ORDER BY study_date""")

    sh = float(study["m"] or 0) / 60.0 if study else 0
    sn = study["n"] if study else 0
    gt = goals["t"] if goals else 0
    ga = float(goals["a"] or 0) if goals else 0
    mt = missions["t"] if missions else 0
    ma = float(missions["a"] or 0) if missions else 0
    tt = tasks["t"] if tasks else 0
    td = tasks["d"] if tasks else 0
    inc = float(fin["inc"] or 0) if fin else 0
    exp = float(fin["exp"] or 0) if fin else 0
    bal = inc - exp
    sm = float(sleep["m"] or 0) if sleep else 0
    score = round(ga*0.35 + ma*0.35 + min(100, sh/7*100)*0.20
                  + ((td/tt*100) if tt else 0)*0.10, 1)

    bars = ""
    mx = max([float(r["m"] or 0) for r in daily] + [1.0])
    for r in daily:
        v = float(r["m"] or 0)
        pct = int(v / mx * 100)
        bars += (f'<div class="bar"><span class="lbl">{r["d"]}</span>'
                 f'<div class="track"><div class="fill" style="width:{pct}%"></div></div>'
                 f'<span class="val">{v/60:.1f}h</span></div>')

    gen = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Mimi Weekly Report</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e5e7eb;margin:0;padding:32px}}
.wrap{{max-width:760px;margin:0 auto}}
h1{{color:#c084fc;margin:0 0 4px}} .sub{{color:#9ca3af;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:20px 0}}
.card{{background:#181b22;border:1px solid #262b35;border-radius:12px;padding:16px}}
.card h3{{margin:0 0 8px;font-size:13px;color:#9ca3af;font-weight:500;letter-spacing:.5px;text-transform:uppercase}}
.card .v{{font-size:24px;font-weight:600;color:#e5e7eb}}
.card .v.g{{color:#4ade80}} .card .v.r{{color:#f87171}} .card .v.y{{color:#fbbf24}}
.score{{font-size:44px;font-weight:700;color:#c084fc;text-align:center;margin:16px 0}}
.bar{{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}}
.bar .lbl{{width:80px;color:#9ca3af}}
.bar .track{{flex:1;height:10px;background:#262b35;border-radius:5px;overflow:hidden}}
.bar .fill{{height:100%;background:linear-gradient(90deg,#a855f7,#22d3ee)}}
.bar .val{{width:60px;text-align:right;color:#e5e7eb}}
.foot{{margin-top:32px;color:#6b7280;font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>Agent Mimi</h1>
<div class="sub">Weekly Report · generated {gen}</div>
<div class="score">Life Score: {score}/100</div>
<div class="grid">
  <div class="card"><h3>Study</h3><div class="v">{sh:.1f}h</div>
    <div class="sub">{sn} sessions · 7 days</div></div>
  <div class="card"><h3>Sleep avg</h3><div class="v">{sm/60:.1f}h</div></div>
  <div class="card"><h3>Goals</h3><div class="v">{gt} · {ga:.0f}%</div></div>
  <div class="card"><h3>Missions</h3><div class="v">{mt} · {ma:.0f}%</div></div>
  <div class="card"><h3>Tasks</h3><div class="v">{td}/{tt}</div></div>
  <div class="card"><h3>Balance</h3><div class="v {'g' if bal>=0 else 'r'}">{bal:,.0f}</div></div>
</div>
<h3 style="color:#9ca3af;margin-top:24px;font-size:13px;letter-spacing:.5px">STUDY · LAST 7 DAYS</h3>
{bars or '<div class="sub">No study sessions recorded.</div>'}
<div class="foot">Generated by Agent Mimi v2.1</div>
</div></body></html>"""

def generate():
    target = _dir() / f"mimi_report_{datetime.now():%Y%m%d_%H%M%S}.html"
    target.write_text(build_html(), encoding="utf-8")
    return target

def open_in_browser(path):
    import subprocess, shutil
    for cmd in (["termux-open", str(path)],
                ["xdg-open", str(path)],
                ["open", str(path)]):
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(cmd,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass
    return False

def main():
    clear()
    header("WEEKLY REPORT", "HTML snapshot")
    print("  1. Generate report")
    print("  2. Generate and open")
    print("  0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "0": return
    if ch in ("1", "2"):
        try:
            p = generate()
            print(c(f"\n  OK Saved: {p}", GREEN))
            if ch == "2":
                if open_in_browser(p):
                    print(c("  Opened in browser.", GREEN))
                else:
                    print(c("  (no opener found; open file manually)", RED))
        except Exception as e:
            print(c(f"\n  X {type(e).__name__}: {e}", RED))
    else:
        print(c("  X Invalid.", RED))
    pause()

run = main
