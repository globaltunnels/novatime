import { Handle, Position, NodeProps } from '@xyflow/react'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useGraph } from '../store/ui'

export function NodeChrome({ id, title, badge }:{ id:string; title:string; badge?:string }){
  const { removeNode } = useGraph()
  const open = () => { const { openInspector } = require('../store/ui').default.getState(); openInspector(id) }
  const attach = () => { const { openInspector } = require('../store/ui').default.getState(); openInspector(id) }
  return (
    <div className="header">
      <div className="title">{title}</div>
      {badge && <span className="badge">{badge}</span>}
      <div className="toolbar" role="toolbar">
        <button className="iconbtn" title="Edit" onClick={open}><Pencil size={14}/></button>
        <button className="iconbtn" title="Attach" onClick={attach}><Plus size={14}/></button>
        <button className="iconbtn" title="Delete" onClick={()=>removeNode(id)}><Trash2 size={14}/></button>
      </div>
    </div>
  )
}
