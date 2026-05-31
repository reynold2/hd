<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bell,
  Check,
  Clock,
  DataLine,
  Finished,
  Money,
  Monitor,
  Operation,
  Tickets,
  Warning
} from '@element-plus/icons-vue'
import {
  createDish,
  confirmPayment,
  fetchCashierPending,
  fetchStoreCatalog,
  fetchStoreQueue,
  issueQueueNumber,
  runSessionAction,
  updateDish,
  type MealSession,
  type SessionAction,
  type StoreCatalog
} from '../api'
import type { AdminRouteMeta } from '../router'

type QueueRow = {
  number: string
  status: string
  people: number
  remark: string
  wait: string
  amount: string
}

const fallbackRows: QueueRow[] = [
  { number: 'A018', status: '制作中', people: 2, remark: '少辣，不要葱', wait: '18 分钟', amount: '¥28.00' },
  { number: 'A019', status: '等待中', people: 2, remark: '微辣，不要葱', wait: '25 分钟', amount: '¥0.00' },
  { number: 'A020', status: '等待中', people: 1, remark: '加宽粉，多加汤', wait: '23 分钟', amount: '¥5.00' },
  { number: 'A021', status: '待结账', people: 3, remark: '不要香菜', wait: '用餐中', amount: '¥46.00' },
  { number: 'A022', status: '已叫号', people: 2, remark: '多放醋', wait: '待取餐', amount: '¥32.00' }
]

const route = useRoute()
const catalog = ref<StoreCatalog | null>(null)
const remoteQueue = ref<MealSession[]>([])
const cashierPending = ref<MealSession[]>([])
const apiNotice = ref('')
const detailVisible = ref(false)
const selectedSession = ref<MealSession | null>(null)
const actionNotice = ref('')

const meta = computed(() => route.meta as AdminRouteMeta)

const queueRows = computed<QueueRow[]>(() => {
  const sourceRows = remoteQueue.value.length > 0 ? remoteQueue.value : cashierPending.value
  if (sourceRows.length === 0) return fallbackRows
  return sourceRows.map((row) => ({
    number: row.number,
    status: statusText(row.status),
    people: row.people_count,
    remark: row.remark || '无',
    wait: row.status === 'checkout_requested' ? '待结账' : '进行中',
    amount: `¥${row.total_amount}`
  }))
})

const stats = computed(() => [
  { label: '今日发号', value: String(queueRows.value.length), unit: '单', color: 'orange', icon: Tickets },
  { label: '等待中', value: String(queueRows.value.filter((row) => row.status === '等待中').length), unit: '桌', color: 'green', icon: Clock },
  { label: '制作中', value: String(queueRows.value.filter((row) => row.status === '制作中').length), unit: '单', color: 'blue', icon: Operation },
  { label: '待结账', value: String(cashierPending.value.length), unit: '单', color: 'purple', icon: Bell },
  { label: '记账金额', value: `¥${cashierPending.value.reduce((sum, row) => sum + Number(row.total_amount || 0), 0).toFixed(2)}`, unit: '', color: 'red', icon: Money }
])

const paymentQrUrl = computed(() => catalog.value?.store.wechat_payment_qr_url || '')
const paymentQrName = computed(() =>
  catalog.value?.store.wechat_payment_qr_name || catalog.value?.store.payment_qr || '请老板先配置微信收款码'
)

onMounted(loadDashboard)

async function loadDashboard() {
  try {
    const [catalogPayload, queuePayload, pendingPayload] = await Promise.all([
      fetchStoreCatalog(1),
      fetchStoreQueue(1),
      fetchCashierPending(1)
    ])
    catalog.value = catalogPayload
    remoteQueue.value = queuePayload
    cashierPending.value = pendingPayload
    refreshSelectedSession()
    actionNotice.value = '仪表盘已刷新'
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '接口暂不可用，已展示本地样例数据'
  }
}

function refreshSelectedSession() {
  if (!selectedSession.value) return
  const latest = [...remoteQueue.value, ...cashierPending.value].find(
    (session) => session.number === selectedSession.value?.number
  )
  selectedSession.value = latest || null
  detailVisible.value = Boolean(latest)
}

async function addSampleDrink() {
  try {
    await createDish(1, { name: '酸梅汤', category: '饮品', price: '8.00', available: true })
    actionNotice.value = '已新增酸梅汤'
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '新增饮品失败'
  }
}

async function toggleFirstDish() {
  const firstDish = catalog.value?.dishes[0]
  if (!firstDish) return
  try {
    await updateDish(firstDish.id, { available: !firstDish.available })
    actionNotice.value = `${firstDish.name} 已切换上下架`
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '菜品切换失败'
  }
}

async function issueSampleNumber() {
  try {
    await issueQueueNumber(1, { people_count: 2, remark: '现场发号，少辣' })
    actionNotice.value = '已发出新号码'
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '发号失败'
  }
}

