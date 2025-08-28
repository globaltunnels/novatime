
'use client'
import React, { useState } from 'react'

export default function Composer(){
  const [text, setText] = useState('')
  const send = (e?: React.FormEvent) => {
    e?.preventDefault()
    if(!text.trim()) return
    console.log('SEND', text)
    setText('')
  }
  return (
    <form className="composer" role="form" onSubmit={send}>
      <textarea data-testid="composer-input" aria-label="Message" value={text} onChange={e=>setText(e.target.value)} placeholder="Message…"/>
      <div className="actions">
        <button className="iconbtn" type="button" data-testid="composer-attach" aria-label="Attach file">📎</button>
        <button className="iconbtn" type="button" data-testid="composer-code-toggle" aria-label="Toggle code mode">&lt;&gt;</button>
        <button className="iconbtn hidden" type="button" data-testid="composer-stop" aria-label="Stop">■</button>
        <button className="iconbtn" type="submit" data-testid="composer-send" aria-label="Send">▶</button>
      </div>
    </form>
  )
}
