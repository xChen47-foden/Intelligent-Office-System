<template>
  <div class="smart-doc-page">
    <el-card shadow="hover" class="main-card">
      <div class="header-row">
        <h2 class="page-title">智能文档</h2>
        <div class="desc">支持文档上传、检索、智能编辑与管理</div>
      </div>
      <el-divider />
      <!-- 上传与检索区 -->
      <div class="top-actions">
        <el-upload
          :action="uploadUrl"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :before-upload="beforeUpload"
          :headers="headers"
          :data="{}"
          name="file"
        >
          <el-button type="primary" :icon="Upload">导入文档</el-button>
        </el-upload>
        <el-input v-model="searchVal" placeholder="请输入文档标题关键词" style="width: 260px" clearable @keyup.enter="searchDocs" />
        <el-button type="primary" @click="searchDocs" :icon="Search">搜索</el-button>
      </div>
      <el-divider />
      <!-- 文档列表 -->
      <div class="doc-list-section">
        <h3 class="section-title">文档列表</h3>
        <el-table
          :data="docList"
          style="width: 100%"
          v-loading="loading"
          stripe
          highlight-current-row
        >
          <el-table-column prop="id" label="ID" width="60"/>
          <el-table-column prop="filename" label="文件名"/>
          <el-table-column prop="upload_time" label="上传时间"/>
          <el-table-column prop="snippet" label="内容片段">
            <template #default="scope">
              <span v-html="highlight(scope.row.snippet)"></span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="260">
            <template #default="scope">
              <el-space>
                <el-button size="small" @click="editDoc(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteDoc(scope.row)">删除</el-button>
                <el-button size="small" @click="downloadDoc(scope.row)">下载</el-button>
                <el-button size="small" @click="showSummary(scope.row)">智能摘要</el-button>
                <el-button size="small" @click="pushToKnowledgeBase(scope.row)">推送到知识库</el-button>
                <el-button size="small" @click="previewDoc(scope.row)">预览</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap">
          <el-pagination
            v-if="total > pageSize"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            @current-change="handlePageChange"
            layout="prev, pager, next"
          />
        </div>
      </div>
    </el-card>
    <!-- 编辑弹窗、摘要弹窗保持不变 -->
    <el-dialog v-model="showEditor" :title="`✏️ 编辑文档: ${editingDocTitle}`" width="900px" :close-on-click-modal="false">
      <div class="editor-wrapper">
        <div class="editor-tips">
          <span>💡 支持富文本编辑，可以插入图片、表格、代码块等内容</span>
        </div>
        <SimpleEditor v-model="editorContent" />
      </div>
      <template #footer>
        <el-button @click="cancelEdit">取消</el-button>
        <el-button type="primary" @click="saveDoc" :loading="loading">💾 保存</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showSummaryDialog" title="🤖 智能摘要" width="600px">
      <div class="summary-content">{{ summaryContent }}</div>
      <template #footer>
        <el-button @click="showSummaryDialog = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-dialog 
      v-model="showPreviewDialog" 
      :title="`👁️ 预览文档: ${editingDocTitle}`" 
      width="1000px" 
      :fullscreen="isPreviewFullscreen"
      :close-on-click-modal="false"
    >
      <div class="preview-container">
        <div class="preview-toolbar">
          <el-button-group>
            <el-button 
              size="small" 
              :type="previewMode === 'formatted' ? 'primary' : ''"
              @click="previewMode = 'formatted'"
            >
              📄 格式化预览
            </el-button>
            <el-button 
              size="small" 
              :type="previewMode === 'raw' ? 'primary' : ''"
              @click="previewMode = 'raw'"
            >
              📝 源码预览
            </el-button>
          </el-button-group>
          <el-button 
            size="small" 
            @click="togglePreviewFullscreen"
            :icon="isPreviewFullscreen ? 'FullScreen' : 'FullScreen'"
          >
            {{ isPreviewFullscreen ? '退出全屏' : '全屏预览' }}
          </el-button>
        </div>
        
        <!-- 格式化预览 -->
        <div 
          v-if="previewMode === 'formatted'" 
          class="preview-content formatted-preview"
          v-html="formatPreviewContent(previewContent)"
        ></div>
        
        <!-- 源码预览 -->
        <div 
          v-if="previewMode === 'raw'" 
          class="preview-content raw-preview"
        >
          {{ previewContent }}
        </div>
      </div>
      
      <template #footer>
        <div class="preview-footer">
          <el-button @click="editDocFromPreview">✏️ 编辑</el-button>
          <el-button @click="downloadDocFromPreview">💾 下载</el-button>
          <el-button @click="showPreviewDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ArtExcelImport from '@/components/core/forms/ArtExcelImport.vue'
