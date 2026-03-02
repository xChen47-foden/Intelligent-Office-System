<template>
  <div class="console">
    <!-- 主要内容区域 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：今日任务 -->
      <el-col :span="12">
        <el-card class="task-card">
          <template #header>
            <div class="card-header">
              <span>📝 今日任务</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="showAddTaskDialog">
                  <el-icon><Plus /></el-icon>
                  添加任务
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- 任务完成率统计 -->
          <div class="task-stats">
            <div class="stats-item">
              <div class="stats-number">{{ todayTasks.length }}</div>
              <div class="stats-label">总任务数</div>
            </div>
            <div class="stats-item">
              <div class="stats-number">{{ completedTasksCount }}</div>
              <div class="stats-label">已完成</div>
            </div>
            <div class="stats-item">
              <div class="stats-number">{{ completionRate }}%</div>
              <div class="stats-label">完成率</div>
            </div>
          </div>
          
          <!-- 完成率进度条 -->
          <div class="completion-progress">
            <div class="progress-label">任务完成进度</div>
            <el-progress 
              :percentage="completionRate" 
              :color="progressColor"
              :stroke-width="8"
              :show-text="false"
            />
            <div class="progress-text">{{ completedTasksCount }}/{{ todayTasks.length }} 已完成</div>
          </div>
          
          <div class="task-list" :class="{ 'no-scroll': todayTasks.length === 0 }">
            <div v-if="todayTasks.length === 0" class="empty-state">
              <el-empty description="暂无任务">
                <el-button type="primary" @click="showAddTaskDialog">添加第一个任务</el-button>
              </el-empty>
            </div>
            <div v-else>
              <div
                v-for="task in todayTasks"
                :key="task.id"
                class="task-item"
                :class="{ 'completed': task.completed }"
              >
                <el-checkbox
                  v-model="task.completed"
                  @change="updateTaskStatus(task)"
                  class="task-checkbox"
                />
                <div class="task-content">
                  <div class="task-title">{{ task.content }}</div>
                  <div class="task-meta">
                    <span class="task-time">⏰ {{ task.time }}</span>
                    <span class="task-type" :class="task.type">{{ getTaskTypeText(task.type) }}</span>
                  </div>
                </div>
                <div class="task-actions">
                  <el-button type="text" size="small" @click="editTask(task)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button type="text" size="small" @click="deleteTask(task.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：今日会议 -->
      <el-col :span="12">
        <el-card class="schedule-card">
          <template #header>
            <div class="card-header">
              <span>📅 今日会议</span>
            </div>
          </template>
          <div class="schedule-content">
            <div class="schedule-list" :class="{ 'no-scroll': todaySchedule.length === 0 }">
            <div v-if="todaySchedule.length === 0" class="empty-schedule">
              <el-empty description="今日暂无会议" :image-size="80" />
            </div>
            <div v-else>
              <div
                v-for="item in todaySchedule"
                :key="item.id"
                class="schedule-item"
              >
                <div class="schedule-time">{{ item.time }}</div>
                <div class="schedule-title">{{ item.title }}</div>
              </div>
              </div>
            </div>
            <div class="schedule-footer">
              <el-button 
                size="small" 
                @click="() => loadTodaySchedule(true)" 
                type="info" 
                class="refresh-btn"
                :loading="scheduleLoading"
                :disabled="scheduleLoading"
              >
                <el-icon v-if="!scheduleLoading"><Refresh /></el-icon>
                {{ scheduleLoading ? '刷新中...' : '刷新' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 部门信息区域 -->
    <el-row :gutter="20" class="department-section" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="department-card">
          <template #header>
            <div class="card-header">
              <span>🏢 {{ departmentInfo.name }}</span>
            </div>
          </template>
          <div class="department-content">
            <div class="department-leader">
              <strong>部门负责人：</strong>{{ departmentInfo.leader }}
            </div>
            <div class="department-responsibilities">
              <strong>部门职责：</strong>
              <div class="responsibility-list" v-if="departmentInfo.responsibilities && departmentInfo.responsibilities.length > 0">
                <div v-for="(responsibility, index) in departmentInfo.responsibilities" :key="index" class="responsibility-item">
                  <span class="responsibility-icon">📋</span>
                  {{ responsibility }}
                </div>
              </div>
              <div v-else class="no-responsibilities">
                <span class="no-data-icon">📝</span>
                暂无部门职责信息
              </div>
            </div>
            <div class="department-members">
              <strong>部门成员：</strong>
              <div class="member-tags">
                <el-tag v-for="member in departmentInfo.members" :key="member" size="small">
                  {{ member }}
                </el-tag>
              </div>
            </div>
            <div class="department-contact">
              <div><strong>联系邮箱：</strong>{{ departmentInfo.email }}</div>
              <div><strong>联系电话：</strong>{{ departmentInfo.phone }}</div>
            </div>
            <div class="department-announcement" v-if="departmentInfo.announcement">
              <strong>部门公告：</strong>
              <div class="announcement-text">{{ departmentInfo.announcement }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加任务对话框 -->
    <el-dialog v-model="taskDialogVisible" title="添加任务" width="500px">
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务内容">
          <el-input v-model="taskForm.content" placeholder="请输入任务内容" />
        </el-form-item>
        <el-form-item label="时间">
          <el-time-picker
            v-model="taskForm.time"
            format="HH:mm"
            placeholder="选择时间"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="taskForm.type" placeholder="选择任务类型">
            <el-option label="普通" value="bg-primary" />
            <el-option label="重要" value="bg-warning" />
            <el-option label="紧急" value="bg-danger" />
            <el-option label="已完成" value="bg-success" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="taskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTask">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, ChatDotRound, VideoCamera, Collection, Document, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { taskService, type Task, eventEmitter, MEETING_EVENTS } from '@/services/taskService'
import { fetchMeetings } from '@/api/meetings'
import { getDepartmentInfo } from '@/api/dashboard'
import dayjs from 'dayjs'

const router = useRouter()

// 类型定义
interface DepartmentInfo {
  name: string
  responsibilities: string[]
  leader: string
  members: string[]
  email: string
  phone: string
  announcement?: string
}

interface ScheduleItem {
  id: number
  title: string
  time: string
}

// 响应式数据
const departmentInfo = ref<DepartmentInfo>({
  name: '',
  responsibilities: [],
  leader: '',
  members: [],
  email: '',
  phone: '',
  announcement: ''
})
const todayTasks = ref<Task[]>([])
const todaySchedule = ref<ScheduleItem[]>([])
const scheduleLoading = ref(false)

// 任务对话框
const taskDialogVisible = ref(false)
const taskForm = ref({
  content: '',
  time: '',
  type: 'bg-primary'
})
const editingTask = ref<Task | null>(null)

// 获取部门信息
const loadDepartmentInfo = async () => {
  try {
    console.log('开始加载部门信息...')
    const data = await getDepartmentInfo()
    console.log('获取到的部门信息:', data) // 添加调试信息
    
    if (data && data.responsibilities) {
      departmentInfo.value = {
        name: data.name || '技术部',
        responsibilities: data.responsibilities || [],
        leader: data.leader || '张三',
        members: data.members || ['李四', '王五', '赵六', '钱七'],
        email: data.email || 'tech@company.com',
        phone: data.phone || '010-12345679',
        announcement: data.announcement || '新版系统将于下周上线，请各位做好测试准备！'
      }
    } else {
      // 如果数据格式不正确，使用默认数据
      departmentInfo.value = {
        name: '技术部',
        responsibilities: [
          '负责系统开发与技术架构设计，制定技术方案，编写核心代码，确保系统稳定性',
          '维护服务器运行与数据安全，监控系统性能，备份重要数据，防范安全风险',
          '推动技术创新与产品优化，研究新技术应用，优化用户体验，提升产品竞争力',
          '提供技术支持与培训服务，解决技术问题，培训其他部门员工，编写技术文档'
        ],
        leader: '张三',
        members: ['李四', '王五', '赵六', '钱七'],
        email: 'tech@company.com',
        phone: '010-12345679',
        announcement: '新版系统将于下周上线，请各位做好测试准备！'
      }
    }
    
    console.log('处理后的部门信息:', departmentInfo.value) // 添加调试信息
    console.log('部门职责数量:', departmentInfo.value.responsibilities?.length || 0)
  } catch (error) {
    console.error('获取部门信息失败:', error)
    // 提供默认部门信息
    departmentInfo.value = {
      name: '技术部',
      responsibilities: [
        '负责系统开发与技术架构设计，制定技术方案，编写核心代码，确保系统稳定性',
        '维护服务器运行与数据安全，监控系统性能，备份重要数据，防范安全风险',
        '推动技术创新与产品优化，研究新技术应用，优化用户体验，提升产品竞争力',
        '提供技术支持与培训服务，解决技术问题，培训其他部门员工，编写技术文档'
      ],
      leader: '张三',
      members: ['李四', '王五', '赵六', '钱七'],
      email: 'tech@company.com',
      phone: '010-12345679',
      announcement: '新版系统将于下周上线，请各位做好测试准备！'
    }
  }
}

// 获取今日任务
const loadTodayTasks = async () => {
  try {
    const tasks = await taskService.getTodayTasks()
    // 确保 completed 状态与任务类型同步
    todayTasks.value = tasks.map(task => ({
      ...task,
      completed: task.completed || task.type === 'bg-success'
    }))
  } catch (error) {
    console.error('获取今日任务失败:', error)
    // 提供默认任务数据
    todayTasks.value = [
      {
        id: 1,
        content: '完成系统文档更新',
        time: '09:00',
        completed: false,
        date: new Date().toISOString().split('T')[0],
        type: 'bg-primary'
      },
      {
        id: 2,
        content: '参加团队会议',
        time: '14:00',
        completed: true,
        date: new Date().toISOString().split('T')[0],
        type: 'bg-success'
      },
      {
        id: 3,
        content: '代码审查',
        time: '16:00',
        completed: false,
        date: new Date().toISOString().split('T')[0],
        type: 'bg-warning'
      }
    ]
  }
}

// 获取今日会议
const loadTodaySchedule = async (showMessage: boolean = false) => {
  try {
    scheduleLoading.value = true
    console.log('[loadTodaySchedule] 开始刷新今日会议...')
    
    // 从任务服务获取今日会议数据
    const todayMeetings = await taskService.getTodayMeetings()
    console.log('[loadTodaySchedule] 获取到的今日会议:', todayMeetings)
    
    // 转换为今日会议格式
    todaySchedule.value = todayMeetings.map((meeting: any) => {
      let displayTime = '待定'
      if (meeting.time) {
        try {
          // 处理不同的时间格式
          if (typeof meeting.time === 'string') {
            if (meeting.time.includes('T') || meeting.time.includes(' ')) {
              // ISO格式或包含空格的时间字符串
              displayTime = dayjs(meeting.time).format('HH:mm')
            } else {
              // 如果只是时间字符串（如 "14:30"）
              displayTime = meeting.time
            }
          } else {
            // Date对象
            displayTime = dayjs(meeting.time).format('HH:mm')
          }
        } catch (error) {
          console.error('[loadTodaySchedule] 解析会议时间失败:', error, meeting.time)
          displayTime = '待定'
        }
      }
      
      return {
        id: meeting.id,
        title: meeting.title,
        time: displayTime
      }
    })
    
    console.log('[loadTodaySchedule] 刷新后的今日会议列表:', todaySchedule.value)
    
    // 只在手动刷新时显示消息
    if (showMessage) {
      const count = todaySchedule.value.length
      if (count > 0) {
        ElMessage.success(`已刷新，共 ${count} 个会议`)
      } else {
        ElMessage.info('已刷新，今日暂无会议')
      }
    }
  } catch (error: any) {
    console.error('[loadTodaySchedule] 获取今日会议失败:', error)
    // 只在手动刷新时显示错误消息
    if (showMessage) {
      const errorMsg = error?.response?.data?.msg || error?.message || '未知错误'
      ElMessage.error(`刷新失败: ${errorMsg}`)
    }
    // 提供默认会议数据
    todaySchedule.value = []
  } finally {
    scheduleLoading.value = false
  }
}

// 显示添加任务对话框
const showAddTaskDialog = () => {
  editingTask.value = null
  taskForm.value = {
    content: '',
    time: '',
    type: 'bg-primary'
  }
  taskDialogVisible.value = true
}

// 编辑任务
const editTask = (task: Task) => {
  editingTask.value = task
  taskForm.value = {
    content: task.content,
    time: task.time,
    type: task.type
  }
  taskDialogVisible.value = true
}

// 保存任务
const saveTask = async () => {
  if (!taskForm.value.content.trim()) {
    ElMessage.warning('请输入任务内容')
    return
  }

  try {
    const taskData = {
      content: taskForm.value.content,
      time: taskForm.value.time || new Date().toTimeString().slice(0, 5),
      type: taskForm.value.type,
      completed: taskForm.value.type === 'bg-success',
      date: new Date().toISOString().split('T')[0]
    }

    if (editingTask.value) {
      // 更新任务
      const success = await taskService.updateTask(editingTask.value.id, taskData)
      if (success) {
        ElMessage.success('任务更新成功')
        loadTodayTasks()
      } else {
        ElMessage.error('任务更新失败')
      }
    } else {
      // 添加任务
      const success = await taskService.addTask(taskData)
      if (success) {
        ElMessage.success('任务添加成功')
        loadTodayTasks()
      } else {
        ElMessage.error('任务添加失败')
      }
    }
    
    taskDialogVisible.value = false
  } catch (error) {
    console.error('保存任务失败:', error)
    ElMessage.error('保存任务失败')
  }
}

// 更新任务状态
const updateTaskStatus = async (task: Task) => {
  try {
    const success = await taskService.updateTaskStatus(task.id, task.completed)
    if (success) {
      // 同步本地任务类型，保持“已完成”标签与状态一致
      if (task.completed) {
        task.type = 'bg-success'
      } else if (task.type === 'bg-success') {
        task.type = 'bg-primary'
      }
      ElMessage.success(task.completed ? '任务已完成' : '任务已重新激活')
    } else {
      ElMessage.error('更新任务状态失败')
    }
  } catch (error) {
    console.error('更新任务状态失败:', error)
    ElMessage.error('更新任务状态失败')
  }
}

// 删除任务
const deleteTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const success = await taskService.deleteTask(taskId)
    if (success) {
      ElMessage.success('任务删除成功')
      loadTodayTasks()
    } else {
      ElMessage.error('任务删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

// 获取任务类型文本
const getTaskTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    'bg-primary': '普通',
    'bg-warning': '重要',
    'bg-danger': '紧急',
    'bg-success': '已完成'
  }
  return typeMap[type] || '普通'
}

// 计算完成率
const completedTasksCount = ref(0)
const completionRate = ref(0)
const progressColor = ref('')

const calculateCompletionRate = () => {
  const totalTasks = todayTasks.value.length
  const completed = todayTasks.value.filter(task => task.completed).length
  completedTasksCount.value = completed
  completionRate.value = totalTasks > 0 ? Math.round((completed / totalTasks) * 100) : 0
  
  // 根据完成率设置进度条颜色
  if (totalTasks === 0) {
    progressColor.value = '#909399'
  } else if (completionRate.value >= 80) {
    progressColor.value = '#67C23A' // 绿色 - 优秀
  } else if (completionRate.value >= 50) {
    progressColor.value = '#E6A23C' // 橙色 - 良好
  } else {
    progressColor.value = '#F56C6C' // 红色 - 需要改进
  }
}

// 监听任务变化，重新计算完成率
watch(todayTasks, () => {
  calculateCompletionRate()
}, { deep: true })

// 页面初始化
onMounted(async () => {
  console.log('页面开始初始化...')
  
  // 先设置测试数据，确保显示正常
  departmentInfo.value = {
    name: '技术部',
    responsibilities: [
      '负责系统开发与技术架构设计，制定技术方案，编写核心代码，确保系统稳定性',
      '维护服务器运行与数据安全，监控系统性能，备份重要数据，防范安全风险',
      '推动技术创新与产品优化，研究新技术应用，优化用户体验，提升产品竞争力',
      '提供技术支持与培训服务，解决技术问题，培训其他部门员工，编写技术文档'
    ],
    leader: '张三',
    members: ['李四', '王五', '赵六', '钱七'],
    email: 'tech@company.com',
    phone: '010-12345679',
    announcement: '新版系统将于下周上线，请各位做好测试准备！'
  }
  
  console.log('设置测试数据完成，部门职责数量:', departmentInfo.value.responsibilities.length)
  
  // 然后尝试加载真实数据
  await loadDepartmentInfo()
  await loadTodayTasks()
  await loadTodaySchedule()
  
  // 监听会议数据变更事件
  eventEmitter.on(MEETING_EVENTS.MEETING_CREATED, () => {
    loadTodaySchedule()
  })
  eventEmitter.on(MEETING_EVENTS.MEETING_UPDATED, () => {
    loadTodaySchedule()
  })
  eventEmitter.on(MEETING_EVENTS.MEETING_DELETED, () => {
    loadTodaySchedule()
  })

  // 计算完成率
  calculateCompletionRate()
  
  // 添加调试信息
  console.log('页面初始化完成，当前部门信息:', departmentInfo.value)
  console.log('部门职责数量:', departmentInfo.value.responsibilities?.length || 0)
})

// 组件卸载时清理事件监听
onUnmounted(() => {
  eventEmitter.off(MEETING_EVENTS.MEETING_CREATED, loadTodaySchedule)
  eventEmitter.off(MEETING_EVENTS.MEETING_UPDATED, loadTodaySchedule)
  eventEmitter.off(MEETING_EVENTS.MEETING_DELETED, loadTodaySchedule)
})

// 添加页面激活时的数据刷新
const refreshData = async () => {
  await loadTodayTasks()
  await loadTodaySchedule()
  calculateCompletionRate() // 刷新完成率
}

// 监听页面可见性变化，当页面重新激活时刷新数据
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    refreshData()
  }
})
</script>

<style lang="scss" scoped>
.console {
  padding: 20px;
  min-height: 100vh;
  background: var(--art-bg-color);
  color: var(--art-text-gray-800);
}

// 主要内容样式
.main-content {
  .el-card {
    border: none;
    box-shadow: var(--art-card-shadow);
    height: 600px; // 固定高度确保一致
    background: var(--art-main-bg-color);
    border: 1px solid var(--art-card-border);
  }
  
  .task-card,
  .schedule-card {
    display: flex;
    flex-direction: column;
  }
}

// 卡片头部样式
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: var(--art-text-gray-800);
}

