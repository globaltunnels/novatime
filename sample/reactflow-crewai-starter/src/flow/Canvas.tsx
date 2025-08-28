import { useCallback, useMemo } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap, addEdge, Connection, Edge, Node
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useGraph } from './store/ui'
import { AgentNode } from './nodes/AgentNode'
import { ToolNode } from './nodes/ToolNode'
import { ResourceNode } from './nodes/ResourceNode'
import { SystemNode } from './nodes/SystemNode'

export default function Canvas(){
  const { nodes, edges, setNodes, setEdges } = useGraph()
  const onNodesChange = useCallback((changes:any) => setNodes(nodes => nodes.map(n => {
    const change = changes.find((c:any) => c.id === n.id && c.type==='position')
    return change ? { ...n, position: change.position } : n
  })), [setNodes])
  const onEdgesChange = useCallback((changes:any) => {/* simple */}, [])
  const onConnect = useCallback((params: Edge | Connection) => setEdges(es => addEdge({ ...params, animated: true }, es)), [setEdges])
  const onDrop = useCallback((evt: React.DragEvent) => {
    evt.preventDefault()
    const typeKey = evt.dataTransfer.getData('application/reactflow')
    const bounds = (evt.target as HTMLElement).getBoundingClientRect()
    const position = { x: evt.clientX - bounds.left, y: evt.clientY - bounds.top }
    useGraph.getState().addNode(typeKey, position)
  }, [])
  const onDragOver = useCallback((evt: React.DragEvent) => { evt.preventDefault(); evt.dataTransfer.dropEffect = 'move' }, [])

  const nodeTypes = useMemo(() => ({
    agent: AgentNode, tool: ToolNode, resource: ResourceNode, system: SystemNode
  }), [])

  return (
    <div className="canvas">
      <div className="rf-wrapper" onDrop={onDrop} onDragOver={onDragOver}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <MiniMap className="minimap"/>
          <Background/>
          <Controls/>
        </ReactFlow>
      </div>
    </div>
  )
}
