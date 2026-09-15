"""Telegram bot - chat with Mimi from anywhere.

Zero-dependency: uses urllib for long polling. No pip install needed.
"""
import json
import time
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

from .api_manager import get as get_key
from .guardian import audit


BASE = "https://api.telegram.org"


def _token():
    return get_key("telegram_bot_token")


def _owner_id():
    return get_key("telegram_chat_id")


def is_configured():
    return bool(_token()) and bool(_owner_id())


def _post(method, payload):
    """POST to Telegram API."""
    tok = _token()
    if not tok:
        return {"ok": False, "error": "no token"}
    url = f"{BASE}/bot{tok}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return {"ok": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _get(method, params=None):
    tok = _token()
    if not tok:
        return {"ok": False, "error": "no token"}
    url = f"{BASE}/bot{tok}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def send_message(chat_id, text, parse_mode=None):
    """Send a plain-text message."""
    payload = {
        "chat_id": str(chat_id),
        "text": str(text)[:4000],
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return _post("sendMessage", payload)


def send_typing(chat_id):
    return _post("sendChatAction", {"chat_id": str(chat_id), "action": "typing"})


def get_updates(offset=0, timeout=25):
    return _get("getUpdates", {"offset": offset, "timeout": timeout})


HELP_TEXT = """🤖 *Mimi Bot*

Just send a message — Mimi (Nusrat) will reply.

Commands:
/start — welcome
/help  — this message
/status — system status
/brief — daily briefing
/balance — finance snapshot
/tasks — open tasks
/council — council of 11 brains
/reset — clear chat history

Anything else goes to Nusrat, who may consult:
• DeepSeek · Groq · Gemini (multi-AI)
• Council of 11 departments
• Learned knowledge base
"""


def _respond_to(text, chat_id, user_name="Sakib"):
    """Generate reply. Returns string."""
    t = text.strip()
    if not t:
        return "Say something, boss."

    low = t.lower()

    if low in ("/start", "start"):
        return (f"Hello, {user_name}. I'm Mimi — your Personal Life OS.\n"
                "Send /help for commands, or just talk to me.")
    if low in ("/help", "help"):
        return HELP_TEXT
    if low == "/status":
        return _status_text()
    if low == "/brief":
        return _try_route("brief")
    if low == "/balance":
        return _try_route("balance")
    if low == "/tasks":
        return _try_route("list_tasks")
    if low == "/council":
        return _council_text()
    if low == "/reset":
        return "__RESET__"

    # Default: talk to Nusrat
    return _talk_nusrat(t, user_name)


def _status_text():
    try:
        from .multi_ai import status as ai_status, PROVIDERS
        lines = ["Mimi status:"]
        for p, ok in ai_status().items():
            name = PROVIDERS[p]["name"]
            lines.append(f"  {'✓' if ok else '·'} {name}")
        try:
            from .council.council import council
            from .council.bootstrap import bootstrap
            bootstrap()
            lines.append(f"  Council: {len(council().all())} departments")
        except Exception:
            pass
        return "\n".join(lines)
    except Exception as e:
        return f"error: {e}"


def _try_route(cmd):
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.council import council
        r = council().route(cmd, actor="telegram")
        if r.get("ok"):
            return str(r["result"])[:1500]
        # fallback
        from .core.orchestrator import orchestrator
        r2 = orchestrator().route(cmd, actor="telegram")
        if r2.get("ok"):
            return str(r2["result"])[:1500]
        return f"(no data for {cmd})"
    except Exception as e:
        return f"error: {type(e).__name__}: {e}"


def _council_text():
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.council import council
        depts = council().all()
        lines = [f"🏛 Council of {len(depts)} departments:"]
        for d in depts:
            lines.append(f"  [{d.PRIORITY}] {d.NAME:<12} {d.ROLE}")
        return "\n".join(lines)
    except Exception as e:
        return f"error: {e}"


def _talk_nusrat(text, user_name):
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.nusrat import nusrat
        r = nusrat().listen(text, actor=user_name)
        reply = r.get("text", "(no reply)")
        # If Nusrat's LLM fallback returned weak reply, try multi-AI
        if "I don't have a good answer" in reply:
            try:
                from .multi_ai import available_providers, ask
                provs = available_providers()
                if provs:
                    reply = str(ask(text, provider=provs[0]))[:1500]
            except Exception:
                pass
        return reply[:4000]
    except Exception as e:
        return f"error: {type(e).__name__}: {e}"


def run_bot(verbose=True, max_iterations=None):
    """Main long-polling loop. Runs until Ctrl+C or max_iterations."""
    if not is_configured():
        print("  X Bot not configured.")
        print("  Set telegram_bot_token and telegram_chat_id.")
        print("  Use: python -c 'from mimi.api_manager import set_key' ...")
        return 1

    owner = str(_owner_id()).strip()
    if verbose:
        print(f"  ✓ Bot started. Owner chat ID: {owner}")
        print("  Send a message to your bot from Telegram.")
        print("  Ctrl+C to stop.\n")

    offset = 0
    iters = 0
    audit.log("telegram_start", actor="telegram", payload={"owner": owner})

    try:
        while True:
            if max_iterations and iters >= max_iterations:
                break
            iters += 1

            resp = get_updates(offset=offset, timeout=25)
            if not resp.get("ok"):
                err = resp.get("error", "unknown")
                if verbose:
                    print(f"  ! poll error: {err}")
                time.sleep(3)
                continue

            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or update.get("edited_message")
                if not msg:
                    continue
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")
                user_name = (msg.get("from", {}).get("first_name")
                             or "Boss")

                # Owner-only gate
                if chat_id != owner:
                    send_message(chat_id, "⛔ This bot is private.")
                    audit.log("telegram_unauthorized", actor="telegram",
                              payload={"chat_id": chat_id})
                    if verbose:
                        print(f"  ! unauthorized: {chat_id}")
                    continue

                if verbose:
                    print(f"  ← {user_name}: {text[:60]}")

                send_typing(chat_id)
                reply = _respond_to(text, chat_id, user_name)

                if reply == "__RESET__":
                    try:
                        from .council.nusrat import nusrat
                        nusrat().history = []
                    except Exception:
                        pass
                    reply = "Chat history cleared."

                # Send (in chunks if long)
                for i in range(0, len(reply), 3500):
                    send_message(chat_id, reply[i:i+3500])

                if verbose:
                    print(f"  → {reply[:60]}")

                audit.log("telegram_msg", actor="telegram",
                          payload={"from": user_name, "len": len(text)})
    except KeyboardInterrupt:
        if verbose:
            print("\n  Bot stopped.")
        audit.log("telegram_stop", actor="telegram")
        return 0
    return 0


def main():
    import sys
    args = sys.argv[1:]
    if "test" in args:
        # Send a test message
        if not is_configured():
            print("  X Not configured.")
            return 1
        r = send_message(_owner_id(), "🤖 Mimi bot test — ready.")
        print("  test:", r.get("ok"), r.get("description", ""))
        return 0
    if "whoami" in args:
        r = _get("getMe")
        print("  getMe:", json.dumps(r.get("result", r), indent=2))
        return 0
    return run_bot(verbose=True)


if __name__ == "__main__":
    sys.exit(main())
