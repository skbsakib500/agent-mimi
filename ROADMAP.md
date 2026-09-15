# Roadmap — Agent-Mimi

## Released

### ✅ V10.0.0 — "Guardian"
- Council of 11 Brains
- Crypto constitution (HMAC-SHA256)
- Signed audit chain
- Upgrade lab

### ✅ V11.0.0 — "Nova"
- Nova TUI, theme engine (8 palettes)
- 120+ icons
- Widgets, layout, animations
- Android-style UI

### ✅ V12.0.0 — "iOS"
- iOS-style web app at /app
- PWA install-to-home-screen
- Bottom tab nav (Home, Council, Nusrat, Stats, More)
- Message chat + typing indicator
- Bottom sheets for add task/goal/expense/journal
- Service worker offline

## In Flight — V13.0.0

Theme: **Chat + Always-On**

- [x] Multi-AI chat session (`ai_chat.py`)
- [x] Parallel multi-provider queries (`multi_ai.py`)
- [x] 24/7 daemon (`daemon.py`)
- [x] Personas system (`personas.py`, `persona_tui.py`)
- [x] Learn module (`learn.py`, `learn_tui.py`)
- [x] Location module (`location.py`, `location_tui.py`)
- [x] Telegram bot (`telegram_bot.py`)
- [x] iOS chat API (`web/ios/ai_chat_api.py`)
- [ ] Version bump 12.0.0 → 13.0.0
- [ ] requirements.txt
- [ ] Daemon install guide (Termux:Boot)
- [ ] iOS shell test pass
- [ ] Port daemon to Mimi-Android (background notifications)

## Planned — V14.0.0

Theme: **Sync + Multi-Profile**

- [ ] Cross-device sync (Mimi-Android ↔ Agent-Mimi)
- [ ] Profile switch UI
- [ ] Encrypted export
- [ ] Cloud-free sync via local network
- [ ] Webhook system

## Planned — V15.0.0

Theme: **Council Depth**

- [ ] Full 11 brain implementations
- [ ] Multi-brain debate view
- [ ] Decision history
- [ ] Nusrat personality tuning

## Backlog

- Plugin marketplace (plug_store/)
- Voice input everywhere
- Vision (already partial in vision.py)
- Widget system
- Test suite
- CI (GitHub Actions)

## Not Planned

- Cloud accounts
- Ad/tracking
- Server dependency
