#!/bin/bash

# 智能办公系统 - 快速公网访问脚本
# 使用内网穿透技术，无需购买服务器即可实现公网访问

echo "🚀 智能办公系统 - 快速公网访问"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统
check_system() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="mac"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    log_info "检测到操作系统: $OS"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        log_error "Python 未安装，请先安装 Python"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 选择内网穿透方案
select_tunnel_method() {
    echo ""
    echo "请选择内网穿透方案："
    echo "1. ngrok (推荐，免费额度够用)"
    echo "2. Cloudflare Tunnel (免费，需要域名)"
    echo "3. 花生壳 (国内，稳定)"
    echo "4. 跳过配置，仅启动本地服务"
    echo ""
    read -p "请选择 [1-4]: " choice
    
    case $choice in
        1)
            setup_ngrok
            ;;
        2)
            setup_cloudflare_tunnel
            ;;
        3)
            setup_peanut_shell
            ;;
        4)
            log_info "跳过内网穿透配置"
            ;;
        *)
            log_error "无效选择，使用默认方案 ngrok"
            setup_ngrok
            ;;
    esac
}

# 配置 ngrok
setup_ngrok() {
    log_info "配置 ngrok..."
    
    # 检查是否已安装 ngrok
    if ! command -v ngrok &> /dev/null; then
        log_info "正在安装 ngrok..."
        
        if [ "$OS" = "linux" ]; then
            curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
            echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
            sudo apt update && sudo apt install ngrok
        elif [ "$OS" = "mac" ]; then
            if command -v brew &> /dev/null; then
                brew install ngrok/ngrok/ngrok
            else
                log_error "请先安装 Homebrew 或手动安装 ngrok"
                exit 1
            fi
        else
            log_error "请手动下载 ngrok: https://ngrok.com/download"
            exit 1
        fi
    fi
    
    # 检查是否配置了 authtoken
    if ! ngrok config check &> /dev/null; then
        echo ""
        log_warn "请先配置 ngrok authtoken："
        echo "1. 访问 https://dashboard.ngrok.com/get-started/setup"
        echo "2. 注册账号并获取 authtoken"
        echo "3. 运行: ngrok authtoken YOUR_TOKEN"
        echo ""
        read -p "按回车键继续，或 Ctrl+C 退出..."
    fi
    
    TUNNEL_METHOD="ngrok"
}

# 配置 Cloudflare Tunnel
setup_cloudflare_tunnel() {
    log_info "配置 Cloudflare Tunnel..."
    
    if ! command -v cloudflared &> /dev/null; then
        log_info "正在安装 cloudflared..."
        
        if [ "$OS" = "linux" ]; then
            curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared.deb
            rm cloudflared.deb
        elif [ "$OS" = "mac" ]; then
            if command -v brew &> /dev/null; then
                brew install cloudflared
            else
                log_error "请先安装 Homebrew 或手动安装 cloudflared"
                exit 1
            fi
        else
            log_error "请手动下载 cloudflared: https://github.com/cloudflare/cloudflared/releases"
            exit 1
        fi
    fi
    
    echo ""
    log_warn "Cloudflare Tunnel 需要域名，请确保："
    echo "1. 拥有一个域名"
    echo "2. 域名DNS托管在 Cloudflare"
    echo "3. 已登录 Cloudflare 账号"
    echo ""
    read -p "按回车键继续，或 Ctrl+C 退出..."
    
    TUNNEL_METHOD="cloudflare"
}

# 配置花生壳
setup_peanut_shell() {
    log_info "配置花生壳..."
    
    echo ""
    log_warn "花生壳配置说明："
    echo "1. 注册花生壳账号: https://hsk.oray.com"
    echo "2. 下载并安装花生壳客户端"
    echo "3. 配置内网穿透规则"
    echo "4. 手动启动花生壳服务"
    echo ""
    log_info "本脚本将启动本地服务，请手动配置花生壳"
    
    TUNNEL_METHOD="peanut"
}

