let testApiBase = null

function configuredApiBase() {
  if (testApiBase !== null) return testApiBase
  return import.meta.env?.VITE_API_BASE || ''
}

function apiUrl(path) {
  const base = configuredApiBase().replace(/\/$/, '')
  if (base === '/api' && path.startsWith('/api/')) {
    return path
  }
  return `${base}${path}`
}

function getStoredRoleProfile() {
  try {
    const raw = uni?.getStorageSync?.('customer-miniapp-role-auth')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function getAuthHeaders(headers = {}) {
  const profile = getStoredRoleProfile()
  const token = profile?.token
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers
}

async function requestJson(path, options = {}) {
  const url = apiUrl(path)
  const uniApi = typeof uni !== 'undefined' ? uni : globalThis.uni
  const headers = options.auth === false ? options.headers : getAuthHeaders(options.headers)
  if (uniApi?.request) {
    return new Promise((resolve, reject) => {
      uniApi.request({
        url,
        method: options.method || 'GET',
        header: headers,
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
    const response = await fetch(url, {
      ...options,
      headers
    })
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

export async function fetchStoreQueue(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/queue`, { errorMessage: '队列加载失败' })
}

export async function fetchCashierPending(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/cashier/pending`, { errorMessage: '收银列表加载失败' })
}

export async function fetchPendingServiceCalls(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/service-calls/pending`, { errorMessage: '服务呼叫加载失败' })
}

export async function fetchOperationLogs(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/operation-logs`, { errorMessage: '操作日志加载失败' })
}

export async function updateBusinessStatus(storeId = 1, businessStatus = 'open') {
  return requestJson(`/api/stores/${storeId}/business-status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ business_status: businessStatus }),
    errorMessage: '营业状态更新失败'
  })
}

export async function updateStoreSettings(storeId = 1, payload = {}) {
  return requestJson(`/api/stores/${storeId}/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '门店设置保存失败'
  })
}

export async function updateWechatPaymentQr(storeId = 1, payload = {}) {
  return requestJson(`/api/stores/${storeId}/payment-qr`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '收款码保存失败'
  })
}

export async function updateStaffStatus(staffId, status = 'active') {
  return requestJson(`/api/staff/${staffId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
    errorMessage: '员工状态更新失败'
  })
}

export async function createDish(storeId = 1, payload = {}) {
  return requestJson(`/api/stores/${storeId}/dishes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '菜品创建失败'
  })
}

export async function updateDish(dishId, payload = {}) {
  return requestJson(`/api/dishes/${dishId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '菜品更新失败'
  })
}

export async function startPreparingMealSession(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/start-preparing`, {
    method: 'POST',
    errorMessage: '开始制作失败'
  })
}

export async function callMealSession(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/call`, {
    method: 'POST',
    errorMessage: '叫号失败'
  })
}

export async function markDiningMealSession(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/mark-dining`, {
    method: 'POST',
    errorMessage: '确认取餐失败'
  })
}

export async function completeMealSession(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/complete`, {
    method: 'POST',
    errorMessage: '完成出餐失败'
  })
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

export async function handleServiceCall(callId, payload) {
  return requestJson(`/api/service-calls/${callId}/handle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    errorMessage: '服务处理失败'
  })
}

export async function requestCheckout(number) {
  return requestJson(`/api/meal-sessions/${number}/actions/request-checkout`, {
    method: 'POST',
    errorMessage: '呼叫结账失败'
  })
}

export async function confirmPayment(number, cashierId, paymentMethod = 'store_qr') {
  return requestJson(`/api/meal-sessions/${number}/actions/confirm-payment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_method: paymentMethod, cashier_id: cashierId }),
    errorMessage: '确认收款失败'
  })
}

export async function fetchKitchenQueue(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/kitchen/queue`, { errorMessage: '制作队列加载失败' })
}

export async function fetchKitchenCompleted(storeId = 1) {
  return requestJson(`/api/stores/${storeId}/kitchen/completed`, { errorMessage: '已完成列表加载失败' })
}

export async function startKitchenOrder(storeId = 1, number) {
  return requestJson(`/api/stores/${storeId}/kitchen/queue/${encodeURIComponent(number)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'start' }),
    errorMessage: '开始制作失败'
  })
}

export async function completeKitchenOrder(storeId = 1, number) {
  return requestJson(`/api/stores/${storeId}/kitchen/queue/${encodeURIComponent(number)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'complete', call_message: '已完成，请取餐' }),
    errorMessage: '完成出餐失败'
  })
}
