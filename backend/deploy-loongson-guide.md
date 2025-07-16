# 智能办公系统 - 龙芯虚拟机部署指南

## 🐉 龙芯架构说明

龙芯是中国自主研发的CPU架构，支持以下操作系统：
- 统信UOS (推荐)
- 银河麒麟 (Kylin)
- Loongnix (龙芯官方系统)
- 中标麒麟

## 📋 系统要求

### 硬件配置
- **CPU**: 龙芯3A5000/3A4000或更高
- **内存**: 4GB或以上（推荐8GB）
- **硬盘**: 50GB或以上
- **架构**: loongarch64 或 mips64el

### 软件要求
- **操作系统**: 统信UOS 20 SP1或更高版本
- **Python**: 3.8+
- **Node.js**: 16.x或18.x
- **Redis**: 5.0+
- **SQLite**: 3.x

## 🚀 部署步骤

### 1. 准备龙芯虚拟机

```bash
# 检查系统架构
uname -a
# 应该显示 loongarch64 或 mips64el

# 检查系统版本
cat /etc/os-release
```

### 2. 配置软件源（以UOS为例）

```bash
# 备份原始源
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# 配置UOS官方源或龙芯源
sudo nano /etc/apt/sources.list

# 添加以下内容（根据系统版本调整）
# deb https://professional-packages.chinauos.com/desktop-professional eagle main contrib non-free
# deb-src https://professional-packages.chinauos.com/desktop-professional eagle main contrib non-free

# 更新软件包
sudo apt update
```

### 3. 安装基础依赖

```bash
# 安装系统依赖
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    gcc \
    g++ \
    make \
    python3-dev \
    libffi-dev \
    libssl-dev \
    redis-server \
    nginx \
    sqlite3 \
    libsqlite3-dev

# 安装Python和pip
sudo apt install -y python3 python3-pip python3-venv

# 验证Python版本
python3 --version
```

### 4. 安装Node.js（龙芯架构专用）

```bash
# 方法一：从源码编译（推荐，确保兼容性）
cd /tmp
wget https://nodejs.org/dist/v18.18.0/node-v18.18.0.tar.gz
tar -xzf node-v18.18.0.tar.gz
cd node-v18.18.0

# 配置编译选项（针对龙芯架构）
if [[ $(uname -m) == "loongarch64" ]]; then
    ./configure --prefix=/usr/local
elif [[ $(uname -m) == "mips64el" ]]; then
    ./configure --prefix=/usr/local --with-mips-arch-variant=loongson3a
fi

# 编译安装（时间较长，请耐心等待）
make -j$(nproc)
sudo make install

# 方法二：使用预编译包（如果有龙芯官方提供）
# 检查龙芯软件源
sudo apt search nodejs
# 如果有，直接安装
sudo apt install -y nodejs npm

# 验证安装
node --version
npm --version
```

### 5. 克隆项目代码

```bash
# 创建项目目录
sudo mkdir -p /opt/smart-office
sudo chown $USER:$USER /opt/smart-office

# 克隆项目（替换为实际的项目地址）
cd /opt
git clone <your-project-git-url> smart-office
cd smart-office

# 或者通过文件传输工具上传项目代码
# 使用 scp, sftp 或其他工具将项目上传到 /opt/smart-office
```

### 6. 配置Python环境

```bash
cd /opt/smart-office

# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 配置pip使用国内源（提高下载速度）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装Python依赖
cd backend/fastapi_app
pip install -r requirements.txt

# 安装额外依赖
pip install python-multipart sqlalchemy aiosqlite bcrypt pyjwt redis
```

### 7. 配置Node.js环境

```bash
cd /opt/smart-office

# 配置npm使用国内源
npm config set registry https://registry.npmmirror.com

# 安装前端依赖
npm install

# 如果遇到依赖问题，尝试清理缓存
npm cache clean --force

# 安装Node.js后端服务依赖
cd backend/node_service
npm install
cd ../..
```

### 8. 构建前端项目

```bash
cd /opt/smart-office

# 构建生产版本
npm run build

# 检查构建结果
ls -la dist/
```

### 9. 配置数据库

```bash
# 启动Redis服务
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 检查Redis状态
redis-cli ping
# 应该返回 PONG

# 创建数据库目录
mkdir -p /opt/smart-office/backend/db
cd /opt/smart-office/backend

# 初始化SQLite数据库（如果需要）
sqlite3 users.db ".databases"
sqlite3 meetings.db ".databases"
```

