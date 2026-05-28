<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Money, Refresh, Shop } from '@element-plus/icons-vue'
import {
  addCashierLineItem,
  adjustSessionRemark,
  confirmPayment,
  fetchCashierPending,
  fetchMealSession,
  type MealSession
} from '../api'
import type { AdminRouteMeta } from '../router'

const meta: AdminRouteMeta = {
  title: '收银工作台',
  crumb: '工作台 / 收银',
  description: '待结账列表、金额调整、收款码展示和确认收款释放'
}

const sessions = ref<MealSession[]>([])
const selectedNumber = ref('')
const detail = ref<(MealSession & { store_id: number }) | null>(null)
const apiNotice = ref('')
const loadingList = ref(false)
const loadingDetail = ref(false)
const busyAction = ref('')
const successNotice = ref('')

const remarkDraft = ref('')
const adjustmentName = ref('收银调整')
const adjustmentAmount = ref('0.00')
const adjustmentReason = ref('')
const paymentMethod = ref('store_qr')
const cashierId = ref(1)

const selectedSession = computed(() => detail.value || sessions.value.find((item) => item.number === selectedNumber.value) || null)
const pendingCount = computed(() => sessions.value.length)
const totalPendingAmount = computed(() =>
  sessions.value.reduce((sum, session) => sum + Number(session.total_amount || '0'), 0).toFixed(2)
)

onMounted(loadPending)

async function loadPending() {
  loadingList.value = true
  try {
    sessions.value = await fetchCashierPending(1)
    apiNotice.value = ''
    successNotice.value = ''
    if (!selectedNumber.value && sessions.value.length) {
      await selectSession(sessions.value[0].number)
    }
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '待结账列表加载失败'
  } finally {
    loadingList.value = false
  }
}

async function selectSession(number: string) {
  selectedNumber.value = number
  loadingDetail.value = true
  try {
    detail.value = await fetchMealSession(number)
    remarkDraft.value = ''
    adjustmentReason.value = ''
    apiNotice.value = ''
    successNotice.value = ''
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '号码详情加载失败'
  } finally {
    loadingDetail.value = false
  }
}

function formatMoney(amount: string | undefined) {
  return `¥${amount || '0.00'}`
}

function currentStoreQr() {
  const storePrefix = selectedSession.value?.store_id || 1
  const queuePrefix = 'A'
  return `/images/store-${storePrefix}-${queuePrefix}-qr.png`
}

async function saveRemark() {
  if (!selectedSession.value || !remarkDraft.value.trim()) return
  busyAction.value = 'remark'
  try {
    detail.value = await adjustSessionRemark(selectedSession.value.number, remarkDraft.value.trim(), 'cashier')
    adjustmentReason.value = ''
    remarkDraft.value = ''
    successNotice.value = '备注已保存'
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '备注更新失败'
  } finally {
    busyAction.value = ''
  }
}

async function addAdjustment() {
  if (!selectedSession.value) return
  busyAction.value = 'adjust'
  try {
    detail.value = await addCashierLineItem(selectedSession.value.number, {
      name: adjustmentName.value.trim() || '收银调整',
      amount: adjustmentAmount.value || '0.00',
      source: 'cashier',
      quantity: 1,
      note: adjustmentReason.value.trim()
    })
    await selectSession(selectedSession.value.number)
    await loadPending()
    successNotice.value = '金额调整已加入账单'
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '金额调整失败'
  } finally {
    busyAction.value = ''
  }
}

async function completePayment() {
  if (!selectedSession.value) return
  busyAction.value = 'pay'
  try {
    detail.value = await confirmPayment(selectedSession.value.number, cashierId.value, paymentMethod.value as 'store_qr' | 'cash' | 'other')
    await loadPending()
  } catch (error) {
    apiNotice.value = error instanceof Error ? error.message : '确认收款失败'
  } finally {
    busyAction.value = ''
  }
}
</script>

