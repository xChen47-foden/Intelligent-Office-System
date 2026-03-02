<template>
  <div class="assistant-layout">
    <aside class="session-list">
      <div class="session-header">
        <span>历史对话</span>
        <el-button size="small" @click="createNewSession">新建会话</el-button>
      </div>
      <ul v-if="sessions.length > 0">
        <li
          v-for="s in sessions"
          :key="s.id"
          :class="{active: s.id === currentSessionId}"
          @click="selectSession(s.id)"
          class="session-item-flex"
        >
          <div class="session-info">
            <div class="session-title">{{ s.title || '新会话' }}</div>
            <div class="session-preview">{{ s.history[s.history.length-1]?.content?.slice(0, 20) }}</div>
          </div>
          <el-button type="text" size="small" class="delete-btn" @click.stop="confirmDeleteSession(s.id)">删除</el-button>
        </li>
      </ul>
      <div v-else class="empty-sessions">
        <div class="empty-text">暂无对话</div>
        <div class="empty-hint">点击"新建会话"开始对话</div>
      </div>
    </aside>
    <section class="chat-main">
      <div class="chat-header">
        <span>智能助手</span>
        <div class="header-actions" v-if="sessions.length > 0 && currentSessionId">
          <el-button size="small" @click="clearHistoryKeepFirst" title="清理对话，保留第一句">
            <el-icon><Delete /></el-icon>
            重置对话
          </el-button>
        </div>
      </div>
      <div class="chat-history" ref="historyRef">
        <div v-if="sessions.length === 0 && !isStreaming" class="empty-chat">
          <div class="empty-chat-icon">💬</div>
          <div class="empty-chat-text">暂无对话</div>
          <div class="empty-chat-hint">开始与智能助手对话吧</div>
        </div>
        <div v-for="(msg, idx) in history" :key="idx" :class="['chat-msg', msg.from === 'user' ? 'right' : 'left']">
          <el-avatar :size="32" :src="msg.avatar" />
          <div class="msg-content">
            <div class="msg-text" v-html="renderMarkdown(msg.content || '')"></div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>
        <div v-if="isStreaming && streamingContent" class="chat-msg left">
          <el-avatar :size="32" :src="botAvatar" />
          <div class="msg-content">
            <div class="msg-text" v-html="renderMarkdown(streamingContent || '')"></div>
            <div class="msg-time">{{ getNowTime() }}</div>
          </div>
        </div>
      </div>
      <div class="chat-input-bar" v-if="sessions.length > 0 && currentSessionId">
        <div class="input-tools">
          <el-button size="small" @click.stop="toggleEmojiPicker" style="margin-right: 8px;">
            <el-icon><ChatDotSquare /></el-icon>
          </el-button>
          <el-upload
            :action="uploadUrl"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :headers="headers"
            name="file"
            accept=".jpg,.jpeg,.png,.gif,.webp,.svg"
            style="margin-right: 8px; display: inline-block;"
            :auto-upload="true"
          >
            <template #trigger>
            <el-button size="small" title="上传图片">
              <el-icon><Picture /></el-icon>
            </el-button>
            </template>
          </el-upload>
          <el-upload
            :action="uploadUrl"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :headers="headers"
            name="file"
            accept=".doc,.docx,.pdf,.zip,.rar,.txt,.xlsx,.xls,.ppt,.pptx"
            style="display: inline-block;"
            :auto-upload="true"
          >
            <template #trigger>
            <el-button size="small" title="上传附件">
              <el-icon><Upload /></el-icon>
            </el-button>
            </template>
          </el-upload>
          <!-- 表情包选择器 -->
          <div v-if="showEmojiPicker" class="emoji-picker" @click.stop>
            <div class="emoji-grid">
              <span v-for="emoji in emojiList" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">
                {{ emoji }}
              </span>
            </div>
          </div>
        </div>
        <div class="input-main">
          <el-input
            v-model="ragQuestion"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            :placeholder="currentFileUrl ? `已选择文件：${currentFileName}，请输入问题或直接发送分析文件` : '请输入你的问题或办公需求，如\'帮我生成会议纪要\''"
            @keyup.enter="ragSearch"
          />
          <div style="display: flex; gap: 8px;">
            <el-button 
              v-if="currentFileUrl" 
              type="success" 
              @click="analyzeFile(currentFileUrl, currentFileName, ragQuestion || '')" 
              :loading="ragLoading"
            >
              分析文件
            </el-button>
          <el-button type="primary" @click="ragSearch" :loading="ragLoading">发送</el-button>
          </div>
        </div>
      </div>
    </section>
    <el-dialog v-model="deleteSessionDialogVisible" title="确认删除" width="300px">
      <span>确定要删除该会话吗？</span>
      <template #footer>
        <el-button @click="deleteSessionDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleDeleteSession">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Picture, Upload, ChatDotSquare, Delete } from '@element-plus/icons-vue'
import axios from 'axios'
import { renderMarkdown } from '@/utils/markdown'
import api from '@/utils/http'
import { aiAutoSendToAll } from '@/services/ai'
import { useUserStore } from '@/store/modules/user'
import { storeToRefs } from 'pinia'
import defaultAvatar from '@/assets/img/avatar/avatar5.jpg'
import dayjs from 'dayjs'

const userStore = useUserStore()
const { info } = storeToRefs(userStore)

// 头像URL处理函数
const getAvatarUrl = (avatar: string) => {
  if (!avatar) return defaultAvatar
  if (avatar.startsWith('http')) return avatar
  // 如果已经是/uploads/开头，直接使用，否则添加/uploads/前缀
  if (avatar.startsWith('/uploads/')) {
      return `${avatar}?t=${Date.now()}`
  }
    return `/uploads/${avatar}?t=${Date.now()}`
}

// 用户头像计算属性，自动同步用户状态
const userAvatar = computed(() => getAvatarUrl(info.value?.avatar || ''))
const botAvatar = new URL('./AI智能.png', import.meta.url).href
const avatarInput = ref<HTMLInputElement | null>(null)

function getNowTime() {
  const d = new Date()
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}

interface Message {
  id: number
  content: string
  from: 'user' | 'bot'
  time: string
  avatar?: string
  sessionId: string
  imageUrl?: string  // 图片URL，用于图片分析
}

const sessions = ref<any[]>([])
const currentSessionId = ref('')
const history = ref<Message[]>([])
const ragQuestion = ref('')
const ragLoading = ref(false)
const streamingContent = ref('')
const isStreaming = ref(false)
const deleteSessionDialogVisible = ref(false)
const sessionIdToDelete = ref('')
const uploadUrl = '/api/assistant/upload'
const currentImageUrl = ref('')  // 当前待分析的图片URL
const currentFileUrl = ref('')  // 当前待分析的文件URL
const currentFileName = ref('')  // 当前待分析的文件名

// 使用计算属性获取最新的认证头
const headers = computed(() => {
  const token = userStore.accessToken || localStorage.getItem('token')
  return token ? { Authorization: 'Bearer ' + token } : {}
})

// 表情包相关
const showEmojiPicker = ref(false)
const emojiList = [
  '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '🫠', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🫢', '🫣', '🤫', '🤔', '🫡', '🤐', '🤨', '😐', '😑', '😶', '😶‍🌫️', '😏', '😒', '🙄', '😬', '😮‍💨', '🤥', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶', '🥴', '😵', '😵‍💫', '🤯', '🤠', '🥳', '🥸', '😎', '🤓', '🧐', '😕', '😟', '🙁', '☹️', '😮', '😯', '😲', '😳', '🥺', '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱', '😖', '😣', '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬', '😈', '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽', '👾', '🤖', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👏', '🙌', '🤲', '🤝', '🙏', '💪', '💋', '👀', '👄', '🫦', '👅', '💃', '🕺', '🎉', '🎊', '🎈', '🎁', '🎂', '🍰', '🧁', '🍭', '🍬', '🍫', '🍪', '🍩', '🍯', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🍾', '🥤', '☕', '🍵', '🥛', '🍼', '🥨', '🍕', '🍔', '🍟', '🌭', '🥪', '🌮', '🌯', '🥙', '🧆', '🥚', '🍳', '🥘', '🍲', '🥗', '🍿', '🧈', '🧀', '🥨', '🥖', '🍞', '🥐', '🥯', '🧇', '🥞', '🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔', '🍠', '🫘', '🥜', '🌰', '🥇', '🥈', '🥉', '🏆', '🏅', '🎖️', '🏵️', '🎗️', '🎫', '🎟️', '🎪', '🎭', '🎨', '🎬', '🎤', '🎧', '🎼', '🎵', '🎶', '🎹', '🥁', '🎷', '🎺', '🎸', '🪕', '🎻', '🎲', '♠️', '♥️', '♦️', '♣️', '♟️', '🃏', '🀄', '🎴', '🎯', '🎳', '🎮', '🎰', '🧩'
]

function createNewSession() {
  const id = Date.now().toString()
  const newSession = {
    id,
    title: '新会话',
    created: new Date().toLocaleString(),
    history: []
  }
  sessions.value.unshift(newSession)
  currentSessionId.value = id
  history.value = newSession.history
  
  // 立即保存新会话到localStorage
  localStorage.setItem('deepseek_sessions', JSON.stringify(sessions.value))
}
function selectSession(id: string) {
  const session = sessions.value.find(s => s.id === id)
  if (session) {
    currentSessionId.value = id
    history.value = session.history
  }
}
function clearHistory() {
  history.value.length = 0
  updateSessionHistory()
}

