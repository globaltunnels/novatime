
'use client'
import React from 'react'

export default function CodeBlock({ language, code }: { language: string; code: string }) {
  const copy = async () => {
    await navigator.clipboard.writeText(code)
    alert('Copied')
  }
  return (
    <div className="code">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6}}>
        <span>{language}</span>
        <button className="iconbtn" data-testid="copy-code" onClick={copy} aria-label={`Copy code block (${language})`}>📋 Copy</button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  )
}
