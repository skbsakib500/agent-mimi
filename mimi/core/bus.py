"""V10 Core - asynchronous event bus.

Modules publish events; subscribers react. No module calls another
module directly for side effects — everything flows through the bus,
so the guardian can audit each event.
"""
import threading
import queue
from datetime import datetime
from collections import defaultdict

from ..guardian import audit


class Event:
    __slots__ = ("type", "actor", "payload", "ts")

    def __init__(self, type, actor, payload):
        self.type = type
        self.actor = actor
        self.payload = payload or {}
        self.ts = datetime.now().isoformat(timespec="microseconds")

    def __repr__(self):
        return f"<Event {self.type} by {self.actor}>"


class Bus:
    def __init__(self):
        self._subs = defaultdict(list)
        self._queue = queue.Queue()
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._handled = 0

    def subscribe(self, event_type, handler):
        """handler(event) -> None. '*' subscribes to all."""
        with self._lock:
            self._subs[event_type].append(handler)
        return handler

    def unsubscribe(self, event_type, handler):
        with self._lock:
            try:
                self._subs[event_type].remove(handler)
            except (KeyError, ValueError):
                pass

    def publish(self, type, actor="system", payload=None):
        """Queue an event. Non-blocking."""
        ev = Event(type, actor, payload)
        audit.log(f"event:{type}", actor=actor, payload=payload or {})
        self._queue.put(ev)
        return ev

    def _dispatch(self, ev):
        handlers = list(self._subs.get(ev.type, []))
        handlers += list(self._subs.get("*", []))
        for h in handlers:
            try:
                h(ev)
            except Exception as e:
                audit.log("handler_error", actor="bus",
                          payload={"type": ev.type,
                                   "error": f"{type(e).__name__}: {e}"})
        self._handled += 1

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            try:
                ev = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._dispatch(ev)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def drain(self):
        """Process everything pending (synchronous helper for tests)."""
        while True:
            try:
                ev = self._queue.get_nowait()
            except queue.Empty:
                return
            self._dispatch(ev)

    def stats(self):
        return {
            "running": self._running,
            "pending": self._queue.qsize(),
            "handled": self._handled,
            "subscriptions": {k: len(v) for k, v in self._subs.items()},
        }


# Process-wide singleton
_BUS = Bus()


def bus():
    return _BUS
