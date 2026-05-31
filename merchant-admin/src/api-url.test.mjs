import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { apiUrl, setApiBaseForTests, updateWechatPaymentQr } from './api.ts'

afterEach(() => {
  setApiBaseForTests('')
})

test('keeps merchant API requests on /api by default', () => {
  assert.equal(apiUrl('/api/stores/1/catalog'), '/api/stores/1/catalog')
})

test('prefixes merchant API requests when an API base is configured', () => {
  setApiBaseForTests('/fh')

  assert.equal(apiUrl('/api/stores/1/catalog'), '/fh/api/stores/1/catalog')
})

test('does not duplicate /api when deployed at the domain root', () => {
  setApiBaseForTests('/api')

  assert.equal(apiUrl('/api/stores/1/catalog'), '/api/stores/1/catalog')
})

test('posts wechat payment qr settings to the store payment endpoint', async () => {
  const originalFetch = globalThis.fetch
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return {
      ok: true,
      async json() {
        return { wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg' }
      }
    }
  }

  try {
    const payload = await updateWechatPaymentQr(1, {
      wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg',
      wechat_payment_qr_name: '中山店微信收款码'
    })

    assert.equal(payload.wechat_payment_qr_url, 'https://cdn.example.com/store-1/wechat-pay.jpg')
    assert.equal(calls[0].url, '/api/stores/1/payment-qr')
    assert.equal(calls[0].options.method, 'PATCH')
    assert.deepEqual(JSON.parse(calls[0].options.body), {
      wechat_payment_qr_url: 'https://cdn.example.com/store-1/wechat-pay.jpg',
      wechat_payment_qr_name: '中山店微信收款码'
    })
  } finally {
    globalThis.fetch = originalFetch
  }
})
