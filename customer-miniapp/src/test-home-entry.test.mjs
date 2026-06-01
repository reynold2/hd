import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const source = readFileSync(new URL('./pages/test-home/index.vue', import.meta.url), 'utf8')

test('test home role cards use real wechat login before entering role pages', () => {
  assert.match(source, /wechatLogin/)
  assert.match(source, /saveRoleProfile\(profile\)/)
  assert.match(source, /uni\.navigateTo/)
})
