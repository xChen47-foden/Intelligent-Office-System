#!/bin/bash

# 智能办公系统 - OpenCloudOS 自动化部署脚本
# 请使用 root 权限或 sudo 运行此脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要 root 权限运行"
        echo "请使用 sudo ./deploy-opencloudos.sh"
        exit 1
    fi
}

# 获取实际用户（即使使用 sudo）
get_real_user() {
    if [ -n "$SUDO_USER" ]; then
        echo "$SUDO_USER"
    else
        echo "$USER"
    fi
}

REAL_USER=$(get_real_user)
INSTALL_DIR="/opt/smartoffice"

print_info "开始部署智能办公系统..."
print_info "安装目录: $INSTALL_DIR"
print_info "执行用户: $REAL_USER"

# 第一步：系统准备
install_system_deps() {
    print_info "更新系统包..."
    dnf update -y

    print_info "安装基础依赖..."
    dnf install -y epel-release
    dnf install -y \
        wget \
        curl \
        git \
        gcc \
        gcc-c++ \
        make \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel \
        xz-devel \
        sqlite-devel \
        readline-devel \
        tk-devel

    print_info "设置系统时区..."
    timedatectl set-timezone Asia/Shanghai
}

# 第二步：安装 Python
install_python() {
    print_info "安装 Python 3.9..."
    dnf install -y python39 python39-devel python39-pip

    # 配置 alternatives
    alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
    alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.9 1

    # 验证安装
    python3 --version
    pip3 --version

    # 升级 pip
    pip3 install --upgrade pip
}

# 第三步：安装 Node.js
install_nodejs() {
    print_info "安装 Node.js 18..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    dnf install -y nodejs

    # 验证安装
    node --version
    npm --version

    # 配置 npm 镜像
    npm config set registry https://registry.npmmirror.com
}

# 第四步：安装 Redis
install_redis() {
    print_info "安装 Redis..."
    dnf install -y redis

    # 启动并设置开机自启
    systemctl enable redis
    systemctl start redis

    # 验证 Redis
    if redis-cli ping | grep -q PONG; then
        print_info "Redis 安装成功"
    else
        print_error "Redis 安装失败"
        exit 1
    fi
}

# 第五步：安装 Nginx
install_nginx() {
    print_info "安装 Nginx..."
    dnf install -y nginx

    # 启动并设置开机自启
    systemctl enable nginx
    systemctl start nginx
}

# 第六步：创建项目目录
setup_project_dir() {
    print_info "创建项目目录..."
    mkdir -p $INSTALL_DIR
    chown $REAL_USER:$REAL_USER $INSTALL_DIR
}

# 第七步：部署项目代码
deploy_code() {
    print_info "部署项目代码..."
    
    # 检查当前目录是否为项目目录
    if [ -f "package.json" ] && [ -d "backend" ]; then
        print_info "检测到项目文件，开始复制..."
        cp -r . $INSTALL_DIR/
        chown -R $REAL_USER:$REAL_USER $INSTALL_DIR
    else
        print_error "当前目录不是项目根目录"
        print_info "请在项目根目录运行此脚本，或手动将项目文件复制到 $INSTALL_DIR"
        exit 1
    fi
}

# 第八步：安装 Python 依赖
install_python_deps() {
    print_info "安装 Python 依赖..."
    
    cd $INSTALL_DIR
    
    # 创建虚拟环境
    sudo -u $REAL_USER python3 -m venv venv
    
    # 创建完整的 requirements.txt
    cat > backend/fastapi_app/requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-docx==1.1.0
python-pptx==0.6.23
aiofiles==23.2.1
sqlalchemy==2.0.23
aiosqlite==0.19.0
bcrypt==4.1.1
pyjwt==2.8.0
redis==5.0.1
httpx==0.25.2
python-jose[cryptography]==3.3.0
alembic==1.13.0
email-validator==2.1.0
python-dotenv==1.0.0
starlette==0.27.0
websockets==12.0
mammoth==1.6.0
officeparser==1.3.0
openpyxl==3.1.2
EOF

    # 安装依赖
    sudo -u $REAL_USER $INSTALL_DIR/venv/bin/pip install -r backend/fastapi_app/requirements.txt
}

# 第九步：安装前端依赖
install_frontend_deps() {
    print_info "安装前端依赖..."
    cd $INSTALL_DIR
    sudo -u $REAL_USER npm install
}

# 第十步：构建前端
build_frontend() {
    print_info "构建前端项目..."
    cd $INSTALL_DIR
    sudo -u $REAL_USER npm run build
}

