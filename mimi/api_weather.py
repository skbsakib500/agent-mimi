"""OpenWeatherMap - current + forecast."""
from .api_manager import get as get_key
from .api_http import get_json

BASE = "https://api.openweathermap.org/data/2.5"


def available():
    return bool(get_key("openweather"))


def current(city="Dhaka", units="metric"):
    key = get_key("openweather")
    if not key:
        return None
    r = get_json(f"{BASE}/weather", {"q": city, "appid": key, "units": units})
    if "_error" in r or r.get("cod") not in (200, "200"):
        return None
    return {
        "city": r.get("name"),
        "desc": (r.get("weather") or [{}])[0].get("description", "?"),
        "temp": r["main"]["temp"],
        "feels": r["main"]["feels_like"],
        "humidity": r["main"]["humidity"],
        "wind": r["wind"]["speed"],
    }


def forecast(city="Dhaka", units="metric"):
    key = get_key("openweather")
    if not key:
        return []
    r = get_json(f"{BASE}/forecast", {"q": city, "appid": key, "units": units, "cnt": 8})
    if "_error" in r:
        return []
    out = []
    for item in r.get("list", [])[:8]:
        out.append({
            "dt": item["dt_txt"],
            "temp": item["main"]["temp"],
            "desc": (item.get("weather") or [{}])[0].get("description", "?"),
        })
    return out


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE,
                     c, clear, header, pause, section)
    clear()
    header("🌤 WEATHER", "OpenWeatherMap")
    if not available():
        print(c("\n  No OPENWEATHER_API_KEY set.", RED))
        print("  Free key: https://openweathermap.org/api")
        pause(); return
    city = input("  City [Dhaka]: ").strip() or "Dhaka"
    cur = current(city)
    if not cur:
        print(c("\n  X Could not fetch weather.", RED)); pause(); return
    print()
    print(c(f"  {cur['city']}", BOLD + CYAN))
    print(f"  {cur['desc'].title()}")
    print(c(f"  {cur['temp']:.1f}°C  (feels {cur['feels']:.1f}°C)", BOLD + GREEN))
    print(f"  Humidity {cur['humidity']}%   Wind {cur['wind']} m/s")
    section("FORECAST", "📅")
    for f in forecast(city)[:5]:
        print(f"  {f['dt']}  {f['temp']:5.1f}°C  {f['desc']}")
    pause()

run = main
