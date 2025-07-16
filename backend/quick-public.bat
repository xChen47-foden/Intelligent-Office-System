@echo off
REM 智能办公系统 - 快速公网访问脚本 (Windows版本)
REM 使用内网穿透技术，无需购买服务器即可实现公网访问

echo 🚀 智能办公系统 - 快速公网访问
echo ==================================
echo.

REM 检查依赖
echo 📋 检查系统依赖...

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装，请先安装 Node.js
    pause
    exit /b 1
)
echo ✅ Node.js 已安装

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python 未安装，请先安装 Python
        pause
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)
echo ✅ Python 已安装

REM 检查 npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm 未安装，请先安装 npm
    pause
    exit /b 1
)
echo ✅ npm 已安装

echo.
echo 🛠️ 选择内网穿透方案：
echo 1. ngrok (推荐，免费额度够用)
echo 2. 花生壳 (国内，稳定)
echo 3. 跳过配置，仅启动本地服务
echo.
set /p choice=请选择 [1-3]: 

if "%choice%"=="1" (
    set TUNNEL_METHOD=ngrok
    goto setup_ngrok
)
if "%choice%"=="2" (
    set TUNNEL_METHOD=peanut
    goto setup_peanut
)
if "%choice%"=="3" (
    set TUNNEL_METHOD=none
    goto start_services
)

echo 无效选择，使用默认方案 ngrok
set TUNNEL_METHOD=ngrok

:setup_ngrok
echo 📦 配置 ngrok...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ngrok 未安装，请先安装 ngrok
    echo 1. 访问 https://ngrok.com/download
    echo 2. 下载并安装 ngrok
    echo 3. 配置 PATH 环境变量
    pause
    exit /b 1
)

echo ✅ ngrok 已安装

REM 检查是否配置了 authtoken
ngrok config check >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ 请先配置 ngrok authtoken：
    echo 1. 访问 https://dashboard.ngrok.com/get-started/setup
    echo 2. 注册账号并获取 authtoken
    echo 3. 运行: ngrok authtoken YOUR_TOKEN
    echo.
    pause
)
goto start_services

:setup_peanut
echo 📦 配置花生壳...
echo.
echo ⚠️ 花生壳配置说明：
echo 1. 注册花生壳账号: https://hsk.oray.com
echo 2. 下载并安装花生壳客户端
echo 3. 配置内网穿透规则
echo 4. 手动启动花生壳服务
echo.
echo 📋 花生壳配置参考：
echo 内网地址: 127.0.0.1
echo 内网端口: 3006
echo 应用类型: HTTP
echo.
pause
goto start_services

:start_services
echo 🔧 启动本地服务...

REM 检查是否已安装依赖
if not exist "node_modules" (
    echo 📦 安装 Node.js 依赖...
    npm install
)

REM 安装 Python 依赖
if exist "backend\requirements.txt" (
    echo 📦 安装 Python 依赖...
    %PYTHON_CMD% -m pip install -r backend\requirements.txt
)

REM 启动后端服务
echo 🔧 启动后端服务...
cd backend
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 3007
cd ..

REM 启动前端服务
echo 🌐 启动前端服务...
start /B node server-production.js

REM 等待服务启动
echo 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo 📊 检查服务状态...
curl -s http://localhost:3006 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端服务启动成功 (http://localhost:3006)
) else (
    echo ❌ 前端服务启动失败
)

curl -s http://localhost:3007 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务启动成功 (http://localhost:3007)
) else (
    echo ❌ 后端服务启动失败
)

REM 启动内网穿透
if "%TUNNEL_METHOD%"=="ngrok" (
    echo 🌐 启动 ngrok 内网穿透...
    start ngrok http 3006
    timeout /t 3 /nobreak >nul
    
    echo.
    echo 🎉 ngrok 已启动！
    echo ==================================
    echo 请查看 ngrok 控制台获取公网地址
    echo ngrok 控制台: http://localhost:4040
    echo ==================================
) else if "%TUNNEL_METHOD%"=="peanut" (
    echo 🌐 花生壳需要手动配置...
    echo 请在花生壳客户端中配置内网穿透规则
) else (
    echo 🏠 仅本地访问模式
    echo ==================================
    echo 本地地址: http://localhost:3006
    echo ==================================
)

echo.
echo 📊 服务状态
echo ==================================
echo 前端服务: http://localhost:3006
echo 后端服务: http://localhost:3007
if "%TUNNEL_METHOD%"=="ngrok" (
    echo ngrok 控制台: http://localhost:4040
)
echo.
echo 📋 管理命令:
echo   查看进程: tasklist | findstr /i "node python uvicorn"
echo   重启服务: 重新运行此脚本
echo.
echo 🛑 按任意键停止所有服务
echo ==================================

pause

REM 清理进程
echo 🛑 正在停止服务...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo ✅ 所有服务已停止
pause 