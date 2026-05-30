<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRoleMeta, loginAdmin, resolveHomePath } from '../auth'

const router = useRouter()
const username = ref('admin_platform')
const password = ref('123456')
const errorMessage = ref('')
const successMessage = ref('')
const selectedRole = ref<'platform_admin' | 'store_owner' | 'cashier' | 'screen'>('platform_admin')

const roleOptions = [
  { username: 'admin_platform', displayName: '平台管理员', role: 'platform_admin' as const },
  { username: 'boss_store_001', displayName: '中山店老板', role: 'store_owner' as const },
  { username: 'cashier_store_001', displayName: '中山店收银', role: 'cashier' as const },
  { username: 'screen_store_001', displayName: '中山店大屏', role: 'screen' as const }
]
const selectedRoleMeta = computed(() => getRoleMeta(selectedRole.value))

function validatePassword(value: string) {
  return value.length >= 6 && /[A-Za-z0-9]/.test(value)
}

function validateUsername(value: string) {
  return value.length >= 3 && /^[A-Za-z0-9_]+$/.test(value)
}

function fillProfile(usernameValue: string, role: typeof selectedRole.value) {
  username.value = usernameValue
  password.value = '123456'
  selectedRole.value = role
  errorMessage.value = ''
  successMessage.value = `已填充 ${getRoleMeta(role).title} 登录信息`
}

async function submitLogin() {
  const trimmedUsername = username.value.trim()
  if (!validateUsername(trimmedUsername)) {
    errorMessage.value = '账号格式不正确，至少 3 位，仅允许字母、数字和下划线'
    successMessage.value = ''
    return
  }
  if (!validatePassword(password.value)) {
    errorMessage.value = '密码至少 6 位，建议包含字母和数字'
    successMessage.value = ''
    return
  }
  try {
    const payload = await loginAdmin(trimmedUsername, password.value)
    successMessage.value = `${payload.profile.displayName} 登录成功`
    errorMessage.value = ''
    router.replace(payload.redirect || resolveHomePath(payload.profile.role))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败'
    successMessage.value = ''
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-glow login-glow-left"></div>
    <div class="login-glow login-glow-right"></div>

    <section class="login-shell-layout">
      <div class="login-brand-panel">
        <div class="login-brand-badge">等锅叫号</div>
        <h1>统一身份中心</h1>
        <p>为平台管理员、门店老板、收银和大屏提供统一登录入口，登录后自动进入对应角色首页。</p>

        <div class="login-brand-stats">
          <article>
            <strong>4</strong>
            <span>后台角色</span>
          </article>
          <article>
            <strong>1</strong>
            <span>统一入口</span>
          </article>
          <article>
            <strong>真实</strong>
            <span>后端接口</span>
          </article>
        </div>
      </div>

      <div class="login-card panel">
        <div class="login-card-header">
          <div>
            <span class="login-eyebrow">后台登录</span>
            <h2>欢迎回来</h2>
            <p>请输入账号和密码进入系统，暂不提供注册入口。</p>
          </div>
          <div class="login-role-card compact">
            <strong>{{ selectedRoleMeta.title }}</strong>
            <span>{{ selectedRoleMeta.description }}</span>
          </div>
        </div>

        <div class="login-form">
          <label>
            <span>账号</span>
            <input v-model="username" placeholder="请输入账号" autocomplete="username" />
          </label>
          <label>
            <span>密码</span>
            <input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" />
          </label>

          <div class="login-actions">
            <button class="primary-button" @click="submitLogin">登录系统</button>
            <button class="ghost-button" @click="router.push('/')">返回首页</button>
          </div>

          <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
          <p v-if="successMessage" class="success-text">{{ successMessage }}</p>
        </div>

        <div class="seed-area">
          <div class="seed-area-title">
            <strong>测试账号</strong>
            <span>点击即可快速填充</span>
          </div>
          <div class="seed-list grid">
            <button
              v-for="profile in roleOptions"
              :key="profile.username"
              class="seed-card"
              @click="fillProfile(profile.username, profile.role)"
            >
              <strong>{{ getRoleMeta(profile.role).title }}</strong>
              <span>{{ profile.displayName }}</span>
              <small>{{ profile.username }}</small>
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
