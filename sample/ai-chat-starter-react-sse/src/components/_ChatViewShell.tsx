
'use client'
import React, { useRef, useState } from 'react'
import ChatPane from './ChatPane'
import Composer from './Composer'

type Msg = { role: 'user'|'assistant', text?: string, codeBlocks?: {language:string; code:string}[] }

async function streamHTTP(prompt: string, onChunk: (chunk: string) => void, signal: AbortSignal) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
    signal
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value))
  }
}

function streamSSE(prompt: string, onChunk: (chunk: string) => void) {
  const es = new EventSource(`/api/chat/sse?prompt=${encodeURIComponent(prompt)}`)
  es.onmessage = (ev) => onChunk(ev.data || '')
  es.addEventListener('done', () => { es.close() })
  es.onerror = () => { es.close() }
  return es
}

export default function ChatViewShell(){
  const [messages, setMessages] = useState<Msg[]>([
    { role:'assistant', text:'Hi! Ask me to write or debug code.' }
  ])
  const [isStreaming, setStreaming] = useState(false)
  const transportRef = useRef<'sse'|'http'>('sse')
  const abortRef = useRef<AbortController | null>(null)
  const esRef = useRef<EventSource | null>(null)

  const onSend = async (text: string) => {
    if (!text.trim() || isStreaming) return
    setMessages(prev => [...prev, { role:'user', text }, { role:'assistant', text:'' }])
    setStreaming(true)

    let acc = ''
    const onChunk = (chunk: string) => {
      acc += chunk
      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = { role:'assistant', text: acc }
        return next
      })
    }

    try {
      if (transportRef.current === 'sse' && typeof window.EventSource !== 'undefined') {
        esRef.current = streamSSE(text, onChunk)
        // When SSE ends, we setStreaming(false) in a small timeout to allow UI update
        const closer = () => { setStreaming(false); esRef.current = null }
        // Attach once-only listener for completion
        const doneHandler = () => { closer() }
        // Since we send a custom 'done' event, rely on onerror/close as well
        const es = esRef.current!
        es.addEventListener('done', doneHandler)
        es.onerror = () => { closer() }
      } else {
        const ac = new AbortController()
        abortRef.current = ac
        await streamHTTP(text, onChunk, ac.signal)
        setStreaming(false)
        abortRef.current = null
      }
    } catch (e) {
      console.error('stream error', e)
      setStreaming(false)
      abortRef.current = null
      if (esRef.current) { esRef.current.close(); esRef.current = null }
    }
  }

  const onStop = () => {
    if (transportRef.current === 'sse' && esRef.current) {
      esRef.current.close()
      esRef.current = null
      setStreaming(false)
    } else if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
      setStreaming(false)
    }
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
      <Composer onSend={onSend} streaming={isStreaming} onStop={onStop}/>
    </main>
  )
}
