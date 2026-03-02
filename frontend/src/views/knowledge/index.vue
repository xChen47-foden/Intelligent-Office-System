<template>
  <div class="knowledge-page">
    <el-card class="main-card">
      <div class="header-section">
        <div class="title-area">
          <h2 class="page-title">📚 知识库管理</h2>
          <p class="page-desc">智能知识库，让企业知识触手可及</p>
        </div>
        <div class="stats-area">
          <el-statistic title="总文档数" :value="totalDocs" />
          <el-statistic title="知识库数" :value="knowledgeList.length" />
          <el-statistic title="今日新增" :value="todayAdded" />
          <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
            <el-button 
              type="warning" 
              size="small" 
              @click="fixDuplicateIds"
              :loading="fixingIds"
            >
              <el-icon><Refresh /></el-icon>
              修复重复ID
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              @click="restoreDeletedDocs"
              :loading="restoring"
            >
              <el-icon><Refresh /></el-icon>
              恢复被覆盖文档
            </el-button>
          </div>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 智能问答区域 -->
      <el-card class="qa-section" shadow="never">
        <template #header>
          <div class="section-header">
            <h3>🤖 智能问答</h3>
            <span class="section-desc">基于知识库的智能问答系统</span>
          </div>
        </template>
        <div class="qa-container">
          <el-input
            v-model="qaInput"
            placeholder="请输入您的问题，如：'公司年假规定是什么？'"
            class="qa-input"
            @keyup.enter="handleQA"
            clearable
          >
            <template #prepend>
              <el-icon><ChatDotRound /></el-icon>
            </template>
            <template #append>
              <el-button 
                type="primary" 
                @click="handleQA" 
                :loading="qaLoading"
                :disabled="!qaInput.trim()"
              >
                {{ qaLoading ? '思考中...' : '提问' }}
              </el-button>
            </template>
          </el-input>
          
          <!-- 对话历史记录 -->
          <div v-if="qaHistory.length > 0" class="qa-history">
            <div class="history-header">
              <span>💬 对话记录</span>
              <el-button size="small" text @click="clearHistory">清空历史</el-button>
            </div>
            <div class="history-list">
              <div 
                v-for="(item, index) in qaHistory.slice(-3)" 
                :key="index" 
                class="history-item"
              >
                <div class="user-question">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>{{ item.question }}</span>
                  <small>{{ item.timestamp }}</small>
                </div>
                <div v-if="item.answer" class="assistant-answer">
                  <el-icon color="#67C23A"><SuccessFilled /></el-icon>
                  <div class="answer-text" v-html="item.answer"></div>
                </div>
                <div v-else-if="index === qaHistory.length - 1 && isTyping" class="typing-indicator">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>AI正在思考中...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 当前回答 -->
          <div v-if="qaAnswer || isTyping" class="qa-answer">
            <div class="answer-header">
              <el-icon color="#67C23A"><SuccessFilled /></el-icon>
              <span>智能助手回答：</span>
              <el-tag size="small" type="success" v-if="relevantDocsCount > 0">
                找到 {{ relevantDocsCount }} 个相关文档
              </el-tag>
            </div>
            
            <div v-if="isTyping" class="typing-indicator">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在生成回答...</span>
            </div>
            
            <div v-else class="answer-content" v-html="qaAnswer"></div>
            
            <!-- 相关文档 -->
            <div v-if="relatedDocs.length > 0" class="related-docs">
              <div class="docs-header">📄 相关文档：</div>
              <div class="docs-list">
                <el-tag
                  v-for="doc in relatedDocs"
                  :key="doc.id"
                  size="small"
                  type="info"
                  effect="plain"
                  class="doc-tag"
                  @click="viewRelatedDoc(doc)"
                >
                  {{ doc.title }}
                </el-tag>
              </div>
            </div>
            
            <div class="answer-actions" v-if="!isTyping">
              <el-button size="small" @click="copyAnswer">
                <el-icon><DocumentCopy /></el-icon>
                复制答案
              </el-button>
              <el-button size="small" @click="regenerateAnswer">
                <el-icon><Refresh /></el-icon>
                重新生成
              </el-button>
              <el-button size="small" @click="continueConversation">
                <el-icon><ChatDotRound /></el-icon>
                继续对话
              </el-button>
              <el-button size="small" @click="clearCurrentAnswer">
                <el-icon><Delete /></el-icon>
                清除
              </el-button>
            </div>
          </div>
          
          <!-- 问题建议区域 -->
          <div v-if="showSuggestions" class="qa-suggestions">
            <div class="suggestions-header">
              <el-icon><QuestionFilled /></el-icon>
              <span>常见问题建议：</span>
              <el-button size="small" text @click="showSuggestions = false">收起</el-button>
            </div>
            
            <div class="suggestions-categories">
              <div 
                v-for="category in questionCategories" 
                :key="category.name"
                class="category-section"
              >
                <div class="category-header">
                  <span class="category-icon">{{ category.icon }}</span>
                  <span class="category-name">{{ category.name }}</span>
                </div>
                <div class="category-questions">
                  <el-tag 
                    v-for="question in category.questions" 
                    :key="question"
                    class="suggestion-tag"
                    @click="selectSuggestion(question)"
                    type="info"
                    effect="plain"
                    size="small"
                  >
                    {{ question }}
                  </el-tag>
                </div>
              </div>
            </div>
            
            <!-- 快捷操作 -->
            <div class="quick-actions">
              <el-button size="small" @click="showRandomQuestion" type="primary" plain>
                🎲 随机问题
              </el-button>
              <el-button size="small" @click="showHotQuestions" type="success" plain>
                🔥 热门问题
              </el-button>
              <el-button size="small" @click="showRecentQuestions" type="warning" plain>
                🕒 最近问题
              </el-button>
            </div>
          </div>
          
          <!-- 快速入口按钮 -->
          <div v-else class="quick-entry">
            <el-button size="small" @click="showQuestionSuggestions" type="primary" plain>
              <el-icon><QuestionFilled /></el-icon>
              问题建议
            </el-button>
            <el-button size="small" @click="showSuggestions = true" type="info" plain>
              💡 智能提示
            </el-button>
          </div>
        </div>
      </el-card>
      
      <!-- 搜索和过滤区域 -->
      <el-card class="filter-section" shadow="never">
        <div class="filter-container">
          <el-input
            v-model="knowledgeSearch"
            placeholder="搜索知识库文档..."
            class="search-input"
            clearable
            @keyup.enter="loadDocs"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select 
            v-model="selectedKnowledge" 
            placeholder="选择知识库"
            class="kb-select"
            clearable
            @change="loadDocs"
          >
            <el-option v-for="item in knowledgeList" :key="item.value" :label="item.label" :value="item.value">
              <span class="option-icon">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </el-option>
          </el-select>
          
          <el-select 
            v-model="selectedType" 
            placeholder="文档类型"
            class="type-select"
            clearable
            @change="loadDocs"
          >
            <el-option label="全部类型" value="" />
            <el-option label="Word文档" value="docx" />
            <el-option label="PDF文档" value="pdf" />
            <el-option label="PPT演示" value="pptx" />
            <el-option label="Markdown" value="md" />
            <el-option label="文本文件" value="txt" />
          </el-select>
          
          <el-upload
            v-if="canUpload"
            :action="''"
            :http-request="handleDocUpload"
            :show-file-list="false"
            :before-upload="beforeUpload"
            class="upload-btn"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              上传文档
            </el-button>
          </el-upload>
          
          <el-button @click="loadDocs" :loading="loading">
            <el-icon><Refresh /></el-icon>
            {{ loading ? '加载中' : '搜索' }}
          </el-button>
        </div>
      </el-card>
      
      <!-- 文档列表区域 -->
      <el-card class="docs-section" shadow="never">
        <template #header>
          <div class="section-header">
            <h3>📋 文档列表</h3>
            <div class="header-actions">
              <el-button-group v-if="selectedDocs.length" class="batch-actions">
                <el-button v-if="canDelete" type="danger" size="small" @click="batchDelete">
                  <el-icon><Delete /></el-icon>
                  批量删除 ({{ selectedDocs.length }})
                </el-button>
                <el-button size="small" @click="batchDownload">
                  <el-icon><Download /></el-icon>
                  批量下载
                </el-button>
              </el-button-group>
              <el-button @click="exportDocs" size="small">
                <el-icon><DocumentCopy /></el-icon>
                导出列表
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table :data="paginatedDocs" style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="40" />
            <el-table-column prop="docId" label="ID" width="60">
              <template #default="{ row }">
                {{ row.docId || row.id }}
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" width="200">
              <template #default="{ row }">
                {{ row.title || row.filename }}
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <!-- 从文件名提取扩展名 -->
                <template v-if="row.filename">
                  <el-icon v-if="(row.filename || '').toLowerCase().endsWith('.docx') || (row.filename || '').toLowerCase().endsWith('.doc')"><Document /></el-icon>
                  <el-icon v-else-if="(row.filename || '').toLowerCase().endsWith('.pptx') || (row.filename || '').toLowerCase().endsWith('.ppt')"><Tickets /></el-icon>
                  <el-icon v-else-if="(row.filename || '').toLowerCase().endsWith('.pdf')"><Folder /></el-icon>
                  <el-icon v-else-if="(row.filename || '').toLowerCase().endsWith('.txt')"><DocumentCopy /></el-icon>
                  <el-icon v-else-if="(row.filename || '').toLowerCase().endsWith('.xlsx') || (row.filename || '').toLowerCase().endsWith('.xls')"><Document /></el-icon>
                <el-icon v-else><Document /></el-icon>
                  <span style="margin-left:4px;">
                    {{ getFileTypeLabel(row.filename) }}
                  </span>
                </template>
                <!-- 如果没有文件名，使用type字段 -->
                <template v-else>
                  <el-icon><Document /></el-icon>
                  <span style="margin-left:4px;">{{ row.type || '未知' }}</span>
                </template>
              </template>
            </el-table-column>
            <el-table-column prop="knowledge_base" label="知识库" width="180">
              <template #default="{ row }">
                <el-select 
                  v-model="row.knowledge_base" 
                  placeholder="选择知识库"
                  size="small"
                  clearable
                  @change="updateDocKnowledgeBase(row)"
                  style="width: 100%;"
                >
                  <el-option 
                    v-for="item in knowledgeList" 
                    :key="item.value" 
                    :label="item.label" 
                    :value="item.value"
                  >
                    <span class="option-icon">{{ item.icon }}</span>
                    <span>{{ item.label }}</span>
                  </el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" min-width="200">
              <template #default="{ row }">
                <span @click="showContent(row.content)" style="cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:inline-block;max-width:200px;">
                  {{ row.content && row.content.length > 100 ? row.content.slice(0, 100) + '...' : row.content }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="300">
              <template #default="scope">
                <div style="display: flex; flex-wrap: nowrap; gap: 4px;">
                  <el-button size="small" @click="previewDoc(scope.row)">预览</el-button>
                  <el-button size="small" @click="() => handleSummary(scope.row)">智能摘要</el-button>
                  <el-button 
                    v-if="canEdit" 
                    type="text" 
                    size="small" 
                    @click="editDoc(scope.row)"
                    :disabled="(scope.row.filename || '').toLowerCase().endsWith('.xlsx') || (scope.row.filename || '').toLowerCase().endsWith('.xls') || (scope.row.filename || '').toLowerCase().endsWith('.csv')"
                  >
                    编辑
                  </el-button>
                  <el-button v-if="canDelete" type="text" size="small" style="color: var(--el-color-danger);" @click="confirmDeleteDoc(scope.row)">删除</el-button>
                  <el-button size="small" @click="downloadDoc(scope.row)">下载</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        
        <!-- 分页控件 -->
        <div class="pagination-container" v-if="totalDocuments > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalDocuments"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            class="pagination"
          />
        </div>
        
        <el-empty v-if="!paginatedDocs.length && !loading" description="暂无文档" />
      </el-card>
    </el-card>

    <!-- 文档预览对话框 -->
    <el-dialog 
      v-model="docPreviewVisible" 
      :title="`👁️ 预览文档: ${docPreview.title}`" 
      width="90%"
      :close-on-click-modal="false"
      class="preview-dialog"
      style="max-width: 1200px"
    >
      <div v-if="previewLoading" class="preview-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在加载文档内容...</span>
      </div>
      
      <div v-else class="preview-container">
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
            <el-button 
              size="small" 
              :type="previewMode === 'edit' ? 'primary' : ''"
              @click="handleEditMode"
              v-if="canEdit"
              :disabled="isExcelFile"
            >
              ✏️ 编辑模式
            </el-button>
          </el-button-group>

        </div>
        
        <!-- 格式化预览 -->
        <div 
          v-if="previewMode === 'formatted'" 
          class="preview-content formatted-preview"
          v-html="formatPreviewContent(docPreview.content)"
        ></div>
        
        <!-- 源码预览 -->
        <div 
          v-if="previewMode === 'raw'" 
          class="preview-content raw-preview"
        >
          {{ docPreview.content }}
        </div>
        
        <!-- 编辑模式 -->
        <div 
          v-if="previewMode === 'edit'" 
          class="preview-content edit-preview"
        >
          <el-alert
            v-if="isExcelFile"
            title="提示"
            type="warning"
            :closable="false"
            style="margin-bottom: 16px;"
          >
            <template #default>
              <div>
                <p>Excel文件（.xlsx/.xls/.csv）不支持在线编辑。</p>
                <p>请下载文件后使用Excel软件进行编辑，然后重新上传。</p>
              </div>
            </template>
          </el-alert>
          
          <!-- 知识库选择 -->
          <div style="margin-bottom: 16px;">
            <el-form-item label="知识库分类">
              <el-select 
                v-model="editKnowledgeBase" 
                placeholder="选择知识库"
                clearable
                style="width: 100%;"
              >
                <el-option 
                  v-for="item in knowledgeList" 
                  :key="item.value" 
                  :label="item.label" 
                  :value="item.value"
                >
                  <span class="option-icon">{{ item.icon }}</span>
                  <span>{{ item.label }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </div>
          
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="20"
            placeholder="请输入文档内容..."
            style="width: 100%;"
            :disabled="isExcelFile"
          />
        </div>
      </div>
      
      <template #footer>
        <div class="preview-footer">
          <el-button 
            v-if="previewMode === 'edit'" 
            type="primary" 
            @click="saveEdit"
            :loading="saveLoading"
          >
            💾 保存编辑
          </el-button>
          <el-button @click="handleSummary(docPreview)">🤖 智能摘要</el-button>
          <el-button @click="downloadDoc(docPreview)">💾 下载</el-button>
          <el-button @click="docPreviewVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="340px">
      <div>确定要删除该文档吗？</div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="deleteDoc">删除</el-button>
      </template>
    </el-dialog>

    <!-- 内容详情对话框 -->
    <el-dialog v-model="contentDialogVisible" title="文档内容" width="60%">
      <div style="white-space: pre-wrap;">{{ currentContent }}</div>
    </el-dialog>

    <!-- 智能摘要对话框 -->
    <el-dialog 
      v-model="summaryDialogVisible" 
      title="🤖 智能摘要" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="summaryLoading" class="summary-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在生成智能摘要，请稍候...</span>
        <div class="loading-progress">
          <el-progress 
            :percentage="summaryProgress" 
            :show-text="false"
            status="success"
            :stroke-width="4"
          />
        </div>
      </div>
      
      <div v-else-if="summaryContent" class="summary-content">
        <div class="summary-header">
          <el-icon color="#67C23A"><SuccessFilled /></el-icon>
          <span>摘要生成完成</span>
          <el-tag size="small" type="success">AI智能分析</el-tag>
        </div>
        
        <div class="summary-body" v-html="summaryContent"></div>
        
        <div class="summary-actions">
          <el-button size="small" @click="copySummary">
            <el-icon><DocumentCopy /></el-icon>
            复制摘要
          </el-button>
          <el-button size="small" @click="regenerateSummary">
            <el-icon><Refresh /></el-icon>
            重新生成
          </el-button>
          <el-button size="small" @click="exportSummary">
            <el-icon><Download /></el-icon>
            导出摘要
          </el-button>
        </div>
      </div>
      
      <div v-else class="summary-empty">
        <el-empty description="暂无摘要内容" />
      </div>
      
      <template #footer>
        <el-button @click="summaryDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Upload, Refresh, ChatDotRound, SuccessFilled, 
  Delete, Download, DocumentCopy, Document, Tickets, Folder, QuestionFilled, Loading
} from '@element-plus/icons-vue'
import { fetchKnowledgeList, searchKnowledgeDocs, uploadKnowledgeDoc, fetchDocDetail, editKnowledgeDoc } from '@/api/knowledge'
import axios from 'axios'
import api from '@/utils/http'

// 基础数据
const knowledgeSearch = ref('')
const knowledgeList = [
  { label: '公司规章制度', value: 'rule', icon: '📋' },
  { label: '项目文档', value: 'project', icon: '📁' },
  { label: '合同知识库', value: 'contract', icon: '📄' },
  { label: '技术文档', value: 'tech', icon: '⚙️' },
  { label: '培训资料', value: 'training', icon: '🎓' },
  { label: '其他', value: 'other', icon: '📦' }
]
const selectedKnowledge = ref('')
const selectedType = ref('')
const knowledgeDocs = ref<any[]>([])
const loading = ref(false)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const totalDocuments = ref(0)

// 统计数据
const totalDocs = ref(0)
const todayAdded = ref(3)

// 智能问答增强
const qaInput = ref('')
const qaAnswer = ref('')
const qaLoading = ref(false)
const relevantDocsCount = ref(0)
const showSuggestions = ref(false)
const qaHistory = ref<Array<{question: string, answer: string, timestamp: string, docs?: any[]}>>([])
const relatedDocs = ref<any[]>([])
const currentConversationId = ref('')
const isTyping = ref(false)

// 问题建议分类
const questionCategories = ref([
  {
    name: '规章制度',
    icon: '📋',
    questions: [
      '公司的年假规定是什么？',
      '员工培训制度有哪些？',
      '如何申请出差？',
      '信息安全管理制度'
    ]
  },
  {
    name: '技术文档',
    icon: '⚙️',
    questions: [
      'Vue3开发规范有哪些？',
      'API接口设计规范',
      '项目开发流程',
      '代码审查标准'
    ]
  },
  {
    name: '办公服务',
    icon: '🏢',
    questions: [
      '会议室如何预约？',
      '如何申请设备？',
      '财务报销流程',
      '人事联系方式'
    ]
  }
])

// 所有问题建议（平铺）
const questionSuggestions = computed(() => {
  return questionCategories.value.flatMap(cat => cat.questions)
})

const handleQA = async () => {
  if (!qaInput.value.trim()) return
  
  const question = qaInput.value.trim()
  const timestamp = new Date().toLocaleString()
  
  // 添加到历史记录（问题）
  qaHistory.value.push({
    question,
    answer: '',
    timestamp,
    docs: []
  })
  
  qaLoading.value = true
  isTyping.value = true
  
  // 清空之前的答案，准备显示新答案
  qaAnswer.value = ''
  relatedDocs.value = []
  relevantDocsCount.value = 0
  
  try {
    // 模拟打字效果
    setTimeout(() => {
      isTyping.value = false
    }, 1000)
    
    // 调用知识库问答API
    const res = await axios.post('http://localhost:3007/api/knowledge/qa', { 
      question,
      knowledge_base: selectedKnowledge.value,
      conversation_id: currentConversationId.value,
      history: qaHistory.value.slice(-5) // 只传递最近5次对话历史
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (res.data.code === 0) {
      const answer = res.data.answer || '抱歉，暂时无法回答您的问题。'
      
      // 打字机效果显示答案
      await typeWriterEffect(answer)
      
      // 更新历史记录
      if (qaHistory.value.length > 0) {
        qaHistory.value[qaHistory.value.length - 1].answer = answer
        qaHistory.value[qaHistory.value.length - 1].docs = res.data.docs || []
      }
      
      // 设置相关文档信息
      if (res.data.relevant_count > 0) {
        relevantDocsCount.value = res.data.relevant_count
        relatedDocs.value = res.data.docs || []
      }
      
      // 设置会话ID
      if (res.data.conversation_id) {
        currentConversationId.value = res.data.conversation_id
      }
      
    } else {
      const errorMsg = res.data.msg || '查询失败，请稍后重试。'
      await typeWriterEffect(errorMsg)
      
      if (qaHistory.value.length > 0) {
        qaHistory.value[qaHistory.value.length - 1].answer = errorMsg
      }
    }
  } catch (error: any) {
    console.error('知识库问答API调用失败:', error)
    // 如果API失败，提供智能降级回答
    const fallbackAnswer = await generateFallbackAnswer(question)
    await typeWriterEffect(fallbackAnswer)
    
    if (qaHistory.value.length > 0) {
      qaHistory.value[qaHistory.value.length - 1].answer = fallbackAnswer
    }
  } finally {
    qaLoading.value = false
    isTyping.value = false
    // 清空输入框
    qaInput.value = ''
    // 隐藏建议
    showSuggestions.value = false
  }
}

// 打字机效果
const typeWriterEffect = async (text: string) => {
  qaAnswer.value = ''
  const speed = 30 // 打字速度(毫秒)
  
  for (let i = 0; i < text.length; i++) {
    qaAnswer.value += text.charAt(i)
    await new Promise(resolve => setTimeout(resolve, speed))
  }
}

// 降级回答生成
const generateFallbackAnswer = async (question: string) => {
  // 尝试在本地文档中搜索
  try {
    const searchResult = await searchKnowledgeDocs(question)
    const docs = Array.isArray(searchResult.data) ? searchResult.data : (searchResult.data.data || [])
    
    if (docs.length > 0) {
      let answer = `基于本地搜索，为您找到以下相关信息：<br/><br/>`
             docs.slice(0, 2).forEach((doc: any, index: number) => {
        const title = doc.title || doc.filename || '未知文档'
        const preview = (doc.content || '').slice(0, 150)
        answer += `<strong>${index + 1}. ${title}</strong><br/>${preview}${doc.content && doc.content.length > 150 ? '...' : ''}<br/><br/>`
      })
      answer += `<small>💡 提示：找到 ${docs.length} 个相关文档，您可以在文档列表中查看完整内容。</small>`
      return answer
    }
  } catch (e) {
    console.error('本地搜索也失败:', e)
  }
  
  // 最终降级回答
  return `针对"${question}"的问题，建议您：<br/>
  1. 🔍 尝试使用更具体的关键词在文档列表中搜索<br/>
  2. 📂 检查相关文档是否已上传到知识库<br/>
  3. 👥 联系管理员获取更详细的信息<br/>
  <small>提示：您可以尝试使用更简洁的关键词进行搜索。</small>`
}

// 显示问题建议
const showQuestionSuggestions = () => {
  showSuggestions.value = !showSuggestions.value
}

// 选择建议问题
const selectSuggestion = (suggestion: string) => {
  qaInput.value = suggestion
  showSuggestions.value = false
  handleQA()
}

// 智能问答增强功能
const clearHistory = () => {
  qaHistory.value = []
  qaAnswer.value = ''
  relevantDocsCount.value = 0
  relatedDocs.value = []
  currentConversationId.value = ''
  ElMessage.success('对话历史已清空')
}

const clearCurrentAnswer = () => {
  qaAnswer.value = ''
  relevantDocsCount.value = 0
  relatedDocs.value = []
}

const regenerateAnswer = async () => {
  if (qaHistory.value.length > 0) {
    const lastQuestion = qaHistory.value[qaHistory.value.length - 1].question
    qaInput.value = lastQuestion
    // 移除最后一个历史记录，重新生成
    qaHistory.value.pop()
    await handleQA()
  }
}

const continueConversation = () => {
  qaInput.value = ''
  showSuggestions.value = true
  ElMessage.info('请输入您的问题继续对话')
}

const viewRelatedDoc = (doc: any) => {
  // 在文档列表中找到对应文档并预览
  const foundDoc = knowledgeDocs.value.find(d => d.id === doc.id || d.docId === doc.id)
  if (foundDoc) {
    previewDoc(foundDoc)
  } else {
    ElMessage.warning('文档未找到，可能已被删除')
  }
}

const showRandomQuestion = () => {
  const allQuestions = questionSuggestions.value
  const randomIndex = Math.floor(Math.random() * allQuestions.length)
  selectSuggestion(allQuestions[randomIndex])
}

const showHotQuestions = () => {
  // 模拟热门问题
  const hotQuestions = [
    '公司的年假规定是什么？',
    '如何申请出差？',
    '会议室如何预约？'
  ]
  ElMessage.info('为您推荐热门问题')
  // 可以在这里显示热门问题列表
}

const showRecentQuestions = () => {
  if (qaHistory.value.length > 0) {
    const recentQuestions = qaHistory.value.slice(-5).map(item => item.question)
    ElMessage.info(`最近问题：${recentQuestions.join('、')}`)
  } else {
    ElMessage.info('暂无最近问题记录')
  }
}

// 复制答案
const copyAnswer = async () => {
  try {
    await navigator.clipboard.writeText(qaAnswer.value.replace(/<[^>]*>/g, ''))
    ElMessage.success('答案已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 文档上传前检查
const beforeUpload = (file: File) => {
  const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                       'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'text/plain']
  const isAllowed = allowedTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowed) {
    ElMessage.error('只支持 PDF、Word、PowerPoint 和文本文件！')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }
  return true
}

// 导出文档列表
const exportDocs = () => {
  const csvContent = [
    ['ID', '标题', '类型', '内容预览'].join(','),
    ...filteredDocs.value.map(doc => [
      doc.docId || doc.id,
      `"${doc.title || doc.filename}"`,
      doc.type || '',
      `"${(doc.content || '').slice(0, 50)}"`
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `知识库文档列表_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  ElMessage.success('文档列表已导出')
}

// 文档加载
const loadDocs = async () => {
  loading.value = true
  try {
    if (knowledgeSearch.value.trim()) {
      const res = await searchKnowledgeDocs(knowledgeSearch.value.trim())
      knowledgeDocs.value = Array.isArray(res.data) ? res.data : (res.data.data || [])
      // 按ID排序（升序）
      knowledgeDocs.value.sort((a, b) => {
        const idA = parseInt(a.id || a.docId || 0) || 0
        const idB = parseInt(b.id || b.docId || 0) || 0
        return idA - idB
      })
    } else {
      const res = await fetchKnowledgeList()
      knowledgeDocs.value = Array.isArray(res.data) ? res.data : (res.data.data || [])
    }
    
    // 按ID排序（升序）
    knowledgeDocs.value.sort((a, b) => {
      const idA = parseInt(a.id || a.docId || 0) || 0
      const idB = parseInt(b.id || b.docId || 0) || 0
      return idA - idB
    })
    
    // 更新总文档数
    totalDocs.value = knowledgeDocs.value.length
  } catch (error) {
    ElMessage.error('获取文档列表失败')
    knowledgeDocs.value = []
  } finally {
    loading.value = false
  }
}

watch([knowledgeSearch, selectedKnowledge, selectedType], loadDocs)
onMounted(loadDocs)

// 文档过滤
const filteredDocs = computed(() => {
  let filtered = [...knowledgeDocs.value]
  
  // 按搜索关键词过滤
  const kw = knowledgeSearch.value.trim().toLowerCase()
  if (kw) {
    filtered = filtered.filter(doc => 
      (doc.title && doc.title.toLowerCase().includes(kw)) ||
      (doc.content && doc.content.toLowerCase().includes(kw)) ||
      (doc.filename && doc.filename.toLowerCase().includes(kw)) ||
      (doc.type && doc.type.toLowerCase().includes(kw))
    )
  }
  
  // 按知识库过滤
  if (selectedKnowledge.value) {
    filtered = filtered.filter(doc => doc.knowledge_base === selectedKnowledge.value)
  }
  
  // 按文档类型过滤
  if (selectedType.value) {
    filtered = filtered.filter(doc => {
      // 优先从文件名提取扩展名
      let docType = ''
      if (doc.filename) {
        const ext = doc.filename.split('.').pop()?.toLowerCase() || ''
        // 统一处理文件类型
        if (ext === 'docx' || ext === 'doc') {
          docType = 'docx'
        } else if (ext === 'pptx' || ext === 'ppt') {
          docType = 'pptx'
        } else {
          docType = ext
        }
      } else if (doc.type) {
        // 如果没有文件名，使用type字段，但也要标准化
        const typeLower = doc.type.toLowerCase()
        if (typeLower === 'docx' || typeLower === 'doc' || typeLower === 'word文档' || typeLower === '文档') {
          docType = 'docx'
        } else if (typeLower === 'pptx' || typeLower === 'ppt' || typeLower === 'ppt演示') {
          docType = 'pptx'
        } else {
          docType = typeLower
        }
      }
      return docType === selectedType.value
    })
  }
  
  // 按ID排序（升序）
  filtered.sort((a, b) => {
    const idA = parseInt(a.id || a.docId || 0) || 0
    const idB = parseInt(b.id || b.docId || 0) || 0
    return idA - idB
  })
  
  // 更新总文档数
  totalDocuments.value = filtered.length
  
  return filtered
})

// 分页文档
const paginatedDocs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDocs.value.slice(start, end)
})

// 分页事件处理
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 文档操作
const docPreviewVisible = ref(false)
const docPreview = ref({ id: 0, title: '', content: '', knowledge_base: '' })
const editing = ref(false)
const editContent = ref('')
const editKnowledgeBase = ref('')

const previewDoc = async (doc: any) => {
  try {
    previewLoading.value = true
    docPreviewVisible.value = true
    
    // 首先尝试从知识库API获取详情
    try {
      const res = await axios.get(`/api/knowledge/detail?id=${doc.docId || doc.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (res.data.code === 0 && res.data.data) {
        docPreview.value = {
          id: res.data.data.docId || res.data.data.id,
          title: res.data.data.title || res.data.data.filename,
          content: res.data.data.content || '',
          knowledge_base: res.data.data.knowledge_base || ''
        }
      } else {
        throw new Error('API返回错误')
      }
    } catch (apiError) {
      // 如果API失败，使用当前行数据
      console.warn('API获取详情失败，使用当前数据:', apiError)
      docPreview.value = {
        id: doc.docId || doc.id,
        title: doc.title || doc.filename,
        content: doc.content || '',
        knowledge_base: doc.knowledge_base || ''
      }
    }
    
    editContent.value = docPreview.value.content
    editKnowledgeBase.value = docPreview.value.knowledge_base || ''
    previewMode.value = 'formatted'
    
    ElMessage.success('文档加载成功')
  } catch (error) {
    ElMessage.error('获取文档详情失败')
  } finally {
    previewLoading.value = false
  }
}

const saveEdit = async () => {
  try {
    saveLoading.value = true
    
    if (!editContent.value.trim()) {
      ElMessage.warning('文档内容不能为空')
      return
    }
    
    // 调用知识库编辑API
    const res = await axios.post('http://localhost:3007/api/knowledge/edit', {
      id: docPreview.value.id,
      content: editContent.value,
      knowledge_base: editKnowledgeBase.value || ''  // 传递知识库分类
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (res.data.code === 0) {
      ElMessage.success('保存成功')
      // 更新预览内容
      docPreview.value.content = editContent.value
      docPreview.value.knowledge_base = editKnowledgeBase.value || ''
      // 切换回格式化预览模式
      previewMode.value = 'formatted'
      // 刷新文档列表
      loadDocs()
    } else {
      throw new Error(res.data.msg || '保存失败')
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.response?.data?.msg || error.message || '网络错误'))
  } finally {
    saveLoading.value = false
  }
}

const handleDocUpload = async (option: any) => {
  try {
    const formData = new FormData()
    formData.append('file', option.file)
    // 如果选择了知识库，传递知识库参数
    if (selectedKnowledge.value) {
      formData.append('knowledge_base', selectedKnowledge.value)
    }
    await uploadKnowledgeDoc(formData)
    ElMessage.success('上传成功')
    loadDocs()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

// 批量操作
const selectedDocs = ref<any[]>([])
const handleSelectionChange = (rows: any[]) => {
  selectedDocs.value = rows
}

const batchDelete = async () => {
  if (selectedDocs.value.length === 0) {
    ElMessage.warning('请选择要删除的文档')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDocs.value.length} 个文档吗？此操作不可恢复。`, 
      '批量删除', 
      {
      type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    // 调用批量删除API
    const ids = selectedDocs.value.map(doc => doc.docId || doc.id).filter(id => id)
    if (ids.length === 0) {
      ElMessage.warning('没有有效的文档ID')
      return
    }
    
    const res = await api.post({
      url: '/api/knowledge/delete',
      data: { ids }
    })
    
    if (res.code === 0) {
      ElMessage.success(`成功删除 ${res.deleted_count || ids.length} 个文档`)
      selectedDocs.value = []
    loadDocs()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('批量删除失败:', e)
      const errorMsg = e?.response?.data?.msg || e?.message || '批量删除失败，请重试'
      ElMessage.error(errorMsg)
    }
  }
}

const batchDownload = () => {
  ElMessage.info('批量下载功能待开发')
}

// 权限控制
const userPerms = ref<string[]>(['view', 'edit', 'upload', 'delete'])
const canEdit = computed(() => userPerms.value.includes('edit'))
const canUpload = computed(() => userPerms.value.includes('upload'))
const canDelete = computed(() => userPerms.value.includes('delete'))

// 单个文档操作
// 获取文件类型标签
const getFileTypeLabel = (filename: string): string => {
  if (!filename) return '未知'
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  
  // Word文档
  if (ext === 'docx' || ext === 'doc') {
    return 'docx'
  }
  // PowerPoint文档
  if (ext === 'pptx' || ext === 'ppt') {
    return 'pptx'
  }
  // PDF文档
  if (ext === 'pdf') {
    return 'pdf'
  }
  // 文本文件
  if (ext === 'txt') {
    return 'txt'
  }
  // Excel文件
  if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') {
    return ext
  }
  
  // 其他情况返回扩展名
  return ext || '未知'
}

// 获取知识库标签
const getKnowledgeLabel = (knowledgeBase: string): string => {
  if (!knowledgeBase) return '未分类'
  const kb = knowledgeList.find(item => item.value === knowledgeBase)
  return kb ? kb.label : knowledgeBase
}

// 更新文档的知识库分类
const updateDocKnowledgeBase = async (doc: any) => {
  try {
    const res = await axios.post('http://localhost:3007/api/knowledge/edit', {
      id: doc.docId || doc.id,
      knowledge_base: doc.knowledge_base || ''  // 只更新知识库分类，不更新内容
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (res.data.code === 0) {
      ElMessage.success('知识库分类已更新')
      // 刷新文档列表
      loadDocs()
    } else {
      throw new Error(res.data.msg || '更新失败')
    }
  } catch (error: any) {
    console.error('更新知识库分类失败:', error)
    ElMessage.error('更新失败: ' + (error.response?.data?.msg || error.message || '网络错误'))
    // 恢复原值
    loadDocs()
  }
}

const editDoc = (doc: any) => {
  // 检查文件类型，xlsx/xls文件不支持编辑
  const filename = doc.filename || doc.title || ''
  const fileExt = filename.split('.').pop()?.toLowerCase() || ''
  
  if (fileExt === 'xlsx' || fileExt === 'xls' || fileExt === 'csv') {
    ElMessage.warning('Excel文件（.xlsx/.xls/.csv）不支持在线编辑，请下载后使用Excel软件编辑')
    return
  }
  
  previewDoc(doc)
  editing.value = true
  // 切换到编辑模式
  previewMode.value = 'edit'
}

const deleteDialogVisible = ref(false)
let docToDelete: any = null
const confirmDeleteDoc = (doc: any) => {
  docToDelete = doc
  deleteDialogVisible.value = true
}

// 恢复被覆盖的文档
const restoring = ref(false)
const restoreDeletedDocs = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将从备份文件或智能文档中恢复被覆盖删除的文档。是否继续？',
      '恢复被覆盖文档',
      {
        type: 'warning',
        confirmButtonText: '确定恢复',
        cancelButtonText: '取消'
      }
    )
    
    restoring.value = true
    const res = await api.post({
      url: '/api/knowledge/restore'
    })
    
    if (res.code === 0) {
      if (res.data?.restored_count > 0) {
        ElMessage.success(`恢复成功！共恢复 ${res.data.restored_count} 个文档`)
        // 刷新文档列表
        loadDocs()
      } else {
        ElMessage.info('未发现需要恢复的文档')
      }
    } else {
      ElMessage.error(res.msg || '恢复失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('恢复文档失败:', e)
      const errorMsg = e?.response?.data?.msg || e?.message || '恢复失败，请重试'
      ElMessage.error(errorMsg)
    }
  } finally {
    restoring.value = false
  }
}

// 修复重复ID
const fixingIds = ref(false)
const fixDuplicateIds = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将修复知识库中所有重复的ID，重新分配唯一ID。是否继续？',
      '修复重复ID',
      {
        type: 'warning',
        confirmButtonText: '确定修复',
        cancelButtonText: '取消'
      }
    )
    
    fixingIds.value = true
    const res = await api.post({
      url: '/api/knowledge/fix-ids'
    })
    
    if (res.code === 0) {
      ElMessage.success(`修复成功！共修复 ${res.data?.duplicates_fixed || 0} 个重复ID，总文档数：${res.data?.total || 0}`)
      // 刷新文档列表
      loadDocs()
    } else {
      ElMessage.error(res.msg || '修复失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('修复ID失败:', e)
      const errorMsg = e?.response?.data?.msg || e?.message || '修复失败，请重试'
      ElMessage.error(errorMsg)
    }
  } finally {
    fixingIds.value = false
  }
}

const deleteDoc = async () => {
  if (!docToDelete) {
    ElMessage.error('未选择要删除的文档')
    return
  }
  
  try {
    const docId = docToDelete.docId || docToDelete.id
    if (!docId) {
      ElMessage.error('文档ID不存在')
      return
    }
    
    // 使用api工具发送请求（注意：api工具使用del方法，不是delete）
    const res = await api.del({
      url: `/api/knowledge/${docId}`
    })
    
    if (res.code === 0) {
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
      docToDelete = null
    loadDocs()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e: any) {
    console.error('删除失败:', e)
    const errorMsg = e?.response?.data?.msg || e?.message || '删除失败，请重试'
    ElMessage.error(errorMsg)
  }
}

// 内容显示
const contentDialogVisible = ref(false)
const currentContent = ref('')
function showContent(content: string) {
  currentContent.value = content
  contentDialogVisible.value = true
}

// 预览功能增强
const previewLoading = ref(false)
const previewMode = ref('formatted')
const saveLoading = ref(false)

// 检查是否是Excel文件
const isExcelFile = computed(() => {
  const filename = docPreview.value.title || ''
  const fileExt = filename.split('.').pop()?.toLowerCase() || ''
  return fileExt === 'xlsx' || fileExt === 'xls' || fileExt === 'csv'
})

// 处理编辑模式切换
const handleEditMode = () => {
  if (isExcelFile.value) {
    ElMessage.warning('Excel文件（.xlsx/.xls/.csv）不支持在线编辑，请下载后使用Excel软件编辑')
    return
  }
  previewMode.value = 'edit'
}

// 智能摘要增强
const summaryDialogVisible = ref(false)
const summaryContent = ref('')
const summaryLoading = ref(false)
const summaryProgress = ref(0)
let currentSummaryDoc: any = null

// 预览功能

const formatPreviewContent = (content: string) => {
  if (!content) return ''
  
  // 处理HTML内容
  if (content.includes('<') && content.includes('>')) {
    return content
  }
  
  // 处理纯文本内容，转换为HTML
  return content
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^(.*)$/, '<p>$1</p>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// 智能摘要功能
async function handleSummary(row: any) {
  currentSummaryDoc = row
  summaryDialogVisible.value = true
  summaryLoading.value = true
  summaryContent.value = ''
  summaryProgress.value = 0
  
  // 模拟进度条动画
  const progressInterval = setInterval(() => {
    if (summaryProgress.value < 90) {
      summaryProgress.value += Math.random() * 10
    }
  }, 300)
  
  try {
    // 获取文档内容
    const content = row.content || ''
    if (!content || content.trim() === '' || content === '<p><br></p>') {
      ElMessage.error('文档内容为空，无法生成摘要')
      return
    }
    
    // 调用AI摘要接口
    const res = await axios.post('http://localhost:3007/api/ai/summary', { 
      content: content 
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (res.data.code === 0 && res.data.summary) {
      summaryContent.value = res.data.summary
      summaryProgress.value = 100
      ElMessage.success('摘要生成成功')
    } else {
      throw new Error(res.data.msg || '摘要生成失败')
    }
  } catch (e: any) {
    console.error('摘要生成错误:', e)
    ElMessage.error('摘要生成失败: ' + (e.response?.data?.msg || e.message || '网络错误'))
    summaryContent.value = '摘要生成失败，请稍后重试'
  } finally {
    clearInterval(progressInterval)
    summaryProgress.value = 100
    summaryLoading.value = false
  }
}

// 复制摘要
const copySummary = async () => {
  try {
    // 移除HTML标签
    const textContent = summaryContent.value.replace(/<[^>]*>/g, '')
    await navigator.clipboard.writeText(textContent)
    ElMessage.success('摘要已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 重新生成摘要
const regenerateSummary = () => {
  if (currentSummaryDoc) {
    handleSummary(currentSummaryDoc)
  }
}

// 导出摘要
const exportSummary = () => {
  if (!summaryContent.value) {
    ElMessage.warning('没有摘要内容可导出')
    return
  }
  
  const docTitle = currentSummaryDoc?.title || currentSummaryDoc?.filename || '文档'
  const textContent = summaryContent.value.replace(/<[^>]*>/g, '')
  const content = `${docTitle} - 智能摘要\n\n生成时间: ${new Date().toLocaleString()}\n\n${textContent}`
  
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${docTitle}_摘要.txt`
  link.click()
  
  ElMessage.success('摘要已导出')
}

function downloadDoc(row: any) {
  const docId = row.docId || row.id
  if (!docId) {
    ElMessage.error('文档ID不存在')
    return
  }
  
  // 使用知识库的下载接口
  const token = localStorage.getItem('token')
  const url = `/api/knowledge/${docId}/download`
  
  // 使用fetch下载，可以添加headers
  fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  .then(async res => {
    // 检查Content-Type，如果是JSON说明是错误响应
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      const data = await res.json()
      throw new Error(data.msg || '下载失败')
    }
    
    // 如果是文件响应，获取blob
    if (res.ok) {
      return res.blob()
    } else {
      const data = await res.json().catch(() => ({ msg: '下载失败' }))
      throw new Error(data.msg || '下载失败')
    }
  })
  .then(blob => {
    // 从响应头获取文件名，如果没有则使用默认名称
    const filename = row.filename || row.title || `文档_${docId}`
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('下载成功')
  })
  .catch(error => {
    console.error('下载失败:', error)
    // 只有真正的错误才显示错误消息
    if (error.message && !error.message.includes('下载成功')) {
      ElMessage.error(error.message || '下载失败')
    }
  })
}
</script>

<style scoped lang="scss">
.knowledge-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 20px;
  
  .main-card {
    max-width: 1400px;
    margin: 0 auto;
    background: var(--el-bg-color);
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    
    :deep(.el-card__body) {
      padding: 24px;
    }
    
    .header-section {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
      
      .title-area {
        .page-title {
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px 0;
          color: var(--el-text-color-primary);
          background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .page-desc {
          color: var(--el-text-color-secondary);
          font-size: 14px;
          margin: 0;
        }
      }
      
      .stats-area {
        display: flex;
        gap: 30px;
        
        :deep(.el-statistic__content) {
          font-size: 20px;
          font-weight: 600;
          color: var(--el-color-primary);
        }
        
        :deep(.el-statistic__head) {
          font-size: 12px;
          color: var(--el-text-color-regular);
          margin-bottom: 4px;
        }
      }
    }
    
    // 智能问答区域
    .qa-section {
      margin-bottom: 20px;
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color-lighter);
      
      .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        
        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .section-desc {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .qa-container {
        .qa-input {
          margin-bottom: 16px;
          
          :deep(.el-input-group__prepend) {
            background: var(--el-color-primary-light-9);
            border-color: var(--el-border-color);
            color: var(--el-color-primary);
          }
          
          :deep(.el-input__wrapper) {
            border-radius: 0;
          }
          
          :deep(.el-input-group__append) {
            background: var(--el-color-primary);
            border-color: var(--el-color-primary);
            
            .el-button {
              background: transparent;
              border: none;
              color: white;
              
              &:hover {
                background: rgba(255, 255, 255, 0.1);
              }
            }
          }
        }
        
        .qa-answer {
          background: var(--el-color-success-light-9);
          border: 1px solid var(--el-color-success-light-5);
          border-radius: 8px;
          padding: 16px;
          animation: slideInUp 0.3s ease-out;
          
          .answer-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            font-weight: 600;
            color: var(--el-color-success);
          }
          
          .answer-content {
            color: var(--el-text-color-primary);
            line-height: 1.6;
            margin-bottom: 12px;
            
            :deep(small) {
              color: var(--el-text-color-secondary);
            }
          }
          
          .answer-actions {
            display: flex;
            gap: 8px;
            
            .el-button {
              height: 28px;
              padding: 0 12px;
              font-size: 12px;
            }
          }
        }
        
        // 对话历史记录
        .qa-history {
          background: var(--el-color-info-light-9);
          border: 1px solid var(--el-color-info-light-5);
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 12px;
          animation: slideInUp 0.3s ease-out;
          
          .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-weight: 600;
            color: var(--el-color-info);
            font-size: 14px;
          }
          
          .history-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            
            .history-item {
              background: var(--el-bg-color);
              padding: 12px;
              border-radius: 6px;
              box-shadow: 0 2px 4px var(--el-box-shadow-light);
              
              .user-question {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                color: var(--el-text-color-primary);
                font-weight: 500;
                font-size: 14px;
                
                small {
                  margin-left: auto;
                  color: var(--el-text-color-secondary);
                  font-size: 12px;
                }
              }
              
              .assistant-answer {
                display: flex;
                align-items: flex-start;
                gap: 8px;
                margin-left: 20px;
                
                .answer-text {
                  flex: 1;
                  color: var(--el-text-color-regular);
                  line-height: 1.5;
                  font-size: 13px;
                }
              }
              
              .typing-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--el-color-success);
                font-style: italic;
                margin-left: 20px;
                font-size: 13px;
              }
            }
          }
        }
        
        // 相关文档
        .related-docs {
          margin: 12px 0;
          padding: 12px;
          background: var(--el-bg-color);
          border-radius: 6px;
          border: 1px solid var(--el-border-color-lighter);
          
          .docs-header {
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 8px;
            font-size: 14px;
          }
          
          .docs-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            
            .doc-tag {
              cursor: pointer;
              transition: all 0.2s ease;
              
              &:hover {
                background: var(--el-color-primary-light-3);
                border-color: var(--el-color-primary-light-3);
                color: white;
                transform: translateY(-1px);
              }
            }
          }
        }
        
        .qa-suggestions {
          background: var(--el-color-info-light-9);
          border: 1px solid var(--el-color-info-light-5);
          border-radius: 8px;
          padding: 16px;
          margin-top: 12px;
          animation: slideInUp 0.3s ease-out;
          
          .suggestions-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            font-weight: 600;
            color: var(--el-color-info);
            font-size: 14px;
          }
          
          .suggestions-categories {
            display: flex;
            flex-direction: column;
            gap: 16px;
            
            .category-section {
              background: var(--el-bg-color);
              padding: 12px;
              border-radius: 8px;
              border: 1px solid var(--el-border-color-lighter);
              
              .category-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                font-weight: 600;
                color: var(--el-text-color-primary);
                
                .category-icon {
                  font-size: 16px;
                }
                
                .category-name {
                  font-size: 14px;
                }
              }
              
              .category-questions {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                
                .suggestion-tag {
                  cursor: pointer;
                  transition: all 0.2s ease;
                  
                  &:hover {
                    background: var(--el-color-primary-light-3);
                    border-color: var(--el-color-primary-light-3);
                    color: white;
                    transform: translateY(-1px);
                  }
                }
              }
            }
          }
          
          .quick-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--el-border-color-lighter);
            
            .el-button {
              height: 32px;
              padding: 0 16px;
              font-size: 12px;
            }
          }
        }
        
        // 快速入口
        .quick-entry {
          display: flex;
          gap: 10px;
          justify-content: center;
          align-items: center;
          padding: 12px;
          background: var(--el-bg-color-page);
          border-radius: 8px;
          border: 1px solid var(--el-border-color-lighter);
          
          .el-button {
            height: 32px;
            padding: 0 16px;
            font-size: 12px;
          }
        }
      }
    }
    
    // 搜索过滤区域
    .filter-section {
      margin-bottom: 20px;
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color-lighter);
      
      .filter-container {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        
        .search-input {
          flex: 1;
          min-width: 250px;
        }
        
        .kb-select, .type-select {
          min-width: 140px;
        }
        
        .upload-btn {
          :deep(.el-button) {
            background: var(--el-color-primary);
            border-color: var(--el-color-primary);
            color: white;
            
            &:hover {
              background: var(--el-color-primary-light-3);
              border-color: var(--el-color-primary-light-3);
            }
          }
        }
        
        .option-icon {
          margin-right: 8px;
        }
      }
    }
    
    // 文档列表区域
    .docs-section {
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color-lighter);
      
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .batch-actions {
            :deep(.el-button) {
              height: 32px;
              padding: 0 12px;
              font-size: 12px;
            }
          }
        }
      }
      
      // 分页容器样式
      .pagination-container {
        margin-top: 20px;
        display: flex;
        justify-content: center;
        
        .pagination {
          :deep(.el-pagination) {
            --el-pagination-button-color: var(--el-text-color-primary);
            --el-pagination-button-bg-color: var(--el-fill-color-light);
            --el-pagination-button-disabled-color: var(--el-text-color-placeholder);
            --el-pagination-button-disabled-bg-color: var(--el-fill-color-light);
            --el-pagination-hover-color: var(--el-color-primary);
          }
        }
      }
      
      // 表格样式
      :deep(.el-table) {
        background: var(--el-bg-color);
        
        th.el-table__cell {
          background: var(--el-bg-color-page);
          color: var(--el-text-color-primary);
          font-weight: 600;
          border-bottom: 2px solid var(--el-border-color);
        }
        
        .el-table__row {
          background: var(--el-bg-color);
          
          &:hover {
            background: var(--el-bg-color-page);
          }
          
          td.el-table__cell {
            border-bottom: 1px solid var(--el-border-color-lighter);
            color: var(--el-text-color-primary);
          }
        }
        
        .el-table__empty-block {
          background: var(--el-bg-color);
        }
      }
      
      // 滚动条美化
      :deep(.el-scrollbar__bar) {
        .el-scrollbar__thumb {
          background: var(--el-border-color-dark);
          border-radius: 4px;
          
          &:hover {
            background: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  // 对话框样式
  :deep(.el-dialog) {
    background: var(--el-bg-color);
    border-radius: 12px;
    
    .el-dialog__header {
      background: var(--el-bg-color-page);
      border-radius: 12px 12px 0 0;
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color);
      
      .el-dialog__title {
        color: var(--el-text-color-primary);
        font-weight: 600;
      }
    }
    
    .el-dialog__body {
      color: var(--el-text-color-primary);
      padding: 20px;
    }
    
    .el-dialog__footer {
      border-top: 1px solid var(--el-border-color);
      padding: 16px 20px;
      background: var(--el-bg-color-page);
      border-radius: 0 0 12px 12px;
    }
  }
  
  // 预览弹窗特别样式
  :deep(.preview-dialog) {
    margin: 5vh auto 5vh;
    max-height: 90vh;
    
    .el-dialog__body {
      max-height: calc(90vh - 120px);
      overflow-y: auto;
      padding: 16px;
    }
    
    .el-dialog__header {
      position: sticky;
      top: 0;
      z-index: 1;
    }
    
    .el-dialog__footer {
      position: sticky;
      bottom: 0;
      z-index: 1;
    }
  }
  
  // 响应式设计
  @media (max-width: 768px) {
    padding: 12px;
    
    .header-section {
      flex-direction: column;
      gap: 16px;
      text-align: center;
      
      .stats-area {
        justify-content: center;
        gap: 20px;
      }
    }
    
    .filter-container {
      flex-direction: column;
      align-items: stretch;
      
      .search-input, .kb-select, .type-select {
        width: 100%;
        min-width: auto;
      }
    }
    
    .section-header {
      flex-direction: column;
      gap: 12px;
      
      .header-actions {
        justify-content: center;
      }
    }
    
    // 预览弹窗移动端适配
    :deep(.preview-dialog) {
      margin: 2vh auto 2vh;
      max-height: 96vh;
      
      .el-dialog__body {
        max-height: calc(96vh - 100px);
        padding: 12px;
      }
    }
    
    .preview-content {
      max-height: calc(96vh - 200px);
      padding: 12px;
    }
    
    .preview-toolbar {
      flex-direction: column;
      gap: 8px;
      
      .el-button-group {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
    }
  }
}

// 动画效果
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 深色模式专门优化
@media (prefers-color-scheme: dark) {
  .knowledge-page .main-card {
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
  }
}

// 预览功能样式
.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--el-text-color-secondary);
  
  .el-icon {
    font-size: 32px;
    margin-bottom: 12px;
    color: var(--el-color-primary);
  }
  
  span {
    font-size: 14px;
    margin-bottom: 16px;
  }
}

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
  max-height: calc(90vh - 250px);
  overflow-y: auto;
  width: 100%;
  background: var(--el-bg-color);
  padding: 20px;
  border-radius: 8px;
  color: var(--el-text-color-primary);
  line-height: 1.6;
  border: 1px solid var(--el-border-color);
  
  &.formatted-preview {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    
    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
      color: var(--el-color-primary);
      margin: 16px 0 8px 0;
      font-weight: 600;
    }
    
    :deep(p) {
      margin: 8px 0;
      text-align: justify;
    }
    
    :deep(table) {
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
  }
  
  &.raw-preview {
    font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    background: var(--el-fill-color-light);
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  &.edit-preview {
    padding: 0;
    border: none;
    background: transparent;
    
    :deep(.el-textarea__inner) {
      min-height: 500px;
      font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.5;
      border: 1px solid var(--el-border-color);
      border-radius: 6px;
      padding: 16px;
      resize: vertical;
    }
  }
}

