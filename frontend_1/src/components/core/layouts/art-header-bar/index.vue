<template>
  <div class="layout-top-bar" :class="[tabStyle]" :style="{ width: topBarWidth() }">
    <div class="menu">
      <div class="left" style="display: flex">
        <!-- 系统信息  -->
        <div class="top-header" @click="toHome" v-if="isTopMenu">
          <svg class="svg-icon2" aria-hidden="true">
            <use xlink:href="#iconsys-zhaopian-copy"></use>
          </svg>
          <p>智能办公助手</p>
        </div>

        <svg class="svg-icon" aria-hidden="true" @click="toHome()">
          <use xlink:href="#iconsys-zhaopian-copy"></use>
        </svg>

        <!-- 菜单按钮 -->
        <div class="btn-box" v-if="isLeftMenu && showMenuButton">
          <div class="btn menu-btn">
            <i class="iconfont-sys" @click="visibleMenu">&#xe6ba;</i>
          </div>
        </div>
        <!-- 刷新按钮 -->
        <div class="btn-box" v-if="showRefreshButton">
          <div class="btn refresh-btn" :style="{ marginLeft: !isLeftMenu ? '10px' : '0' }">
            <i class="iconfont-sys" @click="reload()"> &#xe6b3; </i>
          </div>
        </div>

        <!-- 快速入口 -->
        <ArtFastEnter v-if="width >= 1200" />

        <!-- 面包屑 -->
        <ArtBreadcrumb
          v-if="(showCrumbs && isLeftMenu) || (showCrumbs && isDualMenu)"
          :style="{ paddingLeft: !showRefreshButton && !showMenuButton ? '10px' : '0' }"
        />

        <!-- 顶部菜单 -->
        <ArtHorizontalMenu v-if="isTopMenu" :list="menuList" :width="menuTopWidth" />

        <!-- 混合菜单-顶部 -->
        <ArtMixedMenu v-if="isTopLeftMenu" :list="menuList" :width="menuTopWidth" />
      </div>

      <div class="right">
        <!-- 搜索 -->
        <div class="search-wrap">
          <GlobalSearch />
        </div>

        <!-- 全屏按钮 -->
        <div class="btn-box screen-box" @click="toggleFullScreen">
          <div
            class="btn"
            :class="{ 'full-screen-btn': !isFullscreen, 'exit-full-screen-btn': isFullscreen }"
          >
            <i class="iconfont-sys">{{ isFullscreen ? '&#xe62d;' : '&#xe8ce;' }}</i>
          </div>
        </div>
        <!-- 删除通知按钮 -->
        <!-- 聊天 -->
        <div class="btn-box chat-btn" @click="openChat">
          <div class="btn chat-button">
            <i class="iconfont-sys">&#xe89a;</i>
            <span class="dot"></span>
          </div>
        </div>


          <!-- 切换主题 -->
          <div class="btn-box" @click="themeAnimation($event)">
            <div class="btn theme-btn">
              <i class="iconfont-sys">{{ isDark ? '&#xe6b5;' : '&#xe725;' }}</i>
            </div>
          </div>

          <!-- 用户头像、菜单 -->
        <div class="user">
          <el-popover
            ref="userMenuPopover"
            placement="bottom-end"
            :width="240"
            :hide-after="0"
            :offset="10"
            trigger="hover"
            :show-arrow="false"
            popper-class="user-menu-popover"
            popper-style="border: 1px solid var(--art-border-dashed-color); border-radius: calc(var(--custom-radius) / 2 + 4px); padding: 5px 16px; 5px 16px;"
          >
            <template #reference>
              <img class="cover" :src="getAvatarUrl(userInfo?.avatar)" style="float: left;cursor:pointer" @click="triggerAvatarUpload" />
            </template>
            <template #default>
              <div class="user-menu-box">
                <div class="user-head">
                  <img class="cover" :src="getAvatarUrl(userInfo?.avatar)" style="float: left" />
                  <div class="user-wrap">
                    <span class="name">{{ userInfo.userName }}</span>
                    <span class="email" v-if="userInfo && 'contact' in userInfo">{{ userInfo.contact }}</span>
                  </div>
                </div>
                <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="onAvatarChange" />
                <ul class="user-menu">
                  <li @click="goPage('/system/user-center')">
                    <i class="menu-icon iconfont-sys">&#xe734;</i>
                    <span class="menu-txt">用户中心</span>
                  </li>
                  <li @click="lockScreen()">
                    <i class="menu-icon iconfont-sys">&#xe817;</i>
                    <span class="menu-txt">锁定屏幕</span>
                  </li>
                  <div class="line"></div>
                  <div class="logout-btn" @click="loginOut">
                    退出登录
                  </div>
                </ul>
              </div>
            </template>
          </el-popover>
        </div>
      </div>
    </div>
    <ArtWorkTab />

    <!-- 删除通知组件 -->
  </div>
</template>

