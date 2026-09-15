"""Location TUI."""


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, MAGENTA, RED,
                     WHITE, YELLOW)
    from .ui import c, clear, header, menu, pause, section
    from . import location

    while True:
        clear()
        header("📍 LOCATION", "Consent-based · on-device only")
        if not location.available():
            print(c("\n  termux-location not found.", RED))
            print("  Run: pkg install -y termux-api")
            print("  Grant Location permission to Termux:API app.")
            pause()
            return
        print()
        ch = menu([
            ("1", "Read current location"),
            ("2", "Log current location"),
            ("3", "Recent location history"),
            ("4", "Geofences (add/list/delete)"),
            ("5", "Check geofences now"),
            ("0", "Exit"),
        ], "LOCATION MENU")

        if ch == "1":
            loc = location.get_current()
            if loc:
                print(c(f"\n  ✓ Lat: {loc['latitude']:.5f}  "
                        f"Lon: {loc['longitude']:.5f}", GREEN))
                print(f"  Accuracy: {loc['accuracy']}m")
                print(f"  Provider: {loc['provider']}")
            else:
                print(c("  X Could not read location", RED))
            pause()
        elif ch == "2":
            label = input("  Label [blank]: ").strip() or None
            loc = location.log_current(label=label)
            if loc:
                print(c(f"  ✓ Logged: {loc['latitude']:.5f}, "
                        f"{loc['longitude']:.5f}", GREEN))
            else:
                print(c("  X Failed", RED))
            pause()
        elif ch == "3":
            rows = location.recent()
            clear()
            header("LOCATION HISTORY", f"{len(rows)} entries")
            for r in rows:
                print(f"  #{r['id']}  {r['recorded_at'][:19]}  "
                      f"({r['latitude']:.4f}, {r['longitude']:.4f})  "
                      f"±{r['accuracy']}m  {r.get('label') or ''}")
            pause()
        elif ch == "4":
            _fences_menu()
        elif ch == "5":
            events = location.check_geofences()
            if events:
                for etype, name in events:
                    print(c(f"  {etype.upper()}: {name}", CYAN + BOLD))
            else:
                print(c("  No geofence events.", DIM + WHITE))
            pause()
        elif ch == "0":
            break


def _fences_menu():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED)
    from .ui import c, clear, header, menu, pause
    from . import location
    while True:
        clear()
        header("GEOFENCES", "Named places")
        rows = location.list_geofences()
        if rows:
            for r in rows:
                print(f"  · {r['name']:<14} "
                      f"({r['latitude']:.4f}, {r['longitude']:.4f})  "
                      f"{r['radius_m']}m")
        else:
            print(c("  (none)", DIM))
        ch = menu([
            ("1", "Add from current location"),
            ("2", "Add manually (lat, lon)"),
            ("3", "Delete one"),
            ("0", "Back"),
        ], "GEOFENCE")
        if ch == "1":
            name = input("  Name: ").strip()
            if not name:
                continue
            r = input("  Radius meters [200]: ").strip() or "200"
            res = location.add_geofence_from_current(name, int(r))
            print(c(f"  {'✓' if res.get('ok') else 'X'} {res}", GREEN if res.get('ok') else RED))
            pause()
        elif ch == "2":
            name = input("  Name: ").strip()
            lat = input("  Latitude: ").strip()
            lon = input("  Longitude: ").strip()
            rad = input("  Radius [200]: ").strip() or "200"
            res = location.add_geofence(name, float(lat), float(lon), int(rad))
            print(c(f"  {'✓' if res.get('ok') else 'X'} {res}", GREEN if res.get('ok') else RED))
            pause()
        elif ch == "3":
            name = input("  Name to delete: ").strip()
            location.delete_geofence(name)
            print(c("  ✓ Deleted", GREEN))
            pause()
        elif ch == "0":
            break


run = main

if __name__ == "__main__":
    main()