// 清理历史对话，只保留第一句话并同步头像
function clearHistoryKeepFirst() {
  if (history.value.length > 0) {
    // 找到第一条机器人消息
    const firstBotMessage = history.value.find(msg => msg.from === 'bot')
    if (firstBotMessage) {
      // 只保留第一条机器人消息
      history.value = [firstBotMessage]
      // 同步头像
      firstBotMessage.avatar = botAvatar
    } else {
      // 如果没有机器人消息，清空所有历史
      history.value = []
    }
    
    // 更新当前会话的历史
    updateSessionHistory()
    
    // 立即保存到localStorage
    localStorage.setItem('deepseek_sessions', JSON.stringify(sessions.value))
    
    ElMessage.success('已清理历史对话，保留第一句话')
  }
}
function updateSessionHistory() {
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) session.history = [...history.value]
}
onMounted(() => {
  // 只在需要时初始化用户状态
  if (!userStore.accessToken && !localStorage.getItem('token')) {
    userStore.initState()
  }
  
  // 检查token
  const token = userStore.accessToken || localStorage.getItem('token')
  console.log('智能助手页面token:', token ? '已存在' : '不存在')
  
  // 确保用户头像稳定
  const currentAvatar = userAvatar.value
  
  const saved = localStorage.getItem('deepseek_sessions')
  if (saved) {
    try {
      sessions.value = JSON.parse(saved)
      sessions.value.forEach(session => {
        session.history.forEach((msg: any) => {
          // 强制更新所有用户消息的头像为当前最新头像
          if (msg.from === 'user') {
            msg.avatar = currentAvatar
          } else if (msg.from === 'bot') {
            msg.avatar = botAvatar
          }
          if (!msg.time) msg.time = getNowTime()
          // 确保content是字符串
          if (msg.content === null || msg.content === undefined) {
            msg.content = ''
          } else {
            msg.content = String(msg.content)
          }
        })
      })
      if (sessions.value.length) {
        currentSessionId.value = sessions.value[0].id
        history.value = sessions.value[0].history
      }
    } catch (error) {
      console.error('加载会话数据失败:', error)
      createNewSession()
    }
  } else {
    createNewSession()
  }
  
  // 添加点击外部关闭表情包选择器的监听器
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  // 移除点击外部关闭表情包选择器的监听器
  document.removeEventListener('click', handleOutsideClick)
})

// 强制更新所有用户消息头像的函数
function forceUpdateUserAvatars() {
  const currentAvatar = userAvatar.value
  if (!currentAvatar || sessions.value.length === 0) return
  
  console.log('强制更新头像:', currentAvatar)
  
  // 更新当前会话的历史记录
  history.value.forEach((msg: any) => {
    if (msg.from === 'user') msg.avatar = currentAvatar
  })
  
  // 更新所有会话的历史记录
  sessions.value.forEach((session: any) => {
    session.history.forEach((msg: any) => {
      if (msg.from === 'user') msg.avatar = currentAvatar
    })
  })
  
  // 立即保存到localStorage
  localStorage.setItem('deepseek_sessions', JSON.stringify(sessions.value))
}

// 监听用户头像变化，自动更新历史消息中的头像
watch(userAvatar, (newAvatar, oldAvatar) => {
  // 只要头像有变化就更新，确保同步
  if (newAvatar && newAvatar !== oldAvatar && sessions.value.length > 0) {
    console.log('用户头像已更新:', newAvatar)
    forceUpdateUserAvatars()
  }
})

// 监听用户信息变化，强制同步头像
watch(() => info.value?.avatar, (newAvatar) => {
  if (newAvatar && sessions.value.length > 0) {
    console.log('用户信息中的头像更新:', newAvatar)
    forceUpdateUserAvatars()
  }
})
watch([sessions, currentSessionId], () => {
  localStorage.setItem('deepseek_sessions', JSON.stringify(sessions.value))
}, { deep: true })
// 智能体意图识别
function analyzeIntent(message: string) {
  const msg = message.toLowerCase()
  
  // 日程相关 - 先识别查看意图，避免误识别为添加
  // 查看任务/日程的识别（优先级更高）
  if ((msg.includes('查看') && (msg.includes('任务') || msg.includes('日程') || msg.includes('安排'))) ||
      msg.includes('今天有什么') || msg.includes('今天有哪些') || msg.includes('今日有什么') || msg.includes('今日有哪些') ||
      msg.includes('明天有什么') || msg.includes('明天有哪些') || msg.includes('明日有什么') || msg.includes('明日有哪些') ||
      msg.includes('后天有什么') || msg.includes('后天有哪些') ||
      msg.includes('查看今天') || msg.includes('查看今日') || msg.includes('查看明天') || msg.includes('查看明日') ||
      msg.includes('查看后天') || msg.includes('我的安排') || msg.includes('今日安排') || msg.includes('日程表') ||
      (msg.includes('日程安排') && !msg.includes('添加') && !msg.includes('创建') && !msg.includes('新建')) ||
      /(今天|明天|后天|下周|\d+月\d+[日号]).*?(有什么|有哪些|任务|日程|安排)/.test(msg)) {
    return { type: 'schedule_view', content: message }
  }
  
  // 会议相关 - 优先识别添加会议（必须在添加日程之前）
  if ((msg.includes('添加会议') || msg.includes('创建会议') || msg.includes('新建会议') ||
      msg.includes('安排会议') || msg.includes('开个会') || msg.includes('组织会议') || msg.includes('召开会议') ||
      msg.includes('会议预约') || msg.includes('预约会议') || msg.includes('帮我添加会议') || msg.includes('帮我创建会议')) ||
      // 如果明确提到"会议"且包含时间信息，优先识别为会议
      (msg.includes('会议') && (msg.includes('添加') || msg.includes('创建') || msg.includes('新建') || msg.includes('安排')) &&
       (msg.includes('时间') || msg.includes('点') || msg.includes('明天') || msg.includes('今天') || msg.includes('下午') || msg.includes('上午') || msg.includes('晚上')))) {
    return { type: 'meeting_create', content: message }
  }
  
  // 文档相关 - 更智能的识别
  if (msg.includes('读取文档') || msg.includes('打开文档') || msg.includes('查看文档') ||
      msg.includes('文档内容') || msg.includes('看看文档') || msg.includes('文档详情')) {
    return { type: 'doc_read', content: message }
  }
  
  if (msg.includes('创建文档') || msg.includes('新建文档') || msg.includes('写文档') ||
      msg.includes('新文档') || msg.includes('建个文档')) {
    return { type: 'doc_create', content: message }
  }
  
  if (msg.includes('搜索文档') || msg.includes('找文档') || msg.includes('查找文档') ||
      msg.includes('文档搜索') || msg.includes('找找文档')) {
    return { type: 'doc_search', content: message }
  }
  
  // 添加日程的识别（需要明确包含添加/创建等关键词，且不是会议）
  if ((msg.includes('添加') || msg.includes('新建') || msg.includes('创建') || msg.includes('安排') || msg.includes('提醒我') || msg.includes('记住')) &&
      (msg.includes('日程') || msg.includes('任务') || msg.includes('提醒') || msg.includes('日历')) ||
      msg.includes('添加到日历') || msg.includes('加到日历') ||
      // 如果提到"开会"但没有明确说"会议"，识别为任务
      (msg.includes('开会') && !msg.includes('会议') && (msg.includes('时间') || msg.includes('点') || msg.includes('明天') || msg.includes('今天') || msg.includes('下午') || msg.includes('上午'))) ||
      // 纯时间+任务关键词，识别为任务
      (/\d+点.*?(活动|任务|提醒)/.test(msg) && !msg.includes('会议')) ||
      /(今天|明天|后天|下周|上午|下午|晚上).*?(活动|提醒)/.test(msg)) {
    return { type: 'schedule_add', content: message }
  }
  
  if (msg.includes('查看会议') || msg.includes('今天会议') || msg.includes('会议安排') ||
      msg.includes('会议列表') || msg.includes('我的会议') || msg.includes('会议日程')) {
    return { type: 'meeting_view', content: message }
  }
  
  // 知识库相关 - 更智能的识别
  if (msg.includes('搜索知识库') || msg.includes('查询知识库') || msg.includes('知识库') ||
      msg.includes('知识搜索') || msg.includes('查找知识') || msg.includes('知识查询')) {
    return { type: 'knowledge_search', content: message }
  }
  
  // 联系人相关 - 更智能的识别
  if (msg.includes('添加联系人') || msg.includes('新增联系人') || msg.includes('加联系人') ||
      msg.includes('新联系人') || msg.includes('联系人添加')) {
    return { type: 'contact_add', content: message }
  }
  
  if (msg.includes('查看联系人') || msg.includes('联系人列表') || msg.includes('我的联系人') ||
      msg.includes('联系人查看') || msg.includes('通讯录')) {
    return { type: 'contact_view', content: message }
  }
  
  // 批量操作 - 更智能的识别
  if (msg.includes('给所有联系人发') || msg.includes('群发') || msg.includes('批量发送') ||
      msg.includes('全员发送') || msg.includes('发给所有人')) {
    return { type: 'batch_message', content: message }
  }
  
  // 问候和确认类 - 智能回复
  if (msg.includes('你好') || msg.includes('您好') || msg.includes('hi') || msg.includes('hello')) {
    return { type: 'greeting', content: message }
  }
  
  if ((msg.includes('是的') || msg.includes('好的') || msg.includes('确定') || msg.includes('可以') || 
       msg.includes('需要') || msg.includes('要的') || msg.includes('帮我')) && 
      (msg.includes('添加') || msg.includes('安排') || msg.includes('提醒') || msg.includes('日历'))) {
    return { type: 'schedule_confirm', content: message }
  }
  
  return { type: 'chat', content: message }
}

