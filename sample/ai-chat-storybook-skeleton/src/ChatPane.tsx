
'use client'
import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatPane(){
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
  const scrollToBottom = () => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }
  return (
    <section className="messages" ref={listRef} role="log" aria-live="polite">
      <MessageBubble role="user" text="Write a Python function that returns Fibonacci of n." />
      <div style={{height:8}}/>
      <MessageBubble role="assistant" codeBlocks={[{language:'python', code:'def fib(n):\n    a,b=0,1\n    for _ in range(n):\n        a,b=b,a+b\n    return a'}]} />
      <button className={"scrollFab " + (atBottom?'hidden':'')} data-testid="scroll-fab" onClick={scrollToBottom} aria-label="Scroll to bottom">↓ Latest</button>
    </section>
  )
}
