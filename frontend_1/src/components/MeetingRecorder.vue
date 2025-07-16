<template>
  <div class="meeting-recorder">
    <div class="recorder-header">
      <h3>会议录音与转录</h3>
      <div class="recorder-status">
        <el-tag v-if="isRecording" type="danger" class="pulse">● 录音中</el-tag>
        <el-tag v-else-if="isPaused" type="warning">⏸ 已暂停</el-tag>
        <el-tag v-else type="info">● 待录音</el-tag>
        <span class="duration">{{ formatDuration(duration) }}</span>
      </div>
    </div>

    <div class="recorder-controls">
      <el-button 
        v-if="!isRecording && !isPaused" 
        type="primary" 
        size="large"
        @click="startRecording"
        :loading="loading"
      >
        <el-icon><Microphone /></el-icon>
        开始录音
      </el-button>
      
      <el-button 
        v-if="isRecording" 
        type="warning" 
        size="large"
        @click="pauseRecording"
      >
        <el-icon><VideoPause /></el-icon>
        暂停
      </el-button>
      
      <el-button 
        v-if="isPaused" 
        type="primary" 
        size="large"
        @click="resumeRecording"
      >
        <el-icon><VideoPlay /></el-icon>
        继续
      </el-button>
      
      <el-button 
        v-if="isRecording || isPaused" 
        type="danger" 
        size="large"
        @click="stopRecording"
      >
        <el-icon><CircleClose /></el-icon>
        停止录音
      </el-button>
      
      <!-- 查看历史按钮 - 始终可见 -->
      <el-button 
        @click="viewRecordingHistory"
        size="large"
        type="info"
        class="history-btn"
      >
        <el-icon><Folder /></el-icon>
        录音历史
      </el-button>
    </div>

    <!-- 语音转文字实时显示 -->
    <div class="transcription-section" v-if="isRecording || transcriptText">
      <div class="section-header">
        <h4>实时转录</h4>
        <div class="transcription-controls">
          <el-switch 
            v-model="enableTranscription" 
            active-text="语音转文字" 
            @change="toggleTranscription"
          />
          <el-button 
            size="small" 
            @click="clearTranscript"
            :disabled="!transcriptText"
          >
            清空
          </el-button>
          <el-button 
            size="small" 
            @click="copyTranscript"
            :disabled="!transcriptText"
          >
            复制
          </el-button>
        </div>
      </div>
      
      <el-scrollbar class="transcript-container">
        <div class="transcript-text" v-html="formattedTranscript"></div>
        <div v-if="isRecording && enableTranscription" class="listening-indicator">
          <el-icon class="pulse"><Microphone /></el-icon>
          <span>正在听取...</span>
        </div>
      </el-scrollbar>
    </div>

    <!-- 录音文件管理 -->
    <div class="recordings-section" v-if="recordings.length">
      <div class="section-header">
        <h4>录音文件</h4>
      </div>
      <div class="recordings-list">
        <div 
          v-for="(recording, index) in recordings" 
          :key="index" 
          class="recording-item"
        >
          <div class="recording-info">
            <el-icon><Document /></el-icon>
            <span class="recording-name">{{ recording.name }}</span>
            <span class="recording-duration">{{ formatDuration(recording.duration) }}</span>
          </div>
          <div class="recording-actions">
            <el-button 
              size="small" 
              @click="playRecording(recording)"
              :loading="playing === recording"
            >
              <el-icon><VideoPlay /></el-icon>
              播放
            </el-button>
            <el-button 
              size="small" 
              @click="downloadRecording(recording)"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button 
              size="small" 
              @click="deleteRecording(index)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 会议纪要生成 -->
    <div class="minutes-section" v-if="transcriptText">
      <h4>智能纪要</h4>
      <el-button 
        type="primary" 
        @click="generateMinutes"
        :loading="generatingMinutes"
      >
        <el-icon><DocumentAdd /></el-icon>
        生成会议纪要
      </el-button>
      
      <el-card v-if="meetingMinutes" class="minutes-card">
        <template #header>
          <div class="minutes-header">
            <span>会议纪要</span>
            <el-button size="small" @click="copyMinutes">复制纪要</el-button>
          </div>
        </template>
        <div class="minutes-content" v-html="meetingMinutes"></div>
      </el-card>
    </div>

    <!-- 录音历史弹窗 -->
    <el-dialog 
      v-model="historyDialogVisible" 
      title="录音历史" 
      width="65%"
      class="history-dialog"
    >
      <div class="history-content">
        <!-- 搜索工具栏 -->
        <div class="search-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索会议标题或录音文件名..."
            clearable
            size="default"
            class="search-input"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="loadRecordingHistory" :loading="historyLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <!-- 录音列表 -->
        <el-table 
          :data="recordingHistory" 
          v-loading="historyLoading"
          class="history-table"
          max-height="300"
          size="small"
        >
          <el-table-column label="会议标题" width="220" show-overflow-tooltip>
            <template #default="scope">
              <div class="meeting-info">
                <div 
                  class="meeting-title" 
                  :title="scope.row.meeting_title || '未关联会议'"
                >
                  {{ truncateText(scope.row.meeting_title || '未关联会议', 20) }}
                </div>
                <div 
                  class="filename" 
                  :title="scope.row.filename"
                >
                  {{ truncateText(scope.row.filename, 25) }}
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="录音时长" width="100">
            <template #default="scope">
              <span class="duration">{{ formatDuration(scope.row.duration) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="文件大小" width="100">
            <template #default="scope">
              <span class="file-size">{{ formatFileSize(scope.row.file_size) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="创建时间" width="180">
            <template #default="scope">
              <div class="time-info">
                <div>{{ formatDate(scope.row.created_at) }}</div>
                <div class="time-detail">{{ formatTime(scope.row.created_at) }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="280" fixed="right">
            <template #default="scope">
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="viewHistoryDetail(scope.row)"
                  class="detail-btn"
                >
                  详情
                </el-button>
                <el-button 
                  size="small" 
                  @click="downloadHistoryRecording(scope.row)"
                  :disabled="!scope.row.file_path"
                  class="download-btn"
                >
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  @click="deleteHistoryRecording(scope.row)"
                  class="delete-btn"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
          v-if="historyTotal > 0"
          v-model:current-page="historyCurrentPage"
          v-model:page-size="historyPageSize"
          :total="historyTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          class="pagination"
          @size-change="handleHistorySizeChange"
          @current-change="handleHistoryPageChange"
        />

        <!-- 空状态 -->
        <el-empty 
          v-if="!historyLoading && recordingHistory.length === 0" 
          :image-size="120"
          description="暂无录音历史记录"
        />
      </div>
      
      <template #footer>
        <el-button @click="historyDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 录音详情弹窗 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="录音详情" 
      width="60%"
      class="detail-dialog"
    >
      <div v-if="currentRecording" class="recording-detail">
        <!-- 基本信息 -->
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="会议标题">
            {{ currentRecording.meeting_title || '未关联会议' }}
          </el-descriptions-item>
          <el-descriptions-item label="录音文件">
            {{ currentRecording.filename }}
          </el-descriptions-item>
          <el-descriptions-item label="录音时长">
            {{ formatDuration(currentRecording.duration) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentRecording.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ currentRecording.created_at }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentRecording.status === 'completed' ? 'success' : 'warning'">
              {{ currentRecording.status === 'completed' ? '已完成' : '处理中' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 录音播放器 -->
        <div class="audio-player-section" v-if="currentRecording.file_path">
          <h4>录音播放</h4>
          <audio 
            :src="`/uploads/${currentRecording.file_path}`" 
            controls 
            class="audio-player"
            preload="metadata"
          >
            您的浏览器不支持音频播放
          </audio>
        </div>

        <!-- 转录内容 -->
        <div class="transcript-section" v-if="currentRecording.transcript">
          <div class="section-header">
            <h4>语音转录</h4>
            <el-button size="small" @click="copyText(currentRecording.transcript)">
              复制转录
            </el-button>
          </div>
          <el-scrollbar class="transcript-content">
            <p class="transcript-text">{{ currentRecording.transcript }}</p>
          </el-scrollbar>
        </div>

        <!-- 会议纪要 -->
        <div class="minutes-section" v-if="currentRecording.minutes">
          <div class="section-header">
            <h4>会议纪要</h4>
            <el-button size="small" @click="copyText(currentRecording.minutes)">
              复制纪要
            </el-button>
          </div>
          <div class="minutes-content" v-html="currentRecording.minutes"></div>
        </div>

        <!-- 空转录提示 -->
        <el-empty 
          v-if="!currentRecording.transcript && !currentRecording.minutes"
          :image-size="80"
          description="暂无转录内容和会议纪要"
        />
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button 
            type="primary" 
            @click="downloadHistoryRecording(currentRecording)"
            :disabled="!currentRecording?.file_path"
          >
            下载录音
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Microphone, 
  VideoPause, 
  VideoPlay, 
  CircleClose, 
  Document, 
  Download, 
  Delete,
  DocumentAdd,
  Folder,
  Search,
  Refresh
} from '@element-plus/icons-vue'

const props = defineProps<{
  meetingId?: number
  meetingTitle?: string
}>()

const emit = defineEmits<{
  'recording-started': []
  'recording-stopped': [recording: any]
  'minutes-generated': [minutes: string]
}>()

// 录音状态
const isRecording = ref(false)
const isPaused = ref(false)
const loading = ref(false)
const duration = ref(0)
let durationTimer: any = null

// 语音转文字
const enableTranscription = ref(true)
const transcriptText = ref('')
const isListening = ref(false)

// 录音相关
let mediaRecorder: MediaRecorder | null = null
let audioStream: MediaStream | null = null
let audioChunks: Blob[] = []
const recordings = ref<any[]>([])
const playing = ref<any>(null)

// 语音识别
let recognition: any = null
let finalTranscript = ref('')
let interimTranscript = ref('')

// 会议纪要
const generatingMinutes = ref(false)
const meetingMinutes = ref('')

// 录音历史弹窗
const historyDialogVisible = ref(false)
const historyLoading = ref(false)
const recordingHistory = ref<any[]>([])
const historyTotal = ref(0)
const historyCurrentPage = ref(1)
const historyPageSize = ref(10)
const searchKeyword = ref('')

// 详情弹窗
const detailDialogVisible = ref(false)
const currentRecording = ref<any>(null)

// 计算属性
const formattedTranscript = computed(() => {
  let text = finalTranscript.value
  if (interimTranscript.value) {
    text += `<span class="interim">${interimTranscript.value}</span>`
  }
  return text.replace(/\n/g, '<br>') || '<span class="placeholder">暂无转录内容...</span>'
})

// 格式化时长
const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 初始化语音识别
const initSpeechRecognition = () => {
  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'zh-CN'
    
    recognition.onresult = (event: any) => {
      let interim = ''
      let final = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      
      if (final) {
        finalTranscript.value += final + '\n'
        transcriptText.value = finalTranscript.value
      }
      interimTranscript.value = interim
    }
    
    recognition.onerror = (event: any) => {
      console.error('语音识别错误:', event.error)
      if (event.error === 'no-speech') {
        // 没有检测到语音，继续监听
        if (isRecording.value && enableTranscription.value) {
          setTimeout(() => recognition?.start(), 1000)
        }
      }
    }
    
    recognition.onend = () => {
      if (isRecording.value && enableTranscription.value) {
        // 重新启动识别以保持连续
        setTimeout(() => recognition?.start(), 100)
      }
    }
  } else if ('SpeechRecognition' in window) {
    recognition = new (window as any).SpeechRecognition()
    // 同样的配置...
  } else {
    console.warn('浏览器不支持语音识别')
    enableTranscription.value = false
  }
}

// 开始录音
const startRecording = async () => {
  try {
    loading.value = true
    
    // 获取麦克风权限
    audioStream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })
    
    // 创建媒体录制器
    mediaRecorder = new MediaRecorder(audioStream, {
      mimeType: 'audio/webm;codecs=opus'
    })
    
    audioChunks = []
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      const recording = {
        name: `会议录音_${new Date().toLocaleString()}`,
        blob: audioBlob,
        url: URL.createObjectURL(audioBlob),
        duration: duration.value,
        timestamp: Date.now()
      }
      recordings.value.push(recording)
      
      // 自动上传录音到后端
      await uploadRecordingToServer(recording)
      
      emit('recording-stopped', recording)
    }
    
    // 开始录音
    mediaRecorder.start(1000) // 每秒收集一次数据
    isRecording.value = true
    duration.value = 0
    
    // 开始计时
    durationTimer = setInterval(() => {
      duration.value++
    }, 1000)
    
    // 开始语音转文字
    if (enableTranscription.value && recognition) {
      recognition.start()
    }
    
    emit('recording-started')
    ElMessage.success('录音已开始')
    
  } catch (error) {
    console.error('录音启动失败:', error)
    ElMessage.error('无法启动录音，请检查麦克风权限')
  } finally {
    loading.value = false
  }
}

// 暂停录音
const pauseRecording = () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.pause()
    isPaused.value = true
    isRecording.value = false
    
    if (durationTimer) {
      clearInterval(durationTimer)
    }
    
    if (recognition) {
      recognition.stop()
    }
    
    ElMessage.info('录音已暂停')
  }
}

// 继续录音
const resumeRecording = () => {
  if (mediaRecorder && mediaRecorder.state === 'paused') {
    mediaRecorder.resume()
    isPaused.value = false
    isRecording.value = true
    
    // 重新开始计时
    durationTimer = setInterval(() => {
      duration.value++
    }, 1000)
    
    // 重新开始语音识别
    if (enableTranscription.value && recognition) {
      recognition.start()
    }
    
    ElMessage.info('录音已继续')
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder) {
    mediaRecorder.stop()
    isRecording.value = false
    isPaused.value = false
    
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }
    
    if (recognition) {
      recognition.stop()
    }
    
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop())
      audioStream = null
    }
    
    ElMessage.success('录音已停止')
  }
}

