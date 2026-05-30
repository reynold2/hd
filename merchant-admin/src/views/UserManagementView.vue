<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { createAdminUser, deleteAdminUser, fetchAdminUsers, updateAdminUser, type AdminUser } from '../api'
import type { AdminRouteMeta } from '../router'

const route = useRoute()
const meta = computed(() => route.meta as AdminRouteMeta)
const saveNotice = ref('')
const saving = ref(false)
const users = ref<AdminUser[]>([])

const form = reactive({
  id: 0,
  username: '',
  displayName: '',
  password: '123456',
  avatarUrl: '',
  role: '服务员',
  storeId: 1,
  openid: ''
})

const canSave = computed(() => form.username.trim().length > 0 && form.displayName.trim().length > 0)

onMounted(loadUsers)

async function loadUsers() {
  try {
    users.value = await fetchAdminUsers()
  } catch (error) {
    saveNotice.value = error instanceof Error ? error.message : '用户列表加载失败'
  }
}

function selectUser(user: AdminUser) {
  form.id = user.id
  form.username = user.username
  form.displayName = user.display_name
  form.role = user.role
  form.storeId = user.store_id || 1
  form.openid = user.openid || ''
  form.password = user.password || '123456'
  form.avatarUrl = user.avatar_url || ''
}

async function saveUser() {
  if (!canSave.value) {
    saveNotice.value = '请输入账号和显示名称'
    return
  }
  saving.value = true
  try {
    const payload = {
      username: form.username,
      display_name: form.displayName,
      password: form.password,
      avatar_url: form.avatarUrl,
      role: form.role,
      store_id: form.storeId,
      openid: form.openid
    }
    if (form.id) {
      await updateAdminUser(form.id, payload)
      saveNotice.value = '用户信息已更新'
    } else {
      await createAdminUser(payload)
      saveNotice.value = '用户已创建'
    }
    await loadUsers()
  } catch (error) {
    saveNotice.value = error instanceof Error ? error.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeUser(id: number) {
  try {
    await deleteAdminUser(id)
    saveNotice.value = '员工已删除'
    await loadUsers()
  } catch (error) {
    saveNotice.value = error instanceof Error ? error.message : '删除失败'
  }
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
    </header>

    <section class="module-grid user-management-grid">
      <article class="panel module-hero">
        <div class="module-icon">U</div>
        <div>
          <h2>用户与员工管理</h2>
          <p>系统管理员和平台管理员可管理账号、密码、头像和门店绑定。</p>
        </div>
      </article>

      <article class="panel user-list-panel">
        <div class="panel-title">
          <h2>员工列表</h2>
          <el-tag type="warning">门店隔离</el-tag>
        </div>
        <div class="user-list">
          <button v-for="user in users" :key="user.id" class="user-card" @click="selectUser(user)">
            <strong>{{ user.display_name }}</strong>
            <span>{{ user.username }}</span>
            <small>{{ user.role }} · 门店 #{{ user.store_id || '-' }} · {{ user.status || '启用' }}</small>
            <el-button link type="danger" @click.stop="removeUser(user.id)">删除</el-button>
          </button>
        </div>
      </article>

      <article class="panel user-form-panel">
        <div class="panel-title">
          <h2>编辑信息</h2>
        </div>
        <div class="user-form-grid">
          <el-input v-model="form.username" placeholder="账号" />
          <el-input v-model="form.displayName" placeholder="显示名称" />
          <el-input v-model="form.password" placeholder="密码" />
          <el-input v-model="form.avatarUrl" placeholder="头像地址" />
          <el-select v-model="form.role" placeholder="角色">
            <el-option label="服务员" value="服务员" />
            <el-option label="制作" value="制作" />
            <el-option label="收银" value="收银" />
            <el-option label="老板" value="老板" />
          </el-select>
          <el-input v-model="form.openid" placeholder="微信 openid" />
        </div>
        <div class="user-actions">
          <el-button type="primary" :loading="saving" :disabled="!canSave" @click="saveUser">保存</el-button>
          <el-button @click="form.id = 0; form.username = ''; form.displayName = ''; form.password = '123456'; form.avatarUrl = ''; form.openid = ''">清空</el-button>
        </div>
      </article>
    </section>
  </div>
</template>
