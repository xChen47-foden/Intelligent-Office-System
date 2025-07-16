import type { App } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { staticRoutes } from './routes/staticRoutes'
import { configureNProgress } from './utils/utils'
import { setupBeforeEachGuard } from './guards/beforeEach'
import { setupAfterEachGuard } from './guards/afterEach'

// 创建路由实例
export const router = createRouter({
  history: createWebHashHistory(),
  routes: staticRoutes, // 静态路由
  scrollBehavior: () => ({ left: 0, top: 0 }) // 滚动行为
})

// 调试：打印所有注册的路由
console.log('📋 已注册的静态路由:', router.getRoutes().map(r => ({ name: r.name, path: r.path })))

// 初始化路由
export function initRouter(app: App<Element>): void {
  configureNProgress() // 顶部进度条
  setupBeforeEachGuard(router) // 路由前置守卫
  setupAfterEachGuard(router) // 路由后置守卫
  app.use(router)
}
