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

function fillProfile(usernameValue: string, role: typeof selectedRole.value) {
  username.value = usernameValue
  password.value = '123456'
  selectedRole.value = role
  errorMessage.value = ''
  successMessage.value = `已填充 ${getRoleMeta(role).title} 登录信息`
}

async function submitLogin() {
  try {
    const payload = await loginAdmin(username.value.trim(), password.value)
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
    <section class="login-hero panel">
      <div>
        <div class="store-hero-kicker">后台管理登录</div>
        <h2>统一身份中心</h2>
        <p>登录后按角色进入平台管理员、门店老板、收银或大屏页面。</p>
      </div>
      <div class="login-role-card">
        <strong>{{ selectedRoleMeta.title }}</strong>
        <span>{{ selectedRoleMeta.description }}</span>
      </div>
    </section>

    <section class="login-layout">
      <div class="panel">
        <div class="panel-title">
          <h2>登录表单</h2>
        </div>
        <div class="login-form">
          <label>
            <span>账号</span>
            <input v-model="username" placeholder="请输入账号" />
          </label>
          <label>
            <span>密码</span>
            <input v-model="password" type="password" placeholder="请输入密码" />
          </label>
          <div class="login-actions">
            <button class="primary-button" @click="submitLogin">登录</button>
            <button class="ghost-button" @click="router.push('/')">查看后台首页</button>
          </div>
          <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
          <p v-if="successMessage" class="success-text">{{ successMessage }}</p>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">
          <h2>测试账号</h2>
        </div>
        <div class="seed-list">
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
    </section>
  </div>
</template>
