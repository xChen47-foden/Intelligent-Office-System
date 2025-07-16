import request from '@/utils/request'

export function fetchContracts(params: any) {
  return request.get('/api/contracts/list', { params })
}
export function exportContracts(ids: number[]) {
  return request.post('/api/contracts/export', { ids }, { responseType: 'blob' })
}
export function fetchRemindContracts() {
  return request.get('/api/contracts/remind')
}
export function uploadContract(formData: FormData) {
  return request.post('/api/contracts/upload', formData)
}
export function archiveContract(id: number) {
  return request.post('/api/contracts/archive', { id })
}
export function approveContract(id: number, action: string) {
  return request.post('/api/contracts/approve', { id, action })
}
// 其他API如 createContract、editContract、archiveContract、uploadContract、approveContract 可按需补充 