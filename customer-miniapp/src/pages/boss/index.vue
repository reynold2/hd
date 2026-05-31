<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  createDish,
  fetchCashierPending,
  fetchOperationLogs,
  fetchPendingServiceCalls,
  fetchStoreCatalog,
  fetchStoreQueue,
  issueQueueNumber,
  updateBusinessStatus,
  updateDish,
  updateStaffStatus,
  updateStoreSettings,
  updateWechatPaymentQr
} from '../../api.mjs'
import { getStoredRoleProfile } from '../../role-auth.mjs'

const storeId = ref(1)
const loading = ref(false)
const notice = ref('')
const activePage = ref('home')
const activeDishCategory = ref('全部')
const store = ref(null)
const dishes = ref([])
const staff = ref([])
const queue = ref([])
const cashierPending = ref([])
const serviceCalls = ref([])
const logs = ref([])
const showEmployeeQr = ref(false)
const showStoreQr = ref(false)
const employeeInvite = ref('员工入口码')
const storeQr = ref('门店桌码')
const settings = ref({ business_hours: '', address: '', queue_prefix: 'A', avg_prepare_minutes: 20 })
const paymentQrForm = ref({ wechat_payment_qr_url: '', wechat_payment_qr_name: '' })
const newNumberForm = ref({ people_count: 2, remark: '' })
const customPeopleCount = ref('')
const newDish = ref({ name: '', category: '推荐', price: '12.00', available: true })

const storeName = computed(() => store.value?.name || '川香麻辣烫（中山店）')
const todayOrders = computed(() => queue.value.length + cashierPending.value.length)
const activeOrders = computed(() => queue.value.filter((item) => !['completed', 'paid'].includes(item.status)).length)
const checkoutCount = computed(() => cashierPending.value.length)
const serviceCount = computed(() => serviceCalls.value.length)
const totalAmount = computed(() => cashierPending.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0).toFixed(2))
const avgPrepareMinutes = computed(() => store.value?.avg_prepare_minutes || settings.value.avg_prepare_minutes || 20)
const categoryTabs = computed(() => ['全部', ...new Set(dishes.value.map((item) => item.category).filter(Boolean))])
const filteredDishes = computed(() => activeDishCategory.value === '全部' ? dishes.value : dishes.value.filter((item) => item.category === activeDishCategory.value))
const enabledStaff = computed(() => staff.value.filter((item) => item.status !== 'inactive').length)
const disabledStaff = computed(() => staff.value.length - enabledStaff.value)
const todayIncome = computed(() => (Number(totalAmount.value) + queue.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)).toFixed(2))
const hourlyBars = computed(() => [34, 58, 72, 66, 88, 74, 54])
const pieData = computed(() => [
  { label: '上午', value: '28%', color: '#f97316' },
  { label: '中午', value: '42%', color: '#2563eb' },
  { label: '下午', value: '20%', color: '#22c55e' },
  { label: '晚上', value: '10%', color: '#a855f7' }
])

const pages = [
  { key: 'home', title: '工作台首页', icon: '台', desc: '经营总览' },
  { key: 'queue', title: '队列管理', icon: '队', desc: '叫号开制' },
  { key: 'call', title: '叫号管理', icon: '叫', desc: '当前号码' },
  { key: 'new', title: '新增号码', icon: '号', desc: '手动取号' },
  { key: 'staff', title: '员工管理', icon: '员', desc: '账号角色' },
  { key: 'dish', title: '菜品管理', icon: '菜', desc: '上下架' },
  { key: 'stats', title: '数据统计', icon: '数', desc: '核心指标' },
  { key: 'reports', title: '统计详情', icon: '报', desc: '图表分析' },
  { key: 'cashier', title: '收银队列', icon: '收', desc: '待结账' },
  { key: 'store', title: '门店设置', icon: '店', desc: '基础信息' },
  { key: 'rules', title: '叫号规则设置', icon: '规', desc: '排序提醒' },
  { key: 'qrcode', title: '二维码管理', icon: '码', desc: '桌码入口' },
  { key: 'notice', title: '公告管理', icon: '告', desc: '上新通知' },
  { key: 'notify', title: '通知设置', icon: '通', desc: '开关提醒' },
  { key: 'logs', title: '操作日志', icon: '志', desc: '记录追踪' },
  { key: 'backup', title: '备份与导出', icon: '备', desc: 'Excel/PDF' },
  { key: 'profile', title: '我的', icon: '我', desc: '个人中心' },
  { key: 'account', title: '个人信息', icon: '人', desc: '资料维护' },
  { key: 'password', title: '修改密码', icon: '密', desc: '安全设置' },
  { key: 'about', title: '关于我们', icon: '关', desc: '版本联系' },
  { key: 'feedback', title: '意见反馈', icon: '馈', desc: '提交建议' }
]

