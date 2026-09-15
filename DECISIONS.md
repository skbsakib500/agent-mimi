# Decisions — Agent-Mimi

Architecture Decision Records (ADR-lite).

---

## D-001 · Python over everything

**Context:** Need a personal Life OS that runs on Termux (Android).

**Decision:** Python 3.14+ as the sole language.

**Why:**
- Termux has Python built-in
- stdlib covers HTTP, SQLite, curses
- AI providers all have Python SDKs
- No compilation, edit-and-run

**Rejected:**
- Node/TS — heavy runtime
- Go/Rust — compile step, no curses stdlib
- Bash — too limited for 60+ modules

**Status:** Accepted · 2026-09-13

---

## D-002 · Six interfaces, one core

**Context:** Users want TUI, web, mobile — same data.

**Decision:** One Python core (`mimi/`), 6 presentation layers.

**Why:**
- Data stays in SQLite — any interface reads it
- No duplicated logic
- User picks interface per context (phone → iOS PWA)

**Rejected:**
- Separate apps — data sync nightmare
- Web-only — no offline TUI

**Status:** Accepted · 2026-09-14

---

## D-003 · SQLite (not JSON, not Postgres)

**Context:** Persistence for 60+ modules.

**Decision:** SQLite, per-profile at `data/profiles/<name>/mimi.db`.

**Why:**
- Stdlib, no server
- ACID, indexes, migrations
- Single file → easy backup
- Multi-profile = multiple files

**Rejected:**
- JSON — race conditions, no queries
- Postgres — overkill, server dep
- MongoDB — same

**Status:** Accepted · 2026-09-13

---

## D-004 · Council of 11 Brains

**Context:** Single AI personality feels flat.

**Decision:** 11 specialized "brains" — Nusrat (chair) + 10 depts.

**Why:**
- Different domains need different prompts
- Nusrat coordinates decisions
- Matches real org (DevOps, Finance, Legal…)

**Rejected:**
- Single monolithic AI — no specialization
- Many uncoordinated bots — chaos

**Status:** Accepted · 2026-09-14

---

## D-005 · HMAC constitution + audit chain

**Context:** AI systems drift. Need accountability.

**Decision:** Constitution signed with HMAC-SHA256.
Audit log append-only, each entry signed.

**Why:**
- Verifiable rules
- Tamper detection
- Owner-gated changes (SKB Sakib)
- Trust without external server

**Rejected:**
- No crypto — silent drift
- Blockchain — overkill, external dep
- Central server — breaks offline

**Status:** Accepted · 2026-09-14

---

## D-006 · Multi-provider AI

**Context:** Free tiers fluctuate. Users have different keys.

**Decision:** 7 providers supported (`multi_ai.py`).
User picks per session. Parallel queries available.

**Why:**
- No single point of failure
- User chooses cost/speed tradeoff
- Compare providers side-by-side

**Rejected:**
- Single provider — lock-in
- Backend proxy — privacy break, cost

**Status:** Accepted · 2026-09-15

---

## D-007 · 24/7 daemon via Termux:Boot

**Context:** Notifications, automation need background runs.

**Decision:** `daemon.py` scheduler, started via Termux:Boot.

**Why:**
- Termux has no true background service
- Termux:Boot is standard workaround
- Wakes every minute, runs schedule

**Rejected:**
- Foreground app — kills on close
- Cron — limited on Android
- WorkManager — Android-only, breaks Termux

**Status:** Accepted · 2026-09-15

---

## D-008 · SKB Project Memory (this release)

**Context:** Docs drift. AI sessions forget context.

**Decision:** Every SKB project carries its own memory in-repo.
Same pattern across all projects.

**Why:**
- Source of truth with the code
- Survives AI/model changes
- Machine-readable for `skb` tooling

**Status:** Accepted · 2026-09-15

---

## Open Questions

- V12 vs V13 version bump strategy?
- Add requirements.txt?
- Consolidate tui2/sonic/tui_android?
- Daemon port to Mimi-Android?