// 智能体操作函数
async function executeAgentAction(intent: { type: string, content: string }) {
  const { type, content } = intent
  
  switch (type) {
    case 'schedule_add':
      return await addScheduleAction(content)
    case 'schedule_view':
      return await viewScheduleAction(content)
    case 'schedule_confirm':
      return await handleScheduleConfirm(content)
    case 'doc_read':
      return await readDocumentAction(content)
    case 'doc_create':
      return await createDocumentAction(content)
    case 'doc_search':
      return await searchDocumentAction(content)
    case 'meeting_create':
      return await createMeetingAction(content)
    case 'meeting_view':
      return await viewMeetingAction()
    case 'knowledge_search':
      return await searchKnowledgeAction(content)
    case 'contact_add':
      return await addContactAction(content)
    case 'contact_view':
      return await viewContactAction()
    case 'batch_message':
      return await batchMessageAction(content)
    case 'greeting':
      return handleGreeting(content)
    default:
      return null
  }
}

// 添加日程
async function addScheduleAction(content: string) {
  try {
    // 解析日程信息
    const scheduleInfo = parseScheduleInfo(content)
    
    // 调试日志
    console.log('解析日程信息:', {
      原始内容: content,
      任务名: scheduleInfo.title,
      时间: scheduleInfo.time,
      日期: scheduleInfo.date
    })
    
    const response = await api.post({
      url: '/api/today-tasks',
      data: {
        content: scheduleInfo.title,
        time: scheduleInfo.time,
        date: scheduleInfo.date,
        type: scheduleInfo.type || 'bg-primary',
        endDate: scheduleInfo.endDate || ''
      }
    }) as any
    
    if (response.code === 0) {
      return `✅ 已成功添加日程：${scheduleInfo.title}，时间：${scheduleInfo.date} ${scheduleInfo.time}`
    } else {
      return `❌ 添加日程失败：${response.msg}`
    }
  } catch (error) {
    console.error('添加日程错误:', error)
    return `❌ 添加日程时出错：${error}`
  }
}