function statusText(status) {
  return {
    occupied: '待制作',
    preparing: '制作中',
    called: '已叫号',
    dining: '用餐中',
    checkout_requested: '待结账',
    paid: '已支付',
    completed: '已完成',
    cancelled: '已取消'
  }[status] || status || '待处理'
}

function roleText(role) {
  return {
    boss: '老板',
    manager: '店长',
    cashier: '店员',
    cook: '制作',
    kitchen: '制作',
    staff: '店员'
  }[role] || role
}

function openPage(key) {
  activePage.value = key
}

function backHome() {
  activePage.value = 'home'
}

function syncSettings() {
  settings.value = {
    business_hours: store.value?.business_hours || '10:00-22:30',
    address: store.value?.address || '中山市东区中山三路88号',
    queue_prefix: store.value?.queue_prefix || 'A',
    avg_prepare_minutes: Number(store.value?.avg_prepare_minutes || 20)
  }
  paymentQrForm.value = {
    wechat_payment_qr_url: store.value?.wechat_payment_qr_url || '',
    wechat_payment_qr_name: store.value?.wechat_payment_qr_name || store.value?.payment_qr || '微信收款码'
  }
}

async function loadBossData() {
  loading.value = true
  notice.value = ''
  try {
    const [catalog, currentQueue, pendingCashier, calls, operationLogs] = await Promise.allSettled([
      fetchStoreCatalog(storeId.value),
      fetchStoreQueue(storeId.value),
      fetchCashierPending(storeId.value),
      fetchPendingServiceCalls(storeId.value),
      fetchOperationLogs(storeId.value)
    ])
    if (catalog.status === 'fulfilled') {
      store.value = catalog.value.store
      dishes.value = catalog.value.dishes || []
      staff.value = catalog.value.staff || []
      syncSettings()
    }
    queue.value = currentQueue.status === 'fulfilled' ? currentQueue.value : []
    cashierPending.value = pendingCashier.status === 'fulfilled' ? pendingCashier.value : []
    serviceCalls.value = calls.status === 'fulfilled' ? calls.value : []
    logs.value = operationLogs.status === 'fulfilled' ? operationLogs.value : []
    const rejected = [catalog, currentQueue, pendingCashier, calls, operationLogs].find((item) => item.status === 'rejected')
    if (rejected) notice.value = rejected.reason instanceof Error ? rejected.reason.message : '部分数据加载失败'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '老板端加载失败'
  } finally {
    loading.value = false
  }
}

async function createNumber() {
  loading.value = true
  notice.value = ''
  try {
    const peopleCount = Number(customPeopleCount.value || newNumberForm.value.people_count || 1)
    const payload = await issueQueueNumber(storeId.value, {
      people_count: peopleCount,
      remark: newNumberForm.value.remark
    })
    notice.value = `已生成号码 ${payload.number}`
    newNumberForm.value.remark = ''
    customPeopleCount.value = ''
    await loadBossData()
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '生成号码失败'
  } finally {
    loading.value = false
  }
}

async function toggleBusinessStatus() {
  const next = store.value?.business_status === 'open' ? 'paused' : 'open'
  try {
    store.value = await updateBusinessStatus(storeId.value, next)
    syncSettings()
    notice.value = next === 'open' ? '门店已恢复营业' : '门店已暂停取号'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '营业状态更新失败'
  }
}

async function saveSettings() {
  loading.value = true
  try {
    store.value = await updateStoreSettings(storeId.value, settings.value)
    syncSettings()
    notice.value = '门店设置已保存'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '保存失败'
  } finally {
    loading.value = false
  }
}

async function toggleStaff(member) {
  const next = member.status === 'inactive' ? 'active' : 'inactive'
  try {
    const updated = await updateStaffStatus(member.id, next)
    staff.value = staff.value.map((item) => (item.id === member.id ? updated : item))
    notice.value = `${member.name} 状态已更新`
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '员工状态更新失败'
  }
}

async function toggleDish(dish) {
  try {
    const updated = await updateDish(dish.id, { available: !dish.available })
    dishes.value = dishes.value.map((item) => (item.id === dish.id ? updated : item))
    notice.value = `${dish.name} 已${updated.available ? '上架' : '下架'}`
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '菜品更新失败'
  }
}

