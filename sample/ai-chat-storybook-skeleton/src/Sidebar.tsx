
'use client'
import React, { useEffect, useState } from 'react'
import { useStore } from '../store'

export default function Sidebar() {
  const { conversations, currentId, setCurrent, newChat } = useStore()
  const [collapsed, setCollapsed] = useState<boolean>(false)
  useEffect(() => {
    const v = localStorage.getItem('ui.sidebarCollapsed')
    setCollapsed(v === 'true')
  }, [])
  useEffect(() => {
    document.querySelector('.app')?.classList.toggle('sidebar-collapsed', collapsed)
  }, [collapsed])
  const toggle = () => {
    const next = !collapsed
    setCollapsed(next); localStorage.setItem('ui.sidebarCollapsed', String(next))
    document.querySelector('.app')?.classList.toggle('sidebar-collapsed', next)
  }
  return (
    <aside className="sidebar" data-testid="sidebar" aria-label="Sidebar">
      <button className="iconbtn collapseToggle" data-testid="sidebar-toggle" onClick={toggle} aria-label="Collapse sidebar">☰</button>
      <div className="row" style={{marginTop:8}}>
        <button className="iconbtn" onClick={() => newChat()}>+ New Chat</button>
        <input type="search" placeholder="Search" aria-label="Search conversations" />
      </div>
      <div className="threads" role="list">
        {conversations.map(c => (
          <button
            key={c.id}
            className="thread"
            data-testid="thread-item"
            aria-current={currentId === c.id}
            onClick={() => setCurrent(c.id)}
            title={c.title}
          >
            💬 {collapsed ? '' : c.title}
          </button>
        ))}
      </div>
      <div className="threads" style={{marginTop:16}}>
        <button className="iconbtn" onClick={() => location.assign('/app/settings/general')}>My Settings</button>
        <button className="iconbtn" onClick={() => location.assign('/app/account/profile')}>Account</button>
      </div>
    </aside>
  )
}
