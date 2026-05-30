<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import {
  DataLine,
  Dish,
  Food,
  Grid,
  House,
  Monitor,
  Money,
  Setting,
  Shop,
  Tickets,
  User
} from '@element-plus/icons-vue'
import { getStoredProfile, logoutAdminAndRedirect } from './auth'

const route = useRoute()
const profile = computed(() => getStoredProfile())
const showShell = computed(() => route.path !== '/login')

const navItems = [
  { label: '首页概览', path: '/', icon: House },
  { label: '队列管理', path: '/queue', icon: Tickets },
  { label: '制作工作台', path: '/production', icon: Dish },
  { label: '收银记账', path: '/cashier', icon: Money },
  { label: '门店管理', path: '/store', icon: Shop },
  { label: '菜品管理', path: '/dishes', icon: Food },
  { label: '员工权限', path: '/staff', icon: User },
  { label: '平台审核', path: '/platform', icon: Grid },
  { label: '用户管理', path: '/users', icon: User },
  { label: '大屏叫号', path: '/screen', icon: Monitor },
  { label: '数据统计', path: '/reports', icon: DataLine },
  { label: '系统设置', path: '/settings', icon: Setting }
]

const activePath = computed(() => route.path)

function handleLogout() {
  logoutAdminAndRedirect()
}
</script>

<template>
  <div v-if="showShell" class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">锅</div>
        <div>
          <strong>等锅叫号</strong>
          <span>商家管理后台</span>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="{ active: activePath === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="store-card">
        <strong>{{ profile?.storeName || '川香麻辣烫（中山店）' }}</strong>
        <span>{{ profile?.displayName || '多角色操作台' }}</span>
        <button type="button" @click.prevent.stop="handleLogout">退出登录</button>
      </div>
    </aside>

    <main class="workspace">
      <RouterView />
    </main>
  </div>

  <div v-else class="login-shell">
    <RouterView />
  </div>
</template>
