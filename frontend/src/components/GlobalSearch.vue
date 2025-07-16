<template>
  <div class="global-search">
    <el-input
      v-model="keyword"
      placeholder="搜索文档、消息、联系人..."
      @input="onInput"
      @keydown.enter="onSearch"
      @keydown.esc="clearSearch"
      @focus="onFocus"
      clearable
      size="large"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <div v-if="showDropdown" class="search-dropdown">
      <div v-if="loading" class="search-loading">加载中...</div>
      <div v-else-if="isEmpty">无匹配结果</div>
      <template v-else>
        <div v-for="group in groupedResults" :key="group.type" class="search-group">
          <div class="group-title">{{ group.label }}</div>
          <div
            v-for="item in group.items"
            :key="item.id"
            class="search-item"
            @click="goToDetail(item)"
          >
            <div class="item-content">
              <span class="item-title" v-html="highlight(item.title, keyword)"></span>
              <span v-if="item.department" class="item-meta">{{ item.department }}</span>
              <span v-if="item.summary" class="item-meta">{{ item.summary }}</span>
            </div>
            <div v-if="item.type === 'doc'" class="item-type">文档</div>
            <div v-if="item.type === 'message'" class="item-type">消息</div>
            <div v-if="item.type === 'contact'" class="item-type">联系人</div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElInput, ElIcon } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { globalSearch } from '@/api/search'
import { useRouter } from 'vue-router'

const keyword = ref('')
const results = ref<any>({ docs: [], messages: [], contacts: [] })
const loading = ref(false)
const showDropdown = ref(false)
const router = useRouter()

// 防抖搜索
let searchTimeout: NodeJS.Timeout
const onInput = async () => {
  if (!keyword.value) {
    showDropdown.value = false
    return
  }
  
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    loading.value = true
    showDropdown.value = true
    try {
      const res = await globalSearch(keyword.value)
      console.log('搜索结果:', res)
      results.value = res || { docs: [], messages: [], contacts: [] }
    } catch (error) {
      console.error('搜索失败:', error)
      results.value = { docs: [], messages: [], contacts: [] }
    } finally {
      loading.value = false
    }
  }, 300)
}

const onSearch = () => {
  if (keyword.value && results.value.docs?.length > 0) {
    // 如果有搜索结果，跳转到第一个结果
    goToDetail(results.value.docs[0])
  } else if (keyword.value && results.value.messages?.length > 0) {
    goToDetail(results.value.messages[0])
  } else if (keyword.value && results.value.contacts?.length > 0) {
    goToDetail(results.value.contacts[0])
  }
}

const goToDetail = (item: any) => {
  console.log('跳转到详情页面:', item)
  try {
    if (item.type === 'doc') {
      router.push('/knowledge')
    } else if (item.type === 'message') {
      router.push('/chat-room')
    } else if (item.type === 'contact') {
      router.push('/') // 跳转到工作台页面
    }
    showDropdown.value = false
    keyword.value = ''
  } catch (error) {
    console.error('路由跳转失败:', error)
  }
}

const highlight = (text: string, key: string) => {
  if (!key) return text
  return text.replace(new RegExp(key, 'gi'), (m) => `<span class='highlight'>${m}</span>`)
}

const groupedResults = computed(() => [
  { type: 'docs', label: '文档', items: results.value.docs || [] },
  { type: 'messages', label: '消息', items: results.value.messages || [] },
  { type: 'contacts', label: '联系人', items: results.value.contacts || [] }
].filter(g => g.items.length > 0))

const isEmpty = computed(() =>
  !loading.value &&
  (!results.value.docs?.length && !results.value.messages?.length && !results.value.contacts?.length)
)

// 点击外部关闭搜索下拉框
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (showDropdown.value && !target?.closest?.('.global-search')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 清空搜索
const clearSearch = () => {
  keyword.value = ''
  showDropdown.value = false
  results.value = { docs: [], messages: [], contacts: [] }
}

// 聚焦事件
const onFocus = () => {
  if (keyword.value) {
    showDropdown.value = true
  }
}
</script>

<style scoped lang="scss">
.global-search {
  width: 400px;
  position: relative;
  .search-dropdown {
    position: absolute;
    top: 44px;
    left: 0;
    width: 100%;
    background: #fff;
    border: 1px solid #eee;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    z-index: 1000;
    max-height: 400px;
    overflow-y: auto;
    .search-loading { 
      padding: 16px; 
      text-align: center; 
      color: #999; 
    }
    .group-title { 
      font-weight: bold; 
      margin: 8px 0 4px 12px; 
      color: #666; 
      font-size: 12px;
      text-transform: uppercase;
    }
    .search-item { 
      cursor: pointer; 
      padding: 8px 16px; 
      border-radius: 4px; 
      transition: background .2s;
      display: flex;
      align-items: center;
      justify-content: space-between;
      .item-content {
        flex: 1;
        .item-title {
          display: block;
          font-size: 14px;
          margin-bottom: 2px;
        }
        .item-meta {
          display: block;
          font-size: 12px;
          color: #999;
          margin-top: 2px;
        }
      }
      .item-type {
        padding: 2px 8px;
        background: #f0f0f0;
        border-radius: 12px;
        font-size: 10px;
        color: #666;
      }
    }
    .search-item:hover { 
      background: #f5f7fa; 
    }
    .highlight { 
      color: #409eff; 
      background: #e6f7ff; 
      border-radius: 2px; 
      padding: 0 2px; 
    }
  }
}
</style> 