import express from 'express'
import cors from 'cors'

const app = express()
app.use(cors())
app.use(express.json())

// Simple endpoint to simulate streaming response
app.post('/api/chat', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')

  const messages = [
    "Sure, here's some code...",
    "```python",
    "def fib(n):",
    "    a,b=0,1",
    "    for _ in range(n):",
    "        a,b=b,a+b",
    "    return a",
    "```",
    "Done!"
  ]
  let i = 0
  const interval = setInterval(() => {
    if (i >= messages.length) {
      clearInterval(interval)
      res.write("event: end\n")
      res.write("data: END\n\n")
      res.end()
    } else {
      res.write(`data: ${messages[i]}\n\n`)
      i++
    }
  }, 500)
})

const port = process.env.PORT || 4000
app.listen(port, () => {
  console.log('Mock AI backend listening on port', port)
})
