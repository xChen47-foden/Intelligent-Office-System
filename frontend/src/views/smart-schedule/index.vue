<template>
  <div class="smart-schedule-page">
    <div class="schedule-layout">
      <!-- 日历视图 -->
      <div class="calendar-section">
        <el-calendar v-model="currentDate">
          <template #date-cell="{ data }">
            <div class="calendar-cell" :class="{ 'is-selected': data.isSelected }" @click="handleCellClick(data.day)">
              <p class="calendar-date">{{ formatDate(data.day) }}</p>
              <div class="calendar-events">
                <div
                  v-for="(event, i) in getEvents(data.day).slice(0, 2)"
                  :key="`${event.date}-${event.content}`"
                  class="calendar-event"
                  @click.stop="handleEventClick(event)"
                  :title="event.content"
                >
                  <div class="event-tag" :class="[`${event.type || 'bg-primary'}`]">
                    {{ event.content }}
                  </div>
                </div>
                <div
                  v-if="getEvents(data.day).length >= 3"
                  class="calendar-event more"
                  @click.stop="showAllEvents(data.day)"
                >
                  更多...
                </div>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>
      <!-- 右侧智能区块 -->
      <div class="right-section">
        <div class="section-block">
          <div class="section-header">
            <h3>今日任务</h3>
            <el-button type="primary" size="small" @click="goToWorkbench">
              <el-icon><Back /></el-icon>
              返回工作台
            </el-button>
          </div>
          <ul class="task-list">
            <li v-if="todayTasks.length === 0" class="task-item no-task" style="color: #aaa; text-align: center; width: 100%;">今日暂无任务</li>
            <li v-for="(task, idx) in todayTasks" :key="task.id" class="task-item">
              <el-checkbox v-model="task.completed" @change="() => handleCheckTask(task)" />
              <span
                class="task-content clickable event-tag"
                :class="task.type || 'bg-primary'"
                @click="() => handleClickTaskName(task)"
              >
                {{ task.content }}
              </span>
              <span class="task-time">{{ formatTaskTime(task) }}</span>
              <el-button
                type="text"
                icon="el-icon-delete"
                @click.stop="handleDeleteTask(idx)"
                style="color: #f56c6c; margin-left: 8px;"
              />
            </li>
          </ul>
        </div>
        <div class="section-block">
          <h3>智能添加会议</h3>
          <el-input
            v-model="smartInput"
            placeholder="如：明天下午3点开会，或粘贴会议/任务描述..."
            @keyup.enter="handleSmartAdd"
            clearable
          />
          <el-button type="primary" style="margin-top: 8px;" @click="handleSmartAdd">智能识别并添加</el-button>
        </div>
        <div class="section-block">
          <h3>提醒设置</h3>
          <el-select v-model="remindBefore" placeholder="请选择提醒时间">
            <el-option label="准时提醒" :value="0" />
            <el-option label="提前5分钟" :value="5" />
            <el-option label="提前15分钟" :value="15" />
            <el-option label="提前30分钟" :value="30" />
            <el-option label="提前1小时" :value="60" />
          </el-select>
        </div>
      </div>
    </div>
    <!-- 事件编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" @closed="resetForm">
      <el-form :model="eventForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="eventForm.content" placeholder="请输入会议标题" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="eventForm.type">
            <el-radio label="bg-primary">普通</el-radio>
            <el-radio label="bg-success">重要</el-radio>
            <el-radio label="bg-warning">提醒</el-radio>
            <el-radio label="bg-danger">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="eventForm.date"
            type="datetime"
            placeholder="选择日期和时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="eventForm.endDate"
            type="datetime"
            placeholder="选择结束日期和时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm"
          />
        </el-form-item>
        <el-form-item label="提醒">
          <el-select v-model="eventForm.remindBefore" placeholder="请选择提醒时间">
            <el-option label="准时提醒" :value="0" />
            <el-option label="提前5分钟" :value="5" />
            <el-option label="提前15分钟" :value="15" />
            <el-option label="提前30分钟" :value="30" />
            <el-option label="提前1小时" :value="60" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button v-if="isEditing" type="danger" @click="handleDeleteEvent">删除</el-button>
          <el-button type="primary" @click="handleSaveEvent">{{ isEditing ? '更新' : '添加' }}</el-button>
        </span>
      </template>
    </el-dialog>
    <el-dialog v-model="allEventsDialogVisible" title="全部会议" width="400px">
      <ul>
        <li v-for="event in allEventsOfDay" :key="event.content">
          <span :class="['event-tag', event.type || 'bg-primary']">{{ event.content }}</span>
        </li>
      </ul>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchMeetings } from '@/api/meetings'
