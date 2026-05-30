import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { loginAdmin, setAuthApiBaseForTests } from './auth.ts'

const originalFetch = globalThis.fetch
const originalLocalStorage = globalThis.localStorage

afterEach(() => {
  globalThis.fetch = originalFetch
  globalThis.localStorage = originalLocalStorage
  setAuthApiBaseForTests('')
})

test('prefixes admin login requests when an API base is configured', async () => {
  setAuthApiBaseForTests('/fh')
  const calls = []
  globalThis.localStorage = { setItem() {} }
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return okJson({
      token: 'token_admin_platform',
      profile: { username: 'admin_platform', displayName: '平台管理员', role: 'platform_admin' },
      redirect: '/platform'
    })
  }

  const payload = await loginAdmin('admin_platform', '123456')

  assert.equal(payload.redirect, '/platform')
  assert.equal(calls[0].url, '/fh/api/admin/login')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { username: 'admin_platform', password: '123456' })
})

function okJson(payload) {
  return {
    ok: true,
    async json() {
      return payload
    }
  }
}
