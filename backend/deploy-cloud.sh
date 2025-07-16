#!/bin/bash

# 智能办公系统 - 云服务器部署脚本
# 使用方法: chmod +x deploy-cloud.sh && ./deploy-cloud.sh

set -e

echo "🚀 开始部署智能办公系统到云服务器..."

# 配置变量
DOMAIN="your-domain.com"
EMAIL="your-email@example.com"
PROJECT_DIR="/opt/smart-office"
SERVICE_USER="smartoffice"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统类型
check_system() {
    if [ -f /etc/debian_version ]; then
        OS="debian"
        log_info "检测到 Debian/Ubuntu 系统"
    elif [ -f /etc/redhat-release ]; then
        OS="centos"
        log_info "检测到 CentOS/RHEL 系统"
    else
        log_error "不支持的操作系统"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    if [ "$OS" = "debian" ]; then
        apt update && apt upgrade -y
    else
        yum update -y
    fi
}

# 安装基础依赖
install_dependencies() {
    log_info "安装基础依赖..."
    if [ "$OS" = "debian" ]; then
        apt install -y curl wget git nginx certbot python3-certbot-nginx \
                       python3-pip nodejs npm redis-server supervisor
    else
        yum install -y curl wget git nginx certbot python3-certbot-nginx \
                       python3-pip nodejs npm redis supervisor
    fi
}

# 创建服务用户
create_user() {
    log_info "创建服务用户..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$PROJECT_DIR" "$SERVICE_USER"
        log_info "用户 $SERVICE_USER 创建成功"
    else
        log_info "用户 $SERVICE_USER 已存在"
    fi
}

# 创建项目目录
create_directories() {
    log_info "创建项目目录..."
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/backups"
    mkdir -p /var/log/smartoffice
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    chmod 755 "$PROJECT_DIR"
}

# 部署代码
deploy_code() {
    log_info "部署应用代码..."
    
    # 如果是从Git克隆
    if [ -d ".git" ]; then
        log_info "从Git仓库部署..."
        cp -r . "$PROJECT_DIR/"
    else
        log_info "从当前目录部署..."
        cp -r . "$PROJECT_DIR/"
    fi
    
    cd "$PROJECT_DIR"
    
    # 安装Node.js依赖
    log_info "安装Node.js依赖..."
    npm install --production
    
    # 安装Python依赖
    log_info "安装Python依赖..."
    pip3 install -r backend/requirements.txt
    
    # 构建前端
    log_info "构建前端..."
    npm run build
    
    # 设置权限
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    chmod +x "$PROJECT_DIR/start.sh"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx反向代理..."
    
    cat > /etc/nginx/sites-available/smartoffice << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip压缩
    gzip on;
    gzip_types text/plain application/javascript application/json text/css application/xml;
    
    # 静态文件
    location / {
        proxy_pass http://localhost:3006;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:3007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 文件上传
    location /uploads/ {
        proxy_pass http://localhost:3007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加上传大小限制
        client_max_body_size 50M;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:3006;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/smartoffice /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t && systemctl restart nginx
    log_info "Nginx配置完成"
}

# 获取SSL证书
setup_ssl() {
    log_info "申请SSL证书..."
    
    # 停止nginx以释放80端口
    systemctl stop nginx
    
    # 申请证书
    certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email
    
    # 设置自动续期
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    # 重启nginx
    systemctl start nginx
    log_info "SSL证书配置完成"
}

# 配置系统服务
configure_services() {
    log_info "配置系统服务..."
    
    # 配置Supervisor
    cat > /etc/supervisor/conf.d/smartoffice.conf << EOF
[program:smartoffice-backend]
command=python3 -m uvicorn main:app --host 0.0.0.0 --port 3007
directory=$PROJECT_DIR/backend
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/smartoffice/backend.log
environment=PATH="$PROJECT_DIR/venv/bin"

[program:smartoffice-frontend]
command=node server-production.js
directory=$PROJECT_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/smartoffice/frontend.log
EOF
    
    # 启动服务
    systemctl enable supervisor
    systemctl start supervisor
    supervisorctl reread
    supervisorctl update
    supervisorctl start all
    
    log_info "系统服务配置完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    fi
    
    log_info "防火墙配置完成"
}

# 创建健康检查
create_health_check() {
    log_info "创建健康检查脚本..."
    
    cat > "$PROJECT_DIR/health-check.sh" << EOF
#!/bin/bash
# 健康检查脚本

# 检查前端服务
if curl -f -s http://localhost:3006/health > /dev/null; then
    echo "前端服务正常"
else
    echo "前端服务异常"
    supervisorctl restart smartoffice-frontend
fi

# 检查后端服务
if curl -f -s http://localhost:3007/health > /dev/null; then
    echo "后端服务正常"
else
    echo "后端服务异常"
    supervisorctl restart smartoffice-backend
fi

# 检查数据库
if [ -f "$PROJECT_DIR/backend/users.db" ]; then
    echo "数据库正常"
else
    echo "数据库异常"
fi
EOF
    
    chmod +x "$PROJECT_DIR/health-check.sh"
    
    # 添加到cron
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/health-check.sh >> /var/log/smartoffice/health.log 2>&1") | crontab -
    
    log_info "健康检查配置完成"
}

# 主函数
main() {
    # 检查域名配置
    read -p "请输入您的域名 (如: example.com): " DOMAIN
    read -p "请输入您的邮箱 (用于SSL证书): " EMAIL
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        log_error "域名和邮箱不能为空"
        exit 1
    fi
    
    log_info "开始部署到域名: $DOMAIN"
    
    check_root
    check_system
    update_system
    install_dependencies
    create_user
    create_directories
    deploy_code
    configure_nginx
    setup_ssl
    configure_services
    configure_firewall
    create_health_check
    
    log_info "🎉 部署完成！"
    log_info "访问地址: https://$DOMAIN"
    log_info "日志目录: /var/log/smartoffice/"
    log_info "项目目录: $PROJECT_DIR"
    log_info ""
    log_info "常用管理命令:"
    log_info "  查看服务状态: supervisorctl status"
    log_info "  重启服务: supervisorctl restart all"
    log_info "  查看日志: tail -f /var/log/smartoffice/backend.log"
    log_info "  SSL证书续期: certbot renew"
}

# 运行主函数
main "$@" 