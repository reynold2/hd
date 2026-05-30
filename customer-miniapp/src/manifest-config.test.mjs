import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

test('wechat miniapp manifest uses the production appid', () => {
  const manifest = JSON.parse(readFileSync(resolve(__dirname, 'manifest.json'), 'utf8'))

  assert.equal(manifest['mp-weixin'].appid, 'wxd9a562c913d7eaa5')
})
