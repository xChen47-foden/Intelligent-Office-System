<template>
  <div class="layout-chat">
    <el-drawer v-model="isDrawerVisible" :size="isMobile ? '100%' : '480px'" :with-header="false">
      <div class="header">
        <div class="header-left">
          <span class="name">便捷智能助手</span>
          <div class="status">
            <div class="dot" :class="{ online: isOnline, offline: !isOnline }"></div>
            <span class="status-text">{{ isOnline ? '在线' : '离线' }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-icon class="icon-close" :size="20" @click="closeChat">
            <Close />
          </el-icon>
        </div>
      </div>
      <div class="chat-container">
        <!-- 聊天消息区域 -->
        <div class="chat-messages" ref="messageContainer">
          <template v-for="(message, index) in messages" :key="index">
            <div :class="['message-item', message.isMe ? 'message-right' : 'message-left']">
              <el-avatar :size="32" :src="message.avatar" class="message-avatar" />
              <div class="message-content">
                <div class="message-info">
                  <span class="sender-name">{{ message.sender }}</span>
                  <span class="message-time">{{ message.time }}</span>
                </div>
                <div v-if="message.image" class="message-image">
                  <div v-if="message.uploading" class="image-loading">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span style="margin-left: 8px">上传中...</span>
                  </div>
                  <div v-else-if="message.uploadFailed" class="image-failed">
                    <el-icon><Warning /></el-icon>
                    <span style="margin-left: 8px">上传失败</span>
                  </div>
                  <img 
                    v-else 
                    :src="message.image" 
                    :alt="message.content" 
                    style="max-width:180px;max-height:120px;border-radius:8px;cursor:pointer;"
                    @click="previewImage(message.image)"
                    @error="handleImageError"
                  />
                </div>
                <div v-if="message.content && !message.image" class="message-text">
                  {{ message.content }}
                </div>
                <div v-if="message.content && message.image" class="message-text" style="margin-top: 8px;">
                  {{ message.content }}
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 聊天输入区域 -->
        <div class="chat-input">
          <div class="input-actions-wrapper">
              <div class="input-actions">
                <el-upload
                  :show-file-list="false"
                  accept="image/*"
                :auto-upload="false"
                :on-change="handleImageChange"
                class="action-upload"
              >
                <template #trigger>
                  <div class="action-btn image-btn">
                    <el-icon :size="20"><Picture /></el-icon>
                    <span class="btn-label">图片</span>
                  </div>
                </template>
                </el-upload>
              <div class="action-btn emoji-btn" @click="toggleEmojiPicker">
                <span class="emoji-icon">😀</span>
                <span class="btn-label">表情</span>
              </div>
            </div>
            <div v-if="showEmoji" class="emoji-picker-wrap" @click.stop>
                <div class="emoji-picker">
                  <div class="emoji-header">选择表情</div>
                  <div class="emoji-grid">
                    <span 
                      v-for="emoji in emojiList" 
                      :key="emoji" 
                      class="emoji-item" 
                      @click="insertEmoji(emoji)"
                    >
                      {{ emoji }}
                    </span>
                  </div>
                </div>
              </div>
          </div>
          <el-input
            v-model="messageText"
            type="textarea"
            :rows="3"
            placeholder="输入消息"
            resize="none"
            @keyup.enter.prevent="sendMessage"
          />
          <div class="chat-input-actions">
            <el-button type="primary" @click="sendMessage" v-ripple>发送</el-button>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
  import { Picture, Close, Loading, Warning } from '@element-plus/icons-vue'
  import mittBus from '@/utils/mittBus'
  import meAvatar from '@/assets/img/avatar/avatar5.jpg'
  import aiAvatar from '@/assets/img/avatar/avatar10.jpg'
  import axios from 'axios'
  import { ElMessage } from 'element-plus'
  import { aiAutoSendToAll } from '@/services/ai'
  import { useUserStore } from '@/store/modules/user'
  import { storeToRefs } from 'pinia'

  const isMobile = computed(() => window.innerWidth < 500)

  // 用户store
  const userStore = useUserStore()
  const { info } = storeToRefs(userStore)

  // 头像URL处理函数
  const getAvatarUrl = (avatar: string) => {
    if (!avatar) return meAvatar
    if (avatar.startsWith('http')) return avatar
    // 如果已经是/uploads/开头，直接使用，否则添加/uploads/前缀
    if (avatar.startsWith('/uploads/')) {
      return `http://localhost:3007${avatar}?t=${Date.now()}`
    }
    return `http://localhost:3007/uploads/${avatar}?t=${Date.now()}`
  }

  // 用户头像计算属性，自动同步用户状态
  const userAvatar = computed(() => getAvatarUrl(info.value?.avatar || ''))
  const userName = computed(() => info.value?.realName || info.value?.nickName || info.value?.userName || '我')

  // 抽屉显示状态
  const isDrawerVisible = ref(false)
  // 是否在线
  const isOnline = ref(true)

  // 消息相关数据
  const messageText = ref('')
  // 定义消息类型
  interface ChatMessage {
    id: number;
    sender: string;
    content: string;
    time: string;
    isMe: boolean;
    avatar: string;
    image?: string;
    uploading?: boolean;
    uploadFailed?: boolean;
  }
  const messages = ref<ChatMessage[]>([
    {
      id: 1,
      sender: 'Art Bot',
      content: '你好！我是你的AI助手，有什么我可以帮你的吗？',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: false,
      avatar: aiAvatar
    }
  ])

  const messageId = ref(2) // 用于生成唯一的消息ID

  const showEmoji = ref(false)

  const ragLoading = ref(false)

  // 发送消息（支持自动化指令）
  const sendMessage = async () => {
    const text = messageText.value.trim()
    if (!text) return
    // 自动化指令正则匹配
    const match = text.match(/(给|帮我给)(聊天室里的)?所有联系人(发|发送)(.*)/)
    if (match && match[4]) {
      const msg = match[4].trim()
      await aiAutoSendToAll(msg)
      ElMessage.success('已批量发送')
      messageText.value = ''
      return
    }
    messages.value.push({
      id: messageId.value++, sender: userName.value, content: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: true, avatar: userAvatar.value
    })
    messageText.value = ''
    scrollToBottom()
    ragLoading.value = true
    try {
      const res = await axios.post('/api/assistant/chat', {
        message: text,
        sessionId: '便捷助手',
      })
      
      // 检查响应状态
      if (res.data?.code === 0) {
        // 成功响应，提取回复内容
        const reply = res.data?.data?.reply || res.data?.data?.text || res.data?.answer || res.data?.reply || '抱歉，AI暂时无法回复'
        messages.value.push({
          id: messageId.value++, sender: 'Art Bot', content: reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isMe: false, avatar: aiAvatar
        })
      } else {
        // API返回错误
        const errorMsg = res.data?.msg || 'AI服务暂时不可用，请稍后再试'
        messages.value.push({
          id: messageId.value++, sender: 'Art Bot', content: `❌ ${errorMsg}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isMe: false, avatar: aiAvatar
        })
        ElMessage.error(errorMsg)
      }
      scrollToBottom()
    } catch (error: any) {
      console.error('发送消息失败:', error)
      const errorMsg = error?.response?.data?.msg || error?.message || '网络错误，请检查网络连接'
      messages.value.push({
        id: messageId.value++, sender: 'Art Bot', content: `❌ ${errorMsg}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isMe: false, avatar: aiAvatar
      })
      ElMessage.error('发送消息失败: ' + errorMsg)
      scrollToBottom()
    }
    ragLoading.value = false
  }

  // 监听用户头像变化，自动更新历史消息中的头像
  watch(userAvatar, (newAvatar, oldAvatar) => {
    // 只有在头像真正变化时才更新，避免频繁更新
    if (newAvatar && oldAvatar && newAvatar !== oldAvatar) {
      messages.value.forEach((msg: any) => {
        if (msg.isMe) {
          msg.avatar = newAvatar
          msg.sender = userName.value
        }
      })
    }
  })

  // 监听用户名变化，自动更新历史消息中的用户名
  watch(userName, (newName, oldName) => {
    if (newName && oldName && newName !== oldName) {
      messages.value.forEach((msg: any) => {
        if (msg.isMe) {
          msg.sender = newName
        }
      })
    }
  })

  // 处理图片选择
  const handleImageChange = (file: any) => {
    console.log('图片选择:', file)
    if (file) {
      // ElementPlus upload组件的file对象结构
      const fileObj = file.raw || file
      if (fileObj instanceof File) {
        sendImage(fileObj)
      } else {
        console.error('无效的文件对象:', file)
        ElMessage.error('文件选择失败，请重试')
      }
    }
  }

  // 发送图片
  const sendImage = async (file: File | null) => {
    if (!file) {
      return
    }
    
    // 验证文件类型和大小
    if (!file.type.startsWith('image/')) {
      ElMessage.error('请选择图片文件')
      return
    }
    
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.error('图片大小不能超过5MB')
      return
    }

    // 创建本地预览URL
    const localUrl = URL.createObjectURL(file)
    
    // 立即显示图片消息（使用本地URL）
    const imageMsg = {
      id: messageId.value++, 
      sender: userName.value, 
      content: `[图片: ${file.name}]`,
      image: localUrl,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: true, 
      avatar: userAvatar.value,
      uploading: true // 标记为上传中
    }
    
    messages.value.push(imageMsg)
    scrollToBottom()

    try {
      // 上传到服务器
      const formData = new FormData()
      formData.append('file', file)
      
      const token = userStore.accessToken || localStorage.getItem('token')
      const uploadResponse = await axios.post('http://localhost:3007/api/assistant/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: 'Bearer ' + token } : {})
        }
      })

      if (uploadResponse.data && uploadResponse.data.data && uploadResponse.data.data.url) {
        // 上传成功，更新图片URL
        imageMsg.image = `http://localhost:3007${uploadResponse.data.data.url}`
        imageMsg.uploading = false
        
        // 向AI发送图片分析请求
        ragLoading.value = true
        try {
          const aiResponse = await axios.post('/api/assistant/chat', {
            message: `请分析这张图片：${file.name}`,
            sessionId: '便捷助手',
            image: uploadResponse.data.data.url
          })
          
          const reply = aiResponse.data?.data?.reply || aiResponse.data?.answer || '我看到了这张图片，有什么需要我帮助分析的吗？'
          messages.value.push({
            id: messageId.value++, 
            sender: 'Art Bot', 
            content: reply,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isMe: false, 
            avatar: aiAvatar
          })
          scrollToBottom()
        } catch (error) {
          console.error('AI分析图片失败:', error)
        }
        ragLoading.value = false
        
        ElMessage.success('图片发送成功')
      } else {
        throw new Error('上传响应格式错误')
      }
    } catch (error) {
      console.error('图片上传失败:', error)
      // 上传失败，移除消息或标记失败
      const index = messages.value.findIndex(msg => msg.id === imageMsg.id)
      if (index > -1) {
        messages.value[index].uploading = false
        messages.value[index].uploadFailed = true
      }
      ElMessage.error('图片上传失败，请重试')
    } finally {
      // 清理本地URL
      if (localUrl !== imageMsg.image) {
        URL.revokeObjectURL(localUrl)
      }
    }
  }

  // 表情包数据
  const emojiList = [
    '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', 
    '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙',
    '🥲', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🫢',
    '🤫', '🤔', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '😮',
    '🤐', '🤨', '😵', '😵‍💫', '🤯', '🤠', '🥳', '🥸', '😎', '🤓',
    '🧐', '😕', '😟', '🙁', '☹️', '😮', '😯', '😲', '😳', '🥺',
    '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱', '😖', '😣',
    '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬', '😈',
    '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽', '👾',
    '🤖', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾',
    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
    '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️',
    '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐',
    '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐',
    '♑', '♒', '♓', '🆔', '⚛️', '🉑', '☢️', '☣️', '📴', '📳',
    '🈶', '🈚', '🈸', '🈺', '🈷️', '✴️', '🆚', '💮', '🉐', '㊙️',
    '㊗️', '🈴', '🈵', '🈹', '🈲', '🅰️', '🅱️', '🆎', '🆑', '🅾️',
    '🆘', '❌', '⭕', '🛑', '⛔', '📛', '🚫', '💯', '💢', '♨️',
    '🚷', '🚯', '🚳', '🚱', '🔞', '📵', '🚭', '❗', '❕', '❓',
    '❔', '‼️', '⁉️', '🔅', '🔆', '〽️', '⚠️', '🚸', '🔱', '⚜️',
    '🔰', '♻️', '✅', '🈯', '💹', '❇️', '✳️', '❎', '🌐', '💠'
  ]

  // 切换表情包选择器
  const toggleEmojiPicker = () => {
    showEmoji.value = !showEmoji.value
  }

  // 选择表情
  const insertEmoji = (emoji: string) => {
    messageText.value += emoji
    showEmoji.value = false
  }

  // 点击外部关闭表情选择器
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (!target.closest('.emoji-picker-wrap') && !target.closest('.emoji-button') && !target.closest('.input-actions')) {
      showEmoji.value = false
    }
  }

  // 图片预览
  const previewImage = (imageUrl: string) => {
    window.open(imageUrl, '_blank')
  }

  // 图片加载错误处理
  const handleImageError = (event: Event) => {
    const target = event.target as HTMLImageElement
    const messageId = parseInt(target.dataset.messageId || '0')
    const message = messages.value.find(msg => msg.id === messageId)
    if (message) {
      message.uploadFailed = true
    }
  }

  // 滚动到底部
  const messageContainer = ref<HTMLElement | null>(null)
  const scrollToBottom = () => {
    setTimeout(() => {
      if (messageContainer.value) {
        messageContainer.value.scrollTop = messageContainer.value.scrollHeight
      }
    }, 100)
  }

  const openChat = () => {
    isDrawerVisible.value = true
  }

  const closeChat = () => {
    isDrawerVisible.value = false
  }

  onMounted(() => {
    scrollToBottom()
    mittBus.on('openChat', openChat)
    
    // 初始化用户状态
    if (!userStore.accessToken && !localStorage.getItem('token')) {
      userStore.initState()
    }
    
    // 初始化时确保AI消息头像正确
    if (messages.value.length > 0 && !messages.value[0].isMe) {
      messages.value[0].avatar = aiAvatar
    }
    
    // 添加点击外部关闭表情选择器的事件监听
    document.addEventListener('click', handleClickOutside)
  })

  onUnmounted(() => {
    // 移除事件监听器
    document.removeEventListener('click', handleClickOutside)
  })
