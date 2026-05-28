<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh, Warning } from '@element-plus/icons-vue'
import { fetchStoreQueue, runSessionAction, type MealSession, type SessionAction } from '../api'
import type { AdminRouteMeta } from '../router'
import {
  buildProductionColumns,
  getProductionPrimaryAction,
  type ProductionColumn
} from '../production-workbench'

const meta: AdminRouteMeta = {
  title: '制作工作台',
  crumb: '工作台 / 制作',
  description: '聚焦待制作、制作中和已叫号号码，大按钮推进厨房动作'
}

const sessions = ref<MealSession[]>([])
const apiNotice = ref('')
const busyNumber = ref('')
const lastActionNotice = ref('')

const columns = computed(() => buildProductionColumns(sessions.value))
const totalCount = computed(() =>
  columns.value.reduce((sum: number, column: ProductionColumn) => sum + column.items.length, 0)
)
const hasWork = computed(() => totalCount.value > 0)

onMounted(loadQueue)

async function loadQueue() {
  try {
    sessions.value = await fetchStoreQueue(1)
    apiNotice.value = ''
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '队列加载失败'
  }
}

async function runAction(number: string, action: SessionAction) {
  busyNumber.value = number
  lastActionNotice.value = ''
  try {
    await runSessionAction(number, action)
    lastActionNotice.value = `${number} 已执行 ${action}`
    await loadQueue()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '操作失败'
  } finally {
    busyNumber.value = ''
  }
}

function formatAmount(amount: string | undefined) {
  return `¥${amount || '0.00'}`
}

function itemSummary(session: MealSession) {
  if (!session.items.length) return '暂无登记菜品'
  return session.items.map((item) => `${item.name} x${item.quantity}`).join('、')
}

function columnHint(column: ProductionColumn) {
  if (column.items.length) return `当前 ${column.items.length} 单`
  return '暂无需要处理的号码'
}
</script>

<template>
  <div class="route-page production-page">
    <header class="topbar">
      <div>
        <p>{{ meta.crumb }}</p>
        <h1>{{ meta.title }}</h1>
        <p class="route-description">{{ meta.description }}</p>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
        <p v-else-if="lastActionNotice" class="api-notice success-notice">{{ lastActionNotice }}</p>
      </div>
      <div class="top-actions">
        <el-tag type="warning">{{ totalCount }} 单在厨房队列</el-tag>
        <el-button :icon="Refresh" @click="loadQueue">刷新队列</el-button>
      </div>
    </header>

    <section class="production-board">
      <article v-for="column in columns" :key="column.key" class="panel production-column">
        <div class="panel-title">
          <h2>{{ column.title }}</h2>
          <el-tag>{{ column.items.length }}</el-tag>
        </div>
        <p class="production-column-hint">{{ columnHint(column) }}</p>

        <el-empty v-if="!column.items.length" description="暂无号码" :image-size="72" />

        <div v-for="session in column.items" :key="session.number" class="production-card">
          <div class="production-card-head">
            <strong>{{ session.number }}</strong>
            <span>{{ formatAmount(session.total_amount) }}</span>
          </div>

          <p :class="['production-remark', { empty: !session.remark }]">
            {{ session.remark || '无备注' }}
          </p>

          <p class="production-items">{{ itemSummary(session) }}</p>
          <p class="production-meta">{{ session.people_count }} 人 · {{ session.items.length }} 项</p>

          <div class="production-actions">
            <el-button
              v-if="getProductionPrimaryAction(session)"
              :type="getProductionPrimaryAction(session)!.type"
              size="large"
              :loading="busyNumber === session.number"
              @click="runAction(session.number, getProductionPrimaryAction(session)!.action as SessionAction)"
            >
              {{ getProductionPrimaryAction(session)!.label }}
            </el-button>
            <el-button
              v-if="['occupied', 'preparing', 'called'].includes(session.status)"
              size="large"
              plain
              type="warning"
              :loading="busyNumber === session.number"
              @click="runAction(session.number, 'skip')"
            >
              暂时跳号
            </el-button>
          </div>
        </div>
      </article>
    </section>

    <article class="panel production-tip">
      <div class="panel-title">
        <h2>操作提示</h2>
        <el-icon><Warning /></el-icon>
      </div>
      <p>备注会高亮显示，优先处理有口味要求的号码。叫号后顾客取餐请点“确认取餐”。</p>
      <p v-if="!hasWork" class="production-empty-tip">当前没有可制作号码，刷新后再查看。</p>
    </article>
  </div>
</template>
