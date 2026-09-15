"""Nusrat - Sakib's personal AI. Chairwoman of the council.

She is the 11th brain. Sakib talks only to her. She:
  - receives Sakib's intent
  - dispatches to the appropriate department(s)
  - summarizes and returns the answer
  - keeps a personal memory of Sakib's preferences and patterns
"""
from datetime import datetime
from . import memory as mem
from .council import council
from ..guardian import audit
from ..trust.loader import ensure_trusted


class Nusrat:
    NAME = "nusrat"
    ROLE = "personal_ai_chairwoman"
    MANDATE = "Speak for Sakib; dispatch to council; summarize back."

    def __init__(self):
        self.session_started = datetime.now()
        self.history = []

    # ── memory ──
    def remember(self, kind, value, key=None, importance=7):
        mem.remember(self.NAME, kind, value, key, importance)

    def recall(self, kind=None, limit=20):
        return mem.recall(self.NAME, kind, limit)

    # ── main entry: Sakib talks to Nusrat ──
    def listen(self, message, actor="SKB Sakib"):
        """Handle one utterance from Sakib. Returns reply dict."""
        message = (message or "").strip()
        if not message:
            return self._reply("Say something, Sakib.")

        if not ensure_trusted(fail_closed=False):
            return self._reply(
                "Trust check failed. I cannot act until it is restored.")

        # log the interaction
        audit.log("nusrat_listen", actor=actor,
                  payload={"len": len(message)})
        self.history.append({"ts": datetime.now().isoformat(
            timespec="seconds"), "from": actor, "msg": message})

        # classify intent
        intent = self._classify(message)
        audit.log("nusrat_intent", actor=self.NAME,
                  payload={"intent": intent["kind"],
                           "confidence": intent["confidence"]})

        # dispatch based on intent
        if intent["kind"] == "greeting":
            return self._reply(self._greet())
        if intent["kind"] == "status":
            return self._status()
        if intent["kind"] == "brief":
            return self._dispatch_and_summarize("brief", {})
        if intent["kind"] == "plan":
            return self._dispatch_and_summarize("plan", {})
        if intent["kind"] == "balance":
            return self._dispatch_and_summarize("balance", {})
        if intent["kind"] == "tasks":
            return self._dispatch_and_summarize("list_tasks", {})
        if intent["kind"] == "goals":
            return self._dispatch_and_summarize("list_goals", {})
        if intent["kind"] == "study":
            return self._dispatch_and_summarize("study_summary", {})
        if intent["kind"] == "help":
            return self._reply(self._help_text())
        if intent["kind"] == "remember":
            return self._remember_from(message)
        if intent["kind"] == "recall":
            return self._recall_for(message)
        if intent["kind"] == "council":
            return self._report_council()
        if intent["kind"] == "ask_llm":
            return self._ask_llm(message)

        return self._reply(
            "I am not sure what you want. Say 'help' for options.")

    # ── reply builder ──
    def _reply(self, text, extra=None):
        out = {"from": self.NAME, "text": text}
        if extra:
            out.update(extra)
        return out


    # ── intent classifier (rule-based, fast) ──
    def _classify(self, message):
        m = message.lower().strip()
        # greeting
        if m in ("hi", "hello", "hey", "salam", "assalamualaikum",
                 "assalamu alaikum", "নমস্কার"):
            return {"kind": "greeting", "confidence": 0.95}
        # status
        if any(k in m for k in ("status", "how are you", "kemon acho",
                                 "কেমন আছো")):
            return {"kind": "status", "confidence": 0.9}
        # brief
        if any(k in m for k in ("brief", "briefing", "summary of day",
                                 "আজকের সারসংক্ষেপ")):
            return {"kind": "brief", "confidence": 0.9}
        # plan
        if any(k in m for k in ("plan", "today", "আজকের প্ল্যান",
                                 "what should i do")):
            return {"kind": "plan", "confidence": 0.85}
        # balance
        if any(k in m for k in ("balance", "money", "cash",
                                 "টাকা", "ব্যালান্স")):
            return {"kind": "balance", "confidence": 0.85}
        # tasks
        if any(k in m for k in ("task", "tasks", "to do",
                                 "কাজ")):
            return {"kind": "tasks", "confidence": 0.8}
        # goals
        if any(k in m for k in ("goal", "goals", "লক্ষ্য")):
            return {"kind": "goals", "confidence": 0.8}
        # study
        if any(k in m for k in ("study", "পড়া", "পড়াশোনা")):
            return {"kind": "study", "confidence": 0.8}
        # council
        if any(k in m for k in ("council", "departments", "team",
                                 "বিভাগ")):
            return {"kind": "council", "confidence": 0.85}
        # help
        if m in ("help", "?", "commands", "সাহায্য"):
            return {"kind": "help", "confidence": 0.95}
        # remember
        if m.startswith("remember ") or m.startswith("মনে রাখো "):
            return {"kind": "remember", "confidence": 0.9}
        # recall
        if m.startswith("recall ") or m.startswith("মনে কর "):
            return {"kind": "recall", "confidence": 0.85}
        # fallback: try llm
        return {"kind": "ask_llm", "confidence": 0.4}

    # ── greeting ──
    def _greet(self):
        # Persona greeting overrides time-based
        try:
            from .. import personas
            g = personas.greeting()
            if g:
                return g
        except Exception:
            pass
        h = datetime.now().hour
        if h < 5:
            g = "Still up, Sakib?"
        elif h < 12:
            g = "Good morning, Sakib."
        elif h < 17:
            g = "Good afternoon, Sakib."
        elif h < 22:
            g = "Good evening, Sakib."
        else:
            g = "Late night, Sakib."
        # recall a fact if any
        facts = self.recall(kind="preference", limit=1)
        tail = ""
        if facts:
            tail = f"  ({facts[0]['value']})"
        return g + tail

    # ── status ──
    def _status(self):
        c = council()
        depts = c.all()
        line = f"{len(depts)} departments online"
        try:
            from ..upgrade import proposal
            pend = len(proposal.pending())
            line += f"; {pend} upgrades pending"
        except Exception:
            pass
        return self._reply(f"Ready. {line}.")


    # ── dispatch to council + summarize ──
    def _dispatch_and_summarize(self, command, args):
        c = council()
        r = c.route(command, args=args, actor="SKB Sakib")
        if not r.get("ok"):
            # fallback: use orchestrator
            try:
                from ..core.orchestrator import orchestrator
                r2 = orchestrator().route(command, args=args,
                                           actor="SKB Sakib")
                if r2.get("ok"):
                    return self._reply(
                        self._format_result(command, r2.get("result"),
                                             r2.get("specialist")))
            except Exception:
                pass
            return self._reply(
                f"I could not complete that. ({r.get('reason')})")
        return self._reply(
            self._format_result(command, r.get("result"),
                                 r.get("dept")))

    def _format_result(self, command, result, who):
        if result is None:
            return f"({who}) no data."
        if isinstance(result, list):
            if not result:
                return f"({who}) empty."
            head = f"({who}) {len(result)} item(s):\n"
            lines = []
            for it in result[:8]:
                if isinstance(it, dict):
                    label = it.get("title") or it.get("name") \
                        or str(it)[:50]
                    extra = ""
                    if "progress" in it:
                        extra = f" [{it['progress']}%]"
                    elif "priority" in it:
                        extra = f" [{it['priority']}]"
                    lines.append(f"  - {label}{extra}")
                else:
                    lines.append(f"  - {str(it)[:60]}")
            return head + "\n".join(lines)
        if isinstance(result, dict):
            # pick common keys
            keys = ("greeting", "tasks_pending", "tasks_overdue",
                    "study_week_h", "balance", "income", "expense",
                    "cash_balance", "active_debts", "one_rule")
            parts = []
            for k in keys:
                if k in result:
                    v = result[k]
                    if isinstance(v, float):
                        parts.append(f"{k}={v:.2f}")
                    else:
                        parts.append(f"{k}={v}")
            if parts:
                return f"({who}) " + ", ".join(parts)
            if "plan" in result and isinstance(result["plan"], list):
                lines = [f"  [{b.get('when','-')}] {b.get('action','')}"
                         for b in result["plan"][:6]]
                return f"({who}) plan:\n" + "\n".join(lines)
            return f"({who}) " + str(result)[:200]
        return f"({who}) {str(result)[:200]}"


    # ── remember / recall ──
    def _remember_from(self, message):
        m = message.strip()
        if m.lower().startswith("remember "):
            content = m[9:].strip()
        elif m.startswith("মনে রাখো "):
            content = m[len("মনে রাখো "):].strip()
        else:
            content = m
        if not content:
            return self._reply("What should I remember?")
        self.remember("preference", content, importance=8)
        return self._reply(f"Noted: {content}")

    def _recall_for(self, message):
        m = message.strip()
        for prefix in ("recall ", "মনে কর "):
            if m.lower().startswith(prefix) or m.startswith(prefix):
                q = m[len(prefix):].strip()
                break
        else:
            q = m
        if not q:
            rows = self.recall(limit=10)
            if not rows:
                return self._reply("(nothing stored)")
            lines = [f"  - {r['value']}" for r in rows[:8]]
            return self._reply("Remembered:\n" + "\n".join(lines))
        rows = mem.search(q, limit=10)
        if not rows:
            return self._reply(f"(no memory of '{q}')")
        lines = [f"  - [{r['dept']}] {r['value']}" for r in rows[:8]]
        return self._reply(f"About '{q}':\n" + "\n".join(lines))

    # ── council report ──
    def _report_council(self):
        c = council()
        ds = c.describe_all()
        if not ds:
            return self._reply(
                "No departments are online yet. "
                "Add them via council.register(...).")
        lines = [f"  {d['name']:<12} [{d['priority']}] {d['role']}"
                 for d in ds]
        return self._reply(
            f"{len(ds)} departments:\n" + "\n".join(lines))

    # ── LLM fallback with knowledge check ──
    def _persona_system(self, base):
        try:
            from .. import personas
            return personas.system_prompt() + "\n\n" + (base or "")
        except Exception:
            return base

    def _ask_llm(self, message):
        # First, check learned knowledge
        try:
            from .. import learn
            hits = learn.recall(message, limit=2)
            if hits and hits[0]["confidence"] >= 0.5:
                top = hits[0]
                return self._reply(
                    f"[from learned knowledge, conf {top['confidence']:.2f}]\n"
                    + top["answer"][:1000])
        except Exception:
            pass
        # Then, check multi-AI consensus
        try:
            from ..multi_ai import available_providers, ask
            provs = available_providers()
            if len(provs) >= 2:
                # ask one provider for speed (not full consensus)
                return self._reply(str(ask(message, provider=provs[0]))[:1200])
        except Exception:
            pass
        return self._reply("I don't have a good answer right now.")

    def _ask_llm_old(self, message):
        try:
            from ..agent import Agent
            a = Agent()
            reply = a.respond(message)
            return self._reply(str(reply)[:1500])
        except Exception as e:
            return self._reply(
                f"I cannot answer that right now. "
                f"({type(e).__name__})")

    # ── help ──
    def _help_text(self):
        return (
            "I am Nusrat.\n"
            "Things you can say:\n"
            "  hi / salam          - greet\n"
            "  status              - system status\n"
            "  brief               - daily briefing\n"
            "  plan                - today's plan\n"
            "  balance             - finance\n"
            "  tasks / goals       - lists\n"
            "  study               - study summary\n"
            "  council             - show departments\n"
            "  remember <text>     - save a preference\n"
            "  recall <query>      - look up memory\n"
            "  help                - this message"
        )


# process-wide singleton
_NUSRAT = Nusrat()


def nusrat():
    return _NUSRAT
