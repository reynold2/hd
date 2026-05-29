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
  kitchen: 'openid_kitchen_001',
  cashier: 'openid_cashier_001'
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
  <view class="page test-home-page">
    <view class="hero test-hero">
      <view>
        <text class="store-name">{{ store?.name || '默认门店' }}</text>
        <view class="store-meta">
          <text>模拟扫码进入</text>
          <text>门店 #1</text>
          <text>{{ store?.business_hours || '读取真实门店中' }}</text>
        </view>
      </view>
    </view>

    <view v-if="notice" class="api-notice">{{ notice }}</view>

    <view class="card">
      <view class="section-title">
        <text>选择测试账号</text>
        <text>点击后走真实登录</text>
      </view>
      <view class="role-grid">
        <button
          v-for="role in miniRoles"
          :key="role.code"
          class="role-card"
          :disabled="loadingRole === role.code"
          @click="enterAs(role)"
        >
          <text class="role-label">{{ role.label }}</text>
          <text class="role-desc">{{ role.description }}</text>
          <text class="role-meta">{{ roleOpenids[role.code] }}</text>
        </button>
      </view>
    </view>
  </view>
</template>
