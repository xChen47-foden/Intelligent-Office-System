import api from '@/utils/http'

export function fetchMeetings(params: any): Promise<any> {
  return api.get({ url: '/api/meetings/list', params })
}
export function createMeeting(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/create', data })
}
export function editMeeting(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/edit', data })
}
export function deleteMeeting(id: number): Promise<any> {
  return api.post({ url: '/api/meetings/delete', data: { id } })
}
export function uploadAttachment(formData: FormData): Promise<any> {
  return api.post({ url: '/api/meetings/upload', data: formData })
}
export function generateMinutesAI(meetingId: number): Promise<any> {
  return api.get({ url: '/api/meetings/ai-minutes', params: { meetingId } })
}
export function approveMeetingApi(id: number, action: string): Promise<any> {
  return api.post({ url: '/api/meetings/approve', data: { id, action } })
}
export function exportMeetings(ids: number[]): Promise<any> {
  return api.post({ url: '/api/meetings/export', data: { ids }, responseType: 'blob' })
}
export function notifyMeetingApi(id: number): Promise<any> {
  return api.post({ url: '/api/meetings/notify', data: { id } })
}
export function fetchApprovalHistory(id: number): Promise<any> {
  return api.get({ url: '/api/meetings/approval-history', params: { id } })
}
export function checkMeetingConflict(data: any): Promise<any> {
  return api.post({ url: '/api/meetings/check-conflict', data })
}
export function fetchRooms(): Promise<any> {
  return api.get({ url: '/api/meetings/rooms' })
} 

export function fetchUsers(): Promise<any> {
  return api.get({ url: '/api/users/list' })
} 