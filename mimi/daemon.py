"""Mimi Daemon - 24/7 background scheduler.

Runs on Termux:Boot. Wakes every minute, checks:
  - scheduled notifications (morning, noon, evening)
  - automation cycle (every 30 min)
  - overdue task alerts (hourly)
  - health warnings (every 2h)
  - git sync (every 15 min)

State persisted to ~/.mimi/daemon_state.json.
"""
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from .guardian import audit

STATE_DIR = Path.home() / ".mimi"
STATE_FILE = STATE_DIR / "daemon_state.json"
LOG_FILE = STATE_DIR / "daemon.log"
PID_FILE = STATE_DIR / "daemon.pid"

RUNNING = True


def _now():
    return datetime.now()


def _load_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last": {}}


def _save_state(s):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))


def _log(msg):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="", flush=True)


def _due(state, key, every_seconds):
    last = state["last"].get(key)
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
    except Exception:
        return True
    return (_now() - last_dt).total_seconds() >= every_seconds


def _mark(state, key):
    state["last"][key] = _now().isoformat(timespec="seconds")
    _save_state(state)


def _notify(title, content, priority="default", sound=False, vibrate=False):
    """Push to phone via Termux:API."""
    try:
        from . import notify
        return notify.send(title, content, priority=priority,
                            sound=sound, vibrate=vibrate)
    except Exception as e:
        _log(f"notify error: {e}")
        return False


def _say(text):
    """Speak via Termux TTS."""
    try:
        from . import speak
        if speak.available():
            speak.speak(text, lang="bn")
    except Exception:
        pass


# ─── scheduled tasks ───

def job_morning_brief():
    try:
        from .briefing import gather, compose_text
        d = gather()
        text = compose_text(d)
        _notify("☀️ Mimi Morning Brief", text[:180],
                priority="high", sound=True, vibrate=True)
        _log("morning brief pushed")
        audit.log("daemon_brief", actor="daemon",
                  payload={"kind": "morning"})
    except Exception as e:
        _log(f"morning brief error: {e}")


def job_evening_review():
    try:
        from .database import fetch_one
        def q(sql):
            try:
                r = fetch_one(sql)
                return r[0] if r else 0
            except Exception:
                return 0
        tasks_c = q("SELECT COUNT(*) FROM tasks WHERE status='completed' "
                    "AND completed_at >= date('now')")
        study = q("""SELECT COALESCE(SUM(duration_minutes),0)
                     FROM study_sessions WHERE study_date=date('now')""")
        journal = q("SELECT COUNT(*) FROM journal WHERE entry_date=date('now')")
        text = (f"Today: {tasks_c} tasks done, {study} min studied, "
                f"{journal} journal entries.")
        _notify("🌙 Mimi Evening Review", text,
                priority="default")
        _log("evening review pushed")
    except Exception as e:
        _log(f"evening review error: {e}")


def job_overdue_check():
    try:
        from .database import fetch_one
        r = fetch_one("""SELECT COUNT(*) FROM tasks
                         WHERE status IN ('pending','in_progress')
                         AND due_date IS NOT NULL
                         AND due_date < date('now')""")
        n = r[0] if r else 0
        if n:
            _notify("⚠️ Overdue tasks", f"{n} task(s) past due",
                    priority="high", sound=True, vibrate=True)
            _log(f"overdue alert: {n}")
    except Exception as e:
        _log(f"overdue error: {e}")


def job_health_check():
    try:
        from .health.diagnostic import run_all
        r = run_all()
        if r["fail"] > 0:
            _notify("🩺 Health issue",
                    f"{r['fail']} check(s) failed",
                    priority="high", sound=True, vibrate=True)
            _log(f"health fail: {r['fail']}")
    except Exception as e:
        _log(f"health error: {e}")


def job_automation_cycle():
    try:
        from .scheduler import run_cycle
        r = run_cycle(push=True)
        _log(f"automation: {len(r['rules'])} rules, {r['created']} new")
    except Exception as e:
        _log(f"automation error: {e}")


