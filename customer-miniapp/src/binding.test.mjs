import assert from 'node:assert/strict'
import { test } from 'node:test'

import { parseBindingParams, validateBoundSession } from './binding.mjs'

test('parses H5 scan query into store and uppercase number', () => {
  const params = parseBindingParams({}, '?store_id=2&number=b001&table=7')

  assert.deepEqual(params, { storeId: 2, number: 'B001', table: '7' })
})

test('page options override H5 search params for miniapp compatibility', () => {
  const params = parseBindingParams({ store_id: '3', number: 'c008' }, '?store_id=2&number=b001')

  assert.equal(params.storeId, 3)
  assert.equal(params.number, 'C008')
})

test('rejects session from another store', () => {
  assert.throws(
    () => validateBoundSession({ store_id: 2, number: 'B001', status: 'occupied' }, 1, 'B001'),
    /号码不属于当前门店/
  )
})

test('rejects completed or cancelled session binding', () => {
  assert.throws(
    () => validateBoundSession({ store_id: 1, number: 'A001', status: 'completed' }, 1, 'A001'),
    /号码已结束/
  )
  assert.throws(
    () => validateBoundSession({ store_id: 1, number: 'A002', status: 'cancelled' }, 1, 'A002'),
    /号码已结束/
  )
})
