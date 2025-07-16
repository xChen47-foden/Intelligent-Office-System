
import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3006

// 配置静态文件服务
app.use(express.static(path.join(__dirname, 'dist')))

// 配置 API 代理
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:3007',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api'
  }
}))

// 配置文件上传代理
app.use('/uploads', createProxyMiddleware({
  target: 'http://localhost:3007',
  changeOrigin: true
}))

// 配置认证代理
app.use('/auth', createProxyMiddleware({
  target: 'http://localhost:3007',
  changeOrigin: true
}))

// 处理 SPA 路由
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'))
})

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 智能办公系统已启动！`)
  console.log(`📱 本地访问: http://localhost:${PORT}`)
  console.log(`🌍 网络访问: http://zngb47:${PORT}`)
  console.log(`📚 确保后端API服务器在端口 3007 上运行`)
})