// 切换语音转文字
const toggleTranscription = (enabled: boolean) => {
  if (isRecording.value) {
    if (enabled && recognition) {
      recognition.start()
    } else if (recognition) {
      recognition.stop()
    }
  }
}

// 清空转录
const clearTranscript = () => {
  finalTranscript.value = ''
  transcriptText.value = ''
  interimTranscript.value = ''
}

// 复制转录
const copyTranscript = () => {
  if (transcriptText.value) {
    navigator.clipboard.writeText(transcriptText.value)
    ElMessage.success('转录内容已复制')
  }
}

// 播放录音
const playRecording = (recording: any) => {
  if (playing.value === recording) {
    // 停止播放
    playing.value = null
    return
  }
  
  playing.value = recording
  const audio = new Audio(recording.url)
  
  audio.onended = () => {
    playing.value = null
  }
  
  audio.onerror = () => {
    playing.value = null
    ElMessage.error('播放失败')
  }
  
  audio.play()
}

// 下载录音
const downloadRecording = (recording: any) => {
  const link = document.createElement('a')
  link.href = recording.url
  link.download = `${recording.name}.webm`
  link.click()
}

// 删除录音
const deleteRecording = (index: number) => {
  ElMessageBox.confirm('确定要删除这个录音吗？', '确认删除', {
    type: 'warning'
  }).then(() => {
    const recording = recordings.value[index]
    URL.revokeObjectURL(recording.url)
    recordings.value.splice(index, 1)
    ElMessage.success('录音已删除')
  }).catch(() => {})
}

