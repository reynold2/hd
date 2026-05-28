<script setup>
import { computed, onMounted, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchStoreCatalog } from '../../api'
import { parseBindingParams } from '../../binding.mjs'

const fallbackStore = {
  name: '川香麻辣烫（中山店）',
  status: '营业中',
  time: '10:00-22:30',
  wait: '20-30 分钟',
  address: '中山市东区中山三路88号'
}

const fallbackCurrent = {
  number: '未绑定',
  people: 0,
  status: '待绑定',
  ahead: '-',
  wait: '扫码或输入号码',
  total: '0.00',
  remark: '绑定号码后显示备注',
  items: []
}

const catalog = ref(null)
const selectedStoreId = ref(1)
const bindNumberInput = ref('')
const apiNotice = ref('')
const actionNotice = ref('')
const pageOptions = ref({})
const initialized = ref(false)

onLoad((options) => {
  pageOptions.value = options || {}
  initializePage()
})

onMounted(async () => {
  await initializePage()
})

const store = computed(() => {
  if (!catalog.value) return fallbackStore
  return {
    name: catalog.value.store.name,
    status: catalog.value.store.business_status === 'open' ? '营业中' : '休息中',
    time: catalog.value.store.business_hours,
    wait: `${catalog.value.store.avg_prepare_minutes}-30 分钟`,
    address: catalog.value.store.address
  }
})

const current = computed(() => fallbackCurrent)

async function initializePage() {
  if (initialized.value) return
  initialized.value = true

  try {
    const search = typeof window === 'undefined' ? '' : window.location.search
    const binding = parseBindingParams(pageOptions.value, search)
    selectedStoreId.value = binding.storeId
    bindNumberInput.value = binding.number
    catalog.value = await fetchStoreCatalog(selectedStoreId.value)

    if (binding.number) {
      actionNotice.value = `${binding.number} 已预填，可进入详情页继续操作`
    } else {
      apiNotice.value = '请扫码或输入店员给你的号码'
    }
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '接口暂不可用'
  }
}

function bindNumber() {
  const number = bindNumberInput.value.trim()
  if (!number) {
    actionNotice.value = '请输入号码'
    return
  }
  uni.navigateTo({
    url: `/pages/detail/detail?store_id=${selectedStoreId.value}&number=${encodeURIComponent(number)}`
  })
}

function openDetailPage() {
  const number = bindNumberInput.value.trim()
  if (!number) {
    actionNotice.value = '请先输入号码再查看详情'
    return
  }
  bindNumber()
}

const fallbackDishes = [
  { name: '招牌麻辣烫', price: '¥12.00' },
  { name: '牛肉串', price: '¥15.00' },
  { name: '宽粉', price: '¥2.00' },
  { name: '冰粉', price: '¥6.00' }
]
const dishes = computed(() =>
  !catalog.value
    ? fallbackDishes
    : catalog.value.dishes.filter((dish) => dish.available).map((dish) => ({
        name: dish.name,
        price: `¥${dish.price}`
      }))
)
</script>

<template>
  <view class="page">
    <view class="hero">
      <view>
        <text class="store-name">{{ store.name }}</text>
        <view class="store-meta">
          <text>{{ store.status }}</text>
          <text>{{ store.time }}</text>
          <text>预计等待 {{ store.wait }}</text>
        </view>
      </view>
      <button class="ghost-button" @click="openDetailPage">进入详情</button>
    </view>

    <view v-if="apiNotice" class="api-notice">{{ apiNotice }}</view>
    <view v-if="actionNotice" class="action-notice">{{ actionNotice }}</view>

    <view class="bind-card">
      <input v-model="bindNumberInput" placeholder="输入号码，如 A018" />
      <button @click="bindNumber">绑定并进入详情</button>
    </view>

    <view class="number-card">
      <view class="number-head">
        <text>首页概览</text>
        <text class="status-pill">{{ current.status }}</text>
      </view>
      <text class="number">{{ current.number }}</text>
      <text class="number-tip">首页只展示门店、绑定入口和当前概览，详情操作已拆到独立页面。</text>
      <view class="number-metrics">
        <view>
          <text>{{ current.ahead }}</text>
          <text>前方还有</text>
        </view>
        <view>
          <text>{{ current.wait }}</text>
          <text>预计等待</text>
        </view>
        <view>
          <text>¥{{ current.total || '0.00' }}</text>
          <text>当前金额</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>页面拆分说明</text>
        <text>主流程已按首页 / 详情页分开</text>
      </view>
      <view class="timeline">
        <view class="step done">
          <view class="dot"></view>
          <view><text>首页</text><text>查看门店、输入号码、进入详情</text></view>
        </view>
        <view class="step active">
          <view class="dot"></view>
          <view><text>详情页</text><text>绑定验证、追加、备注、服务、结账</text></view>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>当前可见菜品</text>
        <text>仅用于浏览</text>
      </view>
      <view class="dish-list">
        <view v-for="dish in dishes" :key="dish.name" class="dish-row">
          <view class="dish-thumb"></view>
          <view>
            <text>{{ dish.name }}</text>
            <text>{{ dish.price }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="page-footnote">
      <text>顾客端 C-02 已按页面角色拆分，首页负责入口与概览，详情页负责业务动作。</text>
    </view>
  </view>
</template>
