"""Server handler for multi-AI chat."""
from ...ai_chat import ChatSession
from ...multi_ai import available_providers, PROVIDERS

# One session per process (stateful chat)
_SESSION = ChatSession()


def status():
    return {
        "providers": [
            {"id": p, "name": PROVIDERS[p]["name"],
             "available": True}
            for p in available_providers()
        ],
    }


def handle_chat(payload):
    message = (payload.get("message") or "").strip()
    if not message:
        return {"ok": False, "error": "empty message"}

    providers = payload.get("providers")
    if not providers:
        providers = available_providers()
    if not providers:
        return {"ok": False,
                "error": "no AI providers configured. "
                         "Set keys via API Keys menu."}

    all_mode = len(providers) > 1

    try:
        if all_mode:
            replies = _SESSION.ask_all(message, providers=providers)
            return {
                "ok": True,
                "mode": "multi",
                "replies": [
                    {"provider": p,
                     "name": PROVIDERS[p]["name"],
                     "text": replies[p]}
                    for p in providers
                ],
            }
        else:
            p = providers[0]
            r = _SESSION.ask_one(message, provider=p)
            return {
                "ok": True,
                "mode": "single",
                "replies": [
                    {"provider": p,
                     "name": PROVIDERS[p]["name"],
                     "text": r}
                ],
            }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def reset():
    _SESSION.clear()
    return {"ok": True}
