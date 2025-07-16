#!/bin/bash
# 智能办公系统 - 龙芯架构一键部署脚本
# 适用于统信UOS、银河麒麟等龙芯系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统架构
check_architecture() {
    print_info "检查系统架构..."
    ARCH=$(uname -m)
    if [[ "$ARCH" != "loongarch64" && "$ARCH" != "mips64el" ]]; then
        print_error "不支持的架构: $ARCH"
        print_error "此脚本仅支持龙芯架构 (loongarch64 或 mips64el)"
        exit 1
    fi
    print_success "检测到龙芯架构: $ARCH"
}

# 检查操作系统
check_os() {
    print_info "检查操作系统..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        print_success "操作系统: $OS $VER"
    else
        print_error "无法检测操作系统版本"
        exit 1
    fi
}

# 更新系统包
update_system() {
    print_info "更新系统软件包..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        PKG_MANAGER="apt-get"
    elif command -v yum &> /dev/null; then
        sudo yum update -y
        PKG_MANAGER="yum"
    else
        print_error "不支持的包管理器"
        exit 1
    fi
    print_success "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    print_info "安装基础依赖..."
    
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo apt-get install -y \
            build-essential \
            curl \
            wget \
            git \
            gcc \
            g++ \
            make \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            libffi-dev \
            libssl-dev \
            redis-server \
            nginx \
            sqlite3 \
            libsqlite3-dev
    else
        sudo yum install -y \
            gcc \
            gcc-c++ \
            make \
            curl \
            wget \
            git \
            python3 \
            python3-pip \
            python3-devel \
            libffi-devel \
            openssl-devel \
            redis \
            nginx \
            sqlite \
            sqlite-devel
    fi
    
    print_success "基础依赖安装完成"
}

# 安装Node.js
install_nodejs() {
    print_info "安装Node.js..."
    
    # 检查是否已安装
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        print_warning "Node.js 已安装: $NODE_VER"
        read -p "是否重新安装? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # 根据架构选择安装方式
    if [ "$ARCH" = "loongarch64" ]; then
        print_info "为 loongarch64 架构编译 Node.js..."
        
        cd /tmp
        wget https://nodejs.org/dist/v18.18.0/node-v18.18.0.tar.gz
        tar -xzf node-v18.18.0.tar.gz
        cd node-v18.18.0
        
        ./configure --prefix=/usr/local
        make -j$(nproc)
        sudo make install
        
    elif [ "$ARCH" = "mips64el" ]; then
        print_info "为 mips64el 架构编译 Node.js..."
        
        cd /tmp
        wget https://nodejs.org/dist/v18.18.0/node-v18.18.0.tar.gz
        tar -xzf node-v18.18.0.tar.gz
        cd node-v18.18.0
        
        ./configure --prefix=/usr/local --with-mips-arch-variant=loongson3a
        make -j$(nproc)
        sudo make install
    fi
    
    # 验证安装
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        NPM_VER=$(npm --version)
        print_success "Node.js 安装成功: $NODE_VER"
        print_success "npm 版本: $NPM_VER"
    else
        print_error "Node.js 安装失败"
        exit 1
    fi
}

# 配置项目
setup_project() {
    print_info "配置项目..."
    
    # 获取当前目录
    PROJECT_DIR=$(pwd)
    print_info "项目目录: $PROJECT_DIR"
    
    # 创建虚拟环境
    print_info "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 配置pip国内源
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 安装Python依赖
    print_info "安装Python依赖..."
    cd backend/fastapi_app
    pip install -r requirements.txt
    pip install python-multipart sqlalchemy aiosqlite bcrypt pyjwt redis uvicorn
    cd ../..
    
    # 配置npm国内源
    npm config set registry https://registry.npmmirror.com
    
    # 安装前端依赖
    print_info "安装前端依赖..."
    npm install
    
    # 安装Node.js服务依赖
    cd backend/node_service
    npm install
    cd ../..
    
    print_success "项目配置完成"
}

