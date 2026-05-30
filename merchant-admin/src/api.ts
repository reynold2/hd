export type MealSession = {
  number: string
  status: string
  people_count: number
  remark: string
  total_amount: string
  store_id?: number
  payment_method?: string
  cashier_id?: number
  items: Array<{
    name: string
    amount: string
    quantity: number
    source: string
    note: string
    subtotal: string
  }>
}

export type StoreCatalog = {
  store: {
    name: string
    business_status: string
    business_hours: string
    phone: string
    address: string
    avg_prepare_minutes: number
    queue_prefix: string
  }
  dishes: Array<{ id: number; name: string; category: string; price: string; available: boolean }>
  staff: Array<{ id: number; name: string; role: string; status: string }>
}

export type SessionAction =
  | 'start-preparing'
  | 'call'
  | 'mark-dining'
  | 'request-checkout'
  | 'complete'
  | 'skip'
  | 'resume'
  | 'cancel'
  | 'mark-unpaid-risk'

export type AdminUser = {
  id: number
  username: string
  display_name: string
  avatar_url?: string
  role: string
  store_id?: number | null
  openid?: string | null
  password?: string
  status?: string
}

type IssueQueuePayload = {
  people_count: number
  remark?: string
}

type LineItemPayload = {
  name: string
  amount: string
  source: string
  quantity?: number
  note?: string
}

type RemarkPayload = {
  remark: string
  source?: string
}

type ServiceCallPayload = {
  message: string
  source?: string
}

type CreateDishPayload = {
  name: string
  category?: string
  price: string
  available?: boolean
}

type UpdateDishPayload = Partial<CreateDishPayload>

let testApiBase: string | null = null

function configuredApiBase() {
  if (testApiBase !== null) return testApiBase
  return import.meta.env?.VITE_API_BASE || ''
}

export function apiUrl(path: string) {
  const base = configuredApiBase().replace(/\/$/, '')
  if (base === '/api' && path.startsWith('/api/')) {
    return path
  }
  return `${base}${path}`
}

export function setApiBaseForTests(value: string) {
  testApiBase = value
}

export async function fetchAdminUsers(): Promise<AdminUser[]> {
  const response = await fetch(apiUrl('/api/admin/users'))
  if (!response.ok) throw new Error('用户列表加载失败')
  return response.json()
}

export async function createAdminUser(payload: Partial<AdminUser>) {
  const response = await fetch(apiUrl('/api/admin/users'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) throw new Error('创建用户失败')
  return response.json()
}

export async function updateAdminUser(id: number, payload: Partial<AdminUser>) {
  const response = await fetch(apiUrl(`/api/admin/users/${id}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) throw new Error('更新用户失败')
  return response.json()
}

export async function deleteAdminUser(id: number) {
  const response = await fetch(apiUrl(`/api/admin/users/${id}`), { method: 'DELETE' })
  if (!response.ok) throw new Error('删除用户失败')
  return response.json()
}

export async function createEmployeeInvitation(storeId = 1, payload = { role_scope: ['staff', 'cashier', 'kitchen'] as string[], created_by: 0 }) {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/employee-invitations`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) throw new Error('生成邀请失败')
  return response.json()
}

export async function acceptEmployeeInvitation(token: string, payload: Record<string, unknown>) {
  const response = await fetch(apiUrl(`/api/employee-invitations/${token}/accept`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) throw new Error('员工注册失败')
  return response.json()
}

export async function resolveRoleByOpenid(openid: string, storeId = 1) {
  const response = await fetch(apiUrl(`/api/roles/resolve?openid=${encodeURIComponent(openid)}&store_id=${storeId}`))
  if (!response.ok) {
    throw new Error('角色解析失败')
  }
  return response.json()
}

export async function wechatLogin(payload: { openid: string; store_id: number }) {
  const response = await fetch(apiUrl('/api/auth/wechat-login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('微信登录失败')
  }
  return response.json()
}

export async function fetchStoreCatalog(storeId = 1): Promise<StoreCatalog> {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/catalog`))
  if (!response.ok) {
    throw new Error('门店信息加载失败')
  }
  return response.json()
}

export async function fetchStoreQueue(storeId = 1): Promise<MealSession[]> {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/queue`))
  if (!response.ok) {
    throw new Error('队列加载失败')
  }
  return response.json()
}

export async function fetchCashierPending(storeId = 1): Promise<MealSession[]> {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/cashier/pending`))
  if (!response.ok) {
    throw new Error('待收银列表加载失败')
  }
  return response.json()
}

export async function fetchMealSession(number: string): Promise<MealSession> {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}`))
  if (!response.ok) {
    throw new Error('号码信息加载失败')
  }
  return response.json()
}

export async function issueQueueNumber(storeId = 1, payload: IssueQueuePayload = { people_count: 2, remark: '' }) {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/queue/issue`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('取号失败')
  }
  return response.json()
}

export async function addSessionItem(number: string, item: LineItemPayload) {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/items`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  })
  if (!response.ok) {
    throw new Error('追加失败，请稍后再试')
  }
  return response.json()
}

export async function appendSessionRemark(number: string, payload: RemarkPayload) {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/remarks`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('备注提交失败')
  }
  return response.json()
}

export async function createServiceCall(number: string, payload: ServiceCallPayload) {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/service-calls`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('呼叫服务失败')
  }
  return response.json()
}

export async function requestCheckout(number: string) {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/actions/request-checkout`), {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('呼叫结账失败')
  }
  return response.json()
}

export async function runSessionAction(number: string, action: SessionAction): Promise<MealSession> {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/actions/${action}`), {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('号码状态推进失败')
  }
  return response.json()
}

export async function confirmPayment(number: string, cashierId: number, paymentMethod = 'store_qr'): Promise<MealSession> {
  const response = await fetch(apiUrl(`/api/meal-sessions/${number}/actions/confirm-payment`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_method: paymentMethod, cashier_id: cashierId })
  })
  if (!response.ok) {
    throw new Error('确认收款失败')
  }
  return response.json()
}

export async function createDish(storeId: number, payload: CreateDishPayload) {
  const response = await fetch(apiUrl(`/api/stores/${storeId}/dishes`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('新增菜品失败')
  }
  return response.json()
}

export async function updateDish(dishId: number, payload: UpdateDishPayload) {
  const response = await fetch(apiUrl(`/api/dishes/${dishId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('更新菜品失败')
  }
  return response.json()
}
