import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { appendSessionRemark, createServiceCall, requestCheckout, setApiBaseForTests, wechatLogin } from './api.mjs'

const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
  setApiBaseForTests('')
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

test('prefixes customer API requests when an API base is configured', async () => {
  setApiBaseForTests('/fh')
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ ok: true })
  }

  await requestCheckout('A003')

  assert.equal(calls[0].url, '/fh/api/meal-sessions/A003/actions/request-checkout')
})

test('posts real wechat login payload to backend auth endpoint', async () => {
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ openid: 'openid_customer_001', role: 'customer', store_id: 1 })
  }

  const payload = await wechatLogin({ openid: 'openid_customer_001', store_id: 1 })

  assert.equal(payload.role, 'customer')
  assert.equal(calls[0].url, '/api/auth/wechat-login')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { openid: 'openid_customer_001', store_id: 1 })
})

test('uses uni.request when fetch is unavailable in miniapp runtime', async () => {
  const calls = []
  globalThis.fetch = undefined
  globalThis.uni = {
    request(options) {
      calls.push(options)
      options.success({
        statusCode: 200,
        data: { openid: 'openid_staff_001', role: 'staff', store_id: 1 }
      })
    }
  }
  setApiBaseForTests('http://8.141.105.10/fh')

  const payload = await wechatLogin({ openid: 'openid_staff_001', store_id: 1 })

  assert.equal(payload.role, 'staff')
  assert.equal(calls[0].url, 'http://8.141.105.10/fh/api/auth/wechat-login')
  assert.equal(calls[0].method, 'POST')
  assert.deepEqual(calls[0].data, { openid: 'openid_staff_001', store_id: 1 })
})

function okJson(payload) {
  return {
    ok: true,
    async json() {
      return payload
    }
  }
}
