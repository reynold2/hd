export type NavigationGuardResult = true | string

export function resolveAuthRedirect(path: string, hasStoredProfile: boolean): NavigationGuardResult {
  if (path !== '/login' && !hasStoredProfile) {
    return '/login'
  }
  return true
}