// 生成会议纪要
const generateMinutes = async () => {
  if (!transcriptText.value) {
    ElMessage.warning('没有转录内容可生成纪要')
    return
  }
  
  generatingMinutes.value = true
  
  try {
    const response = await fetch('/api/ai/summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        content: transcriptText.value,
        type: 'meeting_minutes',
        meetingTitle: props.meetingTitle
      })
    })
    
    const result = await response.json()
    
    if (result.code === 0) {
      meetingMinutes.value = formatMinutes(result.summary)
      emit('minutes-generated', meetingMinutes.value)
      ElMessage.success('会议纪要生成成功')
    } else {
      throw new Error(result.msg || '生成失败')
    }
  } catch (error) {
    console.error('生成会议纪要失败:', error)
    ElMessage.error('生成会议纪要失败')
  } finally {
    generatingMinutes.value = false
  }
}

// 格式化会议纪要
const formatMinutes = (summary: string) => {
  let formatted = summary
  
  // 添加会议信息头部
  const header = `
    <div class="minutes-header-info">
      <h3>会议纪要</h3>
      <p><strong>会议主题：</strong>${props.meetingTitle || '未知'}</p>
      <p><strong>记录时间：</strong>${new Date().toLocaleString()}</p>
      <p><strong>会议时长：</strong>${formatDuration(duration.value)}</p>
    </div>
    <hr>
  `
  
  return header + formatted.replace(/\n/g, '<br>')
}

