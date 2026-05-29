<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Clock, DataAnalysis, Refresh, TrendCharts, Money, Tickets } from '@element-plus/icons-vue'
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

const summary = computed(() => {
  const finished = queue.value.filter((item) => item.status === 'completed')
  const waiting = queue.value.filter((item) => ['occupied', 'preparing', 'called'].includes(item.status))
  const pendingAmount = pending.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)

  return [
    { label: '今日收入', value: `¥${pendingAmount.toFixed(2)}`, note: '来自待结账与已确认收款汇总', icon: Money, tone: 'warm' },
    { label: '今日发号', value: queue.value.length, note: '当天累计发出的号码', icon: Tickets, tone: 'blue' },
    { label: '完成单数', value: finished.length, note: '已完成并释放的餐次', icon: DataAnalysis, tone: 'green' },
    { label: '平均等待', value: '18 分钟', note: '按当前门店配置与样例数据估算', icon: Clock, tone: 'purple' }
  ]
})

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

const recentSessions = computed(() => queue.value.slice(0, 6))
</script>

<template>
  <div class="route-page reports-page">
    <header class="topbar reports-topbar">
      <div>
        <p>经营 / 统计</p>
        <h1>统计报表</h1>
        <p class="route-description">老板看经营结果的总览页，重点展示今日收入、发号、完成与等待情况</p>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
        <p v-else class="screen-meta">最近刷新：{{ lastRefreshAt || '暂无' }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadReports">刷新统计</el-button>
      </div>
    </header>

    <section class="stats-grid reports-summary-grid">
      <article v-for="card in summary" :key="card.label" class="stat-card report-card">
        <div :class="['stat-icon', card.tone]">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div>
          <span>{{ card.label }}</span>
          <strong>{{ card.value }} <small v-if="card.label === '今日收入'">元</small></strong>
          <p>{{ card.note }}</p>
        </div>
      </article>
    </section>

    <section class="reports-layout">
      <article class="panel chart-panel">
        <div class="panel-title">
          <h2>状态分布</h2>
          <el-tag type="success">经营概览</el-tag>
        </div>
        <div class="status-bars">
          <div v-for="(count, status) in statusBreakdown" :key="status" class="status-bar-row">
            <div class="status-bar-label">
              <span>{{ status }}</span>
              <strong>{{ count }}</strong>
            </div>
            <div class="status-bar-track">
              <i :style="{ width: `${Math.max(12, count * 18)}%` }"></i>
            </div>
          </div>
        </div>
      </article>

      <article class="panel ranking-panel">
        <div class="panel-title">
          <h2>高等待号码</h2>
          <el-tag type="warning">需关注</el-tag>
        </div>
        <div class="rank-list">
          <div v-for="item in topWaiters" :key="item.number" class="rank-row">
            <div class="rank-num">{{ item.number }}</div>
            <div class="rank-meta">
              <strong>{{ item.status }}</strong>
              <span>{{ item.people_count }} 人 · {{ item.remark || '无备注' }}</span>
            </div>
          </div>
        </div>
      </article>

      <article class="panel recent-panel">
        <div class="panel-title">
          <h2>最近号码</h2>
          <el-tag type="info">最近 6 条</el-tag>
        </div>
        <div class="recent-list">
          <div v-for="item in recentSessions" :key="item.number" class="recent-row">
            <strong>{{ item.number }}</strong>
            <span>{{ item.status }}</span>
            <small>{{ item.people_count }} 人</small>
          </div>
        </div>
      </article>

      <article class="panel note-panel">
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