import SimpleEditor from '@/components/core/forms/SimpleEditor.vue'
import axios from 'axios'
import path from 'path'
import { Upload, Search } from '@element-plus/icons-vue'
import api from '@/utils/http'

const docList = ref<any[]>([])
const loading = ref(false)
const searchVal = ref('')
const showEditor = ref(false)
const editorContent = ref('')
const showSummaryDialog = ref(false)
const summaryContent = ref('')
const showPreviewDialog = ref(false)
const previewContent = ref('')
const editingDocTitle = ref('')
const isPreviewFullscreen = ref(false)
const previewMode = ref('formatted')
let editingDocId: number | null = null
let currentPreviewDoc: any = null

const token = localStorage.getItem('token')
const headers = token ? { Authorization: 'Bearer ' + token } : {}

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 使用相对路径而不是硬编码的完整URL
const uploadUrl = '/api/doc/upload'

// Excel导入成功
function handleImportSuccess(data: any[]) {
  ElMessage.success('导入成功，已解析 ' + data.length + ' 条文档')
}
function handleImportError(err: Error) {
  ElMessage.error('导入失败：' + err.message)
}

// 检索文档
async function searchDocs() {
  loading.value = true
  try {
    await fetchDocList()
  } finally {
    loading.value = false
  }
}

// 编辑文档
async function editDoc(row: any) {
  editingDocId = row.id || null
  editingDocTitle.value = row.filename || '未知文档'
  
  try {
    // 拉取单个文档内容
    const res = await axios.get(`/api/doc/${row.id}`, { headers })
    console.log('获取文档详情:', res.data)
    
    // 处理后端返回的数据结构
    if (res.data?.code === 0) {
      editorContent.value = res.data.content || ''
    } else {
      editorContent.value = res.data?.content || row.content || row.snippet || ''
    }
    
    showEditor.value = true
    ElMessage.success('文档加载成功，可以开始编辑')
  } catch (error) {
    console.error('获取文档详情失败:', error)
    ElMessage.error('获取文档内容失败')
  }
}

