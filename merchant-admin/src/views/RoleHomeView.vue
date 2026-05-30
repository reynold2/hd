<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRoleMeta, getStoredProfile, logoutAdminAndRedirect, type AuthProfile } from '../auth'

const router = useRouter()
const profile = ref<AuthProfile | null>(null)

onMounted(() => {
  profile.value = getStoredProfile()
  if (!profile.value) router.replace('/login')
})

const meta = computed(() => (profile.value ? getRoleMeta(profile.value.role) : null))

function handleLogout() {
  logoutAdminAndRedirect()
}
</script>

<template>
  <div class="route-page">
    <header class="topbar">
      <div>
        <p>登录后首页</p>
        <h1>{{ meta?.title || '未登录' }}</h1>
        <p>{{ meta?.description || '请先登录' }}</p>
      </div>
      <div class="top-actions">
        <div class="profile">{{ profile?.displayName || '访客' }}</div>
        <el-button @click="handleLogout">退出登录</el-button>
      </div>
    </header>

    <section class="panel login-home-panel">
      <div class="login-home-hero">
        <div>
          <div class="store-hero-kicker">角色首页</div>
          <h2>{{ meta?.title }}</h2>
          <p>这是统一登录后的角色首页占位，后续可按角色接入不同业务视图。</p>
        </div>
        <div class="login-home-summary">
          <article>
            <span>账号</span>
            <strong>{{ profile?.username }}</strong>
          </article>
          <article v-if="profile?.storeName">
            <span>门店</span>
            <strong>{{ profile.storeName }}</strong>
          </article>
          <article>
            <span>角色</span>
            <strong>{{ meta?.title }}</strong>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>
