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
      <el-divider direction="vertical" />
      <el-button size="small" @click="insertImage">📷 图片</el-button>
      <el-button size="small" @click="insertTable">📊 表格</el-button>
      <el-button size="small" @click="insertCodeBlock">💻 代码块</el-button>
    </div>
    
    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleImageUpload"
    />
    
    <!-- 表格插入对话框 -->
    <el-dialog v-model="showTableDialog" title="插入表格" width="400px">
      <el-form :model="tableConfig" label-width="80px">
        <el-form-item label="行数">
          <el-input-number v-model="tableConfig.rows" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="列数">
          <el-input-number v-model="tableConfig.cols" :min="1" :max="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTableDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmInsertTable">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 代码块插入对话框 -->
    <el-dialog v-model="showCodeDialog" title="插入代码块" width="500px">
      <el-form :model="codeConfig" label-width="80px">
        <el-form-item label="语言">
          <el-select v-model="codeConfig.language" placeholder="选择语言（可选）">
            <el-option label="无" value="" />
            <el-option label="JavaScript" value="javascript" />
            <el-option label="TypeScript" value="typescript" />
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
            <el-option label="C++" value="cpp" />
            <el-option label="CSS" value="css" />
            <el-option label="HTML" value="html" />
            <el-option label="SQL" value="sql" />
            <el-option label="JSON" value="json" />
            <el-option label="Markdown" value="markdown" />
          </el-select>
        </el-form-item>
        <el-form-item label="代码">
          <el-input
            v-model="codeConfig.code"
            type="textarea"
            :rows="10"
            placeholder="输入代码..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCodeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmInsertCode">确定</el-button>
      </template>
    </el-dialog>
    
    <div 
      ref="editorRef"
      class="editor-content"
      contenteditable="true"
      @input="onInput"
      @keydown="onKeyDown"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElButton, ElIcon, ElDivider, ElDialog, ElForm, ElFormItem, ElInputNumber, ElSelect, ElOption, ElInput, ElMessage } from 'element-plus'
import axios from 'axios'

const modelValue = defineModel<string>({ required: true })

const editorRef = ref<HTMLElement>()
const fileInputRef = ref<HTMLInputElement>()
const isInternalUpdate = ref(false) // 标记是否是内部更新

// 表格插入相关
const showTableDialog = ref(false)
const tableConfig = ref({ rows: 3, cols: 3 })

// 代码块插入相关
const showCodeDialog = ref(false)
const codeConfig = ref({ language: '', code: '' })

// 保存光标位置
function saveSelection() {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0 || !editorRef.value) return null
  
  const range = selection.getRangeAt(0)
  const preCaretRange = range.cloneRange()
  preCaretRange.selectNodeContents(editorRef.value)
  preCaretRange.setEnd(range.endContainer, range.endOffset)
  
  return preCaretRange.toString().length
}

// 恢复光标位置
function restoreSelection(caretPosition: number | null) {
  if (caretPosition === null || !editorRef.value) return
  
  const selection = window.getSelection()
  if (!selection) return
  
  const range = document.createRange()
  let charCount = 0
  const walker = document.createTreeWalker(
    editorRef.value,
    NodeFilter.SHOW_TEXT,
    null
  )
  
  let node: Node | null
  while ((node = walker.nextNode())) {
    const nodeLength = node.textContent?.length || 0
    if (charCount + nodeLength >= caretPosition) {
      range.setStart(node, caretPosition - charCount)
      range.setEnd(node, caretPosition - charCount)
      break
    }
    charCount += nodeLength
  }
  
  // 如果没有找到文本节点，将光标移到末尾
  if (!range.startContainer || range.startContainer === editorRef.value) {
    range.selectNodeContents(editorRef.value)
    range.collapse(false)
  }
  
  selection.removeAllRanges()
  selection.addRange(range)
}

// 执行编辑命令
function execCommand(command: string, value?: string) {
  if (!editorRef.value) return
  
  editorRef.value.focus()
  document.execCommand(command, false, value)
  updateContent()
}

