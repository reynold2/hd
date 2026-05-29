import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const seedPath = resolve(__dirname, '../seed-test-data.json')

const seed = JSON.parse(readFileSync(seedPath, 'utf8'))
console.log('seed loaded:', {
  stores: seed.stores.length,
  users: seed.users.length,
  role_bindings: seed.role_bindings.length,
  generated_at: seed.generated_at
})
console.log('提示：请将这份 JSON 导入数据库或由后端初始化接口写入正式表。')
