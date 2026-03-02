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
            <h3>{{ selectedDateTitle }}</h3>
            <div class="header-actions">
              <el-button type="primary" size="small" @click="handleAddTask">
                <el-icon><Plus /></el-icon>
                添加任务
              </el-button>
              <el-button type="primary" size="small" @click="goToWorkbench">
                <el-icon><Back /></el-icon>
                返回工作台
              </el-button>
            </div>
          </div>
          <ul class="task-list">
            <li v-if="todayTasks.length === 0" class="task-item no-task" style="color: #aaa; text-align: center; width: 100%;">{{ selectedDateEmptyText }}</li>
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
          <h3>智能添加任务</h3>
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
          <el-input v-model="eventForm.content" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="eventForm.type">
            <el-radio label="bg-primary">
              <span class="radio-label">普通</span>
            </el-radio>
            <el-radio label="bg-success">
              <span class="radio-label">重要</span>
            </el-radio>
            <el-radio label="bg-warning">
              <span class="radio-label radio-warning">提醒</span>
            </el-radio>
            <el-radio label="bg-danger">
              <span class="radio-label radio-danger">紧急</span>
            </el-radio>
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
// 智能日程管理页面 - 提供日历视图、任务管理、智能识别等功能
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchMeetings } from '@/api/meetings'
import dayjs from 'dayjs'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { Back, Plus } from '@element-plus/icons-vue'
import { taskService, eventEmitter, MEETING_EVENTS } from '@/services/taskService'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const userStore = useUserStore()

// 日历事件接口定义
interface CalendarEvent {
  date: string
  endDate?: string
  content: string
  type?: 'bg-primary' | 'bg-success' | 'bg-warning' | 'bg-danger'
  time?: string
  remindBefore?: number
  id?: number | string
  isMeeting?: boolean // 标识是否为会议
}

// 任务接口定义
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

// 任务类型选项
const eventTypes = [
  { label: '普通', value: 'bg-primary' },
  { label: '重要', value: 'bg-success' },
  { label: '提醒', value: 'bg-warning' },
  { label: '紧急', value: 'bg-danger' }
] as const

// 当前选中的日期
const currentDate = ref(new Date())
// 日历事件列表（示例数据，实际数据从后端加载）
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

// 所有任务列表
const allTasks = ref<TodayTask[]>([])
// 选中日期的字符串格式
const selectedDayStr = computed(() =>
  dayjs(currentDate.value).format('YYYY-MM-DD')
)
// 计算属性：获取选中日期的任务列表
const todayTasks = computed(() => {
  // 筛选选中日期的任务并排序
  const selectedDate = selectedDayStr.value
  const tasksOfDay = allTasks.value.filter(task => {
    if (!task.date) return false
    // 处理不同的日期格式：YYYY-MM-DD 或 YYYY-MM-DD HH:mm 或 YYYY-MM-DD HH:mm:ss 或 ISO格式
    let taskDateStr = String(task.date).trim()
    
    // 如果包含空格，只取日期部分
    if (taskDateStr.includes(' ')) {
      taskDateStr = taskDateStr.split(' ')[0]
    }
    // 如果包含T（ISO格式），只取日期部分
    if (taskDateStr.includes('T')) {
      taskDateStr = taskDateStr.split('T')[0]
    }
    // 确保格式为 YYYY-MM-DD（取前10个字符）
    taskDateStr = taskDateStr.slice(0, 10)
    
    // 使用 dayjs 进行日期比较，确保格式一致
    const taskDate = dayjs(taskDateStr).format('YYYY-MM-DD')
    const selectedDateFormatted = dayjs(selectedDate).format('YYYY-MM-DD')
    
    const matches = taskDate === selectedDateFormatted
    if (!matches && taskDateStr && selectedDate) {
      // 调试信息：只在开发环境输出
      if (process.env.NODE_ENV === 'development') {
        console.log('任务日期不匹配:', {
          taskId: task.id,
          taskContent: task.content,
          taskDateRaw: task.date,
          taskDateParsed: taskDate,
          selectedDate: selectedDateFormatted
        })
      }
    }
    
    return matches
  })
  return sortTasks([...tasksOfDay])
})