// 更新内容
function updateContent() {
  if (editorRef.value) {
    isInternalUpdate.value = true
    modelValue.value = editorRef.value.innerHTML
    // 使用 nextTick 确保在下一个事件循环中重置标记
    nextTick(() => {
      isInternalUpdate.value = false
    })
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

// 监听外部值变化（只在非内部更新时同步）
watch(modelValue, (newValue) => {
  if (!isInternalUpdate.value && editorRef.value && editorRef.value.innerHTML !== newValue) {
    // 保存光标位置
    const savedCaretPosition = saveSelection()
    
    // 更新内容
    editorRef.value.innerHTML = newValue || ''
    
    // 恢复光标位置
    nextTick(() => {
      if (savedCaretPosition !== null) {
        restoreSelection(savedCaretPosition)
      } else {
        // 如果没有保存的位置，将光标移到末尾
        editorRef.value?.focus()
        const selection = window.getSelection()
        if (selection && editorRef.value) {
          const range = document.createRange()
          range.selectNodeContents(editorRef.value)
          range.collapse(false)
          selection.removeAllRanges()
          selection.addRange(range)
        }
      }
    })
  }
})

// 插入图片
function insertImage() {
  fileInputRef.value?.click()
}

// 处理图片上传
async function handleImageUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  
  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }
  
  try {
    // 创建本地预览URL
    const localUrl = URL.createObjectURL(file)
    
    // 先插入本地预览图片
    insertImageAtCursor(localUrl, file.name)
    
    // 上传到服务器
    const formData = new FormData()
    formData.append('file', file)
    
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = {
      'Content-Type': 'multipart/form-data'
    }
    if (token) {
      headers['Authorization'] = 'Bearer ' + token
    }
    
    const response = await axios.post('/api/upload/image', formData, { headers })
    
    if (response.data?.code === 0 && response.data?.data?.url) {
      // 上传成功，替换为服务器URL
      const serverUrl = response.data.data.url
      replaceLastImage(localUrl, serverUrl)
      ElMessage.success('图片上传成功')
    } else {
      ElMessage.warning('图片上传失败，使用本地预览')
    }
  } catch (error) {
    console.error('图片上传失败:', error)
    ElMessage.error('图片上传失败')
  } finally {
    // 清空文件输入
    if (target) {
      target.value = ''
    }
  }
}

// 在光标位置插入图片
function insertImageAtCursor(imageUrl: string, alt: string = '') {
  if (!editorRef.value) return
  
  editorRef.value.focus()
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) {
    // 如果没有选择，在末尾插入
    const img = document.createElement('img')
    img.src = imageUrl
    img.alt = alt
    img.style.maxWidth = '100%'
    img.style.height = 'auto'
    editorRef.value.appendChild(img)
  } else {
    const range = selection.getRangeAt(0)
    const img = document.createElement('img')
    img.src = imageUrl
    img.alt = alt
    img.style.maxWidth = '100%'
    img.style.height = 'auto'
    range.insertNode(img)
    // 将光标移到图片后面
    range.setStartAfter(img)
    range.collapse(true)
    selection.removeAllRanges()
    selection.addRange(range)
  }
  updateContent()
}

// 获取API基础URL
function getApiBaseURL(): string {
  if (import.meta.env.VITE_API_URL) {
    const apiUrl = import.meta.env.VITE_API_URL
    if (apiUrl.startsWith('http://') || apiUrl.startsWith('https://')) {
      return apiUrl
    }
    return apiUrl
  }
  return import.meta.env.DEV ? '' : window.location.origin
}