<template>
  <div class="route-page cashier-page">
    <header class="topbar">
      <div>
        <p>{{ meta.crumb }}</p>
        <h1>{{ meta.title }}</h1>
        <p class="route-description">{{ meta.description }}</p>
        <p v-if="apiNotice" class="api-notice">{{ apiNotice }}</p>
      </div>
      <div class="top-actions">
        <el-tag type="warning">{{ pendingCount }} 单待收银</el-tag>
        <el-tag type="success">合计 {{ formatMoney(totalPendingAmount) }}</el-tag>
        <el-button :icon="Refresh" :loading="loadingList" @click="loadPending">刷新列表</el-button>
      </div>
    </header>

    <section class="cashier-layout">
      <article class="panel cashier-list-panel">
        <div class="panel-title">
          <h2>待结账号码</h2>
          <el-tag type="warning">实时列表</el-tag>
        </div>

        <el-empty v-if="!sessions.length" description="暂无待收银号码" />

        <button
          v-for="session in sessions"
          :key="session.number"
          :class="['cashier-row', { active: selectedNumber === session.number }]"
          @click="selectSession(session.number)"
        >
          <div>
            <strong>{{ session.number }}</strong>
            <span>{{ session.people_count }} 人 · {{ session.status }}</span>
          </div>
          <div>
            <strong>{{ formatMoney(session.total_amount) }}</strong>
            <span>{{ session.remark || '无备注' }}</span>
          </div>
        </button>
      </article>

      <article class="panel cashier-detail-panel">
        <div class="panel-title">
          <h2>号码详情</h2>
          <el-tag v-if="selectedSession">{{ selectedSession.status }}</el-tag>
        </div>

        <el-skeleton v-if="loadingDetail" :rows="6" animated />

        <template v-else-if="selectedSession">
          <section class="cashier-summary">
            <div>
              <span>当前号码</span>
              <strong>{{ selectedSession.number }}</strong>
            </div>
            <div>
              <span>应收金额</span>
              <strong>{{ formatMoney(selectedSession.total_amount) }}</strong>
            </div>
            <div>
              <span>门店编号</span>
              <strong>#{{ selectedSession.store_id }}</strong>
            </div>
          </section>

          <section class="cashier-card">
            <div class="panel-title">
              <h3>菜品与追加项</h3>
              <el-icon><Shop /></el-icon>
            </div>
            <ul class="cashier-items">
              <li v-for="item in selectedSession.items" :key="`${item.name}-${item.note}`">
                <span>{{ item.name }} × {{ item.quantity }}</span>
                <strong>{{ formatMoney(item.subtotal) }}</strong>
              </li>
            </ul>
          </section>

          <section class="cashier-card">
            <div class="panel-title">
              <h3>收款码与支付方式</h3>
              <el-tag>店内收款码</el-tag>
            </div>
            <div class="qr-box">
              <div class="qr-placeholder">QR</div>
              <div>
                <p>请顾客扫码支付</p>
                <small>门店：{{ currentStoreQr() }}</small>
              </div>
            </div>
            <el-select v-model="paymentMethod" placeholder="支付方式">
              <el-option label="门店收款码" value="store_qr" />
              <el-option label="现金" value="cash" />
              <el-option label="其他" value="other" />
            </el-select>
            <p class="cashier-hint">最终确认会把当前支付方式写入收款记录。</p>
          </section>

          <section class="cashier-card">
            <div class="panel-title">
              <h3>金额调整</h3>
              <el-tag type="warning">记录原因</el-tag>
            </div>
            <div class="cashier-form">
              <el-input v-model="adjustmentName" placeholder="调整项目名称" />
              <el-input v-model="adjustmentAmount" placeholder="金额" />
              <el-input v-model="adjustmentReason" placeholder="调整原因" />
              <el-button :loading="busyAction === 'adjust'" type="warning" @click="addAdjustment">确认调整</el-button>
            </div>
          </section>

          <section class="cashier-card">
            <div class="panel-title">
              <h3>备注</h3>
              <el-tag type="info">可追加收银备注</el-tag>
            </div>
            <el-input v-model="remarkDraft" type="textarea" :rows="3" placeholder="输入收银备注" />
            <div class="cashier-actions-inline">
              <el-button :loading="busyAction === 'remark'" plain @click="saveRemark">保存备注</el-button>
              <el-input-number v-model="cashierId" :min="1" />
              <el-button :loading="busyAction === 'pay'" type="primary" :icon="Money" @click="completePayment">
                确认已收款
              </el-button>
            </div>
          </section>
        </template>
      </article>
    </section>
  </div>
</template>
