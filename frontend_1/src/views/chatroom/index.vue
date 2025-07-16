<template>
  <div class="chat-page">
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        联系人
        <div class="chat-action-btns" style="margin-top: 10px;">
          <el-button type="primary" size="small" @click.stop="showAdd = true">添加</el-button>
          <el-button type="success" size="small" @click="showCreateGroup = true" style="margin-left: 10px;">创建群聊</el-button>
          <el-button type="danger" size="small" @click="openDeleteDialog" style="margin-left: 10px;">删除</el-button>
        </div>
      </div>
      <el-tabs v-model="sidebarTab" class="sidebar-tabs">
        <el-tab-pane label="联系人" name="contacts">
          <ul class="person-list">
            <!-- 群聊分组 -->
            <li v-for="group in groupList" :key="'group-' + group.id" :class="{active: currentGroup && group.id === currentGroup.id}" @click="selectGroup(group)">
              <div class="person-avatar-container">
              <el-avatar :size="36" :src="getAvatarUrl(group.avatar)" />
                <div v-if="getGroupUnreadCount(group.id) > 0" class="unread-badge">
                  {{ getGroupUnreadCount(group.id) > 99 ? '99+' : getGroupUnreadCount(group.id) }}
                </div>
              </div>
              <span class="person-name">{{ group.name }}</span>
              <span class="group-tag">群聊</span>
            </li>
            <!-- 个人联系人分组 -->
            <li v-for="person in personList" :key="person.id" :class="{active: currentPerson && person.id === currentPerson.id}" @click="selectPerson(person)">
              <div class="person-avatar-container">
              <el-avatar :size="36" :src="getAvatarUrl(person.avatar)" @error="onAvatarError" />
                <div v-if="getUnreadCount(person.id) > 0" class="unread-badge">
                  {{ getUnreadCount(person.id) > 99 ? '99+' : getUnreadCount(person.id) }}
                </div>
              </div>
              <span class="person-name">{{ person.real_name || person.username }}</span>
            </li>
          </ul>
        </el-tab-pane>
        <el-tab-pane label="申请中" name="pending">
          <ul class="person-list">
            <li v-for="req in myPendingRequests" :key="req.request_id">
              <el-avatar :size="36" :src="getAvatarUrl(req.avatar)" />
              <span class="person-name">{{ req.to_user_real_name || req.to_user_name }}</span>
              <span class="pending-tag">等待对方同意</span>
            </li>
          </ul>
        </el-tab-pane>
        <el-tab-pane label="待处理申请" name="to_handle">
          <ul class="person-list">
            <li v-for="req in pendingRequests" :key="req.request_id">
              <el-avatar :size="36" :src="getAvatarUrl(req.avatar)" />
              <span class="person-name">{{ req.from_user_real_name || req.from_user_name }}</span>
              <el-button type="success" size="small" @click.stop="handleRequest(req, 'accept')">同意</el-button>
              <el-button type="danger" size="small" @click.stop="handleRequest(req, 'reject')">拒绝</el-button>
            </li>
          </ul>
        </el-tab-pane>
      </el-tabs>
      <el-dialog v-model="showAdd" title="添加联系人">
        <el-form :model="addForm">
          <el-form-item label="选择用户">
            <el-select
              v-model="addForm.contact_user_id"
              filterable
              placeholder="请选择用户"
              :loading="userLoading"
              style="width: 100%"
            >
              <el-option
                v-for="user in availableUserOptions"
                :key="user.id"
                :label="user.real_name || user.username"
                :value="user.id"
              >
                <el-avatar :size="20" :src="getAvatarUrl(user.avatar)" style="margin-right:6px;" />
                <span>{{ user.real_name || user.username }}</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAdd = false">取消</el-button>
          <el-button type="primary" @click="addContact">确定</el-button>
        </template>
      </el-dialog>
      <el-dialog v-model="deleteSelectVisible" title="选择要删除的联系人" width="320px">
        <el-select v-model="deleteSelectId" placeholder="请选择联系人" style="width: 100%">
          <el-option v-for="person in personList" :key="person.id" :label="person.real_name || person.username" :value="person.id">
            <el-avatar :size="20" :src="getAvatarUrl(person.avatar)" style="margin-right:6px;" @error="onAvatarError" />
            <span>{{ person.real_name || person.username }}</span>
          </el-option>
          <el-option v-for="group in groupList" :key="'group-' + group.id" :label="group.name + '（群聊）'" :value="'group-' + group.id">
            <el-avatar :size="20" icon="el-icon-user-solid" class="group-avatar" />
            <span>{{ group.name }}（群聊）</span>
          </el-option>
        </el-select>
        <template #footer>
          <el-button @click="deleteSelectVisible = false">取消</el-button>
          <el-button type="danger" :disabled="!deleteSelectId" @click="confirmDeleteSelected">下一步</el-button>
        </template>
      </el-dialog>
      <el-dialog v-model="deleteDialogVisible" title="确认删除" width="300px">
        <span>确定要删除该联系人吗？</span>
        <template #footer>
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="deleteContact">删除</el-button>
        </template>
      </el-dialog>
      <el-dialog v-model="showCreateGroup" title="创建群聊">
        <el-form :model="groupForm">
          <el-form-item label="群聊名称">
            <el-input v-model="groupForm.name" placeholder="请输入群聊名称" />
          </el-form-item>
          <el-form-item label="选择成员">
            <el-select v-model="groupForm.members" multiple filterable placeholder="请选择群成员">
              <el-option v-for="person in personList" :key="person.id" :label="person.real_name || person.username" :value="person.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateGroup = false">取消</el-button>
          <el-button type="primary" @click="createGroup">创建</el-button>
        </template>
      </el-dialog>
    </aside>
    <section class="chat-main">
      <div class="chat-header">
        <span>
          {{ currentGroup ? currentGroup.name + '（群聊）' : (currentPerson?.real_name || currentPerson?.username || '未选择联系人') }}
        </span>
      </div>
      <div v-if="currentGroup" class="chat-history" ref="historyRef">
        <div v-for="msg in groupMessages" :key="msg.id" :class="['chat-msg', Number(msg.user_id) === Number(myUserId) ? 'right' : 'left']">
          <el-avatar :size="32" :src="getAvatarUrl(msg.avatar)" @error="onAvatarError" />
          <div class="msg-content">
            <div class="msg-text">
              <span v-if="Number(msg.user_id) !== Number(myUserId)" class="sender-name">{{ msg.sender_name }}：</span>
              <span v-if="msg.type === 'image'">
                <img :src="getImageUrl(msg.content)" class="chat-image" @click="previewImage(msg.content)" />
              </span>
              <span v-else>{{ msg.content }}</span>
            </div>
            <div class="msg-time">{{ formatTime(msg.time) }}</div>
          </div>
        </div>
      </div>
      <div v-else-if="currentPerson" class="chat-history" ref="historyRef">
        <div v-if="messages.length === 0 && currentPerson && personList.some(p => p.id === currentPerson.id)" class="friend-tip">
          你们已成为好友，可以开始聊天了
        </div>
                  <div v-for="msg in messages" :key="msg.id" :class="['chat-msg', msg.from_user_id === myUserId ? 'right' : 'left']">
            <el-avatar :size="32" :src="msg.from_user_id === myUserId ? getAvatarUrl(myAvatar) : getAvatarUrl(currentPerson?.avatar)" @error="onAvatarError" />
          <div class="msg-content">
            <div class="msg-text">
              <span v-if="msg.type === 'image'">
                <img :src="getImageUrl(msg.content)" class="chat-image" @click="previewImage(msg.content)" />
              </span>
              <span v-else>{{ msg.content }}</span>
            </div>
            <div class="msg-time">{{ formatTime(msg.time) }}</div>
          </div>
        </div>
      </div>
      <div v-else class="chat-history empty">
        <span>请先选择联系人</span>
      </div>
      <div class="chat-input-bar">
        <div class="input-tools">
          <el-button size="small" @click="toggleEmojiPicker" style="margin-right: 8px;">
            <el-icon><ChatDotSquare /></el-icon>
          </el-button>
          <el-button size="small" @click="selectImage">
            <el-icon><Picture /></el-icon>
          </el-button>
          <input ref="imageInput" type="file" accept="image/*" @change="handleImageSelect" style="display: none" />
          <!-- 表情包选择器 -->
          <div v-if="showEmojiPicker" class="emoji-picker">
            <div class="emoji-grid">
              <span v-for="emoji in emojiList" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">
                {{ emoji }}
              </span>
            </div>
          </div>
        </div>
        <div class="input-main">
          <el-input v-model="inputMsg" type="textarea" :autosize="{minRows: 3, maxRows: 6}" placeholder="输入消息..." @keyup.enter.native="sendMsg" :disabled="!currentPerson && !currentGroup">
            <template #textarea>
              <div class="el-textarea__inner">
                {{ inputMsg }}
              </div>
            </template>
          </el-input>
          <el-button type="primary" @click="sendMsg" :disabled="!currentPerson && !currentGroup">发送</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Avatar, Picture, ChatDotSquare } from '@element-plus/icons-vue'
