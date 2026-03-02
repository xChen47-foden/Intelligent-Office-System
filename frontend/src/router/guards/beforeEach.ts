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

// 是否已注册动态路由（使用 sessionStorage 持久化，避免刷新时丢失）
const getRouteRegistered = () => {
  try {
    return sessionStorage.getItem('routeRegistered') === 'true'
  } catch {
    return false
  }
}

const setRouteRegistered = (value: boolean) => {
  try {
    sessionStorage.setItem('routeRegistered', value ? 'true' : 'false')
  } catch {
    // 忽略错误
  }
}

// 是否已注册动态路由
const isRouteRegistered = ref(getRouteRegistered())

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

  // 如果用户已登录但路由未匹配，需要注册动态路由
  if (userStore.isLogin && !isStaticRoute(to.path)) {
    // 如果路由未注册，或者需要重新注册
    if (!isRouteRegistered.value) {
    console.log('🔄 开始动态路由注册')
    await handleDynamicRoutes(to, router, next)
    return
    } else {
      // 如果已注册但路由仍未匹配，可能是路由注册有问题，重新注册
      console.log('🔄 路由已注册但未匹配，重新注册动态路由')
    isRouteRegistered.value = false
    await handleDynamicRoutes(to, router, next)
    return
    }
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
    console.log('🔄 开始注册动态路由，目标路径:', to.path)
    await getMenuData(router)
    console.log('✅ 动态路由注册完成，准备导航到:', to.fullPath)
    
    // 等待路由注册完成
    await new Promise(resolve => setTimeout(resolve, 100))
    
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
  const department = userStore.info.department || ''

  // 如果没有角色信息，设置默认角色
  if (!roles || roles.length === 0) {
    console.warn('用户角色信息缺失，使用默认角色')
    roles = ['R_USER']
    // 更新用户信息中的角色
    userStore.setUserInfo({ ...userStore.info, roles } as any)
  }

  console.log('👤 用户角色:', roles, '部门:', department, '部门类型:', typeof department)
  console.log('📋 原始菜单列表:', menuList)
  const filteredMenuList = filterMenuByRolesAndDepartment(menuList, roles, department)
  console.log('📋 过滤后的菜单列表:', filteredMenuList)
  console.log('📋 过滤后的菜单项名称:', filteredMenuList[0]?.children?.map((item: any) => item.name))
  
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
  setRouteRegistered(true)
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
 * 根据角色和部门过滤菜单
 */
const filterMenuByRolesAndDepartment = (menu: MenuListType[], roles: string[], department: string): MenuListType[] => {
  return menu.reduce((acc: MenuListType[], item) => {
    const itemRoles = item.meta?.roles
    const itemDepartment = item.meta?.department as string | undefined
    
    // 检查角色权限
    const hasRolePermission = !itemRoles || itemRoles.some((role) => Array.isArray(roles) && roles.includes(role))
    
    // 检查部门权限（如果菜单项指定了部门要求）
    let hasDepartmentPermission = true
    if (itemDepartment) {
      hasDepartmentPermission = department === itemDepartment
    }
    
    // 特殊处理：人员管理只对人事部显示
    const isPersonnelMenu = item.name === 'Personnel' || 
                           item.path?.includes('personnel') || 
                           item.path?.includes('/personnel') ||
                           item.meta?.title === '人员管理'
    
    if (isPersonnelMenu) {
      console.log(`[菜单过滤] 检测到人员管理菜单项`)
      console.log(`[菜单过滤] 菜单项名称: ${item.name}, 路径: ${item.path}`)
      console.log(`[菜单过滤] 当前用户部门: "${department}" (类型: ${typeof department})`)
      console.log(`[菜单过滤] 需要部门: "人事部"`)
      hasDepartmentPermission = department === '人事部'
      console.log(`[菜单过滤] 人员管理权限检查结果: ${hasDepartmentPermission}`)
      if (!hasDepartmentPermission) {
        console.log(`[菜单过滤] 非人事部用户，隐藏人员管理菜单`)
        return acc // 直接返回，不添加此菜单项
      }
    }

    const hasPermission = hasRolePermission && hasDepartmentPermission

    if (hasPermission) {
      const filteredItem = { ...item }
      if (filteredItem.children?.length) {
        filteredItem.children = filterMenuByRolesAndDepartment(filteredItem.children, roles, department)
      }
      acc.push(filteredItem)
    } else {
      // 如果是人员管理菜单但没有权限，记录日志
      if (isPersonnelMenu) {
        console.log(`[菜单过滤] 人员管理菜单被过滤掉`)
      }
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
  setRouteRegistered(false)
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
