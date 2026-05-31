<script setup>
import { computed, onMounted, ref } from 'vue'
import { completeKitchenOrder, fetchKitchenCompleted, fetchKitchenQueue, fetchStoreCatalog, startKitchenOrder } from '../../api'

const activeTab = ref('home')
const loading = ref(false)
const notice = ref('')
const store = ref(null)
const orders = ref([])
const doneOrders = ref([])
const storeId = ref(1)

const pendingOrders = computed(() => orders.value.filter((order) => order.status !== 'done'))
const preparingCount = computed(() => orders.value.filter((order) => order.status === 'preparing').length)
const pendingCount = computed(() => orders.value.filter((order) => order.status === 'pending').length)
const doneCount = computed(() => doneOrders.value.length)

function buildTags(item) {
  const tags = [...(item.tags || [])]
  if (item.people_count) tags.unshift(`${item.people_count}人`)
  if (item.remark) tags.push(item.remark.split('\n').filter(Boolean).slice(-1)[0] || item.remark)
  return tags.filter(Boolean).slice(0, 3)
}

async function loadData() {
  loading.value = true
  notice.value = ''
  try {
    const [catalog, queue, completed] = await Promise.all([
      fetchStoreCatalog(storeId.value),
      fetchKitchenQueue(storeId.value),
      fetchKitchenCompleted(storeId.value)
    ])
    store.value = catalog.store
    orders.value = queue.map((item) => ({
      number: item.number,
      status: item.status === 'preparing' || item.status === 'called' ? 'preparing' : 'pending',
      tags: buildTags(item)
    }))
    doneOrders.value = completed.map((item) => ({
      number: item.number,
      tags: buildTags(item),
      status: item.status || 'called'
    }))
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '制作队列加载失败'
    orders.value = []
    doneOrders.value = []
  } finally {
    loading.value = false
  }
}

function setTab(tab) {
  activeTab.value = tab
}

function findOrder(number) {
  return orders.value.find((item) => item.number === number)
}

async function markOrder(order) {
  notice.value = ''
  const current = findOrder(order.number)
  if (!current) return
  loading.value = true
  try {
    if (current.status === 'pending') {
      const updated = await startKitchenOrder(storeId.value, current.number)
      current.status = updated.status === 'preparing' || updated.status === 'called' ? 'preparing' : 'pending'
      notice.value = `${current.number} 已进入制作中`
      return
    }
    await completeKitchenOrder(storeId.value, current.number)
    notice.value = `${current.number} 已完成并已自动叫号`
    await loadData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

function resetView() {
  activeTab.value = 'home'
  loadData()
}

function statusText(status) {
  if (status === 'preparing') return '制作中'
  if (status === 'done') return '已完成'
  return '待制作'
}

onMounted(async () => {
  const launchOptions = typeof uni !== 'undefined' ? uni.getLaunchOptionsSync?.() || {} : {}
  storeId.value = Number(launchOptions?.query?.store_id || 1)
  await loadData()
})
</script>

<template>
  <view class="page role-page kitchen-page">
    <view class="hero kitchen-hero">
      <view>
        <text class="store-name">{{ store?.name || '等锅叫号' }} · 制作首页</text>
        <view class="store-meta">
          <text>点一下变绿，第二次点击完成并自动呼叫</text>
          <text>当前待制作 {{ pendingCount }} 单 · 制作中 {{ preparingCount }} 单</text>
        </view>
      </view>
      <button class="ghost-button" :disabled="loading" @click="resetView">刷新</button>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="kitchen-stats">
      <view class="stat-card">
        <text class="stat-value">{{ pendingCount }}</text>
        <text class="stat-label">待制作</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ preparingCount }}</text>
        <text class="stat-label">制作中</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ doneCount }}</text>
        <text class="stat-label">已完成</text>
      </view>
    </view>

    <view class="action-notice">第一次点击进入制作中，第二次点击完成并自动发送取餐呼叫。</view>

    <view v-if="activeTab === 'home'" class="card kitchen-board">
      <view class="section-title">
        <text>制作首页</text>
        <text>{{ pendingOrders.length }} 张卡片</text>
      </view>
      <view class="kitchen-grid">
        <button
          v-for="order in pendingOrders"
          :key="order.number"
          class="kitchen-order"
          :class="[`status-${order.status}`]"
          :disabled="loading"
          @click="markOrder(order)"
        >
          <view class="order-head">
            <text class="order-number">{{ order.number }}</text>
            <text class="order-status">{{ statusText(order.status) }}</text>
          </view>
          <view class="order-tags">
            <text v-for="tag in order.tags" :key="tag" class="order-tag">{{ tag }}</text>
          </view>
        </button>
      </view>
    </view>

    <view v-else class="card kitchen-board">
      <view class="section-title">
        <text>已完成列表</text>
        <text>{{ doneOrders.length }} 张卡片</text>
      </view>
      <view class="done-list">
        <view v-for="order in doneOrders" :key="order.number" class="done-item">
          <text class="done-number">{{ order.number }}</text>
          <text class="done-tags">{{ order.tags.join(' / ') }}</text>
        </view>
      </view>
    </view>

    <view class="checkout-bar kitchen-nav">
      <button :class="{ active: activeTab === 'home' }" @click="setTab('home')">制作首页</button>
      <button :class="{ active: activeTab === 'done' }" @click="setTab('done')">已完成列表</button>
    </view>
  </view>
</template>