// 计算属性：根据选中日期显示标题（今日任务/XX月XX日任务）
const selectedDateTitle = computed(() => {
  const today = dayjs().format('YYYY-MM-DD')
  const selected = selectedDayStr.value
  if (selected === today) {
    return '今日任务'
  } else {
    const date = dayjs(selected)
    return `${date.format('M月D日')}任务`
  }
})

// 计算属性：根据选中日期显示空状态文本
const selectedDateEmptyText = computed(() => {
  const today = dayjs().format('YYYY-MM-DD')
  const selected = selectedDayStr.value
  if (selected === today) {
    return '今日暂无任务'
  } else {
    const date = dayjs(selected)
    return `${date.format('M月D日')}暂无任务`
  }
})
// 智能输入框内容
const smartInput = ref('')
// 提醒提前时间（分钟）
const remindBefore = ref(15)

// 弹窗相关状态
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
const editingMeetingId = ref<number | null>(null)
const isEditing = computed(() => editingTaskId.value !== null || editingMeetingId.value !== null)
const isEditingMeeting = computed(() => editingMeetingId.value !== null)

// 会议列表
const meetings = ref<any[]>([])

// 所有事件弹窗状态
const allEventsDialogVisible = ref(false)
const allEventsOfDay = ref<CalendarEvent[]>([])

// 同步任务数据到日历事件
function syncTasksToEvents() {
  // 只添加任务，不添加会议
  const taskEvents = allTasks.value
    .filter((task: any) => task && task.id != null) // 过滤掉没有ID的任务
    .map((task: any) => ({
    date: task.date,
    endDate: task.endDate || '',
    content: task.content,
      type: task.type || 'bg-primary',
      id: Number(task.id), // 确保ID是数字
      isMeeting: false
  }))
  // 不再添加会议到日历事件中
  events.value = taskEvents
}

// 从服务端刷新会议数据
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
  // 清理已通知的任务ID（页面刷新后重新开始）
  notifiedTaskIds.clear()
  
  // 确保 currentDate 初始化为今天的日期
  currentDate.value = new Date()
  
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
    console.log('已加载任务:', allTasks.value.length, '个')
    // 调试信息：显示所有任务的日期
    if (process.env.NODE_ENV === 'development') {
      console.log('所有任务的日期:', allTasks.value.map(t => ({ id: t.id, content: t.content, date: t.date })))
      console.log('当前选中的日期:', selectedDayStr.value)
      console.log('今天的日期:', dayjs().format('YYYY-MM-DD'))
    }
  } catch (e) {
    console.error('加载任务失败:', e)
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

// 计算属性：所有事件（包含任务和会议）
const allEvents = computed(() => {
  // 直接返回events.value，因为syncTasksToEvents()已经包含了会议数据
  return events.value
})

// 格式化日期显示（只显示日期数字）
const formatDate = (date: string) => date.split('-')[2]

// 格式化任务时间显示（处理全天任务）
const formatTaskTime = (task: TodayTask) => {
  if (!task.time || task.time === '待定') {
    return '全天'
  }
  return task.time
}

// 任务排序函数：按时间排序，全天任务排在前面
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

// 获取指定日期的所有事件
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
// 重置表单数据
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
  editingTaskId.value = null
  editingMeetingId.value = null
}
// 处理添加任务按钮点击
const handleAddTask = () => {
  // 使用当前选中的日期
  const selectedDate = selectedDayStr.value
  
  dialogTitle.value = '添加任务'
  // 设置默认时间为当前时间
  const defaultDateTime = `${selectedDate} ${dayjs().format('HH:mm')}`
  eventForm.value = {
    content: '',
    time: '',
    completed: false,
    id: '',
    date: defaultDateTime,
    type: 'bg-primary',
    endDate: '',
    remindBefore: remindBefore.value
  }
  editingTaskId.value = null
  editingMeetingId.value = null
  editingEventIndex.value = -1
  dialogVisible.value = true
}

