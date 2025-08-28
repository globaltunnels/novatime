
'use client'
import React, { useState } from 'react'
import ChatPane from './ChatPane'
import Composer from './Composer'

type Msg = { role: 'user'|'assistant', text?: string, codeBlocks?: {language:string; code:string}[] }

async function streamPrompt(prompt: string, onChunk: (chunk: string) => void) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value))
  }
}

export default function ChatViewShell(){
  const [messages, setMessages] = useState<Msg[]>([
    { role:'assistant', text:'Hi! Ask me to write or debug code.' }
  ])
  const onSend = async (text: string) => {
    if (!text.trim()) return
    setMessages(prev => [...prev, { role:'user', text }, { role:'assistant', text:'' }])
    let acc = ''
    await streamPrompt(text, (chunk) => {
      acc += chunk
      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = { role:'assistant', text: acc }
        return next
      })
    })
  }
  return (
    <main className="chat" role="main">
      <header className="chatHeader">
        <h1 contentEditable suppressContentEditableWarning>Untitled Chat</h1>
        <select data-testid="header-model" aria-label="Model">
          <option>gpt-5-mini</option>
          <option>gpt-4.1</option>
        </select>
        <button className="iconbtn" data-testid="header-export">⇪</button>
        <button className="iconbtn" data-testid="help-button">❔</button>
      </header>
      <ChatPane messages={messages}/>
      <Composer onSend={onSend}/>
    </main>
  )
}
