<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { addSessionItem, appendSessionRemark, createServiceCall, fetchMealSession, fetchStoreCatalog, requestCheckout } from '../../api'
import { normalizeQueueNumber, parseBindingParams, validateBoundSession } from '../../binding.mjs'
import { buildServiceCallPayload, getCheckoutButtonState, getCustomerActionState } from '../../customer-actions.mjs'

const pageOptions = ref({})
const bindNumberInput = ref('')
const selectedStoreId = ref(1)
const session = ref(null)
const catalog = ref(null)
const apiNotice = ref('')
const actionNotice = ref('')
const remarkDraft = ref('')
const serviceMessage = ref('需要店员协助')
const lastRefreshedAt = ref('')
let refreshTimer = null

onLoad((options) => {
  pageOptions.value = options || {}
})
onMounted(async () => {
  await initializePage()
  refreshTimer = setInterval(refreshSession, 15000)
})
onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

const actionState = computed(() => getCustomerActionState(session.value))
const checkoutState = computed(() => getCheckoutButtonState(session.value))
const statusText = (status) => ({ occupied: '等待中', preparing: '制作中', called: '待取餐', dining: '用餐中', checkout_requested: '待结账', paid: '已收款', completed: '已完成', skipped: '已跳号', cancelled: '已取消', risk_unpaid: '待确认' }[status] || status)
const progressSteps = computed(() => [
  { key: 'occupied', label: '已取号', desc: '门店已收到您的号码' },
  { key: 'preparing', label: '制作中', desc: '后厨正在为您准备' },
  { key: 'called', label: '待取餐', desc: '请留意门店叫号' },
  { key: 'dining', label: '用餐中', desc: '可继续加菜或结账' }
])
const currentStepIndex = computed(() => {
  const order = ['occupied', 'preparing', 'called', 'dining', 'checkout_requested', 'paid', 'completed']
  const index = order.indexOf(session.value?.status)
  return index < 0 ? 0 : Math.min(index, 3)
})
const availableDishes = computed(() => (catalog.value?.dishes || []).filter((item) => item.available).slice(0, 4))
const totalQuantity = computed(() => (session.value?.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0))
const storeName = computed(() => catalog.value?.store?.name || `门店 #${selectedStoreId.value}`)

async function initializePage() {
  const search = typeof window === 'undefined' ? '' : window.location.search
  const binding = parseBindingParams(pageOptions.value, search)
  selectedStoreId.value = binding.storeId
  bindNumberInput.value = binding.number
  try {
    catalog.value = await fetchStoreCatalog(selectedStoreId.value)
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '门店信息加载失败'
  }
  if (binding.number) await bindNumber(binding.number)
  else apiNotice.value = '请先绑定号码'
}
async function refreshSession() {
  if (!session.value) return
  try {
    const payload = await fetchMealSession(session.value.number)
    validateBoundSession(payload, selectedStoreId.value, session.value.number)
    session.value = payload
    lastRefreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '自动刷新失败'
  }
}
async function bindNumber(number = bindNumberInput.value) {
  const normalized = normalizeQueueNumber(number)
  if (!normalized) return (actionNotice.value = '请输入号码')
  try {
    const payload = await fetchMealSession(normalized)
    validateBoundSession(payload, selectedStoreId.value, normalized)
    session.value = payload
    bindNumberInput.value = normalized
    lastRefreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    actionNotice.value = `${normalized} 已绑定`
  } catch (error) {
    actionNotice.value = error instanceof Error ? error.message : '号码绑定失败'
  }
}
async function submitRemark() {
  if (!actionState.value.canSubmit) return (actionNotice.value = actionState.value.message)
  const remark = remarkDraft.value.trim()
  if (!remark) return (actionNotice.value = '请输入要补充的备注')
  session.value = await appendSessionRemark(session.value.number, { remark, source: 'customer' })
  remarkDraft.value = ''
  lastRefreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  actionNotice.value = '备注已提交'
}
async function callService() {
  if (!actionState.value.canSubmit) return (actionNotice.value = actionState.value.message)
  await createServiceCall(session.value.number, buildServiceCallPayload(serviceMessage.value))
  actionNotice.value = '已呼叫服务'
}
async function callCheckout() {
  if (checkoutState.value.disabled) return (actionNotice.value = checkoutState.value.hint)
  session.value = await requestCheckout(session.value.number)
  lastRefreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  actionNotice.value = '已呼叫结账'
}
async function addDish(dish) {
  if (!actionState.value.canSubmit) return (actionNotice.value = actionState.value.message)
  session.value = await addSessionItem(session.value.number, {
    name: dish.name,
    amount: dish.price,
    source: 'customer',
    quantity: 1,
    note: '详情页追加'
  })
  lastRefreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  actionNotice.value = `${dish.name} 已加入当前号码`
}
</script>

