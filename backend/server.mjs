import { createServer } from 'node:http'
import { readFileSync, writeFileSync } from 'node:fs'
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
      meal_sessions: [],
      invitations: []
    }
  }
}

function persist() {
  writeFileSync(seedPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8')
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
      storeName: store?.name,
      avatarUrl: user.avatar_url || ''
    },
    redirect: redirectMap[user.role] || '/'
  }
}

function nextUserId() {
  return data.users.length ? Math.max(...data.users.map((user) => user.id)) + 1 : 1
}

function upsertRoleBinding(user, source = 'api') {
  const existingIndex = data.role_bindings.findIndex((binding) => binding.user_id === user.id)
  const payload = {
    user_id: user.id,
    role: user.role,
    store_id: user.store_id || null,
    openid: user.openid || null,
    enabled: true,
    source
  }
  if (existingIndex >= 0) data.role_bindings[existingIndex] = payload
  else data.role_bindings.push(payload)
}

function upsertInvitation(token, payload) {
  const existingIndex = data.invitations.findIndex((item) => item.token === token)
  if (existingIndex >= 0) data.invitations[existingIndex] = { ...data.invitations[existingIndex], ...payload }
  else data.invitations.push({ token, ...payload })
}

function findUserById(id) {
  return data.users.find((user) => user.id === Number(id))
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

  if (req.method === 'GET' && url.pathname === '/api/admin/users') {
    return writeJson(res, 200, data.users)
  }

  if (req.method === 'POST' && url.pathname === '/api/admin/users') {
    const body = await readBody(req)
    if (!body.username || !body.display_name) return writeJson(res, 400, { message: '账号和显示名称不能为空' })
    if (data.users.some((user) => user.username === body.username)) return writeJson(res, 409, { message: '账号已存在' })
    const user = {
      id: nextUserId(),
      username: body.username,
      display_name: body.display_name,
      avatar_url: body.avatar_url || '',
      role: body.role || 'staff',
      store_id: body.store_id || null,
      openid: body.openid || null,
      password: body.password || '123456',
      status: body.status || 'enabled'
    }
    data.users.push(user)
    upsertRoleBinding(user, 'admin-create')
    persist()
    return writeJson(res, 201, user)
  }

  const userMatch = url.pathname.match(/^\/api\/admin\/users\/(\d+)$/)
  if (userMatch && req.method === 'PATCH') {
    const body = await readBody(req)
    const user = findUserById(userMatch[1])
    if (!user) return writeJson(res, 404, { message: '用户不存在' })
    Object.assign(user, {
      username: body.username ?? user.username,
      display_name: body.display_name ?? user.display_name,
      avatar_url: body.avatar_url ?? user.avatar_url,
      role: body.role ?? user.role,
      store_id: body.store_id ?? user.store_id,
      openid: body.openid ?? user.openid,
      status: body.status ?? user.status
    })
    upsertRoleBinding(user, 'admin-update')
    persist()
    return writeJson(res, 200, user)
  }

  const userDeleteMatch = url.pathname.match(/^\/api\/admin\/users\/(\d+)$/)
  if (userDeleteMatch && req.method === 'DELETE') {
    data.users = data.users.filter((user) => user.id !== Number(userDeleteMatch[1]))
    data.role_bindings = data.role_bindings.filter((binding) => binding.user_id !== Number(userDeleteMatch[1]))
    persist()
    return writeJson(res, 200, { ok: true })
  }

  const userPasswordMatch = url.pathname.match(/^\/api\/admin\/users\/(\d+)\/password$/)
  if (userPasswordMatch && req.method === 'PATCH') {
    const body = await readBody(req)
    const user = findUserById(userPasswordMatch[1])
    if (!user) return writeJson(res, 404, { message: '用户不存在' })
    user.password = body.password || user.password
    persist()
    return writeJson(res, 200, { ok: true })
  }

  const userAvatarMatch = url.pathname.match(/^\/api\/admin\/users\/(\d+)\/avatar$/)
  if (userAvatarMatch && req.method === 'PATCH') {
    const body = await readBody(req)
    const user = findUserById(userAvatarMatch[1])
    if (!user) return writeJson(res, 404, { message: '用户不存在' })
    user.avatar_url = body.avatar_url || user.avatar_url
    persist()
    return writeJson(res, 200, { ok: true })
  }

  const wechatBindingMatch = url.pathname.match(/^\/api\/admin\/users\/(\d+)\/wechat-binding$/)
  if (wechatBindingMatch && req.method === 'PATCH') {
    const body = await readBody(req)
    const user = findUserById(wechatBindingMatch[1])
    if (!user) return writeJson(res, 404, { message: '用户不存在' })
    user.openid = body.openid || user.openid
    upsertRoleBinding(user, 'wechat-binding')
    persist()
    return writeJson(res, 200, { ok: true, openid: user.openid })
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

  const invitationCreateMatch = url.pathname.match(/^\/api\/stores\/(\d+)\/employee-invitations$/)
  if (invitationCreateMatch && req.method === 'POST') {
    const body = await readBody(req)
    const token = `invite_${invitationCreateMatch[1]}_${Date.now()}`
    const invite = {
      token,
      store_id: Number(invitationCreateMatch[1]),
      role_scope: body.role_scope || ['staff', 'cashier', 'kitchen'],
      created_by: body.created_by || 0,
      expires_at: body.expires_at || null,
      status: 'active'
    }
    upsertInvitation(token, invite)
    persist()
    return writeJson(res, 201, invite)
  }

  const invitationMatch = url.pathname.match(/^\/api\/employee-invitations\/([^/]+)$/)
  if (invitationMatch && req.method === 'GET') {
    const invite = data.invitations.find((item) => item.token === invitationMatch[1])
    if (!invite) return writeJson(res, 404, { message: '邀请不存在' })
    return writeJson(res, 200, invite)
  }

  const invitationAcceptMatch = url.pathname.match(/^\/api\/employee-invitations\/([^/]+)\/accept$/)
  if (invitationAcceptMatch && req.method === 'POST') {
    const invite = data.invitations.find((item) => item.token === invitationAcceptMatch[1])
    if (!invite) return writeJson(res, 404, { message: '邀请不存在' })
    const body = await readBody(req)
    if (!body.username || !body.display_name) return writeJson(res, 400, { message: '账号和显示名称不能为空' })
    let user = data.users.find((item) => item.username === body.username)
    if (!user) {
      user = {
        id: nextUserId(),
        username: body.username,
        display_name: body.display_name,
        avatar_url: body.avatar_url || '',
        role: body.role || 'staff',
        store_id: invite.store_id,
        openid: body.openid || null,
        password: body.password || '123456',
        status: 'enabled'
      }
      data.users.push(user)
    } else {
      user.display_name = body.display_name || user.display_name
      user.avatar_url = body.avatar_url || user.avatar_url
      user.role = body.role || user.role
      user.store_id = invite.store_id
      user.password = body.password || user.password
      user.status = 'enabled'
      user.openid = body.openid || user.openid
    }
    upsertRoleBinding(user, 'invite-accept')
    persist()
    return writeJson(res, 200, loginResponse(user))
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
      staff: data.users.filter((user) => user.store_id === store.id)
    })
  }

  const paymentQrMatch = url.pathname.match(/^\/api\/stores\/(\d+)\/payment-qr$/)
  if (req.method === 'PATCH' && paymentQrMatch) {
    const body = await readBody(req)
    const store = getStore(paymentQrMatch[1])
    if (!store) return writeJson(res, 404, { message: '门店不存在' })
    store.wechat_payment_qr_url = body.wechat_payment_qr_url || store.wechat_payment_qr_url || ''
    store.wechat_payment_qr_name = body.wechat_payment_qr_name || store.wechat_payment_qr_name || '微信收款码'
    store.payment_qr = store.wechat_payment_qr_name
    persist()
    return writeJson(res, 200, store)
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