.preview-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  align-items: center;
}

// 智能摘要样式
.summary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--el-text-color-secondary);
  
  .el-icon {
    font-size: 32px;
    margin-bottom: 12px;
    color: var(--el-color-primary);
  }
  
  span {
    font-size: 14px;
    margin-bottom: 16px;
  }
  
  .loading-progress {
    width: 200px;
    margin-top: 8px;
  }
}

.summary-content {
  .summary-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px;
    background: var(--el-color-success-light-9);
    border-radius: 6px;
    border: 1px solid var(--el-color-success-light-5);
    
    .el-icon {
      font-size: 18px;
    }
    
    span {
      font-weight: 600;
      color: var(--el-color-success);
    }
  }
  
  .summary-body {
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    padding: 20px;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    margin-bottom: 16px;
    
    :deep(h1), :deep(h2), :deep(h3) {
      color: var(--el-color-primary);
      margin: 16px 0 8px 0;
      font-weight: 600;
    }
    
    :deep(p) {
      margin: 8px 0;
    }
    
    :deep(strong) {
      color: var(--el-color-primary);
      font-weight: 600;
    }
    
    :deep(ul), :deep(ol) {
      margin: 12px 0;
      padding-left: 20px;
    }
    
    :deep(li) {
      margin: 4px 0;
    }
  }
  
  .summary-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    
    .el-button {
      height: 32px;
      padding: 0 12px;
      font-size: 12px;
    }
  }
}

.summary-empty {
  padding: 40px;
  text-align: center;
}
</style> 