<template>
  <view class="page compact-page customer-detail-page scenic-customer-page">
    <view class="customer-detail-hero">
      <view class="customer-hero-top">
        <view>
          <text class="customer-hello">{{ storeName }}</text>
          <text class="customer-store-name">号码详情</text>
        </view>
        <button class="customer-refresh-button" @click="refreshSession">刷新</button>
      </view>
      <view v-if="session" class="customer-number-display">
        <text>{{ session.number }}</text>
        <text>{{ statusText(session.status) }}</text>
      </view>
      <text class="customer-hero-desc">{{ lastRefreshedAt ? `已同步 ${lastRefreshedAt}` : '后台每 15 秒自动刷新当前号码状态' }}</text>
    </view>

    <view v-if="apiNotice" class="api-notice customer-notice">{{ apiNotice }}</view>
    <view v-if="actionNotice" class="action-notice customer-notice">{{ actionNotice }}</view>

    <view class="customer-quick-card compact-bind-card">
      <view class="customer-bind-grid single-action-grid">
        <view class="customer-field">
          <text>切换号码</text>
          <input v-model="bindNumberInput" class="customer-input strong" placeholder="输入号码，如 A018" />
        </view>
        <button class="customer-primary-button" @click="bindNumber()">绑定</button>
      </view>
    </view>

    <view v-if="session" class="customer-stat-grid">
      <view><text>{{ session.people_count }}</text><text>用餐人数</text></view>
      <view><text>{{ totalQuantity }}</text><text>菜品数量</text></view>
      <view><text>¥{{ session.total_amount }}</text><text>当前合计</text></view>
    </view>

    <view v-if="session" class="card customer-progress-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">PROGRESS</text>
          <text class="customer-section-title">当前进度</text>
        </view>
        <text class="customer-section-more">{{ statusText(session.status) }}</text>
      </view>
      <view class="customer-timeline">
        <view v-for="(step, index) in progressSteps" :key="step.key" class="timeline-item" :class="{ active: index <= currentStepIndex }">
          <view class="timeline-dot">{{ index + 1 }}</view>
          <view>
            <text>{{ step.label }}</text>
            <text>{{ step.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="session" class="card customer-order-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">ORDER</text>
          <text class="customer-section-title">当前订单</text>
        </view>
        <text class="customer-section-more">{{ session.items?.length || 0 }} 项</text>
      </view>
      <view class="customer-order-list">
        <view v-for="item in session.items" :key="`${item.name}-${item.note}`" class="customer-order-row">
          <view>
            <text>{{ item.name }}</text>
            <text>{{ item.note || item.source }}</text>
          </view>
          <text>x{{ item.quantity }}</text>
          <text>¥{{ item.subtotal || item.amount }}</text>
        </view>
      </view>
      <view v-if="!session.items?.length" class="customer-empty">暂无菜品，可先让店员下单或在下方追加。</view>
      <text class="customer-remark-line">备注：{{ session.remark || '暂无备注' }}</text>
    </view>

    <view v-if="session" class="card customer-menu-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">ADD</text>
          <text class="customer-section-title">可追加菜品</text>
        </view>
        <text class="customer-section-more">点一下加入当前号码</text>
      </view>
      <view class="customer-add-list">
        <view v-for="dish in availableDishes" :key="dish.name" class="customer-add-row">
          <view class="customer-dish-cover small">锅</view>
          <view>
            <text>{{ dish.name }}</text>
            <text>¥{{ dish.price }} · {{ dish.category || '推荐' }}</text>
          </view>
          <button @click="addDish(dish)">加菜</button>
        </view>
      </view>
    </view>

    <view v-if="session" class="card customer-action-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">SERVICE</text>
          <text class="customer-section-title">服务与备注</text>
        </view>
      </view>
      <textarea v-model="remarkDraft" maxlength="80" class="customer-textarea" placeholder="补充口味、加汤、打包等备注" />
      <button class="customer-secondary-button full" @click="submitRemark">提交备注</button>
      <input v-model="serviceMessage" class="customer-input service-input" placeholder="例如：需要餐巾纸、帮忙加汤" />
      <view class="customer-button-row">
        <button class="customer-secondary-button" @click="callService">呼叫店员</button>
        <button class="customer-primary-button" :disabled="checkoutState.disabled" @click="callCheckout">{{ checkoutState.label }}</button>
      </view>
      <text v-if="checkoutState.disabled" class="customer-disabled-hint">{{ checkoutState.hint }}</text>
    </view>

    <view class="detail-footer-actions customer-footer-actions">
      <button class="ghost-link" @click="uni.navigateTo({ url: '/pages/index/index' })">返回首页</button>
      <button class="ghost-link primary-link" @click="refreshSession">刷新当前号码</button>
    </view>
  </view>
</template>
