<script>
export default {
  onLaunch() {
    try {
      const current = uni.getStorageSync('customer-miniapp-role-auth')
      if (!current) {
        uni.setStorageSync('customer-miniapp-role-auth', JSON.stringify({ code: 'customer', label: '顾客', openid: 'openid_customer_001', storeId: 1, number: 'A018' }))
      }
    } catch {}
  }
}
</script>
