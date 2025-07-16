import api from '@/utils/http'

// 会议数据变更事件
export const MEETING_EVENTS = {
  MEETING_CREATED: 'meeting:created',
  MEETING_UPDATED: 'meeting:updated',
  MEETING_DELETED: 'meeting:deleted'
}

// 事件发射器
class EventEmitter {
  private events: Record<string, Function[]> = {}

  on(event: string, callback: Function) {
    if (!this.events[event]) {
      this.events[event] = []
    }
    this.events[event].push(callback)
  }

  off(event: string, callback: Function) {
    if (!this.events[event]) return
    this.events[event] = this.events[event].filter(cb => cb !== callback)
  }

  emit(event: string, data?: any) {
    if (!this.events[event]) return
    this.events[event].forEach(callback => callback(data))
  }
}

export const eventEmitter = new EventEmitter()

export interface Task {
  id: number
  content: string
  time: string
  completed: boolean
  date: string
  type: string
  endDate?: string
  remindBefore?: number
}

export interface Meeting {
  id: number
  title: string
  time: string
  host: string
  location: string
  status: string
}

// API响应类型定义
interface ApiResponse<T = any> {
  code: number
  msg?: string
  data?: T
  tasks?: T
}

interface TasksApiResponse {
  code: number
  msg?: string
  tasks: Task[]
}

interface MeetingsApiResponse {
  code: number
  msg?: string
  data: Meeting[]
}

class TaskService {
  private api = api

  // 获取所有任务
  async getAllTasks(): Promise<Task[]> {
    try {
      const response = await this.api.get<TasksApiResponse>({ url: '/api/today-tasks' })
      if (response && response.code === 0) {
        return response.tasks || []
      }
      return []
    } catch (error) {
      console.error('获取所有任务失败:', error)
      return []
    }
  }

  // 获取今日任务
  async getTodayTasks(): Promise<Task[]> {
    try {
      const response = await this.api.get<TasksApiResponse>({ url: '/api/today-tasks' })
      // 检查响应结构
      if (response && response.code === 0) {
        const allTasks = response.tasks || []
        // 过滤出今日的任务
        const today = new Date().toISOString().split('T')[0]
        return allTasks.filter((task: Task) => task.date === today)
      }
      return []
    } catch (error) {
      console.error('获取今日任务失败:', error)
      return []
    }
  }

  // 添加任务
  async addTask(task: Omit<Task, 'id'>): Promise<boolean> {
    try {
      const response = await this.api.post<ApiResponse>({ url: '/api/today-tasks', data: task })
      return response && response.code === 0
    } catch (error) {
      console.error('添加任务失败:', error)
      return false
    }
  }

  // 更新任务
  async updateTask(id: number, task: Partial<Task>): Promise<boolean> {
    try {
      const response = await this.api.put<ApiResponse>({ url: `/api/today-tasks/${id}`, data: task })
      return response && response.code === 0
    } catch (error) {
      console.error('更新任务失败:', error)
      return false
    }
  }

  // 更新任务状态
  async updateTaskStatus(id: number, completed: boolean): Promise<boolean> {
    try {
      // 先获取当前任务信息
      const allTasks = await this.getAllTasks()
      const currentTask = allTasks.find(task => task.id === id)
      if (!currentTask) {
        console.error('任务不存在:', id)
        return false
      }
      
      // 更新任务状态
      const response = await this.api.put<ApiResponse>({ 
        url: `/api/today-tasks/${id}`, 
        data: { 
          content: currentTask.content,
          time: currentTask.time,
          completed: completed,
          date: currentTask.date,
          type: currentTask.type,
          endDate: currentTask.endDate || ''
        } 
      })
      return response && response.code === 0
    } catch (error) {
      console.error('更新任务状态失败:', error)
      return false
    }
  }

  // 删除任务
  async deleteTask(id: number): Promise<boolean> {
    try {
      const response = await this.api.del<ApiResponse>({ url: `/api/today-tasks/${id}` })
      return response && response.code === 0
    } catch (error) {
      console.error('删除任务失败:', error)
      return false
    }
  }

  // 获取所有会议
  async getAllMeetings(): Promise<Meeting[]> {
    try {
      const response = await this.api.get<ApiResponse<{list: Meeting[]}>>({ url: '/api/meetings/list', params: { page: 1, pageSize: 100 } })
      if (response && response.code === 0) {
        return response.data?.list || []
      }
      return []
    } catch (error) {
      console.error('获取所有会议失败:', error)
      return []
    }
  }

  // 获取今日会议
  async getTodayMeetings(): Promise<Meeting[]> {
    try {
      // 使用与会议管理页面相同的数据源
      const response = await this.api.get<ApiResponse<{list: Meeting[]}>>({ 
        url: '/api/meetings/list', 
        params: { page: 1, pageSize: 100 } 
      })
      if (response && response.code === 0) {
        const allMeetings = response.data?.list || []
        // 过滤出今日的会议
        const today = new Date().toISOString().split('T')[0]
        return allMeetings.filter((meeting: Meeting) => {
          if (!meeting.time) return false
          // 处理不同的时间格式
          let meetingDate: string
          if (typeof meeting.time === 'string') {
            // 如果是ISO格式的完整时间字符串
            if (meeting.time.includes('T') || meeting.time.includes(' ')) {
              meetingDate = new Date(meeting.time).toISOString().split('T')[0]
            } else {
              // 如果只是日期字符串
              meetingDate = meeting.time.slice(0, 10)
            }
          } else {
            // 如果是Date对象
            meetingDate = new Date(meeting.time).toISOString().split('T')[0]
          }
          return meetingDate === today
        })
      }
      return []
    } catch (error) {
      console.error('获取今日会议失败:', error)
      return []
    }
  }

  // 创建会议
  async createMeeting(meeting: Omit<Meeting, 'id'>): Promise<boolean> {
    try {
      const response = await this.api.post<ApiResponse>({ url: '/api/meetings/create', data: meeting })
      if (response && response.code === 0) {
        // 通知会议创建事件
        eventEmitter.emit(MEETING_EVENTS.MEETING_CREATED, meeting)
        return true
      }
      return false
    } catch (error) {
      console.error('创建会议失败:', error)
      return false
    }
  }

  // 更新会议
  async updateMeeting(id: number, meeting: Partial<Meeting>): Promise<boolean> {
    try {
      const response = await this.api.post<ApiResponse>({ url: '/api/meetings/edit', data: { id, ...meeting } })
      if (response && response.code === 0) {
        // 通知会议更新事件
        eventEmitter.emit(MEETING_EVENTS.MEETING_UPDATED, { id, ...meeting })
        return true
      }
      return false
    } catch (error) {
      console.error('更新会议失败:', error)
      return false
    }
  }

  // 删除会议
  async deleteMeeting(id: number): Promise<boolean> {
    try {
      const response = await this.api.post<ApiResponse>({ url: '/api/meetings/delete', data: { id } })
      if (response && response.code === 0) {
        // 通知会议删除事件
        eventEmitter.emit(MEETING_EVENTS.MEETING_DELETED, { id })
        return true
      }
      return false
    } catch (error) {
      console.error('删除会议失败:', error)
      return false
    }
  }
}

export const taskService = new TaskService() 