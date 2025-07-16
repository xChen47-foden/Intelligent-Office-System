# 智能办公系统 - OpenCloudOS 虚拟机完整部署指南

## 📋 系统要求

### 硬件配置
- **CPU**: 2核或以上
- **内存**: 4GB或以上（推荐8GB）
- **硬盘**: 20GB或以上
- **网络**: 能够访问互联网

### 软件要求
- **操作系统**: OpenCloudOS 8.x 或 9.x
- **Python**: 3.8+
- **Node.js**: 16.x 或 18.x
- **Redis**: 5.0+
- **SQLite**: 3.x

## 🚀 部署步骤

### 1. 系统准备

```bash
# 更新系统
sudo dnf update -y

# 安装基础工具
sudo dnf install -y epel-release
sudo dnf install -y \
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

# 设置系统时区
sudo timedatectl set-timezone Asia/Shanghai
```

### 2. 安装 Python 3.9

```bash
# 安装 Python 3.9
sudo dnf install -y python39 python39-devel python39-pip

# 创建 python3 软链接
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
sudo alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.9 1

# 验证安装
python3 --version
pip3 --version

# 升级 pip
pip3 install --upgrade pip
```

### 3. 安装 Node.js 18

```bash
# 安装 Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# 验证安装
node --version
npm --version

# 配置 npm 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
```

### 4. 安装 Redis

```bash
# 安装 Redis
sudo dnf install -y redis

# 启动并设置开机自启
sudo systemctl enable redis
sudo systemctl start redis

# 验证 Redis 运行状态
redis-cli ping
# 应该返回 PONG
```

### 5. 安装 Nginx

```bash
# 安装 Nginx
sudo dnf install -y nginx

# 启动并设置开机自启
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 6. 上传项目代码

```bash
# 创建项目目录
sudo mkdir -p /opt/smartoffice
sudo chown $USER:$USER /opt/smartoffice

# 将项目代码上传到 /opt/smartoffice
# 可以使用 scp、ftp 或其他工具
# 示例：scp -r ./qxc/* user@your-server:/opt/smartoffice/

# 或者使用 git clone（如果项目在 git 仓库中）
# cd /opt
# git clone <your-project-url> smartoffice
```

### 7. 安装 Python 依赖

```bash
cd /opt/smartoffice

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

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

# 安装 Python 依赖
pip install -r backend/fastapi_app/requirements.txt
```

### 8. 安装前端依赖

```bash
cd /opt/smartoffice

# 安装前端依赖
npm install

# 如果遇到依赖问题，尝试：
npm install --force
```

### 9. 构建前端项目

```bash
cd /opt/smartoffice

# 构建生产版本
npm run build

# 验证构建结果
ls -la dist/
```

### 10. 创建数据库目录和文件

```bash
cd /opt/smartoffice/backend

# 创建必要的数据库文件
touch users.db meetings.db chat-db.json

# 初始化 chat-db.json
echo '{"messages": {}, "groups": {}}' > chat-db.json

# 创建上传目录
mkdir -p uploads/{avatar,images,meetings,assistant}

# 设置权限
chmod -R 755 uploads/
```

### 11. 配置 Nginx

```bash
# 创建 Nginx 配置文件
sudo tee /etc/nginx/conf.d/smartoffice.conf << 'EOF'
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

# 测试 Nginx 配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 12. 创建系统服务

```bash
# 创建 FastAPI 后端服务
sudo tee /etc/systemd/system/smartoffice-backend.service << EOF
[Unit]
Description=Smart Office Backend Service
After=network.target redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/smartoffice/backend/fastapi_app
Environment="PATH=/opt/smartoffice/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/smartoffice/backend"
ExecStart=/opt/smartoffice/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建前端服务（可选，如果不使用 Nginx 直接提供静态文件）
sudo tee /etc/systemd/system/smartoffice-frontend.service << EOF
[Unit]
Description=Smart Office Frontend Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/smartoffice
Environment="NODE_ENV=production"
Environment="PORT=3006"
ExecStart=/usr/bin/node server-production.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 13. 配置环境变量

```bash
# 创建环境配置文件
cat > /opt/smartoffice/backend/fastapi_app/.env << EOF
# 邮件配置
EMAIL_USER=your_email@qq.com
EMAIL_PASS=your_email_password
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465

