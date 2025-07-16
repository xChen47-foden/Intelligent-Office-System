<template>
  <div class="meetings-page">
    <h2 class="page-title">会议管理</h2>
    <div class="meetings-toolbar">
      <el-input
        v-model="searchText"
        placeholder="搜索会议主题/主持人..."
        clearable
        size="large"
        class="meeting-search-input high-input"
      />
      <el-select
        v-model="selectedStatus"
        placeholder="会议状态"
        size="large"
        class="meeting-status-select high-input"
      >
        <el-option label="全部" value="" />
        <el-option label="待召开" value="upcoming" />
        <el-option label="已结束" value="finished" />
        <el-option label="已取消" value="canceled" />
      </el-select>
      <el-button
        v-if="canCreate"
        type="primary"
        size="small"
        @click="showCreateDialog = true"
        style="margin-left: 12px;"
      >安排会议</el-button>
    </div>
    <el-card class="meetings-list-card">
      <div class="batch-toolbar" v-if="selectedMeetings.length">
        <el-button v-if="canDelete" size="small" @click="batchDelete">批量删除</el-button>
        <el-button size="small" @click="batchExport">批量导出</el-button>
      </div>
      <el-scrollbar style="max-height: 340px;">
        <el-table :data="pagedMeetings" style="width: 100%" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="title" label="会议主题" />
          <el-table-column prop="host" label="主持人" width="100" />
          <el-table-column prop="time" label="时间" width="160">
            <template #default="scope">
              {{ formatTime(scope.row.time) }}
            </template>
          </el-table-column>
          <el-table-column prop="location" label="地点" width="120" />
          <el-table-column prop="cycle" label="周期" width="80">
            <template #default="scope">
              <el-tag v-if="scope.row.cycle && scope.row.cycle !== 'none'" type="info">
                {{ cycleText(scope.row.cycle) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="scope">
              <el-tag :type="statusTagType(scope.row.status)" size="small">{{ statusText(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button type="text" size="small" @click="viewDetail(scope.row)">详情</el-button>
              <el-button v-if="canEdit && scope.row.status === 'upcoming'" type="text" size="small" @click="handleEditMeeting(scope.row)">编辑</el-button>
              <el-button v-if="canDelete" type="text" size="small" @click="handleDeleteMeeting(scope.row)">删除</el-button>
              <el-button v-if="scope.row.status === 'upcoming'" type="text" size="small" @click="startMeetingRecording(scope.row)">开始录音</el-button>
              <el-button v-if="scope.row.status === 'finished'" type="text" size="small" @click="showMinutesDialog(scope.row)">生成纪要</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-scrollbar>
      <el-pagination
        v-if="totalPages > 1"
        background
        layout="prev, pager, next"
        :total="filteredMeetings.length"
        :page-size="pageSize"
        :current-page.sync="currentPage"
        style="margin-top: 12px; text-align: right;"
      />
      <el-empty v-if="!filteredMeetings.length && !loading" description="暂无会议" />
      <el-skeleton v-if="loading" :rows="4" animated style="margin-top: 20px;" />
    </el-card>
    <!-- 会议详情/编辑弹窗 -->
    <el-dialog v-model="detailDialogVisible" :title="detailDialogTitle" width="520px">
      <el-form :model="detailForm" label-width="90px" v-if="detailDialogVisible">
        <el-form-item label="会议主题">
          <el-input v-model="detailForm.title" :readonly="!editingDetail" />
        </el-form-item>
        <el-form-item label="主持人">
          <el-input v-model="detailForm.host" :readonly="!editingDetail" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="detailForm.time" type="datetime" :readonly="!editingDetail" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="detailForm.location" :readonly="!editingDetail" />
        </el-form-item>
        <el-form-item label="参会人">
          <el-select
            v-model="detailForm.participants"
            :disabled="!editingDetail"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择参会人"
            style="width: 100%;"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.realName || user.username"
              :value="user.id"
            >
              <div style="display: flex; align-items: center;">
                <el-avatar :size="24" :src="user.avatar" style="margin-right: 8px;">
                  {{ (user.realName || user.username).charAt(0) }}
                </el-avatar>
                <span>{{ user.realName || user.username }}</span>
                <span v-if="user.department" style="color: #999; margin-left: 8px; font-size: 12px;">
                  ({{ user.department }})
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="detailForm.status" :disabled="!editingDetail">
            <el-option label="待召开" value="upcoming" />
            <el-option label="已结束" value="finished" />
            <el-option label="已取消" value="canceled" />
          </el-select>
        </el-form-item>
        <el-form-item label="审批状态" v-if="detailForm.status === 'pending' || detailForm.status === 'rejected'">
          <el-tag v-if="detailForm.status === 'pending'" type="warning">待审批</el-tag>
          <el-tag v-if="detailForm.status === 'rejected'" type="danger">已驳回</el-tag>
        </el-form-item>
        <el-form-item label="审批操作" v-if="detailForm.status === 'pending' && canApprove">
          <el-button type="success" size="small" @click="approveMeeting('approve')">同意</el-button>
          <el-button type="danger" size="small" @click="approveMeeting('reject')">驳回</el-button>
        </el-form-item>
        <el-form-item label="审批历史" v-if="approvalHistory.length">
          <el-timeline>
            <el-timeline-item
              v-for="item in approvalHistory"
              :key="item.time"
              :timestamp="item.time"
              :color="item.status === 'approved' ? 'green' : item.status === 'rejected' ? 'red' : 'gray'"
            >
              {{ item.user }}：{{ item.action }}（{{ item.remark || '无备注' }}）
            </el-timeline-item>
          </el-timeline>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="detailForm.remark" type="textarea" :readonly="!editingDetail" />
        </el-form-item>
        <div v-if="Array.isArray(attachments) && attachments.length" style="margin: 16px 0 0 0;">
          <h4 style="margin-bottom: 8px;">附件列表：</h4>
          <el-table :data="Array.isArray(attachments) ? attachments : []" size="small" border style="width: 100%;">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column label="下载">
              <template #default="scope">
                <a :href="scope.row.url" target="_blank">下载</a>
              </template>
            </el-table-column>
            <el-table-column prop="upload_time" label="上传时间" width="160" />
          </el-table>
        </div>
      </el-form>
      <template #footer>
        <el-button v-if="!editingDetail && canEdit" @click="editingDetail = true">编辑</el-button>
        <el-button v-if="editingDetail" type="primary" @click="saveDetail">保存</el-button>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <!-- 新建/编辑会议弹窗 -->
    <el-dialog v-model="showCreateDialog" title="安排会议" width="480px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="会议主题">
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="主持人">
          <el-input v-model="createForm.host" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="createForm.time" type="datetime" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="createForm.location" />
        </el-form-item>
        <el-form-item label="参会人">
          <el-select
            v-model="createForm.participants"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择参会人"
            style="width: 100%;"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.realName || user.username"
              :value="user.id"
            >
              <div style="display: flex; align-items: center;">
                <el-avatar :size="24" :src="user.avatar" style="margin-right: 8px;">
                  {{ (user.realName || user.username).charAt(0) }}
                </el-avatar>
                <span>{{ user.realName || user.username }}</span>
                <span v-if="user.department" style="color: #999; margin-left: 8px; font-size: 12px;">
                  ({{ user.department }})
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="会议周期">
          <el-select v-model="createForm.cycle" placeholder="请选择周期" style="width: 100%;">
            <el-option label="不重复" value="none" />
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" type="textarea" />
        </el-form-item>
        <el-form-item label="上传附件">
          <el-upload
            :file-list="fileList"
            :auto-upload="false"
            :on-change="(file, fileListArg) => { fileList = fileListArg; createAttachments = fileListArg.map(f => f.raw).filter(f => typeof f === 'object' && f && f.size) }"
            :show-file-list="true"
            :multiple="true"
            :limit="5"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #file="{ file }">
              <span class="upload-file-name" :title="file.name">{{ file.name }}</span>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="saveCreate">保存</el-button>
        <el-button @click="showCreateDialog = false">取消</el-button>
      </template>
    </el-dialog>
    <!-- 会议录音弹窗 -->
    <el-dialog v-model="recordingDialogVisible" title="会议录音" width="80%" class="recording-dialog">
      <MeetingRecorder
        v-if="recordingDialogVisible"
        :meeting-id="currentMeeting?.id"
        :meeting-title="currentMeeting?.title"
        @recording-started="onRecordingStarted"
        @recording-stopped="onRecordingStopped"
        @minutes-generated="onMinutesGenerated"
      />
      <template #footer>
        <el-button @click="recordingDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 会议纪要生成弹窗 -->
    <el-dialog v-model="minutesDialogVisible" title="会议纪要生成" width="520px">
      <el-input
        v-model="minutesContent"
        type="textarea"
        :rows="8"
        placeholder="可手动输入或粘贴AI生成的会议纪要..."
        style="margin-bottom: 12px;"
      />
      <el-button type="primary" @click="generateAIMinutes" style="margin-right: 8px;">AI生成纪要</el-button>
      <template #footer>
        <el-button type="primary" @click="saveMinutes">保存纪要</el-button>
        <el-button @click="minutesDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <!-- 会议提醒区块 -->
    <el-card class="remind-card" style="margin-bottom: 18px;" v-if="remindMeetings.length">
      <div class="remind-title">会议提醒</div>
      <ul>
        <li v-for="m in remindMeetings" :key="m.id">
          <span>{{ m.title }}（时间：{{ m.time }}）</span>
          <el-button size="small" @click="notifyMeeting(m)">通知</el-button>
        </li>
      </ul>
    </el-card>
    <el-button size="small" @click="uploadDialogVisible = true">
      <el-icon><Upload /></el-icon>
      上传附件
    </el-button>
    <el-dialog v-model="uploadDialogVisible" title="上传会议附件" width="400px">
      <el-form>
        <el-form-item label="选择会议">
          <el-select v-model="selectedMeetingId" placeholder="请选择会议" style="width: 100%;">
            <el-option
              v-for="m in allMeetings"
              :key="m.id"
              :label="`${m.title}（${formatTime(m.time)}）`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="上传附件">
    <el-upload
      :action="''"
      :http-request="handleUpload"
      :show-file-list="false"
            :disabled="!selectedMeetingId"
    >
            <el-button size="small">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
    </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-card class="calendar-card" style="margin-bottom: 18px;">
      <el-calendar v-model="calendarDate" @input="onCalendarChange">
        <template #date-cell="{ data }">
          <div :class="{ 'is-today': data.isSelected }">
            {{ data.day.split('-')[2] }}
            <div v-if="meetingsByDate[data.day]">
              <el-tag
                v-for="m in meetingsByDate[data.day]"
                :key="m.id"
                size="small"
                type="success"
                style="margin-top:2px;display:block;"
              >
                {{ m.title }}
              </el-tag>
            </div>
          </div>
        </template>
      </el-calendar>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchMeetings, createMeeting, editMeeting as apiEditMeeting, deleteMeeting as apiDeleteMeeting, uploadAttachment, generateMinutesAI, approveMeetingApi, exportMeetings, notifyMeetingApi, fetchApprovalHistory, checkMeetingConflict, fetchRooms, fetchUsers } from '@/api/meetings'
import dayjs from 'dayjs'
import { eventEmitter, MEETING_EVENTS } from '@/services/taskService'
import { Upload } from '@element-plus/icons-vue'
import api from '@/utils/http'
import MeetingRecorder from '@/components/MeetingRecorder.vue'

const attachments = ref<any[]>([])

// 权限模拟，实际应由后端返回
const userPerms = ref<string[]>(['view', 'edit', 'create', 'delete'])
const canEdit = computed(() => userPerms.value.includes('edit'))
const canCreate = computed(() => userPerms.value.includes('create'))
const canDelete = computed(() => userPerms.value.includes('delete'))
const canApprove = computed(() => userPerms.value.includes('approve'))

// 用户列表
const userList = ref<any[]>([])
const loadUsers = async () => {
  try {
    const res = await fetchUsers()
    userList.value = res.data || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
    userList.value = []
  }
}

// 会议数据（实际应由API获取）
const allMeetings = ref<any[]>([])
const loading = ref(false)
const searchText = ref('')
const selectedStatus = ref('')
const selectedMeetings = ref<any[]>([])
const pageSize = 10
const currentPage = ref(1)
const selectedMeetingId = ref<string | number>('')

// 新增：当前选中日期字符串
const calendarDate = ref(new Date())
const selectedDayStr = computed(() => {
  return calendarDate.value instanceof Date
    ? calendarDate.value.toISOString().slice(0, 10)
    : ''
})

// 修改 filteredMeetings 逻辑，显示所有会议数据
const filteredMeetings = computed(() => {
  let list = allMeetings.value || []
  if (searchText.value.trim()) {
    const kw = searchText.value.trim().toLowerCase()
    list = list.filter(m => m.title.toLowerCase().includes(kw) || m.host.toLowerCase().includes(kw))
  }
  if (selectedStatus.value) {
    list = list.filter(m => m.status === selectedStatus.value)
  }
  return list
})
const totalPages = computed(() => Math.ceil(filteredMeetings.value.length / pageSize))
const pagedMeetings = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredMeetings.value.slice(start, start + pageSize)
})
const handleSelectionChange = (rows: any[]) => {
  selectedMeetings.value = rows
}
const batchDelete = () => {
  allMeetings.value = allMeetings.value.filter((m: any) => !selectedMeetings.value.includes(m))
  ElMessage.success('批量删除成功（模拟）')
}
const batchExport = async () => {
  const ids = selectedMeetings.value.map(m => m.id)
  const res = await exportMeetings(ids)
  const blob = new Blob([res.data], { type: 'application/vnd.ms-excel' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '会议导出.xlsx'
  a.click()
  window.URL.revokeObjectURL(url)
}
const statusText = (status: string) => {
  if (status === 'upcoming') return '待召开'
  if (status === 'finished') return '已结束'
  if (status === 'canceled') return '已取消'
  return status
}
const statusTagType = (status: string) => {
  if (status === 'upcoming') return 'success'
  if (status === 'finished') return 'info'
  if (status === 'canceled') return 'danger'
  return 'info'
}
// 会议详情/编辑
const detailDialogVisible = ref(false)
const detailDialogTitle = ref('会议详情')
const detailForm = ref<any>({})
const editingDetail = ref(false)
const approvalHistory = ref<any[]>([])

const fetchAttachments = async (meetingId: number) => {
  try {
    const res: any = await api.get({ url: `/api/meetings/${meetingId}/attachments` })
    if (Array.isArray(res.data)) {
      attachments.value = res.data
    } else if (Array.isArray(res)) {
      attachments.value = res
    } else {
      attachments.value = []
    }
  } catch (e) {
    attachments.value = []
  }
}

const viewDetail = async (row: any) => {
  detailDialogTitle.value = '会议详情'
  detailForm.value = { 
    ...row,
    participants: row.participants 
      ? (Array.isArray(row.participants) ? row.participants : row.participants.split(',').map((p: string) => p.trim()).filter(Boolean))
      : []
  }
  editingDetail.value = false
  detailDialogVisible.value = true
  await loadApprovalHistory(row.id)
  await fetchAttachments(row.id)
}
const handleEditMeeting = async (row: any) => {
  detailDialogTitle.value = '编辑会议'
  detailForm.value = { ...row }
  editingDetail.value = true
  detailDialogVisible.value = true
  await fetchAttachments(row.id)
}
const saveDetail = async () => {
  await apiEditMeeting(detailForm.value)
  ElMessage.success('保存成功')
  detailDialogVisible.value = false
  loadMeetings()
}
const handleDeleteMeeting = async (row: any) => {
  await apiDeleteMeeting(row.id)
  ElMessage.success('删除成功')
  loadMeetings()
}
// 新建会议
const showCreateDialog = ref(false)
const createForm = ref<any>({
  title: '', host: '', time: '', location: '', participants: [], remark: '', cycle: 'none'
})
let fileList: any[] = []
let createAttachments: any[] = []
const saveCreate = async () => {
  const ok = await checkConflict()
  if (!ok) return
  // 只传递后端需要的字段
  const payload = {
    title: createForm.value.title,
    host: createForm.value.host,
    time: createForm.value.time,
    location: createForm.value.location,
    period: createForm.value.cycle, // cycle 映射为 period
    status: 'upcoming',
    participants: createForm.value.participants || []
  }
  const res = await createMeeting(payload)
  ElMessage.success('新建成功')
  showCreateDialog.value = false
  loadMeetings()
  // 新建会议成功后上传附件
  if (res && res.code === 0 && res.meetingId && createAttachments.length) {
    for (const file of createAttachments) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('meetingId', String(res.meetingId))
      await uploadAttachment(formData)
    }
    ElMessage.success('附件上传成功')
    createAttachments = []
    fileList = []
  }
}
// 会议录音相关
const recordingDialogVisible = ref(false)
const currentMeeting = ref<any>(null)

// 会议纪要生成
const minutesDialogVisible = ref(false)
const minutesContent = ref('')
const currentMinutesMeeting = ref<any>({ attachments: [] })
const showMinutesDialog = (row: any) => {
  currentMinutesMeeting.value = {
    ...(row || {}),
    attachments: Array.isArray(row?.attachments) ? row.attachments : []
  }
  minutesContent.value = row?.minutes || ''
  minutesDialogVisible.value = true
}
const saveMinutes = () => {
  if (currentMinutesMeeting.value) {
    currentMinutesMeeting.value.minutes = minutesContent.value
    currentMinutesMeeting.value.remark = '已生成纪要'
    ElMessage.success('纪要已保存（模拟）')
    minutesDialogVisible.value = false
  }
}
// 会议提醒
const remindMeetings = computed(() => {
  const now = new Date()
  return allMeetings.value.filter((m: any) => m.status === 'upcoming' && new Date(m.time).getTime() - now.getTime() < 48 * 3600 * 1000 && new Date(m.time).getTime() > now.getTime())
})
const notifyMeeting = async (m: any) => {
  await notifyMeetingApi(m.id)
  ElMessage.success('已通知参会人')
}

const loadMeetings = async () => {
  loading.value = true
  try {
    const params = {
      kw: searchText.value,
      status: selectedStatus.value,
      page: currentPage.value,
      pageSize
    }
    console.log('[会议列表] 请求参数:', params)
    const res = await fetchMeetings(params)
    console.log('[会议列表] API响应:', res)
    allMeetings.value = res.data.list || []
    console.log('[会议列表] 设置的数据:', allMeetings.value)
  } catch (error) {
    console.error('[会议列表] 加载会议数据失败:', error)
    allMeetings.value = []
  } finally {
    loading.value = false
  }
}
watch([searchText, selectedStatus, currentPage], loadMeetings)
onMounted(() => {
  loadMeetings()
  loadUsers()
})

const uploadDialogVisible = ref(false)

const handleUpload = async (option: any) => {
  if (!selectedMeetingId.value) {
    ElMessage.warning('请先选择会议')
    return
  }
  const formData = new FormData()
  formData.append('file', option.file as File)
  formData.append('meetingId', String(selectedMeetingId.value))
  await uploadAttachment(formData)
  ElMessage.success('附件上传成功')
  uploadDialogVisible.value = false
  // 可刷新附件列表
}

const generateAIMinutes = async () => {
  if (!currentMinutesMeeting.value) return
  const res = await generateMinutesAI(currentMinutesMeeting.value.id)
  minutesContent.value = res.data.content
  ElMessage.success('AI纪要已生成')
}

const approveMeeting = async (action: 'approve' | 'reject') => {
  await approveMeetingApi(detailForm.value.id, action)
  ElMessage.success(action === 'approve' ? '审批通过' : '已驳回')
  detailDialogVisible.value = false
  loadMeetings()
}

// 附件删除功能
const deleteAttachment = async (file: any) => {
  // 实际应调用API删除附件
  if (currentMinutesMeeting.value && Array.isArray(currentMinutesMeeting.value.attachments)) {
    currentMinutesMeeting.value.attachments = currentMinutesMeeting.value.attachments.filter((f: any) => f.id !== file.id)
    ElMessage.success('附件已删除（模拟）')
  }
}

const loadApprovalHistory = async (id: number) => {
  const res = await fetchApprovalHistory(id)
  approvalHistory.value = res.data
}

const onCalendarChange = (date: Date) => {
  calendarDate.value = date
}

const cycleText = (cycle: string) => {
  if (cycle === 'daily') return '每天'
  if (cycle === 'weekly') return '每周'
  if (cycle === 'monthly') return '每月'
  return '无'
}

const checkConflict = async () => {
  const res = await checkMeetingConflict({
    time: createForm.value.time,
    location: createForm.value.location,
    cycle: createForm.value.cycle
  })
  if (res.data.conflict) {
    ElMessage.error('该时间段会议室已被占用，请更换时间或会议室！')
    return false
  }
  return true
}

const rooms = ref<any[]>([])
const loadRooms = async () => {
  const res = await fetchRooms()
  rooms.value = res.data
}
onMounted(loadRooms)

const meetingsByDate = computed(() => {
  const map: Record<string, any[]> = {}
  allMeetings.value.forEach(m => {
    // 取日期部分（兼容ISO格式）
    const dateStr = m.time ? m.time.slice(0, 10) : ''
    if (dateStr) {
      if (!map[dateStr]) map[dateStr] = []
      map[dateStr].push(m)
    }
  })
  return map
})

const formatTime = (time: string) => {
  if (!time) return ''
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 录音相关函数
const startMeetingRecording = (meeting: any) => {
  currentMeeting.value = meeting
  recordingDialogVisible.value = true
  ElMessage.info('即将开始会议录音')
}

const onRecordingStarted = () => {
  ElMessage.success('会议录音已开始')
  // 可以更新会议状态为"进行中"
  if (currentMeeting.value) {
    updateMeetingStatus(currentMeeting.value.id, 'ongoing')
  }
}

const onRecordingStopped = (recording: any) => {
  ElMessage.success('会议录音已结束')
  console.log('录音文件:', recording)
  // 可以自动生成会议纪要或保存录音文件
}

const onMinutesGenerated = (minutes: string) => {
  ElMessage.success('会议纪要已生成')
  // 可以自动保存纪要到会议记录中
  if (currentMeeting.value) {
    saveMeetingMinutes(currentMeeting.value.id, minutes)
  }
}

const updateMeetingStatus = async (meetingId: number, status: string) => {
  try {
    // 调用API更新会议状态
    // await updateMeetingStatusApi(meetingId, status)
    loadMeetings() // 刷新会议列表
  } catch (error) {
    console.error('更新会议状态失败:', error)
  }
}

const saveMeetingMinutes = async (meetingId: number, minutes: string) => {
  try {
    // 调用API保存会议纪要
    // await saveMeetingMinutesApi(meetingId, minutes)
    ElMessage.success('会议纪要已保存')
  } catch (error) {
    console.error('保存会议纪要失败:', error)
    ElMessage.error('保存会议纪要失败')
  }
}
</script>

<style scoped lang="scss">
.meetings-page {
  padding: 32px;
  max-width: 900px;
  margin: 0 auto;
  .page-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 18px;
  }
  .meetings-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
  }
  .meetings-list-card {
    margin-bottom: 24px;
    min-height: 220px;
  }
  .batch-toolbar {
    margin-bottom: 8px;
  }
  .remind-card {
    margin-bottom: 18px;
    .remind-title {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    ul {
      list-style: none;
      padding: 0;
      li {
        margin-bottom: 8px;
        span {
          margin-right: 12px;
        }
      }
    }
  }
  .calendar-card {
    margin-bottom: 18px;
  }
  .meeting-search-input,
  .meeting-status-select {
    width: 220px;
  }
  .high-input :deep(.el-input__wrapper),
  .high-input :deep(.el-select__wrapper) {
    min-height: 44px !important;
    border-radius: 12px !important;
    font-size: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
  }
  .high-input :deep(.el-input__inner),
  .high-input :deep(.el-select__selected-item) {
    font-size: 16px;
    line-height: 44px;
  }
  .upload-file-name {
    max-width: 220px;
    display: inline-block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
  }
  :deep(.el-upload-list__item-name) {
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
    vertical-align: middle;
  }
}

// 录音弹窗样式
.recording-dialog {
  :deep(.el-dialog) {
    border-radius: 8px;
    overflow: hidden;
  }

  :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
  }

  :deep(.el-dialog__title) {
    color: white;
    font-weight: 600;
  }

  :deep(.el-dialog__body) {
    padding: 20px;
    background: #f5f7fa;
  }

  :deep(.el-dialog__footer) {
    background: #f5f7fa;
    border-top: 1px solid #e4e7ed;
  }
}
</style> 