.header-actions {
  display: flex;
  gap: 10px;
}

// 任务列表样式
.task-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
  max-height: 350px; // 为统计信息留出空间
  
  // 没有任务时隐藏滚动条
  &.no-scroll {
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.task-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--art-border-color);
  border-radius: 6px;
  margin-bottom: 10px;
  transition: all 0.3s;
  background: var(--art-main-bg-color);

  &:hover {
    background: var(--art-gray-100);
    border-color: var(--art-gray-300);
  }

  &.completed {
    opacity: 0.6;
    
    .task-title {
      text-decoration: line-through;
    }
  }
}

.task-checkbox {
  margin-right: 12px;
}

.task-content {
  flex: 1;
}

.task-title {
  font-size: 14px;
  color: var(--art-text-gray-800);
  margin-bottom: 4px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-time {
  color: var(--art-text-gray-600);
  font-size: 12px;
}

.task-type {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  color: white;

  &.bg-primary {
    background: #409EFF;
  }

  &.bg-warning {
    background: #E6A23C;
  }

  &.bg-danger {
    background: #F56C6C;
  }

  &.bg-success {
    background: #67C23A;
  }
}

.task-actions {
  display: flex;
  gap: 5px;
}

// 任务完成率统计样式
.task-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid var(--art-border-color);
}

