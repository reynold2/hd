<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Calendar,
  Check,
  CirclePlus,
  Connection,
  DataLine,
  Document,
  Monitor,
  Operation,
  Setting,
  Tickets,
  User
} from '@element-plus/icons-vue'
import type { AdminRouteMeta } from '../router'

const route = useRoute()
const meta = computed(() => route.meta as AdminRouteMeta)
const saving = ref(false)
const saveNotice = ref('')

const platformRows = ref([
  { merchant: '川香麻辣烫', store: '城南店', status: '待审核', package: '基础版' },
  { merchant: '串串小院', store: '大学城店', status: '已通过', package: '专业版' }
])
const screenRows = ref([
  { number: 'A018', status: '制作中', remark: '少辣，不要葱' },
  { number: 'A019', status: '已叫号', remark: '微辣' },
  { number: 'A021', status: '待结账', remark: '不要香菜' }
])
const reportStats = ref([
  { label: '今日发号', value: 86, unit: '单' },
  { label: '完成单数', value: 71, unit: '单' },
  { label: '待结账', value: 9, unit: '单' },
  { label: '平均等待', value: 18, unit: '分钟' }
])

const storeForm = reactive({
  business_status: 'open',
  business_hours: '10:00-22:00',
  address: '门店地址待配置',
  avg_prepare_minutes: 12,
  number_prefix: 'A',
  payment_qr: 'store-qr-001'
})

const staffForm = reactive({
  name: '',
  role: 'cashier',
  status: 'enabled'
})

const ruleForm = reactive({
  max_people_per_number: 4,
  queue_timeout_minutes: 90,
  auto_complete_paid: true,
  allow_checkout_without_dining: true
})

const platformForm = reactive({
  audit_status: 'pending',
  package: '基础版',
  notice: '平台公告待配置'
})

const settingsForm = reactive({
  announcement: '欢迎使用等锅叫号系统',
  featureSwitch: true,
  enableReports: true
})

const checklist = computed(() => {
  const routeName = String(route.name || '')
  const map: Record<string, string[]> = {
    production: ['筛选待制作号码', '突出备注和菜篮', '大按钮开始制作和叫号'],
    cashier: ['查看待结账号码', '调整金额和支付方式', '确认收款并完成释放'],
    store: ['维护营业状态', '配置营业时间和地址', '设置平均制作时长和号码前缀'],
    dishes: ['新增和编辑菜品', '分类和价格维护', '上下架控制'],
    staff: ['员工账号列表', '角色权限配置', '启停用员工'],
    platform: ['商户入驻审核', '门店资料审核', '套餐功能配置'],
    screen: ['当前叫号展示', '最近叫号列表', '等待队列横屏适配'],
    reports: ['今日发号和完成数', '待结账和金额统计', '平均等待时间'],
    settings: ['系统公告', '平台配置', '功能开关']
  }
  return map[routeName] || ['模块数据加载', '表单保存', '操作反馈']
})

const actionLabel = computed(() => {
  const routeName = String(route.name || '')
  if (routeName === 'store' || routeName === 'staff' || routeName === 'settings' || routeName === 'platform') return '保存'
  if (routeName === 'dishes') return '新增菜品'
  if (routeName === 'screen') return '刷新屏幕'
  if (routeName === 'reports') return '导出报表'
  return '新增'
})

function handleSave() {
  saving.value = true
  saveNotice.value = ''
  setTimeout(() => {
    saving.value = false
    saveNotice.value = '配置已保存，后续可接入真实 API。'
  }, 250)
}
</script>