// 解析日程信息
function parseScheduleInfo(content: string) {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  
  // 默认值
  let title = '新任务'
  let time = '09:00'
  let date = today.toISOString().split('T')[0]
  let type = 'bg-primary'
  let endDate = ''
  
  // 先提取时间信息（避免时间被当作任务名）
  let hour = 9
  let minute = 0
  let timeText = '' // 保存匹配到的时间文本，用于后续移除
  
  // 匹配时间信息 - 使用多个模式，按优先级匹配
  // 模式1: "下午3点"、"上午10点"、"晚上8点"、"下午3点30分" 等格式
  const timePattern1 = /(上午|下午|晚上|中午|凌晨|傍晚)\s*(\d{1,2})\s*[点:]?\s*(\d{0,2})\s*(?:分|分钟)?/
  const timeMatch1 = content.match(timePattern1)
  
  if (timeMatch1) {
    timeText = timeMatch1[0] // 保存完整的时间文本
    const period = timeMatch1[1]
    hour = parseInt(timeMatch1[2]) || 9
    const minuteStr = timeMatch1[3] || ''
    minute = minuteStr ? parseInt(minuteStr) : 0
    
    // 处理上午下午
    if (period === '下午' || period === '晚上' || period === '傍晚') {
      if (hour > 0 && hour < 12) {
        hour += 12
      }
    } else if (period === '上午' || period === '凌晨') {
      if (hour === 12 && period === '上午') {
        hour = 0
      }
    } else if (period === '中午') {
      hour = 12
    }
    
    // 24小时制校正
    if (hour >= 24) hour = 23
    if (hour < 0) hour = 0
    if (minute >= 60) minute = 59
  } else {
    // 模式2: "15:30"、"9:00" 等格式
    const timePattern2 = /(\d{1,2})[：:](\d{2})/
    const timeMatch2 = content.match(timePattern2)
    if (timeMatch2) {
      timeText = timeMatch2[0]
      hour = parseInt(timeMatch2[1]) || 9
      minute = parseInt(timeMatch2[2]) || 0
      if (hour >= 24) hour = 23
      if (minute >= 60) minute = 59
    } else {
      // 模式3: 纯数字时间，如 "3点"、"15点"、"3时"
      const timePattern3 = /(\d{1,2})\s*[点时]/
      const timeMatch3 = content.match(timePattern3)
      if (timeMatch3) {
        timeText = timeMatch3[0]
        hour = parseInt(timeMatch3[1]) || 9
        if (hour >= 24) hour = 23
        minute = 0
      }
    }
  }
  
  // 调试日志
  console.log('时间提取结果:', {
    原始内容: content,
    匹配到的时间文本: timeText,
    小时: hour,
    分钟: minute,
    最终时间: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
  })
  
  time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
  
  // 提取日期
  let dateText = '' // 保存日期文本，用于后续移除
  let dateMatched = false
  
  // 优先匹配具体的日期格式：X月X日、X月X号、YYYY年X月X日等
  const datePatterns = [
    { pattern: /(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'full' },  // 2026年1月6日、2026年1月6号
    { pattern: /(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'month-day' },  // 1月6日、1月6号、3月15日
    { pattern: /(\d{1,2})\/(\d{1,2})/, type: 'slash' },  // 1/6、3/15（月/日格式）
    { pattern: /(\d{4})-(\d{1,2})-(\d{1,2})/, type: 'dash' },  // 2026-01-06
    { pattern: /(\d{4})\.(\d{1,2})\.(\d{1,2})/, type: 'dot' }  // 2026.01.06
  ]
  
  for (const { pattern, type } of datePatterns) {
    const match = pattern.exec(content)
    if (match) {
      dateText = match[0]
      let year: number, month: number, day: number
      
      if (type === 'full') {
        // 2026年1月6日格式
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      } else if (type === 'month-day') {
        // 1月6日格式
        const currentYear = dayjs().year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        // 如果日期已过，可能是明年的日期
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(dayjs(), 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'slash') {
        // 1/6格式（月/日）
        const currentYear = dayjs().year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        // 如果日期已过，可能是明年的日期
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(dayjs(), 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'dash' || type === 'dot') {
        // 2026-01-06 或 2026.01.06格式
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      }
      
      // 验证日期有效性
      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        try {
          const parsedDate = dayjs(`${year}-${month}-${day}`)
          if (parsedDate.isValid()) {
            date = parsedDate.format('YYYY-MM-DD')
            dateMatched = true
            break
          }
        } catch (e) {
          console.error('日期解析失败:', e)
        }
      }
    }
  }
  
  // 如果没有匹配到具体日期，再匹配相对日期
  if (!dateMatched) {
    if (content.includes('明天')) {
      date = tomorrow.toISOString().split('T')[0]
      dateText = '明天'
      dateMatched = true
    } else if (content.includes('后天')) {
      const dayAfterTomorrow = new Date(today)
      dayAfterTomorrow.setDate(today.getDate() + 2)
      date = dayAfterTomorrow.toISOString().split('T')[0]
      dateText = '后天'
      dateMatched = true
    } else if (content.includes('下周')) {
      const nextWeek = new Date(today)
      nextWeek.setDate(today.getDate() + 7)
      date = nextWeek.toISOString().split('T')[0]
      dateText = '下周'
      dateMatched = true
    } else if (content.includes('今天') || content.includes('今日')) {
      date = today.toISOString().split('T')[0]
      dateText = '今天'
      dateMatched = true
    } else if (content.includes('昨天') || content.includes('昨日')) {
      const yesterday = new Date(today)
      yesterday.setDate(today.getDate() - 1)
      date = yesterday.toISOString().split('T')[0]
      dateText = '昨天'
      dateMatched = true
    }
  }
  
  // 调试日志：日期提取结果
  console.log('日期提取结果:', {
    原始内容: content,
    匹配到的日期文本: dateText,
    是否匹配到日期: dateMatched,
    最终日期: date
  })
  
  // 从内容中移除时间和日期信息，用于提取任务标题
  let cleanContent = content
  if (timeText) {
    cleanContent = cleanContent.replace(timeText, '').trim()
  }
  if (dateText) {
    // 移除匹配到的日期模式
    cleanContent = cleanContent.replace(new RegExp(dateText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '').trim()
  }
  // 移除相对日期关键词
  cleanContent = cleanContent
    .replace(/明天|明日/g, '')
    .replace(/后天|后日/g, '')
    .replace(/大后天/g, '')
    .replace(/今天|今日/g, '')
    .replace(/昨天|昨日/g, '')
    .replace(/下周/g, '')
  // 移除年月日关键词
  cleanContent = cleanContent
    .replace(/\d{4}年/g, '')
    .replace(/\d{1,2}月/g, '')
    .replace(/\d{1,2}[日号]/g, '')
  // 移除常见的时间相关词汇
  cleanContent = cleanContent.replace(/(上午|下午|晚上|中午|点|时)/g, '').trim()
  
  // 优先尝试从"添加任务"、"帮我添加任务"等模式中提取任务名称
  const taskTitlePatterns = [
    /(?:帮我)?添加任务[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/,
    /(?:帮我)?创建任务[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/,
    /(?:帮我)?新建任务[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/,
    /(?:帮我)?安排任务[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/,
    /添加日程[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/,
    /提醒我(.+?)(?:[，。]|$)/,
    /记住(.+?)(?:[，。]|$)/,
    /安排(.+?)(?:[，。]|$)/
  ]
  
  let extractedTitle = ''
  for (const pattern of taskTitlePatterns) {
    const match = cleanContent.match(pattern)
    if (match && match[1]) {
      extractedTitle = match[1].trim()
      // 移除时间信息
      extractedTitle = extractedTitle
        .replace(/明天|明日|后天|后日|大后天|今天|今日|昨天|昨日|下周/g, '')
        .replace(/\d{4}年/g, '')
        .replace(/\d{1,2}月/g, '')
        .replace(/\d{1,2}[日号]/g, '')
        .replace(/(上午|下午|晚上|中午|凌晨|傍晚)\s*\d{1,2}\s*[点:]?\s*\d{0,2}\s*(?:分|分钟)?/g, '')
        .replace(/\d{1,2}[：:]?\d{0,2}\s*(点|时)/g, '')
        .replace(/\d{1,2}[：:]?\d{2}/g, '')
        .replace(/(上午|下午|晚上|中午|明天|后天|下周)/g, '')
        .trim()
      
      if (extractedTitle && extractedTitle.length >= 2) {
        title = extractedTitle
        break
      }
    }
  }
  
  // 如果没有从模式中提取到标题，尝试从清理后的内容中提取
  if (!title || title === '新任务') {
    // 移除"添加任务"、"帮我添加任务"等关键词
    let remainingContent = cleanContent
      .replace(/(?:帮我)?添加任务[：:]?/g, '')
      .replace(/(?:帮我)?创建任务[：:]?/g, '')
      .replace(/(?:帮我)?新建任务[：:]?/g, '')
      .replace(/(?:帮我)?安排任务[：:]?/g, '')
      .replace(/添加日程[：:]?/g, '')
      .replace(/提醒我/g, '')
      .replace(/记住/g, '')
      .replace(/安排/g, '')
      .replace(/任务/g, '') // 移除"任务"关键词，避免误识别
      .trim()
    
    // 如果剩余内容不为空，使用它作为标题
    if (remainingContent && remainingContent.length >= 2) {
      title = remainingContent
    } else {
      // 如果还是没有，尝试匹配整个清理后的内容
      const fallbackMatch = cleanContent.match(/(.+?)(?:[，。]|$)/)
      if (fallbackMatch && fallbackMatch[1]) {
        let fallbackTitle = fallbackMatch[1].trim()
        // 移除"任务"关键词
        fallbackTitle = fallbackTitle.replace(/任务/g, '').trim()
        if (fallbackTitle && fallbackTitle.length >= 2) {
          title = fallbackTitle
        }
      }
    }
  }
  
  // 如果标题仍然为空或只包含标点符号，使用默认标题
  if (!title || title.length < 2 || /^[，。、；：！？\s]+$/.test(title)) {
    title = '新任务'
  }
  
  // 提取优先级
  if (content.includes('重要') || content.includes('紧急')) {
    type = 'bg-danger'
  } else if (content.includes('提醒')) {
    type = 'bg-warning'
  } else if (content.includes('会议') || content.includes('开会')) {
    type = 'bg-info'
  }
  
  return { title, time, date, type, endDate }
}

// 解析查询日期（从消息中提取日期信息）
function parseQueryDate(content: string): string {
  const msg = content.toLowerCase()
  const today = dayjs()
  
  // 优先匹配具体的日期格式
  const datePatterns = [
    { pattern: /(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'full' },
    { pattern: /(\d{1,2})月\s*(\d{1,2})[日号]/, type: 'month-day' },
    { pattern: /(\d{1,2})\/(\d{1,2})/, type: 'slash' },
    { pattern: /(\d{4})-(\d{1,2})-(\d{1,2})/, type: 'dash' },
    { pattern: /(\d{4})\.(\d{1,2})\.(\d{1,2})/, type: 'dot' }
  ]
  
  for (const { pattern, type } of datePatterns) {
    const match = pattern.exec(content)
    if (match) {
      let year: number, month: number, day: number
      
      if (type === 'full') {
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      } else if (type === 'month-day') {
        const currentYear = today.year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(today, 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'slash') {
        const currentYear = today.year()
        year = currentYear
        month = parseInt(match[1])
        day = parseInt(match[2])
        const testDate = dayjs(`${year}-${month}-${day}`)
        if (testDate.isBefore(today, 'day')) {
          year = currentYear + 1
        }
      } else if (type === 'dash' || type === 'dot') {
        year = parseInt(match[1])
        month = parseInt(match[2])
        day = parseInt(match[3])
      }
      
      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        try {
          const parsedDate = dayjs(`${year}-${month}-${day}`)
          if (parsedDate.isValid()) {
            return parsedDate.format('YYYY-MM-DD')
          }
        } catch (e) {
          console.error('日期解析失败:', e)
        }
      }
    }
  }
  
  // 匹配相对日期
  if (msg.includes('明天') || msg.includes('明日')) {
    return today.add(1, 'day').format('YYYY-MM-DD')
  } else if (msg.includes('后天') || msg.includes('后日')) {
    return today.add(2, 'day').format('YYYY-MM-DD')
  } else if (msg.includes('大后天')) {
    return today.add(3, 'day').format('YYYY-MM-DD')
  } else if (msg.includes('下周')) {
    return today.add(7, 'day').format('YYYY-MM-DD')
  } else if (msg.includes('昨天') || msg.includes('昨日')) {
    return today.subtract(1, 'day').format('YYYY-MM-DD')
  }
  
  // 默认返回今天
  return today.format('YYYY-MM-DD')
}

// 查看日程
async function viewScheduleAction(content?: string) {
  try {
    // 解析查询日期
    const queryDate = content ? parseQueryDate(content) : dayjs().format('YYYY-MM-DD')
    const today = dayjs().format('YYYY-MM-DD')
    
    // 获取所有任务
    const taskResponse = await api.get({ url: '/api/today-tasks' }) as any
    
    // 格式化日期显示
    const dateDisplay = dayjs(queryDate).format('M月D日')
    const dateTitle = queryDate === today ? '今日' : dateDisplay
    
    let result = `📅 ${dateTitle}安排：\n\n`
    let hasContent = false
    
    // 处理任务
    if (taskResponse.code === 0 && taskResponse.tasks) {
      // 过滤指定日期的任务
      const targetTasks = taskResponse.tasks.filter((task: any) => {
        if (!task.date) return false
        // 处理不同的日期格式
        let taskDateStr = String(task.date).trim()
        if (taskDateStr.includes(' ')) {
          taskDateStr = taskDateStr.split(' ')[0]
        }
        if (taskDateStr.includes('T')) {
          taskDateStr = taskDateStr.split('T')[0]
        }
        taskDateStr = taskDateStr.slice(0, 10)
        const taskDate = dayjs(taskDateStr).format('YYYY-MM-DD')
        return taskDate === queryDate
      })
      
      if (targetTasks.length > 0) {
        hasContent = true
        result += '📋 任务：\n'
        targetTasks.forEach((task: any, index: number) => {
          const status = task.completed ? '✅' : '⏰'
          const priority = task.type === 'bg-danger' ? '🔴' : 
                          task.type === 'bg-warning' ? '🟡' : 
                          task.type === 'bg-success' ? '🟢' : '🔵'
          result += `  ${index + 1}. ${status} ${priority} ${task.content}`
          if (task.time) result += ` (${task.time})`
          result += '\n'
        })
        result += '\n'
      }
    }
    
    // 处理会议（需要从会议接口获取）
    try {
      const meetingResponse = await api.get({ 
        url: '/api/meetings/list', 
        params: { page: 1, pageSize: 100 } 
      }) as any
      
      if (meetingResponse.code === 0 && meetingResponse.data?.list) {
        const targetMeetings = meetingResponse.data.list.filter((meeting: any) => {
          if (!meeting.time) return false
          let meetingDateStr = String(meeting.time).trim()
          if (meetingDateStr.includes('T')) {
            meetingDateStr = meetingDateStr.split('T')[0]
          }
          if (meetingDateStr.includes(' ')) {
            meetingDateStr = meetingDateStr.split(' ')[0]
          }
          meetingDateStr = meetingDateStr.slice(0, 10)
          const meetingDate = dayjs(meetingDateStr).format('YYYY-MM-DD')
          return meetingDate === queryDate
        })
        
        if (targetMeetings.length > 0) {
          hasContent = true
          result += '📅 会议：\n'
          targetMeetings.forEach((meeting: any, index: number) => {
            const timeStr = meeting.time ? dayjs(meeting.time).format('HH:mm') : ''
            result += `  ${index + 1}. 📅 ${meeting.title}`
            if (timeStr) result += ` (${timeStr})`
            if (meeting.location) result += ` @ ${meeting.location}`
            result += '\n'
          })
        }
      }
    } catch (e) {
      console.error('获取会议失败:', e)
    }
    
    if (!hasContent) {
      return `📅 ${dateTitle}暂无日程安排，您可以添加新的任务或会议。`
    }
    
    return result
  } catch (error) {
    console.error('查看日程错误:', error)
    return `❌ 查看日程时出错：${error}`
  }
}

// 读取文档
async function readDocumentAction(content: string) {
  try {
    // 提取文档名称或ID
    const docName = extractDocumentName(content)
    
    // 搜索文档
    const response = await api.get({
      url: '/api/doc/search',
      params: { q: docName, page: 1, size: 10 }
    })
    
    if (response.total > 0) {
      const doc = response.data[0]
      const summary = doc.content.substring(0, 200) + (doc.content.length > 200 ? '...' : '')
      return `📄 文档《${doc.filename}》内容预览：\n\n${summary}\n\n如需查看完整内容，请前往智能文档页面。`
    } else {
      return `❌ 未找到名为"${docName}"的文档`
    }
  } catch (error) {
    return `❌ 读取文档时出错：${error}`
  }
}

// 提取文档名称
function extractDocumentName(content: string) {
  const patterns = [
    /读取文档[：:]?(.+?)(?:[，。]|$)/,
    /打开文档[：:]?(.+?)(?:[，。]|$)/,
    /查看文档[：:]?(.+?)(?:[，。]|$)/,
    /文档[：:]?(.+?)(?:[，。]|$)/
  ]
  
  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match) {
      return match[1].trim()
    }
  }
  
  return '会议'  // 默认搜索关键词
}

// 搜索文档
async function searchDocumentAction(content: string) {
  try {
    const keyword = extractSearchKeyword(content)
    
    const response = await api.get({
      url: '/api/doc/search',
      params: { q: keyword, page: 1, size: 5 }
    })
    
    if (response.total > 0) {
      let result = `🔍 找到 ${response.total} 个相关文档：\n\n`
      response.data.forEach((doc, index) => {
        result += `${index + 1}. 📄 ${doc.filename}\n`
        result += `   上传时间：${doc.upload_time}\n`
        if (doc.content) {
          const preview = doc.content.substring(0, 50) + '...'
          result += `   预览：${preview}\n`
        }
        result += '\n'
      })
      return result
    } else {
      return `❌ 未找到包含"${keyword}"的文档`
    }
  } catch (error) {
    return `❌ 搜索文档时出错：${error}`
  }
}

// 提取搜索关键词
function extractSearchKeyword(content: string) {
  const patterns = [
    /搜索文档[：:]?(.+?)(?:[，。]|$)/,
    /找文档[：:]?(.+?)(?:[，。]|$)/,
    /搜索[：:]?(.+?)(?:[，。]|$)/
  ]
  
  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match) {
      return match[1].trim()
    }
  }
  
  return '文档'
}

// 创建会议
async function createMeetingAction(content: string) {
  try {
    const meetingInfo = parseMeetingInfo(content)
    
    const response = await api.post({
      url: '/api/meetings/create',
      data: {
        title: meetingInfo.title,
        host: meetingInfo.host,
        time: meetingInfo.time,
        location: meetingInfo.location,
        participants: []
      }
    })
    
    if (response.code === 0) {
      return `✅ 已成功创建会议：${meetingInfo.title}，时间：${meetingInfo.time}，地点：${meetingInfo.location}`
    } else {
      return `❌ 创建会议失败：${response.msg}`
    }
  } catch (error) {
    return `❌ 创建会议时出错：${error}`
  }
}

// 解析会议信息
function parseMeetingInfo(content: string) {
  let title = '新会议'
  let host = '我'
  let location = '会议室A'
  const today = dayjs()
  let date = today.format('YYYY-MM-DD')
  let time = today.format('HH:mm')
  
  // 先提取日期和时间信息（使用与任务相同的解析逻辑）
  const scheduleInfo = parseScheduleInfo(content)
  date = scheduleInfo.date
  time = scheduleInfo.time
  
  // 提取会议主题 - 优先从"添加会议:"、"创建会议:"等模式中提取
  let cleanContent = content
  // 移除日期和时间相关的关键词
  cleanContent = cleanContent
    .replace(/添加会议[：:]?/g, '')
    .replace(/创建会议[：:]?/g, '')
    .replace(/新建会议[：:]?/g, '')
    .replace(/安排会议[：:]?/g, '')
    .replace(/帮我添加会议[：:]?/g, '')
    .replace(/帮我创建会议[：:]?/g, '')
    .replace(/明天|明日|后天|后日|大后天|今天|今日|昨天|昨日|下周/g, '')
    .replace(/\d{4}年/g, '')
    .replace(/\d{1,2}月/g, '')
    .replace(/\d{1,2}[日号]/g, '')
    .replace(/(上午|下午|晚上|中午|凌晨|傍晚)\s*\d{1,2}\s*[点:]?\s*\d{0,2}\s*(?:分|分钟)?/g, '')
    .replace(/\d{1,2}[：:]?\d{0,2}\s*(点|时)/g, '')
    .replace(/\d{1,2}[：:]?\d{2}/g, '')
    .replace(/[，。、；：！？\s]+/g, ' ')
    .trim()
  
  // 尝试提取会议标题
  // 模式1: "添加会议: 标题" 或 "添加会议: 时间, 标题"
  const titlePattern1 = /(?:添加|创建|新建|安排)会议[：:]?\s*(?:.*?[，,]\s*)?(.+?)(?:[，。]|$)/
  const match1 = content.match(titlePattern1)
  if (match1 && match1[1]) {
    let extractedTitle = match1[1].trim()
    // 移除时间信息
    extractedTitle = extractedTitle
      .replace(/明天|明日|后天|后日|大后天|今天|今日|昨天|昨日|下周/g, '')
      .replace(/\d{4}年/g, '')
      .replace(/\d{1,2}月/g, '')
      .replace(/\d{1,2}[日号]/g, '')
      .replace(/(上午|下午|晚上|中午|凌晨|傍晚)\s*\d{1,2}\s*[点:]?\s*\d{0,2}\s*(?:分|分钟)?/g, '')
      .replace(/\d{1,2}[：:]?\d{0,2}\s*(点|时)/g, '')
      .replace(/\d{1,2}[：:]?\d{2}/g, '')
      .trim()
    if (extractedTitle && extractedTitle.length > 0) {
      title = extractedTitle
    }
  } else if (cleanContent && cleanContent.length > 0) {
    // 如果清理后的内容不为空，使用清理后的内容作为标题
    title = cleanContent
  }
  
  // 如果标题为空或只包含标点符号，使用默认值
  if (!title || title.length < 2 || /^[，。、；：！？\s]+$/.test(title)) {
    title = '新会议'
  }
  
  // 提取地点
  const locationMatch = content.match(/在(.+?)(?:举行|开会|召开|进行)/) ||
                        content.match(/地点[：:]?(.+?)(?:[，。]|$)/) ||
                        content.match(/会议室[：:]?(.+?)(?:[，。]|$)/)
  if (locationMatch && locationMatch[1]) {
    location = locationMatch[1].trim()
  }
  
  // 组合日期和时间
  const fullDateTime = `${date} ${time}`
  
  return { title, host, time: fullDateTime, location }
}

// 查看会议
async function viewMeetingAction() {
  try {
    const response = await api.get({
      url: '/api/meetings/list',
      params: { page: 1, pageSize: 10 }
    })
    
    if (response.code === 0 && response.data.list.length > 0) {
      let result = '📅 近期会议安排：\n\n'
      response.data.list.forEach((meeting, index) => {
        result += `${index + 1}. 📋 ${meeting.title}\n`
        result += `   主持人：${meeting.host}\n`
        result += `   时间：${meeting.time}\n`
        result += `   地点：${meeting.location}\n`
        result += `   状态：${meeting.status === 'upcoming' ? '待开始' : '已结束'}\n\n`
      })
      return result
    } else {
      return '📅 暂无会议安排'
    }
  } catch (error) {
    return `❌ 查看会议时出错：${error}`
  }
}

// 创建文档
async function createDocumentAction(content: string) {
  try {
    const docInfo = parseDocumentInfo(content)
    
    // 这里可以集成到智能文档创建API
    return `✅ 已为您记录文档创建需求：${docInfo.title}。请前往智能文档页面完成创建。`
  } catch (error) {
    return `❌ 创建文档时出错：${error}`
  }
}

// 解析文档信息
function parseDocumentInfo(content: string) {
  let title = '新文档'
  
  const titleMatch = content.match(/创建文档[：:]?(.+?)(?:[，。]|$)/) ||
                     content.match(/新建文档[：:]?(.+?)(?:[，。]|$)/) ||
                     content.match(/写文档[：:]?(.+?)(?:[，。]|$)/)
  if (titleMatch) {
    title = titleMatch[1].trim()
  }
  
  return { title }
}

// 添加联系人
async function addContactAction(content: string) {
  try {
    return `✅ 已记录添加联系人需求。请前往联系人页面完成添加操作。`
  } catch (error) {
    return `❌ 添加联系人时出错：${error}`
  }
}

// 查看联系人
async function viewContactAction() {
  try {
    const response = await api.get({ url: '/api/contact/list' }) as any
    
    if (response.code === 0 && response.data && response.data.length > 0) {
      let result = '👥 联系人列表：\n\n'
      response.data.forEach((contact: any, index: number) => {
        result += `${index + 1}. 👤 ${contact.realName || contact.username}\n`
        if (contact.department) result += `   部门：${contact.department}\n`
        result += '\n'
      })
      return result
    } else {
      return '👥 暂无联系人'
    }
  } catch (error) {
    return `❌ 查看联系人时出错：${error}`
  }
}

// 搜索知识库
async function searchKnowledgeAction(content: string) {
  try {
    const keyword = extractSearchKeyword(content)
    
    const response = await api.post({
      url: '/api/knowledge/qa',
      data: { question: keyword }
    }) as any
    
    if (response.code === 0) {
      return `🧠 知识库搜索结果：\n\n${response.answer}`
    } else {
      return `❌ 知识库搜索失败：${response.msg}`
    }
  } catch (error) {
    return `❌ 搜索知识库时出错：${error}`
  }
}

// 批量发送消息
async function batchMessageAction(content: string) {
  try {
    const message = extractBatchMessage(content)
    await aiAutoSendToAll(message)
    return `✅ 已向所有联系人发送消息：${message}`
  } catch (error) {
    return `❌ 批量发送消息失败：${error}`
  }
}

// 提取批量消息内容
function extractBatchMessage(content: string) {
  const patterns = [
    /给所有联系人发[：:]?(.+?)(?:[，。]|$)/,
    /群发[：:]?(.+?)(?:[，。]|$)/,
    /发送[：:]?(.+?)(?:[，。]|$)/
  ]
  
  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match) {
      return match[1].trim()
    }
  }
  
  return content
}

// 处理问候
function handleGreeting(content: string) {
  const greetings = [
    "您好！我是您的智能助手，可以帮您处理以下任务：\n\n📅 日程管理 - 添加、查看日程安排\n📄 文档操作 - 搜索、读取文档\n📋 会议管理 - 创建、查看会议\n👥 联系人管理 - 查看联系人列表\n🧠 知识库查询 - 搜索相关资料\n\n请告诉我您需要什么帮助！",
    "Hi！很高兴为您服务！我可以帮您管理日程、处理文档、安排会议等。您有什么需要的吗？",
    "您好！我是您的专属助手，随时准备为您提供帮助。无论是工作安排还是信息查询，都可以交给我！"
  ]
  
  return greetings[Math.floor(Math.random() * greetings.length)]
}

// 处理日程确认
async function handleScheduleConfirm(content: string) {
  // 从上下文或内容中提取日程信息
  const scheduleInfo = parseScheduleFromConfirm(content)
  
  if (scheduleInfo.title) {
    return await addScheduleAction(`添加日程：${scheduleInfo.title} ${scheduleInfo.time}`)
  } else {
    return "好的！请告诉我具体的日程安排，比如时间和事项内容，我来帮您添加。\n\n例如：\"明天下午3点开会\" 或 \"提醒我周五写报告\""
  }
}

// 从确认对话中解析日程信息
function parseScheduleFromConfirm(content: string) {
  const msg = content.toLowerCase()
  let title = ''
  let time = ''
  
  // 尝试从内容中提取时间和事件信息
  const timePattern = /(\d{1,2})[：:]?(\d{0,2})\s*(点|时)/
  const timeMatch = msg.match(timePattern)
  if (timeMatch) {
    const hour = timeMatch[1].padStart(2, '0')
    const minute = timeMatch[2] || '00'
    time = `${hour}:${minute}`
  }
  
  // 提取事件类型
  if (msg.includes('开会') || msg.includes('会议')) {
    title = '会议'
  } else if (msg.includes('汇报') || msg.includes('报告')) {
    title = '工作汇报'
  } else if (msg.includes('培训')) {
    title = '培训'
  } else if (msg.includes('活动')) {
    title = '活动'
  }
  
  return { title, time }
}

// 查找最近上传的文件
function findRecentFile(): { url: string; name: string } | null {
  // 从历史消息中查找最近的文件消息
  for (let i = history.value.length - 1; i >= 0; i--) {
    const msg = history.value[i]
    if (msg.from === 'user' && msg.content) {
      // 检查消息中是否包含文件链接
      const fileMatch = msg.content.match(/href=["']([^"']*\/uploads\/assistant\/[^"']+)["']/)
      if (fileMatch) {
        const fileNameMatch = msg.content.match(/>([^<]+\.(xlsx|xls|docx|doc|pdf|txt|pptx|ppt|csv))</i)
        return {
          url: fileMatch[1],
          name: fileNameMatch ? fileNameMatch[1] : '文件'
        }
      }
    }
  }
  return null
}

async function ragSearch() {
  if (!ragQuestion.value) return
  
  // 如果没有会话，自动创建新会话
  if (!currentSessionId.value || sessions.value.length === 0) {
    createNewSession()
  }
  
  // 检查是否要求分析文件
  const analyzeFilePatterns = [
    /分析(上面|这个|刚才|最近|上传的)?(文件|附件|文档)/i,
    /帮我(分析|看看|解读)(一下)?(这个|上面|刚才|最近|上传的)?(文件|附件|文档)/i,
    /(这个|上面|刚才|最近|上传的)?(文件|附件|文档)(的内容|情况|信息)/i
  ]
  
  const shouldAnalyzeFile = analyzeFilePatterns.some(pattern => pattern.test(ragQuestion.value))
  
  if (shouldAnalyzeFile) {
    // 查找最近的文件
    const recentFile = findRecentFile()
    if (recentFile) {
      // 提取问题（如果有）
      const question = ragQuestion.value.replace(/分析(上面|这个|刚才|最近|上传的)?(文件|附件|文档)/i, '').trim()
      
      // 添加用户消息
      const userMsg: Message = {
        id: Date.now(),
        content: String(ragQuestion.value || ''),
        from: 'user',
        time: getNowTime(),
        avatar: userAvatar.value,
        sessionId: currentSessionId.value
      }
      history.value.push(userMsg)
      updateSessionHistory()
      
      // 分析文件
      await analyzeFile(recentFile.url, recentFile.name, question)
      ragQuestion.value = ''
      return
    } else if (currentFileUrl.value) {
      // 如果当前有选中的文件，使用它
      const question = ragQuestion.value.replace(/分析(上面|这个|刚才|最近|上传的)?(文件|附件|文档)/i, '').trim()
      
      const userMsg: Message = {
        id: Date.now(),
        content: String(ragQuestion.value || ''),
        from: 'user',
        time: getNowTime(),
        avatar: userAvatar.value,
        sessionId: currentSessionId.value
      }
      history.value.push(userMsg)
      updateSessionHistory()
      
      await analyzeFile(currentFileUrl.value, currentFileName.value, question)
      ragQuestion.value = ''
      return
    } else {
      // 没有找到文件，提示用户
      const userMsg: Message = {
        id: Date.now(),
        content: String(ragQuestion.value || ''),
        from: 'user',
        time: getNowTime(),
        avatar: userAvatar.value,
        sessionId: currentSessionId.value
      }
      history.value.push(userMsg)
      updateSessionHistory()
      
      const botMsg: Message = {
        id: Date.now() + 1,
        content: '抱歉，我没有找到您要分析的文件。请先上传文件，或者直接点击文件进行分析。',
        from: 'bot',
        time: getNowTime(),
        avatar: botAvatar,
        sessionId: currentSessionId.value
      }
      history.value.push(botMsg)
      updateSessionHistory()
      ragQuestion.value = ''
      ragLoading.value = false
      return
    }
  }
  
  ragLoading.value = true
  const userMsg: Message = {
    id: Date.now(),
    content: ragQuestion.value,
    from: 'user',
    time: getNowTime(),
    avatar: userAvatar.value,
    sessionId: currentSessionId.value
  }
  history.value.push(userMsg)
  updateSessionHistory()
  
  // 智能体意图识别
  const intent = analyzeIntent(ragQuestion.value)
  
  let botReply = ''
  
  // 如果识别到特定意图，执行对应操作
  if (intent.type !== 'chat') {
    try {
      const actionResult = await executeAgentAction(intent)
      if (actionResult) {
        botReply = actionResult
        
        // 添加机器人回复
        const botMsg: Message = {
          id: Date.now() + 1,
          content: String(botReply || ''),
          from: 'bot',
          time: getNowTime(),
          avatar: botAvatar,
          sessionId: currentSessionId.value
        }
        history.value.push(botMsg)
        updateSessionHistory()
        ragQuestion.value = ''
        ragLoading.value = false
        return
      }
    } catch (error) {
      botReply = `执行操作时出错：${error}`
    }
  }
  
  // 如果没有特定操作或操作失败，使用AI对话
  streamingContent.value = ''
  isStreaming.value = true
  
  try {
    // 构建请求体，如果当前有图片URL，则包含图片
    const requestBody: any = { 
      message: ragQuestion.value, 
      sessionId: currentSessionId.value 
    }
    
    // 如果有待分析的图片，添加到请求中
    if (currentImageUrl.value) {
      requestBody.image_url = currentImageUrl.value
    }
    
    const response = await fetch('/api/assistant/chat', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...(headers.value as Record<string, string>)
      },
      body: JSON.stringify(requestBody),
    })
    
    // 检查响应类型
    const contentType = response.headers.get('content-type') || ''
    
    // 如果是图片分析（有image_url），后端返回JSON格式
    if (currentImageUrl.value) {
      try {
        const data = await response.json()
        
        if (data.code === 0 && data.data?.reply) {
          // 确保reply是字符串，处理各种可能的格式
          let replyText = ''
          if (typeof data.data.reply === 'string') {
            replyText = data.data.reply
          } else if (typeof data.data.reply === 'object') {
            // 如果是对象，尝试转换为字符串
            try {
              replyText = JSON.stringify(data.data.reply, null, 2)
            } catch {
              replyText = String(data.data.reply)
            }
          } else {
            replyText = String(data.data.reply || '')
          }
          
          streamingContent.value = replyText
          
          const botMsg: Message = {
            id: Date.now() + 1,
            content: replyText,
            from: 'bot',
            time: getNowTime(),
            avatar: botAvatar,
            sessionId: currentSessionId.value
          }
          history.value.push(botMsg)
          updateSessionHistory()
          ragQuestion.value = ''
          currentImageUrl.value = ''  // 清空图片URL
          ragLoading.value = false
          isStreaming.value = false
          return
        } else {
          const errorMsg = String(data.msg || data.error?.message || '图片分析失败')
          ElMessage.error(errorMsg)
          
          const errorBotMsg: Message = {
            id: Date.now() + 1,
            content: `图片分析失败：${errorMsg}`,
            from: 'bot',
            time: getNowTime(),
            avatar: botAvatar,
            sessionId: currentSessionId.value
          }
          history.value.push(errorBotMsg)
          updateSessionHistory()
          currentImageUrl.value = ''
          ragLoading.value = false
          isStreaming.value = false
          return
        }
      } catch (jsonError) {
        console.error('解析JSON响应失败:', jsonError)
        const errorMsg = '图片分析失败：响应格式错误'
        ElMessage.error(errorMsg)
        
        const errorBotMsg: Message = {
          id: Date.now() + 1,
          content: errorMsg,
          from: 'bot',
          time: getNowTime(),
          avatar: botAvatar,
          sessionId: currentSessionId.value
        }
        history.value.push(errorBotMsg)
        updateSessionHistory()
        currentImageUrl.value = ''
        ragLoading.value = false
        isStreaming.value = false
        return
      }
    }
    
    // 纯文本对话使用流式响应
    if (!response.body) throw new Error('无流式响应')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let done = false
    let aiMsg = ''
    
    while (!done) {
      const { value, done: doneReading } = await reader.read()
      done = doneReading
      if (value) {
        const chunk = decoder.decode(value)
        streamingContent.value += chunk
        aiMsg += chunk
      }
    }
    
    let reply = aiMsg
    try {
      const data = JSON.parse(aiMsg)
      if (data && data.data && data.data.reply) {
        reply = data.data.reply
      }
    } catch {}
    
    // 确保reply是字符串
    const replyText = String(reply || '')
    streamingContent.value = replyText
    
    const botMsg: Message = {
      id: Date.now() + 1,
      content: replyText,
      from: 'bot',
      time: getNowTime(),
      avatar: botAvatar,
      sessionId: currentSessionId.value
    }
    history.value.push(botMsg)
    updateSessionHistory()
    ragQuestion.value = ''
    currentImageUrl.value = ''  // 清空图片URL
  } catch (e: any) {
    console.error('对话失败:', e)
    const errorMsg = e?.message || '对话失败，请重试'
    ElMessage.error(errorMsg)
    
    // 添加错误消息到聊天记录
    const errorBotMsg: Message = {
      id: Date.now() + 1,
      content: `对话失败：${String(errorMsg)}`,
      from: 'bot',
      time: getNowTime(),
      avatar: botAvatar,
      sessionId: currentSessionId.value
    }
    history.value.push(errorBotMsg)
    updateSessionHistory()
    
    currentImageUrl.value = ''  // 出错时也清空
  }
  
  ragLoading.value = false
  isStreaming.value = false
}

function handleAvatarClick() {
  if (avatarInput.value) (avatarInput.value as HTMLInputElement).click()
}

// 头像更改现在通过个人中心统一管理，这里只是占位函数
function onAvatarChange(e: Event) {
  // 不需要处理，头像更改通过个人中心进行
}

function confirmDeleteSession(id: string) {
  sessionIdToDelete.value = id
  deleteSessionDialogVisible.value = true
}

function handleDeleteSession() {
  if (!sessionIdToDelete.value) return
  deleteSession(sessionIdToDelete.value)
  deleteSessionDialogVisible.value = false
  sessionIdToDelete.value = ''
}

function deleteSession(id: string) {
  const idx = sessions.value.findIndex(s => s.id === id)
  if (idx !== -1) {
    sessions.value.splice(idx, 1)
    
    // 保存到localStorage
    localStorage.setItem('deepseek_sessions', JSON.stringify(sessions.value))
    
    // 如果删除的是当前会话，切换到其他会话
    if (currentSessionId.value === id) {
      if (sessions.value.length > 0) {
        // 切换到第一个会话
        currentSessionId.value = sessions.value[0].id
        history.value = sessions.value[0].history
      } else {
        // 如果没有会话了，清空当前会话和历史记录
        currentSessionId.value = ''
        history.value = []
      }
    }
    
    ElMessage.success('会话已删除')
  } else {
    ElMessage.error('会话不存在')
  }
}

// 批量给所有联系人发送消息
async function sendMsgToAllContacts(content: string) {
  // 1. 获取联系人列表
  const res = await api.get<{ code: number; data: any[] }>({ url: '/api/contact/list' })
  if (res.code !== 0) {
    ElMessage.error('获取联系人失败')
    return
  }
  const contacts = res.data
  // 2. 依次发送消息
  for (const person of contacts) {
    await api.post({ url: '/api/message/send', data: { to_user_id: person.id, content } })
  }
  ElMessage.success('已批量发送')
}

// 自动化：批量加联系人
async function addContactsBatch(contacts: {name: string, phone: string}[]) {
  for (const c of contacts) {
    await api.post({ url: '/api/contact/add', data: c })
  }
  ElMessage.success('批量添加完成')
}

// 自动化：批量审批会议
async function approveAllMeetings() {
  const res = await api.get<{ code: number; data: any[] }>({ url: '/api/meetings/pending' })
  if (res.code !== 0) {
    ElMessage.error('获取待审批会议失败')
    return
  }
  for (const m of res.data) {
    await api.post({ url: '/api/meetings/approve', data: { id: m.id } })
  }
  ElMessage.success('全部审批完成')
}

// 自动化：批量导出联系人
async function exportContacts() {
  const res = await api.get({ url: '/api/contact/export', responseType: 'blob' })
  let blob: Blob
  if (res instanceof Blob) {
    blob = res
  } else if (res instanceof ArrayBuffer) {
    blob = new Blob([res])
  } else {
    blob = new Blob([JSON.stringify(res)])
  }
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'contacts.xlsx')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('联系人已导出')
}

// 自动化：批量生成文档
async function generateDocsBatch(topics: string[]) {
  for (const t of topics) {
    await api.post({ url: '/api/doc/generate', data: { topic: t } })
  }
  ElMessage.success('批量生成文档完成')
}

// 智能解析用户输入并自动触发业务API
watch(ragQuestion, async (val) => {
  if (!val) return
  if (val.includes('给所有联系人发')) {
    const msg = val.replace('给所有联系人发', '').trim()
    await sendMsgToAllContacts(msg)
  } else if (val.includes('批量添加联系人')) {
    // 假设格式：批量添加联系人张三:123,李四:456
    const arr = val.match(/联系人(.+)/)
    if (arr && arr[1]) {
      const contacts = arr[1].split(',').map(s => {
        const [name, phone] = s.split(':')
        return { name: name.trim(), phone: phone?.trim() || '' }
      })
      await addContactsBatch(contacts)
    }
  } else if (val.includes('批量审批会议')) {
    await approveAllMeetings()
  } else if (val.includes('导出联系人')) {
    await exportContacts()
  } else if (val.includes('批量生成文档')) {
    // 假设格式：批量生成文档A,B,C
    const arr = val.match(/文档(.+)/)
    if (arr && arr[1]) {
      const topics = arr[1].split(',').map(s => s.trim())
      await generateDocsBatch(topics)
    }
  }
})

function handleUploadSuccess(response: any) {
  if (response && response.data && response.data.url) {
    sendMsgWithAttachment(response.data.url, response.data.type, response.data.original_name)
  } else {
    ElMessage.error('上传失败')
  }
}

function handleUploadError(error: any) {
  console.error('上传失败:', error)
  
  // 根据错误类型显示不同的错误信息
  if (error?.status === 401) {
    ElMessage.error('认证失败，请重新登录')
  } else if (error?.status === 413) {
    ElMessage.error('文件过大，请选择较小的文件')
  } else if (error?.status === 415) {
    ElMessage.error('不支持的文件类型')
  } else {
    ElMessage.error('上传失败，请重试')
  }
}

function sendMsgWithAttachment(url: string, type: string, originalName?: string) {
  let content = ''
  if (type === 'image') {
    content = `[图片: ${originalName || '图片'}]`
  } else {
    content = `[附件: ${originalName || '文件'}]`
  }
  
  // 创建用户消息，确保使用最新的头像
  const userMsg: Message = {
    id: Date.now(),
    content: content,
    from: 'user',
    time: getNowTime(),
    avatar: userAvatar.value, // 使用最新的头像
    sessionId: currentSessionId.value
  }
  
  // 添加附件信息
  if (type === 'image') {
    userMsg.content = `<img src="${url}" style="max-width:300px; max-height:300px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); cursor:pointer;" onclick="window.open('${url}', '_blank')" />`
    userMsg.imageUrl = url  // 保存图片URL，用于发送给AI分析
  } else {
    userMsg.content = `<div style="padding:10px; border:1px solid #e0e0e0; border-radius:8px; background:#f5f5f5;">
      <div style="font-size:14px; color:#666;">📎 附件</div>
      <div style="font-size:16px; margin:4px 0;">${originalName}</div>
      <a href="${url}" target="_blank" style="color:#409eff; text-decoration:none;">下载</a>
    </div>`
  }
  
  history.value.push(userMsg)
  updateSessionHistory()
  
  // 如果是图片，发送给AI进行分析
  if (type === 'image') {
    // 保存当前图片URL，用于后续发送
    currentImageUrl.value = url
    ragQuestion.value = `请分析这张图片`
    ragSearch()
  } else if (type === 'document' || type === 'text') {
    // 如果是文档文件，保存文件信息并自动分析
    currentFileUrl.value = url
    currentFileName.value = originalName || '文件'
    // 延迟一下再分析，确保文件已保存
    setTimeout(() => {
      analyzeFile(url, originalName || '文件', '')
    }, 500)
  } else {
    // 其他类型文件也保存信息，但不自动分析
    currentFileUrl.value = url
    currentFileName.value = originalName || '文件'
    ElMessage.success('附件上传成功，您可以输入"分析上面文件"来分析该文件')
  }
}

// 分析文件内容
async function analyzeFile(fileUrl: string, fileName: string, question: string = '') {
  // 如果没有会话，自动创建新会话
  if (!currentSessionId.value || sessions.value.length === 0) {
    createNewSession()
  }
  
  ragLoading.value = true
  
  // 显示分析中的提示
  const loadingMsg: Message = {
    id: Date.now() + 1,
    content: '正在分析文件内容，请稍候...',
    from: 'bot',
    time: getNowTime(),
    avatar: botAvatar,
    sessionId: currentSessionId.value
  }
  history.value.push(loadingMsg)
  updateSessionHistory()
  
  try {
    const response = await api.post<{ code: number; data?: { reply: string; content_length?: number }; msg?: string }>({
      url: '/api/assistant/analyze-file',
      data: {
        file_url: fileUrl,
        question: question  // 可以留空，使用默认分析提示，也可以传入自定义问题
      }
    })
    
    // 移除加载提示
    const loadingIndex = history.value.findIndex(msg => msg.id === loadingMsg.id)
    if (loadingIndex !== -1) {
      history.value.splice(loadingIndex, 1)
    }
    
    if (response.code === 0 && response.data?.reply) {
      // 添加AI回复消息，确保content是字符串
      const replyText = String(response.data.reply || '分析完成，但未返回内容')
      const botMsg: Message = {
        id: Date.now() + 2,
        content: replyText,
        from: 'bot',
        time: getNowTime(),
        avatar: botAvatar,
        sessionId: currentSessionId.value
      }
      history.value.push(botMsg)
      updateSessionHistory()
      ElMessage.success('文件分析完成')
      
      // 清空文件URL
      currentFileUrl.value = ''
      currentFileName.value = ''
    } else {
      const errorMsg = String(response.msg || '文件分析失败')
      ElMessage.error(errorMsg)
      
      // 添加错误消息到聊天记录
      const errorBotMsg: Message = {
        id: Date.now() + 2,
        content: `文件分析失败：${errorMsg}`,
        from: 'bot',
        time: getNowTime(),
        avatar: botAvatar,
        sessionId: currentSessionId.value
      }
      history.value.push(errorBotMsg)
      updateSessionHistory()
    }
  } catch (error: any) {
    // 移除加载提示
    const loadingIndex = history.value.findIndex(msg => msg.id === loadingMsg.id)
    if (loadingIndex !== -1) {
      history.value.splice(loadingIndex, 1)
    }
    
    console.error('文件分析失败:', error)
    
    // 获取详细的错误信息
    let errorMessage = '文件分析失败，请重试'
    if (error?.response?.data?.msg) {
      errorMessage = String(error.response.data.msg)
    } else if (error?.message) {
      errorMessage = `文件分析失败：${String(error.message)}`
    } else if (error?.response?.status) {
      errorMessage = `文件分析失败：服务器错误 ${error.response.status}`
    }
    
    ElMessage.error(errorMessage)
    
    // 添加错误消息到聊天记录
    const errorBotMsg: Message = {
      id: Date.now() + 2,
      content: errorMessage,
      from: 'bot',
      time: getNowTime(),
      avatar: botAvatar,
      sessionId: currentSessionId.value
    }
    history.value.push(errorBotMsg)
    updateSessionHistory()
  } finally {
    ragLoading.value = false
  }
}

// 切换表情包选择器
function toggleEmojiPicker() {
  showEmojiPicker.value = !showEmojiPicker.value
}

// 插入表情包
function insertEmoji(emoji: string) {
  ragQuestion.value += emoji
  showEmojiPicker.value = false
}

// 点击外部关闭表情包选择器
function handleOutsideClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.emoji-picker') && !target.closest('.input-tools')) {
    showEmojiPicker.value = false
  }
}
</script>