# 第十一步：初始化数据库
init_database() {
    print_info "初始化数据库..."
    cd $INSTALL_DIR/backend
    
    # 创建数据库文件
    sudo -u $REAL_USER touch users.db meetings.db chat-db.json
    
    # 初始化 chat-db.json
    echo '{"messages": {}, "groups": {}}' | sudo -u $REAL_USER tee chat-db.json > /dev/null
    
    # 创建上传目录
    sudo -u $REAL_USER mkdir -p uploads/{avatar,images,meetings,assistant}
    
    # 设置权限
    chmod -R 755 uploads/
}

# 第十二步：配置 Nginx
configure_nginx() {
    print_info "配置 Nginx..."
    
    # 创建 Nginx 配置文件
    cat > /etc/nginx/conf.d/smartoffice.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    root /opt/smartoffice/dist;
    index index.html;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # 认证路由
    location /auth/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    
    # 文件上传目录
    location /uploads/ {
        alias /opt/smartoffice/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 文件大小限制
    client_max_body_size 100M;
}
EOF

    # 测试配置
    nginx -t
    
    # 重载 Nginx
    systemctl reload nginx
}

# 第十三步：创建系统服务
create_systemd_services() {
    print_info "创建系统服务..."
    
    # FastAPI 服务
    cat > /etc/systemd/system/smartoffice-backend.service << EOF
[Unit]
Description=Smart Office Backend Service
After=network.target redis.service

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=/opt/smartoffice/backend/fastapi_app
Environment="PATH=/opt/smartoffice/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/smartoffice/backend"
ExecStart=/opt/smartoffice/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重载 systemd
    systemctl daemon-reload
}

# 第十四步：配置环境变量
setup_env() {
    print_info "配置环境变量..."
    
    # 提示用户输入邮箱配置
    print_warning "请配置邮箱服务（用于发送验证码）"
    read -p "请输入邮箱地址 (如 xxx@qq.com): " email_user
    read -p "请输入邮箱授权码: " email_pass
    
    # 生成随机密钥
    secret_key=$(openssl rand -hex 32)
    
    # 创建环境配置文件
    cat > $INSTALL_DIR/backend/fastapi_app/.env << EOF
# 邮件配置
EMAIL_USER=$email_user
EMAIL_PASS=$email_pass
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465

# JWT 密钥
SECRET_KEY=$secret_key

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 其他配置
UPLOAD_MAX_SIZE=104857600
EOF

    # 设置权限
    chmod 600 $INSTALL_DIR/backend/fastapi_app/.env
    chown $REAL_USER:$REAL_USER $INSTALL_DIR/backend/fastapi_app/.env
}

# 第十五步：配置防火墙
configure_firewall() {
    print_info "配置防火墙..."
    
    # 检查是否安装了 firewalld
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    else
        print_warning "firewalld 未安装，跳过防火墙配置"
    fi
}

# 第十六步：启动服务
start_services() {
    print_info "启动服务..."
    
    # 启动后端服务
    systemctl enable smartoffice-backend
    systemctl start smartoffice-backend
    
    # 检查服务状态
    sleep 3
    if systemctl is-active --quiet smartoffice-backend; then
        print_info "后端服务启动成功"
    else
        print_error "后端服务启动失败"
        journalctl -u smartoffice-backend -n 50
    fi
}

# 第十七步：运行数据库迁移
run_migrations() {
    print_info "运行数据库迁移..."
    cd $INSTALL_DIR
    
    # 检查是否有 alembic.ini
    if [ -f "alembic.ini" ]; then
        sudo -u $REAL_USER $INSTALL_DIR/venv/bin/alembic upgrade head
    else
        print_warning "未找到 alembic.ini，跳过数据库迁移"
    fi
}

# 获取服务器 IP
get_server_ip() {
    # 尝试获取第一个非本地 IP
    ip addr show | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+' | grep -v '127.0.0.1' | head -n 1
}

# 主函数
main() {
    check_root
    
    print_info "=== 智能办公系统自动化部署 ==="
    
    # 询问是否继续
    read -p "是否继续部署？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 0
    fi
    
    # 执行安装步骤
    install_system_deps
    install_python
    install_nodejs
    install_redis
    install_nginx
    setup_project_dir
    deploy_code
    install_python_deps
    install_frontend_deps
    build_frontend
    init_database
    configure_nginx
    create_systemd_services
    setup_env
    configure_firewall
    run_migrations
    start_services
    
    # 部署完成
    SERVER_IP=$(get_server_ip)
    print_info "=== 部署完成！==="
    print_info "访问地址: http://$SERVER_IP/"
    print_info "后端 API: http://$SERVER_IP:3007/"
    print_info ""
    print_info "查看日志: sudo journalctl -u smartoffice-backend -f"
    print_info "重启服务: sudo systemctl restart smartoffice-backend"
    print_info ""
    print_warning "请记得在防火墙中开放 80 端口"
}

# 运行主函数
main 