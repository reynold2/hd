<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { fetchStoreQueue, runSessionAction, type MealSession } from '../api'

const storeId = 1
const queue = ref<MealSession[]>([])
const notice = ref('')
const loading = ref(false)
const lastRefreshAt = ref('')

onMounted(loadScreen)

async function loadScreen() {
  loading.value = true
  try {
    queue.value = await fetchStoreQueue(storeId)
    notice.value = ''
    lastRefreshAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '大屏加载失败'
  } finally {
    loading.value = false
  }
}

const current = computed(() => queue.value.find((item) => ['called', 'dining', 'preparing'].includes(item.status)) || queue.value[0])
const recent = computed(() => queue.value.slice(0, 6))
const waiting = computed(() => queue.value.filter((item) => item.status === 'occupied'))
const lastCalled = computed(() => queue.value.filter((item) => item.status === 'called').slice(0, 3))

async function refreshCall() {
  if (!current.value) return
  try {
    await runSessionAction(current.value.number, 'call')
    notice.value = `已重新播报 ${current.value.number}`
    await loadScreen()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '播报失败'
  }
}
</script>

<template>
  <div class="screen-page">
    <header class="screen-header">
      <div>
        <p>展示 / 大屏</p>
        <h1>当前叫号</h1>
        <p v-if="notice" class="api-notice">{{ notice }}</p>
        <p v-else class="screen-meta">最近刷新：{{ lastRefreshAt || '暂无' }}</p>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="loadScreen">刷新大屏</el-button>
    </header>

    <section class="screen-hero">
      <div class="screen-current">
        <span>正在叫号</span>
        <strong>{{ current?.number || 'A018' }}</strong>
        <p>{{ current ? current.remark || '暂无备注' : '等待更多号码' }}</p>
        <el-button type="success" @click="refreshCall">重新播报</el-button>
      </div>
      <div class="screen-summary">
        <article>
          <span>最近叫号</span>
          <strong>{{ recent.length }}</strong>
        </article>
        <article>
          <span>等待队列</span>
          <strong>{{ waiting.length }}</strong>
        </article>
        <article>
          <span>当前刷新</span>
          <strong>{{ lastRefreshAt || '--:--' }}</strong>
        </article>
      </div>
    </section>

    <section class="screen-grid">
      <article class="panel">
        <div class="panel-title">
          <h2>最近叫号</h2>
        </div>
        <div class="screen-list">
          <div v-for="item in recent" :key="item.number" class="screen-row">
            <strong>{{ item.number }}</strong>
            <span>{{ item.status }}</span>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>最近已叫号码</h2>
        </div>
        <div class="screen-list">
          <div v-for="item in lastCalled" :key="item.number" class="screen-row">
            <strong>{{ item.number }}</strong>
            <span>{{ item.people_count }} 人 · {{ item.remark || '无备注' }}</span>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>等待队列</h2>
        </div>
        <div class="screen-list">
          <div v-for="item in waiting" :key="item.number" class="screen-row">
            <strong>{{ item.number }}</strong>
            <span>{{ item.people_count }} 人 · {{ item.remark || '无备注' }}</span>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>
