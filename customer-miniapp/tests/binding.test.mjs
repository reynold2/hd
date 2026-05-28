import assert from 'node:assert/strict'
import { normalizeQueueNumber, parseBindingParams, parseH5BindingSearch } from '../src/binding.mjs'

assert.equal(normalizeQueueNumber(' a018 '), 'A018')
assert.deepEqual(parseBindingParams({ store_id: '2', number: 'b009' }), { storeId: 2, number: 'B009' })
assert.deepEqual(parseBindingParams({ storeId: '3', no: 'c010' }), { storeId: 3, number: 'C010' })
assert.deepEqual(parseBindingParams({ store: 'bad', scene: 'a001' }), { storeId: 1, number: 'A001' })
assert.deepEqual(parseH5BindingSearch('?store_id=4&number=d088'), { storeId: 4, number: 'D088' })