.stats-item {
  text-align: center;
}

.stats-number {
  font-size: 24px;
  font-weight: bold;
  color: var(--art-text-gray-800);
}

.stats-label {
  font-size: 12px;
  color: var(--art-text-gray-600);
  margin-top: 5px;
}

// 完成率进度条样式
.completion-progress {
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid var(--art-border-color);
}

.progress-label {
  font-size: 14px;
  color: var(--art-text-gray-800);
  margin-bottom: 8px;
  font-weight: bold;
}

.progress-text {
  font-size: 12px;
  color: var(--art-text-gray-600);
  text-align: right;
}

// 部门信息样式
.department-card {
  height: auto !important; // 覆盖固定高度
  min-height: 200px;
  background: var(--art-main-bg-color);
  border: 1px solid var(--art-card-border);
}

.department-content {
  line-height: 1.6;
  font-size: 13px;
  color: var(--art-text-gray-700);
}

.department-leader,
.department-contact > div {
  margin-bottom: 8px;
  color: var(--art-text-gray-700);
}

.department-responsibilities {
  margin-bottom: 12px;
}

.responsibility-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.responsibility-item {
  background: #409EFF;
  color: #ffffff;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  transition: all 0.3s ease;
  width: 100%;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    background: #66b1ff;
  }
}

