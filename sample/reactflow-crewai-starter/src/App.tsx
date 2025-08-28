import { ReactFlowProvider } from '@xyflow/react'
import Canvas from './flow/Canvas'
import Palette from './flow/Palette'
import Inspector from './flow/Inspector'
import useUI from './flow/store/ui'

export default function App(){
  const { inspectorOpen } = useUI()
  return (
    <ReactFlowProvider>
      <div className="layout">
        <Palette/>
        <Canvas/>
        <Inspector open={inspectorOpen}/>
      </div>
    </ReactFlowProvider>
  )
}
