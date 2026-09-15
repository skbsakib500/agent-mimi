# Changelog — Agent Mimi

## [13.0.0] — 2026-09-16

### Added
- Multi-AI chat session (`ai_chat.py`, `ai_chat_tui.py`)
- Parallel multi-provider queries (`multi_ai.py`)
- 24/7 background daemon (`daemon.py`)
- Personas system (`personas.py`, `persona_tui.py`)
- Learn + Location modules
- Telegram bot integration
- iOS chat API endpoint
- Runtime prompt wiring — reads from `~/SKB-Dev/spec/lifos/ai/prompts/`

### Changed
- `ai_plan.py` now loads prompt from canonical spec, hardcoded fallback
- `ai_plan.build_prompt()` returns 3-tuple `(text, context, source)`

### Architecture
- Zero third-party dependencies (100% Python stdlib)
- Canonical prompt spec at `spec/lifos/ai/prompts/`
- Runtime = adapter · spec = source of truth

### Commits
- `fe96a3d` feat: V13 — multi-AI chat, 24/7 daemon, personas, telegram
- `f094ff2` feat: wire ai_plan to Life OS canonical spec

## [12.0.0] — "iOS"

### Added
- iOS-style web app at `/app` — install-to-home-screen PWA
- Frosted glass nav bar with large-title collapse
- Bottom tab bar (Home, Council, Nusrat, Stats, More)
- iOS message-style chat with typing indicator
- Bottom sheets for add task / goal / expense / journal
- Floating action button (FAB)
- Touch gestures: swipe-back, swipe-tabs, edge-swipe
- Haptic feedback on all interactions
- Service worker for offline use
- New API routes: `/api/council`, `/api/launch`, `/api/action`

### Changed
- Version bumped to V12.0 "iOS"

## [11.0.0] — "Nova"
- Nova TUI, theme engine (8 palettes), 120+ icons
- Widgets, layout engine, animations
- Android-style UI

## [10.0.0] — "Guardian"
- Council of 11 Brains, crypto constitution,
  signed audit chain, upgrade lab, department factory

## [9.0.0] — "Echo"    Web chat, voice, vision
## [7.0.0] — "Aurora"  Web dashboard + PWA
## [6.0.0] — "Nexus"   Multi-profile, plugins, cloud sync
## [5.0.0] — "Quantum" Full-screen curses TUI
## [4.0.0] — "Oracle"  Briefing, suggestions, LLM APIs
## [3.0.0] — "Nova"    XP, levels, badges (initial)
## [2.0.0] — "Zenith"  Agent, insights, automation
