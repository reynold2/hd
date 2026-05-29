<script setup>
import { computed, onMounted, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchMealSession, fetchStoreCatalog } from '../../api'
import { normalizeQueueNumber, parseBindingParams, validateBoundSession } from '../../binding.mjs'

const pageOptions = ref({})
const store = ref(null)
const selectedStoreId = ref(1)
const bindNumberInput = ref('')
const notice = ref('')
const loading = ref(false)

onLoad((options) => {
  pageOptions.value = options || {}
})

onMounted(async () => {
  const search = typeof window === 'undefined' ? '' : window.location.search
  const binding = parseBindingParams(pageOptions.value, search)
  selectedStoreId.value = binding.storeId
  bindNumberInput.value = binding.number
  await loadStore()
  if (binding.number) {
    await bindNumber()
  }
})

const storeStatusText = computed(() => {
  if (!store.value) return '读取中'
  return store.value.business_status === 'open' ? '营业中' : '休息中'
})

async function loadStore() {
  try {
    const catalog = await fetchStoreCatalog(selectedStoreId.value)
    store.value = catalog.store
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
</script>

<template>
  <view class="page">
    <view class="hero">
      <view>
        <text class="store-name">{{ store?.name || '等锅叫号' }}</text>
        <view class="store-meta">
          <text>{{ storeStatusText }}</text>
          <text>{{ store?.business_hours || '营业时间读取中' }}</text>
          <text>{{ store?.address || '请确认门店二维码' }}</text>
        </view>
      </view>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="card">
      <view class="section-title">
        <text>绑定号码</text>
        <text>输入店员给你的号码</text>
      </view>
      <view class="bind-card clean-bind-card">
        <input v-model="bindNumberInput" placeholder="例如 A018" />
        <button :disabled="loading" @click="bindNumber">{{ loading ? '绑定中' : '绑定' }}</button>
      </view>
    </view>
  </view>
</template>