### 10. 配置Nginx

```bash
# 创建Nginx配置文件
sudo nano /etc/nginx/sites-available/smart-office

# 添加以下配置
```

```nginx
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    root /opt/smart-office/dist;
    index index.html;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # FastAPI后端代理
    location /api/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 认证相关路由
    location /auth/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket路由
    location /ws/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
    
    # 文件上传
    location /uploads/ {
        alias /opt/smart-office/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 文件大小限制
    client_max_body_size 100M;
}
```

```bash
# 启用站点配置
sudo ln -s /etc/nginx/sites-available/smart-office /etc/nginx/sites-enabled/

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 11. 创建系统服务

```bash
# 创建FastAPI服务
sudo nano /etc/systemd/system/smart-office-backend.service
```

```ini
[Unit]
Description=Smart Office Backend Service
After=network.target redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/smart-office/backend/fastapi_app
Environment="PATH=/opt/smart-office/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/smart-office/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 创建Node.js服务（如果需要）
sudo nano /etc/systemd/system/smart-office-node.service
```

```ini
[Unit]
Description=Smart Office Node Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/smart-office/backend/node_service
ExecStart=/usr/local/bin/node index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 12. 启动服务

```bash
# 重载系统服务
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable smart-office-backend
sudo systemctl start smart-office-backend

# 如果有Node.js服务
sudo systemctl enable smart-office-node
sudo systemctl start smart-office-node

# 检查服务状态
sudo systemctl status smart-office-backend
sudo systemctl status smart-office-node
sudo systemctl status nginx
sudo systemctl status redis
```

### 13. 防火墙配置

```bash
# 如果使用ufw防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# 如果使用firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

## 🔧 龙芯架构特殊处理

### 1. 编译优化

```bash
# 设置编译器优化选项
export CFLAGS="-march=loongarch64 -O2"
export CXXFLAGS="-march=loongarch64 -O2"

# 对于mips64el架构
export CFLAGS="-march=loongson3a -O2"
export CXXFLAGS="-march=loongson3a -O2"
```

### 2. Python包兼容性

某些Python包可能没有龙芯架构的预编译版本，需要从源码编译：

```bash
# 如果某个包安装失败，尝试：
pip install --no-binary :all: package_name

# 或者手动编译
pip install --no-deps --force-reinstall --no-binary :all: package_name
```

### 3. Node.js包兼容性

```bash
# 如果npm包含有原生模块，可能需要重新编译
npm rebuild

# 或者指定架构
npm install --target_arch=loong64
```

## 📊 性能优化

### 1. 数据库优化

```bash
# SQLite优化
cat > /opt/smart-office/backend/sqlite_optimize.sql << EOF
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 30000000000;
EOF

# 应用优化
cd /opt/smart-office/backend
sqlite3 users.db < sqlite_optimize.sql
sqlite3 meetings.db < sqlite_optimize.sql
```

### 2. Python性能优化

```bash
# 安装性能优化包
pip install uvloop httptools

# 在main.py中添加（如果支持）
# import uvloop
# uvloop.install()
```

### 3. Nginx优化

```nginx
# 在nginx.conf的http块中添加
worker_processes auto;
worker_cpu_affinity auto;

events {
    worker_connections 1024;
    use epoll;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

## 🐛 故障排查

### 1. 查看日志

```bash
# 查看后端日志
sudo journalctl -u smart-office-backend -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# 查看系统日志
sudo journalctl -xe
```

### 2. 常见问题

#### Python包安装失败
```bash
# 安装编译工具
sudo apt install python3-dev gcc g++ make

# 使用国内源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

#### Node.js模块编译失败
```bash
# 清理并重新安装
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### 权限问题
```bash
# 修复文件权限
sudo chown -R $USER:$USER /opt/smart-office
chmod -R 755 /opt/smart-office
```

## ✅ 验证部署

```bash
# 检查服务状态
curl http://localhost:3007/health
curl http://localhost/

# 测试API
curl http://localhost/api/health

# 访问Web界面
# 在浏览器中访问: http://龙芯虚拟机IP地址
```

## 🎉 部署完成

恭喜！您已经成功将智能办公系统部署到龙芯虚拟机上。

**注意事项**：
1. 定期备份数据库文件
2. 监控系统资源使用情况
3. 定期更新系统和依赖包
4. 根据实际使用情况调整配置

**技术支持**：
- 龙芯官方文档：http://www.loongson.cn/
- UOS技术支持：https://www.chinauos.com/ 