"""Startup splash screen."""
import time, os, sys

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; MG="\033[95m"; GR="\033[92m"; WH="\033[97m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R

LOGO = r"""
   ___   ___ ___ _____ _  _   __  __ ___ __  __ ___
  / _ \ / __| _ \_   _| \| | |  \/  |_ _|  \/  |_ _|
 | (_) | (_ |   / | | | .` | | |\/| || || |\/| || |
  \___/ \___|_|_\ |_| |_|\_| |_|  |_|___|_|  |_|___|
"""

def show(user="SKB Sakib", delay=0.9):
    os.system("clear")
    print()
    for line in LOGO.strip("\n").splitlines():
        print(c(line, B + MG))
        time.sleep(0.03)
    print()
    print(c(f"      Personal Life Agent  ·  v2.0.0 'Zenith'", CY))
    print(c(f"      Welcome back, {user}", GR + B))
    print()
    time.sleep(delay)
    print(c("      loading", D + WH), end="", flush=True)
    for _ in range(3):
        time.sleep(0.25)
        sys.stdout.write(c(".", D + WH)); sys.stdout.flush()
    print("\n")
    time.sleep(0.3)

def main():
    show()

run = main
