<template>
  <div class="today-tasks art-custom-card">
    <div class="header">
      <div class="icon-circle">
        <i class="el-icon-date"></i>
      </div>
      <h3 class="title">今日任务</h3>
      <div class="header-right">
        <div class="completion-rate" v-if="todayTasks.length > 0">
          <span class="rate-text">完成率</span>
          <span class="rate-number">{{ completionRate }}%</span>
        </div>
        <el-button type="primary" size="small" @click="showAddDialog = true">
          <i class="el-icon-plus"></i>
          添加任务
        </el-button>
      </div>
    </div>
    
    <div class="content">
      <div v-if="todayTasks.length === 0" class="empty-state">
        <i class="el-icon-circle-check"></i>
        <p>暂无任务，添加一个新任务开始您的一天吧！</p>
      </div>
      
      <div v-else class="task-list">
        <div 
          v-for="task in currentPageTasks" 
          :key="task.id" 
          class="task-item"
          :class="{ 'completed': task.completed }"
        >
          <div class="task-checkbox">
            <el-checkbox 
              v-model="task.completed" 
              @change="toggleTask(task)"
            ></el-checkbox>
          </div>
          
          <div class="task-content">
            <div class="task-text" :class="{ 'completed': task.completed }">
              {{ task.content }}
            </div>
            <div class="task-meta">
              <span v-if="task.time" class="task-time">
                <i class="el-icon-time"></i>
                {{ task.time }}
              </span>
              <span v-if="task.endDate" class="task-deadline">
                <i class="el-icon-alarm-clock"></i>
                截止: {{ task.endDate }}
              </span>
            </div>
          </div>
          
          <div class="task-actions">
            <el-button 
              type="danger" 
              size="mini" 
              icon="el-icon-delete"
              @click="deleteTask(task.id)"
              circle
            ></el-button>
          </div>
        </div>
        
        <!-- 分页组件 -->
        <div v-if="totalPages > 1" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="todayTasks.length"
            layout="prev, pager, next"
            :small="true"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 添加任务对话框 -->
    <el-dialog
      title="添加新任务"
      v-model="showAddDialog"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="newTask" label-width="80px">
        <el-form-item label="任务内容" required>
          <el-input
            v-model="newTask.content"
            placeholder="请输入任务内容"
            maxlength="100"
            show-word-limit
          ></el-input>
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-time-picker
            v-model="newTask.time"
            format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
          ></el-time-picker>
        </el-form-item>
        
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="newTask.endDate"
            type="date"
            placeholder="选择截止日期"
            style="width: 100%"
          ></el-date-picker>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-radio-group v-model="newTask.type">
            <el-radio label="bg-primary">普通</el-radio>
            <el-radio label="bg-success">重要</el-radio>
            <el-radio label="bg-warning">提醒</el-radio>
            <el-radio label="bg-danger">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addTask" :loading="adding">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

interface Task {
  id: number
  content: string
  time: string
  completed: boolean
  date: string
  type: string
  endDate: string
}

const taskList = ref<Task[]>([])
// 当天日期字符串
const todayStr = new Date().toISOString().split('T')[0]

// 只取当天任务
const todayTasks = computed(() => taskList.value.filter(t => (t.date || '').slice(0, 10) === todayStr))

const showAddDialog = ref(false)
const adding = ref(false)

// 分页相关状态
const currentPage = ref(1)
const pageSize = ref(8) // 每页显示8个任务

const newTask = ref({
  content: '',
  time: '',
  endDate: '',
  type: 'bg-primary'
})

// 获取任务列表
const loadTasks = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/today-tasks', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      taskList.value = response.data.tasks || []
      ensurePageInRange()
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 添加任务
const addTask = async () => {
  if (!newTask.value.content.trim()) {
    ElMessage.warning('请输入任务内容')
    return
  }
  
  adding.value = true
  try {
    const token = localStorage.getItem('token')
    const taskData = {
      content: newTask.value.content,
      time: newTask.value.time ? formatTime(newTask.value.time) : '',
      endDate: newTask.value.endDate ? formatDate(newTask.value.endDate) : '',
      type: newTask.value.type,
      completed: false,
      date: new Date().toISOString().split('T')[0]
    }
    
    const response = await axios.post('/api/today-tasks', taskData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data.code === 0) {
      ElMessage.success('任务添加成功')
      showAddDialog.value = false
      // 重置表单
      newTask.value = {
        content: '',
        time: '',
        endDate: '',
        type: 'bg-primary'
      }
      // 重新加载任务列表
      await loadTasks()
    } else {
      ElMessage.error(response.data.msg || '添加任务失败')
    }
  } catch (error) {
    console.error('添加任务失败:', error)
    ElMessage.error('添加任务失败')
  } finally {
    adding.value = false
  }
}

