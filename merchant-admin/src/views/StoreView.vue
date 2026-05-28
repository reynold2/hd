<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { OfficeBuilding, Refresh, Setting, User } from '@element-plus/icons-vue'
import { fetchStoreCatalog, updateStaffStatus, updateStoreSettings, updateBusinessStatus } from '../api'

const storeId = 1
const apiNotice = ref('')
const loading = ref(false)
const saving = ref('')
const catalog = ref<any>(null)

const form = reactive({
  business_hours: '',
  address: '',
  queue_prefix: '',
  avg_prepare_minutes: 18
})

const queuePrefixPreview = computed(() => `${form.queue_prefix || 'A'}001`)
const storeQrPreview = computed(() => `/images/store-${storeId}-${form.queue_prefix || 'A'}-qr.png`)

onMounted(loadStore)

async function loadStore() {
  loading.value = true
  try {
    catalog.value = await fetchStoreCatalog(storeId)
    form.business_hours = catalog.value.store.business_hours
    form.address = catalog.value.store.address
    form.queue_prefix = catalog.value.store.queue_prefix
    form.avg_prepare_minutes = catalog.value.store.avg_prepare_minutes
    apiNotice.value = ''
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '门店信息加载失败'
  } finally {
    loading.value = false
  }
}

async function saveStoreSettings() {
  saving.value = 'store'
  try {
    catalog.value.store = await updateStoreSettings(storeId, { ...form })
    apiNotice.value = '门店设置已保存'
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '门店设置保存失败'
  } finally {
    saving.value = ''
  }
}

async function toggleStoreStatus() {
  if (!catalog.value) return
  saving.value = 'status'
  try {
    const next = catalog.value.store.business_status === 'open' ? 'paused' : 'open'
    catalog.value.store = await updateBusinessStatus(storeId, next)
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '营业状态更新失败'
  } finally {
    saving.value = ''
  }
}

async function toggleStaffStatus(staff: any) {
  saving.value = `staff-${staff.id}`
  try {
    const next = staff.status === 'active' ? 'inactive' : 'active'
    staff.status = (await updateStaffStatus(staff.id, next)).status
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '员工状态更新失败'
  } finally {
    saving.value = ''
  }
}
</script>

<template>
  <div class="route-page store-page">
    <header class="topbar">
      <div>
        <p>设置 / 门店</p>
        <h1>门店 / 员工 / 规则配置</h1>
        <p class="route-description">维护营业状态、门店参数、排号前缀和员工启停用</p>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
      </div>
      <div class="top-actions">
        <el-button :icon="Refresh" @click="loadStore">刷新</el-button>
      </div>
    </header>

    <section class="main-grid">
      <article class="panel">
        <div class="panel-title">
          <h2>门店信息</h2>
          <el-icon><OfficeBuilding /></el-icon>
        </div>
        <p>{{ catalog?.store.name }}</p>
        <el-tag>{{ catalog?.store.business_status }}</el-tag>
        <div class="form-grid">
          <el-input v-model="form.business_hours" placeholder="营业时间" />
          <el-input v-model="form.address" placeholder="门店地址" />
          <el-input v-model="form.queue_prefix" placeholder="号码前缀" />
          <el-input-number v-model="form.avg_prepare_minutes" :min="1" />
        </div>
        <div class="panel-actions">
          <el-button type="primary" :loading="saving === 'store'" @click="saveStoreSettings">保存门店设置</el-button>
          <el-button :loading="saving === 'status'" @click="toggleStoreStatus">切换营业状态</el-button>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>员工账号</h2>
          <el-icon><User /></el-icon>
        </div>
        <div class="staff-list">
          <div v-for="staff in catalog?.staff || []" :key="staff.id" class="staff-row">
            <div>
              <strong>{{ staff.name }}</strong>
              <span>{{ staff.role }}</span>
            </div>
            <el-tag :type="staff.status === 'active' ? 'success' : 'info'">{{ staff.status }}</el-tag>
            <el-button size="small" :loading="saving === `staff-${staff.id}`" @click="toggleStaffStatus(staff)">
              {{ staff.status === 'active' ? '停用' : '启用' }}
            </el-button>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title">
          <h2>规则配置</h2>
          <el-icon><Setting /></el-icon>
        </div>
        <ul class="rule-list">
          <li>门店营业状态影响顾客端首页和取号入口</li>
          <li>号码前缀用于日常发号和大屏展示，示例：{{ queuePrefixPreview }}</li>
          <li>平均制作时长用于后续等待时间估算</li>
          <li>收银工作台最终确认会使用当前支付方式记录</li>
        </ul>
        <div class="qr-box">{{ storeQrPreview }}</div>
      </article>
    </section>
  </div>
</template>