<style scoped>
.assistant-layout {
  display: flex;
  height: calc(100vh - 130px);
  background: var(--el-bg-color-page);
  overflow: hidden;
}

.session-list {
  width: 220px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  box-shadow: var(--el-box-shadow);
  padding: 0;
  display: flex;
  flex-direction: column;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid var(--el-border-color-light);
  color: var(--el-text-color-primary);
  background: var(--el-bg-color);
}

.session-list ul {
  list-style: none;
  margin: 0; 
  padding: 0;
  flex: 1;
  overflow-y: auto;
  background: var(--el-bg-color);
}

.empty-sessions {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
}

.empty-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.session-item-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: all 0.2s ease;
  cursor: pointer;
  color: var(--el-text-color-primary);
}

.session-item-flex:hover {
  background: var(--el-fill-color-light);
}

.session-list li.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-left: 3px solid var(--el-color-primary);
}

.session-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.session-title { 
  font-size: 15px; 
  font-weight: 500; 
  color: inherit;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-preview { 
  font-size: 12px; 
  color: var(--el-text-color-placeholder); 
  margin-top: 4px; 
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  margin-left: 12px;
  align-self: center;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item-flex:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: var(--el-bg-color-page);
  position: relative;
}

.empty-chat {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.empty-chat-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-chat-text {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
}

.empty-chat-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.chat-msg {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  opacity: 0;
  animation: fadeInUp 0.3s ease forwards;
}

.chat-msg.left {
  flex-direction: row;
}

.chat-msg.right {
  flex-direction: row-reverse;
}

.msg-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  max-width: 70%;
}

.chat-msg.right .msg-content {
  align-items: flex-end;
}

.msg-text {
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
  box-shadow: var(--el-box-shadow-light);
  margin-bottom: 2px;
  border: 1px solid var(--el-border-color-lighter);
  position: relative;
}

.chat-msg.right .msg-text {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.msg-text :deep(h1),
.msg-text :deep(h2),
.msg-text :deep(h3),
.msg-text :deep(h4),
.msg-text :deep(h5),
.msg-text :deep(h6) {
  color: var(--el-color-primary);
  margin: 8px 0 4px 0;
}

.msg-text :deep(p) {
  margin: 4px 0;
  line-height: 1.6;
}

.msg-text :deep(code) {
  background: var(--el-fill-color-light);
  color: var(--el-color-danger);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.msg-text :deep(pre) {
  background: var(--el-fill-color-darker);
  color: var(--el-text-color-primary);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.msg-text :deep(ul),
.msg-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.msg-text :deep(li) {
  margin: 4px 0;
}

.msg-text :deep(a) {
  color: var(--el-color-primary);
  text-decoration: underline;
}

.msg-text :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 8px 0;
}

.msg-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin: 4px 0 0 8px;
  text-align: left;
}

.chat-msg.right .msg-time {
  text-align: right;
  margin-left: 0;
  margin-right: 8px;
}

.chat-input-bar {
  background: var(--el-bg-color);
  padding: 8px 12px 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: var(--el-box-shadow);
  border-radius: 0 0 0 18px;
  z-index: 10;
  border-top: 1px solid var(--el-border-color-light);
  position: relative;
}

.input-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.input-tools .el-button {
  padding: 6px 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  border-radius: 4px;
  transition: all 0.3s;
}

.input-tools .el-button:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary);
}

