import request from '@/utils/http'
 
export function globalSearch(keyword: string) {
  return request.get({ url: '/api/search', params: { q: keyword } })
} 