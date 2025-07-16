import { ElMessage } from 'element-plus'
import { router } from '@/router'
import { useUserStore } from '@/store/modules/user'
import { useSettingStore } from '@/store/modules/setting'
import { useWorktabStore } from '@/store/modules/worktab'
import { useTableStore } from '@/store/modules/table'

// 初始化本地数据
export function initState() {
  if (validateStorageData() || isLocalStorageEmpty()) {
    const userStore = useUserStore()
    const worktabStore = useWorktabStore()
    const settingStore = useSettingStore()
    const tableStore = useTableStore()

    userStore.initState()
    worktabStore.initState()
    settingStore.initState()
    tableStore.initState()
  }
}

// 获取系统存储数据
export function getSysStorage() {
  const version = getSysVersion() || import.meta.env.VITE_VERSION
  return localStorage.getItem(`sys-v${version}`) as any
}

// 获取系统版本
export function getSysVersion() {
  return localStorage.getItem('version')
}

// 验证本地存储数据的类型
function validate(obj: any, schema: any, path: string = ''): boolean {
  // 如果 obj 不存在，则跳过验证
  if (!obj || typeof obj !== 'object') {
    return false
  }
  
  return Object.keys(schema).every((key) => {
    const fullPath = path ? `${path}.${key}` : key
    const expectedType = schema[key]
    const actualType = typeof obj[key]

    // 如果字段不存在，记录警告但不阻止验证
    if (obj[key] === undefined) {
      console.warn(
        `本地存储字段缺失 path：[/utils/storage.ts] ${fullPath}，将使用默认值`
      )
      return true // 允许缺失字段，使用默认值
    }

    if (typeof expectedType === 'object' && !Array.isArray(expectedType)) {
      return validate(obj[key], expectedType, fullPath)
    } else if (actualType !== expectedType) {
      console.error(
        `检测到本地数据异常 path：[/utils/storage.ts] ${fullPath} 数据类型应为 ${expectedType}，实际为 ${actualType}`
      )
      return false
    }

    return true
  })
}

// 显示错误消息并处理登出逻辑
function handleError() {
  ElMessage({
    type: 'error',
    offset: 40,
    duration: 5000,
    message: '系统检测到本地数据异常，请重新登录系统恢复使用！'
  })

  logOut()
}

function logOut() {
  setTimeout(() => {
    localStorage.clear()
    useUserStore().logOut()
    router.push('/login')
    initState()
  }, 1000)
}

// 验证本地存储数据并处理异常
export function validateStorageData() {
  if (typeof location.href === 'string' && (location.href.includes('/login') || location.href.includes('/register'))) return true

  const schema = {
    user: {
      info: 'object',
      isLogin: 'boolean',
      worktab: 'object', // 简化worktab的验证，不深入验证内部结构
      setting: {
        systemThemeType: 'string',
        systemThemeMode: 'string',
        menuThemeType: 'string',
        boxBorderMode: 'boolean',
        uniqueOpened: 'boolean',
        systemThemeColor: 'string',
        showMenuButton: 'boolean',
        showRefreshButton: 'boolean',
        showCrumbs: 'boolean',
        autoClose: 'boolean',
        showWorkTab: 'boolean',
        showNprogress: 'boolean',
        colorWeak: 'boolean',
        showSettingGuide: 'boolean',
        refresh: 'boolean'
      }
    }
  }

  try {
    const data = getLocalStorageData()
    // 模拟本地数据类型错误
    // data.user.language = 2024

    // 如果是刚登录的用户，数据可能还没有完全保存，给一些宽容度
    if (Object.keys(data).length === 0) {
      // 检查是否有token，如果有token但没有存储数据，可能是正在登录过程中
      const token = localStorage.getItem('token')
      if (token) {
        console.warn('检测到token但存储数据为空，可能正在登录过程中，跳过验证')
        return true
      }
      logOut()
      return false
    }

    if (!validate(data, schema)) {
      throw new Error('本地存储数据结构异常')
    }

    return true
  } catch {
    handleError()
    return false
  }
}

// 获取本地存储数据
function getLocalStorageData() {
  return JSON.parse(getSysStorage() || '{}')
}

// 本地存储是否为空
function isLocalStorageEmpty() {
  return Object.keys(getLocalStorageData()).length === 0
}

// 将 vuex 中的数据保存到 localStorage 中（在即将离开页面(刷新或关闭)时执行）
export function saveUserData() {
  const isiOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
  const eventType = isiOS ? 'pagehide' : 'beforeunload'

  window.addEventListener(eventType, () => {
    if (getSysVersion()) {
      useUserStore().saveUserData()
    }
  })
}
