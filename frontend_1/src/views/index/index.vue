<template>
  <div class="layouts">
    <ArtHeaderBar />
    <div class="main-body" :class="mainBodyClass">
      <ArtSidebarMenu v-if="showSidebarMenu" />
      <div class="main-content" :style="layoutStyle">
        <ArtPageContent />
      </div>
    </div>
    
    <ArtScreenLock />
    <ArtChatWindow />
    <ArtFireworksEffect />
    <ArtWatermark :visible="watermarkVisible" />
  </div>
</template>

<script setup lang="ts">
import '@/assets/styles/transition.scss'
import { MenuTypeEnum } from '@/enums/appEnum'
import { useMenuStore } from '@/store/modules/menu'
import { useSettingStore } from '@/store/modules/setting'
import { getTabConfig } from '@/utils/tabs'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { watchEffect } from 'vue'

// 导入布局组件
import ArtHeaderBar from '@/components/core/layouts/art-header-bar/index.vue'
import ArtSidebarMenu from '@/components/core/layouts/art-menus/art-sidebar-menu/index.vue'
import ArtPageContent from '@/components/core/layouts/art-page-content/index.vue'
import ArtScreenLock from '@/components/core/layouts/art-screen-lock/index.vue'
import ArtChatWindow from '@/components/core/layouts/art-chat-window/index.vue'
import ArtWatermark from '@/components/core/others/ArtWatermark.vue'

// 导入特效组件 (如果不存在就创建一个空组件)
import ArtFireworksEffect from '@/components/core/others/ArtFireworksEffect.vue'

const settingStore = useSettingStore()
const menuStore = useMenuStore()
const router = useRouter()

const { menuType, menuOpen, showWorkTab, watermarkVisible, tabStyle } = storeToRefs(settingStore)

const showSidebarMenu = computed(() =>
  menuType.value === MenuTypeEnum.LEFT ||
  menuType.value === MenuTypeEnum.DUAL_MENU ||
  menuType.value === MenuTypeEnum.TOP_LEFT
)

const mainBodyClass = computed(() => {
  if (menuType.value === MenuTypeEnum.TOP) return 'main-body-top'
  if (menuType.value === MenuTypeEnum.DUAL_MENU) return 'main-body-dual'
  return ''
})

watchEffect(() => {
  const isOpen = menuOpen.value
  const width = isOpen ? settingStore.getMenuOpenWidth : 60
  menuStore.setMenuWidth(typeof width === 'string' ? width : `${width}px`)
})

const paddingLeft = computed(() => {
  const isOpen = menuOpen.value
  const type = menuType.value
  const width = isOpen ? settingStore.getMenuOpenWidth : 60
  const { isRootMenu } = router.currentRoute.value.meta || {}

  if (type === MenuTypeEnum.DUAL_MENU) {
    return isRootMenu ? '80px' : `calc(${typeof width === 'string' ? width : width + 'px'} + 80px)`
  }

  if (type === MenuTypeEnum.TOP_LEFT && isRootMenu) {
    return '0px'
  }

  // 移除左侧内边距，让内容紧贴侧边栏
  return '0px'
})

const paddingTop = computed(() => {
  const { openTop, closeTop } = getTabConfig(tabStyle.value)
  // 大幅减少顶部内边距，让内容紧贴顶部导航栏
  const baseTop = showWorkTab.value ? openTop : closeTop
  return `${Math.max(0, baseTop - 40)}px`
})

const layoutStyle = computed(() => ({
  paddingLeft: paddingLeft.value,
  paddingTop: paddingTop.value
}))
</script>

<style lang="scss" scoped>
.layouts {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.main-body {
  display: flex;
  flex: 1;
  min-height: 0;
}
.main-body-top {
  flex-direction: column;
}
.main-body-dual {
}
ArtSidebarMenu {
  width: 220px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #eee;
  height: 100%;
}
.main-content {
  flex: 1;
  min-width: 0;
  background: #f7f8fa;
  padding: 24px;
  overflow: auto;
  margin-top: 0;       // 移除顶部间距，紧贴导航栏
  margin-left: 0;      // 移除左侧间距，紧贴导航栏
  border-radius: 12px; // 圆角
  box-shadow: 0 2px 8px rgba(0,0,0,0.04); // 阴影
}
</style>