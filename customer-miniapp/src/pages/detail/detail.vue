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
const availableDishes = computed(() => (catalog.value?.dishes || []).filter((item) => item.available).slice(0, 4))

async function initializePage() {
  const search = typeof window === 'undefined' ? '' : window.location.search
  const binding = parseBindingParams(pageOptions.value, search)
  selectedStoreId.value = binding.storeId
  bindNumberInput.value = binding.number
  catalog.value = await fetchStoreCatalog(selectedStoreId.value)
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
  <view class="page compact-page">
    <view class="top-banner"><text>号码详情</text><text>进度、备注、服务、结账</text></view>
    <view v-if="apiNotice" class="api-notice">{{ apiNotice }}</view><view v-if="actionNotice" class="action-notice">{{ actionNotice }}</view>
    <view class="bind-card"><input v-model="bindNumberInput" placeholder="输入号码，如 A018" /><button @click="bindNumber()">绑定号码</button></view>
    <view v-if="session" class="card detail-summary">
      <view class="number-head">
        <text>当前号码</text>
        <text class="status-pill">{{ statusText(session.status) }}</text>
      </view>
      <text class="number">{{ session.number }}</text>
      <text class="number-tip">{{ session.people_count }} 人 · 合计 ¥{{ session.total_amount }}</text>
      <text class="detail-remark">{{ session.remark || '暂无备注' }}</text>
      <view class="detail-meta">
        <text>门店 #{{ selectedStoreId }}</text>
        <text>项目数 {{ session.items?.length || 0 }}</text>
      </view>
      <view class="refresh-hint">{{ lastRefreshedAt ? `已同步 ${lastRefreshedAt}` : '后台将自动刷新当前号码状态' }}</view>
    </view>
    <view v-if="session" class="card"><view class="section-title"><text>可追加菜品</text><text>点一下直接加到当前号码</text></view><view class="dish-list compact-dish-list"><view v-for="dish in availableDishes" :key="dish.name" class="dish-row"><view class="dish-thumb"></view><view><text>{{ dish.name }}</text><text>¥{{ dish.price }}</text></view><button @click="addDish(dish)">+</button></view></view></view>
    <view v-if="session" class="card"><view class="section-title"><text>补充备注</text></view><textarea v-model="remarkDraft" maxlength="80" placeholder="补充口味、加汤、打包等备注" /><button class="primary-line-button" @click="submitRemark">提交备注</button></view>
    <view v-if="session" class="card"><view class="section-title"><text>呼叫服务</text></view><input v-model="serviceMessage" placeholder="例如：需要餐巾纸、帮忙加汤" /><button @click="callService">呼叫店员</button></view>
    <view v-if="session" class="card"><view class="section-title"><text>呼叫结账</text></view><button :disabled="checkoutState.disabled" @click="callCheckout">{{ checkoutState.label }}</button></view>
    <view class="detail-footer-actions"><button class="ghost-link" @click="uni.navigateTo({ url: '/pages/index/index' })">返回首页</button><button class="ghost-link primary-link" @click="refreshSession">刷新当前号码</button></view>
  </view>
</template>
