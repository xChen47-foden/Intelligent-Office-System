import axios from 'axios'

export interface DashboardStats {
  cardStats: Array<{
    des: string
    icon: string
    num: number
    change: string
  }>
  docStats: {
    total: number
    todayProcessed: number
    pending: number
  }
  scheduleStats: {
    todaySchedule: number
    upcoming: number
    completed: number
  }
}

export interface ChartData {
  month: string
  value: number
}

export interface DepartmentData {
  name: string
  responsibilities: string[]
  leader: string
  members: string[]
  email: string
  phone: string
  announcement?: string
}

export interface TodayTask {
  id: number
  content: string
  time: string
  completed: boolean
  date: string
  type: string
  endDate: string
}

export interface ScheduleTask {
  id: number
  title: string
  time: string
}

/**
 * 获取工作台统计数据
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/dashboard/stats', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      return response.data.data
    }
    
    throw new Error(response.data.msg || '获取统计数据失败')
  } catch (error) {
    console.error('获取工作台统计数据失败:', error)
    // 返回默认数据
    return {
      cardStats: [
        { des: '总访问次数', icon: '&#xe721;', num: 5000, change: '+15%' },
        { des: '在线访客数', icon: '&#xe724;', num: 50, change: '+8%' },
        { des: '点击量', icon: '&#xe7aa;', num: 4500, change: '-5%' },
        { des: '新用户', icon: '&#xe82a;', num: 30, change: '+25%' }
      ],
      docStats: { total: 0, todayProcessed: 0, pending: 0 },
      scheduleStats: { todaySchedule: 0, upcoming: 0, completed: 0 }
    }
  }
}

/**
 * 获取图表数据
 */
export async function getChartData(): Promise<ChartData[]> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/dashboard/chart-data', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      return response.data.data
    }
    
    throw new Error(response.data.msg || '获取图表数据失败')
  } catch (error) {
    console.error('获取图表数据失败:', error)
    // 返回默认数据
    return [
      { month: '一月', value: 80 },
      { month: '二月', value: 120 },
      { month: '三月', value: 150 },
      { month: '四月', value: 100 },
      { month: '五月', value: 90 },
      { month: '六月', value: 130 },
      { month: '七月', value: 140 },
      { month: '八月', value: 170 },
      { month: '九月', value: 160 }
    ]
  }
}

/**
 * 获取部门信息
 */
export async function getDepartmentInfo(): Promise<DepartmentData> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/dashboard/department', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      return response.data.data
    }
    
    throw new Error(response.data.msg || '获取部门信息失败')
  } catch (error) {
    console.error('获取部门信息失败:', error)
    // 返回默认数据
    return {
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

/**
 * 获取今日任务列表
 */
export async function getTodayTasks(): Promise<TodayTask[]> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/today-tasks', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      return response.data.tasks || []
    }
    
    throw new Error(response.data.msg || '获取任务列表失败')
  } catch (error) {
    console.error('获取今日任务失败:', error)
    return []
  }
}

/**
 * 添加今日任务
 */
export async function addTodayTask(task: Omit<TodayTask, 'id'>): Promise<TodayTask> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post('/api/today-tasks', task, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data.code === 0) {
      return response.data.task
    }
    
    throw new Error(response.data.msg || '添加任务失败')
  } catch (error) {
    console.error('添加任务失败:', error)
    throw error
  }
}

/**
 * 更新今日任务
 */
export async function updateTodayTask(taskId: number, task: Omit<TodayTask, 'id'>): Promise<TodayTask> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.put(`/api/today-tasks/${taskId}`, task, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data.code === 0) {
      return response.data.task
    }
    
    throw new Error(response.data.msg || '更新任务失败')
  } catch (error) {
    console.error('更新任务失败:', error)
    throw error
  }
}

/**
 * 删除今日任务
 */
export async function deleteTodayTask(taskId: number): Promise<void> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.delete(`/api/today-tasks/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code !== 0) {
      throw new Error(response.data.msg || '删除任务失败')
    }
  } catch (error) {
    console.error('删除任务失败:', error)
    throw error
  }
}

/**
 * 获取今日会议任务
 */
export async function getTodaySchedule(): Promise<ScheduleTask[]> {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/schedule/today', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.code === 0) {
      return response.data.data || []
    }
    
    throw new Error(response.data.msg || '获取会议失败')
  } catch (error) {
    console.error('获取今日会议失败:', error)
    return []
  }
}

/**
 * 刷新工作台数据
 */
export async function refreshDashboardData() {
  try {
    const [statsData, departmentData] = await Promise.all([
      getDashboardStats(),
      getDepartmentInfo()
    ])
    
    return {
      stats: statsData,
      department: departmentData
    }
  } catch (error) {
    console.error('刷新工作台数据失败:', error)
    throw error
  }
} 