async function progressNumber(row: QueueRow) {
  const statusMap: Record<string, SessionAction> = {
    等待中: 'start-preparing',
    制作中: 'call',
    已叫号: 'mark-dining',
    用餐中: 'request-checkout',
    已跳号: 'resume'
  }
  const action = statusMap[row.status]
  if (!action) return
  try {
    await runSessionAction(row.number, action)
    actionNotice.value = `${row.number} 已推进到下一步`
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '推进失败'
  }
}

async function receivePayment(row: QueueRow) {
  try {
    await confirmPayment(row.number, 1)
    await runSessionAction(row.number, 'complete')
    actionNotice.value = `${row.number} 已完成收款并释放`
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '确认收款失败'
  }
}

async function applyExceptionAction(row: QueueRow, action: SessionAction) {
  try {
    await runSessionAction(row.number, action)
    actionNotice.value = `${row.number} 已执行 ${statusTextForAction(action)}`
    await loadDashboard()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '异常动作失败'
  }
}

function openBigScreen() {
  actionNotice.value = '大屏入口已准备，可直接切换到 /screen 查看'
}

function reannounceCurrent() {
  actionNotice.value = `正在重新播报 ${queueRows.value[0]?.number || '当前号码'}`
}

function showQueueDetail(row: QueueRow) {
  selectedSession.value =
    [...remoteQueue.value, ...cashierPending.value].find((session) => session.number === row.number) ||
    fallbackSession(row)
  detailVisible.value = true
}

function fallbackSession(row: QueueRow): MealSession {
  return {
    number: row.number,
    status: reverseStatusText(row.status),
    people_count: row.people,
    remark: row.remark,
    total_amount: row.amount.replace('¥', ''),
    items: []
  }
}

function rowFromSession(session: MealSession): QueueRow {
  return {
    number: session.number,
    status: statusText(session.status),
    people: session.people_count,
    remark: session.remark || '无',
    wait: session.status === 'checkout_requested' ? '待结账' : '进行中',
    amount: `¥${session.total_amount}`
  }
}

function reverseStatusText(status: string) {
  const map: Record<string, string> = {
    等待中: 'occupied',
    制作中: 'preparing',
    已叫号: 'called',
    用餐中: 'dining',
    待结账: 'checkout_requested',
    已收款: 'paid',
    已完成: 'completed',
    已跳号: 'skipped',
    已取消: 'cancelled',
    风险: 'risk_unpaid'
  }
  return map[status] || status
}

function statusTagType(status: string) {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    occupied: 'warning',
    preparing: 'primary',
    called: 'success',
    dining: 'success',
    checkout_requested: 'danger',
    paid: 'info',
    completed: 'info',
    skipped: 'warning',
    cancelled: 'info',
    risk_unpaid: 'danger'
  }
  return map[status] || 'info'
}

function statusText(status: string) {
  const map: Record<string, string> = {
    occupied: '等待中',
    preparing: '制作中',
    called: '已叫号',
    dining: '用餐中',
    checkout_requested: '待结账',
    paid: '已收款',
    completed: '已完成',
    skipped: '已跳号',
    cancelled: '已取消',
    risk_unpaid: '风险'
  }
  return map[status] || status
}

function statusTextForAction(action: SessionAction) {
  const map: Record<SessionAction, string> = {
    'start-preparing': '开始制作',
    call: '叫号',
    'mark-dining': '确认取餐',
    'request-checkout': '请求结账',
    complete: '完成',
    skip: '跳号',
    resume: '恢复',
    cancel: '取消',
    'mark-unpaid-risk': '风险标记'
  }
  return map[action]
}

const logs = [
  'A018 厨房开始制作，备注：少辣，不要葱',
  'A020 顾客追加可乐 1 份',
  'A021 呼叫结账，等待收银确认',
  '门店二维码已生成，可用于顾客绑号'
]
</script>

