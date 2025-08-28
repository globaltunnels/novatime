import { create } from 'zustand'
import type { Node, Edge, XYPosition } from '@xyflow/react'
import { nanoid } from '../utils/nanoid'

export type ToolRef = { id: string; name: string; params?: Record<string, any> }
export type ResourceRef = { id: string; name: string; location?: string }

export type CrewAIConfig = {
  mode?: 'chat' | 'agent' | 'tool' | 'workflow'
  system?: string
  tools?: ToolRef[]
  resources?: ResourceRef[]
  attachments?: { name: string; url?: string }[]
  model?: string
  params?: Record<string, any>
}

export type AppNodeData = {
  label: string
  typeKey: string
  icon?: string
  config: CrewAIConfig
}

type UIState = {
  inspectorOpen: boolean
  openInspector: (id?: string) => void
  closeInspector: () => void
  editingId?: string
}

const useUI = create<UIState>((set) => ({
  inspectorOpen: false,
  editingId: undefined,
  openInspector: (id) => set({ inspectorOpen: true, editingId: id }),
  closeInspector: () => set({ inspectorOpen: false, editingId: undefined })
}))

type GraphState = {
  nodes: Node<AppNodeData>[]
  edges: Edge[]
  selectedId?: string
  addNode: (typeKey: string, position: XYPosition) => void
  updateNodeData: (id: string, data: Partial<AppNodeData>) => void
  removeNode: (id: string) => void
  setNodes: (ns: Node<AppNodeData>[]) => void
  setEdges: (es: Edge[]) => void
  setSelected: (id?: string) => void
}

export const useGraph = create<GraphState>((set, get) => ({
  nodes: [
    { id: 'agent-1', type: 'agent', position: { x: 200, y: 100 }, data: { label: 'Agent', typeKey: 'agent', icon:'bot', config: { mode: 'agent', system: 'You are helpful.', model:'gpt-5-mini', tools: [] } } }
  ],
  edges: [],
  selectedId: undefined,
  addNode: (typeKey, position) => {
    const id = nanoid()
    const base = { label: typeKey[0].toUpperCase() + typeKey.slice(1), typeKey, icon: typeKey, config: { mode: typeKey === 'tool' ? 'tool' : 'chat', tools: [], resources: [], attachments: [] } }
    set({ nodes: [...get().nodes, { id, type: typeKey, position, data: base }] })
  },
  updateNodeData: (id, data) => {
    set({ nodes: get().nodes.map(n => n.id === id ? { ...n, data: { ...n.data, ...data } } : n) })
  },
  removeNode: (id) => {
    set({ nodes: get().nodes.filter(n => n.id !== id), edges: get().edges.filter(e => e.source !== id && e.target !== id) })
  },
  setNodes: (ns) => set({ nodes: ns }),
  setEdges: (es) => set({ edges: es }),
  setSelected: (id) => set({ selectedId: id })
}))

export default useUI
