import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  getCustomerActionState,
  getCheckoutButtonState,
  buildServiceCallPayload
} from './customer-actions.mjs'

test('disables customer actions before binding and after terminal states', () => {
  assert.equal(getCustomerActionState(null).canSubmit, false)
  assert.match(getCustomerActionState(null).message, /请先绑定号码/)

  assert.deepEqual(getCustomerActionState({ status: 'paid' }), {
    canSubmit: false,
    message: '号码已收款，不能再追加内容'
  })
  assert.deepEqual(getCustomerActionState({ status: 'completed' }), {
    canSubmit: false,
    message: '号码已结束，请联系店员'
  })
})

test('describes checkout button state for pending and closed sessions', () => {
  assert.deepEqual(getCheckoutButtonState({ status: 'dining' }), {
    disabled: false,
    label: '呼叫结账',
    hint: '呼叫收银统一结账'
  })
  assert.deepEqual(getCheckoutButtonState({ status: 'checkout_requested' }), {
    disabled: true,
    label: '已呼叫',
    hint: '等待店员核算'
  })
  assert.equal(getCheckoutButtonState({ status: 'cancelled' }).disabled, true)
})

test('normalizes blank service messages to the default assistance text', () => {
  assert.deepEqual(buildServiceCallPayload('   '), {
    message: '需要店员协助',
    source: 'customer'
  })
  assert.deepEqual(buildServiceCallPayload('加一套餐具'), {
    message: '加一套餐具',
    source: 'customer'
  })
})