// 保存文档
async function saveDoc() {
  if (!editingDocId) {
    ElMessage.error('无效的文档ID')
    return
  }
  
  if (!editorContent.value.trim()) {
    ElMessage.warning('文档内容不能为空')
    return
  }
  
  try {
    loading.value = true
    const res = await axios.put(`/api/doc/${editingDocId}`, { 
      html_content: editorContent.value 
    }, { headers })
    
    console.log('保存文档响应:', res.data)
    
    if (res.data?.code === 0) {
      ElMessage.success('保存成功')
      showEditor.value = false
      await fetchDocList() // 刷新文档列表
      editingDocId = null
      editorContent.value = ''
      editingDocTitle.value = ''
    } else {
      ElMessage.error(res.data?.msg || '保存失败')
    }
  } catch (error) {
    console.error('保存文档失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 取消编辑
function cancelEdit() {
  showEditor.value = false
  editorContent.value = ''
  editingDocId = null
  editingDocTitle.value = ''
}

function handleUploadSuccess(response: any) {
  if (response && response.id) {
    ElMessage.success('上传成功')
    fetchDocList()
  } else {
    ElMessage.error('上传失败')
  }
}

function beforeUpload(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowExts = ['txt', 'docx', 'pptx', 'xls', 'xlsx', 'csv']
  if (!ext || !allowExts.includes(ext)) {
    ElMessage.error('仅支持 txt、docx、pptx、xls、xlsx、csv 文件')
    return false
  }
  return true
}

function fetchDocList() {
  axios.get('/api/doc/search', {
    params: { q: searchVal.value, page: page.value, size: pageSize.value },
    headers
  }).then(res => {
    if (res.data && Array.isArray(res.data.data)) {
      docList.value = res.data.data
      total.value = res.data.total || docList.value.length
    } else if (Array.isArray(res.data)) {
      docList.value = res.data
      total.value = docList.value.length
    } else {
      docList.value = []
      total.value = 0
    }
  })
}

// 删除文档
async function deleteDoc(row: any) {
  try {
    await axios.delete(`/api/doc/${row.id}`, { headers })
    ElMessage.success('删除成功')
    fetchDocList()
  } catch (e: any) {
    ElMessage.error('删除失败')
  }
}

// 下载文档
function downloadDoc(row: any) {
  window.open(`/api/doc/${row.id}/download?token=${token}`)
}

// 智能摘要
async function showSummary(row: any) {
  try {
    // 获取文档内容，优先 content 字段
    const content = row.content || row.html_content || row.snippet || ''
    if (!content || content.trim() === '' || content === '<p><br></p>') {
      ElMessage.error('文档内容为空，无法生成摘要')
      return
    }
    
    // 显示加载状态
    ElMessage.info('正在生成智能摘要，请稍候...')
    loading.value = true
    
    const res = await axios.post('/api/ai/summary', { content }, { headers })
    console.log('AI摘要接口返回', res.data)
    
    if (res.data.code === 0 && res.data.summary) {
      summaryContent.value = res.data.summary
      showSummaryDialog.value = true
      ElMessage.success('摘要生成成功')
    } else {
      ElMessage.error(res.data.msg || '摘要生成失败')
    }
  } catch (e: any) {
    console.error('摘要生成错误:', e)
    ElMessage.error('获取摘要失败: ' + (e.response?.data?.msg || e.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

function handlePageChange(val: number) {
  page.value = val
  fetchDocList()
}

function highlight(text: string) {
  if (!searchVal.value) return text
  const reg = new RegExp(searchVal.value, 'gi')
  return text.replace(reg, (match) => `<mark>${match}</mark>`)
}

async function pushToKnowledgeBase(row: any) {
  let loadingMessage: any = null
  try {
    loading.value = true
    loadingMessage = ElMessage({
      message: '正在推送到知识库...',
      type: 'info',
      duration: 0, // 不自动关闭
      showClose: false
    })
    
    // 首先尝试从后端获取完整内容
    let content = ''
    try {
      const res = await axios.get(`/api/doc/${row.id}`, { headers })
      if (res.data?.code === 0) {
        content = res.data.content || ''
      } else {
        content = row.content || row.html_content || row.snippet || ''
      }
    } catch (error) {
      console.warn('获取文档内容失败，使用本地数据:', error)
      content = row.content || row.html_content || row.snippet || ''
    }
    
    // 如果内容为空或只有空白标签，仍然允许推送但给出提示
    let hasEmptyContent = false
    if (!content || content.trim() === '' || content.trim() === '<p><br></p>') {
      hasEmptyContent = true
      content = `<h1>${row.filename}</h1><p>文档已上传，但内容为空。</p><p>上传时间：${row.upload_time}</p>`
    }
    
    await axios.post('/api/knowledge/import', {
      docId: row.id,
      title: row.filename,
      content,
      type: row.type || '文档'
    }, { headers })
    
    // 关闭加载消息
    if (loadingMessage) {
      loadingMessage.close()
      loadingMessage = null
    }
    
    // 显示成功消息
    if (hasEmptyContent) {
      ElMessage.success('已成功推送到知识库（内容为空，已生成基本信息）')
    } else {
      ElMessage.success('已成功推送到知识库')
    }
  } catch (e: any) {
    console.error('推送失败:', e)
    // 关闭加载消息
    if (loadingMessage) {
      loadingMessage.close()
      loadingMessage = null
    }
    ElMessage.error('推送失败: ' + (e.response?.data?.msg || e.message || '网络错误'))
  } finally {
    loading.value = false
    // 确保加载消息被关闭
    if (loadingMessage) {
      loadingMessage.close()
    }
  }
}

// 预览文档
async function previewDoc(row: any) {
  try {
    loading.value = true
    currentPreviewDoc = row
    
    // 首先尝试从后端获取完整内容
    const res = await axios.get(`/api/doc/${row.id}`, { headers })
    console.log('获取文档预览内容:', res.data)
    
    let content = ''
    if (res.data?.code === 0) {
      content = res.data.content || ''
    } else {
      content = res.data?.content || row.content || row.html_content || row.snippet || ''
    }
    
    if (!content.trim()) {
      ElMessage.warning('文档内容为空')
      return
    }
    
    previewContent.value = content
    editingDocTitle.value = row.filename || '未知文档'
    previewMode.value = 'formatted'
    isPreviewFullscreen.value = false
    showPreviewDialog.value = true
    ElMessage.success('文档加载完成')
    
  } catch (error) {
    console.error('获取预览内容失败:', error)
    // 失败时使用本地数据
    previewContent.value = row.content || row.html_content || row.snippet || '获取内容失败'
    editingDocTitle.value = row.filename || '未知文档'
    showPreviewDialog.value = true
  } finally {
    loading.value = false
  }
}

// 格式化预览内容
function formatPreviewContent(content: string) {
  if (!content) return '暂无内容'
  
  // 如果内容包含HTML标签，直接返回
  if (content.includes('<') && content.includes('>')) {
    return content
  }
  
  // 否则将纯文本转换为HTML格式
  return content
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

// 切换全屏预览
function togglePreviewFullscreen() {
  isPreviewFullscreen.value = !isPreviewFullscreen.value
}

// 从预览直接编辑
function editDocFromPreview() {
  if (currentPreviewDoc) {
    showPreviewDialog.value = false
    editDoc(currentPreviewDoc)
  }
}

// 从预览直接下载
function downloadDocFromPreview() {
  if (currentPreviewDoc) {
    downloadDoc(currentPreviewDoc)
  }
}

onMounted(() => {
  fetchDocList()
})
</script>

<style scoped>
.smart-doc-page {
  padding: 32px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.main-card {
  max-width: 1100px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: var(--el-box-shadow);
  padding: 32px 36px 24px 36px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
}

.header-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 8px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title::before {
  content: '📄';
  font-size: 24px;
}

.desc {
  color: var(--el-text-color-regular);
  font-size: 15px;
  margin-bottom: 0;
  line-height: 1.5;
  background: var(--el-fill-color-lighter);
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid var(--el-color-primary);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  border-left: 4px solid var(--el-color-primary);
  padding-left: 12px;
}

.section-title::before {
  content: '📋';
  font-size: 16px;
}

.doc-list-section {
  margin-top: 12px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 18px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

/* 预览容器样式 */
.preview-container {
  .preview-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 6px;
    border: 1px solid var(--el-border-color-lighter);
  }
}

.preview-content {
  max-height: 600px;
  overflow-y: auto !important;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
  background: var(--el-bg-color);
  padding: 20px;
  border-radius: 8px;
  color: var(--el-text-color-primary);
  line-height: 1.6;
  border: 1px solid var(--el-border-color);
  
      &.formatted-preview {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      
      /* 美化HTML内容样式 */
      h1, h2, h3, h4, h5, h6 {
      color: var(--el-color-primary);
      margin: 16px 0 8px 0;
      font-weight: 600;
    }
    
    p {
      margin: 8px 0;
      text-align: justify;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      
      th, td {
        border: 1px solid var(--el-border-color);
        padding: 8px 12px;
        text-align: left;
      }
      
      th {
        background: var(--el-fill-color-light);
        font-weight: 600;
      }
    }
    
    img {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
      margin: 8px 0;
    }
    
    code {
      background: var(--el-fill-color-light);
      padding: 2px 6px;
      border-radius: 3px;
      font-family: 'Monaco', 'Consolas', monospace;
      font-size: 13px;
    }
    
    pre {
      background: var(--el-fill-color-light);
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 12px 0;
      
      code {
        background: none;
        padding: 0;
      }
    }
    
    blockquote {
      border-left: 4px solid var(--el-color-primary);
      padding-left: 12px;
      margin: 12px 0;
      color: var(--el-text-color-regular);
      font-style: italic;
    }
    
    ul, ol {
      padding-left: 20px;
      margin: 8px 0;
    }
    
    li {
      margin: 4px 0;
    }
  }
  
  &.raw-preview {
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 13px;
    white-space: pre-wrap;
    background: var(--el-fill-color-lighter);
  }
}

.preview-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 全屏预览时的样式调整 */
.el-dialog--fullscreen {
  .preview-content {
    max-height: calc(100vh - 200px);
  }
}

.editor-wrapper {
  .editor-tips {
    background: var(--el-color-primary-light-9);
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 12px;
    border-left: 3px solid var(--el-color-primary);
    
    span {
      color: var(--el-color-primary);
      font-size: 13px;
      font-weight: 500;
    }
  }
}

/* 表格样式优化 */
.doc-list-section :deep(.el-table) {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.doc-list-section :deep(.el-table__header) {
  background: var(--el-fill-color-light);
}

.doc-list-section :deep(.el-table th) {
  background: var(--el-fill-color-light) !important;
  color: var(--el-text-color-primary) !important;
  font-weight: 600;
  border-bottom: 1px solid var(--el-border-color) !important;
}

.doc-list-section :deep(.el-table td) {
  border-bottom: 1px solid var(--el-border-color-lighter) !important;
  color: var(--el-text-color-regular);
}

.doc-list-section :deep(.el-table__row:hover) {
  background: var(--el-fill-color-lighter) !important;
}

.doc-list-section :deep(.el-table__row.current-row) {
  background: var(--el-color-primary-light-9) !important;
}

.doc-list-section :deep(.el-table--striped .el-table__row:nth-child(even)) {
  background: var(--el-fill-color-lighter);
}

/* 高亮标记样式 */
.doc-list-section :deep(mark) {
  background: var(--el-color-warning-light-8);
  color: var(--el-color-warning-dark-2);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

/* 按钮组优化 */
.doc-list-section :deep(.el-space) {
  flex-wrap: wrap;
  gap: 6px 8px !important;
}

.doc-list-section :deep(.el-button--small) {
  padding: 5px 8px;
  font-size: 12px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.doc-list-section :deep(.el-button--small:hover) {
  transform: translateY(-1px);
  box-shadow: var(--el-box-shadow-light);
}

/* 弹窗样式优化 */
:deep(.el-dialog) {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
}

:deep(.el-dialog__header) {
  background: var(--el-fill-color-lighter);
  padding: 20px 24px 16px;
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

:deep(.el-dialog__title) {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 16px;
}

:deep(.el-dialog__body) {
  padding: 24px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

:deep(.el-dialog__footer) {
  background: var(--el-fill-color-lighter);
  padding: 16px 24px 20px;
  border-radius: 0 0 12px 12px;
  border-top: 1px solid var(--el-border-color-light);
}

/* 摘要弹窗内容样式 */
.summary-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-lighter);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
}

/* 编辑器包装器样式 */
.editor-wrapper {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  overflow: hidden;
}

/* 预览容器样式 */
.preview-container {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  overflow: hidden;
  min-height: 500px;
}

.preview-toolbar {
  background: var(--el-fill-color-lighter);
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-content {
  padding: 24px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  line-height: 1.6;
  max-height: 600px;
  overflow-y: auto;
  font-size: 14px;
}

/* 格式化预览样式 */
.formatted-preview {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}

.formatted-preview h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--el-color-primary);
}

.formatted-preview h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 24px 0 16px 0;
  padding-left: 8px;
  border-left: 4px solid var(--el-color-primary);
}

.formatted-preview h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 20px 0 12px 0;
}

.formatted-preview p {
  margin: 12px 0;
  color: var(--el-text-color-primary);
  line-height: 1.8;
}

.formatted-preview ul, .formatted-preview ol {
  margin: 12px 0 12px 20px;
  padding-left: 20px;
}

.formatted-preview li {
  margin: 8px 0;
  color: var(--el-text-color-primary);
  line-height: 1.6;
}

.formatted-preview table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  background: var(--el-bg-color);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.formatted-preview th, .formatted-preview td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--el-border-color);
}

.formatted-preview th {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.formatted-preview tr:hover {
  background: var(--el-fill-color-lighter);
}

.formatted-preview blockquote {
  margin: 16px 0;
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-left: 4px solid var(--el-color-primary);
  border-radius: 0 6px 6px 0;
  color: var(--el-text-color-regular);
  font-style: italic;
}

.formatted-preview code {
  background: var(--el-fill-color-lighter);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: var(--el-color-primary);
}

.formatted-preview pre {
  background: var(--el-fill-color-lighter);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
  border: 1px solid var(--el-border-color);
}

.formatted-preview pre code {
  background: none;
  padding: 0;
  border-radius: 0;
  color: var(--el-text-color-primary);
}

.formatted-preview strong {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.formatted-preview em {
  font-style: italic;
  color: var(--el-text-color-regular);
}

/* 源码预览样式 */
.raw-preview {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: var(--el-fill-color-lighter);
  padding: 20px;
  border-radius: 6px;
  color: var(--el-text-color-primary);
  min-height: 400px;
}

/* 预览底部按钮样式 */
.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.doc-list-section :deep(.el-dialog .preview-content) {
  background: var(--el-fill-color-lighter);
}

/* 滚动条样式优化 */
.preview-content::-webkit-scrollbar {
  width: 8px;
}

.preview-content::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

/* 深色模式优化 */
.dark .main-card {
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.dark .doc-list-section :deep(.el-table) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.dark .doc-list-section :deep(mark) {
  background: var(--el-color-warning-dark-2);
  color: var(--el-color-warning-light-8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .smart-doc-page {
    padding: 16px;
  }
  
  .main-card {
    padding: 20px 16px;
    max-width: 100%;
  }
  
  .page-title {
    font-size: 22px;
  }
  
  .top-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    padding: 16px;
  }
  
  .top-actions .el-input {
    width: 100% !important;
  }
  
  .doc-list-section :deep(.el-table) {
    font-size: 12px;
  }
  
  .doc-list-section :deep(.el-space) {
    flex-direction: column;
    align-items: stretch;
  }
  
  .doc-list-section :deep(.el-button--small) {
    width: 100%;
    margin: 2px 0;
  }
  
  .preview-content {
    max-height: 400px;
    font-size: 14px;
  }
}

/* 动画效果 */
.main-card {
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.doc-list-section :deep(.el-table__row) {
  transition: all 0.2s ease;
}

.top-actions > * {
  transition: all 0.2s ease;
}

.top-actions > *:hover {
  transform: translateY(-1px);
}
</style> 