// 处理日历单元格点击
const handleCellClick = (day: string) => {
  // 更新当前选中的日期，以便显示该日期的任务
  currentDate.value = new Date(day)
  
  dialogTitle.value = '添加任务'
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
  editingMeetingId.value = null
  editingEventIndex.value = -1
  dialogVisible.value = true
}
// 处理日历事件点击（编辑任务或会议）
const handleEventClick = (event: CalendarEvent) => {
  // 判断是会议还是任务
  if (event.isMeeting) {
  dialogTitle.value = '编辑会议'
    // 找到对应的会议对象（支持数字和字符串ID匹配）
    const meeting = meetings.value.find((m: any) => {
      const meetingId = Number(m.id)
      const eventId = Number(event.id)
      return !isNaN(meetingId) && !isNaN(eventId) && meetingId === eventId
    })
    if (meeting && meeting.id != null) {
      const meetingId = Number(meeting.id)
      if (!isNaN(meetingId) && meetingId > 0) {
  eventForm.value = {
          content: meeting.title || event.content,
          time: meeting.time ? dayjs(meeting.time).format('HH:mm') : '',
    completed: false,
          id: meetingId,
          date: meeting.time ? dayjs(meeting.time).format('YYYY-MM-DD HH:mm') : event.date,
          type: 'bg-success',
          endDate: '',
          remindBefore: 15
        }
        editingMeetingId.value = meetingId
        editingTaskId.value = null
  editingEventIndex.value = events.value.findIndex(
    (e) => e.date === event.date && e.content === event.content
  )
  dialogVisible.value = true
      } else {
        ElMessage.warning('会议ID无效')
      }
    } else {
      ElMessage.warning('无法找到对应的会议信息')
    }
  } else {
    dialogTitle.value = '编辑任务'
    // 找到对应的任务对象（支持数字和字符串ID匹配）
    const task = allTasks.value.find((t: any) => {
      const taskId = Number(t.id)
      const eventId = Number(event.id)
      return !isNaN(taskId) && !isNaN(eventId) && taskId === eventId
    })
    if (task && task.id != null) {
      const taskId = Number(task.id)
      if (!isNaN(taskId) && taskId > 0) {
        eventForm.value = {
          content: task.content,
          time: task.time || '',
          completed: task.completed || false,
          id: taskId,
          date: task.date ? `${task.date} ${task.time || ''}`.trim() : event.date,
          type: task.type || 'bg-primary',
          endDate: task.endDate || '',
          remindBefore: task.remindBefore || 15
        }
        editingTaskId.value = taskId
        editingMeetingId.value = null
        editingEventIndex.value = events.value.findIndex(
          (e) => e.date === event.date && e.content === event.content
        )
        dialogVisible.value = true
      } else {
        ElMessage.warning('任务ID无效')
      }
    } else {
      ElMessage.warning('无法找到对应的任务信息')
    }
  }
}
// 保存事件（添加或更新任务/会议）
const handleSaveEvent = async () => {
  if (!eventForm.value.content || !eventForm.value.date) return
  
  const token = localStorage.getItem('token')
  const headers = { 'Authorization': `Bearer ${token}` }
  
  if (isEditingMeeting.value && editingMeetingId.value) {
    // 更新会议
    const fullDateTime = eventForm.value.date
    const meetingData = {
      title: eventForm.value.content,
      time: fullDateTime,
      location: '',
      period: 'none',
      status: 'upcoming',
      participants: []
    }
    
    const success = await taskService.updateMeeting(editingMeetingId.value, meetingData)
    if (success) {
      await refreshMeetings()
      ElMessage.success('会议更新成功')
      dialogVisible.value = false
      resetForm()
    } else {
      ElMessage.error('会议更新失败')
    }
  } else if (editingTaskId.value) {
    // 更新任务
  const fullDateTime = eventForm.value.date
  const datePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[0] : fullDateTime
  const timePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[1] : '待定'
  
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
    dialogVisible.value = false
    resetForm()
  } else {
    // 添加任务（会议应该通过会议管理页面创建）
    const fullDateTime = eventForm.value.date
    const datePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[0] : fullDateTime
    const timePart = fullDateTime.includes(' ') ? fullDateTime.split(' ')[1] : '待定'
    
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
  dialogVisible.value = false
  resetForm()
  }
}
// 删除事件（任务或会议）
const handleDeleteEvent = async () => {
  if (!isEditing.value) {
    ElMessage.warning('请先选择要删除的项目')
    return
  }
  
  // 检查是否有有效的ID
  if (!editingTaskId.value && !editingMeetingId.value) {
    ElMessage.warning('无法获取要删除的项目ID')
    return
  }
  
  // 保存当前编辑状态
  const currentTaskId = editingTaskId.value
  const currentMeetingId = editingMeetingId.value
  const isMeeting = isEditingMeeting.value
  
  // 先关闭编辑对话框，确保确认对话框显示在最前面
  dialogVisible.value = false
  
  // 等待对话框关闭动画完成
  await new Promise(resolve => setTimeout(resolve, 300))
  
  try {
    const token = localStorage.getItem('token')
    const headers = { 'Authorization': `Bearer ${token}` }
    
    if (isMeeting && currentMeetingId) {
      // 删除会议
      await ElMessageBox.confirm('确定要删除该会议吗？', '删除会议', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        zIndex: 4000, // 设置更高的 z-index
        appendToBody: true // 确保添加到 body
      })
      
      const success = await taskService.deleteMeeting(currentMeetingId)
      if (success) {
        // 刷新会议列表
        await refreshMeetings()
        ElMessage.success('会议删除成功')
        // 最后重置表单
        resetForm()
      } else {
        ElMessage.error('会议删除失败')
      }
    } else if (currentTaskId) {
      // 删除任务
      await ElMessageBox.confirm('确定要删除该任务吗？', '删除任务', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        zIndex: 4000, // 设置更高的 z-index
        appendToBody: true // 确保添加到 body
      })
      
      // 确保ID是有效的数字
      const taskId = Number(currentTaskId)
      if (isNaN(taskId) || taskId <= 0) {
        ElMessage.error('无效的任务ID')
        return
      }
      
      const deleteRes = await axios.delete(`/api/today-tasks/${taskId}`, { headers })
      
      // 检查删除是否成功
      if (deleteRes.data && deleteRes.data.code === 0) {
        // 从本地数据中移除已删除的任务
        allTasks.value = allTasks.value.filter((t: any) => Number(t.id) !== taskId)
        // 同步更新事件列表
        syncTasksToEvents()
        ElMessage.success('任务删除成功')
      } else {
        // 如果删除失败，重新获取完整列表
      const res = await axios.get('/api/today-tasks', { headers })
      if (res.data && res.data.code === 0) {
        const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
        allTasks.value = sortTasks(tasks)
        syncTasksToEvents()
      }
      ElMessage.success('任务删除成功')
      }
      // 最后重置表单
      resetForm()
    } else {
      ElMessage.warning('无法确定要删除的项目类型')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('删除出错', e)
      ElMessage.error(`删除失败: ${e.message || '未知错误'}`)
    } else {
      // 如果用户取消，重新打开编辑对话框
      if (isMeeting && currentMeetingId) {
        editingMeetingId.value = currentMeetingId
        editingTaskId.value = null
      } else if (currentTaskId) {
        editingTaskId.value = currentTaskId
        editingMeetingId.value = null
      }
      dialogVisible.value = true
    }
  }
}
/**
 * 解析智能输入中的日期和时间
 */