import api from '@/utils/http'
import { useUserStore } from '@/store/modules/user'

const defaultAvatar = '/avatar.png'
const personList = ref<any[]>([])
const currentPerson = ref<any>(null)
const messages = ref<any[]>([])
const inputMsg = ref('')
const historyRef = ref<HTMLElement | null>(null)
const myUserId = ref<number>(0)
const myAvatar = ref<string>('')

const showAdd = ref(false)
const addForm = ref({ contact_user_id: '' })
const userOptions = ref<any[]>([])
const userLoading = ref(false)

const sidebarTab = ref('contacts')
const pendingRequests = ref<any[]>([])
const myPendingRequests = ref<any[]>([])

let ws: WebSocket | null = null
let wsConnected = ref(false)
let reconnectTimer: any = null

const deleteDialogVisible = ref(false)
const contactToDelete = ref<any>(null)
const deleteSelectVisible = ref(false)
const deleteSelectId = ref('')

const showCreateGroup = ref(false)
const groupForm = reactive({ name: '', members: [] as any[] })

const groupList = ref<any[]>([])
const currentGroup = ref<any>(null)
const groupMessages = ref<any[]>([])

const userStore = useUserStore()

// 头像时间戳用于强制刷新
const avatarTimestamp = ref(Date.now())

// 未读消息计数相关
const unreadCounts = ref<{ [key: string]: number }>({})
const groupUnreadCounts = ref<{ [key: string]: number }>({})