import dayjs from 'dayjs'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { Back } from '@element-plus/icons-vue'
import { taskService, eventEmitter, MEETING_EVENTS } from '@/services/taskService'

const router = useRouter()

interface CalendarEvent {
  date: string
  endDate?: string
  content: string
  type?: 'bg-primary' | 'bg-success' | 'bg-warning' | 'bg-danger'
  time?: string
  remindBefore?: number
}

interface TodayTask {
  content: string
  time: string
  completed: boolean
  id: number | string
  date: string
  type?: 'bg-primary' | 'bg-success' | 'bg-warning' | 'bg-danger'
  endDate?: string
  remindBefore: number
}

const eventTypes = [
  { label: '普通', value: 'bg-primary' },
  { label: '重要', value: 'bg-success' },
  { label: '提醒', value: 'bg-warning' },
  { label: '紧急', value: 'bg-danger' }
] as const

const currentDate = ref(new Date())
const events = ref<CalendarEvent[]>([
  { date: '2025-02-01', content: '产品需求评审', type: 'bg-primary' },
  { date: '2025-02-03', endDate: '2025-02-05', content: '项目周报会议', type: 'bg-primary' },
  { date: '2025-02-10', content: '瑜伽课程', type: 'bg-success' },
  { date: '2025-02-15', content: '团队建设活动', type: 'bg-primary' },
  { date: '2025-02-20', content: '健身训练', type: 'bg-success' },
  { date: '2025-02-20', content: '代码评审', type: 'bg-danger' },
  { date: '2025-02-20', content: '团队午餐', type: 'bg-primary' },
  { date: '2025-02-20', content: '项目进度汇报', type: 'bg-warning' },
  { date: '2025-02-28', content: '月度总结会', type: 'bg-warning' }
])

const allTasks = ref<TodayTask[]>([])
const selectedDayStr = computed(() =>
  dayjs(currentDate.value).format('YYYY-MM-DD')
)
const todayTasks = computed(() => {
  // 筛选当日任务并排序
  const tasksOfDay = allTasks.value.filter(task => (task.date || '').slice(0, 10) === selectedDayStr.value)
  return sortTasks([...tasksOfDay])
})
const smartInput = ref('')
const remindBefore = ref(15)

// 弹窗相关
const dialogVisible = ref(false)
const dialogTitle = ref('添加会议')
const editingEventIndex = ref<number>(-1)
const eventForm = ref<TodayTask>({
  content: '',
  time: '',
  completed: false,
  id: '',
  date: '',
  type: 'bg-primary',
  endDate: '',
  remindBefore: 15
})
const editingTaskId = ref<number | null>(null)
const isEditing = computed(() => editingTaskId.value !== null)

const meetings = ref<any[]>([])

const allEventsDialogVisible = ref(false)
const allEventsOfDay = ref<CalendarEvent[]>([])

function syncTasksToEvents() {
  const taskEvents = allTasks.value.map((task: any) => ({
    date: task.date,
    endDate: task.endDate || '',
    content: task.content,
    type: task.type || 'bg-primary'
  }))
  const meetingEvents = meetings.value.map((m: any) => ({
    date: m.time ? dayjs(m.time).format('YYYY-MM-DD') : '',
    endDate: '',
    content: m.title,
    type: 'bg-success'
  }))
  events.value = [...taskEvents, ...meetingEvents]
}

