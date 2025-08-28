import { Bot, Wrench, HardDrive, Quote } from 'lucide-react'

const items = [
  { typeKey:'agent', icon: Bot, label:'Agent' },
  { typeKey:'tool', icon: Wrench, label:'Tool' },
  { typeKey:'resource', icon: HardDrive, label:'Resource' },
  { typeKey:'system', icon: Quote, label:'System' }
]

export default function Palette(){
  const onDragStart = (e: React.DragEvent, typeKey: string) => {
    e.dataTransfer.setData('application/reactflow', typeKey)
    e.dataTransfer.effectAllowed = 'move'
  }
  return (
    <aside className="palette" aria-label="Palette">
      {items.map(({typeKey, icon:Icon, label}) => (
        <div key={typeKey} className="group">
          <div className="item" data-testid={`palette-${typeKey}` } draggable onDragStart={(e) => onDragStart(e, typeKey)} title={label}>
            <Icon size={18} />
          </div>
        </div>
      ))}
    </aside>
  )
}