// 获取个人未读消息数
const getUnreadCount = (userId: number) => {
  const key = String(userId)
  const count = unreadCounts.value[key] || unreadCounts.value[userId] || 0
  console.log(`用户 ${userId} 的未读消息数: ${count}`, '所有未读计数:', unreadCounts.value)
  return count
}

// 获取群聊未读消息数
const getGroupUnreadCount = (groupId: number) => {
  return groupUnreadCounts.value[groupId] || 0
}

// 更新未读消息计数
const updateUnreadCount = (userId: number, count: number) => {
  if (count <= 0) {
    delete unreadCounts.value[userId]
  } else {
    unreadCounts.value[userId] = count
  }
}

// 更新群聊未读消息计数
const updateGroupUnreadCount = (groupId: number, count: number) => {
  if (count <= 0) {
    delete groupUnreadCounts.value[groupId]
  } else {
    groupUnreadCounts.value[groupId] = count
  }
}

// 加载未读消息计数
const loadUnreadCounts = async () => {
  try {
    console.log('开始加载未读消息计数...')
    
    // 加载个人聊天未读消息计数
    const personalResponse = await api.get<{ code: number; data: { [key: string]: number } }>({ url: '/api/message/unread_counts' })
    console.log('个人聊天未读消息API响应:', personalResponse)
    
    if (personalResponse.code === 0) {
      unreadCounts.value = personalResponse.data || {}
      console.log('加载的未读消息计数:', unreadCounts.value)
    } else {
      console.error('个人聊天未读消息API返回错误:', personalResponse)
    }
    
    // 加载群聊未读消息计数
    const groupResponse = await api.get<{ code: number; data: { [key: string]: number } }>({ url: '/api/group/unread_counts' })
    console.log('群聊未读消息API响应:', groupResponse)
    
    if (groupResponse.code === 0) {
      groupUnreadCounts.value = groupResponse.data || {}
      console.log('加载的群聊未读消息计数:', groupUnreadCounts.value)
    } else {
      console.error('群聊未读消息API返回错误:', groupResponse)
    }
  } catch (error) {
    console.error('加载未读消息计数失败:', error)
  }
}