// 替换最后插入的图片
function replaceLastImage(oldUrl: string, newUrl: string) {
  if (!editorRef.value) return
  
  const images = editorRef.value.querySelectorAll('img')
  for (let i = images.length - 1; i >= 0; i--) {
    if (images[i].src === oldUrl || images[i].src.includes(oldUrl)) {
      // 如果newUrl已经是完整URL，直接使用；否则拼接API基础URL
      if (newUrl.startsWith('http://') || newUrl.startsWith('https://')) {
        images[i].src = newUrl
      } else {
        images[i].src = `${getApiBaseURL()}${newUrl}`
      }
      break
    }
  }
  updateContent()
}

// 插入表格
function insertTable() {
  tableConfig.value = { rows: 3, cols: 3 }
  showTableDialog.value = true
}

// 确认插入表格
function confirmInsertTable() {
  if (!editorRef.value) return
  
  const rows = tableConfig.value.rows
  const cols = tableConfig.value.cols
  
  editorRef.value.focus()
  const selection = window.getSelection()
  const range = selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null
  
  // 创建表格HTML
  let tableHtml = '<table style="border-collapse: collapse; width: 100%; margin: 16px 0;"><tbody>'
  for (let i = 0; i < rows; i++) {
    tableHtml += '<tr>'
    for (let j = 0; j < cols; j++) {
      tableHtml += '<td style="border: 1px solid #ddd; padding: 8px;">&nbsp;</td>'
    }
    tableHtml += '</tr>'
  }
  tableHtml += '</tbody></table>'
  
  if (range) {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = tableHtml
    const table = tempDiv.firstElementChild
    if (table) {
      range.insertNode(table)
      // 将光标移到表格后面
      range.setStartAfter(table)
      range.collapse(true)
      selection?.removeAllRanges()
      selection?.addRange(range)
    }
  } else {
    // 如果没有选择，在末尾插入
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = tableHtml
    const table = tempDiv.firstElementChild
    if (table) {
      editorRef.value.appendChild(table)
    }
  }
  
  updateContent()
  showTableDialog.value = false
}

// 插入代码块
function insertCodeBlock() {
  codeConfig.value = { language: '', code: '' }
  showCodeDialog.value = true
}

// 确认插入代码块
function confirmInsertCode() {
  if (!editorRef.value) return
  
  const language = codeConfig.value.language
  const code = codeConfig.value.code
  
  if (!code.trim()) {
    ElMessage.warning('请输入代码')
    return
  }
  
  editorRef.value.focus()
  const selection = window.getSelection()
  const range = selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null
  
  // 创建代码块HTML
  const codeBlock = document.createElement('pre')
  codeBlock.style.cssText = 'background: #f5f5f5; padding: 16px; border-radius: 4px; overflow-x: auto; margin: 16px 0; font-family: "Courier New", monospace;'
  
  const codeElement = document.createElement('code')
  if (language) {
    codeElement.className = `language-${language}`
  }
  codeElement.textContent = code
  codeBlock.appendChild(codeElement)
  
  if (range) {
    range.insertNode(codeBlock)
    // 将光标移到代码块后面
    range.setStartAfter(codeBlock)
    range.collapse(true)
    selection?.removeAllRanges()
    selection?.addRange(range)
  } else {
    // 如果没有选择，在末尾插入
    editorRef.value.appendChild(codeBlock)
  }
  
  updateContent()
  showCodeDialog.value = false
}

onMounted(() => {
  // 初始化编辑器内容
  nextTick(() => {
    if (editorRef.value) {
      editorRef.value.innerHTML = modelValue.value || ''
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

.editor-content img {
  max-width: 100%;
  height: auto;
  margin: 8px 0;
  border-radius: 4px;
}

.editor-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.editor-content table td,
.editor-content table th {
  border: 1px solid var(--el-border-color);
  padding: 8px;
  text-align: left;
}

.editor-content table th {
  background: var(--el-fill-color-lighter);
  font-weight: 600;
}

.editor-content pre {
  background: var(--el-fill-color-lighter);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 16px 0;
  font-family: "Courier New", monospace;
  border: 1px solid var(--el-border-color);
}

.editor-content code {
  font-family: "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
}

.icon-text { font-weight: bold; font-size: 14px; }
</style> 