<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { fetchStoreCatalog, updateWechatPaymentQr } from '../api'

const loading = ref(false)
const notice = ref('')
const store = ref<any>(null)
const paymentQrForm = reactive({
  wechat_payment_qr_url: '',
  wechat_payment_qr_name: ''
})

onMounted(loadStore)

async function loadStore() {
  loading.value = true
  try {
    const catalog = await fetchStoreCatalog(1)
    store.value = catalog.store
    paymentQrForm.wechat_payment_qr_url = catalog.store.wechat_payment_qr_url || ''
    paymentQrForm.wechat_payment_qr_name = catalog.store.wechat_payment_qr_name || catalog.store.payment_qr || '微信收款码'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '门店信息加载失败'
  } finally {
    loading.value = false
  }
}

async function savePaymentQr() {
  loading.value = true
  notice.value = ''
  try {
    store.value = await updateWechatPaymentQr(1, paymentQrForm)
    paymentQrForm.wechat_payment_qr_url = store.value.wechat_payment_qr_url || ''
    paymentQrForm.wechat_payment_qr_name = store.value.wechat_payment_qr_name || '微信收款码'
    notice.value = '微信收款二维码已保存'
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '收款码保存失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="route-page">
    <header class="topbar">
      <div>
        <p>设置 / 门店</p>
        <h1>门店老板首页</h1>
        <p class="route-description">查看本门店经营、员工、收银和大屏状态</p>
        <p v-if="notice" class="api-notice">{{ notice }}</p>
      </div>
    </header>

    <section class="module-grid">
      <article class="panel module-hero">
        <div class="module-icon">S</div>
        <div>
          <div class="store-hero-kicker">门店首页</div>
          <h2>{{ store?.name || '当前门店经营视图' }}</h2>
          <p>{{ store?.address || '读取门店真实配置中' }}</p>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title"><h2>门店能力</h2></div>
        <ul class="module-checklist">
          <li>营业状态配置</li>
          <li>员工角色管理</li>
          <li>微信收款码配置</li>
          <li>大屏展示联动</li>
        </ul>
      </article>

      <article class="panel module-form-panel">
        <div class="panel-title">
          <h2>微信收款码</h2>
          <el-tag type="success">老板可改</el-tag>
        </div>
        <div class="module-form">
          <img
            v-if="paymentQrForm.wechat_payment_qr_url"
            class="store-payment-preview"
            :src="paymentQrForm.wechat_payment_qr_url"
            :alt="paymentQrForm.wechat_payment_qr_name"
          />
          <div v-else class="store-qr-box">请配置微信收款二维码</div>
          <el-input v-model="paymentQrForm.wechat_payment_qr_name" placeholder="收款码名称" />
          <el-input v-model="paymentQrForm.wechat_payment_qr_url" placeholder="https://.../wechat-pay.jpg 或 /static/..." />
          <el-button type="primary" :loading="loading" @click="savePaymentQr">保存微信收款码</el-button>
        </div>
      </article>
    </section>
  </div>
</template>