function parseSmartInput(input: string): { date: string, time: string, content: string } {
  let date = dayjs().format('YYYY-MM-DD') // 默认今天
  let time = dayjs().format('HH:mm') // 默认当前时间
  let content = input.trim()
  
  const inputLower = input.toLowerCase()
  
  // 解析日期关键词
  let dateMatched = false
  let matchedDatePattern = ''
  
  // 优先匹配具体的日期格式：X月X日、X月X号、YYYY年X月X日等
  const datePatterns = [
    { pattern: /(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'full' },  // 2026年1月6日、2026年1月6号
    { pattern: /(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'month-day' },  // 1月6日、1月6号、3月15日
    { pattern: /(\d{1,2})\/(\d{1,2})/, type: 'slash' },  // 1/6、3/15（月/日格式）
    { pattern: /(\d{4})-(\d{1,2})-(\d{1,2})/, type: 'dash' },  // 2026-01-06
    { pattern: /(\d{4})\.(\d{1,2})\.(\d{1,2})/, type: 'dot' }  // 2026.01.06
  ]
  
  for (const { pattern, type } of datePatterns) {
    const match = pattern.exec(input)
    if (match) {
      matchedDatePattern = match[0]
      let year: number, month: number, day: number
      
      if (type === 'full') {
        // 2026年1月6日格式
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      } else if (type === 'month-day') {
        // 1月6日格式
        const currentYear = dayjs().year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        // 如果日期已过，可能是明年的日期
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(dayjs(), 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'slash') {
        // 1/6格式（月/日）
        const currentYear = dayjs().year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        // 如果日期已过，可能是明年的日期
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(dayjs(), 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'dash' || type === 'dot') {
        // 2026-01-06 或 2026.01.06格式
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      }
      
      // 验证日期有效性
      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        try {
          const parsedDate = dayjs(`${year}-${month}-${day}`)
          if (parsedDate.isValid()) {
            date = parsedDate.format('YYYY-MM-DD')
            dateMatched = true
            break
          }
        } catch (e) {
          console.error('日期解析失败:', e)
        }
      }
    }
  }
  
  // 如果没有匹配到具体日期，再匹配相对日期
  if (!dateMatched) {
    if (inputLower.includes('明天') || inputLower.includes('明日')) {
      date = dayjs().add(1, 'day').format('YYYY-MM-DD')
      dateMatched = true
    } else if (inputLower.includes('后天') || inputLower.includes('后日')) {
      date = dayjs().add(2, 'day').format('YYYY-MM-DD')
      dateMatched = true
    } else if (inputLower.includes('大后天')) {
      date = dayjs().add(3, 'day').format('YYYY-MM-DD')
      dateMatched = true
    } else if (inputLower.includes('今天') || inputLower.includes('今日')) {
      date = dayjs().format('YYYY-MM-DD')
      dateMatched = true
    } else if (inputLower.includes('昨天') || inputLower.includes('昨日')) {
      date = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
      dateMatched = true
    }
  }
  
  // 解析时间
  let timeMatched = false
  let matchedTimePattern = ''
  // 匹配 "下午3点"、"下午三点"、"3点"、"15:00" 等格式
  const timePatterns = [
    /(?:上午|早上|早晨|早)\s*(\d{1,2})(?:点|:)?(\d{2})?/,
    /(?:下午|晚上|傍晚|晚)\s*(\d{1,2})(?:点|:)?(\d{2})?/,
    /(\d{1,2}):(\d{2})/,
    /(\d{1,2})点(\d{2})?/,
    /(\d{1,2})时(\d{2})?/
  ]
  
  for (const pattern of timePatterns) {
    const match = input.match(pattern)
    if (match) {
      let hour = parseInt(match[1])
      let minute = match[2] ? parseInt(match[2]) : 0
      
      // 处理下午/晚上时间
      if (inputLower.includes('下午') || inputLower.includes('晚上') || inputLower.includes('傍晚') || inputLower.includes('晚')) {
        if (hour < 12) {
          hour += 12
        }
      }
      
      // 处理上午时间
      if (inputLower.includes('上午') || inputLower.includes('早上') || inputLower.includes('早晨') || inputLower.includes('早')) {
        if (hour === 12) {
          hour = 0
        }
      }
      
      time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      matchedTimePattern = match[0]
      timeMatched = true
      break
    }
  }
  
  // 如果没有匹配到具体时间，但有"下午"、"晚上"等关键词，设置默认时间
  if (!timeMatched) {
    if (inputLower.includes('下午')) {
      time = '14:00' // 默认下午2点
      timeMatched = true
    } else if (inputLower.includes('晚上') || inputLower.includes('傍晚') || inputLower.includes('晚')) {
      time = '19:00' // 默认晚上7点
      timeMatched = true
    } else if (inputLower.includes('上午') || inputLower.includes('早上') || inputLower.includes('早晨') || inputLower.includes('早')) {
      time = '09:00' // 默认上午9点
      timeMatched = true
    }
  }
  
  // 清理内容：移除日期和时间相关的关键词
  let cleanContent = content
  
  // 移除日期关键词和模式
  if (dateMatched) {
    // 移除匹配到的日期模式
    if (matchedDatePattern) {
      cleanContent = cleanContent.replace(new RegExp(matchedDatePattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '')
    }
    // 移除相对日期关键词
    cleanContent = cleanContent
      .replace(/明天|明日/g, '')
      .replace(/后天|后日/g, '')
      .replace(/大后天/g, '')
      .replace(/今天|今日/g, '')
      .replace(/昨天|昨日/g, '')
    // 移除年月日关键词
    cleanContent = cleanContent
      .replace(/\d{4}年/g, '')
      .replace(/\d{1,2}月/g, '')
      .replace(/\d{1,2}[日号]/g, '')
  }
  
  // 移除时间关键词和模式
  if (timeMatched && matchedTimePattern) {
    cleanContent = cleanContent.replace(new RegExp(matchedTimePattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '')
  }
  
  // 移除其他时间相关关键词
  cleanContent = cleanContent
    .replace(/上午|早上|早晨|早/g, '')
    .replace(/下午|晚上|傍晚|晚/g, '')
    .replace(/\d{1,2}[：:]?\d{0,2}\s*(点|时)/g, '')
    .replace(/\d{1,2}[：:]?\d{2}/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  
  // 如果清理后内容为空，使用默认值
  if (!cleanContent || cleanContent.length === 0) {
    cleanContent = '新任务'
  }
  
  return { date, time, content: cleanContent }
}

// 智能添加会议：解析自然语言输入，自动识别日期和时间
async function handleSmartAdd() {
  if (!smartInput.value) return
  try {
    // 解析输入文本，提取日期和时间
    const { date, time, content } = parseSmartInput(smartInput.value)
    
    console.log('智能解析结果:', { date, time, content, original: smartInput.value })
    
    // 获取当前用户信息作为主持人
    const userInfo = userStore.info
    const hostName = userInfo.realName || userInfo.userName || userInfo.nickName || '我'
    
    // 将日期和时间组合成完整的日期时间字符串（ISO格式）
    const fullDateTime = `${date} ${time}:00`
    const isoDateTime = dayjs(fullDateTime).format('YYYY-MM-DDTHH:mm:ss')
    
    // 创建会议而不是任务
    const meetingData = {
      title: content,
      host: hostName,
      time: isoDateTime,
      location: '',
      period: 'none',
      status: 'upcoming',
      participants: []
    }
    
    const success = await taskService.createMeeting(meetingData)
    if (success) {
      // 刷新会议列表
      await refreshMeetings()
      smartInput.value = ''
      ElMessage.success('会议添加成功')
    } else {
      ElMessage.error('会议添加失败')
    }
  } catch (e: any) {
    console.error('智能添加失败:', e)
    ElMessage.error('添加失败: ' + (e.message || '未知错误'))
  }
}
// 显示指定日期的所有事件弹窗
function showAllEvents(day: string) {
  allEventsOfDay.value = getEvents(day)
  allEventsDialogVisible.value = true
}
// 处理删除任务
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
    const deleteRes = await axios.delete(`/api/today-tasks/${task.id}`, { headers })
    
    // 检查删除是否成功
    if (deleteRes.data && deleteRes.data.code === 0) {
      // 从本地数据中移除已删除的任务
      allTasks.value = allTasks.value.filter((t: any) => Number(t.id) !== Number(task.id))
      // 同步更新事件列表
      syncTasksToEvents()
      ElMessage.success('任务删除成功')
    } else {
      // 如果删除失败或响应格式不同，重新获取完整列表
    const res = await axios.get('/api/today-tasks', { headers })
    if (res.data && res.data.code === 0) {
      const tasks = res.data.tasks.map((t: any) => ({ ...t, type: t.type || 'bg-primary', remindBefore: typeof t.remindBefore === 'number' ? t.remindBefore : 15 }))
      allTasks.value = sortTasks(tasks)
      syncTasksToEvents()
    }
    ElMessage.success('任务删除成功')
    }
  } catch (e) {
    // 取消操作
  }
}
// 处理任务完成状态切换
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
      // 强制刷新任务列表（获取所有任务，不只是今天的）
      const tasks = await taskService.getAllTasks()
      allTasks.value = sortTasks(tasks.map((t: any) => ({ 
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
// 处理点击任务名称（打开编辑对话框）
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

// 任务提醒功能：定时检查任务时间，发送提醒通知
let notifiedTaskIds: Set<string | number> = new Set()
setInterval(() => {
  const now = new Date()
  const today = dayjs().format('YYYY-MM-DD')
  
  // 检查所有未完成的任务，而不仅仅是当前选中日期的任务
  allTasks.value.forEach(task => {
    const t = task as TodayTask
    // 跳过已完成的任务
    if (t.completed) return
    // 跳过没有时间的任务
    if (!t.time || t.time === '待定' || t.time === '全天') return
    
    // 获取任务日期（提取日期部分）
    let taskDateStr = (t.date || '').trim()
    if (taskDateStr.includes(' ')) {
      taskDateStr = taskDateStr.split(' ')[0]
    }
    if (taskDateStr.includes('T')) {
      taskDateStr = taskDateStr.split('T')[0]
    }
    taskDateStr = taskDateStr.slice(0, 10)
    
    // 只提醒今天和未来的任务
    if (taskDateStr < today) return
    
    // 获取提醒时间设置
    let remindBefore = 15 // 默认15分钟
    if (typeof t.remindBefore === 'number') {
      remindBefore = t.remindBefore
    }
    
    // 构建任务日期时间
    let taskDateTime: Date
    try {
      // 处理日期格式：YYYY-MM-DD 或 YYYY-MM-DD HH:mm
      if (t.date.includes(' ')) {
        // 如果date已经包含时间，直接使用
        taskDateTime = dayjs(t.date).toDate()
      } else {
        // 如果date只有日期，需要组合time
        const timeStr = t.time.includes(':') ? t.time : `${t.time}:00`
        taskDateTime = dayjs(`${taskDateStr} ${timeStr}`).toDate()
      }
    } catch (e) {
      console.error('解析任务日期时间失败:', t.date, t.time, e)
      return
    }
    
    // 计算提醒时间
    const remindTime = dayjs(taskDateTime).subtract(remindBefore, 'minute').toDate()
    
    // 检查是否在提醒时间窗口内（5分钟窗口，确保不会错过）
    const timeDiff = now.getTime() - remindTime.getTime()
    if (
      timeDiff >= 0 &&
      timeDiff <= 5 * 60 * 1000 && // 5分钟窗口
      !notifiedTaskIds.has(t.id)
    ) {
      // 计算距离任务开始还有多长时间
      const minutesLeft = Math.floor((taskDateTime.getTime() - now.getTime()) / (60 * 1000))
      let timeText = ''
      if (minutesLeft <= 0) {
        timeText = '即将开始'
      } else if (minutesLeft < 60) {
        timeText = `${minutesLeft}分钟后开始`
      } else {
        const hours = Math.floor(minutesLeft / 60)
        const mins = minutesLeft % 60
        timeText = mins > 0 ? `${hours}小时${mins}分钟后开始` : `${hours}小时后开始`
      }
      
      ElNotification({
        title: '任务提醒',
        message: `任务「${t.content}」${timeText}！`,
        type: 'warning',
        duration: 5000, // 显示5秒
        position: 'top-right'
      })
      notifiedTaskIds.add(t.id)
    }
  })
}, 60 * 1000) // 每分钟检查一次

// 跳转到工作台页面
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
          .header-actions {
            display: flex;
            gap: 8px;
            align-items: center;
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

// 单选按钮标签颜色
:deep(.el-radio) {
  .radio-label {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    transition: all 0.3s;
    
    &.radio-warning {
      background: var(--el-color-warning-light-9);
      color: var(--el-color-warning);
      font-weight: 500;
    }
    
    &.radio-danger {
      background: var(--el-color-error-light-9);
      color: var(--el-color-error);
      font-weight: 500;
    }
  }
  
  // 选中状态时保持颜色
  &.is-checked {
    .radio-warning {
      background: var(--el-color-warning-light-8);
      color: var(--el-color-warning);
    }
    
    .radio-danger {
      background: var(--el-color-error-light-8);
      color: var(--el-color-error);
    }
  }
}
</style> 