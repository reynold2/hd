import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { apiUrl, setApiBaseForTests } from './api.ts'

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