// 表情包和图片相关
const showEmojiPicker = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const emojiList = [
  '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '🫠', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🫢', '🫣', '🤫', '🤔', '🫡', '🤐', '🤨', '😐', '😑', '😶', '😶‍🌫️', '😏', '😒', '🙄', '😬', '😮‍💨', '🤥', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶', '🥴', '😵', '😵‍💫', '🤯', '🤠', '🥳', '🥸', '😎', '🤓', '🧐', '😕', '😟', '🙁', '☹️', '😮', '😯', '😲', '😳', '🥺', '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱', '😖', '😣', '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬', '😈', '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽', '👾', '🤖', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👏', '🙌', '🤲', '🤝', '🙏', '💪', '💋', '👀', '👄', '🫦', '👅', '💃', '🕺', '🎉', '🎊', '🎈', '🎁', '🎂', '🍰', '🧁', '🍭', '🍬', '🍫', '🍪', '🍩', '🍯', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🍾', '🥤', '☕', '🍵', '🥛', '🍼', '🥨', '🍕', '🍔', '🍟', '🌭', '🥪', '🌮', '🌯', '🥙', '🧆', '🥚', '🍳', '🥘', '🍲', '🥗', '🍿', '🧈', '🧀', '🥨', '🥖', '🍞', '🥐', '🥯', '🧇', '🥞', '🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔', '🍠', '🫘', '🥜', '🌰', '🥇', '🥈', '🥉', '🏆', '🏅', '🎖️', '🏵️', '🎗️', '🎫', '🎟️', '🎪', '🎭', '🎨', '🎬', '🎤', '🎧', '🎼', '🎵', '🎶', '🎹', '🥁', '🎷', '🎺', '🎸', '🪕', '🎻', '🎲', '♠️', '♥️', '♦️', '♣️', '♟️', '🃏', '🀄', '🎴', '🎯', '🎳', '🎮', '🎰', '🧩'
]

const getAvatarUrl = (avatar: string) => {
  if (!avatar) return defaultAvatar
  if (avatar.startsWith('http')) return avatar
  
  // 检查是否已经包含完整路径
  if (avatar.startsWith('/uploads/')) {
    return `${avatar}?t=${avatarTimestamp.value}`
  }
  
  // 如果只是文件名，添加完整路径
  if (!avatar.startsWith('/')) {
    return `/uploads/${avatar}?t=${avatarTimestamp.value}`
  }
  
  return `${avatar}?t=${avatarTimestamp.value}`
}

// 更新头像时间戳
const updateAvatarTimestamp = () => {
  avatarTimestamp.value = Date.now()
}

const availableUserOptions = computed(() => {
  const addedIds = personList.value.map(p => p.id)
  return userOptions.value.filter(u => !addedIds.includes(u.id))
})

function getToken() {
  return userStore.accessToken || localStorage.getItem('token') || ''
}

function connectWebSocket() {
  const token = getToken()
  if (!token) return
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://localhost:3007/ws/chat/user?token=${token}`
  ws = new WebSocket(wsUrl)
  ws.onopen = () => {
    wsConnected.value = true
  }
  ws.onclose = () => {
    wsConnected.value = false
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }
  ws.onerror = () => {
    wsConnected.value = false
    ws?.close()
  }
  ws.onmessage = (event) => {
    console.log('WS收到消息:', event.data)
    try {
      const msg = JSON.parse(event.data)
      console.log('WS解析后:', msg, '当前聊天对象:', currentPerson.value)
      
      // 如果是群聊消息
      if (msg.group_id) {
        // 如果当前不在这个群聊中，增加未读计数
        if (!currentGroup.value || currentGroup.value.id !== msg.group_id) {
          const currentCount = getGroupUnreadCount(msg.group_id)
          updateGroupUnreadCount(msg.group_id, currentCount + 1)
        } else {
          // 如果正在这个群聊中，直接添加消息
          groupMessages.value.push(msg)
        }
      } else {
        // 个人消息
        // 如果当前不在这个聊天中，增加未读计数
        if (!currentPerson.value || currentPerson.value.id !== msg.from_user_id) {
          const currentCount = getUnreadCount(msg.from_user_id)
          updateUnreadCount(msg.from_user_id, currentCount + 1)
        } else {
          // 如果正在这个聊天中，直接添加消息并标记为已读
      messages.value.push(msg)
          // 自动标记为已读
          api.post({ url: '/api/message/read', data: { msg_id: msg.id } })
        }
      }
      
      nextTick(() => {
        if (historyRef.value) {
          historyRef.value.scrollTop = historyRef.value.scrollHeight
        }
      })
    } catch (e) {
      console.error('WS消息解析异常:', e)
    }
  }
}

