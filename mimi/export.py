"""Export to JSON/CSV."""
import json, csv
from datetime import datetime
from pathlib import Path
from .database import DB_PATH, db, get_tables
from .ui import GREEN, RED, c, clear, header, pause

def _dir():
    d = Path(DB_PATH).parent.parent / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d

def export_json():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = _dir() / f"mimi_export_{stamp}.json"
    data = {}
    with db() as conn:
        for t in get_tables():
            if t == "schema_version":
                continue
            try:
                rows = conn.execute(f"SELECT * FROM {t}").fetchall()
                data[t] = [dict(r) for r in rows]
            except Exception as e:
                data[t] = [{"error": str(e)}]
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return target

def export_csv():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = _dir() / f"mimi_export_{stamp}.csv"
    with target.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        with db() as conn:
            for t in get_tables():
                if t == "schema_version":
                    continue
                w.writerow([f"=== {t} ==="])
                try:
                    rows = conn.execute(f"SELECT * FROM {t}").fetchall()
                    if rows:
                        w.writerow(list(rows[0].keys()))
                        for r in rows:
                            w.writerow([r[k] for k in r.keys()])
                except Exception as e:
                    w.writerow([f"error: {e}"])
                w.writerow([])
    return target

def main():
    while True:
        clear()
        header("EXPORT DATA", "JSON or CSV")
        print("  1. Export JSON")
        print("  2. Export CSV")
        print("  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "1":
            try:
                p = export_json()
                print(c(f"\n  OK {p}", GREEN)); pause()
            except Exception as e:
                print(c(f"\n  X {type(e).__name__}: {e}", RED)); pause()
        elif ch == "2":
            try:
                p = export_csv()
                print(c(f"\n  OK {p}", GREEN)); pause()
            except Exception as e:
                print(c(f"\n  X {type(e).__name__}: {e}", RED)); pause()
        elif ch == "0":
            break
        else:
            print(c("  X Invalid.", RED)); pause()

run = main
