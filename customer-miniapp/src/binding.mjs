export function normalizeQueueNumber(value) {
  return String(value || '').trim().toUpperCase()
}

export function parseBindingParams(query = {}, search = '') {
  const searchParams = parseSearch(search)
  const merged = { ...searchParams, ...query }
  const storeId = Number(merged.store_id || merged.storeId || merged.store || 1)
  const number = normalizeQueueNumber(merged.number || merged.no || merged.queue_number || merged.scene)
  return {
    storeId: Number.isFinite(storeId) && storeId > 0 ? storeId : 1,
    number,
    table: String(merged.table || '').trim()
  }
}

export function parseH5BindingSearch(search = '') {
  return parseBindingParams({}, search)
}

export function validateBoundSession(session, storeId, number) {
  if (!session) {
    throw new Error('号码不存在，请确认后重新输入')
  }
  if (Number(session.store_id) !== Number(storeId)) {
    throw new Error('号码不属于当前门店')
  }
  if (normalizeQueueNumber(session.number) !== normalizeQueueNumber(number)) {
    throw new Error('号码信息不匹配')
  }
  if (['completed', 'cancelled'].includes(session.status)) {
    throw new Error('号码已结束，请联系店员重新取号')
  }
  return session
}

function parseSearch(search = '') {
  if (!search) {
    return {}
  }
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search)
  return Object.fromEntries(params.entries())
}
