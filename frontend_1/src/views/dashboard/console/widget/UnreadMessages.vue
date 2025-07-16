<template>
  <div class="unread-msg art-custom-card">
    <div class="header">
      <span class="title">未读消息</span>
    </div>
    <div class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else class="counts">
        <div class="count-item">
          <span class="num">{{ counts.personal }}</span>
          <span class="label">私聊</span>
        </div>
        <div class="count-item">
          <span class="num">{{ counts.group }}</span>
          <span class="label">群聊</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUnreadCounts, getGroupUnreadCounts } from '@/api/message'

const counts = ref({ personal: 0, group: 0 })
const loading = ref(false)

async function loadCounts() {
  loading.value = true
  try {
    const [p, g] = await Promise.all([getUnreadCounts(), getGroupUnreadCounts()])
    counts.value = { personal: p.data?.count || 0, group: g.data?.count || 0 }
  } catch (e) {
    counts.value = { personal: 0, group: 0 }
  } finally {
    loading.value = false
  }
}

onMounted(loadCounts)
</script>
<style scoped lang="scss">
.unread-msg {
  padding: 20px 24px 18px 24px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  .header { margin-bottom: 12px; .title { font-size: 16px; font-weight: 500; color: var(--art-gray-900); } }
  .counts {
    display: flex;
    justify-content: space-around;
    .count-item { text-align: center; .num { font-size: 24px; color: var(--main-color); font-weight: 600; } .label { font-size: 12px; color: var(--art-gray-600); } }
  }
  .loading { text-align: center; color: var(--art-gray-500); padding: 20px 0; }
}
</style> 