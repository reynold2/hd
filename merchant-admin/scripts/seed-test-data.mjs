import { writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const outputPath = resolve(__dirname, '../seed-test-data.json')

const stores = [
  {
    id: 1,
    name: '川香麻辣烫（中山店）',
    queue_prefix: 'A',
    business_status: 'open',
    business_hours: '10:00-22:30',
    address: '中山市东区中山三路88号',
    avg_prepare_minutes: 20
  }
]

const users = [
  { id: 1, username: 'admin_platform', display_name: '平台管理员', role: 'platform_admin', scope: 'platform', store_id: null, openid: null, password: '123456' },
  { id: 2, username: 'boss_store_001', display_name: '中山店老板', role: 'store_owner', scope: 'store', store_id: 1, openid: null, password: '123456' },
  { id: 3, username: 'cashier_store_001', display_name: '中山店收银', role: 'cashier', scope: 'store', store_id: 1, openid: null, password: '123456' },
  { id: 4, username: 'screen_store_001', display_name: '中山店大屏', role: 'screen', scope: 'store', store_id: 1, openid: null, password: '123456' },
  { id: 5, username: 'wx_customer_001', display_name: '顾客测试号', role: 'customer', scope: 'store', store_id: 1, openid: 'openid_customer_001', password: null },
  { id: 6, username: 'wx_boss_001', display_name: '小程序老板', role: 'boss', scope: 'store', store_id: 1, openid: 'openid_boss_001', password: null },
  { id: 7, username: 'wx_staff_001', display_name: '小程序服务员', role: 'staff', scope: 'store', store_id: 1, openid: 'openid_staff_001', password: null },
  { id: 8, username: 'wx_kitchen_001', display_name: '小程序制作', role: 'kitchen', scope: 'store', store_id: 1, openid: 'openid_kitchen_001', password: null },
  { id: 9, username: 'wx_cashier_001', display_name: '小程序收银', role: 'cashier', scope: 'store', store_id: 1, openid: 'openid_cashier_001', password: null }
]

const roleBindings = users
  .filter((user) => user.store_id || user.scope === 'platform')
  .map((user) => ({
    user_id: user.id,
    role: user.role,
    store_id: user.store_id,
    openid: user.openid,
    enabled: true
  }))

const seed = {
  generated_at: new Date().toISOString(),
  stores,
  users,
  role_bindings: roleBindings,
  notes: [
    '测试数据仅用于临时初始化，正式环境请由后端管理界面维护。',
    '小程序真实模式依赖 openid + 门店角色路由，不使用本地内置测试账号。'
  ]
}

writeFileSync(outputPath, `${JSON.stringify(seed, null, 2)}\n`, 'utf8')
console.log(`seed data written to ${outputPath}`)
console.log(JSON.stringify(seed, null, 2))
