<template>
  <div class="route-page screen-page">
    <header class="topbar">
      <div>
        <p>展示 / 大屏</p>
        <h1>门店大屏</h1>
        <p class="route-description">实时叫号、等待队列与制作进度展示</p>
      </div>
    </header>

    <section class="screen-grid">
      <article class="screen-current">
        <span>当前叫号</span>
        <strong>A018</strong>
        <p>川香麻辣烫（中山店）</p>
      </article>
      <article class="screen-summary panel">
        <article><span>等待中</span><strong>12</strong><small>单</small></article>
        <article><span>制作中</span><strong>4</strong><small>单</small></article>
        <article><span>待结账</span><strong>3</strong><small>单</small></article>
      </article>
      <article class="panel screen-panel-large">
        <div class="panel-title"><h2>实时队列</h2></div>
        <div class="screen-list">
          <div class="screen-row"><strong>A019</strong><span>等待中</span><span>18 分钟</span></div>
          <div class="screen-row"><strong>A020</strong><span>制作中</span><span>12 分钟</span></div>
          <div class="screen-row"><strong>A021</strong><span>待结账</span><span>5 分钟</span></div>
        </div>
      </article>
    </section>
  </div>
</template>