async function submitDish() {
  if (!newDish.value.name.trim()) {
    notice.value = '请输入菜品名称'
    return
  }
  try {
    const created = await createDish(storeId.value, {
      name: newDish.value.name,
      category: newDish.value.category,
      price: Number(newDish.value.price || 0),
      available: newDish.value.available
    })
    dishes.value.unshift(created)
    newDish.value.name = ''
    notice.value = '菜品已新增'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '菜品创建失败'
  }
}

async function makeEmployeeQr() {
  try {
    const payload = await issueQueueNumber(storeId.value, { people_count: 1, remark: '员工邀请码' })
    employeeInvite.value = `员工入口码：invite_store_${storeId.value}_${payload.number}`
    showEmployeeQr.value = true
    uni.setStorageSync('active_employee_invite', employeeInvite.value)
    notice.value = '员工入口码已生成'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '生成入口码失败'
  }
}

function makeStoreQr() {
  storeQr.value = `门店桌码：store_${storeId.value}_${Date.now()}`
  showStoreQr.value = true
  notice.value = '桌码已生成'
}

async function savePaymentQr() {
  loading.value = true
  try {
    store.value = await updateWechatPaymentQr(storeId.value, paymentQrForm.value)
    syncSettings()
    notice.value = '微信收款二维码已更新'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '收款码保存失败'
  } finally {
    loading.value = false
  }
}

function exportData(type) {
  notice.value = type === 'excel' ? '已生成 Excel 导出任务' : '已生成 PDF 报表任务'
}

onMounted(async () => {
  const profile = getStoredRoleProfile()
  storeId.value = Number(profile?.store_id || 1)
  await loadBossData()
})
</script>

