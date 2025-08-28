
'use client'
import React from 'react'
import CodeBlock from './CodeBlock'

export default function MessageBubble({ role, text, codeBlocks }:{ role:'user'|'assistant'|'system'; text?:string; codeBlocks?:{language:string;code:string}[] }){
  return (
    <div className={"bubble " + (role==='user'?'user':'')} data-testid="chat-message" role="article">
      {text && <div style={{whiteSpace:'pre-wrap'}}>{text}</div>}
      {codeBlocks?.map((b, i) => <div key={i} style={{marginTop:8}}><CodeBlock language={b.language} code={b.code}/></div>)}
      {role==='assistant' && (
        <div className="msgActions" data-testid="message-actions" aria-label="Message actions">
          <button className="iconbtn" data-testid="regen">Regenerate</button>
          <button className="iconbtn" data-testid="feedback-up" aria-label="Thumbs up">👍</button>
          <button className="iconbtn" data-testid="feedback-down" aria-label="Thumbs down">👎</button>
          <button className="iconbtn" data-testid="delete-message">Delete</button>
        </div>
      )}
    </div>
  )
}
