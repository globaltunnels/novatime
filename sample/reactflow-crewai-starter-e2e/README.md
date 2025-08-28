# React Flow + CrewAI-style Builder (Starter)

A compact, user-friendly workflow builder inspired by Make, Coze, n8n, and ComfyUI.
- **Drag & drop** nodes from a small **Palette** (icons only on narrow layouts).
- Nodes open a **Inspector Drawer** (form) with dynamic fields: **mode, system message,
  tools, resources, attachments** (CrewAI-like JSON).
- **Small footprint UI** with micro-icons and toolbars designed for tight spaces.
- **Undo/Redo** history.
- **Zustand** store (nodes/edges/actions).

## Quickstart
```bash
pnpm i   # or npm i / yarn
pnpm dev # http://localhost:5173
```

## Key UX
- Drag from palette → drop on canvas.
- Click node → small toolbar (✎ edit, ⊕ attach, ⌫ delete).
- Double-click node → open Inspector drawer (form).
- Edges: connect via handles; auto layout is manual (drag nodes).

## Extend
- Add your own node types in `src/flow/nodes/` and register in `nodeTypes`.
- Customize inspector schema in `src/flow/schemas.ts`.
