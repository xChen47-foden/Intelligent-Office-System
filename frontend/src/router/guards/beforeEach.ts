import type { Router, RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { ref } from 'vue'
import NProgress from 'nprogress'
import { useSettingStore } from '@/store/modules/setting'
import { useUserStore } from '@/store/modules/user'
import { useMenuStore } from '@/store/modules/menu'
import { setWorktab } from '@/utils/worktab'
import { setPageTitle, setSystemTheme } from '../utils/utils'
import { menuService } from '@/api/menuApi'
import { registerDynamicRoutes } from '../utils/registerRoutes'
import { MenuListType } from '@/types/menu'
import { RoutesAlias } from '../routesAlias'
import { menuDataToRouter } from '../utils/menuToRouter'
import { asyncRoutes } from '../routes/asyncRoutes'
import { loadingService } from '@/utils/loading'
import { useCommon } from '@/composables/useCommon'

// 是否已注册动态路由
const isRouteRegistered = ref(false)

/**
 * 路由全局前置守卫
 * 处理进度条、获取菜单列表、动态路由注册、404 检查、工作标签页及页面标题设置
 */
export function setupBeforeEachGuard(router: Router): void {
  router.beforeEach(
    async (
      to: RouteLocationNormalized,
      from: RouteLocationNormalized,
      next: NavigationGuardNext
    ) => {
      try {
        await handleRouteGuard(to, from, next, router)
      } catch (error) {
        console.error('路由守卫处理失败:', error)
        next('/exception/500')
      }
    }
  )
}

/**
 * 处理路由守卫逻辑
 */
async function handleRouteGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
  router: Router
): Promise<void> {
  const settingStore = useSettingStore()
  const userStore = useUserStore()

  console.log('🛡️ 路由守卫:', {
    from: from.path,
    to: to.path,
    isLogin: userStore.isLogin,
    matched: to.matched.length,
    isStatic: isStaticRoute(to.path)
  })

  // 处理进度条
  if (settingStore.showNprogress) {
    NProgress.start()
  }

  // 设置系统主题
  setSystemTheme(to)

  // 处理登录状态
  if (!(await handleLoginStatus(to, userStore, next))) {
    console.log('❌ 登录状态检查失败')
    return
  }

  // 处理已知的匹配路由（包括静态路由）
  if (to.matched.length > 0) {
    console.log('✅ 路由匹配成功，允许访问:', to.path)
    // 设置页面信息
    setWorktab(to)
    setPageTitle(to)
    next()
    return
  }

  console.log('⚠️ 路由未匹配，matched.length:', to.matched.length)

  // 处理动态路由注册（只有在需要时才注册）
  if (!isRouteRegistered.value && userStore.isLogin && !isStaticRoute(to.path)) {
    console.log('🔄 开始动态路由注册')
    await handleDynamicRoutes(to, router, next)
    return
  }

  // 尝试刷新路由重新注册
  if (userStore.isLogin && !isStaticRoute(to.path)) {
    console.log('🔄 重新注册动态路由')
    isRouteRegistered.value = false
    await handleDynamicRoutes(to, router, next)
    return
  }

  // 如果以上都不匹配，跳转到404
  console.log('❌ 所有条件都不匹配，跳转到404')
  next(RoutesAlias.Exception404)
}

/**
 * 处理登录状态
 */
async function handleLoginStatus(
  to: RouteLocationNormalized,
  userStore: ReturnType<typeof useUserStore>,
  next: NavigationGuardNext
): Promise<boolean> {
  if (!userStore.isLogin && to.path !== '/login' && !to.meta.noLogin) {
    userStore.logOut()
    next('/login')
    return false
  }
  return true
}

/**
 * 处理动态路由注册
 */
async function handleDynamicRoutes(
  to: RouteLocationNormalized,
  router: Router,
  next: NavigationGuardNext
): Promise<void> {
  try {
    await getMenuData(router)
    // 重新导航到目标路由，以便重新匹配
    next({ path: to.fullPath, replace: true })
  } catch (error) {
    console.error('动态路由注册失败:', error)
    next('/exception/500')
  }
}

/**
 * 获取菜单数据
 * @param router 路由实例
 */
