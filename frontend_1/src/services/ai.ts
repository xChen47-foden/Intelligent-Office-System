import api from '@/utils/http'

export async function aiAutoSendToAll(content: string) {
    const res: { code: number; data: any[] } = await api.get({ url: '/api/contact/list' })
    if (res.code !== 0) return false
    for (const person of res.data) {
      await api.post({ url: '/api/message/send', data: { to_user_id: person.id, content } })
    }
    return true
}