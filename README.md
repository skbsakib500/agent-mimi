# Agent Mimi

**Version 12.0 "iOS"** — Personal Life OS for Termux

## Four interfaces

    python -m mimi             # Nova TUI (curses)
    python -m mimi ios         # iOS-style web app (PWA)
    python -m mimi app         # Android-style TUI
    python -m mimi sonic       # Sonic CLI
    python -m mimi --classic   # classic menu
    python -m mimi web         # browser dashboard

## Council of 11 Brains

Nusrat (Chairwoman) + 10 departments:
DevOps · Strategy · Finance · Admin · Study
Health · Civil · Research · Relations · Legal

## V12 iOS app

Open in browser: `http://127.0.0.1:8765/app`

- True iOS-style UI: nav bar, tab bar, cards, chat
- Bottom tab navigation: Home · Council · Nusrat · Stats · More
- Touch-first: tap, swipe, long-press
- Haptic vibration on every interaction
- Message-style chat with typing indicator
- Bottom sheets for add task / goal / expense / journal
- FAB for quick add
- PWA: install to home screen (iOS/Android)
- Offline-capable via service worker

## Safety

- Cryptographic constitution (HMAC-SHA256)
- Signed append-only audit chain
- Owner-gated permissions (SKB Sakib)
- Sandbox testing before apply
- Auto rollback on failure

## Verify

    python -m mimi.trust.verify
    python -m mimi.guardian.audit verify
    python -m mimi.health.diagnostic run
