
import type { NodeProps } from '@xyflow/react'
import { Handle, Position } from '@xyflow/react'
import type { AppNodeData } from '../store/ui'
import { NodeChrome } from './NodeChrome'

export function ResourceNode(props: NodeProps<AppNodeData>) {
  const d = props.data
  return (
    <div className="node">
      <NodeChrome id={props.id} title={d.label} badge="Resource"/>
      <div className="body">
        <div><small>Items:</small> {(d.config.resources||[]).length}</div>
      </div>
      <Handle type="target" position={Position.Left}/>
      <Handle type="source" position={Position.Right}/>
    </div>
  )
}