# JWT 密钥
SECRET_KEY=your-secret-key-here-change-this-in-production

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 其他配置
UPLOAD_MAX_SIZE=104857600
EOF

# 设置权限
chmod 600 /opt/smartoffice/backend/fastapi_app/.env
```

### 14. 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动后端服务
sudo systemctl enable smartoffice-backend
sudo systemctl start smartoffice-backend

# 检查服务状态
sudo systemctl status smartoffice-backend

# 查看日志
sudo journalctl -u smartoffice-backend -f
```

### 15. 配置防火墙

```bash
# 如果使用 firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# 如果使用 iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save
```

### 16. 初始化数据

```bash
cd /opt/smartoffice/backend

# 激活虚拟环境
source ../venv/bin/activate

# 运行数据库迁移（如果有）
cd ..
alembic upgrade head
```

## 🔧 验证部署

### 1. 检查服务状态

```bash
# 检查所有相关服务
sudo systemctl status nginx
sudo systemctl status redis
sudo systemctl status smartoffice-backend

# 检查端口监听
sudo ss -tulnp | grep -E '(80|3007|6379)'
```

### 2. 测试访问

1. **本地测试**:
   ```bash
   # 测试 API
   curl http://localhost:3007/health
   
   # 测试前端
   curl http://localhost/
   ```

2. **浏览器访问**:
   - 打开浏览器访问: `http://你的服务器IP/`
   - 应该能看到登录页面

### 3. 创建测试账号

1. 访问注册页面
2. 输入邮箱获取验证码
3. 完成注册
4. 使用新账号登录测试

## 🐛 故障排查

### 1. 后端服务无法启动

```bash
# 查看详细日志
sudo journalctl -u smartoffice-backend -n 100

# 手动测试运行
cd /opt/smartoffice/backend/fastapi_app
/opt/smartoffice/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007
```

### 2. 前端无法访问

```bash
# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 检查文件权限
ls -la /opt/smartoffice/dist/
```

### 3. 数据库错误

```bash
# 检查数据库文件权限
ls -la /opt/smartoffice/backend/*.db

# 修复权限
sudo chown $USER:$USER /opt/smartoffice/backend/*.db
chmod 644 /opt/smartoffice/backend/*.db
```

### 4. Redis 连接失败

```bash
# 检查 Redis 状态
redis-cli ping

# 检查 Redis 配置
sudo cat /etc/redis/redis.conf | grep -E "(bind|port)"
```

## 📊 性能优化

### 1. 增加 Uvicorn Workers

编辑服务文件，修改 ExecStart:
```bash
ExecStart=/opt/smartoffice/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007 --workers 4
```

### 2. 配置 Nginx 缓存

在 Nginx 配置中添加:
```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 启用 Gzip 压缩

在 Nginx 配置中添加:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 10240;
gzip_proxied expired no-cache no-store private auth;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
```

## 🔒 安全加固

### 1. 配置 HTTPS（可选）

```bash
# 安装 Certbot
sudo dnf install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com
```

### 2. 限制文件上传

在 Nginx 配置中设置:
```nginx
client_max_body_size 50M;
```

### 3. 配置防火墙规则

```bash
# 只允许必要的端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --reload
```

## 📝 维护建议

1. **定期备份**:
   ```bash
   # 创建备份脚本
   mkdir -p /opt/smartoffice/backups
   cp /opt/smartoffice/backend/*.db /opt/smartoffice/backups/
   tar -czf /opt/smartoffice/backups/uploads-$(date +%Y%m%d).tar.gz /opt/smartoffice/backend/uploads/
   ```

2. **监控日志**:
   ```bash
   # 查看应用日志
   sudo journalctl -u smartoffice-backend -f
   
   # 查看 Nginx 访问日志
   sudo tail -f /var/log/nginx/access.log
   ```

3. **更新维护**:
   ```bash
   # 更新代码后重启服务
   sudo systemctl restart smartoffice-backend
   sudo systemctl reload nginx
   ```

## 完成部署！

现在你的智能办公系统应该已经在 OpenCloudOS 上成功运行了。访问 `http://你的服务器IP/` 即可使用系统。

如有问题，请检查日志文件或参考故障排查部分。 