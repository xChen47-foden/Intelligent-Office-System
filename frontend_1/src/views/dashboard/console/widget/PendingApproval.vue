<template>
  <div class="pending-approval art-custom-card">
    <div class="header">
      <span class="title">待审批事项</span>
    </div>
    <div class="stats-content">
      <div class="stat-item">
        <div class="stat-value">3</div>
        <div class="stat-label">待审批文档</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">1</div>
        <div class="stat-label">待审批合同</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">2</div>
        <div class="stat-label">请假申请</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 可根据实际业务对数据进行props传递或API获取
</script>

<style lang="scss" scoped>
.pending-approval {
  padding: 20px 24px 18px 24px;
  margin-bottom: 15px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  .header {
    display: flex;
    align-items: center;
    margin-bottom: 18px;
    .title {
      font-size: 16px;
      font-weight: 500;
      color: var(--art-gray-900);
    }
  }
  .stats-content {
    display: flex;
    justify-content: space-between;
    .stat-item {
      flex: 1;
      text-align: center;
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: var(--main-color);
        margin-bottom: 4px;
      }
      .stat-label {
        font-size: 13px;
        color: var(--art-gray-600);
      }
    }
  }
}
</style> 