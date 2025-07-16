import axios from 'axios'

const service = axios.create({
  baseURL: '/',
  timeout: 10000
})

service.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

const request = {
  get: (url: string, config?: any) => service.get(url, config),
  post: (url: string, data?: any, config?: any) => service.post(url, data, config)
}

export default request 