<template>
  <ElConfigProvider size="default" :z-index="3000">
    <RouterView></RouterView>
  </ElConfigProvider>
</template>

<script setup lang="ts">
  import { useUserStore } from './store/modules/user'
  import { systemUpgrade } from './utils/upgrade'
  import { initState, saveUserData } from './utils/storage'
  import { UserService } from './api/usersApi'
  import { ApiStatus } from './utils/http/status'
  import { setThemeTransitionClass } from './utils/theme/animation'
  import { onBeforeMount, onMounted } from 'vue'
  import { useRoute } from 'vue-router'

  const userStore = useUserStore()
  const route = useRoute()
  userStore.initState()

  onBeforeMount(() => {
    setThemeTransitionClass(true)
  })

  onMounted(() => {
    initState()
    saveUserData()
    setThemeTransitionClass(false)
    systemUpgrade()
    // 只有在不是登录页面时才尝试获取用户信息
    if (route.path !== '/login' && route.path !== '/register') {
    getUserInfo()
    }
  })

  // 获取用户信息
  const getUserInfo = async () => {
    // 检查是否有token
    const token = localStorage.getItem('token')
    if (!token) {
      return
    }

    // 检查用户是否已登录
    if (userStore.isLogin) {
      try {
      const res = await UserService.getUserInfo()
      if (res.code === ApiStatus.success) {
        userStore.setUserInfo(res.data)
        }
      } catch (error) {
        // 静默处理错误，避免在控制台显示错误
        console.debug('获取用户信息失败，可能是token已过期')
      }
    }
  }
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>
