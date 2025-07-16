<template>
  <template v-for="item in list">
    <el-sub-menu v-if="item.children" :index="item.path" :key="item.path + '-submenu'">
      <template #title>
        <MenuItemIcon :icon="item.meta.icon" />
        <span>{{ $t(item.meta.title) }}</span>
      </template>
      <SidebarSubmenu :list="item.children" />
    </el-sub-menu>
    <el-menu-item v-else :index="item.path" :key="item.path + '-item'" @click="goPage(item)">
      <MenuItemIcon :icon="item.meta.icon" />
      <span>{{ $t(item.meta.title) }}</span>
    </el-menu-item>
  </template>
</template>

<script setup lang="ts">
  import { computed, h, defineComponent } from 'vue'
  import type { MenuListType } from '@/types/menu'
  import { formatMenuTitle } from '@/router/utils/utils'
  import { handleMenuJump } from '@/utils/jump'
  // 引入 Element Plus 图标
  import { HomeFilled, UserFilled, Document, Calendar, Collection, Flag, User, Message, OfficeBuilding } from '@element-plus/icons-vue'
  import { ElIcon } from 'element-plus'

  // 类型定义
  interface Props {
    title?: string
    list?: MenuListType[]
    theme?: {
      iconColor?: string
    }
    isMobile?: boolean
    level?: number
  }

  // Props定义
  const props = withDefaults(defineProps<Props>(), {
    title: '',
    list: () => [],
    theme: () => ({}),
    isMobile: false,
    level: 0
  })

  // Emits定义
  const emit = defineEmits<{
    (e: 'close'): void
  }>()

  // 计算属性
  const filteredMenuItems = computed(() => filterRoutes(props.list))

  // 跳转页面
  const goPage = (item: MenuListType) => {
    closeMenu()
    handleMenuJump(item)
  }

  // 关闭菜单
  const closeMenu = () => emit('close')

  // 只保留一级菜单项
  const filterRoutes = (items: MenuListType[]): MenuListType[] => {
    return items.filter((item) => !item.meta.isHide)
  }

  const MenuItemIcon = defineComponent({
    name: 'MenuItemIcon',
    props: {
      icon: String,
      color: String
    },
    setup(props) {
      const iconMap = {
        'el-icon-s-home': HomeFilled,
        'el-icon-user-solid': UserFilled,
        'el-icon-document': Document,
        'el-icon-date': Calendar,
        'el-icon-collection': Collection,
        'el-icon-s-flag': Flag,
        'el-icon-user': User,
        'el-icon-message': Message,
        'el-icon-office-building': OfficeBuilding
      } as Record<string, any>
      if (props.icon && iconMap[props.icon as string]) {
        return () => h(
          ElIcon,
          { class: 'menu-icon', style: props.color ? { color: props.color } : undefined },
          { default: () => h(iconMap[props.icon as string]) }
        )
      }
      return () => h('i', {
        class: 'menu-icon iconfont-sys',
        style: props.color ? { color: props.color } : undefined,
        innerHTML: props.icon
      })
    }
  })
</script>
