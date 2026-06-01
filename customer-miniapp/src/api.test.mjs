import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import {
  appendSessionRemark,
  confirmPayment,
  createServiceCall,
  handleServiceCall,
  requestCheckout,
  setApiBaseForTests,
  updateWechatPaymentQr,
  wechatLogin
} from './api.mjs'

const originalFetch = globalThis.fetch
const originalWx = globalThis.wx

afterEach(() => {
  globalThis.fetch = originalFetch
  globalThis.wx = originalWx
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

test('posts staff payment confirmation to the cashier endpoint', async () => {
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ number: 'A005', status: 'paid', payment_method: 'store_qr', cashier_id: 7 })
  }

  const payload = await confirmPayment('A005', 7)

  assert.equal(payload.status, 'paid')
  assert.equal(calls[0].url, '/api/meal-sessions/A005/actions/confirm-payment')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { payment_method: 'store_qr', cashier_id: 7 })
})

test('posts staff service handling resolution to the service call endpoint', async () => {
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ id: 12, status: 'handled', resolution: '已处理' })
  }

  const payload = await handleServiceCall(12, { staff_id: 7, resolution: '已处理' })

  assert.equal(payload.status, 'handled')
  assert.equal(calls[0].url, '/api/service-calls/12/handle')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { staff_id: 7, resolution: '已处理' })
})

test('posts boss wechat payment qr configuration to store endpoint', async () => {
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({
      wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg',
      wechat_payment_qr_name: '中山店微信收款码'
    })
  }

  const payload = await updateWechatPaymentQr(1, {
    wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg',
    wechat_payment_qr_name: '中山店微信收款码'
  })

  assert.equal(payload.wechat_payment_qr_name, '中山店微信收款码')
  assert.equal(calls[0].url, '/api/stores/1/payment-qr')
  assert.equal(calls[0].options.method, 'PATCH')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg',
    wechat_payment_qr_name: '中山店微信收款码'
  })
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

test('does not duplicate /api when H5 is deployed at the domain root', async () => {
  setApiBaseForTests('/api')
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ ok: true })
  }

  await requestCheckout('A004')

  assert.equal(calls[0].url, '/api/meal-sessions/A004/actions/request-checkout')
})

test('uses the production domain when a wechat miniapp build omits API base', async () => {
  setApiBaseForTests(null)
  globalThis.wx = {}
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({ openid: 'openid_staff_001', role: 'staff', store_id: 1 })
  }

  await wechatLogin({ openid: 'openid_staff_001', store_id: 1 })

  assert.equal(calls[0].url, 'https://hd.yxck3d.tech/api/auth/wechat-login')
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
