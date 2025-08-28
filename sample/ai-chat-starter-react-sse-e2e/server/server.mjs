import express from 'express'
import cors from 'cors'

const app = express()
app.use(cors())
app.use(express.json({ limit: '1mb' }))

app.get('/api/health', (_req, res) => res.json({ ok: true }))

// Simple streaming endpoint (chunked text).
// Client POSTs: { prompt: string }
app.post('/api/chat/stream', async (req, res) => {
  const { prompt } = req.body || {}
  const text = (prompt && String(prompt).trim())
    ? `Sure. Here's a mocked response to: "${prompt}".\n\n` +
      "```python\n" +
      "def fib(n):\n" +
      "    a, b = 0, 1\n" +
      "    for _ in range(n):\n" +
      "        a, b = b, a + b\n" +
      "    return a\n" +
      "```\n"
    : "Hello! Provide a prompt to see streaming in action.\n"
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  res.setHeader('Transfer-Encoding', 'chunked')
  res.setHeader('Cache-Control', 'no-cache')
  const delay = (ms) => new Promise(r => setTimeout(r, ms))
  const tokens = text.split(/(\s+)/) // keep spaces as tokens for demo
  for (const t of tokens) {
    res.write(t)
    await delay(30)
  }
  res.end()
})

const PORT = process.env.PORT || 4000
app.listen(PORT, () => {
  console.log(`[mock-server] running on http://localhost:${PORT}`)
})


// SSE endpoint: streams one token at a time via Server-Sent Events
app.post('/api/chat/sse', async (req, res) => {
  const { prompt } = req.body || {}
  const text = (prompt && String(prompt).trim())
    ? `SSE response for: ${prompt}\n`
    : "Hello from SSE endpoint.\n"
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders()
  const delay = (ms) => new Promise(r => setTimeout(r, ms))
  const tokens = text.split(/(\s+)/)
  for (const t of tokens) {
    res.write(`data: ${t}\n\n`)
    await delay(50)
  }
  res.write("event: end\n")
  res.write("data: [DONE]\n\n")
  res.end()
})

// Stop signal simulation
let activeStreams = {}
app.post('/api/chat/stream/start', (req, res) => {
  const id = Date.now().toString(36)
  activeStreams[id] = true
  res.json({ streamId: id })
})
app.post('/api/chat/stream/stop', (req, res) => {
  const { streamId } = req.body || {}
  if (streamId && activeStreams[streamId]) {
    delete activeStreams[streamId]
    res.json({ stopped: true })
  } else {
    res.json({ stopped: false })
  }
})
