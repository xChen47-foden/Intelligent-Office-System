#!/usr/bin/env node

import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 部署配置
const config = {
  buildDir: 'dist',
  serverPort: 3006,
  apiPort: 3007
}

console.log('🚀 开始部署智能办公系统...')

// 1. 清理旧的构建文件
console.log('📦 清理旧的构建文件...')
if (fs.existsSync(config.buildDir)) {
  fs.rmSync(config.buildDir, { recursive: true, force: true })
}

// 2. 构建项目
console.log('🔨 构建项目...')
try {
  execSync('npm run build', { stdio: 'inherit' })
  console.log('✅ 构建完成!')
} catch (error) {
  console.error('❌ 构建失败:', error.message)
  process.exit(1)
}

// 3. 创建静态服务器配置
console.log('⚙️  创建服务器配置...')
const serverConfig = `
import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || ${config.serverPort}

// 配置静态文件服务
app.use(express.static(path.join(__dirname, '${config.buildDir}')))

// 配置 API 代理
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:${config.apiPort}',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api'
  }
}))

// 配置文件上传代理
app.use('/uploads', createProxyMiddleware({
  target: 'http://localhost:${config.apiPort}',
  changeOrigin: true
}))

// 配置认证代理
app.use('/auth', createProxyMiddleware({
  target: 'http://localhost:${config.apiPort}',
  changeOrigin: true
}))

// 处理 SPA 路由
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '${config.buildDir}', 'index.html'))
})

app.listen(PORT, '0.0.0.0', () => {
  console.log(\`🌐 智能办公系统已启动！\`)
  console.log(\`📱 本地访问: http://localhost:\${PORT}\`)
  console.log(\`🌍 网络访问: http://zngb47:\${PORT}\`)
  console.log(\`📚 确保后端API服务器在端口 ${config.apiPort} 上运行\`)
})
`

fs.writeFileSync(path.join(__dirname, 'server-production.js'), serverConfig)

// 4. 创建启动脚本
console.log('📝 创建启动脚本...')
const startScript = `#!/bin/bash
echo "🚀 启动智能办公系统..."

# 检查 node_modules
if [ ! -d "node_modules" ]; then
  echo "📦 安装依赖..."
  npm install
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port ${config.apiPort} --reload &
BACKEND_PID=$!
cd ..

# 启动前端服务
echo "🌐 启动前端服务..."
node server-production.js &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo "📱 访问地址: http://localhost:${config.serverPort}"
echo "🛑 按 Ctrl+C 停止服务"

# 捕获停止信号
trap 'echo "🛑 停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' SIGINT SIGTERM

# 等待进程结束
wait
`

fs.writeFileSync(path.join(__dirname, 'start.sh'), startScript)

// 5. 创建 Windows 启动脚本
const startBat = `@echo off
echo 🚀 启动智能办公系统...

REM 检查 node_modules
if not exist "node_modules" (
  echo 📦 安装依赖...
  npm install
)

REM 启动后端服务
echo 🔧 启动后端服务...
cd backend
start /B python -m uvicorn main:app --host 0.0.0.0 --port ${config.apiPort} --reload
cd ..

REM 启动前端服务
echo 🌐 启动前端服务...
start /B node server-production.js

echo ✅ 系统启动完成！
echo 📱 访问地址: http://localhost:${config.serverPort}
echo 🛑 按任意键停止服务
pause
`

fs.writeFileSync(path.join(__dirname, 'start.bat'), startBat)

// 6. 更新 package.json 脚本
console.log('📋 更新 package.json 脚本...')
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'))
packageJson.scripts = {
  ...packageJson.scripts,
  "deploy": "node deploy.js",
  "start:prod": "node server-production.js",
  "start:full": "concurrently \"cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 3007 --reload\" \"npm run start:prod\"",
  "build:web": "vite build",
  "preview:web": "vite preview --host 0.0.0.0"
}

fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2))

console.log('✅ 部署配置完成!')
console.log('')
console.log('🎉 现在你可以使用以下命令启动系统:')
console.log('')
console.log('  Windows:')
console.log('    start.bat')
console.log('')
console.log('  Linux/Mac:')
console.log('    chmod +x start.sh')
console.log('    ./start.sh')
console.log('')
console.log('  或者手动启动:')
console.log('    npm run start:full')
console.log('')
console.log('📍 系统将在以下地址可用:')
console.log(`  - 本地: http://localhost:${config.serverPort}`)
console.log(`  - 网络: http://zngb47:${config.serverPort}`)
console.log('')
console.log('🔧 确保后端 FastAPI 服务器在端口 3007 上运行') 