<template>
  <div class="route-page">
    <header class="topbar">
      <div>
        <p>{{ meta.crumb }}</p>
        <h1>{{ meta.title }}</h1>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
        <p v-else-if="actionNotice" class="api-notice success-notice">{{ actionNotice }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Monitor" @click="openBigScreen">打开大屏</el-button>
        <el-button :icon="Bell" circle @click="reannounceCurrent" />
        <div class="profile">张老板</div>
      </div>
    </header>

    <section class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <div :class="['stat-icon', stat.color]">
          <el-icon><component :is="stat.icon" /></el-icon>
        </div>
        <div>
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }} <small>{{ stat.unit }}</small></strong>
          <p>实时同步</p>
        </div>
      </article>
    </section>

    <section class="main-grid">
      <article class="panel current-number">
        <div class="panel-title">
          <h2>当前制作</h2>
          <el-button type="primary" :icon="Bell" @click="reannounceCurrent">重新播报</el-button>
        </div>
        <div class="number-card">
          <span>{{ queueRows[0]?.number || 'A018' }}</span>
          <p>{{ queueRows[0]?.status || '制作中' }}</p>
        </div>
        <div class="action-grid">
          <el-button type="success" :icon="Check">制作完成</el-button>
          <el-button type="warning" :icon="Finished">跳过此单</el-button>
          <el-button type="primary" :icon="Money">收银确认</el-button>
        </div>
      </article>

      <article class="panel queue-panel">
        <div class="panel-title">
          <h2>队列管理</h2>
          <el-button type="success" @click="issueSampleNumber">新增号码</el-button>
        </div>
        <el-table :data="queueRows" height="360">
          <el-table-column prop="number" label="号码" width="90" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="people" label="人数" width="80" />
          <el-table-column prop="remark" label="备注" />
          <el-table-column prop="wait" label="等待/阶段" width="110" />
          <el-table-column prop="amount" label="金额" width="110" />
          <el-table-column label="操作" width="260">
            <template #default="scope">
              <el-button link type="primary" @click="showQueueDetail(scope.row)">详情</el-button>
              <el-button link type="success" @click="progressNumber(scope.row)">
                {{ scope.row.status === '已跳号' ? '恢复' : scope.row.status === '待结账' ? '待收银' : '推进' }}
              </el-button>
              <el-button v-if="scope.row.status === '待结账'" link type="warning" @click="receivePayment(scope.row)">收款</el-button>
              <el-button v-if="['等待中','制作中','已叫号'].includes(scope.row.status)" link type="warning" @click="applyExceptionAction(scope.row, 'skip')">跳号</el-button>
              <el-button v-if="scope.row.status !== '待结账'" link type="danger" @click="applyExceptionAction(scope.row, 'cancel')">取消</el-button>
              <el-button v-if="!['已完成','已取消'].includes(scope.row.status)" link type="danger" @click="applyExceptionAction(scope.row, 'mark-unpaid-risk')">风险</el-button>
            </template>
          </el-table-column>
        </el-table>
      </article>

      <article class="panel cashier-panel">
        <div class="panel-title">
          <h2>轻量记账收银</h2>
          <el-tag type="success">线下扫码付款</el-tag>
        </div>
        <div class="cashier-layout">
          <div>
            <span>待结账号码</span>
            <strong>{{ cashierPending[0]?.number || '暂无' }}</strong>
            <p>{{ cashierPending[0] ? `应收 ¥${cashierPending[0].total_amount}` : '没有待结账号码' }}</p>
          </div>
          <img v-if="paymentQrUrl" class="qr-box qr-image" :src="paymentQrUrl" :alt="paymentQrName" />
          <div v-else class="qr-box">{{ paymentQrName }}</div>
          <el-button type="primary" :icon="Check" :disabled="!cashierPending[0]" @click="cashierPending[0] && receivePayment(rowFromSession(cashierPending[0]))">确认已收到</el-button>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>操作提醒</h2>
          <el-icon><Warning /></el-icon>
        </div>
        <ul class="log-list">
          <li v-for="log in logs" :key="log">{{ log }}</li>
        </ul>
      </article>

      <article class="panel dishes-panel">
        <div class="panel-title">
          <h2>菜品展示</h2>
          <div class="panel-actions">
            <el-button type="success" @click="addSampleDrink">新增饮品</el-button>
            <el-button @click="toggleFirstDish">切换首项上下架</el-button>
          </div>
        </div>
        <div class="dish-grid">
          <div v-for="dish in catalog?.dishes || []" :key="dish.id" class="dish-chip">
            <strong>{{ dish.name }}</strong>
            <span>{{ dish.category }} / ¥{{ dish.price }}</span>
            <el-tag :type="dish.available ? 'success' : 'info'">{{ dish.available ? '上架' : '下架' }}</el-tag>
          </div>
        </div>
      </article>
    </section>

    <el-drawer v-model="detailVisible" size="420px" title="号码详情" class="queue-detail-drawer">
      <div v-if="selectedSession" class="queue-detail">
        <section class="detail-hero">
          <div>
            <span>当前号码</span>
            <strong>{{ selectedSession.number }}</strong>
          </div>
          <el-tag :type="statusTagType(selectedSession.status)" size="large">
            {{ statusText(selectedSession.status) }}
          </el-tag>
        </section>

        <section class="detail-grid">
          <div>
            <span>人数</span>
            <strong>{{ selectedSession.people_count }} 人</strong>
          </div>
          <div>
            <span>合计金额</span>
            <strong>¥{{ selectedSession.total_amount }}</strong>
          </div>
          <div>
            <span>收款方式</span>
            <strong>{{ selectedSession.payment_method || '未收款' }}</strong>
          </div>
          <div>
            <span>收银员</span>
            <strong>{{ selectedSession.cashier_id || '-' }}</strong>
          </div>
        </section>

        <section class="detail-block">
          <h3>备注信息</h3>
          <p>{{ selectedSession.remark || '暂无备注' }}</p>
        </section>

        <section class="detail-block">
          <h3>登记内容</h3>
          <el-table v-if="selectedSession.items.length" :data="selectedSession.items" size="small">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="quantity" label="数量" width="68" />
            <el-table-column prop="source" label="来源" width="82" />
            <el-table-column prop="subtotal" label="小计" width="82" />
          </el-table>
          <el-empty v-else description="暂无已登记菜品" :image-size="72" />
        </section>
      </div>
    </el-drawer>
  </div>
</template>