</script>

<style lang="scss">
  .layout-chat {
    .el-overlay {
      background-color: rgb(0 0 0 / 20%) !important;
    }
  }
</style>

<style lang="scss" scoped>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    .header-left {
      .name {
        font-size: 16px;
        font-weight: 500;
      }

      .status {
        display: flex;
        gap: 4px;
        align-items: center;
        margin-top: 6px;

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;

          &.online {
            background-color: var(--el-color-success);
          }

          &.offline {
            background-color: var(--el-color-danger);
          }
        }

        .status-text {
          font-size: 12px;
          color: var(--art-gray-500);
        }
      }
    }

    .header-right {
      .icon-close {
        cursor: pointer;
      }
    }
  }

  .chat-container {
    display: flex;
    flex-direction: column;
    height: calc(100% - 70px);

    .chat-messages {
      flex: 1;
      padding: 30px 16px;
      overflow-y: auto;
      border-top: 1px solid var(--el-border-color-lighter);

      &::-webkit-scrollbar {
        width: 5px !important;
      }

      .message-item {
        display: flex;
        flex-direction: row;
        gap: 8px;
        align-items: flex-start;
        width: 100%;
        margin-bottom: 30px;

        .message-text {
          font-size: 14px;
          color: var(--art-gray-900);
          border-radius: 6px;
        }

        &.message-left {
          justify-content: flex-start;

          .message-content {
            align-items: flex-start;

            .message-info {
              flex-direction: row;
            }

            .message-text {
              background-color: #f8f5ff;
            }
          }
        }

        &.message-right {
          flex-direction: row-reverse;

          .message-content {
            align-items: flex-end;

            .message-info {
              flex-direction: row-reverse;
            }

            .message-text {
              background-color: #e9f3ff;
            }
          }
        }

        .message-avatar {
          flex-shrink: 0;
        }

        .message-content {
          display: flex;
          flex-direction: column;
          max-width: 70%;

          .message-info {
            display: flex;
            gap: 8px;
            margin-bottom: 4px;
            font-size: 12px;

            .message-time {
              color: var(--el-text-color-secondary);
            }

            .sender-name {
              font-weight: 500;
            }
          }

          .message-text {
            padding: 10px 14px;
            line-height: 1.4;
          }
        }
      }
    }

    .chat-input {
      padding: 16px 16px 0;

      .input-actions-wrapper {
        margin-bottom: 12px;
        position: relative;
      }

      .chat-input-actions {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-top: 12px;

        // 确保发送按钮与输入框对齐
        el-button {
          min-width: 80px;
        }
      }
    }
  }

  .dark {
    .chat-container {
      .chat-messages {
        .message-item {
          &.message-left {
            .message-text {
              background-color: #232323 !important;
            }
          }

          &.message-right {
            .message-text {
              background-color: #182331 !important;
            }
          }
        }
      }
    }
  }

  .input-actions-wrapper {
    position: relative;
    width: 100%;
  }
  
  .input-actions {
    display: flex;
    gap: 12px;
    align-items: center;
    
    .action-upload {
      display: inline-block;
    }
    
    .action-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 20px;
      background: var(--el-fill-color-lighter);
      border: 1px solid var(--el-border-color-lighter);
      cursor: pointer;
      transition: all 0.3s ease;
      user-select: none;
      
      &:hover {
        background: var(--el-fill-color);
        border-color: var(--el-color-primary);
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
      
      &:active {
        transform: translateY(0);
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
      }
      
      .el-icon {
        color: var(--el-color-primary);
        transition: transform 0.2s;
      }
      
      .emoji-icon {
        font-size: 18px;
        line-height: 1;
      }
      
      .btn-label {
        font-size: 14px;
        color: var(--el-text-color-primary);
        font-weight: 500;
      }
      
      &:hover .el-icon {
        transform: scale(1.1);
      }
    }
    
    .image-btn {
      &:hover {
        background: rgba(64, 158, 255, 0.1);
      }
    }
    
    .emoji-btn {
      &:hover {
        background: rgba(255, 193, 7, 0.1);
        border-color: rgba(255, 193, 7, 0.3);
      }
    }
  }

  .emoji-picker-wrap {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 0;
    z-index: 2000;
    
    .emoji-picker {
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color);
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      max-width: 300px;
      
      .emoji-header {
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        border-bottom: 1px solid var(--el-border-color-lighter);
        background: var(--el-bg-color-page);
        border-radius: 8px 8px 0 0;
      }
      
      .emoji-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 4px;
        padding: 12px;
        max-height: 200px;
        overflow-y: auto;
        
        .emoji-item {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.2s;
          font-size: 16px;
          
          &:hover {
            background-color: var(--el-fill-color-light);
          }
          
          &:active {
            background-color: var(--el-fill-color);
          }
        }
        
        &::-webkit-scrollbar {
          width: 4px;
        }
        
        &::-webkit-scrollbar-track {
          background: var(--el-fill-color-lighter);
          border-radius: 2px;
        }
        
        &::-webkit-scrollbar-thumb {
          background: var(--el-fill-color);
          border-radius: 2px;
        }
      }
    }
  }
  
  // 图片消息样式
  .message-item {
    .message-text {
      &.has-image {
        padding: 0;
        background: transparent !important;
        
        img {
          max-width: 200px;
          max-height: 200px;
          border-radius: 8px;
          object-fit: cover;
          cursor: pointer;
        }
        
        .image-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 200px;
          height: 120px;
          background: var(--el-fill-color-lighter);
          border-radius: 8px;
          color: var(--el-text-color-secondary);
          font-size: 14px;
        }
        
        .image-failed {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 200px;
          height: 120px;
          background: var(--el-color-danger-light-9);
          border-radius: 8px;
          color: var(--el-color-danger);
          font-size: 14px;
        }
      }
    }
  }
</style>
