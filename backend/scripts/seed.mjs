import { writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const output = resolve(__dirname, '../seed-data.json')

const seedData = {
  stores: [
    {
      id: 1,
      name: '川香麻辣烫（中山店）',
      queue_prefix: 'A',
      business_status: 'open',
      business_hours: '10:00-22:30',
      address: '中山市东区中山三路88号',
      avg_prepare_minutes: 20
    }
  ],
  users: [
    { id: 1, username: 'admin_platform', display_name: '平台管理员', role: 'platform_admin', scope: 'platform', store_id: null, openid: null, password: '123456' },
    { id: 2, username: 'boss_store_001', display_name: '中山店老板', role: 'store_owner', scope: 'store', store_id: 1, openid: null, password: '123456' },
    { id: 3, username: 'cashier_store_001', display_name: '中山店收银', role: 'cashier', scope: 'store', store_id: 1, openid: null, password: '123456' },
    { id: 4, username: 'screen_store_001', display_name: '中山店大屏', role: 'screen', scope: 'store', store_id: 1, openid: null, password: '123456' },
    { id: 5, username: 'wx_customer_001', display_name: '顾客测试号', role: 'customer', scope: 'store', store_id: 1, openid: 'openid_customer_001', password: null },
    { id: 6, username: 'wx_boss_001', display_name: '小程序老板', role: 'boss', scope: 'store', store_id: 1, openid: 'openid_boss_001', password: null },
    { id: 7, username: 'wx_staff_001', display_name: '小程序服务员', role: 'staff', scope: 'store', store_id: 1, openid: 'openid_staff_001', password: null },
    { id: 8, username: 'wx_kitchen_001', display_name: '小程序制作', role: 'kitchen', scope: 'store', store_id: 1, openid: 'openid_kitchen_001', password: null },
    { id: 9, username: 'wx_cashier_001', display_name: '小程序收银', role: 'cashier', scope: 'store', store_id: 1, openid: 'openid_cashier_001', password: null }
  ],
  role_bindings: [
    { user_id: 1, role: 'platform_admin', store_id: null, openid: null, enabled: true },
    { user_id: 2, role: 'store_owner', store_id: 1, openid: null, enabled: true },
    { user_id: 3, role: 'cashier', store_id: 1, openid: null, enabled: true },
    { user_id: 4, role: 'screen', store_id: 1, openid: null, enabled: true },
    { user_id: 5, role: 'customer', store_id: 1, openid: 'openid_customer_001', enabled: true },
    { user_id: 6, role: 'boss', store_id: 1, openid: 'openid_boss_001', enabled: true },
    { user_id: 7, role: 'staff', store_id: 1, openid: 'openid_staff_001', enabled: true },
    { user_id: 8, role: 'kitchen', store_id: 1, openid: 'openid_kitchen_001', enabled: true },
    { user_id: 9, role: 'cashier', store_id: 1, openid: 'openid_cashier_001', enabled: true }
  ],
  meal_sessions: [
    {
      number: 'A018',
      store_id: 1,
      status: 'preparing',
      people_count: 2,
      remark: '少辣，不要葱',
      total_amount: '28.00',
      payment_method: null,
      cashier_id: null,
      items: [
        { name: '招牌麻辣烫', amount: '12.00', quantity: 1, source: 'customer', note: '', subtotal: '12.00' },
        { name: '宽粉', amount: '2.00', quantity: 1, source: 'customer', note: '', subtotal: '2.00' },
        { name: '牛肉串', amount: '14.00', quantity: 1, source: 'customer', note: '', subtotal: '14.00' }
      ]
    }
  ]
}

writeFileSync(output, `${JSON.stringify(seedData, null, 2)}\n`, 'utf8')
console.log(`Seed data written to ${output}`)
