import assert from 'node:assert/strict'
import { test } from 'node:test'
import { resolveAuthRedirect } from './router-auth.ts'

test('unauthenticated users see the standalone login entry first', () => {
  assert.equal(resolveAuthRedirect('/login', false), true)
  assert.equal(resolveAuthRedirect('/', false), '/login')
  assert.equal(resolveAuthRedirect('/home', false), '/login')
  assert.equal(resolveAuthRedirect('/cashier', false), '/login')
})

test('authenticated users can enter role workspaces', () => {
  assert.equal(resolveAuthRedirect('/', true), true)
  assert.equal(resolveAuthRedirect('/home', true), true)
  assert.equal(resolveAuthRedirect('/cashier', true), true)
})
