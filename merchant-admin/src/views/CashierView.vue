<template>
  <div class="route-page">
    <header class="topbar">
      <div>
        <p>工作台 / 收银</p>
        <h1>收银工作台</h1>
        <p class="route-description">处理待结账号码、核对金额与确认支付</p>
      </div>
    </header>

    <section class="module-grid">
      <article class="panel module-hero">
        <div class="module-icon">C</div>
        <div>
          <div class="store-hero-kicker">收银台</div>
          <h2>当前待结账号码</h2>
          <p>这里可以接入收银列表、二维码出示和支付确认。</p>
        </div>
      </article>

      <article class="panel">
        <div class="panel-title"><h2>收银流程</h2></div>
        <ul class="module-checklist">
          <li>核对金额</li>
          <li>出示二维码</li>
          <li>确认支付</li>
          <li>完成释放号码</li>
        </ul>
      </article>

      <article class="panel">
        <div class="panel-title"><h2>说明</h2></div>
        <p class="module-note">收银角色仅能看到自己门店的收银工作内容。</p>
      </article>
    </section>
  </div>
</template>
