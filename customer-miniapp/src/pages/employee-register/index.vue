<script setup>
import { computed, onMounted, ref } from 'vue'
import { wechatLogin } from '../../api.mjs'

const storeName = ref('川香麻辣烫（中山店）')
const selectedRole = ref('服务员')
const account = ref('')
const password = ref('123456')
const avatar = ref('默认头像')
const notice = ref('')
const registered = ref(false)
const submitting = ref(false)
const inviteToken = ref('')
const isDuplicateAccount = ref(false)

const roleOptions = ['服务员', '制作', '收银']

const canSubmit = computed(() => account.value.trim().length > 0 && password.value.trim().length >= 6)

onMounted(() => {
  inviteToken.value = (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('token')) || uni.getStorageSync('active_employee_invite') || `invite_${Date.now()}`
})

async function submitRegister() {
  if (!canSubmit.value) {
    notice.value = '请输入账号并保证密码不少于 6 位'
    return
  }
  submitting.value = true
  try {
    const payload = await wechatLogin({
      openid: `invite_${Date.now()}`,
      username: account.value.trim(),
      password: password.value,
      display_name: account.value.trim(),
      avatar_url: avatar.value,
      role: selectedRole.value,
      store_name: storeName.value,
      invite_token: inviteToken.value
    })
    registered.value = true
    isDuplicateAccount.value = Boolean(payload?.redirect === '/home' && payload?.token)
    notice.value = isDuplicateAccount.value ? `账号已存在，已进入 ${selectedRole.value} 首页` : `注册成功，已进入 ${selectedRole.value} 首页`
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/index/index' })
    }, 800)
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '注册失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <view class="page role-page">
    <view class="hero">
      <view>
        <text class="store-name">员工扫码注册</text>
        <view class="store-meta">
          <text>{{ storeName }}</text>
          <text>选择角色</text>
          <text>绑定门店</text>
        </view>
      </view>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="card">
      <view class="section-title">
        <text>门店内角色</text>
        <text>扫码后选择</text>
      </view>
      <view class="role-grid compact-role-grid">
        <view
          v-for="role in roleOptions"
          :key="role"
          class="role-card"
          :class="{ active: selectedRole === role }"
          @click="selectedRole = role"
        >
          <text class="role-label">{{ role }}</text>
          <text class="role-desc">点击切换</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>账号信息</text>
        <text>默认值可直接使用</text>
      </view>
      <view class="bind-card register-card">
        <input v-model="account" placeholder="账号，未注册可创建" />
        <input v-model="password" placeholder="密码，默认 123456" password />
        <input v-model="avatar" placeholder="头像说明 / 地址" />
      </view>
      <button class="primary-button register-button" :disabled="!canSubmit || submitting" @click="submitRegister">
        {{ submitting ? '提交中' : '确认注册' }}
      </button>
    </view>

    <view class="card">
      <view class="section-title">
        <text>注册状态</text>
        <text>{{ registered ? '已完成' : '待提交' }}</text>
      </view>
      <view class="notice-box">
        <text>账号存在时将提示已注册；账号不存在时创建账号并关联当前门店与角色。</text>
      </view>
    </view>
  </view>
</template>