async function getMenuData(router: Router): Promise<void> {
  try {
    if (useCommon().isFrontendMode.value) {
      await processFrontendMenu(router) // 前端控制模式
    } else {
      await processBackendMenu(router) // 后端控制模式
    }
  } catch (error) {
    handleMenuError(error)
  }
}

/**
 * 处理前端控制模式的菜单逻辑
 */
async function processFrontendMenu(router: Router): Promise<void> {
  console.log('🚀 开始处理前端控制模式路由')
  const menuList = asyncRoutes.map((route) => menuDataToRouter(route))
  const userStore = useUserStore()
  let roles = userStore.info.roles

  // 如果没有角色信息，设置默认角色
  if (!roles || roles.length === 0) {
    console.warn('用户角色信息缺失，使用默认角色')
    roles = ['R_USER']
    // 更新用户信息中的角色
    userStore.setUserInfo({ ...userStore.info, roles } as any)
  }

  console.log('👤 用户角色:', roles)
  const filteredMenuList = filterMenuByRoles(menuList, roles)
  console.log('📋 过滤后的菜单列表:', filteredMenuList)
  
  await registerAndStoreMenu(router, filteredMenuList, () => {})
}

/**
 * 处理后端控制模式的菜单逻辑
 */
async function processBackendMenu(router: Router): Promise<void> {
  console.log('🔄 尝试处理后端控制模式路由')
  // 暂时禁用后端控制模式，直接使用前端路由
  console.warn('⚠️ 后端控制模式暂时禁用，转为前端控制模式')
  await processFrontendMenu(router)
}

/**
 * 注册路由并存储菜单数据
 */
async function registerAndStoreMenu(
  router: Router,
  menuList: MenuListType[],
  closeLoading: () => void
): Promise<void> {
  if (!isValidMenuList(menuList)) {
    console.error('❌ 菜单列表无效:', menuList)
    closeLoading()
    throw new Error('获取菜单列表失败，请重新登录')
  }

  console.log('✅ 菜单列表有效，开始注册路由')
  const menuStore = useMenuStore()
  menuStore.setMenuList(menuList)
  console.log('📝 菜单数据已存储到store')
  
  registerDynamicRoutes(router, menuList)
  console.log('🛤️ 动态路由注册完成')
  
  isRouteRegistered.value = true
  console.log('🎯 路由注册标记已设置为true')
  closeLoading()
}

/**
 * 处理菜单相关错误
 */
function handleMenuError(error: unknown): void {
  console.error('菜单处理失败:', error)
  useUserStore().logOut()
  throw error instanceof Error ? error : new Error('获取菜单列表失败，请重新登录')
}

/**
 * 根据角色过滤菜单
 */
const filterMenuByRoles = (menu: MenuListType[], roles: string[]): MenuListType[] => {
  return menu.reduce((acc: MenuListType[], item) => {
    const itemRoles = item.meta?.roles
    const hasPermission = !itemRoles || itemRoles.some((role) => Array.isArray(roles) && roles.includes(role))

    if (hasPermission) {
      const filteredItem = { ...item }
      if (filteredItem.children?.length) {
        filteredItem.children = filterMenuByRoles(filteredItem.children, roles)
      }
      acc.push(filteredItem)
    }

    return acc
  }, [])
}

/**
 * 验证菜单列表是否有效
 */
function isValidMenuList(menuList: MenuListType[]): boolean {
  return Array.isArray(menuList) && menuList.length > 0
}

/**
 * 检查是否是静态路由
 */
function isStaticRoute(path: string): boolean {
  const staticRoutes = ['/workbench', '/login', '/register', '/forget-password', '/exception', '/outside']
  return staticRoutes.some(route => path.startsWith(route))
}

/**
 * 重置路由相关状态
 */
export function resetRouterState(router: Router): void {
  isRouteRegistered.value = false
  // 清理动态注册的路由
  router.getRoutes().forEach((route) => {
    if (route.meta?.dynamic) {
      router.removeRoute(route.name as string)
    }
  })
  // 清空菜单数据
  const menuStore = useMenuStore()
  menuStore.setMenuList([])
}
