import { upgradeLogList } from '@/mock/upgradeLog'
import { RoutesAlias } from '../routesAlias'
import { MenuListType } from '@/types/menu'
import { WEB_LINKS } from '@/utils/links'

/**
 * 菜单列表、异步路由
 *
 * 支持两种模式:
 * 1. 前端静态配置 - 直接使用本文件中定义的路由配置
 * 2. 后端动态配置 - 后端返回菜单数据，前端解析生成路由
 *
 * 菜单标题（title）:
 * 可以是 i18n 的 key，也可以是字符串，比如：'用户列表'
 */
export const asyncRoutes: MenuListType[] = [
  {
    id: 0,
    path: '/',
    name: 'Root',
    component: 'index/index', // 主布局
    meta: { title: '主布局', keepAlive: false },
    children: [
      {
        id: 1,
        name: 'Workbench',
        path: 'workbench',
        component: 'dashboard/console/index',
        meta: { title: '工作台', keepAlive: true, icon: 'el-icon-s-home' }
      },
      {
        id: 6,
        name: 'SmartAssistant',
        path: 'smart-assistant',
        component: 'smart-assistant/index',
        meta: { title: '智能助手',  keepAlive: true, icon: 'el-icon-user-solid' }
      },
      {
        id: 7,
        name: 'ChatRoom',
        path: 'chat-room',
        component: 'chatroom/index',
        meta: { title: '聊天室', keepAlive: true, icon: 'el-icon-message' }
      },
      {
        id: 9,
        name: 'SmartDoc',
        path: 'smart-doc',
        component: 'smart-doc/index',
        meta: { title: '智能文档',  keepAlive: true, icon: 'el-icon-document' }
      },
      {
        id: 10,
        name: 'SmartSchedule',
        path: 'smart-schedule',
        component: 'smart-schedule/index',
        meta: { title: '智能会议',  keepAlive: true, icon: 'el-icon-date' }
      },
      {
        id: 11,
        name: 'Knowledge',
        path: 'knowledge',
        component: 'knowledge/index',
        meta: { title: '知识库',  keepAlive: true, icon: 'el-icon-collection' }
      },
      {
        id: 12,
        name: 'Meetings',
        path: 'meetings',
        component: 'meetings/index',
        meta: { title: '会议管理',  keepAlive: true, icon: 'el-icon-s-flag' }
      },
      {
        id: 13,
        name: 'UserCenter',
        path: 'system/user-center',
        component: 'system/UserCenter',
        meta: {
          title: '个人中心',
          keepAlive: true,
          icon: 'el-icon-user'
        }
      }
    ]
  },
  {
    id: 8,
    path: '/system',
    name: 'System',
    component: RoutesAlias.Home,
    meta: {
      title: 'menus.system.title',
      icon: '&#xe7b9;',
      keepAlive: false,
      roles: ['R_SUPER', 'R_ADMIN']
    },
    children: [
      {
        id: 41,
        path: 'user',
        name: 'User',
        component: RoutesAlias.User,
        meta: {
          title: 'menus.system.user',
          keepAlive: true,
          roles: ['R_SUPER', 'R_ADMIN']
        }
      },
      {
        id: 42,
        path: 'role',
        name: 'Role',
        component: RoutesAlias.Role,
        meta: {
          title: 'menus.system.role',
          keepAlive: true,
          roles: ['R_SUPER']
        }
      },
      {
        id: 43,
        path: 'user-center',
        name: 'UserCenter',
        component: RoutesAlias.UserCenter,
        meta: {
          title: 'menus.system.userCenter',
          isHide: true,
          keepAlive: true,
          isHideTab: true
        }
      },
      {
        id: 44,
        path: 'menu',
        name: 'Menus',
        component: RoutesAlias.Menu,
        meta: {
          title: 'menus.system.menu',
          keepAlive: true,
          roles: ['R_SUPER'],
          authList: [
            {
              id: 441,
              title: '新增',
              auth_mark: 'add'
            },
            {
              id: 442,
              title: '编辑',
              auth_mark: 'edit'
            },
            {
              id: 443,
              title: '删除',
              auth_mark: 'delete'
            }
          ]
        }
      },
 
      {
        id: 46,
        path: 'nested',
        name: 'Nested',
        component: '',
        meta: {
          title: 'menus.system.nested',
          keepAlive: true
        },
        children: [
          {
            id: 461,
            path: 'menu1',
            name: 'NestedMenu1',
            component: RoutesAlias.NestedMenu1,
            meta: {
              title: 'menus.system.menu1',
              icon: '&#xe676;',
              keepAlive: true
            }
          },
          {
            id: 462,
            path: 'menu2',
            name: 'NestedMenu2',
            component: '',
            meta: {
              title: 'menus.system.menu2',
              icon: '&#xe676;',
              keepAlive: true
            },
            children: [
              {
                id: 4621,
                path: 'menu2-1',
                name: 'NestedMenu2-1',
                component: RoutesAlias.NestedMenu21,
                meta: {
                  title: 'menus.system.menu21',
                  icon: '&#xe676;',
                  keepAlive: true
                }
              }
            ]
          },
          {
            id: 463,
            path: 'menu3',
            name: 'NestedMenu3',
            component: '',
            meta: {
              title: 'menus.system.menu3',
              icon: '&#xe676;',
              keepAlive: true
            },
            children: [
              {
                id: 4631,
                path: 'menu3-1',
                name: 'NestedMenu3-1',
                component: RoutesAlias.NestedMenu31,
                meta: {
                  title: 'menus.system.menu31',
                  icon: '&#xe676;',
                  keepAlive: true
                }
              },
              {
                id: 4632,
                path: 'menu3-2',
                name: 'NestedMenu3-2',
                component: '',
                meta: {
                  title: 'menus.system.menu32',
                  icon: '&#xe676;',
                  keepAlive: true
                },
                children: [
                  {
                    id: 46321,
                    path: 'menu3-2-1',
                    name: 'NestedMenu3-2-1',
                    component: RoutesAlias.NestedMenu321,
                    meta: {
                      title: 'menus.system.menu321',
                      icon: '&#xe676;',
                      keepAlive: true
                    }
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  },
  {
    id: 13,
    name: '',
    path: '',
    component: RoutesAlias.Home,
    meta: {
      title: 'menus.help.title',
      icon: '&#xe719;',
      keepAlive: false,
      roles: ['R_SUPER', 'R_ADMIN']
    },
    children: [
      {
        id: 91,
        path: '',
        name: 'Document',
        meta: {
          title: 'menus.help.document',
          link: WEB_LINKS.DOCS,
          isIframe: false,
          keepAlive: false
        }
      }
    ]
  },
]
