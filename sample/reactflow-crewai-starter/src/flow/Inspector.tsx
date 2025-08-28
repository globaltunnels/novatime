
import useUI, { useGraph, type AppNodeData, type ToolRef, type ResourceRef } from './store/ui'
import { X, Plus, Save, Wrench, HardDrive } from 'lucide-react'
import { useMemo } from 'react'

export default function Inspector({ open }:{ open:boolean }){
  const { closeInspector, editingId } = useUI()
  const { nodes, updateNodeData } = useGraph()
  const node = useMemo(()=> nodes.find(n => n.id === editingId), [nodes, editingId])
  if(!open || !node) return null
  const d = node.data as AppNodeData

  const set = (patch: Partial<AppNodeData>) => updateNodeData(node.id, patch)
  const setCfg = (patch: any) => updateNodeData(node.id, { config: { ...d.config, ...patch } })

  const addTool = () => setCfg({ tools: [ ...(d.config.tools||[]), { id: Date.now()+'' , name: 'tool', params: {} } as ToolRef ] })
  const addRes  = () => setCfg({ resources: [ ...(d.config.resources||[]), { id: Date.now()+'' , name: 'res', location: '' } as ResourceRef ] })

  return (
    <aside className="drawer" role="dialog" aria-modal="true">
      <header>
        <b>Edit Node</b>
        <button className="iconbtn" onClick={closeInspector} aria-label="Close"><X size={16}/></button>
      </header>

      <div className="form">
        <label>Label<input value={d.label} onChange={e=>set({ label: e.target.value })}/></label>
        <div className="row">
          <label>Mode
            <select value={d.config.mode||'chat'} onChange={e=>setCfg({ mode: e.target.value })}>
              <option value="chat">chat</option>
              <option value="agent">agent</option>
              <option value="tool">tool</option>
              <option value="workflow">workflow</option>
            </select>
          </label>
          <label>Model<input value={d.config.model||''} onChange={e=>setCfg({ model: e.target.value })} placeholder="gpt-5-mini"/></label>
        </div>
        <label>System Message
          <textarea rows={4} value={d.config.system||''} onChange={e=>setCfg({ system: e.target.value })} placeholder="You are a helpful assistant."/>
        </label>

        <div>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <b>Tools</b>
            <button className="iconbtn" onClick={addTool} title="Add tool"><Plus size={14}/></button>
          </div>
          <div style={{display:'flex',gap:6,flexWrap:'wrap',marginTop:6}}>
            {(d.config.tools||[]).map((t,i)=> (
              <span className="tag" key={i} title={t.name}><Wrench size={12}/> {t.name}</span>
            ))}
          </div>
        </div>

        <div>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <b>Resources</b>
            <button className="iconbtn" onClick={addRes} title="Add resource"><Plus size={14}/></button>
          </div>
          <div style={{display:'flex',gap:6,flexWrap:'wrap',marginTop:6}}>
            {(d.config.resources||[]).map((r,i)=> (
              <span className="tag" key={i} title={r.name}><HardDrive size={12}/> {r.name}</span>
            ))}
          </div>
        </div>

        <button className="iconbtn" onClick={closeInspector}><Save size={14}/> Save</button>
      </div>
    </aside>
  )
}
