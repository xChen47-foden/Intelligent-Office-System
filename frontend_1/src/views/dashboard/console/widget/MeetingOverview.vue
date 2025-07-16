<template>
  <div class="meeting-overview art-custom-card">
    <div class="header">
      <span class="title">今日会议</span>
    </div>
    <div class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="meetingsToday.length === 0" class="empty">今日暂无会议</div>
      <ul v-else class="meeting-list">
        <li v-for="m in meetingsToday" :key="m.id" class="meeting-item">
          <span class="time">{{ formatTime(m.time) }}</span>
          <span class="name" :title="m.title">{{ m.title }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { fetchMeetings } from '@/api/meetings'
import dayjs from 'dayjs'

interface MeetingItem {
  id: number
  title: string
  time: string
}

const meetingList = ref<MeetingItem[]>([])
const loading = ref(false)

const todayStr = dayjs().format('YYYY-MM-DD')

const meetingsToday = computed(() =>
  meetingList.value.filter(m => m.time && m.time.startsWith(todayStr))
)

function formatTime(timeStr: string) {
  return dayjs(timeStr).format('HH:mm')
}

async function loadMeetings() {
  loading.value = true
  try {
    const res = await fetchMeetings({ page: 1, pageSize: 50 })
    meetingList.value = (res.data?.list || []).map((m: any) => ({ id: m.id, title: m.title, time: m.time }))
  } catch (e) {
    meetingList.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadMeetings)
</script>

<style scoped lang="scss">
.meeting-overview {
  padding: 20px 24px 18px 24px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  .header {
    margin-bottom: 12px;
    .title {
      font-size: 16px;
      font-weight: 500;
      color: var(--art-gray-900);
    }
  }
  .empty, .loading {
    text-align: center;
    color: var(--art-gray-500);
    padding: 20px 0;
  }
  .meeting-list {
    .meeting-item {
      display: flex;
      gap: 12px;
      padding: 6px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      &:last-child { border-bottom: none; }
      .time { color: var(--main-color); font-weight: 500; width: 50px; }
      .name { flex: 1; color: var(--art-gray-800); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    }
  }
}
</style> 