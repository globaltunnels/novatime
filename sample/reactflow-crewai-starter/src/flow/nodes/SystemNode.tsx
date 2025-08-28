
import type { NodeProps } from '@xyflow/react'
import { Handle, Position } from '@xyflow/react'
import type { AppNodeData } from '../store/ui'
import { NodeChrome } from './NodeChrome'

export function SystemNode(props: NodeProps<AppNodeData>) {
  const d = props.data
  return (
    <div className="node">
      <NodeChrome id={props.id} title={d.label} badge="System"/>
      <div className="body">
        <div style={{maxHeight:64,overflow:'hidden',textOverflow:'ellipsis'}}>
          <small>System:</small> {d.config.system || '—'}
        </div>
      </div>
      <Handle type="target" position={Position.Left}/>
      <Handle type="source" position={Position.Right}/>
    </div>
  )
}
