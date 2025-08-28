
# Interface Standard Template — Conversational Programming Assistant (Reusable)

Use this as a baseline for any project implementing an OpenAI-style programming/chat interface.

## 1. Purpose
Consistent, accessible, mobile-ready interface for chat + coding.

## 2. Visual Tokens (override per brand)
- Colors: primary, backgrounds, bubbles, code, alerts.
- Typography: sans + mono; sizes (h1, h2, body, small, code).
- Spacing: 8px baseline; cards 16px; bubbles 12px; gaps 8px.
- Motion: fast 120ms, base 200ms, slow 320ms; curve easing.

## 3. IA
- Pre-login, Post-login (Profile, Security, Social, Sessions, Billing, Danger).
- Chat (Sidebar, Chat Pane, Composer, Right Rail).

## 4. Components
- Sidebar: New, Search, Pinned, Recent, Utilities (Settings, Account, Shortcuts, Changelog, Help).
- Chat Pane: user/assistant bubbles, code blocks, citations.
- Composer: textarea, send, attach, code mode, stop.
- Header: title, model, export, help.
- Drawers/Modals/Sheets.

## 5. Behaviors
- Streaming + Stop; Auto-follow; Scroll FAB; Infinite scroll up.
- Message actions: edit prompt, regenerate (version tabs), feedback, copy, delete, insert to editor.
- Sidebar collapse/expand (persisted).

## 6. Accessibility
- Landmarks, h1 per view, aria-live polite log, focus management, reduced-motion support, AA contrast.

## 7. Mobile
- Drawer sidebar; sticky composer; long-press actions; horizontal scroll in code.

## 8. Navigation & Routes (sample)
- /app, /app/chat/:id, /app/chat/:id?popout=1
- /app/settings/:tab (general, appearance, models, files, notifications, advanced)
- /app/account/:tab (profile, security, social, sessions, billing, danger)

## 9. Events (contract)
- sidebar.toggle, nav.open, chat.new, chat.open, chat.popout.open/close
- composer.send, message.stop/retry/regenerate/copy/feedback
- thread.rename/pin/delete, scroll.follow.enable/disable

## 10. Data Models
- Conversation, Message, RichContent (text, codeBlocks, attachments, citations).

## 11. State Machines
- Message: idle → requesting → streaming → completed|stopped|error → regenerating.
- Navigation: ChatHome ↔ ChatView ↔ Settings/Account; Popout isolate.

## 12. Testing Hooks & Budgets
- data-testid list for e2e.
- Perf/SR budgets; usability timing.

## 13. Mockups (ASCII)
- Desktop expanded, sidebar collapsed, mobile drawer.
