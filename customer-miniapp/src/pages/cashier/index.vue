<script setup>
import { onMounted, ref } from 'vue'
import { fetchStoreCatalog } from '../../api'

const store = ref(null)

onMounted(async () => {
  try {
    const result = await fetchStoreCatalog(1)
    store.value = result.store
  } catch {
    store.value = null
  }
})
</script>

<template>
  <view class="page role-page compact-page">
    <view class="hero">
      <view>
        <text class="store-name">{{ store?.name || '店员工作台' }}</text>
        <view class="store-meta">
          <text>收银入口已并入服务员工作台</text>
          <text>结账、核对、支付确认统一处理</text>
        </view>
      </view>
      <view class="hero-badge">统一入口</view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>页面说明</text>
        <text>合并后入口</text>
      </view>
      <view class="item-cloud">
        <text>收银点入口已切到服务员界面</text>
        <text>保留结账提醒与支付确认流程</text>
        <text>后续操作统一从店员工作台完成</text>
      </view>
    </view>
  </view>
</template>
