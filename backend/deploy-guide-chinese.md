# 智能办公系统 - 中国云服务器部署指南

## 🌐 适用服务商

- 阿里云（推荐）
- 腾讯云
- 华为云
- 百度云
- 京东云

## 💻 推荐配置

### 基础配置
- **CPU**: 2核或以上
- **内存**: 2GB或以上
- **硬盘**: 40GB或以上
- **带宽**: 3M或以上（推荐5M）
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 7+

### 网络配置
- **安全组设置**：开放 22、80、443 端口
- **域名解析**：A记录指向服务器公网IP
- **备案**：如使用中国大陆服务器，需要完成ICP备案

## 🛠️ 一键部署脚本

```bash
#!/bin/bash
# 中国云服务器一键部署脚本

echo "🚀 智能办公系统 - 中国云服务器部署"
echo "适用于：阿里云、腾讯云、华为云等"
echo "========================================"

# 检查系统
if [ -f /etc/redhat-release ]; then
    OS="centos"
    echo "检测到 CentOS 系统"
elif [ -f /etc/debian_version ]; then
    OS="ubuntu"
    echo "检测到 Ubuntu 系统"
else
    echo "不支持的操作系统"
    exit 1
fi

# 更新系统
echo "📦 更新系统包..."
if [ "$OS" = "centos" ]; then
    yum update -y
    yum install -y epel-release
    yum install -y curl wget git nginx nodejs npm python3 python3-pip redis supervisor
else
    apt update && apt upgrade -y
    apt install -y curl wget git nginx nodejs npm python3 python3-pip redis-server supervisor
fi

# 安装 Node.js (最新LTS版本)
echo "📦 安装 Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
if [ "$OS" = "ubuntu" ]; then
    apt install -y nodejs
else
    yum install -y nodejs
fi

# 克隆项目
echo "📥 下载项目代码..."
cd /opt
git clone https://github.com/your-username/smart-office.git
cd smart-office

# 安装依赖
echo "📦 安装项目依赖..."
npm install --production
pip3 install -r backend/requirements.txt

# 构建前端
echo "🔨 构建前端..."
npm run build

# 配置 Nginx
echo "⚙️ 配置 Nginx..."
cat > /etc/nginx/conf.d/smartoffice.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /opt/smart-office/dist;
    index index.html;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 文件上传
    location /uploads/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 启用 gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# 配置系统服务
echo "⚙️ 配置系统服务..."
cat > /etc/supervisor/conf.d/smartoffice.conf << 'EOF'
[program:smartoffice-backend]
command=python3 -m uvicorn main:app --host 0.0.0.0 --port 3007
directory=/opt/smart-office/backend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/smartoffice-backend.log

[program:smartoffice-frontend]
command=node server-production.js
directory=/opt/smart-office
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/smartoffice-frontend.log
EOF

# 启动服务
echo "🚀 启动服务..."
systemctl enable nginx redis supervisor
systemctl start nginx redis supervisor
supervisorctl reread
supervisorctl update
supervisorctl start all

# 配置防火墙
echo "🛡️ 配置防火墙..."
if [ "$OS" = "centos" ]; then
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
else
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

echo "✅ 部署完成！"
echo "========================================"
echo "🌐 访问地址: http://$(curl -s ifconfig.me)"
echo "📊 服务状态: supervisorctl status"
echo "📋 查看日志: tail -f /var/log/smartoffice-backend.log"
echo "🔧 重启服务: supervisorctl restart all"
echo "========================================"
```

## 🔧 手动部署步骤

### 1. 连接服务器
```bash
# 使用SSH连接（替换为您的服务器IP）
ssh root@your-server-ip
```

### 2. 系统初始化
```bash
# Ubuntu/Debian
apt update && apt upgrade -y
apt install -y curl wget git nginx nodejs npm python3 python3-pip redis-server supervisor

# CentOS/RHEL
yum update -y
yum install -y epel-release
yum install -y curl wget git nginx nodejs npm python3 python3-pip redis supervisor
```

### 3. 下载项目
```bash
cd /opt
git clone https://github.com/your-username/smart-office.git
cd smart-office
```

### 4. 安装依赖
```bash
npm install --production
pip3 install -r backend/requirements.txt
```

### 5. 构建前端
```bash
npm run build
```

### 6. 配置服务
参考上面的配置文件进行设置

## 🌟 中国特色优化

### 1. 使用国内镜像源
```bash
# npm 淘宝镜像
npm config set registry https://registry.npm.taobao.org

# pip 清华镜像
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. CDN 加速
```nginx
# 在 Nginx 配置中添加
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    # 可以配置阿里云CDN或腾讯云CDN
}
```

### 3. 数据库优化
```bash
# 针对小内存服务器的 SQLite 优化
echo "pragma journal_mode = WAL;" >> /opt/smart-office/backend/optimize.sql
```

## 🔒 安全配置

### 1. 修改SSH端口
```bash
# 编辑 /etc/ssh/sshd_config
Port 2222
PermitRootLogin no
```

### 2. 安装安全组件
```bash
# 安装 fail2ban
apt install -y fail2ban  # Ubuntu
yum install -y fail2ban  # CentOS
```

### 3. 配置 SSL 证书
```bash
# 使用 Let's Encrypt 免费证书
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## 📊 监控和维护

### 1. 系统监控
```bash
# 安装监控工具
apt install -y htop iotop nethogs

# 查看系统资源
htop
df -h
free -h
```

### 2. 应用监控
```bash
# 查看服务状态
supervisorctl status

# 查看日志
tail -f /var/log/smartoffice-backend.log
tail -f /var/log/smartoffice-frontend.log
```

### 3. 定期维护
```bash
# 创建维护脚本
cat > /opt/maintenance.sh << 'EOF'
#!/bin/bash
# 每日维护脚本

# 备份数据库
cp /opt/smart-office/backend/users.db /opt/backups/users-$(date +%Y%m%d).db
cp /opt/smart-office/backend/meetings.db /opt/backups/meetings-$(date +%Y%m%d).db

# 清理日志
find /var/log -name "*.log" -mtime +7 -exec rm {} \;

# 清理备份
find /opt/backups -name "*.db" -mtime +30 -exec rm {} \;

# 重启服务
supervisorctl restart all
EOF

chmod +x /opt/maintenance.sh

# 添加到 crontab
echo "0 2 * * * /opt/maintenance.sh" | crontab -
```

## 🚨 常见问题

### 1. 内存不足
```bash
# 创建 swap 文件
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 2. 端口占用
```bash
# 查看端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :3007

# 杀死占用进程
kill -9 PID
```

### 3. 权限问题
```bash
# 修复权限
chown -R root:root /opt/smart-office
chmod -R 755 /opt/smart-office
```

## 📱 域名和备案

### 1. 域名解析
```
类型    名称    值             TTL
A       @       服务器IP       600
A       www     服务器IP       600
```

### 2. ICP备案
如果使用中国大陆服务器，需要完成ICP备案：
1. 在云服务商管理后台申请备案
2. 提交相关资料
3. 等待审核通过（通常需要7-20个工作日）

### 3. 公安备案
部分地区还需要进行公安备案：
1. 访问 [全国公安机关互联网站安全管理服务平台](http://www.beian.gov.cn/)
2. 按要求提交资料
3. 等待审核通过

## 🎉 部署完成

恭喜！您的智能办公系统已经成功部署到中国云服务器！

**访问地址**: http://your-server-ip
**管理后台**: 登录后台查看系统状态

**技术支持**:
- 查看日志排查问题
- 定期更新系统和应用
- 监控服务器资源使用情况

祝您使用愉快！🚀 