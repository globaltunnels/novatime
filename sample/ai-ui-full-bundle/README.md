
# AI UI Full Bundle
**Generated:** 2025-08-27T22:34:13

This bundle aggregates the full spec docs and working starters.

## Contents
- **docs/**
  - AI_Programming_Assistant_Chat_UI_Spec_v1.3.md — canonical UI spec
  - Interface_Standard_Template.md — reusable baseline for other projects
  - ai_chat_ui_spec_bundle.zip — the two docs above as a separate zip
- **projects/**
  - ai-chat-storybook-skeleton.zip — standalone Storybook workbench
  - ai-chat-starter-react.zip — plain React + Vite starter
  - ai-chat-starter-react-stream.zip — React + Vite + Express (chunked fetch stream)
  - ai-chat-starter-react-sse.zip — React + Vite + Express with SSE + Stop (recommended)
  - reactflow-crewai-starter.zip — React Flow builder with small-icon nodes + inspector

## Quickstart
Unzip one project and follow its README:
```bash
# example
unzip projects/ai-chat-starter-react-sse.zip -d ./ai-chat-starter-react-sse
cd ai-chat-starter-react-sse
pnpm i
pnpm dev:full   # starts Express + Vite
```