// 刷新会议数据
const refreshMeetings = async () => {
  try {
    const allMeetings = await taskService.getAllMeetings()
    meetings.value = allMeetings
    syncTasksToEvents()
  } catch (e) {
    meetings.value = []
    syncTasksToEvents()
  }
}

// 页面初始化
onMounted(async () => {
  // 获取今日任务
  try {
    const tasksData = await taskService.getAllTasks()
    const tasks = tasksData.map((t: any) => ({ 
      ...t, 
      type: t.type || 'bg-primary', 
      remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 
    }))
    allTasks.value = sortTasks(tasks)
    syncTasksToEvents()
  } catch (e) {
    allTasks.value = []
    syncTasksToEvents()
  }
  // 获取会议数据
  await refreshMeetings()
  
  // 监听会议数据变更事件
  eventEmitter.on(MEETING_EVENTS.MEETING_CREATED, () => {
    refreshMeetings()
  })
  eventEmitter.on(MEETING_EVENTS.MEETING_UPDATED, () => {
    refreshMeetings()
  })
  eventEmitter.on(MEETING_EVENTS.MEETING_DELETED, () => {
    refreshMeetings()
  })
})

// 组件卸载时清理事件监听
onUnmounted(() => {
  eventEmitter.off(MEETING_EVENTS.MEETING_CREATED, refreshMeetings)
  eventEmitter.off(MEETING_EVENTS.MEETING_UPDATED, refreshMeetings)
  eventEmitter.off(MEETING_EVENTS.MEETING_DELETED, refreshMeetings)
})

// 监听页面可见性变化，当页面重新激活时刷新会议数据
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    refreshMeetings()
  }
})

const allEvents = computed(() => {
  // 直接返回events.value，因为syncTasksToEvents()已经包含了会议数据
  return events.value
})

const formatDate = (date: string) => date.split('-')[2]

// 格式化任务时间显示
const formatTaskTime = (task: TodayTask) => {
  if (!task.time || task.time === '待定') {
    return '全天'
  }
  return task.time
}

// 任务排序函数
const sortTasks = (tasks: TodayTask[]) => {
  return tasks.sort((a, b) => {
    const timeA = a.time || '全天'
    const timeB = b.time || '全天'
    
    // 如果都是全天任务，按创建顺序（ID）排列
    if ((timeA === '全天' || timeA === '待定') && (timeB === '全天' || timeB === '待定')) {
      return (a.id as number) - (b.id as number)
    }
    
    // 全天任务排在前面
    if (timeA === '全天' || timeA === '待定') return -1
    if (timeB === '全天' || timeB === '待定') return 1
    
    // 都有具体时间的任务按时间排序
    return timeA.localeCompare(timeB)
  })
}

