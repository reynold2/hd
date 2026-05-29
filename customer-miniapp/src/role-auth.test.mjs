import assert from 'node:assert/strict'
import { test } from 'node:test'

import { buildRoleEntryUrl, getRoleEntry } from './role-auth.mjs'

test('builds customer role URL with default store and seeded queue number', () => {
  const url = buildRoleEntryUrl({
    role: 'customer',
    entry_page: '/pages/detail/detail',
    store_id: 1
  })

  assert.equal(url, '/pages/detail/detail?store_id=1&number=A018')
})

test('builds staff role URL with default store only', () => {
  const url = buildRoleEntryUrl({
    role: 'kitchen',
    entry_page: '/pages/kitchen/index',
    store_id: 1
  })

  assert.equal(url, '/pages/kitchen/index?store_id=1')
})

test('falls back to local role entry when backend omits entry page', () => {
  const role = getRoleEntry('cashier')
  const url = buildRoleEntryUrl({ role: role.code, store_id: 1 })

  assert.equal(url, '/pages/cashier/index?store_id=1')
})
