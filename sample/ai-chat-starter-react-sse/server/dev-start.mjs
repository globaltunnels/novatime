
import { spawn } from 'node:child_process'
const run = (cmd, args, name) => {
  const p = spawn(cmd, args, { stdio: 'inherit', shell: process.platform === 'win32' })
  p.on('close', code => process.exit(code ?? 0))
  return p
}
run('node', ['server/server.mjs'], 'server')
run('vite', [], 'vite')
