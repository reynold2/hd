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

test('cashier role falls back to the merged staff workbench', () => {
  const role = getRoleEntry('cashier')
  const url = buildRoleEntryUrl({ role: role.code, store_id: 1 })

  assert.equal(url, '/pages/staff/index?store_id=1')
})

test('cashier backend entry page is normalized to the merged staff workbench', () => {
  const url = buildRoleEntryUrl({
    role: 'cashier',
    entry_page: '/pages/cashier/index',
    store_id: 1
  })

  assert.equal(url, '/pages/staff/index?store_id=1')
})