// 切换任务完成状态
const toggleTask = async (task: Task) => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.put(`/api/today-tasks/${task.id}`, {
      content: task.content,
      time: task.time,
      endDate: task.endDate,
      type: task.type,
      completed: task.completed,
      date: task.date
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data.code !== 0) {
      ElMessage.error('更新任务状态失败')
      // 恢复原状态
      task.completed = !task.completed
    }
  } catch (error) {
    console.error('更新任务状态失败:', error)
    ElMessage.error('更新任务状态失败')
    // 恢复原状态
    task.completed = !task.completed
  }
}

// 删除任务
const deleteTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    const token = localStorage.getItem('token')
    const response = await axios.delete(`/api/today-tasks/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      ElMessage.success('任务删除成功')
      await loadTasks()
    } else {
      ElMessage.error(response.data.msg || '删除任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

// 格式化时间
const formatTime = (time: any) => {
  if (!time) return ''
  if (typeof time === 'string') return time
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 格式化日期
const formatDate = (date: any) => {
  if (!date) return ''
  if (typeof date === 'string') return date
  const d = new Date(date)
  return d.toISOString().split('T')[0]
}

// 计算完成率（当天任务）
const completionRate = computed(() => {
  if (todayTasks.value.length === 0) return 0
  const completedTasks = todayTasks.value.filter(task => task.completed).length
  return Math.round((completedTasks / todayTasks.value.length) * 100)
})

// 计算总页数（当天任务）
const totalPages = computed(() => {
  return Math.ceil(todayTasks.value.length / pageSize.value)
})

// 计算当前页显示的任务（当天任务）
const currentPageTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return todayTasks.value.slice(start, end)
})

// 页码变化处理
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 在 loadTasks 结束后如果当前页超出总页数则重置
const ensurePageInRange = () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value || 1
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style lang="scss" scoped>
.today-tasks {
  padding: 24px;
  background: var(--art-main-bg-color);
  border-radius: calc(var(--custom-radius) + 4px);
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
  
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    
    .icon-circle {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      
      i {
        font-size: 18px;
        color: white;
      }
    }
    
    .title {
      font-size: 18px;
      font-weight: 600;
      color: var(--art-gray-900);
      margin: 0;
      flex: 1;
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .completion-rate {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 8px 12px;
      background: linear-gradient(135deg, #e8f5e8 0%, #f0f9ff 100%);
      border-radius: 8px;
      border: 1px solid #e1f5fe;
      
      .rate-text {
        font-size: 12px;
        color: var(--art-gray-600);
        margin-bottom: 2px;
      }
      
      .rate-number {
        font-size: 18px;
        font-weight: 600;
        color: #52c41a;
      }
    }
  }
  
  .content {
    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--art-gray-500);
      
      i {
        font-size: 48px;
        color: var(--art-gray-300);
        margin-bottom: 16px;
        display: block;
      }
      
      p {
        margin: 0;
        font-size: 14px;
      }
    }
    
    .task-list {
      .task-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        transition: all 0.3s ease;
        
        &:last-child {
          border-bottom: none;
        }
        
        &:hover {
          background: var(--el-color-primary-light-9);
          border-radius: 8px;
          margin: 0 -8px;
          padding: 12px 8px;
        }
        
        &.completed {
          opacity: 0.6;
        }
        
        .task-checkbox {
          margin-right: 12px;
        }
        
        .task-content {
          flex: 1;
          
          .task-text {
            font-size: 14px;
            color: var(--art-gray-800);
            margin-bottom: 4px;
            line-height: 1.4;
            
            &.completed {
              text-decoration: line-through;
              color: var(--art-gray-500);
            }
          }
          
          .task-meta {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--art-gray-500);
            
            .task-time,
            .task-deadline {
              display: flex;
              align-items: center;
              gap: 4px;
              
              i {
                font-size: 12px;
              }
            }
            
            .task-deadline {
              color: #f56c6c;
            }
          }
        }
        
        .task-actions {
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        
        &:hover .task-actions {
          opacity: 1;
        }
      }
      
      .pagination-wrapper {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color-lighter);
      }
    }
  }
}

.dark {
  .today-tasks {
    .header {
      .completion-rate {
        background: linear-gradient(135deg, #1a2f1a 0%, #1a2332 100%);
        border-color: #2a3f2a;
        
        .rate-text {
          color: var(--art-gray-400);
        }
        
        .rate-number {
          color: #73d13d;
        }
      }
    }
    
    .task-list {
      .task-item {
        &:hover {
          background: var(--el-color-primary-dark-2);
        }
      }
    }
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
    color: white;
    padding: 20px;
    margin: 0;
    
    .el-dialog__title {
      color: white;
      font-weight: 600;
    }
    
    .el-dialog__close {
      color: white;
      
      &:hover {
        color: #f0f0f0;
      }
    }
  }
}
</style> 