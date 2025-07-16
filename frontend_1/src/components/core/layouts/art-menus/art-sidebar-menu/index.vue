<!-- 左侧菜单 或 双列菜单 -->
<template>
  <div
    class="ArtSidebarMenu"
    v-if="showLeftMenu || isDualMenu"
    :class="{ 'no-border': menuList.length === 0 }"
    :style="{ width: menuOpen ? openwidth : closewidth, background: getMenuTheme.background }"
  >
    <!-- 双列菜单（左侧） -->
    <div class="dual-menu-left" :style="{ background: getMenuTheme.background }" v-if="isDualMenu">
      <svg class="svg-icon" aria-hidden="true" @click="toHome">
        <use xlink:href="#iconsys-zhaopian-copy"></use>
      </svg>
      <el-scrollbar style="height: calc(100% - 135px)">
        <ul>
          <li v-for="menu in firstLevelMenus" :key="menu.path" @click="handleMenuJump(menu, true)">
            <el-tooltip
              class="box-item"
              effect="dark"
              :content="$t(menu.meta.title)"
              placement="right"
              :offset="25"
              :hide-after="0"
              :disabled="dualMenuShowText"
            >
              <div
                :class="{
                  'is-active': menu.meta.isRootMenu
                    ? menu.path === route.path
                    : menu.path === firstLevelMenuPath
                }"
                :style="{
                  margin: dualMenuShowText ? '5px' : '15px',
                  height: dualMenuShowText ? '60px' : '46px'
                }"
              >
                <i
                  class="iconfont-sys"
                  v-html="menu.meta.icon"
                  :style="{
                    fontSize: dualMenuShowText ? '18px' : '22px',
                    marginBottom: dualMenuShowText ? '5px' : '0'
                  }"
                ></i>
                <span v-if="dualMenuShowText">
                  {{ $t(menu.meta.title) }}
                </span>
              </div>
            </el-tooltip>
          </li>
        </ul>
      </el-scrollbar>
      <div class="switch-btn" @click="setDualMenuMode">
        <i class="iconfont-sys">&#xe798;</i>
      </div>
    </div>

    <!-- 左侧菜单 || 双列菜单（右侧） -->
    <div
      v-show="menuList.length > 0"
      class="menu-left"
      id="menu-left"
      :class="`menu-left-${getMenuTheme.theme} menu-left-${!menuOpen ? 'close' : 'open'}`"
      :style="{ background: getMenuTheme.background }"
    >
      <div class="header" @click="toHome" :style="{ background: getMenuTheme.background }">
        <svg class="svg-icon sidebar-logo" aria-hidden="true" v-if="!isDualMenu">
          <use xlink:href="#iconsys-zhaopian-copy"></use>
        </svg>
        <p
          :class="{ 'is-dual-menu-name': isDualMenu }"
          :style="{ color: getMenuTheme.systemNameColor, opacity: !menuOpen ? 0 : 1 }"
        >
          {{ AppConfig.systemInfo.name }}
        </p>
        <p v-if="userInfo.department" class="sidebar-department" style="font-size: 13px; color: #888; margin: 0; padding: 0 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
          部门：{{ userInfo.department }}
        </p>
      </div>
      <el-menu
        :router="true"
        :collapse="!menuOpen"
        :default-active="routerPath"
        :text-color="getMenuTheme.textColor"
        :unique-opened="uniqueOpened"
        :background-color="getMenuTheme.background"
        :active-text-color="getMenuTheme.textActiveColor"
        :default-openeds="defaultOpenedsArray"
        :popper-class="`menu-left-${getMenuTheme.theme}-popper`"
      >
        <SidebarSubmenu
          :list="menuList"
          :isMobile="isMobileModel"
          :theme="getMenuTheme"
          @close="closeMenu"
        />
      </el-menu>

      <div
        class="menu-model"
        @click="visibleMenu"
        :style="{
          opacity: !menuOpen ? 0 : 1,
          transform: showMobileModel ? 'scale(1)' : 'scale(0)'
        }"
      >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import AppConfig from '@/config'
  import { HOME_PAGE } from '@/router/routesAlias'
  import { useSettingStore } from '@/store/modules/setting'
  import { MenuTypeEnum, MenuWidth } from '@/enums/appEnum'
  import { useMenuStore } from '@/store/modules/menu'
  import { isIframe } from '@/utils/utils'
  import { handleMenuJump } from '@/utils/jump'
  import SidebarSubmenu from './widget/SidebarSubmenu.vue'
  import { asyncRoutes } from '@/router/routes/asyncRoutes'
  import { useUserStore } from '@/store/modules/user'
  import { useRoute, useRouter } from 'vue-router'
  import { computed, ref, watch, onMounted } from 'vue'
  import { storeToRefs } from 'pinia'

  const route = useRoute()
  const router = useRouter()
  const settingStore = useSettingStore()
  const userStore = useUserStore()

  const { getMenuOpenWidth, menuType, uniqueOpened, dualMenuShowText, menuOpen, getMenuTheme } =
    storeToRefs(settingStore)

  const menuCloseWidth = MenuWidth.CLOSE

  const openwidth = computed(() => getMenuOpenWidth.value)
  const closewidth = computed(() => menuCloseWidth)

  const isTopLeftMenu = computed(() => menuType.value === MenuTypeEnum.TOP_LEFT)
  const showLeftMenu = computed(
    () => menuType.value === MenuTypeEnum.LEFT || menuType.value === MenuTypeEnum.TOP_LEFT
  )
  const isDualMenu = computed(() => menuType.value === MenuTypeEnum.DUAL_MENU)

  const defaultOpenedsArray = ref([])

  // 一级菜单列表
  const firstLevelMenus = computed(() => {
    return useMenuStore().menuList.filter((menu) => !menu.meta.isHide)
  })

  const menuList = computed(() => asyncRoutes[0]?.children ?? [])

  const firstLevelMenuPath = computed(() => {
    return route.matched[0].path
  })

  const routerPath = computed(() => {
    return route.path
  })

  const userInfo = userStore.getUserInfo

  onMounted(() => {
    listenerWindowResize()
  })

  const isMobileModel = ref(false)
  const showMobileModel = ref(false)

  watch(
    () => !menuOpen.value,
    (collapse: boolean) => {
      if (!collapse) {
        showMobileModel.value = true
      }
    }
  )

  const toHome = () => {
    router.push(HOME_PAGE)
  }

  let screenWidth = 0

  const listenerWindowResize = () => {
    screenWidth = document.body.clientWidth

    setMenuModel()

    window.onresize = () => {
      return (() => {
        screenWidth = document.body.clientWidth
        setMenuModel()
      })()
    }
  }

  const setMenuModel = () => {
    // 小屏幕折叠菜单
    if (screenWidth < 800) {
      settingStore.setMenuOpen(false)
    }
  }

  const visibleMenu = () => {
    settingStore.setMenuOpen(!menuOpen.value)

    // 移动端模态框
    if (!showMobileModel.value) {
      showMobileModel.value = true
    } else {
      setTimeout(() => {
        showMobileModel.value = false
      }, 200)
    }
  }

  const closeMenu = () => {
    if (document.body.clientWidth < 800) {
      settingStore.setMenuOpen(false)
      showMobileModel.value = false
    }
  }

  const setDualMenuMode = () => {
    settingStore.setDualMenuShowText(!dualMenuShowText.value)
  }
</script>

<style lang="scss" scoped>
  @use './style';
  .header {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 0 8px 0;
  }
  .sidebar-logo {
    width: 48px;
    height: 48px;
    margin-bottom: 8px;
    display: block;
  }
  .sidebar-department {
    margin-top: 2px;
    font-size: 13px;
    color: #888;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>

<style lang="scss">
  @use './theme';

  .ArtSidebarMenu {
    // 展开的宽度
    .el-menu:not(.el-menu--collapse) {
      width: v-bind(openwidth);
    }

    // 折叠后宽度
    .el-menu--collapse {
      width: v-bind(closewidth);
    }
  }
</style>