<template>
  <div class="route-page">
    <header class="topbar">
      <div>
        <p>{{ meta.crumb }}</p>
        <h1>{{ meta.title }}</h1>
        <p class="route-description">{{ meta.description }}</p>
        <p v-if="saveNotice" class="api-notice">{{ saveNotice }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Calendar">今日</el-button>
        <el-button type="primary" :icon="CirclePlus">{{ actionLabel }}</el-button>
      </div>
    </header>

    <section class="module-grid">
      <article class="panel module-hero">
        <div class="module-icon">
          <el-icon><Setting /></el-icon>
        </div>
        <div>
          <h2>{{ meta.title }}</h2>
          <p>{{ meta.description }}</p>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>功能清单</h2>
          <el-tag type="warning">待接业务视图</el-tag>
        </div>
        <ul class="module-checklist">
          <li v-for="item in checklist" :key="item">
            <el-icon><Check /></el-icon>
            <span>{{ item }}</span>
          </li>
        </ul>
      </article>

      <article class="panel module-form-panel" v-if="route.name === 'store'">
        <div class="panel-title">
          <h2>门店基础配置</h2>
          <el-icon><Document /></el-icon>
        </div>
        <div class="module-form">
          <el-select v-model="storeForm.business_status" placeholder="营业状态">
            <el-option label="营业中" value="open" />
            <el-option label="暂停营业" value="paused" />
            <el-option label="已打烊" value="closed" />
          </el-select>
          <el-input v-model="storeForm.business_hours" placeholder="营业时间" />
          <el-input v-model="storeForm.address" placeholder="门店地址" />
          <el-input-number v-model="storeForm.avg_prepare_minutes" :min="1" :max="180" />
          <el-input v-model="storeForm.number_prefix" placeholder="号码前缀" />
          <el-input v-model="storeForm.payment_qr" placeholder="收款码编号" />
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'staff'">
        <div class="panel-title">
          <h2>员工账号</h2>
          <el-icon><User /></el-icon>
        </div>
        <div class="module-form">
          <el-input v-model="staffForm.name" placeholder="员工姓名" />
          <el-select v-model="staffForm.role" placeholder="角色">
            <el-option label="店员" value="clerk" />
            <el-option label="制作员" value="cook" />
            <el-option label="收银员" value="cashier" />
            <el-option label="老板" value="owner" />
          </el-select>
          <el-select v-model="staffForm.status" placeholder="状态">
            <el-option label="启用" value="enabled" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'settings'">
        <div class="panel-title">
          <h2>系统规则</h2>
          <el-icon><Connection /></el-icon>
        </div>
        <div class="module-form">
          <el-input-number v-model="ruleForm.max_people_per_number" :min="1" :max="20" />
          <el-input-number v-model="ruleForm.queue_timeout_minutes" :min="10" :max="999" />
          <el-switch v-model="ruleForm.auto_complete_paid" active-text="自动完成" inactive-text="手动完成" />
          <el-switch v-model="ruleForm.allow_checkout_without_dining" active-text="允许提前结账" inactive-text="仅取餐后结账" />
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'platform'">
        <div class="panel-title">
          <h2>商户审核</h2>
          <el-icon><Tickets /></el-icon>
        </div>
        <div class="module-form">
          <el-select v-model="platformForm.audit_status" placeholder="审核状态">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
          <el-input v-model="platformForm.package" placeholder="套餐权限" />
          <el-input v-model="platformForm.notice" placeholder="平台公告" />
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'screen'">
        <div class="panel-title">
          <h2>大屏预览</h2>
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="screen-preview">
          <div class="screen-current">A018</div>
          <div class="screen-list">
            <div v-for="row in screenRows" :key="row.number" class="screen-row">
              <strong>{{ row.number }}</strong>
              <span>{{ row.status }}</span>
              <small>{{ row.remark }}</small>
            </div>
          </div>
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'reports'">
        <div class="panel-title">
          <h2>经营统计</h2>
          <el-icon><DataLine /></el-icon>
        </div>
        <div class="report-grid">
          <div v-for="item in reportStats" :key="item.label" class="report-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }} <small>{{ item.unit }}</small></strong>
          </div>
        </div>
      </article>

      <article class="panel module-form-panel" v-else-if="route.name === 'dishes'">
        <div class="panel-title">
          <h2>菜品管理</h2>
          <el-icon><Operation /></el-icon>
        </div>
        <p class="module-note">菜品管理已在总览入口可见，后续可直接替换为完整 CRUD 表单。</p>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>接入状态</h2>
          <el-icon><Tickets /></el-icon>
        </div>
        <p class="module-note">
          已具备独立路由入口，后续任务可以直接替换本页内容，不需要再调整全局导航。
        </p>
        <el-button :loading="saving" type="primary" @click="handleSave">{{ actionLabel }}</el-button>
      </article>

      <article class="panel" v-if="route.name === 'platform'">
        <div class="panel-title">
          <h2>平台审核列表</h2>
          <el-tag type="warning">待办</el-tag>
        </div>
        <el-table :data="platformRows" height="260">
          <el-table-column prop="merchant" label="商户" />
          <el-table-column prop="store" label="门店" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column prop="package" label="套餐" width="90" />
        </el-table>
      </article>
    </section>
  </div>
</template>
