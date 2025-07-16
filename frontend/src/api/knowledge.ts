import api from '@/utils/http'

export function fetchKnowledgeList() {
  return api.get({ url: '/api/knowledge' })
}

export function searchKnowledgeDocs(kw: string) {
  return api.get({ url: '/api/knowledge/search', params: { kw } })
}

export function uploadKnowledgeDoc(formData: FormData) {
  return api.post({ url: '/api/knowledge/upload', data: formData })
}

export function fetchDocDetail(id: number) {
  return api.get({ url: '/api/knowledge/detail', params: { id } })
}

export function editKnowledgeDoc(data: { id: number, content: string }) {
  return api.post({ url: '/api/knowledge/edit', data })
} 