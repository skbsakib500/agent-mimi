"""Agent Mimi - insights."""
from datetime import datetime, date, timedelta
from .database import fetch_all, fetch_one
from .ui import GREEN, RED, YELLOW, c, clear, header, pause, section


def streaks():
    rows = fetch_all("""SELECT DISTINCT study_date FROM study_sessions
                        ORDER BY study_date DESC LIMIT 60""")
    if not rows:
        return 0
    dates = [r["study_date"] for r in rows]
    streak = 0
    today = date.today()
    for i, d in enumerate(dates):
        try:
            dd = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            continue
        expected = today - timedelta(days=i)
        if dd == expected:
            streak += 1
        else:
            break
    return streak


def best_hour():
    rows = fetch_all("""SELECT substr(created_at,12,2) AS h,
                        SUM(duration_minutes) AS m
                        FROM study_sessions GROUP BY h
                        ORDER BY m DESC LIMIT 1""")
    if not rows or not rows[0]["h"]:
        return None
    return rows[0]["h"] + ":00"


def top_subject():
    rows = fetch_all("""SELECT subject, SUM(duration_minutes) AS m
                        FROM study_sessions GROUP BY subject
                        ORDER BY m DESC LIMIT 1""")
    if not rows:
        return None
    return rows[0]["subject"], rows[0]["m"] / 60.0


def week_delta():
    this_w = fetch_one("""SELECT COALESCE(SUM(duration_minutes),0) AS m
                          FROM study_sessions
                          WHERE study_date >= date('now','-6 days')""")["m"] / 60.0
    last_w = fetch_one("""SELECT COALESCE(SUM(duration_minutes),0) AS m
                          FROM study_sessions
                          WHERE study_date BETWEEN date('now','-13 days')
                          AND date('now','-7 days')""")["m"] / 60.0
    return {"this": this_w, "last": last_w, "delta": this_w - last_w}


def main():
    clear()
    header("INSIGHTS", "Pattern detection")
    section("STREAKS", "[*]")
    st = streaks()
    if st:
        print(c(f"  {st}-day study streak.", GREEN))
    else:
        print(c("  No active streak.", YELLOW))

    section("BEST TIME", "[~]")
    h = best_hour()
    print(f"  Peak study hour: {h}" if h else "  Not enough data.")

    section("TOP SUBJECT", "[+]")
    ts = top_subject()
    if ts:
        print(f"  {ts[0]} - {ts[1]:.1f}h logged.")
    else:
        print("  No subject data.")

    section("WEEK VS WEEK", "[/]")
    wd = week_delta()
    arrow = "UP" if wd["delta"] > 0 else "DOWN" if wd["delta"] < 0 else "FLAT"
    color = GREEN if wd["delta"] > 0 else RED if wd["delta"] < 0 else YELLOW
    print(f"  This: {wd['this']:.1f}h   Last: {wd['last']:.1f}h")
    print(c(f"  {arrow} {abs(wd['delta']):.1f}h", color))
    pause()


run = main
