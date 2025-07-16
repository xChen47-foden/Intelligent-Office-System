<template>
  <div class="doc-processing-stats art-custom-card">
    <div class="header">
      <span class="title">文档处理统计</span>
    </div>
    <div class="stats-content">
      <div class="stat-item">
        <div class="stat-value">{{ docStats.total }}</div>
        <div class="stat-label">文档总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ docStats.todayProcessed }}</div>
        <div class="stat-label">今日处理</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ docStats.pending }}</div>
        <div class="stat-label">待审批</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DocStatsData {
  total: number
  todayProcessed: number
  pending: number
}

const props = defineProps<{
  data?: DocStatsData
}>()

const docStats = computed(() => {
  return props.data || {
    total: 0,
    todayProcessed: 0,
    pending: 0
  }
})
</script>

<style lang="scss" scoped>
.doc-processing-stats {
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