<template>
  <view class="page boss-prototype-page">
    <view v-if="activePage !== 'home'" class="boss-sub-header">
      <button @click="backHome">‹</button>
      <text>{{ pages.find((item) => item.key === activePage)?.title }}</text>
      <button :disabled="loading" @click="loadBossData">刷新</button>
    </view>

    <view v-if="notice" class="api-notice boss-notice">{{ notice }}</view>

    <view v-if="activePage === 'home'" class="boss-screen">
      <view class="boss-hero-orange">
        <view>
          <text class="boss-role">老板端</text>
          <text class="boss-store">{{ storeName }}</text>
          <text class="boss-meta">今日 {{ todayOrders }} 单 · 待结账 {{ checkoutCount }} 单 · 服务 {{ serviceCount }} 条</text>
        </view>
        <button @click="toggleBusinessStatus">{{ store?.business_status === 'open' ? '营业中' : '暂停中' }}</button>
      </view>

      <view class="boss-current-card">
        <view>
          <text>当前叫号</text>
          <text>{{ queue[0]?.number || 'A023' }}</text>
        </view>
        <button @click="openPage('call')">叫号</button>
      </view>

      <view class="boss-stat-panel">
        <view><text>{{ todayOrders }}</text><text>今日订单</text></view>
        <view><text>{{ activeOrders }}</text><text>制作中</text></view>
        <view><text>{{ checkoutCount }}</text><text>待结账</text></view>
        <view><text>{{ serviceCount }}</text><text>服务呼叫</text></view>
        <view><text>{{ enabledStaff }}</text><text>在线员工</text></view>
        <view><text>{{ avgPrepareMinutes }}分</text><text>平均等待</text></view>
      </view>

      <view class="boss-menu-card">
        <view class="section-title">
          <text>功能菜单</text>
          <text>按原型入口</text>
        </view>
        <view class="boss-function-grid">
          <button v-for="item in pages.slice(1)" :key="item.key" @click="openPage(item.key)">
            <text>{{ item.icon }}</text>
            <text>{{ item.title }}</text>
            <text>{{ item.desc }}</text>
          </button>
        </view>
      </view>
    </view>

    <view v-else-if="activePage === 'queue'" class="boss-panel">
      <view class="boss-tabs"><text class="active">排队中</text><text>制作中</text><text>已叫号</text><text>已完成</text></view>
      <view class="boss-list">
        <view v-for="item in queue" :key="item.number" class="queue-row">
          <text>{{ item.number }}</text><text>{{ item.people_count }}人</text><text>{{ statusText(item.status) }}</text>
        </view>
      </view>
      <view class="boss-bottom-actions"><button @click="openPage('new')">批量操作</button><button @click="openPage('call')">叫号</button></view>
    </view>

    <view v-else-if="activePage === 'call'" class="boss-panel call-panel">
      <text class="current-label">当前叫号</text>
      <text class="call-number">{{ queue[0]?.number || 'A023' }}</text>
      <text class="call-sub">等待中 {{ queue[1]?.number || 'A024' }} · {{ queue[1]?.people_count || 3 }}人</text>
      <view class="call-actions"><button @click="openPage('queue')">叫下一号</button><button @click="openPage('queue')">跳过此号</button><button @click="openPage('service')">呼叫店员</button></view>
      <view class="call-history"><view v-for="item in queue.slice(0, 5)" :key="item.number"><text>{{ item.number }}</text><text>{{ statusText(item.status) }}</text></view></view>
    </view>

    <view v-else-if="activePage === 'new'" class="boss-panel">
      <view class="form-card boss-form-card">
        <view class="section-title"><text>手动新增号码</text><text>选择人数</text></view>
        <view class="people-options">
          <button v-for="count in [1, 2, 3, 4, 5]" :key="count" :class="{ active: newNumberForm.people_count === count && !customPeopleCount }" @click="newNumberForm.people_count = count; customPeopleCount = ''">{{ count }}人</button>
        </view>
        <input v-model="customPeopleCount" placeholder="自定义人数" />
        <textarea v-model="newNumberForm.remark" placeholder="备注（选填）" />
        <button class="orange-button" :disabled="loading" @click="createNumber">生成号码</button>
      </view>
    </view>

    <view v-else-if="activePage === 'staff'" class="boss-panel">
      <view class="boss-stat-panel three"><view><text>{{ staff.length }}</text><text>员工总数</text></view><view><text>{{ enabledStaff }}</text><text>启用</text></view><view><text>{{ disabledStaff }}</text><text>停用</text></view></view>
      <view class="staff-list"><view v-for="member in staff" :key="member.id" class="staff-row"><view class="avatar">{{ member.name.slice(0, 1) }}</view><view><text>{{ member.name }}</text><text>{{ roleText(member.role) }} · {{ member.status === 'inactive' ? '已停用' : '启用中' }}</text></view><button @click="toggleStaff(member)">{{ member.status === 'inactive' ? '启用' : '停用' }}</button></view></view>
      <button class="orange-button" @click="makeEmployeeQr">+ 添加员工</button>
    </view>

    <view v-else-if="activePage === 'dish'" class="boss-panel">
      <view class="boss-tabs"><text v-for="tab in categoryTabs" :key="tab" :class="{ active: activeDishCategory === tab }" @click="activeDishCategory = tab">{{ tab }}</text></view>
      <view class="dish-manage-list"><view v-for="dish in filteredDishes" :key="dish.id" class="dish-manage-row"><view class="dish-photo">菜</view><view><text>{{ dish.name }}</text><text>¥{{ dish.price }}</text></view><button @click="toggleDish(dish)">{{ dish.available ? '下架' : '上架' }}</button></view></view>
      <view class="boss-form-card"><input v-model="newDish.name" placeholder="菜品名称" /><input v-model="newDish.price" placeholder="价格" /><button class="orange-button" @click="submitDish">新增菜品</button></view>
    </view>

    <view v-else-if="activePage === 'stats'" class="boss-panel">
      <view class="boss-stat-panel"><view><text>{{ todayOrders }}</text><text>订单量</text></view><view><text>{{ checkoutCount }}</text><text>收款数</text></view><view><text>¥{{ todayIncome }}</text><text>营业额</text></view><view><text>{{ avgPrepareMinutes }}分</text><text>平均等待</text></view></view>
      <view class="line-chart"><i v-for="(height, index) in [34, 50, 58, 76, 92, 70, 48]" :key="index" :style="{ height: `${height}px` }"></i></view>
    </view>

    <view v-else-if="activePage === 'reports'" class="boss-panel">
      <view class="bar-chart"><i v-for="height in hourlyBars" :key="height" :style="{ height: `${height}px` }"></i></view>
      <view class="pie-wrap"><view class="pie-chart"></view><view><text v-for="item in pieData" :key="item.label"><b :style="{ background: item.color }"></b>{{ item.label }} {{ item.value }}</text></view></view>
    </view>

    <view v-else-if="activePage === 'cashier'" class="boss-panel">
      <view class="cashier-list"><view v-for="item in cashierPending" :key="item.number" class="cashier-row"><view><text>{{ item.number }}</text><text>{{ statusText(item.status) }}</text></view><text>¥{{ item.total_amount }}</text><button>去收款</button></view></view>
    </view>

    <view v-else-if="activePage === 'store'" class="boss-panel">
      <view class="store-card"><view class="store-logo">店</view><view><text>{{ storeName }}</text><text>{{ settings.address }}</text></view></view>
      <view class="boss-form-card"><input v-model="settings.business_hours" placeholder="营业时间" /><input v-model="settings.address" placeholder="门店地址" /><input v-model="settings.queue_prefix" placeholder="号码前缀" /><input v-model="settings.avg_prepare_minutes" placeholder="平均等待分钟" /><button class="orange-button" @click="saveSettings">保存</button></view>
    </view>

    <view v-else-if="activePage === 'rules'" class="boss-panel">
      <view class="switch-list"><view><text>自动叫号</text><switch checked /></view><view><text>提醒客户</text><switch checked /></view><view><text>超时跳号</text><switch /></view></view>
      <view class="boss-form-card"><input v-model="settings.avg_prepare_minutes" placeholder="等待分钟" /><button class="orange-button" @click="saveSettings">保存</button></view>
    </view>

    <view v-else-if="activePage === 'qrcode'" class="boss-panel">
      <view class="qr-list"><view><view class="fake-qr">码</view><text>顾客扫码点餐</text><button @click="makeStoreQr">查看二维码</button></view><view><view class="fake-qr">员</view><text>员工入口码</text><button @click="makeEmployeeQr">查看二维码</button></view></view>
      <view v-if="showStoreQr || showEmployeeQr" class="qr-result">{{ showEmployeeQr ? employeeInvite : storeQr }}</view>
      <view class="boss-form-card">
        <text>微信收款二维码</text>
        <image v-if="paymentQrForm.wechat_payment_qr_url" class="payment-qr-image" :src="paymentQrForm.wechat_payment_qr_url" mode="aspectFit" />
        <input v-model="paymentQrForm.wechat_payment_qr_name" placeholder="收款码名称" />
        <input v-model="paymentQrForm.wechat_payment_qr_url" placeholder="https://.../wechat-pay.jpg 或 /static/..." />
        <button class="orange-button" :disabled="loading" @click="savePaymentQr">保存微信收款码</button>
      </view>
    </view>

    <view v-else-if="activePage === 'notice'" class="boss-panel">
      <view class="notice-list"><view><text>今日营业时间调整通知</text><text>显示中</text></view><view><text>新品上架：牛肉丸</text><text>显示中</text></view><view><text>缺货提醒：请及时补货</text><text>待处理</text></view></view><button class="orange-button">+ 发布公告</button>
    </view>

    <view v-else-if="activePage === 'notify'" class="boss-panel">
      <view class="switch-list"><view><text>呼叫服务通知</text><switch checked /></view><view><text>出餐提醒</text><switch checked /></view><view><text>未结账提醒</text><switch checked /></view><view><text>营业数据通知</text><switch /></view></view><button class="orange-button">保存</button>
    </view>

    <view v-else-if="activePage === 'logs'" class="boss-panel">
      <view class="log-list"><view v-for="item in logs.slice(0, 10)" :key="item.id"><text>{{ item.staff_name }}</text><text>{{ item.action }} {{ item.target_id }}</text><text>{{ item.created_at }}</text></view></view>
    </view>

    <view v-else-if="activePage === 'backup'" class="boss-panel">
      <view class="backup-card"><text>数据备份</text><button @click="exportData('backup')">立即备份</button></view><view class="backup-card"><text>导出报表</text><button @click="exportData('excel')">导出 Excel 表格</button><button @click="exportData('pdf')">导出 PDF 报表</button></view>
    </view>

    <view v-else-if="activePage === 'profile'" class="boss-panel mine-panel">
      <view class="mine-hero"><view class="avatar large">老</view><view><text>张老板</text><text>{{ storeName }}</text></view></view>
      <view class="mine-menu"><view @click="openPage('account')">个人信息</view><view @click="openPage('password')">修改密码</view><view @click="openPage('about')">关于我们</view><view @click="openPage('feedback')">意见反馈</view></view>
    </view>

    <view v-else-if="activePage === 'account'" class="boss-panel"><view class="boss-form-card"><input value="张老板" /><input value="138****5678" /><input :value="storeName" /><button class="orange-button">保存</button></view></view>
    <view v-else-if="activePage === 'password'" class="boss-panel"><view class="boss-form-card"><input placeholder="原密码" password /><input placeholder="新密码" password /><input placeholder="确认新密码" password /><button class="orange-button">确认修改</button></view></view>
    <view v-else-if="activePage === 'about'" class="boss-panel"><view class="about-card"><text>等锅叫号</text><text>V1.0.0</text><text>门店排队、叫号、点餐、收银和统计一体化工具。</text><button>联系我们</button></view></view>
    <view v-else-if="activePage === 'feedback'" class="boss-panel"><view class="boss-form-card"><textarea placeholder="请输入反馈内容" /><input placeholder="联系方式（选填）" /><button class="orange-button">提交反馈</button></view></view>
  </view>
</template>
