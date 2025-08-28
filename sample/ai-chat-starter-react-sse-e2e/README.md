# AI Chat UI Starter (React + Vite)

Implements a minimal, spec-compliant shell:
- OpenAI-style chat (sidebar + chat pane + composer)
- Design tokens via CSS variables
- Events + store aligned to the AI spec
- Mock local store, no backend calls

## Quickstart
```bash
pnpm i   # or npm i / yarn
pnpm dev # http://localhost:3000
```


## Mock Backend
Run `pnpm server` (or npm run server) to start a local Express mock backend on port 4000.
POST to `/api/chat` returns a streaming event-source simulation of AI output.


## Mock Streaming Server (Express)
This starter includes a minimal Express server that streams chunked text for `/api/chat/stream`.

### Run both (two terminals)
```bash
# Terminal A (server)
pnpm server   # runs on http://localhost:4000

# Terminal B (vite dev)
pnpm dev      # http://localhost:3000 (proxied /api -> 4000)
```

### One command (spawns both)
```bash
pnpm dev:full
```


## SSE Endpoint
You can also test streaming via SSE:
```
POST /api/chat/sse
{ "prompt": "hello" }
```

## Stop Button
The composer shows a Stop ■ button while streaming. It cancels the current fetch via AbortController.


## SSE endpoint
- `GET /api/chat/sse?prompt=...` returns `text/event-stream`
- Client uses `EventSource` and sends a custom `done` event at end.
- Stop (■) closes `EventSource` (SSE) or aborts fetch (HTTP stream).
