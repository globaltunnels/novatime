import React from 'react'
import { StoreProvider } from './lib/store'
import Sidebar from './components/Sidebar'
import ChatViewShell from './components/_ChatViewShell'

export default function App() {
  return (
    <StoreProvider>
      <div className="app">
        <Sidebar/>
        <ChatViewShell/>
      </div>
    </StoreProvider>
  )
}