function closeWebSocket() {
  if (ws) {
    ws.close()
    ws = null
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function loadContacts() {
  api.get<{ code: number; data: any[] }>({ url: '/api/contact/list' }).then((res) => {
    if (res.code === 0) {
      personList.value = res.data
      if (!currentPerson.value && personList.value.length > 0) {
        currentPerson.value = personList.value[0]
      }
      if (personList.value.length === 0) {
        currentPerson.value = null
      }
      if (currentPerson.value) {
        loadMessages()
      }
    }
  })
}

function loadAvailableUsers() {
  userLoading.value = true
  api.get({ url: '/api/contact/available' }).then((res: any) => {
    userOptions.value = res.data || []
    userLoading.value = false
  }).catch(() => {
    userLoading.value = false
  })
}

function addContact() {
  if (!addForm.value.contact_user_id) return
  api.post<{ code: number; msg?: string }>({
    url: '/api/contact/add',
    data: { contact_user_id: addForm.value.contact_user_id }
  }).then((res) => {
    if (res.code === 0) {
      ElMessage.success('好友申请已发送')
      showAdd.value = false
      addForm.value = { contact_user_id: '' }
      loadContacts()
      loadMyPendingRequests()
    } else {
      ElMessage.error(res.msg || '操作失败')
    }
  })
}

function selectPerson(person: any) {
  currentPerson.value = person
  currentGroup.value = null
  // 清除该联系人的未读消息计数
  updateUnreadCount(person.id, 0)
  loadMessages()
}

function loadMessages() {
  if (!currentPerson.value) return
  api.get<{ code: number; data: any[] }>({ url: '/api/message/history', params: { to_user_id: currentPerson.value.id } }).then((res) => {
    messages.value = res.data || []
    nextTick(() => {
      if (historyRef.value) {
        historyRef.value.scrollTop = historyRef.value.scrollHeight
      }
    })
    markAllAsRead()
  })
}

function markAllAsRead() {
  const unreadIds = messages.value
    .filter(msg => msg.to_user_id === myUserId.value && msg.is_read === 0)
    .map(msg => msg.id)
  unreadIds.forEach(id => {
    api.post({ url: '/api/message/read', data: { msg_id: id } })
  })
  
  // 清除当前聊天对象的未读计数
  if (currentPerson.value) {
    updateUnreadCount(currentPerson.value.id, 0)
  }
}

function sendMsg() {
  const text = inputMsg.value.trim()
  if (!text) return

  if (currentGroup.value) {
    api.post<{ code: number; msg?: string }>({
      url: '/api/group/send_message',
      data: { group_id: currentGroup.value.id, content: text }
    }).then((res) => {
      if (res.code === 0) {
        // 立即添加到本地群聊消息列表
        groupMessages.value.push({
          id: Date.now(), // 临时ID
          user_id: myUserId.value,
          content: text,
          time: new Date().toISOString(),
          sender_name: userStore.info?.realName || userStore.info?.userName || 'Me',
          avatar: myAvatar.value
        })
        
        inputMsg.value = ''
        
        // 滚动到底部
        nextTick(() => {
          if (historyRef.value) {
            historyRef.value.scrollTop = historyRef.value.scrollHeight
          }
        })
      }
    })
    return
  }

  if (!currentPerson.value) return
  if (ws && wsConnected.value) {
    const msgObj = {
      from_user_id: myUserId.value,
      to_user_id: currentPerson.value.id,
      content: text,
      time: new Date().toISOString()
    }
    ws.send(JSON.stringify(msgObj))
    
    // 立即添加到本地消息列表
    messages.value.push({
      id: Date.now(), // 临时ID
      from_user_id: myUserId.value,
      to_user_id: currentPerson.value.id,
      content: text,
      time: new Date().toISOString(),
      is_read: 1
    })
    
    inputMsg.value = ''
    
    // 滚动到底部
    nextTick(() => {
      if (historyRef.value) {
        historyRef.value.scrollTop = historyRef.value.scrollHeight
      }
    })
  } else {
    api.post<{ code: number; msg?: string }>({ url: '/api/message/send', data: { to_user_id: currentPerson.value.id, content: text } }).then((res) => {
      if (res.code === 0) {
        inputMsg.value = ''
        loadMessages()
      }
    })
  }
}

function onAvatarError(e: Event) {
  const target = e.target as HTMLImageElement | null
  if (target && !target.src.endsWith(defaultAvatar)) target.src = defaultAvatar
}

function loadMyInfo() {
  api.get<{ code: number; data: any }>({ url: '/auth/getUserInfo' }).then((res) => {
    if (res.code === 0) {
      myUserId.value = res.data.userId
      myAvatar.value = res.data.avatar || defaultAvatar
      
      // 同步到userStore
      if (userStore.info) {
        userStore.info.avatar = res.data.avatar || defaultAvatar
      }
      
      updateAvatarTimestamp()
    }
  })
}

// 监听用户状态变化，同步头像
watch(() => userStore.info?.avatar, (newAvatar) => {
  if (newAvatar) {
    myAvatar.value = newAvatar
    updateAvatarTimestamp() // 更新时间戳强制刷新
  }
}, { immediate: true })

// 同时监听用户信息变化
watch(() => userStore.info, (newInfo) => {
  if (newInfo?.avatar) {
    myAvatar.value = newInfo.avatar
    updateAvatarTimestamp()
  }
}, { deep: true, immediate: true })

function loadPendingRequests() {
  api.get<{ code: number; data: any[] }>({ url: '/api/contact/requests' }).then((res) => {
    if (res.code === 0) {
      pendingRequests.value = res.data
    }
  })
}

function loadMyPendingRequests() {
  api.get<{ code: number; data: any[] }>({ url: '/api/contact/my_requests' }).then((res) => {
    if (res.code === 0) {
      myPendingRequests.value = res.data
    }
  })
}

function openDeleteDialog() {
  deleteSelectId.value = ''
  deleteSelectVisible.value = true
}

function confirmDeleteSelected() {
  if (!deleteSelectId.value) return
  if (typeof deleteSelectId.value === 'string' && deleteSelectId.value.startsWith('group-')) {
    const groupId = deleteSelectId.value.replace('group-', '')
    contactToDelete.value = { id: groupId, isGroup: true }
    deleteDialogVisible.value = true
  } else {
    const person = personList.value.find(p => p.id === deleteSelectId.value)
    if (person) {
      contactToDelete.value = person
      deleteDialogVisible.value = true
    }
  }
  deleteSelectVisible.value = false
}

function deleteContact() {
  if (!contactToDelete.value) return
  if (contactToDelete.value.isGroup) {
    api.post<{ code: number; msg?: string }>({ url: '/api/group/delete', data: { group_id: contactToDelete.value.id } }).then((res: { code: number; msg?: string }) => {
      if (res.code === 0) {
        ElMessage.success('群聊删除成功')
        loadGroups()
        if (currentGroup.value && currentGroup.value.id == contactToDelete.value.id) {
          currentGroup.value = null
        }
      } else {
        ElMessage.error(res.msg || '群聊删除失败')
      }
      deleteDialogVisible.value = false
      contactToDelete.value = null
    })
  } else {
    api.post<{ code: number; msg?: string }>({ url: '/api/contact/delete', data: { id: contactToDelete.value.id } }).then((res) => {
      if (res.code === 0) {
        ElMessage.success('删除成功')
        personList.value = personList.value.filter(p => p.id !== contactToDelete.value.id)
        loadContacts()
        if (currentPerson.value && currentPerson.value.id === contactToDelete.value.id) {
          currentPerson.value = null
        }
      } else {
        ElMessage.error(res.msg || '删除失败')
      }
      deleteDialogVisible.value = false
      contactToDelete.value = null
    })
  }
}

function handleRequest(req: any, action: 'accept' | 'reject') {
  api.post<{ code: number; msg?: string }>({
    url: '/api/contact/handle_request',
    data: { request_id: req.request_id, action }
  }).then((res) => {
    if (res.code === 0) {
      ElMessage.success(action === 'accept' ? '已同意' : '已拒绝')
      loadPendingRequests()
      loadContacts()
    } else {
      ElMessage.error(res.msg || '操作失败')
    }
  })
}

function createGroup() {
  if (!groupForm.name || groupForm.members.length === 0) {
    ElMessage.warning('请填写群聊名称并选择成员')
    return
  }
  api.post<{ code: number; msg?: string }>({
    url: '/api/group/create',
    data: { name: groupForm.name, members: groupForm.members }
  }).then((res) => {
    if (res.code === 0) {
      ElMessage.success('群聊创建成功')
      showCreateGroup.value = false
      groupForm.name = ''
      groupForm.members = []
      loadContactsAndGroups()
      groupMessages.value = []
    } else {
      ElMessage.error(res.msg || '创建失败')
    }
  })
}

function loadGroups() {
  api.get<{ code: number; data: any[] }>({ url: '/api/group/list' }).then((res) => {
    if (res.code === 0) {
      groupList.value = res.data || []
    }
  })
}

function selectGroup(group: any) {
  currentGroup.value = group
  currentPerson.value = null
  // 清除该群聊的未读消息计数
  updateGroupUnreadCount(group.id, 0)
  loadGroupMessages()
}

function loadGroupMessages() {
  if (!currentGroup.value) return
  api.get<{ code: number; data: any[] }>({
    url: '/api/group/messages',
    params: { group_id: currentGroup.value.id }
  }).then((res) => {
    groupMessages.value = res.data || []
    nextTick(() => {
      if (historyRef.value) {
        historyRef.value.scrollTop = historyRef.value.scrollHeight
      }
    })
  })
}

function loadContactsAndGroups() {
  loadContacts()
  loadGroups()
}

function formatTime(time: string) {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return time
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}

// 选择图片
function selectImage() {
  imageInput.value?.click()
}

// 处理图片选择
function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  
  // 验证文件大小（限制5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }
  
  // 上传图片
  uploadImage(file)
}

// 上传图片
async function uploadImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await api.post<{ code: number; data: { url: string } }>({
      url: '/api/upload/image',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.code === 0) {
      // 发送图片消息
      sendImageMessage(res.data.url)
    } else {
      ElMessage.error('图片上传失败')
    }
  } catch (error) {
    ElMessage.error('图片上传失败')
  }
}

