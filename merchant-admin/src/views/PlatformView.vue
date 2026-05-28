<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { CircleCheck, CircleClose, DocumentChecked, Refresh, UserFilled } from '@element-plus/icons-vue'

const loading = ref(false)
const notice = ref('')

const merchantAudits = reactive([
  { name: '麻辣烫示例商户', store: '中山店', status: 'pending', package: '标准版', city: '杭州' },
  { name: '串串示例商户', store: '火锅街店', status: 'approved', package: '旗舰版', city: '成都' },
  { name: '炸串示例商户', store: '大学城店', status: 'processing', package: '标准版', city: '广州' }
])

const packageRules = reactive([
  { name: '标准版', storeLimit: 3, staffLimit: 8, enabled: ['队列', '收银', '统计'] },
  { name: '旗舰版', storeLimit: 20, staffLimit: 50, enabled: ['队列', '收银', '统计', '大屏', '平台审核'] }
])

const platformStats = [
  { label: '商户数', value: '18', icon: UserFilled },
  { label: '门店数', value: '26', icon: DocumentChecked },
  { label: '活跃号码', value: '143', icon: CircleCheck },
  { label: '投诉处理中', value: '4', icon: CircleClose }
]

const complaintList = reactive([
  { title: '结账响应慢', merchant: '麻辣烫示例商户', status: '处理中' },
  { title: '门店资料待核验', merchant: '串串示例商户', status: '待补充' }
])

function review(status: string, target: (typeof merchantAudits)[number]) {
  target.status = status
  notice.value = `${target.name} · ${target.store} 已更新为 ${status}`
}

function refresh() {
  loading.value = true
  notice.value = '平台数据已刷新'
  setTimeout(() => (loading.value = false), 300)
}
</script>

<template>
  <div class="route-page platform-page">
    <header class="topbar">
      <div>
        <p>平台 / 审核</p>
        <h1>平台管理后台</h1>
        <p class="route-description">商户审核、门店审核、套餐权限和平台公告</p>
        <p v-if="notice" class="api-notice">{{ notice }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Refresh" :loading="loading" @click="refresh">刷新</el-button>
      </div>
    </header>

    <section class="stats-grid">
      <article v-for="card in platformStats" :key="card.label" class="stat-card">
        <div class="stat-icon green">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div>
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <p>平台视角</p>
        </div>
      </article>
    </section>

    <section class="main-grid">
      <article class="panel">
        <div class="panel-title">
          <h2>待审核商户</h2>
          <el-tag type="warning">审核队列</el-tag>
        </div>
        <div class="merchant-list">
          <div v-for="merchant in merchantAudits" :key="`${merchant.name}-${merchant.store}`" class="merchant-row">
            <div>
              <strong>{{ merchant.name }}</strong>
              <span>{{ merchant.store }} · {{ merchant.city }} · {{ merchant.package }}</span>
            </div>
            <el-tag>{{ merchant.status }}</el-tag>
            <div class="panel-actions">
              <el-button size="small" type="success" @click="review('approved', merchant)">通过</el-button>
              <el-button size="small" type="danger" @click="review('rejected', merchant)">拒绝</el-button>
            </div>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>套餐权限</h2>
          <el-tag type="info">平台配置</el-tag>
        </div>
        <div class="rule-list">
          <div v-for="rule in packageRules" :key="rule.name" class="package-card">
            <strong>{{ rule.name }}</strong>
            <p>门店上限：{{ rule.storeLimit }}，员工上限：{{ rule.staffLimit }}</p>
            <span>功能：{{ rule.enabled.join(' / ') }}</span>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>投诉 / 反馈</h2>
          <el-tag type="danger">待处理</el-tag>
        </div>
        <ul class="rule-list">
          <li v-for="item in complaintList" :key="item.title">
            {{ item.title }} · {{ item.merchant }} · {{ item.status }}
          </li>
        </ul>
      </article>
    </section>
  </div>
</template>
