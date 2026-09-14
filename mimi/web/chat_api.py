"""Chat API for web dashboard."""
from ..agent import Agent

_agent_cache = {}


def _get_agent():
    if "a" not in _agent_cache:
        _agent_cache["a"] = Agent()
    return _agent_cache["a"]


def handle_chat(payload):
    msg = (payload.get("message") or "").strip()
    if not msg:
        return {"ok": False, "error": "empty message"}
    try:
        agent = _get_agent()
        reply = agent.respond(msg)
        return {"ok": True, "reply": reply}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
