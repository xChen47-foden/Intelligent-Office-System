@echo off
echo 🚀 启动智能办公系统...

REM 检查 node_modules
if not exist "node_modules" (
  echo 📦 安装依赖...
  npm install
)

REM 启动后端服务
echo 🔧 启动后端服务...
cd backend
start /B python -m uvicorn main:app --host 0.0.0.0 --port 3007 --reload
cd ..

REM 启动前端服务
echo 🌐 启动前端服务...
start /B node server-production.js

echo ✅ 系统启动完成！
echo 📱 本地访问: http://localhost:3006
echo 🌍 网络访问: http://zngb47:3006
echo 🛑 按任意键停止服务
pause
