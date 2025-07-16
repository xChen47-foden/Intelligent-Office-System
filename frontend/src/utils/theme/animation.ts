import { useTheme } from '@/composables/useTheme'
import { SystemThemeEnum } from '@/enums/appEnum'
import { useSettingStore } from '@/store/modules/setting'
import { getSysStorage, getSysVersion } from '@/utils/storage'
const { LIGHT, DARK } = SystemThemeEnum

/**
 * 主题切换动画
 * @param e 鼠标点击事件
 */
export const themeAnimation = (e: any) => {
  const x = e.clientX
  const y = e.clientY
  // 计算鼠标点击位置距离视窗的最大圆半径
  const endRadius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))

  // 设置CSS变量
  document.documentElement.style.setProperty('--x', x + 'px')
  document.documentElement.style.setProperty('--y', y + 'px')
  document.documentElement.style.setProperty('--r', endRadius + 'px')

  if (document.startViewTransition) {
    document.startViewTransition(() => toggleTheme())
  } else {
    toggleTheme()
  }
}

/**
 * 切换主题
 */
const toggleTheme = () => {
  const settingStore = useSettingStore()
  const targetTheme = settingStore.systemThemeType === LIGHT ? DARK : LIGHT
  useTheme().switchThemeStyles(targetTheme)
  
  // 保存主题设置到本地存储
  const version = getSysVersion() || import.meta.env.VITE_VERSION
  const storageKey = `sys-v${version}`
  const storage = localStorage.getItem(storageKey)
  
  if (storage) {
    const parsedStorage = JSON.parse(storage)
    if (parsedStorage.user && parsedStorage.user.setting) {
      parsedStorage.user.setting.systemThemeType = targetTheme
      parsedStorage.user.setting.systemThemeMode = targetTheme
      localStorage.setItem(storageKey, JSON.stringify(parsedStorage))
    }
  }
}

/**
 * 提升暗黑主题下页面刷新视觉体验
 * @param addClass 是否添加 class
 */
export const setThemeTransitionClass = (addClass: boolean) => {
  const el = document.getElementsByTagName('body')[0]

  if (addClass) {
    el.setAttribute('class', 'theme-change')
  } else {
    setTimeout(() => {
      el.removeAttribute('class')
    }, 300)
  }
}
