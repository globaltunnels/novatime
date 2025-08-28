import { Download, Upload } from 'lucide-react'
import { useGraph } from './store/ui'

export default function Toolbar(){
  const { nodes, edges, setNodes, setEdges } = useGraph()

  const exportGraph = () => {
    const data = JSON.stringify({ nodes, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'workflow.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const importGraph = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result))
        if (Array.isArray(parsed.nodes) && Array.isArray(parsed.edges)) {
          setNodes(parsed.nodes); setEdges(parsed.edges)
        } else {
          alert('Invalid graph JSON')
        }
      } catch (e) { alert('Failed to parse JSON') }
    }
    reader.readAsText(file)
  }

  const onPick = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'application/json'
    input.onchange = () => {
      const file = input.files?.[0]
      if (file) importGraph(file)
    }
    input.click()
  }

  return (
    <div style={{position:'absolute', left: 80, top: 8, display:'flex', gap: 8, zIndex: 10}}>
      <button className="iconbtn" data-testid="export-json" title="Export JSON" onClick={exportGraph}><Download size={14}/></button>
      <button className="iconbtn" data-testid="import-json" title="Import JSON" onClick={onPick}><Upload size={14}/></button>
    </div>
  )
}