// 发送图片消息
function sendImageMessage(imageUrl: string) {
  if (currentGroup.value) {
    api.post<{ code: number; msg?: string }>({
      url: '/api/group/send_message',
      data: { group_id: currentGroup.value.id, content: imageUrl, type: 'image' }
    }).then((res) => {
      if (res.code === 0) {
        loadGroupMessages()
      }
    })
    return
  }
  
  if (!currentPerson.value) return
  
  const msgObj = {
    from_user_id: myUserId.value,
    to_user_id: currentPerson.value.id,
    content: imageUrl,
    type: 'image',
    time: new Date().toISOString()
  }
  
  if (ws && wsConnected.value) {
    ws.send(JSON.stringify(msgObj))
  } else {
    api.post<{ code: number; msg?: string }>({
      url: '/api/message/send',
      data: { to_user_id: currentPerson.value.id, content: imageUrl, type: 'image' }
    }).then((res) => {
      if (res.code === 0) {
        loadMessages()
      }
    })
  }
}

// 切换表情包选择器
function toggleEmojiPicker() {
  showEmojiPicker.value = !showEmojiPicker.value
}

// 插入表情包
function insertEmoji(emoji: string) {
  inputMsg.value += emoji
  showEmojiPicker.value = false
}

// 获取图片URL
function getImageUrl(imagePath: string) {
  if (!imagePath) return ''
  if (imagePath.startsWith('http')) return imagePath
  return `http://localhost:3007${imagePath}`
}

