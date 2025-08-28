
import type { NodeProps } from '@xyflow/react'
import { Handle, Position } from '@xyflow/react'
import type { AppNodeData } from '../store/ui'
import { NodeChrome } from './NodeChrome'

export function ToolNode(props: NodeProps<AppNodeData>) {
  const d = props.data
  return (
    <div className="node">
      <NodeChrome id={props.id} title={d.label} badge="Tool"/>
      <div className="body">
        <div><small>Name:</small> {d.label}</div>
        <div><small>Params:</small> {Object.keys(d.config.params||{}).length} keys</div>
      </div>
      <Handle type="target" position={Position.Left}/>
      <Handle type="source" position={Position.Right}/>
    </div>
  )
}
