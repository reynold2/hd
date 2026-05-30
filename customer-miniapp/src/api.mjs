let testApiBase = null

function configuredApiBase() {
  if (testApiBase !== null) return testApiBase
  return import.meta.env?.VITE_API_BASE || ''
}

function apiUrl(path) {
  const base = configuredApiBase().replace(/\/$/, '')
  return `${base}${path}`
}

async function requestJson(path, options = {}) {
  const url = apiUrl(path)
  const uniApi = typeof uni !== 'undefined' ? uni : globalThis.uni
  if (uniApi?.request) {
    return new Promise((resolve, reject) => {
      uniApi.request({
        url,
        method: options.method || 'GET',
        header: options.headers,
        data: options.body ? JSON.parse(options.body) : undefined,
        success(response) {
          const statusCode = response.statusCode || 0
          if (statusCode < 200 || statusCode >= 300) {
            reject(new Error(options.errorMessage || '请求失败'))
            return
          }
          resolve(response.data)
        },
        fail() {
          reject(new Error(options.errorMessage || '请求失败'))
        }
      })
    })
  }
  if (typeof fetch === 'function') {
    const response = await fetch(url, options)
    if (!response.ok) {
      throw new Error(options.errorMessage || '请求失败')
    }
    return response.json()
  }
  throw new Error(options.errorMessage || '请求失败')
}

export function setApiBaseForTests(value) {
  testApiBase = value
}

export async function resolveRoleByOpenid(openid, storeId = 1) {
  return requestJson(`/api/roles/resolve?openid=${encodeURIComponent(openid)}&store_id=${storeId}`, {
    errorMessage: '角色解析失败'
  })
}

export async function wechatLogin(payload) {
  return requestJson('/api/auth/wechat-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '微信登录失败'
  })
}

export async function createEmployeeInvitation(storeId = 1, payload = {}) {
  return requestJson(`/api/stores/${storeId}/employee-invitations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '生成员工邀请失败'
  })
}

export async function acceptEmployeeInvitation(token, payload) {
  return requestJson(`/api/employee-invitations/${encodeURIComponent(token)}/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '员工注册失败'
  })
}

export async function fetchStoreCatalog(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/catalog`, { errorMessage: '门店信息加载失败' })
}

export async function fetchMealSession(number) {
  return requestJson(`/api/meal-sessions/${number}`, { errorMessage: '号码信息加载失败' })
}

export async function issueQueueNumber(storeId = 1, payload = { people_count: 2, remark: '' }) {
  return requestJson(`/api/stores/${storeId}/queue/issue`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '取号失败'
  })
}

export async function addSessionItem(number, item) {
  return requestJson(`/api/meal-sessions/${number}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
    errorMessage: '追加失败，请稍后再试'
  })
}

export async function appendSessionRemark(number, payload) {
  return requestJson(`/api/meal-sessions/${number}/remarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '备注提交失败'
  })
}

export async function createServiceCall(number, payload) {
  return requestJson(`/api/meal-sessions/${number}/service-calls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '呼叫服务失败'
  })
}

export async function requestCheckout(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/request-checkout`, {
    method: 'POST',
    errorMessage: '呼叫结账失败'
  })
}
