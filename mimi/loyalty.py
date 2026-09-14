"""Mimi's loyalty layer - every sensitive action passes through here."""
from .database import execute
from .constitution import OWNER, PRINCIPLES


# Actions considered sensitive - must be reviewed
SENSITIVE = {
    "delete_data", "reset_db", "modify_code", "change_constitution",
    "export_private", "send_external", "install_package",
    "self_update_apply", "share_data",
}


def _log(action, verdict, reason=""):
    try:
        execute(
            """INSERT INTO system_logs (log_type, message)
               VALUES (?, ?)""",
            ("loyalty", f"action={action} verdict={verdict} reason={reason}"),
        )
    except Exception:
        pass


def review(action, context=None):
    """Return (allowed: bool, reason: str)."""
    action = str(action).lower().strip()
    context = context or {}

    # 1. Always allowed: read-only, user-initiated info
    if action in ("read", "list", "show", "query", "compute", "plan",
                  "predict", "review", "brief"):
        return True, "read-only"

    # 2. Never allowed without explicit Sakib approval
    if action in SENSITIVE:
        approved = context.get("approved_by")
        if approved != OWNER:
            _log(action, "DENIED", "no owner approval")
            return False, (
                f"Action '{action}' requires explicit approval from {OWNER}. "
                f"Constitution: Principle 3 (Consent)."
            )
        _log(action, "ALLOWED", f"approved by {OWNER}")
        return True, "owner approved"

    # 3. LLM requests: allow only if destination is Sakib-authorized
    if action == "llm_call":
        provider = (context.get("provider") or "").lower()
        allowed = {"groq", "gemini", "openai", "anthropic", "ollama"}
        if provider not in allowed:
            _log(action, "DENIED", f"unknown provider {provider}")
            return False, f"Provider '{provider}' not in authorized list."
        return True, "authorized provider"

    # 4. Network: allow only to known endpoints
    if action == "network":
        host = (context.get("host") or "").lower()
        allowed_hosts = (
            "api.groq.com", "generativelanguage.googleapis.com",
            "api.openai.com", "api.anthropic.com", "localhost",
            "127.0.0.1", "github.com", "api.openweathermap.org",
        )
        if not any(host.endswith(h) for h in allowed_hosts):
            _log(action, "DENIED", f"host {host}")
            return False, f"Network host '{host}' not authorized."
        return True, "authorized host"

    # 5. Everything else: allow but log
    return True, "default-allow"


def check_constitution():
    """Verify the constitution has not been tampered with."""
    from .constitution import is_sealed
    if not is_sealed():
        _log("constitution_check", "TAMPERED", "pledge or principles modified")
        return False
    return True


def who_is_owner():
    return OWNER


def principles_bn():
    return [(p["id"], p["bn"], p["rule"]) for p in PRINCIPLES]
