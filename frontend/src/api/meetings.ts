// 会议相关API接口
import api from '@/utils/http'

// 获取会议列表
export function fetchMeetings(params: any): Promise<any> {
  return api.get({ url: '/api/meetings/list', params })
}
// 创建会议
export function createMeeting(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/create', data })
}
// 编辑会议
export function editMeeting(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/edit', data })
}
// 删除会议
export function deleteMeeting(id: number): Promise<any> {
  return api.post({ url: '/api/meetings/delete', data: { id } })
}
// 上传会议附件
export function uploadAttachment(formData: FormData): Promise<any> {
  return api.post({ url: '/api/meetings/upload', data: formData })
}
// AI生成会议纪要
export function generateMinutesAI(meetingId: number): Promise<any> {
  return api.get({ url: '/api/meetings/ai-minutes', params: { meetingId } })
}
// 审批会议
export function approveMeetingApi(id: number, action: string): Promise<any> {
  return api.post({ url: '/api/meetings/approve', data: { id, action } })
}
// 导出会议
export function exportMeetings(ids: number[]): Promise<any> {
  return api.post({ url: '/api/meetings/export', data: { ids }, responseType: 'blob' })
}
// 通知会议
export function notifyMeetingApi(id: number): Promise<any> {
  return api.post({ url: '/api/meetings/notify', data: { id } })
}
// 获取审批历史
export function fetchApprovalHistory(id: number): Promise<any> {
  return api.get({ url: '/api/meetings/approval-history', params: { id } })
}
// 检查会议冲突
export function checkMeetingConflict(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/check-conflict', data })
}
// 获取会议室列表
export function fetchRooms(): Promise<any> {
  return api.get({ url: '/api/meetings/rooms' })
} 

// 获取用户列表
export function fetchUsers(): Promise<any> {
  return api.get({ url: '/api/users/list' })
} 