// 复制纪要
const copyMinutes = () => {
  if (meetingMinutes.value) {
    const text = meetingMinutes.value.replace(/<[^>]*>/g, '')
    navigator.clipboard.writeText(text)
    ElMessage.success('会议纪要已复制')
  }
}

// 上传录音到服务器
const uploadRecordingToServer = async (recording: any) => {
  try {
    const formData = new FormData()
    
    // 创建文件对象
    const file = new File([recording.blob], recording.name, { type: 'audio/webm' })
    formData.append('file', file)
    
    // 录音数据
    const recordingData = {
      meeting_id: props.meetingId,
      meeting_title: props.meetingTitle,
      transcript: transcriptText.value,
      minutes: meetingMinutes.value,
      duration: recording.duration,
      file_size: recording.blob.size
    }
    formData.append('data', JSON.stringify(recordingData))
    
    const response = await fetch('/api/recordings/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: formData
    })
    
    const result = await response.json()
    
    if (result.code === 0) {
      ElMessage.success('录音已保存到历史记录')
      // 给录音添加服务器ID
      recording.serverId = result.data.id
    } else {
      throw new Error(result.msg || '上传失败')
    }
  } catch (error) {
    console.error('上传录音失败:', error)
    ElMessage.warning('录音保存失败，但本地文件仍可使用')
  }
}