const getEvents = (day: string) => {
  const result = (allEvents.value as CalendarEvent[]).filter((event) => {
    const eventDate = new Date(event.date)
    const currentDate = new Date(day)
    const endDate = event.endDate ? new Date(event.endDate) : new Date(event.date)
    return currentDate >= eventDate && currentDate <= endDate
  })
  console.log('getEvents', day, result)
  return result
}
const resetForm = () => {
  eventForm.value = {
    content: '',
    time: '',
    completed: false,
    id: '',
    date: '',
    type: 'bg-primary',
    endDate: '',
    remindBefore: 15
  }
  editingEventIndex.value = -1
}
const handleCellClick = (day: string) => {
  dialogTitle.value = '添加会议'
  // 设置默认时间为当前时间
  const defaultDateTime = `${day} ${dayjs().format('HH:mm')}`
  eventForm.value = {
    content: '',
    time: '',
    completed: false,
    id: '',
    date: defaultDateTime,
    type: 'bg-primary',
    endDate: '',
    remindBefore: 15
  }
  editingTaskId.value = null
  editingEventIndex.value = -1
  dialogVisible.value = true
}
const handleEventClick = (event: CalendarEvent) => {
  dialogTitle.value = '编辑会议'
  eventForm.value = {
    content: event.content,
    time: event.time || '',
    completed: false,
    id: '',
    date: event.date,
    type: event.type || 'bg-primary',
    endDate: event.endDate || '',
    remindBefore: event.remindBefore || 15
  }
  editingEventIndex.value = events.value.findIndex(
    (e) => e.date === event.date && e.content === event.content
  )
  dialogVisible.value = true
}
const handleSaveEvent = async () => {
  if (!eventForm.value.content || !eventForm.value.date) return
  
  // 从完整的日期时间字符串中提取日期和时间部分
  const fullDateTime = eventForm.value.date
  const datePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[0] : fullDateTime
  const timePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[1] : '待定'
  
  const token = localStorage.getItem('token')
  const headers = { 'Authorization': `Bearer ${token}` }
  
  if (editingTaskId.value) {
    await axios.put(`/api/today-tasks/${editingTaskId.value}`, {
      content: eventForm.value.content,
      time: timePart,
      completed: false,
      date: datePart,
      endDate: eventForm.value.endDate || '',
      type: eventForm.value.type || 'bg-primary',
      remindBefore: eventForm.value.remindBefore
    }, { headers })
    const res = await axios.get('/api/today-tasks', { headers })
    if (res.data && res.data.code === 0) {
      const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
      allTasks.value = sortTasks(tasks)
      syncTasksToEvents()
    }
    ElMessage.success('任务更新成功')
  } else {
    await axios.post('/api/today-tasks', {
      content: eventForm.value.content,
      time: timePart,
      completed: false,
      date: datePart,
      endDate: eventForm.value.endDate || '',
      type: eventForm.value.type || 'bg-primary',
      remindBefore: eventForm.value.remindBefore
    }, { headers })
    const res = await axios.get('/api/today-tasks', { headers })
    if (res.data && res.data.code === 0) {
      const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
      allTasks.value = sortTasks(tasks)
      syncTasksToEvents()
    }
    ElMessage.success('任务添加成功')
  }
  dialogVisible.value = false
  resetForm()
}
const handleDeleteEvent = async () => {
  if (isEditing.value && editingTaskId.value) {
    try {
      await ElMessageBox.confirm('确定要删除该任务吗？', '删除任务', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }
      await axios.delete(`/api/today-tasks/${editingTaskId.value}`, { headers })
      // 先关闭弹窗
      dialogVisible.value = false
      // 再刷新任务列表
      const res = await axios.get('/api/today-tasks', { headers })
      if (res.data && res.data.code === 0) {
        const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
        allTasks.value = sortTasks(tasks)
        syncTasksToEvents()
      }
      ElMessage.success('任务删除成功')
      // 最后重置表单
      resetForm()
    } catch (e) {
      console.error('删除任务出错', e)
    }
  }
}
// 智能添加日程（模拟，后续可对接AI）
async function handleSmartAdd() {
  if (!smartInput.value) return
  try {
    const today = dayjs().format('YYYY-MM-DD')
    // 使用当前时间作为默认时间
    const currentTime = dayjs().format('HH:mm')
    const token = localStorage.getItem('token')
    const headers = { 'Authorization': `Bearer ${token}` }
    const res = await axios.post('/api/today-tasks', {
      content: smartInput.value,
      time: currentTime,
      completed: false,
      date: today,
      endDate: '',
      remindBefore: 15
    }, { headers })
    if (res.data && res.data.code === 0) {
      const newTask = { ...res.data.task, type: 'bg-primary', remindBefore: 15 }
      allTasks.value = sortTasks([...allTasks.value, newTask])
      events.value.push({ ...res.data.task, remindBefore: 15 })
      smartInput.value = ''
      syncTasksToEvents()
    }
  } catch (e) {
    // 可加错误提示
  }
}
function showAllEvents(day: string) {
  allEventsOfDay.value = getEvents(day)
  allEventsDialogVisible.value = true
}
async function handleDeleteTask(idx: number) {
  const task = todayTasks.value[idx]
  console.log('[删除按钮] idx:', idx, task)
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '删除任务', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const token = localStorage.getItem('token')
    const headers = { 'Authorization': `Bearer ${token}` }
    await axios.delete(`/api/today-tasks/${task.id}`, { headers })
    const res = await axios.get('/api/today-tasks', { headers })
    if (res.data && res.data.code === 0) {
      const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
      allTasks.value = sortTasks(tasks)
      syncTasksToEvents()
    }
    ElMessage.success('任务删除成功')
  } catch (e) {
    // 取消操作
  }
}
async function handleCheckTask(task: TodayTask) {
  // 新状态（用户点击后的状态）
  const newCompleted = task.completed
  // 旧状态
  const oldCompleted = !newCompleted
  // 立即恢复为旧状态，等待用户确认
  task.completed = oldCompleted
  try {
    await ElMessageBox.confirm(
      newCompleted ? '确定要将该任务标记为已完成吗？' : '确定要将该任务标记为未完成吗？',
      newCompleted ? '确认完成任务' : '确认未完成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    // 用户确认后才切换状态并请求后端
    const taskId = typeof task.id === 'string' ? parseInt(task.id) : task.id
    const success = await taskService.updateTaskStatus(taskId, newCompleted)
    if (success) {
      // 强制刷新任务列表
      const tasks = await taskService.getAllTasks()
      const today = new Date().toISOString().split('T')[0]
      const todayTasksData = tasks.filter((t: any) => t.date === today)
      allTasks.value = sortTasks(todayTasksData.map((t: any) => ({ 
        ...t, 
        type: t.type || 'bg-primary', 
        remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 
      })))
      syncTasksToEvents()
      ElMessage.success(newCompleted ? '任务已完成' : '任务已设为未完成')
    } else {
      ElMessage.error('更新任务状态失败')
      // 恢复原状态
      task.completed = oldCompleted
    }
  } catch (e) {
    // 取消操作，状态保持不变
    if (e !== 'cancel') {
      ElMessage.error('更新任务状态失败')
      task.completed = oldCompleted
    }
  }
}
const handleClickTaskName = (task: TodayTask) => {
  dialogTitle.value = '编辑会议'
  
  // 将分离的日期和时间重新组合成完整的日期时间字符串
  let fullDateTime = task.date
  if (task.time && task.time !== '待定') {
    fullDateTime = `${task.date} ${task.time}`
  }
  
  eventForm.value = {
    content: task.content,
    time: task.time || '',
    completed: task.completed,
    id: task.id,
    date: fullDateTime,
    type: task.type || 'bg-primary',
    endDate: task.endDate || '',
    remindBefore: typeof task.remindBefore === 'number' ? task.remindBefore : 15
  }
  editingTaskId.value = typeof task.id === 'number' ? task.id : parseInt(task.id as string)
  editingEventIndex.value = -1
  dialogVisible.value = true
}

let notifiedTaskIds: Set<string | number> = new Set()
setInterval(() => {
  const now = new Date()
  todayTasks.value.forEach(task => {
    const t = task as TodayTask
    if (t.completed) return
    if (!t.time) return
    let remindBefore = 15
    if (typeof t.remindBefore === 'number') remindBefore = t.remindBefore
    if (eventForm.value && eventForm.value.content === t.content && typeof eventForm.value.remindBefore === 'number') {
      remindBefore = eventForm.value.remindBefore
    }
    const taskDateTime = new Date(`${t.date} ${t.time}`)
    const remindTime = new Date(taskDateTime.getTime() - remindBefore * 60 * 1000)
    if (
      now >= remindTime &&
      now < new Date(remindTime.getTime() + 60 * 1000) &&
      !notifiedTaskIds.has(t.id)
    ) {
      ElNotification({
        title: '任务提醒',
        message: `任务「${t.content}」即将开始！`,
        type: 'warning'
      })
      notifiedTaskIds.add(t.id)
    }
  })
}, 60 * 1000)

function goToWorkbench() {
  router.push('/workbench')
}
</script>

<style scoped lang="scss">
.smart-schedule-page {
  padding: 24px;
  .schedule-layout {
    display: flex;
    gap: 32px;
    align-items: flex-start;
    .calendar-section {
      flex: 1.2;
      min-width: 420px;
      .calendar-cell {
        min-height: 360px;
        max-height: 420px;
        overflow: hidden;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        .calendar-date {
          position: absolute;
          top: 6px;
          right: 10px;
          font-size: 14px;
          z-index: 10;
          background: transparent;
          pointer-events: none;
        }
        .calendar-events {
          max-height: 180px;
          overflow: hidden;
          position: relative;
          width: 100%;
          padding-bottom: 18px;
          margin-top: 24px;
        }
        .calendar-event {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          width: 100%;
        }
        .calendar-event.more {
          position: absolute;
          left: 0;
          bottom: 2px;
          width: 100%;
          background: var(--el-color-primary-light-9);
          color: #409eff;
          font-size: 12px;
          text-align: left;
          z-index: 10;
          line-height: 16px;
          padding-left: 2px;
        }
        .event-tag {
          min-width: 100px;
          padding: 6px 12px;
          overflow: hidden;
          font-size: 13px;
          font-weight: 500;
          line-height: 24px;
          text-overflow: ellipsis;
          white-space: nowrap;
          border-radius: 4px;
          &.bg-primary { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
          &.bg-success { background: var(--el-color-success-light-9); color: var(--el-color-success); }
          &.bg-warning { background: var(--el-color-warning-light-9); color: var(--el-color-warning); }
          &.bg-danger { background: var(--el-color-error-light-9); color: var(--el-color-error); }
        }
      }
    }
    .right-section {
      flex: 1;
      min-width: 320px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      .section-block {
        background: var(--art-main-bg-color);
        border-radius: 8px;
        padding: 18px 20px 12px 20px;
        box-shadow: 0 2px 8px 0 rgb(0 0 0 / 3%);
        h3 {
          font-size: 16px;
          font-weight: 500;
          margin-bottom: 12px;
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          h3 {
            margin-bottom: 0;
          }
        }
        .task-list {
          list-style: none;
          padding: 0;
          margin: 0;
          .task-item {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 6px 0;
            border-bottom: 1px solid var(--el-border-color);
            &:last-child {
              border-bottom: none;
            }
            .el-checkbox {
              flex: none;
              margin-right: 12px;
            }
            .task-content {
              flex: 1;
              text-align: left;
              margin-right: 12px;
              min-width: 0;
              word-break: break-all;
            }
            .task-time {
              margin-left: 12px;
              color: var(--el-color-info);
              font-size: 12px;
              white-space: nowrap;
            }
          }
        }
      }
    }
  }
}
:deep(.el-calendar__body) {
  height: auto !important;
  min-height: unset !important;
  max-height: unset !important;
}
:deep(.el-calendar-table) {
  height: auto !important;
  min-height: unset !important;
  max-height: unset !important;
  table-layout: fixed !important;
}
:deep(.el-calendar-table td) {
  height: 120px !important;
  min-height: 120px !important;
  max-height: 120px !important;
  padding: 0 !important;
}
:deep(.el-calendar-table .el-calendar-day) {
  height: 120px !important;
  min-height: 120px !important;
  max-height: 120px !important;
  box-sizing: border-box;
  vertical-align: top;
  padding: 0 !important;
}
.task-content.clickable {
  cursor: pointer;
  color: var(--el-color-primary);
  text-decoration: underline;
}
.type-primary { color: var(--el-color-primary); }
.type-success { color: var(--el-color-success); }
.type-warning { color: var(--el-color-warning); }
.type-danger { color: var(--el-color-error); }
</style> 