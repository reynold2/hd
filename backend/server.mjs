import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const seedPath = resolve('./backend/seed-data.json')
let data = loadSeed()

function loadSeed() {
  try {
    const raw = readFileSync(seedPath, 'utf8')
    return JSON.parse(raw)
  } catch {
    return {
      stores: [],
      users: [],
      role_bindings: [],
      meal_sessions: []
    }
  }
}

function writeJson(res, statusCode, payload) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(payload))
}

function readBody(req) {
  return new Promise((resolveBody) => {
    const chunks = []
    req.on('data', (chunk) => chunks.push(chunk))
    req.on('end', () => {
      const text = Buffer.concat(chunks).toString('utf8')
      resolveBody(text ? JSON.parse(text) : {})
    })
  })
}

function getStore(storeId) {
  return data.stores.find((store) => store.id === Number(storeId)) || data.stores[0]
}

function getMeals(storeId) {
  return data.meal_sessions.filter((session) => session.store_id === Number(storeId))
}

function getMeal(number) {
  return data.meal_sessions.find((session) => session.number === number)
}

function loginResponse(user) {
  const store = user.store_id ? getStore(user.store_id) : null
  const redirectMap = {
    platform_admin: '/platform',
    store_owner: '/store',
    cashier: '/cashier',
    screen: '/screen'
  }
  return {
    token: `token_${user.username}`,
    profile: {
      username: user.username,
      displayName: user.display_name,
      role: user.role,
      storeId: user.store_id || undefined,
      storeName: store?.name
    },
    redirect: redirectMap[user.role] || '/'
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url || '/', 'http://127.0.0.1')
  if (req.method === 'POST' && url.pathname === '/api/admin/login') {
    const body = await readBody(req)
    const user = data.users.find((item) => item.username === body.username && item.password === body.password)
    if (!user) return writeJson(res, 401, { message: '账号或密码错误' })
    return writeJson(res, 200, loginResponse(user))
  }

  if (req.method === 'POST' && url.pathname === '/api/admin/seed-test-data') {
    data = loadSeed()
    return writeJson(res, 200, { ok: true, message: 'seed loaded' })
  }

  if (req.method === 'POST' && url.pathname === '/api/auth/wechat-login') {
    const body = await readBody(req)
    const user = data.users.find((item) => item.openid === body.openid)
    if (!user) return writeJson(res, 404, { message: 'openid 未绑定角色' })
    return writeJson(res, 200, loginResponse(user))
  }

  if (req.method === 'POST' && url.pathname === '/api/auth/by-openid') {
    const body = await readBody(req)
    const user = data.users.find((item) => item.openid === body.openid)
    if (!user) return writeJson(res, 404, { message: '未找到 openid 对应身份' })
    return writeJson(res, 200, { user, store: getStore(user.store_id || 1) })
  }

  if (req.method === 'GET' && url.pathname === '/api/roles/resolve') {
    const openid = url.searchParams.get('openid')
    const user = data.users.find((item) => item.openid === openid)
    if (!user) return writeJson(res, 404, { message: '未找到角色' })
    return writeJson(res, 200, { user, store: getStore(user.store_id || 1), redirect: loginResponse(user).redirect })
  }

  const storeMatch = url.pathname.match(/^\/api\/stores\/(\d+)\/catalog$/)
  if (req.method === 'GET' && storeMatch) {
    const store = getStore(storeMatch[1])
    return writeJson(res, 200, {
      store,
      dishes: [
        { id: 1, name: '招牌麻辣烫', category: '主食', price: '12.00', available: true },
        { id: 2, name: '牛肉串', category: '小吃', price: '15.00', available: true },
        { id: 3, name: '宽粉', category: '加料', price: '2.00', available: true },
        { id: 4, name: '冰粉', category: '甜品', price: '6.00', available: true }
      ],
      staff: []
    })
  }

  const queueMatch = url.pathname.match(/^\/api\/stores\/(\d+)\/queue$/)
  if (req.method === 'GET' && queueMatch) {
    return writeJson(res, 200, getMeals(queueMatch[1]))
  }

  const pendingMatch = url.pathname.match(/^\/api\/stores\/(\d+)\/cashier\/pending$/)
  if (req.method === 'GET' && pendingMatch) {
    return writeJson(res, 200, getMeals(pendingMatch[1]).filter((item) => item.status === 'checkout_requested'))
  }

  const mealMatch = url.pathname.match(/^\/api\/meal-sessions\/([A-Z0-9-]+)$/)
  if (req.method === 'GET' && mealMatch) {
    const meal = getMeal(mealMatch[1])
    if (!meal) return writeJson(res, 404, { message: '号码不存在' })
    return writeJson(res, 200, meal)
  }

  return writeJson(res, 404, { message: 'not found' })
})

server.listen(3000, () => {
  console.log('Backend running on http://127.0.0.1:3000')
})
