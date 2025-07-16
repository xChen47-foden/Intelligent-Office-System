<template>
  <div class="schedule-overview art-custom-card">
    <div class="header">
      <span class="title">会议总览</span>
      <button class="refresh-btn" @click="refreshSchedule" :disabled="loading">
        <i class="el-icon-refresh"></i>
        刷新
      </button>
    </div>
    
    <div class="schedule-content">
      <div v-if="scheduleList.length === 0" class="empty-state">
        <i class="el-icon-calendar"></i>
        <p>今日暂无会议安排</p>
      </div>
      <div v-else class="schedule-list">
        <div v-for="task in scheduleList" :key="task.id" class="schedule-item">
          <div class="schedule-time">{{ task.time }}</div>
          <div class="schedule-title">{{ task.title }}</div>
        </div>
      </div>
    </div>
    
    <div class="stats-footer">
      <div class="stat-item">
        <span class="stat-label">今日任务</span>
        <span class="stat-value">{{ scheduleList.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已完成</span>
        <span class="stat-value">{{ completedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">进行中</span>
        <span class="stat-value">{{ scheduleList.length - completedCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getTodaySchedule, type ScheduleTask } from '@/api/dashboard'

const scheduleList = ref<ScheduleTask[]>([])
const loading = ref(false)

const completedCount = computed(() => {
  // 这里可以根据实际情况判断完成状态
  // 目前假设已完成的任务数量
  return Math.floor(scheduleList.value.length * 0.6)
})

const refreshSchedule = async () => {
  loading.value = true
  try {
    console.log('开始获取日程数据...')
    const data = await getTodaySchedule()
    console.log('获取到的日程数据:', data)
    // 直接使用获取到的数据，如果没有数据就显示空列表
    scheduleList.value = data || []
    console.log('最终scheduleList.value:', scheduleList.value)
  } catch (error) {
    console.error('刷新日程失败:', error)
    // 出错时也显示空列表，不使用默认数据
    scheduleList.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshSchedule()
})
</script>

<style lang="scss" scoped>
.schedule-overview {
  padding: 20px 24px 18px 24px;
  margin-bottom: 15px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    
    .title {
      font-size: 16px;
      font-weight: 500;
      color: var(--art-gray-900);
    }
  }
  
  .schedule-content {
    min-height: 120px;
    margin-bottom: 16px;
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 120px;
      color: var(--art-gray-500);
      
      i {
        font-size: 32px;
        margin-bottom: 8px;
      }
      
      p {
        font-size: 14px;
        margin: 0;
      }
    }
    
    .schedule-list {
      max-height: 200px;
      overflow-y: auto;
      
      .schedule-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--art-gray-200);
        
        &:last-child {
          border-bottom: none;
        }
        
        .schedule-time {
          width: 60px;
          font-size: 12px;
          color: var(--main-color);
          font-weight: 500;
          flex-shrink: 0;
        }
        
        .schedule-title {
          flex: 1;
          font-size: 14px;
          color: var(--art-gray-800);
          margin-left: 12px;
        }
      }
    }
  }
  
  .stats-footer {
    display: flex;
    justify-content: space-between;
    padding-top: 16px;
    border-top: 1px solid var(--art-gray-200);
    
    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex: 1;
      
      .stat-label {
        font-size: 12px;
        color: var(--art-gray-600);
        margin-bottom: 4px;
      }
      
      .stat-value {
        font-size: 16px;
        font-weight: bold;
        color: var(--main-color);
      }
    }
  }
}

// 按钮样式
.refresh-btn {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--art-gray-300);
  border-radius: 4px;
  background: var(--art-main-bg-color);
  color: var(--art-gray-700);
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    color: var(--main-color);
    border-color: var(--main-color);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  i {
    margin-right: 4px;
  }
}

// 滚动条样式
.schedule-list::-webkit-scrollbar {
  width: 4px;
}

.schedule-list::-webkit-scrollbar-track {
  background: var(--art-gray-100);
  border-radius: 2px;
}

.schedule-list::-webkit-scrollbar-thumb {
  background: var(--art-gray-400);
  border-radius: 2px;
}

.schedule-list::-webkit-scrollbar-thumb:hover {
  background: var(--art-gray-500);
}
</style> 