<template>
  <div class="simple-editor">
    <div class="editor-toolbar">
      <el-button size="small" @click="execCommand('bold')"><span class="icon-text">B</span></el-button>
      <el-button size="small" @click="execCommand('italic')"><span class="icon-text">I</span></el-button>
      <el-button size="small" @click="execCommand('underline')"><span class="icon-text">U</span></el-button>
      <el-divider direction="vertical" />
      <el-button size="small" @click="execCommand('justifyLeft')">左对齐</el-button>
      <el-button size="small" @click="execCommand('justifyCenter')">居中</el-button>
      <el-button size="small" @click="execCommand('justifyRight')">右对齐</el-button>
      <el-divider direction="vertical" />
      <el-button size="small" @click="execCommand('insertUnorderedList')">无序列表</el-button>
      <el-button size="small" @click="execCommand('insertOrderedList')">有序列表</el-button>
      <el-divider direction="vertical" />
      <el-button size="small" @click="execCommand('formatBlock', 'h1')">标题1</el-button>
      <el-button size="small" @click="execCommand('formatBlock', 'h2')">标题2</el-button>
      <el-button size="small" @click="execCommand('formatBlock', 'p')">段落</el-button>
    </div>
    
    <div 
      ref="editorRef"
      class="editor-content"
      contenteditable="true"
      @input="onInput"
      @keydown="onKeyDown"
      v-html="modelValue"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElButton, ElIcon, ElDivider } from 'element-plus'

const modelValue = defineModel<string>({ required: true })

const editorRef = ref<HTMLElement>()

// 执行编辑命令
function execCommand(command: string, value?: string) {
  document.execCommand(command, false, value)
  editorRef.value?.focus()
  updateContent()
}

// 更新内容
function updateContent() {
  if (editorRef.value) {
    modelValue.value = editorRef.value.innerHTML
  }
}

// 输入事件
function onInput() {
  updateContent()
}

// 按键事件
function onKeyDown(event: KeyboardEvent) {
  // 支持常用快捷键
  if (event.ctrlKey || event.metaKey) {
    switch(event.key) {
      case 'b':
        event.preventDefault()
        execCommand('bold')
        break
      case 'i':
        event.preventDefault()
        execCommand('italic')
        break
      case 'u':
        event.preventDefault()
        execCommand('underline')
        break
    }
  }
}

onMounted(() => {
  // 初始化编辑器内容
  nextTick(() => {
    if (editorRef.value && modelValue.value) {
      editorRef.value.innerHTML = modelValue.value
    }
  })
})
</script>

<style scoped>
.simple-editor {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color);
  flex-wrap: wrap;
}

.editor-content {
  min-height: 400px;
  padding: 16px;
  outline: none;
  line-height: 1.6;
  font-size: 14px;
  overflow-y: auto;
  max-height: 600px;
}

.editor-content:focus {
  outline: none;
}

.editor-content p {
  margin: 8px 0;
}

.editor-content h1, .editor-content h2, .editor-content h3 {
  margin: 16px 0 8px 0;
  font-weight: 600;
}

.editor-content h1 {
  font-size: 24px;
  color: var(--el-color-primary);
}

.editor-content h2 {
  font-size: 20px;
  color: var(--el-color-primary);
}

.editor-content h3 {
  font-size: 18px;
  color: var(--el-color-primary);
}

.editor-content ul, .editor-content ol {
  padding-left: 24px;
  margin: 12px 0;
}

.editor-content li {
  margin: 4px 0;
}

.icon-text { font-weight: bold; font-size: 14px; }
</style> 