# 启动本地服务
start_local_services() {
    log_info "启动本地服务..."
    
    # 检查是否已安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装 Node.js 依赖..."
        npm install
    fi
    
    # 检查 Python 依赖
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "未找到 backend/requirements.txt 文件"
        exit 1
    fi
    
    # 安装 Python 依赖
    log_info "安装 Python 依赖..."
    if command -v python3 &> /dev/null; then
        python3 -m pip install -r backend/requirements.txt
    else
        python -m pip install -r backend/requirements.txt
    fi
    
    # 启动后端服务
    log_info "启动后端服务..."
    cd backend
    if command -v python3 &> /dev/null; then
        python3 -m uvicorn main:app --host 0.0.0.0 --port 3007 &
    else
        python -m uvicorn main:app --host 0.0.0.0 --port 3007 &
    fi
    BACKEND_PID=$!
    cd ..
    
    # 启动前端服务
    log_info "启动前端服务..."
    node server-production.js &
    FRONTEND_PID=$!
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否正常启动
    if curl -s http://localhost:3006 > /dev/null 2>&1; then
        log_info "✅ 前端服务启动成功 (http://localhost:3006)"
    else
        log_error "❌ 前端服务启动失败"
    fi
    
    if curl -s http://localhost:3007 > /dev/null 2>&1; then
        log_info "✅ 后端服务启动成功 (http://localhost:3007)"
    else
        log_error "❌ 后端服务启动失败"
    fi
}

# 启动内网穿透
start_tunnel() {
    if [ "$TUNNEL_METHOD" = "ngrok" ]; then
        log_info "启动 ngrok 内网穿透..."
        echo ""
        log_info "🌐 正在创建公网访问链接..."
        
        # 启动 ngrok
        ngrok http 3006 &
        NGROK_PID=$!
        
        # 等待 ngrok 启动
        sleep 3
        
        # 获取公网地址
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'tunnels' in data and len(data['tunnels']) > 0:
        print(data['tunnels'][0]['public_url'])
except:
    pass
")
        
        if [ ! -z "$PUBLIC_URL" ]; then
            echo ""
            echo "🎉 公网访问地址已生成！"
            echo "=================================="
            echo -e "${GREEN}公网地址: $PUBLIC_URL${NC}"
            echo "ngrok 控制台: http://localhost:4040"
            echo "=================================="
        else
            log_warn "无法获取公网地址，请检查 ngrok 配置"
            log_info "请手动访问 http://localhost:4040 查看地址"
        fi
        
    elif [ "$TUNNEL_METHOD" = "cloudflare" ]; then
        log_info "启动 Cloudflare Tunnel..."
        echo ""
        read -p "请输入您的域名 (如: example.com): " domain
        
        if [ -z "$domain" ]; then
            log_error "域名不能为空"
            exit 1
        fi
        
        cloudflared tunnel --url http://localhost:3006 --hostname $domain &
        CLOUDFLARE_PID=$!
        
        echo ""
        echo "🎉 Cloudflare Tunnel 已启动！"
        echo "=================================="
        echo -e "${GREEN}公网地址: https://$domain${NC}"
        echo "=================================="
        
    elif [ "$TUNNEL_METHOD" = "peanut" ]; then
        log_info "花生壳需要手动配置"
        echo ""
        echo "📋 花生壳配置参考："
        echo "内网地址: 127.0.0.1"
        echo "内网端口: 3006"
        echo "应用类型: HTTP"
        echo ""
        
    else
        log_info "仅本地访问模式"
        echo ""
        echo "🏠 本地访问地址："
        echo "=================================="
        echo -e "${GREEN}本地地址: http://localhost:3006${NC}"
        echo "=================================="
    fi
}

# 显示服务状态
show_status() {
    echo ""
    log_info "📊 服务状态"
    echo "=================================="
    echo "前端服务: http://localhost:3006"
    echo "后端服务: http://localhost:3007"
    
    if [ "$TUNNEL_METHOD" = "ngrok" ]; then
        echo "ngrok 控制台: http://localhost:4040"
    fi
    
    echo ""
    echo "📋 管理命令:"
    echo "  查看进程: ps aux | grep -E '(node|python|uvicorn|ngrok)'"
    echo "  停止服务: kill \$FRONTEND_PID \$BACKEND_PID"
    echo "  重启服务: ./quick-public.sh"
    echo ""
    echo "🛑 按 Ctrl+C 停止所有服务"
    echo "=================================="
}

# 清理函数
cleanup() {
    echo ""
    log_info "正在停止服务..."
    
    # 停止后端服务
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        log_info "后端服务已停止"
    fi
    
    # 停止前端服务
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        log_info "前端服务已停止"
    fi
    
    # 停止 ngrok
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null
        log_info "ngrok 已停止"
    fi
    
    # 停止 Cloudflare Tunnel
    if [ ! -z "$CLOUDFLARE_PID" ]; then
        kill $CLOUDFLARE_PID 2>/dev/null
        log_info "Cloudflare Tunnel 已停止"
    fi
    
    log_info "所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    echo "🚀 正在启动智能办公系统公网访问..."
    echo ""
    
    check_system
    check_dependencies
    select_tunnel_method
    start_local_services
    start_tunnel
    show_status
    
    # 保持脚本运行
    while true; do
        sleep 1
    done
}

# 运行主函数
main "$@" 