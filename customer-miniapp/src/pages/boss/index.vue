<script setup>
import { computed, ref } from 'vue'
import { issueQueueNumber } from '../../api.mjs'

const showQr = ref(false)
const qrCodeText = ref('员工绑定二维码')
const employeeCount = ref(6)
const pendingAccounts = ref(2)
const inviteToken = ref('')
const loading = ref(false)
const inviteNotice = ref('')

const employeeRoles = [
  { label: '服务员', count: 2 },
  { label: '制作', count: 1 },
  { label: '收银', count: 1 },
  { label: '顾客联调', count: 2 }
]

const qrHint = computed(() => (showQr.value ? '二维码已生成，可供员工扫码注册' : '点击按钮生成员工二维码'))

async function openQr() {
  loading.value = true
  try {
    const payload = await issueQueueNumber(1, { people_count: 1, remark: '员工邀请码' })
    inviteToken.value = `invite_store_1_${payload.number || Date.now()}`
    qrCodeText.value = `门店邀请码：${inviteToken.value}`
    showQr.value = true
    inviteNotice.value = '已生成员工邀请二维码'
    uni.setStorageSync('active_employee_invite', inviteToken.value)
  } catch (error) {
    inviteNotice.value = error instanceof Error ? error.message : '生成二维码失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="page role-page">
    <view class="hero">
      <view>
        <text class="store-name">老板个人中心</text>
        <view class="store-meta">
          <text>员工管理</text>
          <text>门店绑定</text>
          <text>账号维护</text>
        </view>
      </view>
      <button class="ghost-button" @click="openQr">{{ loading ? '生成中...' : '添加员工二维码' }}</button>
    </view>

    <view v-if="inviteNotice" class="api-notice">{{ inviteNotice }}</view>

    <view class="card">
      <view class="section-title">
        <text>员工管理说明</text>
        <text>老板仅能管理自己门店员工</text>
      </view>
      <view class="notice-box">
        <text>员工扫码后可选择所属门店内角色，设置账号、密码和头像；若账号已存在则提示已注册。</text>
      </view>
    </view>

    <view class="card stats-strip">
      <view>
        <text>当前员工</text>
        <text>{{ employeeCount }}</text>
      </view>
      <view>
        <text>待完善账号</text>
        <text>{{ pendingAccounts }}</text>
      </view>
      <view>
        <text>扫码状态</text>
        <text>{{ showQr ? '已生成' : '未生成' }}</text>
      </view>
    </view>

    <view class="card" v-if="showQr">
      <view class="section-title">
        <text>员工二维码</text>
        <text>扫码后进入注册流程</text>
      </view>
      <view class="store-qr-box">
        <text>{{ qrCodeText }}</text>
        <small>{{ qrHint }}</small>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>所属门店角色</text>
        <text>扫码后可选择</text>
      </view>
      <view class="role-grid">
        <view v-for="role in employeeRoles" :key="role.label" class="role-card">
          <text class="role-label">{{ role.label }}</text>
          <text class="role-desc">可分配 {{ role.count }} 人</text>
        </view>
      </view>
    </view>
  </view>
</template>
