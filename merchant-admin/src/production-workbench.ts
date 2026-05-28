import type { MealSession } from './api'

const PRODUCTION_STATUSES = ['occupied', 'preparing', 'called', 'skipped'] as const

const COLUMN_META: Record<(typeof PRODUCTION_STATUSES)[number], { title: string }> = {
  occupied: { title: '待制作' },
  preparing: { title: '制作中' },
  called: { title: '已叫号' },
  skipped: { title: '已跳号' }
}

const PRIMARY_ACTIONS: Record<
  (typeof PRODUCTION_STATUSES)[number],
  { action: string; label: string; type: 'primary' | 'success' | 'warning' }
> = {
  occupied: { action: 'start-preparing', label: '开始制作', type: 'primary' },
  preparing: { action: 'call', label: '制作完成并叫号', type: 'success' },
  called: { action: 'mark-dining', label: '确认取餐', type: 'success' },
  skipped: { action: 'resume', label: '恢复排队', type: 'warning' }
}

export type ProductionColumn = {
  key: (typeof PRODUCTION_STATUSES)[number]
  title: string
  items: MealSession[]
}

export type ProductionAction = {
  action: string
  label: string
  type: 'primary' | 'success' | 'warning'
}

export function getProductionQueue(sessions: MealSession[]) {
  return sessions.filter((session) =>
    (PRODUCTION_STATUSES as readonly string[]).includes(session.status)
  )
}

export function buildProductionColumns(sessions: MealSession[]): ProductionColumn[] {
  const queue = getProductionQueue(sessions)
  return PRODUCTION_STATUSES.map((key) => ({
    key,
    title: COLUMN_META[key].title,
    items: queue.filter((session) => session.status === key)
  }))
}

export function getProductionPrimaryAction(
  session: Pick<MealSession, 'status'>
): ProductionAction | null {
  if (!(session.status in PRIMARY_ACTIONS)) return null
  return PRIMARY_ACTIONS[session.status as (typeof PRODUCTION_STATUSES)[number]]
}
