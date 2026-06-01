<script setup>
import { onMounted, ref } from 'vue'
import { fetchStoreCatalog, wechatLogin } from '../../api'
import { buildRoleEntryUrl, buildStoredProfile, miniRoles, saveRoleProfile } from '../../role-auth.mjs'

const store = ref(null)
const loadingRole = ref('')
const notice = ref('')

const roleOpenids = {
  customer: 'openid_customer_001',
  boss: 'openid_boss_001',
  staff: 'openid_staff_001',
  kitchen: 'openid_kitchen_001'
}

onMounted(async () => {
  try {
    const catalog = await fetchStoreCatalog(1)
    store.value = catalog.store
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '门店信息加载失败'
  }
})

async function enterAs(role) {
  loadingRole.value = role.code
  notice.value = ''
  try {
    const openid = roleOpenids[role.code]
    const payload = await wechatLogin({ openid, store_id: 1 })
    const profile = buildStoredProfile(payload, openid)
    saveRoleProfile(profile)
    uni.navigateTo({ url: buildRoleEntryUrl(profile) })
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '账号进入失败'
  } finally {
    loadingRole.value = ''
  }
}
</script>

<template>
  <view class="page app-page test-home-page">
    <view class="app-hero green-hero">
      <view class="hero-copy">
        <text class="eyebrow">测试用户入口</text>
        <text class="store-name">{{ store?.name || '默认门店' }}</text>
        <text class="hero-subtitle">点击角色后走真实登录流程，进入对应小程序页面</text>
      </view>
      <view class="hero-orb">测</view>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="card feature-card">
      <view class="section-title">
        <text>选择测试账号</text>
        <text>门店 #1 · {{ store?.business_hours || '读取中' }}</text>
      </view>
      <view class="prototype-grid">
        <view
          v-for="role in miniRoles"
          :key="role.code"
          class="prototype-tile"
          :class="{ 'is-loading': loadingRole === role.code }"
          @click="enterAs(role)"
          hover-class="prototype-tile-hover"
        >
          <text class="tile-icon">{{ role.label.slice(0, 1) }}</text>
          <text class="tile-title">{{ role.label }}</text>
          <text class="tile-desc">{{ role.description }}</text>
        </view>
      </view>
    </view>
  </view>
</template>