// 图片预览
function previewImage(imagePath: string) {
  const imageUrl = getImageUrl(imagePath)
  window.open(imageUrl, '_blank')
}

watch(showAdd, (val) => {
  if (val) {
    loadAvailableUsers()
  }
})

// 点击外部关闭表情包选择器
function handleOutsideClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.emoji-picker') && !target.closest('.input-tools')) {
    showEmojiPicker.value = false
  }
}

onMounted(() => {
  loadMyInfo()
  loadContactsAndGroups()
  loadPendingRequests()
  loadMyPendingRequests()
  loadUnreadCounts()
  connectWebSocket()
  
  // 添加点击外部关闭表情包选择器的监听器
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  closeWebSocket()
  
  // 移除点击外部关闭表情包选择器的监听器
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 130px);
  background: var(--el-bg-color-page);
}
.chat-sidebar {
  width: 250px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  color: var(--el-text-color-primary);
}
.person-list {
  flex: 1;
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
}
.person-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background 0.2s;
  color: var(--el-text-color-primary);
}
.person-list li:hover {
  background: var(--el-fill-color-light);
}
.person-list li.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.person-name {
  font-size: 15px;
  font-weight: 500;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
  min-width: 0;
}
.chat-header {
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
}
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px 0 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: var(--el-bg-color-page);
}
.chat-history.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}
.chat-msg {
  display: flex;
  align-items: center;
  gap: 12px;
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
}
.chat-msg.right .msg-content {
  align-items: flex-end;
}
.msg-text {
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  padding: 10px 16px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.7;
  word-break: break-all;
  box-shadow: var(--el-box-shadow-light);
  margin-bottom: 2px;
  border: 1px solid var(--el-border-color-lighter);
  max-width: 70%;
  max-width: min(70%, 400px);
  overflow: hidden;
}

