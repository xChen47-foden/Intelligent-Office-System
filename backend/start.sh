#!/bin/bash
echo "🚀 启动智能办公系统..."

# 检查 node_modules
if [ ! -d "node_modules" ]; then
  echo "📦 安装依赖..."
  npm install
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 3007 --reload &
BACKEND_PID=$!
cd ..

# 启动前端服务
echo "🌐 启动前端服务..."
node server-production.js &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo "📱 本地访问: http://localhost:3006"
echo "🌍 网络访问: http://zngb47:3006"
echo "🛑 按 Ctrl+C 停止服务"

# 捕获停止信号
trap 'echo "🛑 停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' SIGINT SIGTERM

# 等待进程结束
wait
