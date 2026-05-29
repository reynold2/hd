const STORAGE_KEY = 'customer-miniapp-role-auth'
const DEFAULT_STORE_ID = 1
const DEFAULT_CUSTOMER_NUMBER = 'A018'

export const miniRoles = [
  { code: 'customer', label: '顾客', page: '/pages/index/index', description: '进店、选菜、绑定、加退菜、支付' },
  { code: 'boss', label: '老板', page: '/pages/boss/index', description: '门店经营与订单总览' },
  { code: 'staff', label: '服务员', page: '/pages/staff/index', description: '协助加退菜、呼叫处理' },
  { code: 'kitchen', label: '制作', page: '/pages/kitchen/index', description: '制作队列与出餐状态' },
  { code: 'cashier', label: '收银', page: '/pages/cashier/index', description: '结算、出码、支付确认' }
]

export function getStoredRoleProfile() {
  try {
    const raw = uni.getStorageSync(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveRoleProfile(profile) {
  uni.setStorageSync(STORAGE_KEY, JSON.stringify(profile))
}

export function clearRoleProfile() {
  uni.removeStorageSync(STORAGE_KEY)
}

export function getRoleEntry(roleCode) {
  return miniRoles.find((item) => item.code === roleCode) || miniRoles[0]
}

export function buildRoleEntryUrl(profile) {
  const role = getRoleEntry(profile?.role)
  const page = profile?.entry_page || role.page
  const storeId = Number(profile?.store_id || DEFAULT_STORE_ID)
  const params = [`store_id=${encodeURIComponent(storeId)}`]
  if (role.code === 'customer') {
    params.push(`number=${encodeURIComponent(profile?.number || DEFAULT_CUSTOMER_NUMBER)}`)
  }
  return `${page}?${params.join('&')}`
}

export function buildStoredProfile(loginPayload, openid) {
  return {
    ...loginPayload,
    openid: loginPayload?.openid || openid,
    store_id: Number(loginPayload?.store_id || DEFAULT_STORE_ID)
  }
}