.msg-text img {
  max-width: 100%;
  height: auto;
  display: block;
}
.chat-msg.right .msg-text {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}
.msg-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin: 2px 0 0 8px;
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

.input-tools .el-button-group {
  display: flex;
  gap: 4px;
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
  width: 380px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-color-primary);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  max-height: 280px;
  overflow-y: auto;
  padding: 12px;
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
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
  padding: 4px;
}

.emoji-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
  font-size: 20px;
  background: var(--el-fill-color-lighter);
}

.emoji-item:hover {
  background: var(--el-color-primary-light-8);
  transform: scale(1.1);
}

.chat-image {
  max-width: 200px;
  max-height: 200px;
  width: auto;
  height: auto;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: var(--el-box-shadow-light);
  display: block;
  object-fit: cover;
}

.chat-image:hover {
  transform: scale(1.02);
}





.chat-input-bar .el-textarea__inner {
  min-height: 100px;
  font-size: 16px;
  line-height: 1.6;
}

.sidebar-tabs {
  margin-bottom: 0;
}

.sidebar-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: var(--el-bg-color);
}

.sidebar-tabs :deep(.el-tabs__nav-wrap) {
  background: var(--el-bg-color);
}

.sidebar-tabs :deep(.el-tabs__content) {
  color: var(--el-text-color-primary);
}

.chat-action-btns {
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  margin: 10px 0 0 0;
}

.friend-tip {
  text-align: center;
  color: var(--el-text-color-placeholder);
  margin: 30px 0;
  font-size: 16px;
}

.dark .msg-text {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.dark .chat-input-bar {
  box-shadow: 0 -2px 24px rgba(0, 0, 0, 0.3);
}

.dark .person-list li:hover {
  background: var(--el-fill-color);
}

.group-tag {
  color: var(--el-color-success);
  font-size: 12px;
  margin-left: 8px;
  background: var(--el-color-success-light-9);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.pending-tag {
  color: var(--el-color-warning);
  font-size: 12px;
  margin-left: 8px;
  background: var(--el-color-warning-light-9);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.group-avatar {
  background: var(--el-color-success) !important;
  margin-right: 6px;
}

.sender-name {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 500;
}

.person-list::-webkit-scrollbar,
.chat-history::-webkit-scrollbar {
  width: 6px;
}

.person-list::-webkit-scrollbar-track,
.chat-history::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
}

.person-list::-webkit-scrollbar-thumb,
.chat-history::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.person-list::-webkit-scrollbar-thumb:hover,
.chat-history::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

/* 未读消息红点样式 */
.person-avatar-container {
  position: relative;
  display: inline-block;
}

.unread-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: var(--el-color-danger);
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: bold;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  border: 2px solid var(--el-bg-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.unread-badge:empty {
  display: none;
}

/* 未读消息列表项样式 */
.person-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.person-list li .person-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
