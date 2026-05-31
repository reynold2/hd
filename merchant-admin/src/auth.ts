export type AdminRole = 'platform_admin' | 'store_owner' | 'cashier' | 'screen'

export type AuthProfile = {
  username: string
  displayName: string
  role: AdminRole
  storeId?: number
  storeName?: string
}

export type LoginResponse = {
  token: string
  profile: AuthProfile
  redirect: string
}

const STORAGE_KEY = 'queue-admin-auth'
const TOKEN_KEY = 'queue-admin-auth-token'
let testAuthApiBase: string | null = null

const roleMeta: Record<AdminRole, { title: string; description: string; home: string }> = {
  platform_admin: {
    title: '平台管理员',
    description: '管理平台、门店、测试数据与全局配置',
    home: '/platform'
  },
  store_owner: {
    title: '门店老板',
    description: '查看本门店经营、队列、菜品与员工',
    home: '/store'
  },
  cashier: {
    title: '收银',
    description: '处理待结账号码、收款确认和异常核对',
    home: '/cashier'
  },
  screen: {
    title: '大屏',
    description: '展示当前叫号、等待队列与实时状态',
    home: '/screen'
  }
}

function configuredAuthApiBase() {
  if (testAuthApiBase !== null) return testAuthApiBase
  return import.meta.env?.VITE_API_BASE || ''
}

function authApiUrl(path: string) {
  const base = configuredAuthApiBase().replace(/\/$/, '')
  if (base === '/api' && path.startsWith('/api/')) {
    return path
  }
  return `${base}${path}`
}

export function setAuthApiBaseForTests(value: string) {
  testAuthApiBase = value
}

export function getRoleMeta(role: AdminRole) {
  return roleMeta[role]
}

export async function loginAdmin(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(authApiUrl('/api/admin/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  if (!response.ok) {
    throw new Error('账号或密码错误')
  }
  const payload = (await response.json()) as LoginResponse
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload.profile))
  localStorage.setItem(TOKEN_KEY, payload.token)
  return payload
}

export function getStoredProfile(): AuthProfile | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as AuthProfile) : null
  } catch {
    return null
  }
}

export function logoutAdmin() {
  localStorage.removeItem(STORAGE_KEY)
  localStorage.removeItem(TOKEN_KEY)
}

export function adminLoginHref(base = import.meta.env?.BASE_URL || '') {
  const normalizedBase = base ? base.replace(/\/?$/, '/') : '/'
  return `${normalizedBase}login`
}

export function logoutAdminAndRedirect() {
  logoutAdmin()
  window.location.assign(adminLoginHref())
}

export function resolveHomePath(role: AdminRole) {
  return roleMeta[role].home
}
