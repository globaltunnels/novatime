
import type { NodeProps } from '@xyflow/react'
import { Handle, Position } from '@xyflow/react'
import type { AppNodeData } from '../store/ui'
import { NodeChrome } from './NodeChrome'

export function AgentNode(props: NodeProps<AppNodeData>) {
  const d = props.data
  return (
    <div className="node">
      <NodeChrome id={props.id} title={d.label} badge="Agent"/>
      <div className="body">
        <div><small>Mode:</small> {d.config.mode || 'agent'}</div>
        <div><small>Model:</small> {d.config.model || 'gpt-5-mini'}</div>
        <div style={{display:'flex',gap:6,flexWrap:'wrap',marginTop:6}}>
          {(d.config.tools||[]).slice(0,3).map((t,i)=>(<span key={i} className="tag">{t.name}</span>))}
        </div>
      </div>
      <Handle type="target" position={Position.Left}/>
      <Handle type="source" position={Position.Right}/>
    </div>
  )
}
