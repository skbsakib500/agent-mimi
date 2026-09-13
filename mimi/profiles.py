"""Multi-profile system - separate DB per profile."""
import os, shutil
from pathlib import Path
from datetime import datetime
from .database import DB_PATH, DATA_DIR

PROFILE_DIR = DATA_DIR / "profiles"
ACTIVE_FILE = DATA_DIR / ".active_profile"

DEFAULT_PROFILES = {
    "personal": "Personal life, goals, health, finance",
    "work":     "Work projects, career, meetings",
    "study":    "Study, exams, learning",
}


def _ensure():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def active():
    _ensure()
    if ACTIVE_FILE.exists():
        name = ACTIVE_FILE.read_text().strip()
        if name:
            return name
    return "default"


def set_active(name):
    _ensure()
    name = name.strip().lower().replace(" ", "_")
    if not name:
        return False
    ACTIVE_FILE.write_text(name)
    return True


def list_profiles():
    _ensure()
    out = ["default"]
    for p in sorted(PROFILE_DIR.iterdir()):
        if p.is_dir():
            out.append(p.name)
    return out


def profile_db(name):
    if name == "default":
        return DB_PATH
    return PROFILE_DIR / name / "mimi.db"


def create(name, description=""):
    _ensure()
    name = name.strip().lower().replace(" ", "_")
    if name in ("default", ""):
        return False, "reserved name"
    pdir = PROFILE_DIR / name
    if pdir.exists():
        return False, "already exists"
    pdir.mkdir(parents=True)
    (pdir / "info.txt").write_text(
        f"name: {name}\ndescription: {description}\ncreated: {datetime.now().isoformat()}\n"
    )
    return True, str(pdir)


def delete(name):
    _ensure()
    if name == active():
        return False, "cannot delete active profile"
    pdir = PROFILE_DIR / name
    if not pdir.exists():
        return False, "not found"
    shutil.rmtree(pdir)
    return True, "deleted"


def info(name):
    if name == "default":
        return {"name": "default", "description": "Primary profile", "path": str(DB_PATH)}
    pdir = PROFILE_DIR / name
    desc = ""
    info_f = pdir / "info.txt"
    if info_f.exists():
        for line in info_f.read_text().splitlines():
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
    db = profile_db(name)
    size = db.stat().st_size // 1024 if db.exists() else 0
    return {"name": name, "description": desc,
            "path": str(db), "size_kb": size}


def switch_and_relaunch(name):
    """Set active and print restart hint."""
    set_active(name)
    return True


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    while True:
        clear()
        header("👥 PROFILES", "Separate data for different contexts")
        act = active()
        print(c(f"\n  Active: {act}", BOLD + GREEN))
        section("AVAILABLE", "📁")
        for p in list_profiles():
            marker = "●" if p == act else "○"
            i = info(p)
            desc = i.get("description", "")
            size = i.get("size_kb", 0)
            size_str = f" ({size} KB)" if size else ""
            print(f"  {marker} {p:<12} {desc}{size_str}")
        print()
        print("  1. Switch profile")
        print("  2. Create profile")
        print("  3. Delete profile")
        print("  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "0":
            break
        elif ch == "1":
            n = input("  Profile name: ").strip()
            if n in list_profiles():
                set_active(n)
                print(c(f"  OK Active set to '{n}'.", GREEN))
                print(c("  Restart Mimi to apply.", YELLOW))
                pause()
            else:
                print(c("  X Not found.", RED)); pause()
        elif ch == "2":
            n = input("  New profile name: ").strip()
            d = input("  Description: ").strip()
            ok, msg = create(n, d)
            print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
            pause()
        elif ch == "3":
            n = input("  Profile to delete: ").strip()
            ok, msg = delete(n)
            print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
            pause()

run = main
