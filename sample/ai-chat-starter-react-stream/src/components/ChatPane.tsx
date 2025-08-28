
'use client'
import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatPane({ messages }:{ messages:{role:'user'|'assistant', text?:string, codeBlocks?:{language:string;code:string}[]}[] }){
  const listRef = useRef<HTMLDivElement>(null)
  const [atBottom, setAtBottom] = useState(true)
  useEffect(() => {
    const el = listRef.current
    if(!el) return
    const onScroll = () => {
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120
      setAtBottom(nearBottom)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [])
  useEffect(() => {
    if (atBottom) listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, atBottom])
  const scrollToBottom = () => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  return (
    <section className="messages" ref={listRef} role="log" aria-live="polite">
      {messages.map((m,i) => (
        <div key={i} style={{marginBottom:12}}>
          <MessageBubble role={m.role} text={m.text} codeBlocks={m.codeBlocks}/>
        </div>
      ))}
      <button className={"scrollFab " + (atBottom?'hidden':'')} data-testid="scroll-fab" onClick={scrollToBottom} aria-label="Scroll to bottom">↓ Latest</button>
    </section>
  )
}
