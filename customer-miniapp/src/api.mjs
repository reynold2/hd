const API_BASE = ''

export async function fetchStoreCatalog(storeId = 1) {
  const response = await fetch(`${API_BASE}/api/stores/${storeId}/catalog`)
  if (!response.ok) {
    throw new Error('门店信息加载失败')
  }
  return response.json()
}

export async function fetchMealSession(number) {
  const response = await fetch(`${API_BASE}/api/meal-sessions/${number}`)
  if (!response.ok) {
    throw new Error('号码信息加载失败')
  }
  return response.json()
}

export async function issueQueueNumber(storeId = 1, payload = { people_count: 2, remark: '' }) {
  const response = await fetch(`${API_BASE}/api/stores/${storeId}/queue/issue`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('取号失败')
  }
  return response.json()
}

export async function addSessionItem(number, item) {
  const response = await fetch(`${API_BASE}/api/meal-sessions/${number}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  })
  if (!response.ok) {
    throw new Error('追加失败，请稍后再试')
  }
  return response.json()
}

export async function appendSessionRemark(number, payload) {
  const response = await fetch(`${API_BASE}/api/meal-sessions/${number}/remarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('备注提交失败')
  }
  return response.json()
}

export async function createServiceCall(number, payload) {
  const response = await fetch(`${API_BASE}/api/meal-sessions/${number}/service-calls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    throw new Error('呼叫服务失败')
  }
  return response.json()
}

export async function requestCheckout(number) {
  const response = await fetch(`${API_BASE}/api/meal-sessions/${number}/actions/request-checkout`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('呼叫结账失败')
  }
  return response.json()
}