<script setup lang="ts">
  import { MenuTypeEnum, MenuWidth } from '@/enums/appEnum'
  import { useSettingStore } from '@/store/modules/setting'
  import { useUserStore } from '@/store/modules/user'
  import { useFullscreen } from '@vueuse/core'
  import { ElMessageBox } from 'element-plus'
  import { HOME_PAGE } from '@/router/routesAlias'
  import mittBus from '@/utils/mittBus'
  import { useMenuStore } from '@/store/modules/menu'
  import AppConfig from '@/config'
  import { UserService } from '@/api/usersApi'
  import defaultAvatar from '@/assets/img/avatar/avatar5.jpg'
  import { useRouter } from 'vue-router'
  import { computed, ref, onMounted, onUnmounted } from 'vue'
  import { storeToRefs } from 'pinia'
  
  const isWindows = navigator.userAgent.includes('Windows')

  const settingStore = useSettingStore()
  const userStore = useUserStore()
  const router = useRouter()

  const {
    showMenuButton,
    showRefreshButton,
    menuOpen,
    showCrumbs,
    systemThemeColor,
    menuType,
    isDark,
    tabStyle
  } = storeToRefs(settingStore)

  const { getUserInfo: userInfo } = storeToRefs(userStore)

  const { menuList } = storeToRefs(useMenuStore())

  // 删除通知相关变量
  const userMenuPopover = ref()

  const isLeftMenu = computed(() => menuType.value === MenuTypeEnum.LEFT)
  const isDualMenu = computed(() => menuType.value === MenuTypeEnum.DUAL_MENU)
  const isTopMenu = computed(() => menuType.value === MenuTypeEnum.TOP)
  const isTopLeftMenu = computed(() => menuType.value === MenuTypeEnum.TOP_LEFT)

    import { useCommon } from '@/composables/useCommon'
  import { WEB_LINKS } from '@/utils/links'
  import { themeAnimation } from '@/utils/theme/animation'
  // 删除通知相关导入



  const menuTopWidth = computed(() => {
    return width.value * 0.5
  })

  onMounted(() => {
    // 删除通知相关事件监听
  })

  onUnmounted(() => {
    // 删除通知相关事件监听
  })

  const { isFullscreen, toggle: toggleFullscreen } = useFullscreen()

  const toggleFullScreen = () => {
    toggleFullscreen()
  }

  const topBarWidth = (): string => {
    const { TOP, DUAL_MENU, TOP_LEFT } = MenuTypeEnum
    const { getMenuOpenWidth } = settingStore
    const { isRootMenu } = router.currentRoute.value.meta
    const type = menuType.value
    const isMenuOpen = menuOpen.value

    const isTopLayout = type === TOP || (type === TOP_LEFT && isRootMenu)

    if (isTopLayout) {
      return '100%'
    }

    if (type === DUAL_MENU) {
      return isRootMenu ? 'calc(100% - 80px)' : `calc(100% - 80px - ${getMenuOpenWidth})`
    }

    return isMenuOpen ? `calc(100% - ${getMenuOpenWidth})` : `calc(100% - ${MenuWidth.CLOSE})`
  }

  const visibleMenu = () => {
    settingStore.setMenuOpen(!menuOpen.value)
  }

  const goPage = (path: string) => {
    router.push(path)
  }


  const toHome = () => {
    router.push(HOME_PAGE)
  }

  const loginOut = () => {
    closeUserMenu()
    setTimeout(() => {
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'login-out-dialog'
      }).then(() => {
        userStore.logOut()
      })
    }, 200)
  }

  const reload = (time: number = 0) => {
    setTimeout(() => {
      useCommon().refresh()
    }, time)
  }





  const openSearchDialog = () => {
    mittBus.emit('openSearchDialog')
  }

  // 删除通知相关函数

  const openChat = () => {
    mittBus.emit('openChat')
  }

  const lockScreen = () => {
    mittBus.emit('openLockScreen')
  }

  const closeUserMenu = () => {
    setTimeout(() => {
      userMenuPopover.value.hide()
    }, 100)
  }

  const avatarInput = ref<HTMLInputElement | null>(null)

  function triggerAvatarUpload() {
    avatarInput.value && avatarInput.value.click()
  }

  async function onAvatarChange(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0]
    console.log('上传文件', file)
    if (!file) {
      ElMessageBox.alert('请选择图片文件', '提示')
      return
    }
    const res = await UserService.uploadAvatar(file)
    if (res && res.data && res.data.avatar) {
      const user = {
        userId: Number(userInfo.value.userId) || 0,
        userName: userInfo.value.userName || '',
        roles: userInfo.value.roles || [],
        buttons: userInfo.value.buttons || [],
        realName: userInfo.value.realName || '',
        nickName: userInfo.value.nickName || '',
        avatar: res.data.avatar,
      }
      userStore.setUserInfo(user)
      ElMessageBox.alert('头像上传成功！', '提示')
    }
    if (avatarInput.value) avatarInput.value.value = ''
  }

  // 添加头像URL处理函数
  const getAvatarUrl = (avatar: string) => {
    if (!avatar) return defaultAvatar
    if (avatar.startsWith('http')) return avatar
    // 如果已经是/uploads/开头，直接使用，否则添加/uploads/前缀
    if (avatar.startsWith('/uploads/')) {
      return `${avatar}?t=${Date.now()}`
    }
    return `/uploads/${avatar}?t=${Date.now()}`
  }
</script>

<style lang="scss" scoped>
  @use './style';
  @use './mobile';
</style>
