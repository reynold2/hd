<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  addSessionItem,
  appendSessionRemark,
  callMealSession,
  completeMealSession,
  confirmPayment,
  createServiceCall,
  fetchCashierPending,
  fetchPendingServiceCalls,
  fetchStoreCatalog,
  fetchStoreQueue,
  handleServiceCall,
  issueQueueNumber,
  markDiningMealSession,
  requestCheckout,
  resolveRoleByOpenid,
  startPreparingMealSession
} from '../../api'
import { getStoredRoleProfile } from '../../role-auth.mjs'

const loading = ref(false)
const notice = ref('')
const store = ref(null)
const queue = ref([])
const cashierPending = ref([])
const serviceCalls = ref([])
const activeTab = ref('queue')
const storeId = ref(1)
const cashierId = ref(7)
const registerForm = ref({ people_count: 2, remark: '现场登记', item_name: '', item_amount: '' })

const pendingCount = computed(() => queue.value.filter((item) => !['completed', 'paid'].includes(item.status)).length)
const preparingCount = computed(() => queue.value.filter((item) => item.status === 'preparing').length)
const checkoutCount = computed(() => cashierPending.value.length)
const checkoutAmount = computed(() =>
  cashierPending.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0).toFixed(2)
)
const currentNumber = computed(() => queue.value[0]?.number || cashierPending.value[0]?.number || '暂无')
const paymentQrUrl = computed(() => store.value?.wechat_payment_qr_url || '')
const paymentQrText = computed(() =>
  store.value?.wechat_payment_qr_name || store.value?.payment_qr || `${store.value?.name || '本店'}微信收款二维码`
)

function statusText(status) {
  return {
    occupied: '等待中',
    preparing: '制作中',
    called: '已叫号',
    dining: '用餐中',
    checkout_requested: '待结账',
    paid: '已收款',
    completed: '已完成',
    skipped: '已跳号',
    cancelled: '已取消',
    risk_unpaid: '待确认'
  }[status] || status
}

function normalizeSession(item) {
  return {
    ...item,
    tags: [item.people_count ? `${item.people_count}人` : '', item.remark || ''].filter(Boolean)
  }
}

async function loadData() {
  loading.value = true
  notice.value = ''
  try {
    const [catalog, currentQueue, pendingCashier, pendingService] = await Promise.all([
      fetchStoreCatalog(storeId.value),
      fetchStoreQueue(storeId.value),
      fetchCashierPending(storeId.value),
      fetchPendingServiceCalls(storeId.value)
    ])
    store.value = catalog.store
    queue.value = currentQueue.map(normalizeSession)
    cashierPending.value = pendingCashier.map(normalizeSession)
    serviceCalls.value = pendingService
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '店员工作台加载失败'
    queue.value = []
    cashierPending.value = []
    serviceCalls.value = []
  } finally {
    loading.value = false
  }
}

async function registerNumber() {
  loading.value = true
  notice.value = ''
  try {
    const session = await issueQueueNumber(storeId.value, {
      people_count: Number(registerForm.value.people_count || 1),
      remark: registerForm.value.remark || '现场登记'
    })
    const amount = Number(registerForm.value.item_amount || 0)
    if (registerForm.value.item_name && amount > 0) {
      await addSessionItem(session.number, {
        name: registerForm.value.item_name,
        amount: amount.toFixed(2),
        quantity: 1,
        source: 'staff'
      })
    }
    notice.value = `${session.number} 已登记`
    registerForm.value = { people_count: 2, remark: '现场登记', item_name: '', item_amount: '' }
    await loadData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '登记失败'
  } finally {
    loading.value = false
  }
}

async function runAction(kind, number = '') {
  if (!number) return
  loading.value = true
  notice.value = ''
  try {
    if (kind === 'start') {
      await startPreparingMealSession(number)
      notice.value = `${number} 已开始处理`
    } else if (kind === 'call') {
      await callMealSession(number)
      notice.value = `${number} 已叫号`
    } else if (kind === 'dining') {
      await markDiningMealSession(number)
      notice.value = `${number} 已确认取餐`
    } else if (kind === 'complete') {
      await completeMealSession(number)
      notice.value = `${number} 已完成`
    } else if (kind === 'remark') {
      await appendSessionRemark(number, { remark: '店员已核对', source: 'staff' })
      notice.value = `${number} 已添加备注`
    } else if (kind === 'service') {
      await createServiceCall(number, { message: '店员协助处理中', source: 'staff' })
      notice.value = `${number} 已记录服务处理`
    } else if (kind === 'checkout') {
      await requestCheckout(number)
      notice.value = `${number} 已进入结账`
    }
    await loadData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '操作失败'
  } finally {
    loading.value = false
  }
}

async function receivePayment(session) {
  if (!session?.number) return
  loading.value = true
  notice.value = ''
  try {
    await confirmPayment(session.number, cashierId.value)
    await completeMealSession(session.number)
    notice.value = `${session.number} 已确认收到 ¥${session.total_amount} 并释放号码`
    await loadData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '确认收款失败'
  } finally {
    loading.value = false
  }
}

async function resolveService(call) {
  loading.value = true
  notice.value = ''
  try {
    await handleServiceCall(call.id, { staff_id: cashierId.value, resolution: '店员已处理' })
    notice.value = `${call.number} 服务已处理`
    await loadData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '服务处理失败'
  } finally {
    loading.value = false
  }
}

function setTab(tab) {
  activeTab.value = tab
}

