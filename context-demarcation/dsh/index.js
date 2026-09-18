/**
 * Thin DeepSeek Harness wrapper. The algorithm lives in ../core (Python).
 * This file only shells out and registers ctx.contextDemarcation + three tools.
 */
import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'context-demarcation'
export const inject = ['tools']
export const provide = 'contextDemarcation'

const here = path.dirname(fileURLToPath(import.meta.url))
export const CORE_ROOT = path.resolve(here, '..')

export function py(args, signal) {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', ['-m', 'core', ...args], {
      cwd: CORE_ROOT,
      env: { ...process.env, PYTHONPATH: CORE_ROOT },
    })
    let stdout = ''
    let stderr = ''
    child.stdout.on('data', (c) => { stdout += c })
    child.stderr.on('data', (c) => { stderr += c })
    const onAbort = () => child.kill('SIGTERM')
    if (signal) {
      if (signal.aborted) onAbort()
      else signal.addEventListener('abort', onAbort, { once: true })
    }
    child.on('error', reject)
    child.on('close', (code) => {
      if (code === 0) resolve(stdout)
      else reject(new Error(stderr.trim() || `demarcation exit ${code}`))
    })
  })
}

export function apply(ctx) {
  const svc = {
    index: (root, out, k = 1) => py(['index', root, '-o', out, '-k', String(k)]),
    getWindow: (out, id) => py(['window', out, '--id', id]).then(JSON.parse),
    getPlan: (out) => py(['plan', out]).then(JSON.parse),
  }
  ctx.contextDemarcation = svc
  const tools = [
    ['demarcation_index', 'Walk a folder of page images; write plan.json + windows.jsonl.', {
      root: { type: 'string', required: true },
      out: { type: 'string', required: true },
      k: { type: 'number' },
    }, (a, exec) => py(['index', a.root, '-o', a.out, '-k', String(a.k ?? 1)], exec?.signal)],
    ['demarcation_get_window', 'Return focus + neighbor ids for one unit.', {
      out: { type: 'string', required: true },
      id: { type: 'string', required: true },
    }, (a, exec) => py(['window', a.out, '--id', a.id], exec?.signal)],
    ['demarcation_get_plan', 'Print plan.json.', {
      out: { type: 'string', required: true },
    }, (a, exec) => py(['plan', a.out], exec?.signal)],
  ]
  for (const [name, description, parameters, execute] of tools) {
    ctx.tools.register({ name, description, parameters, execute })
  }
}
