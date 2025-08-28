
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