def job_location():
    try:
        from .location import check_geofences, available
        if not available():
            return
        events = check_geofences()
        for etype, name in events:
            _log(f"geofence {etype}: {name}")
            audit.log("geofence_event", actor="daemon",
                      payload={"kind": etype, "name": name})
    except Exception as e:
        _log(f"location error: {e}")


def job_sync():
    try:
        from .sync import is_repo, pull
        if not is_repo():
            return
        ok, msg = pull()
        if ok:
            _log("sync pull ok")
    except Exception as e:
        _log(f"sync error: {e}")


# Jobs and their intervals (in seconds)
JOBS = [
    # (key, interval, job_fn, hours_only)
    ("morning",      86400, job_morning_brief,     (7, 8)),      # 7-8 AM once daily
    ("evening",      86400, job_evening_review,    (21, 22)),    # 9-10 PM once daily
    ("overdue",      3600,  job_overdue_check,     None),        # hourly
    ("health",       7200,  job_health_check,      None),        # every 2h
    ("automation",   1800,  job_automation_cycle,  None),        # every 30m
    ("sync",         900,   job_sync,              None),        # every 15m
    ("location",     600,   job_location,          None),        # every 10m
]


def _should_run_now(job_hours, now):
    if job_hours is None:
        return True
    h = now.hour
    lo, hi = job_hours
    return lo <= h < hi


def _stop(sig, frame):
    global RUNNING
    RUNNING = False
    _log("signal received, shutting down")


def run_forever():
    global RUNNING
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

    # Keep phone awake
    try:
        import subprocess
        subprocess.Popen(["termux-wake-lock"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except Exception:
        pass

    _log(f"daemon started (pid={os.getpid()})")
    audit.log("daemon_start", actor="daemon",
              payload={"pid": os.getpid()})

    state = _load_state()

    while RUNNING:
        now = _now()
        for key, interval, fn, hours_only in JOBS:
            if not _should_run_now(hours_only, now):
                continue
            if _due(state, key, interval):
                try:
                    fn()
                    _mark(state, key)
                except Exception as e:
                    _log(f"job {key} error: {e}")

        # Sleep 30s between checks
        for _ in range(30):
            if not RUNNING:
                break
            time.sleep(1)

    # Cleanup
    try:
        import subprocess
        subprocess.Popen(["termux-wake-unlock"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        PID_FILE.unlink()
    except Exception:
        pass
    _log("daemon stopped")


def stop_daemon():
    if not PID_FILE.exists():
        return False, "not running"
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        return True, f"sent SIGTERM to {pid}"
    except Exception as e:
        return False, str(e)


def status():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)  # check alive
            return {"running": True, "pid": pid}
        except Exception:
            return {"running": False, "stale_pid": True}
    return {"running": False}


def main():
    import sys
    args = sys.argv[1:]
    cmd = args[0] if args else "run"

    if cmd == "run":
        run_forever()
        return 0
    if cmd == "start":
        st = status()
        if st["running"]:
            print(f"  already running (pid {st['pid']})")
            return 0
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, "-m", "mimi.daemon", "run"],
            stdout=open(LOG_FILE, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True)
        print(f"  ✓ daemon started (pid {proc.pid})")
        return 0
    if cmd == "stop":
        ok, msg = stop_daemon()
        print(f"  {'✓' if ok else 'X'} {msg}")
        return 0 if ok else 1
    if cmd == "status":
        st = status()
        if st["running"]:
            print(f"  ✓ running (pid {st['pid']})")
        else:
            print(f"  · not running")
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text().splitlines()[-5:]
            print()
            print("  recent log:")
            for l in lines:
                print(f"    {l}")
        return 0
    if cmd == "test":
        print("  running all jobs once…")
        for key, interval, fn, hours in JOBS:
            try:
                fn()
                print(f"  ✓ {key}")
            except Exception as e:
                print(f"  X {key}: {e}")
        return 0
    print("usage: python -m mimi.daemon [run|start|stop|status|test]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
