<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { DataLine, Refresh } from '@element-plus/icons-vue'
import { fetchCashierPending, fetchStoreQueue, type MealSession } from '../api'

const storeId = 1
const queue = ref<MealSession[]>([])
const pending = ref<MealSession[]>([])
const apiNotice = ref('')
const loading = ref(false)
const lastRefreshAt = ref('')

onMounted(loadReports)

async function loadReports() {
  loading.value = true
  try {
    const [queuePayload, pendingPayload] = await Promise.all([fetchStoreQueue(storeId), fetchCashierPending(storeId)])
    queue.value = queuePayload
    pending.value = pendingPayload
    apiNotice.value = ''
    lastRefreshAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '统计加载失败'
  } finally {
    loading.value = false
  }
}

const reportCards = computed(() => [
  { label: '今日发号', value: queue.value.length },
  { label: '完成单数', value: queue.value.filter((item) => item.status === 'completed').length },
  { label: '待结账', value: pending.value.length },
  { label: '待收金额', value: `¥${pending.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0).toFixed(2)}` },
  { label: '平均等待时间', value: '18 分钟' }
])

const statusBreakdown = computed(() => {
  const counts: Record<string, number> = {}
  for (const session of queue.value) {
    counts[session.status] = (counts[session.status] || 0) + 1
  }
  return counts
})

const topWaiters = computed(() =>
  queue.value
    .filter((item) => ['occupied', 'preparing', 'called'].includes(item.status))
    .slice(0, 5)
)
</script>

<template>
  <div class="route-page reports-page">
    <header class="topbar">
      <div>
        <p>经营 / 统计</p>
        <h1>统计报表</h1>
        <p class="route-description">查看发号、完成、待收银和平均等待时间的基础统计</p>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
        <p v-else class="screen-meta">最近刷新：{{ lastRefreshAt || '暂无' }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadReports">刷新统计</el-button>
      </div>
    </header>

    <section class="stats-grid">
      <article v-for="card in reportCards" :key="card.label" class="stat-card">
        <div class="stat-icon blue">
          <el-icon><DataLine /></el-icon>
        </div>
        <div>
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <p>今日汇总</p>
        </div>
      </article>
    </section>

    <section class="main-grid">
      <article class="panel">
        <div class="panel-title">
          <h2>状态分布</h2>
        </div>
        <ul class="rule-list">
          <li v-for="(count, status) in statusBreakdown" :key="status">
            {{ status }}：{{ count }} 单
          </li>
        </ul>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>高等待号码</h2>
        </div>
        <ul class="rule-list">
          <li v-for="item in topWaiters" :key="item.number">
            {{ item.number }} · {{ item.status }} · {{ item.people_count }} 人
          </li>
        </ul>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>口径说明</h2>
        </div>
        <ul class="rule-list">
          <li>统计口径基于当前门店活跃号码和待收银号码</li>
          <li>平均等待时间暂按配置值展示，后续可替换为真实 SLA</li>
          <li>后端可继续扩展按天、按班次、按门店聚合</li>
        </ul>
      </article>
    </section>
  </div>
</template>
