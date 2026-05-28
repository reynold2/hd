import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { appendSessionRemark, createServiceCall, requestCheckout } from './api.mjs'

const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
})

test('posts customer remark append payload to the bound session endpoint', async () => {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options })
    return okJson({ number: 'A001', remark: '少辣' })
  }

  const payload = await appendSessionRemark('A001', { remark: '少辣', source: 'customer' })

  assert.equal(payload.remark, '少辣')
  assert.equal(calls[0].url, '/api/meal-sessions/A001/remarks')
  assert.equal(calls[0].options.method, 'POST')
  assert.equal(calls[0].options.headers['Content-Type'], 'application/json')
  assert.deepEqual(JSON.parse(calls[0].options.body), { remark: '少辣', source: 'customer' })
})

test('posts service calls and checkout requests with the expected methods', async () => {
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ ok: true })
  }

  await createServiceCall('A002', { message: '需要餐巾纸', source: 'customer' })
  await requestCheckout('A002')

  assert.equal(calls[0].url, '/api/meal-sessions/A002/service-calls')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { message: '需要餐巾纸', source: 'customer' })
  assert.equal(calls[1].url, '/api/meal-sessions/A002/actions/request-checkout')
  assert.equal(calls[1].options.method, 'POST')
})

function okJson(payload) {
  return {
    ok: true,
    async json() {
      return payload
    }
  }
}
