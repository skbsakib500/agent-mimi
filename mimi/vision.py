"""Vision - image analysis via Gemini."""
import base64
from pathlib import Path
from .api_manager import get as get_key
from .api_http import post_json

BASE = "https://generativelanguage.googleapis.com/v1beta"


def available():
    return bool(get_key("gemini"))


def _encode(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    ext = Path(path).suffix.lower().lstrip(".") or "jpeg"
    if ext == "jpg":
        ext = "jpeg"
    return b64, f"image/{ext}"


def analyze(image_path, prompt):
    key = get_key("gemini")
    if not key:
        return "[no Gemini key]"
    b64, mime = _encode(image_path)
    url = f"{BASE}/models/gemini-3.6-flash:generateContent?key={key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime, "data": b64}},
            ]
        }],
        "generationConfig": {"maxOutputTokens": 600, "temperature": 0.2},
    }
    out = post_json(url, payload)
    if "_error" in out:
        return f"[Gemini error: {out['_error']}]"
    try:
        return out["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "[vision: unexpected response]"


def scan_receipt(image_path):
    prompt = (
        "Read this receipt. Reply with JSON only:\n"
        '{"merchant":"...","total":0,"currency":"BDT",'
        '"date":"YYYY-MM-DD","category":"...",'
        '"items":[{"name":"...","amount":0}]}'
    )
    return analyze(image_path, prompt)


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from .ui import c, clear, header, pause
    clear()
    header("👁 VISION", "Image to data")
    if not available():
        print(c("\n  Gemini API key required.", RED))
        print("  Set: 7 > API Keys > gemini")
        pause()
        return
    print("\n  1. Scan receipt (auto-log expense)")
    print("  2. Analyze any image with custom prompt")
    print("  0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "0":
        return
    path = input("  Image path: ").strip()
    if not path or not Path(path).exists():
        print(c("  X File not found.", RED))
        pause()
        return

    if ch == "1":
        print(c("\n  Reading receipt...", DIM + WHITE))
        out = scan_receipt(path)
        print()
        print(out)
        print()
        if input("  Add as expense? [y/N]: ").strip().lower() == "y":
            _log_receipt(out)
        pause()
    elif ch == "2":
        prompt = input("  Prompt: ").strip()
        if not prompt:
            return
        print(c("\n  Analyzing...", DIM + WHITE))
        out = analyze(path, prompt)
        print()
        print(out)
        pause()


def _log_receipt(text):
    import json, re
    from datetime import date
    from .database import execute
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        print("  X No JSON found.")
        return
    try:
        data = json.loads(m.group(0))
    except Exception as e:
        print(f"  X Parse error: {e}")
        return
    amt = float(data.get("total") or 0)
    if amt <= 0:
        print("  X No valid total.")
        return
    execute(
        """INSERT INTO finance
           (transaction_date, transaction_type, category, amount, description)
           VALUES (?, 'expense', ?, ?, ?)""",
        (data.get("date") or str(date.today()),
         data.get("category") or "general",
         amt,
         data.get("merchant") or "receipt"),
    )
    print(f"  OK {amt:,.2f} logged as expense.")


run = main
