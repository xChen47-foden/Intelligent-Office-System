<template>
  <div class="chat-page">
    <aside class="chat-sidebar">
      <div class="sidebar-header">联系人</div>
      <ul class="person-list">
        <li v-for="person in personList" :key="person.id" :class="{active: person.id === currentPerson.id}" @click="selectPerson(person)">
          <el-avatar :size="36" :src="person.avatar" />
          <span class="person-name">{{ person.name }}</span>
        </li>
      </ul>
    </aside>
    <section class="chat-main">
      <div class="chat-header">
        <span>{{ currentPerson.name }}</span>
      </div>
      <div class="chat-history" ref="historyRef">
        <div v-for="msg in messages" :key="msg.id" :class="['chat-msg', msg.isMe ? 'right' : 'left']">
          <el-avatar :size="32" :src="msg.avatar" />
          <div class="msg-content">
            <div class="msg-text">{{ msg.content }}</div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>
      </div>
      <div class="chat-input-bar">
        <el-input v-model="inputMsg" type="textarea" :autosize="{minRows: 2, maxRows: 4}" placeholder="输入消息..." @keyup.enter.native="sendMsg" />
        <el-button type="primary" @click="sendMsg">发送</el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const personList = ref([])
const currentPerson = ref(null)
const messages = ref([])
const inputMsg = ref('')
const historyRef = ref<HTMLElement | null>(null)

function selectPerson(person: any) {
  currentPerson.value = person
  messages.value = []
}

function sendMsg() {
  const text = inputMsg.value.trim()
  if (!text) return
  messages.value.push({
    id: Date.now(),
    content: text,
    isMe: true,
    avatar: 'https://api.multiavatar.com/me.svg',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })
  inputMsg.value = ''
  nextTick(() => {
    if (historyRef.value) {
      historyRef.value.scrollTop = historyRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
  background: #f7f8fa;
}
.chat-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid #f0f0f0;
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
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}
.person-list li.active {
  background: #e6f0ff;
}
.person-name {
  font-size: 15px;
  font-weight: 500;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
  min-width: 0;
  position: relative;
}
.chat-header {
  padding: 18px 16px 8px 16px;
  font-weight: bold;
  border-bottom: 1px solid #f0f0f0;
}
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px 80px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.chat-msg {
  display: flex;
  align-items: flex-end;
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
}
.chat-msg.right .msg-content {
  align-items: flex-end;
}
.msg-text {
  background: #fff;
  padding: 10px 16px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.7;
  word-break: break-all;
  box-shadow: 0 2px 12px #e6eaf1;
  margin-bottom: 2px;
}
.msg-time {
  font-size: 12px;
  color: #aaa;
  margin: 2px 0 0 8px;
  text-align: left;
}
.chat-msg.right .msg-time {
  text-align: right;
  margin-left: 0;
  margin-right: 8px;
}
.chat-input-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
  padding: 8px 12px 8px 12px;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 24px #e6eaf1;
  border-radius: 0 0 0 18px;
  z-index: 10;
}
</style> 