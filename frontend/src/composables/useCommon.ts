import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { getTabConfig } from '@/utils/tabs'
import { useSettingStore } from '@/store/modules/setting'

// 通用函数
export function useCommon() {
  const settingStore = useSettingStore()
  const { showWorkTab, tabStyle } = storeToRefs(settingStore)

  // 是否是前端控制模式
  const isFrontendMode = computed(() => {
    // 如果没有设置环境变量，默认使用前端控制模式
    const accessMode = import.meta.env.VITE_ACCESS_MODE
    return !accessMode || accessMode === 'frontend'
  })

  // 刷新页面
  const refresh = () => {
    settingStore.reload()
  }

  // 回到顶部
  const scrollToTop = () => {
    window.scrollTo({ top: 0 })
  }

  // 页面最小高度
  const containerMinHeight = computed(() => {
    const { openHeight, closeHeight } = getTabConfig(tabStyle.value)
    return `calc(100vh - ${showWorkTab.value ? openHeight : closeHeight}px)`
  })

  return {
    isFrontendMode,
    refresh,
    scrollToTop,
    containerMinHeight
  }
}