.responsibility-icon {
  font-size: 14px;
  opacity: 0.9;
  flex-shrink: 0;
}

.no-responsibilities {
  color: var(--art-text-gray-500);
  font-style: italic;
  font-size: 12px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.no-data-icon {
  font-size: 14px;
  opacity: 0.7;
}

.department-members {
  margin-bottom: 12px;
}

.member-tags {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.department-announcement {
  margin-top: 12px;
}

.announcement-text {
  margin-top: 4px;
  padding: 8px;
  background: var(--art-bg-primary);
  border-radius: 4px;
  color: var(--art-text-gray-700);
  font-size: 12px;
  line-height: 1.5;
  border: 1px solid var(--art-border-color);
}

// 会议内容容器
.schedule-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

// 会议列表样式
.schedule-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
  min-height: 0; // 允许flex收缩
  
  // 没有会议时隐藏滚动条
  &.no-scroll {
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

// 会议底部刷新按钮
.schedule-footer {
  padding: 10px 0;
  border-top: 1px solid var(--art-border-color);
  display: flex;
  justify-content: flex-end;
  margin-top: auto;
  flex-shrink: 0;
  
  .refresh-btn {
    margin-right: 0;
  }
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--art-border-color);
  border-radius: 6px;
  margin-bottom: 10px;
  transition: all 0.3s;
  background: var(--art-main-bg-color);

  &:hover {
    background: var(--art-gray-100);
    border-color: var(--art-gray-300);
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.schedule-time {
  width: 60px;
  color: #409EFF;
  font-weight: bold;
  font-size: 12px;
  margin-right: 12px;
}

.schedule-title {
  flex: 1;
  color: var(--art-text-gray-800);
  font-size: 14px;
}

// 快速操作样式
.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: var(--art-gray-100);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid var(--art-border-color);

  &:hover {
    background: var(--art-gray-200);
    transform: translateY(-2px);
    box-shadow: var(--art-box-shadow-sm);
  }
}

.action-icon {
  font-size: 32px;
  color: #409EFF;
  margin-bottom: 8px;
}

.empty-state,
.empty-schedule {
  text-align: center;
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.empty-schedule {
  min-height: 300px;
}

// 滚动条样式
.task-list::-webkit-scrollbar,
.schedule-list::-webkit-scrollbar {
  width: 6px;
}

.task-list::-webkit-scrollbar-track,
.schedule-list::-webkit-scrollbar-track {
  background: var(--art-gray-100);
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb,
.schedule-list::-webkit-scrollbar-thumb {
  background: var(--art-gray-300);
  border-radius: 3px;

  &:hover {
    background: var(--art-gray-400);
  }
}

// 深色模式支持
:deep(.dark) {
  .console {
    background: var(--art-bg-color);
    color: var(--art-text-gray-800);
  }

  .main-content .el-card {
    background: var(--art-main-bg-color);
    border-color: var(--art-border-color);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .card-header {
    color: var(--art-text-gray-800);
  }

  .task-item,
  .schedule-item {
    background: var(--art-main-bg-color);
    border-color: var(--art-border-color);

    &:hover {
      background: var(--art-gray-100);
      border-color: var(--art-gray-300);
    }
  }

  .task-title,
  .schedule-title {
    color: var(--art-text-gray-800);
  }

  .task-time,
  .stats-label,
  .progress-text {
    color: var(--art-text-gray-600);
  }

  .stats-number,
  .progress-label {
    color: var(--art-text-gray-800);
  }

  .task-stats,
  .completion-progress {
    border-bottom-color: var(--art-border-color);
  }

  .department-content,
  .department-leader,
  .department-contact > div {
    color: var(--art-text-gray-700);
  }

  .responsibility-item {
    background: #409EFF;
    color: #ffffff;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
  }

  .responsibility-icon {
    opacity: 0.9;
  }

  .no-responsibilities {
    color: var(--art-text-gray-500);
  }

  .no-data-icon {
    opacity: 0.7;
  }

  .announcement-text {
    background: var(--art-bg-primary);
    color: var(--art-text-gray-700);
    border-color: var(--art-border-color);
  }

  .empty-state,
  .empty-schedule {
    color: var(--art-text-gray-600);
  }

  // Element Plus 组件深色模式
  .el-button {
    background: var(--art-main-bg-color);
    border-color: var(--art-border-color);
    color: var(--art-text-gray-800);

    &:hover {
      background: var(--art-gray-100);
      border-color: var(--art-gray-300);
    }

    &.el-button--primary {
      background: #409EFF;
      border-color: #409EFF;
      color: #ffffff;

      &:hover {
        background: #66b1ff;
        border-color: #66b1ff;
      }
    }
  }

  .el-checkbox {
    .el-checkbox__input {
      .el-checkbox__inner {
        background: var(--art-main-bg-color);
        border-color: var(--art-border-color);
      }
    }
  }

  .el-progress {
    .el-progress-bar__outer {
      background: var(--art-gray-200);
    }
  }

  .el-tag {
    background: var(--art-gray-100);
    border-color: var(--art-border-color);
    color: var(--art-text-gray-700);
  }

  .el-empty {
    .el-empty__description {
      color: var(--art-text-gray-600);
    }
  }

  // 滚动条深色模式
  .task-list::-webkit-scrollbar-track,
  .schedule-list::-webkit-scrollbar-track {
    background: var(--art-gray-100);
  }

  .task-list::-webkit-scrollbar-thumb,
  .schedule-list::-webkit-scrollbar-thumb {
    background: var(--art-gray-300);

    &:hover {
      background: var(--art-gray-400);
    }
  }

  // 对话框深色模式
  .el-dialog {
    background: var(--art-main-bg-color);
    border: 1px solid var(--art-border-color);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

    .el-dialog__header {
      background: var(--art-main-bg-color);
      border-bottom: 1px solid var(--art-border-color);
      
      .el-dialog__title {
        color: var(--art-text-gray-800);
      }
    }

    .el-dialog__body {
      background: var(--art-main-bg-color);
      color: var(--art-text-gray-700);
    }

    .el-dialog__footer {
      background: var(--art-main-bg-color);
      border-top: 1px solid var(--art-border-color);
    }
  }

  // 表单组件深色模式
  .el-form-item__label {
    color: var(--art-text-gray-700);
  }

  .el-input__wrapper {
    background: var(--art-main-bg-color);
    border-color: var(--art-border-color);
    box-shadow: 0 0 0 1px var(--art-border-color);

    &:hover {
      border-color: var(--art-gray-400);
    }

    &.is-focus {
      border-color: #409EFF;
      box-shadow: 0 0 0 1px #409EFF;
    }
  }

  .el-input__inner {
    background: var(--art-main-bg-color);
    color: var(--art-text-gray-800);
  }

  .el-select {
    .el-input__wrapper {
      background: var(--art-main-bg-color);
      border-color: var(--art-border-color);
    }
  }

  .el-select-dropdown {
    background: var(--art-main-bg-color);
    border: 1px solid var(--art-border-color);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

    .el-select-dropdown__item {
      color: var(--art-text-gray-700);

      &:hover {
        background: var(--art-gray-100);
      }

      &.is-selected {
        background: #409EFF;
        color: #ffffff;
      }
    }
  }

  // 时间选择器深色模式
  .el-time-picker {
    .el-input__wrapper {
      background: var(--art-main-bg-color);
      border-color: var(--art-border-color);
    }
  }

  .el-time-panel {
    background: var(--art-main-bg-color);
    border: 1px solid var(--art-border-color);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

    .el-time-spinner__list {
      background: var(--art-main-bg-color);
    }

    .el-time-spinner__item {
      color: var(--art-text-gray-700);

      &:hover {
        background: var(--art-gray-100);
      }

      &.is-active {
        background: #409EFF;
        color: #ffffff;
      }
    }
  }
}
</style>
