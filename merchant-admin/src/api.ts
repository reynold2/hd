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

export async function fetchStoreCatalog(storeId = 1): Promise<StoreCatalog> {
  const response = await fetch(`/api/stores/${storeId}/catalog`)
  if (!response.ok) {
    throw new Error('门店信息加载失败')
  }
  return response.json()
}

export async function fetchStoreQueue(storeId = 1): Promise<MealSession[]> {
  const response = await fetch(`/api/stores/${storeId}/queue`)
  if (!response.ok) {
    throw new Error('队列加载失败')
  }
  return response.json()
}

export async function updateBusinessStatus(storeId: number, businessStatus: 'open' | 'paused' | 'closed') {
  const response = await fetch(`/api/stores/${storeId}/business-status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ business_status: businessStatus })
  })
  if (!response.ok) {
    throw new Error('营业状态更新失败')
  }
  return response.json()
}

export async function updateStoreSettings(
  storeId: number,
  payload: { business_hours?: string; address?: string; queue_prefix?: string; avg_prepare_minutes?: number }
) {
  const response = await fetch(`/api/stores/${storeId}/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('门店设置保存失败')
  }
  return response.json()
}

export async function updateStaffStatus(staffId: number, status: 'active' | 'inactive') {
  const response = await fetch(`/api/staff/${staffId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })
  if (!response.ok) {
    throw new Error('员工状态更新失败')
  }
  return response.json()
}

export async function createDish(storeId: number, payload: { name: string; category: string; price: string; available: boolean }) {
  const response = await fetch(`/api/stores/${storeId}/dishes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('菜品创建失败')
  }
  return response.json()
}

export async function updateDish(dishId: number, payload: { available?: boolean; price?: string; name?: string; category?: string }) {
  const response = await fetch(`/api/dishes/${dishId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('菜品更新失败')
  }
  return response.json()
}

export async function issueQueueNumber(storeId = 1, payload = { people_count: 2, remark: '' }) {
  const response = await fetch(`/api/stores/${storeId}/queue/issue`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('发号失败')
  }
  return response.json()
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

export async function runSessionAction(number: string, action: SessionAction) {
  const response = await fetch(`/api/meal-sessions/${number}/actions/${action}`, { method: 'POST' })
  if (!response.ok) {
    throw new Error('操作失败')
  }
  return response.json()
}

export async function confirmPayment(
  number: string,
  cashierId = 1,
  paymentMethod: 'store_qr' | 'cash' | 'other' = 'store_qr'
) {
  const response = await fetch(`/api/meal-sessions/${number}/actions/confirm-payment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_method: paymentMethod, cashier_id: cashierId })
  })
  if (!response.ok) {
    throw new Error('确认收款失败')
  }
  return response.json()
}

export async function fetchCashierPending(storeId = 1): Promise<MealSession[]> {
  const response = await fetch(`/api/stores/${storeId}/cashier/pending`)
  if (!response.ok) {
    throw new Error('待结账列表加载失败')
  }
  return response.json()
}

export async function fetchMealSession(number: string): Promise<MealSession & { store_id: number }> {
  const response = await fetch(`/api/meal-sessions/${number}`)
  if (!response.ok) {
    throw new Error('号码详情加载失败')
  }
  return response.json()
}

export async function adjustSessionRemark(number: string, remark: string, source = 'cashier') {
  const response = await fetch(`/api/meal-sessions/${number}/remarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ remark, source })
  })
  if (!response.ok) {
    throw new Error('备注更新失败')
  }
  return response.json()
}

export async function addCashierLineItem(
  number: string,
  payload: { name: string; amount: string; source: 'cashier'; quantity: number; note?: string }
) {
  const response = await fetch(`/api/meal-sessions/${number}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('金额调整失败')
  }
  return response.json()
}
