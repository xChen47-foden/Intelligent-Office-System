import api from '@/utils/http'

export interface UnreadCounts {
  personal: number
  group: number
}

export function getUnreadCounts(): Promise<UnreadCounts> {
  return api.get({ url: '/api/message/unread_counts' })
}

export function getGroupUnreadCounts(): Promise<UnreadCounts> {
  return api.get({ url: '/api/group/unread_counts' })
} 