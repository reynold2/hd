import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  buildProductionColumns,
  getProductionPrimaryAction,
  getProductionQueue
} from './production-workbench.ts'

const sessions = [
  { number: 'A001', status: 'occupied', remark: '少辣', total_amount: '12.00' },
  { number: 'A002', status: 'preparing', remark: '不要葱', total_amount: '18.00' },
  { number: 'A003', status: 'called', remark: '', total_amount: '20.00' },
  { number: 'A004', status: 'checkout_requested', remark: '待收银', total_amount: '30.00' },
  { number: 'A005', status: 'skipped', remark: '稍后做', total_amount: '8.00' }
]

test('filters production queue to kitchen-facing statuses in stable order', () => {
  assert.deepEqual(
    getProductionQueue(sessions).map((session) => session.number),
    ['A001', 'A002', 'A003', 'A005']
  )
})

test('maps production statuses into kanban columns', () => {
  const columns = buildProductionColumns(sessions)

  assert.deepEqual(columns.map((column) => column.key), ['occupied', 'preparing', 'called', 'skipped'])
  assert.deepEqual(columns[0].items.map((item) => item.number), ['A001'])
  assert.deepEqual(columns[1].items.map((item) => item.number), ['A002'])
  assert.deepEqual(columns[2].items.map((item) => item.number), ['A003'])
  assert.deepEqual(columns[3].items.map((item) => item.number), ['A005'])
})

test('returns the expected primary kitchen action for each status', () => {
  assert.deepEqual(getProductionPrimaryAction({ status: 'occupied' }), {
    action: 'start-preparing',
    label: '开始制作',
    type: 'primary'
  })
  assert.deepEqual(getProductionPrimaryAction({ status: 'preparing' }), {
    action: 'call',
    label: '制作完成并叫号',
    type: 'success'
  })
  assert.deepEqual(getProductionPrimaryAction({ status: 'called' }), {
    action: 'mark-dining',
    label: '确认取餐',
    type: 'success'
  })
  assert.deepEqual(getProductionPrimaryAction({ status: 'skipped' }), {
    action: 'resume',
    label: '恢复排队',
    type: 'warning'
  })
})