// 查看录音历史
const viewRecordingHistory = () => {
  historyDialogVisible.value = true
  loadRecordingHistory()
}

// 加载录音历史
const loadRecordingHistory = async () => {
  historyLoading.value = true
  try {
    const params = new URLSearchParams({
      page: historyCurrentPage.value.toString(),
      pageSize: historyPageSize.value.toString(),
      keyword: searchKeyword.value
    })

    const response = await fetch(`/api/recordings/history?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    const result = await response.json()
    
    if (result.code === 0) {
      recordingHistory.value = result.data.list
      historyTotal.value = result.data.total
    } else {
      throw new Error(result.msg || '加载失败')
    }
  } catch (error) {
    console.error('加载录音历史失败:', error)
    ElMessage.error('加载录音历史失败')
  } finally {
    historyLoading.value = false
  }
}

// 搜索处理
let searchTimer: any = null
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    historyCurrentPage.value = 1
    loadRecordingHistory()
  }, 500)
}

// 分页处理
const handleHistorySizeChange = (size: number) => {
  historyPageSize.value = size
  historyCurrentPage.value = 1
  loadRecordingHistory()
}

const handleHistoryPageChange = (page: number) => {
  historyCurrentPage.value = page
  loadRecordingHistory()
}

// 查看历史详情
const viewHistoryDetail = async (recording: any) => {
  try {
    const response = await fetch(`/api/recordings/${recording.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    const result = await response.json()
    
    if (result.code === 0) {
      currentRecording.value = result.data
      detailDialogVisible.value = true
    } else {
      throw new Error(result.msg || '获取详情失败')
    }
  } catch (error) {
    console.error('获取录音详情失败:', error)
    ElMessage.error('获取录音详情失败')
  }
}

// 下载历史录音
const downloadHistoryRecording = async (recording: any) => {
  try {
    const response = await fetch(`/api/recordings/${recording.id}/download`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = recording.filename
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('下载成功')
    } else {
      throw new Error('下载失败')
    }
  } catch (error) {
    console.error('下载录音失败:', error)
    ElMessage.error('下载录音失败')
  }
}

// 删除历史录音
const deleteHistoryRecording = async (recording: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除录音 "${recording.filename}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const response = await fetch(`/api/recordings/${recording.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    const result = await response.json()
    
    if (result.code === 0) {
      ElMessage.success('删除成功')
      loadRecordingHistory()
    } else {
      throw new Error(result.msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除录音失败:', error)
      ElMessage.error('删除录音失败')
    }
  }
}

// 截断文本显示
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 复制文本
const copyText = (text: string) => {
  const plainText = text.replace(/<[^>]*>/g, '')
  navigator.clipboard.writeText(plainText).then(() => {
    ElMessage.success('复制成功')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split(' ')[0]
}

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split(' ')[1] || ''
}

onMounted(() => {
  initSpeechRecognition()
})

onUnmounted(() => {
  if (isRecording.value || isPaused.value) {
    stopRecording()
  }
  
  if (durationTimer) {
    clearInterval(durationTimer)
  }
  
  // 清理录音文件URL
  recordings.value.forEach(recording => {
    URL.revokeObjectURL(recording.url)
  })
})
</script>

<style scoped>
.meeting-recorder {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.recorder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.recorder-header h3 {
  margin: 0;
  color: #333;
}

.recorder-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.duration {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: bold;
  color: #666;
}

.recorder-controls {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
}

.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.transcription-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  color: #333;
}

.transcription-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.transcript-container {
  max-height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  background: white;
}

.transcript-text {
  line-height: 1.6;
  color: #333;
  min-height: 60px;
}

.transcript-text .interim {
  color: #999;
  font-style: italic;
}

.transcript-text .placeholder {
  color: #ccc;
  font-style: italic;
}

.listening-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-size: 14px;
  margin-top: 8px;
}

.recordings-section h4,
.minutes-section h4 {
  margin: 20px 0 12px 0;
  color: #333;
}

.recordings-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recording-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #eee;
}

.recording-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.recording-name {
  font-weight: 500;
}

.recording-duration {
  color: #666;
  font-family: monospace;
}

.recording-actions {
  display: flex;
  gap: 8px;
}

.minutes-card {
  margin-top: 12px;
}

.minutes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.minutes-content {
  line-height: 1.6;
  color: #333;
}

.minutes-header-info {
  margin-bottom: 16px;
}

.minutes-header-info h3 {
  margin: 0 0 8px 0;
}

.minutes-header-info p {
  margin: 4px 0;
  color: #666;
}

/* 录音历史弹窗样式 */
.history-dialog {
  :deep(.el-dialog) {
    border-radius: 8px;
  }

  .history-content {
    .search-toolbar {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      align-items: center;
      
      .search-input {
        flex: 1;
        max-width: 400px;
      }
    }

    .history-table {
      .meeting-info {
        .meeting-title {
          font-weight: 500;
          color: #1f2937;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 100%;
        }
        
        .filename {
          font-size: 12px;
          color: #6b7280;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 100%;
        }
      }

      .duration {
        font-family: monospace;
        font-weight: 500;
      }

      .file-size {
        font-size: 13px;
        color: #6b7280;
      }

      .time-info {
        .time-detail {
          font-size: 12px;
          color: #9ca3af;
        }
      }

      .action-buttons {
        display: flex;
        gap: 8px;
        justify-content: flex-start;
        flex-wrap: nowrap;
        align-items: center;
        width: 100%;
        
        .detail-btn {
          min-width: 60px;
          padding: 5px 10px;
          font-size: 12px;
        }
        
        .download-btn,
        .delete-btn {
          min-width: 36px;
          padding: 5px 8px;
          font-size: 12px;
        }
      }
    }

    .pagination {
      margin-top: 12px;
      display: flex;
      justify-content: center;
    }
  }
}

/* 录音详情弹窗样式 */
.detail-dialog {
  .recording-detail {
    .audio-player-section {
      margin: 20px 0;
      
      h4 {
        margin: 0 0 12px 0;
        color: #374151;
      }
      
      .audio-player {
        width: 100%;
        outline: none;
      }
    }

    .transcript-section,
    .minutes-section {
      margin: 20px 0;
      
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        h4 {
          margin: 0;
          color: #374151;
        }
      }
      
      .transcript-content {
        max-height: 300px;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 16px;
        background: #f9fafb;
        
        .transcript-text {
          line-height: 1.6;
          color: #374151;
          margin: 0;
        }
      }
      
      .minutes-content {
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 16px;
        background: #f9fafb;
        line-height: 1.6;
        color: #374151;
        
        :deep(h2), :deep(h3) {
          color: #1f2937;
          margin-top: 0;
        }
        
        :deep(p) {
          margin: 8px 0;
        }
        
        :deep(hr) {
          border: none;
          border-top: 1px solid #e5e7eb;
          margin: 16px 0;
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style> 