import { MenuListType } from '@/types/menu'
import { router } from '@/router'

// 打开外部链接
export const openExternalLink = (link: string) => {
  window.open(link, '_blank')
}

/**
 * 菜单跳转
 * @param item 菜单项
 * @param jumpToFirst 是否跳转到第一个子菜单
 * @returns
 */
export const handleMenuJump = (item: MenuListType, jumpToFirst: boolean = false) => {
  // 处理外部链接
  const { link, isIframe } = item.meta
  if (link && !isIframe) {
    return openExternalLink(link)
  }

  // 只要是“个人中心”，都强制跳转到绝对路径
  let path = item.path
  if (
    path === 'user-center' ||
    path === '/user-center' ||
    path === 'system/user-center' ||
    path === '/system/user-center' ||
    path.endsWith('/user-center')
  ) {
    path = '/system/user-center'
  }
  // 跳转时一定要用绝对路径
  if (!path.startsWith('/')) {
    path = '/' + path
  }

  // 如果不需要跳转到第一个子菜单，或者没有子菜单，直接跳转当前路径
  if (!jumpToFirst || !item.children?.length) {
    return router.push(path)
  }

  // 获取第一个可见的子菜单，如果没有则取第一个子菜单
  const firstChild = item.children.find((child) => !child.meta.isHide) || item.children[0]

  // 如果第一个子菜单是外部链接则打开新窗口
  if (firstChild.meta?.link) {
    return openExternalLink(firstChild.meta.link)
  }

  // 跳转到子菜单路径
  router.push(firstChild.path)
}