.input-main {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.emoji-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  width: 420px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-color-primary);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  max-height: 320px;
  overflow-y: auto;
  padding: 16px;
  margin-bottom: 12px;
}

/* 箭头指向按钮 */
.emoji-picker::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 16px;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid var(--el-color-primary);
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 4px;
  padding: 4px;
}

.emoji-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 18px;
  background: var(--el-fill-color-lighter);
  border: 1px solid transparent;
}

.emoji-item:hover {
  background: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary);
  transform: scale(1.1);
}

.emoji-picker::-webkit-scrollbar {
  width: 6px;
}

.emoji-picker::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.emoji-picker::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.emoji-picker::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

.input-main .el-textarea .el-textarea__inner {
  min-height: 100px;
  font-size: 16px;
  line-height: 1.6;
  box-shadow: none !important;
  background: var(--el-bg-color) !important;
  border: 1px solid var(--el-border-color) !important;
  border-radius: 8px !important;
  color: var(--el-text-color-primary) !important;
  resize: none;
}

.input-main .el-textarea .el-textarea__inner:focus {
  border-color: var(--el-color-primary) !important;
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8) !important;
}

/* 滚动条样式 */
.session-list ul::-webkit-scrollbar,
.chat-history::-webkit-scrollbar {
  width: 6px;
}

.session-list ul::-webkit-scrollbar-track,
.chat-history::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
}

.session-list ul::-webkit-scrollbar-thumb,
.chat-history::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.session-list ul::-webkit-scrollbar-thumb:hover,
.chat-history::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 深色模式优化 */
.dark .session-list {
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.3);
}

.dark .msg-text {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.dark .chat-input-bar {
  box-shadow: 0 -2px 24px rgba(0, 0, 0, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .assistant-layout {
    flex-direction: column;
  }
  
  .session-list {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--el-border-color);
  }
  
  .chat-history {
    padding: 12px 16px 12px 16px;
    gap: 12px;
  }
  
  .chat-input-bar {
    padding: 8px 12px;
    gap: 8px;
  }
  
  .msg-content {
    max-width: 85%;
  }
}
</style>
