import axios, { InternalAxiosRequestConfig, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import EmojiText from '../emojo'

// 根据环境配置API基础URL
const getBaseURL = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // 开发环境使用代理，生产环境使用绝对路径
  return import.meta.env.DEV ? '/' : 'http://localhost:3007'
}

const axiosInstance = axios.create({
  timeout: 15000, // 请求超时时间(毫秒)
  baseURL: getBaseURL(), // API地址
  withCredentials: true, // 异步请求携带cookie
  validateStatus: (status) => status >= 200 && status < 300, // 只接受 2xx 的状态码
  headers: {
    get: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' },
    post: { 'Content-Type': 'application/json;charset=utf-8' }
  },
  transformResponse: [
    (data, headers) => {
      const contentType = headers['content-type']
      if (contentType && typeof contentType === 'string' && contentType.includes('application/json')) {
        try {
          return JSON.parse(data)
        } catch {
          return data
        }
      }
      return data
    }
  ]
})

// 请求拦截器
axiosInstance.interceptors.request.use(
  (request) => {
    // 这些接口不需要 token
    const noAuthApis = ['/api/send-captcha', '/api/reset-password', '/api/verify-captcha']
    if (!noAuthApis.some(api => request.url?.includes(api))) {
    const token = localStorage.getItem('token')
    if (token) {
      request.headers['Authorization'] = 'Bearer ' + token
      }
    }
    return request
  },
  (error) => {
    ElMessage.error(`服务器异常！ ${EmojiText[500]}`)
    return Promise.reject(error)
  }
)

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (axios.isCancel(error)) {
      console.log('repeated request: ' + error.message)
    } else {
      // 处理401错误（未授权）
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
      
      const errorMessage = error.response?.data.msg
      ElMessage.error(
        errorMessage
          ? `${errorMessage} ${EmojiText[500]}`
          : `请求超时或服务器异常！${EmojiText[500]}`
      )
    }
    return Promise.reject(error)
  }
)

// 请求
async function request<T = any>(config: AxiosRequestConfig): Promise<T> {
  // 对 POST | PUT 请求特殊处理
  if (config.method?.toUpperCase() === 'POST' || config.method?.toUpperCase() === 'PUT') {
    // 如果已经有 data，则保留原有的 data
    if (config.params && !config.data) {
      config.data = config.params
      config.params = undefined // 使用 undefined 而不是空对象
    }
  }
  // 关键修复：如果 data 是 FormData，移除 transformRequest，避免 axios 把 FormData 转成字符串
  if (config.data instanceof FormData) {
    delete config.transformRequest;
    // 关键修复：移除 headers.post[Content-Type]，让 axios 自动设置 multipart/form-data
    if (config.headers && config.headers['Content-Type']) {
      delete config.headers['Content-Type']
    }
    // 兼容全局 axiosInstance 默认 headers
    if (axiosInstance.defaults.headers.post && axiosInstance.defaults.headers.post['Content-Type']) {
      delete axiosInstance.defaults.headers.post['Content-Type']
    }
  }

  try {
    const res = await axiosInstance.request<T>({ ...config })
    return res.data
  } catch (e) {
    if (axios.isAxiosError(e)) {
      // 可以在这里处理 Axios 错误
    }
    return Promise.reject(e)
  }
}

// API 方法集合
const api = {
  get<T>(config: AxiosRequestConfig): Promise<T> {
    return request({ ...config, method: 'GET' }) // GET 请求
  },
  post<T>(config: AxiosRequestConfig): Promise<T> {
    return request({ ...config, method: 'POST' }) // POST 请求
  },
  put<T>(config: AxiosRequestConfig): Promise<T> {
    return request({ ...config, method: 'PUT' }) // PUT 请求
  },
  del<T>(config: AxiosRequestConfig): Promise<T> {
    return request({ ...config, method: 'DELETE' }) // DELETE 请求
  },
  request<T>(config: AxiosRequestConfig): Promise<T> {
    return request({ ...config }) // 通用请求
  }
}

export default api
