# Known Issues — Agent-Mimi

Priority: 🔴 critical · 🟠 high · 🟡 medium · 🟢 low

---

## 🟠 KI-A01 · Version drift (__init__ vs CHANGELOG)

**Reality:** `mimi/__init__.py` = `"12.0.0"`, but V13 features
(multi-AI chat, daemon, personas) committed in `fe96a3d`.

**Impact:** `pip show` / `--version` reports old number.

**Fix:** Bump to `13.0.0` in V13 release commit.

---

## 🟠 KI-A02 · No requirements.txt

**Reality:** 172 Python files. Dependencies implicit.

**Impact:** Fresh install impossible without reading code.

**Fix:** Generate via `pip freeze` + manual trim.

---

## 🟠 KI-A03 · daemon.py depends on Termux:Boot

**Reality:** Daemon only works if user installed Termux:Boot.
Not documented in DEVELOPMENT.md.

**Impact:** Silent failure on non-Termux-Boot devices.

**Fix:** Document + add fallback (launch on app open).

---

## 🟡 KI-A04 · No test suite

**Reality:** Zero automated tests across 172 modules.

**Impact:** Refactor = fear. Every change = manual verify.

**Fix:** Start with smoke tests for core modules.

---

## 🟡 KI-A05 · Provider registry overlap

**Reality:** `api_manager.py` + `multi_ai.py` both track providers.

**Impact:** Adding a provider requires editing 2 places.

**Fix:** Single registry, imported by both.

---

## 🟡 KI-A06 · Three TUI implementations

**Reality:** `tui2.py` + `tui_android.py` + `sonic.py` overlap.

**Impact:** Bug fixes need 3 edits.

**Fix:** Consolidate into ui2/ framework.

---

## 🟢 KI-A07 · `.env` only has DEEPSEEK key

**Reality:** `.env` = 1 line (DEEPSEEK_API_KEY=).
Other providers configured elsewhere?

**Fix:** Document all provider keys in DEVELOPMENT.md.

---

## 🟢 KI-A08 · Backup dirs in ~

**Reality:** 4 backup trees in home dir duplicate this repo.

**Impact:** ~47MB wasted.

**Fix:** Consolidate into ~/Mimi-Forever/.

---

## Resolved (this release)

### ✅ KI-A00 · Missing remote / broken origin
Fixed: `gh repo create agent-mimi` + URL set + push.

### ✅ KI-A09 · .env not in .gitignore
Fixed: .gitignore rewritten, .env untracked (was already).

### ✅ KI-A10 · Runtime data tracked
Fixed: data/mimi.db, audit.chain, audit.jsonl untracked.
