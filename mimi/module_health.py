"""Module Health Center."""
from .router import health_check
from .ui import (BOLD, DIM, GREEN, RED, WHITE, YELLOW, c, clear, header,
                 pause, section)

def main(categories=None):
    if categories is None:
        from .main import CATEGORIES as categories
    clear()
    header("MODULE HEALTH", "Integration diagnostics")
    results = health_check(categories)
    counts = {"PASS":0, "ADAPTER":0, "MISSING":0, "IMPORT ERROR":0}
    for item in results:
        s = item["status"]
        counts[s] = counts.get(s, 0) + 1
        if s == "PASS":
            marker, style = "OK", GREEN
        elif s == "ADAPTER":
            marker, style = "AD", YELLOW
        else:
            marker, style = "XX", RED
        entry = f" -> {item['entrypoint']}" if item["entrypoint"] else ""
        print(f"  [{marker}] {item['name']:<20} {c(s, style)}{entry}")
        if s not in ("PASS","ADAPTER"):
            print(c(f"         {item['detail']}", DIM+WHITE))
    section("RESULT", "[*]")
    total = len(results)
    good = counts["PASS"] + counts["ADAPTER"]
    print(f"  Ready: {good}/{total}")
    print(f"  {c('PASS', GREEN)} {counts['PASS']}   "
          f"{c('ADAPTER', YELLOW)} {counts['ADAPTER']}   "
          f"{c('ISSUES', RED)} {counts['MISSING']+counts['IMPORT ERROR']}")
    if good == total:
        print(c("\n  SYSTEM READY", GREEN+BOLD))
    else:
        print(c("\n  NEEDS ATTENTION", RED+BOLD))
    pause()