onMounted(async () => {
  const profile = getStoredRoleProfile()
  cashierId.value = Number(profile?.staff_id || profile?.user_id || profile?.id || cashierId.value)
  const openid = profile?.openid
  if (openid) {
    try {
      const resolved = await resolveRoleByOpenid(openid, Number(profile?.store_id || 1))
      storeId.value = Number(resolved?.store_id || profile?.store_id || 1)
      cashierId.value = Number(resolved?.staff_id || resolved?.user_id || cashierId.value)
    } catch {
      storeId.value = Number(profile?.store_id || 1)
    }
  }
  const launchOptions = typeof uni !== 'undefined' ? uni.getLaunchOptionsSync?.() || {} : {}
  storeId.value = Number(launchOptions?.query?.store_id || storeId.value || 1)
  await loadData()
})
</script>

<template>
  <view class="page role-page compact-page">
    <view class="hero">
      <view>
        <text class="store-name">{{ store?.name || '店员工作台' }}</text>
        <view class="store-meta">
          <text>队列、叫号、登记、服务、收款确认</text>
          <text>当前 {{ currentNumber }} · 待结账 {{ checkoutCount }} 单</text>
        </view>
      </view>
      <view class="hero-badge">{{ pendingCount }} 待处理</view>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="kitchen-stats">
      <view class="stat-card">
        <text class="stat-value">{{ pendingCount }}</text>
        <text class="stat-label">队列中</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ preparingCount }}</text>
        <text class="stat-label">处理中</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ checkoutCount }}</text>
        <text class="stat-label">待收款</text>
      </view>
    </view>

    <view class="tab-bar">
      <view class="tab-item" :class="{ active: activeTab === 'queue' }" @click="setTab('queue')">队列</view>
      <view class="tab-item" :class="{ active: activeTab === 'register' }" @click="setTab('register')">登记</view>
      <view class="tab-item" :class="{ active: activeTab === 'cashier' }" @click="setTab('cashier')">收款</view>
      <view class="tab-item" :class="{ active: activeTab === 'service' }" @click="setTab('service')">服务</view>
    </view>

    <view v-if="activeTab === 'queue'" class="card">
      <view class="section-title">
        <text>队列叫号</text>
        <text>{{ queue.length }} 单</text>
      </view>
      <view class="completed-list">
        <view v-for="item in queue" :key="item.number" class="staff-work-row">
          <view>
            <text class="completed-number">{{ item.number }} · {{ statusText(item.status) }}</text>
            <text class="completed-meta">{{ item.tags.join(' / ') || '暂无备注' }} · ¥{{ item.total_amount }}</text>
          </view>
          <view class="staff-action-strip">
            <button v-if="item.status === 'occupied'" :disabled="loading" @click="runAction('start', item.number)">开制</button>
            <button v-if="item.status === 'preparing'" :disabled="loading" @click="runAction('call', item.number)">叫号</button>
            <button v-if="item.status === 'called'" :disabled="loading" @click="runAction('dining', item.number)">取餐</button>
            <button v-if="item.status === 'dining'" :disabled="loading" @click="runAction('checkout', item.number)">结账</button>
            <button :disabled="loading" @click="runAction('remark', item.number)">备注</button>
          </view>
        </view>
      </view>
      <view v-if="!queue.length" class="empty-state">暂无队列，先到登记页发号。</view>
    </view>

    <view v-else-if="activeTab === 'register'" class="card">
      <view class="section-title">
        <text>登记发号</text>
        <text>现场录入</text>
      </view>
      <view class="form-stack">
        <input v-model="registerForm.people_count" type="number" placeholder="人数" />
        <input v-model="registerForm.remark" placeholder="备注，如少辣、堂食" />
        <input v-model="registerForm.item_name" placeholder="可选：登记菜品名称" />
        <input v-model="registerForm.item_amount" type="digit" placeholder="可选：菜品金额" />
        <button class="orange-button" :disabled="loading" @click="registerNumber">登记并发号</button>
      </view>
    </view>

    <view v-else-if="activeTab === 'cashier'" class="card">
      <view class="section-title">
        <text>收款确认</text>
        <text>待收 ¥{{ checkoutAmount }}</text>
      </view>
      <view class="payment-qr-card">
        <image v-if="paymentQrUrl" class="payment-qr-image" :src="paymentQrUrl" mode="aspectFit" />
        <view v-else class="fake-qr large-qr">未配置</view>
        <view>
          <text class="completed-number">老板配置微信收款码</text>
          <text class="completed-meta">{{ paymentQrText }}</text>
          <text v-if="!paymentQrUrl" class="completed-meta">请老板先上传或配置微信收款二维码</text>
        </view>
      </view>
      <view class="cashier-list">
        <view v-for="item in cashierPending" :key="item.number" class="cashier-row">
          <view>
            <text>{{ item.number }} · {{ statusText(item.status) }}</text>
            <text>{{ item.remark || '暂无备注' }}</text>
          </view>
          <text>¥{{ item.total_amount }}</text>
          <button :disabled="loading" @click="receivePayment(item)">确认已收到</button>
        </view>
      </view>
      <view v-if="!cashierPending.length" class="empty-state">暂无待收款号码。</view>
    </view>

    <view v-else class="card">
      <view class="section-title">
        <text>服务处理</text>
        <text>{{ serviceCalls.length }} 条</text>
      </view>
      <view class="completed-list">
        <view v-for="call in serviceCalls" :key="call.id" class="staff-work-row">
          <view>
            <text class="completed-number">{{ call.number }}</text>
            <text class="completed-meta">{{ call.message }}</text>
          </view>
          <button :disabled="loading" @click="resolveService(call)">已处理</button>
        </view>
      </view>
      <view v-if="!serviceCalls.length" class="empty-state">暂无待处理服务。</view>
    </view>

    <view class="checkout-bar">
      <view>
        <text>店员闭环</text>
        <text>队列 · 登记 · 服务 · 收款</text>
      </view>
      <button :disabled="loading" @click="loadData">刷新</button>
    </view>
  </view>
</template>
