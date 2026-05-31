<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchMealSession, fetchStoreCatalog, issueQueueNumber } from '../../api'
import { normalizeQueueNumber, parseBindingParams, validateBoundSession } from '../../binding.mjs'

const store = ref(null)
const catalog = ref(null)
const selectedStoreId = ref(1)
const bindNumberInput = ref('')
const peopleCountInput = ref(2)
const remarkInput = ref('')
const notice = ref('')
const loading = ref(false)
const issuing = ref(false)

onLoad(async (options) => {
  const binding = parseBindingParams(options || {})
  selectedStoreId.value = binding.storeId
  bindNumberInput.value = binding.number
  await loadStore()
  if (binding.number) {
    await bindNumber()
  }
})

const storeStatusText = computed(() => {
  if (!store.value) return '门店读取中'
  return store.value.business_status === 'open' ? '营业中' : '休息中'
})
const storeStatusClass = computed(() => (store.value?.business_status === 'open' ? 'is-open' : 'is-closed'))
const featuredDishes = computed(() => (catalog.value?.dishes || []).filter((item) => item.available).slice(0, 6))
const storeTips = computed(() => [
  { label: '预计等待', value: `${store.value?.avg_prepare_minutes || 18} 分钟` },
  { label: '营业时间', value: store.value?.business_hours || '读取中' },
  { label: '门店地址', value: store.value?.address || '请确认门店二维码' }
])

async function loadStore() {
  try {
    const payload = await fetchStoreCatalog(selectedStoreId.value)
    catalog.value = payload
    store.value = payload.store
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '门店信息加载失败'
  }
}

async function bindNumber() {
  const number = normalizeQueueNumber(bindNumberInput.value)
  if (!number) {
    notice.value = '请输入店员发放的号码'
    return
  }
  loading.value = true
  notice.value = ''
  try {
    const session = await fetchMealSession(number)
    validateBoundSession(session, selectedStoreId.value, number)
    uni.navigateTo({ url: `/pages/detail/detail?store_id=${selectedStoreId.value}&number=${number}` })
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '号码绑定失败'
  } finally {
    loading.value = false
  }
}

async function issueNumber() {
  issuing.value = true
  notice.value = ''
  try {
    const session = await issueQueueNumber(selectedStoreId.value, {
      people_count: Number(peopleCountInput.value) || 1,
      remark: remarkInput.value.trim()
    })
    bindNumberInput.value = session.number
    uni.navigateTo({ url: `/pages/detail/detail?store_id=${selectedStoreId.value}&number=${session.number}` })
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '取号失败，请稍后再试'
  } finally {
    issuing.value = false
  }
}
</script>

<template>
  <view class="page app-page customer-home scenic-customer-page">
    <view class="customer-hero-card">
      <view class="customer-hero-top">
        <view>
          <text class="customer-hello">欢迎光临</text>
          <text class="customer-store-name">{{ store?.name || '等锅叫号' }}</text>
        </view>
        <text class="customer-status" :class="storeStatusClass">{{ storeStatusText }}</text>
      </view>
      <text class="customer-hero-title">扫码取号，边等边逛菜单</text>
      <text class="customer-hero-desc">绑定号码后可实时看进度、追加菜品、补充口味、呼叫服务与结账。</text>
      <view class="customer-hero-actions">
        <button class="customer-white-button" @click="issueNumber">{{ issuing ? '取号中' : '立即取号' }}</button>
        <button class="customer-outline-button" @click="bindNumber">绑定已有号码</button>
      </view>
    </view>

    <view v-if="notice" class="api-notice customer-notice">{{ notice }}</view>

    <view class="customer-quick-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">QUEUE</text>
          <text class="customer-section-title">我的排队号码</text>
        </view>
        <text class="customer-section-more">{{ store?.queue_prefix || 'A' }} 系列</text>
      </view>
      <view class="customer-bind-grid">
        <view class="customer-field">
          <text>已有号码</text>
          <input v-model="bindNumberInput" class="customer-input strong" placeholder="A018" />
        </view>
        <view class="customer-field small-field">
          <text>用餐人数</text>
          <input v-model="peopleCountInput" class="customer-input" type="number" placeholder="2" />
        </view>
      </view>
      <view class="customer-field">
        <text>取号备注</text>
        <input v-model="remarkInput" class="customer-input" placeholder="例如：带小朋友、需要宝宝椅" />
      </view>
      <view class="customer-button-row">
        <button class="customer-primary-button" :disabled="issuing" @click="issueNumber">{{ issuing ? '正在取号' : '门店取号' }}</button>
        <button class="customer-secondary-button" :disabled="loading" @click="bindNumber">{{ loading ? '绑定中' : '查进度' }}</button>
      </view>
    </view>

    <view class="customer-feature-strip">
      <view><text>进度</text><text>实时刷新</text></view>
      <view><text>加菜</text><text>快速追加</text></view>
      <view><text>服务</text><text>一键呼叫</text></view>
      <view><text>结账</text><text>通知收银</text></view>
    </view>

    <view class="card customer-menu-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">MENU</text>
          <text class="customer-section-title">今日推荐</text>
        </view>
        <text class="customer-section-more">到号后可继续加菜</text>
      </view>
      <view class="customer-dish-grid">
        <view v-for="dish in featuredDishes" :key="dish.name" class="customer-dish-card">
          <view class="customer-dish-cover">锅</view>
          <view>
            <text class="customer-dish-name">{{ dish.name }}</text>
            <text class="customer-dish-category">{{ dish.category || '推荐' }}</text>
          </view>
          <text class="customer-dish-price">¥{{ dish.price }}</text>
        </view>
      </view>
      <view v-if="featuredDishes.length === 0" class="customer-empty">菜单读取中，请稍候</view>
    </view>

    <view class="card customer-info-card">
      <view class="customer-section-head">
        <view>
          <text class="customer-section-kicker">STORE</text>
          <text class="customer-section-title">门店信息</text>
        </view>
      </view>
      <view class="customer-info-list">
        <view v-for="tip in storeTips" :key="tip.label">
          <text>{{ tip.label }}</text>
          <text>{{ tip.value }}</text>
        </view>
      </view>
    </view>
  </view>
</template>