# 构建前端
build_frontend() {
    print_info "构建前端项目..."
    npm run build
    
    if [ -d "dist" ]; then
        print_success "前端构建成功"
    else
        print_error "前端构建失败"
        exit 1
    fi
}

# 配置数据库
setup_database() {
    print_info "配置数据库..."
    
    # 启动Redis
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
    else
        sudo systemctl enable redis
        sudo systemctl start redis
    fi
    
    # 检查Redis
    if redis-cli ping &> /dev/null; then
        print_success "Redis 启动成功"
    else
        print_error "Redis 启动失败"
    fi
    
    # 创建数据库目录
    mkdir -p backend/db
    
    # 初始化SQLite数据库
    cd backend
    sqlite3 users.db ".databases" 2>/dev/null || true
    sqlite3 meetings.db ".databases" 2>/dev/null || true
    cd ..
    
    print_success "数据库配置完成"
}

# 配置Nginx
setup_nginx() {
    print_info "配置Nginx..."
    
    PROJECT_DIR=$(pwd)
    
    # 创建Nginx配置
    sudo tee /etc/nginx/sites-available/smart-office > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    root $PROJECT_DIR/dist;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /auth/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
    }
    
    location /uploads/ {
        alias $PROJECT_DIR/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 100M;
}
EOF

    # 创建软链接（如果sites-enabled目录存在）
    if [ -d "/etc/nginx/sites-enabled" ]; then
        sudo ln -sf /etc/nginx/sites-available/smart-office /etc/nginx/sites-enabled/
    else
        # 对于某些系统，可能需要直接编辑nginx.conf
        print_warning "sites-enabled 目录不存在，请手动配置Nginx"
    fi
    
    # 测试Nginx配置
    if sudo nginx -t; then
        sudo systemctl restart nginx
        print_success "Nginx 配置成功"
    else
        print_error "Nginx 配置错误"
    fi
}

# 创建系统服务
create_services() {
    print_info "创建系统服务..."
    
    PROJECT_DIR=$(pwd)
    USER=$(whoami)
    
    # 创建FastAPI服务
    sudo tee /etc/systemd/system/smart-office-backend.service > /dev/null <<EOF
[Unit]
Description=Smart Office Backend Service
After=network.target redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR/backend/fastapi_app
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重载并启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable smart-office-backend
    sudo systemctl start smart-office-backend
    
    sleep 3
    
    # 检查服务状态
    if sudo systemctl is-active --quiet smart-office-backend; then
        print_success "后端服务启动成功"
    else
        print_error "后端服务启动失败"
        sudo journalctl -u smart-office-backend -n 50
    fi
}

# 显示部署信息
show_info() {
    echo
    echo "=========================================="
    echo -e "${GREEN}部署完成！${NC}"
    echo "=========================================="
    echo
    echo -e "${BLUE}访问地址:${NC} http://$(hostname -I | awk '{print $1}')"
    echo -e "${BLUE}API地址:${NC} http://$(hostname -I | awk '{print $1}'):3007"
    echo
    echo -e "${YELLOW}服务管理命令:${NC}"
    echo "  查看后端状态: sudo systemctl status smart-office-backend"
    echo "  重启后端服务: sudo systemctl restart smart-office-backend"
    echo "  查看后端日志: sudo journalctl -u smart-office-backend -f"
    echo
    echo -e "${YELLOW}默认账号信息:${NC}"
    echo "  请使用邮箱注册新账号"
    echo
    echo "=========================================="
}

# 主函数
main() {
    echo "=========================================="
    echo "智能办公系统 - 龙芯架构一键部署"
    echo "=========================================="
    echo
    
    # 检查是否以root运行
    if [ "$EUID" -eq 0 ]; then 
        print_error "请不要使用root用户运行此脚本"
        exit 1
    fi
    
    # 执行部署步骤
    check_architecture
    check_os
    update_system
    install_dependencies
    install_nodejs
    setup_project
    build_frontend
    setup_database
    setup_nginx
    create_services
    show_info
}

# 运行主函数
main 