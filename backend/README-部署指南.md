# 智能办公系统 - 公网部署指南

## 🌐 部署方案概览

本项目提供三种公网部署方案：

1. **云服务器部署**（推荐）- 完整的生产环境部署
2. **Docker容器化部署** - 简化的容器化部署
3. **内网穿透部署** - 快速临时公网访问

---

## 🚀 方案一：云服务器部署

### 准备工作

1. **购买云服务器**
   - 推荐配置：2核4G，40G硬盘，5Mbps带宽
   - 操作系统：Ubuntu 20.04 LTS 或 CentOS 7+
   - 云服务商：阿里云、腾讯云、华为云等

2. **购买域名**
   - 在域名注册商购买域名（如：example.com）
   - 将域名A记录解析到服务器公网IP

3. **配置安全组**
   - 开放端口：22（SSH）、80（HTTP）、443（HTTPS）

### 一键部署

```bash
# 1. 连接到服务器
ssh root@your-server-ip

# 2. 下载项目代码
git clone https://github.com/your-username/smart-office.git
cd smart-office

# 3. 运行一键部署脚本
chmod +x deploy-cloud.sh
./deploy-cloud.sh
```

### 手动部署步骤

如果一键部署失败，可以按以下步骤手动部署：

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装依赖
apt install -y curl wget git nginx certbot python3-certbot-nginx \
               python3-pip nodejs npm redis-server supervisor

# 3. 克隆项目
git clone https://github.com/your-username/smart-office.git
cd smart-office

# 4. 安装项目依赖
npm install --production
pip3 install -r backend/requirements.txt

# 5. 构建前端
npm run build

# 6. 配置Nginx
# 编辑 /etc/nginx/sites-available/smartoffice
# 参考 deploy-cloud.sh 中的配置

# 7. 申请SSL证书
certbot --nginx -d your-domain.com

# 8. 配置系统服务
# 参考 deploy-cloud.sh 中的 Supervisor 配置

# 9. 启动服务
systemctl start nginx
supervisorctl start all
```

### 访问系统

- **HTTPS访问**：https://your-domain.com
- **HTTP访问**：http://your-domain.com （自动重定向到HTTPS）

### 管理命令

```bash
# 查看服务状态
supervisorctl status

# 重启服务
supervisorctl restart all

# 查看日志
tail -f /var/log/smartoffice/backend.log
tail -f /var/log/smartoffice/frontend.log

# SSL证书续期
certbot renew
```

---

## 🐳 方案二：Docker容器化部署

### 准备工作

1. 安装Docker和Docker Compose
2. 配置域名解析到服务器IP

### 快速部署

```bash
# 1. 克隆项目
git clone https://github.com/your-username/smart-office.git
cd smart-office

# 2. 创建必要的目录
mkdir -p nginx/conf.d ssl logs backups

# 3. 配置Nginx
cat > nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    location / {
        proxy_pass http://smartoffice:3006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://smartoffice:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 4. 申请SSL证书（需要先停止服务）
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/*.pem ssl/

# 5. 启动服务
docker-compose up -d
```

### 管理命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f smartoffice

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码
git pull
docker-compose build
docker-compose up -d
```

---

## 🔗 方案三：内网穿透部署

### 使用 ngrok（推荐）

```bash
# 1. 安装 ngrok
# Windows: 下载 ngrok.exe
# Mac: brew install ngrok
# Linux: wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip

# 2. 注册账号并获取 authtoken
# 访问 https://dashboard.ngrok.com/get-started/setup
ngrok authtoken YOUR_AUTHTOKEN

# 3. 启动本地服务
npm install
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 3007 &
cd .. && node server-production.js &

# 4. 启动内网穿透
ngrok http 3006
```

### 使用花生壳

```bash
# 1. 注册花生壳账号
# 2. 下载并安装花生壳客户端
# 3. 配置内网穿透规则
#    - 内网地址：127.0.0.1
#    - 内网端口：3006
#    - 外网端口：80
# 4. 启动本地服务
./start.sh
```

### 使用 frp

```bash
# 1. 下载 frp
wget https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz
tar -xzf frp_0.52.3_linux_amd64.tar.gz

# 2. 配置客户端
cat > frpc.ini << 'EOF'
[common]
server_addr = your-frp-server.com
server_port = 7000
token = your-token

[smartoffice]
type = http
local_ip = 127.0.0.1
local_port = 3006
custom_domains = your-domain.com
EOF

# 3. 启动服务
./start.sh
./frpc -c frpc.ini
```

---

## 📊 性能优化建议

### 服务器配置

```bash
# 1. 增加文件描述符限制
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# 2. 优化内核参数
cat >> /etc/sysctl.conf << 'EOF'
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 120
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
EOF
sysctl -p

# 3. 配置Redis优化
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
echo "never" > /sys/kernel/mm/transparent_hugepage/enabled
```

### 应用层优化

```bash
# 1. 启用Gzip压缩
# 2. 配置静态资源缓存
# 3. 使用CDN加速
# 4. 数据库索引优化
# 5. 接口响应缓存
```

---

## 🔐 安全配置

### 基础安全

```bash
# 1. 修改SSH端口
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart ssh

# 2. 禁用root登录
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 3. 配置防火墙
ufw allow 2222/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 4. 安装fail2ban
apt install -y fail2ban
```

### 应用安全

```bash
# 1. 定期更新系统
apt update && apt upgrade -y

# 2. 定期备份数据
# 参考 docker-compose.yml 中的备份服务

# 3. 监控系统资源
# 安装 htop, iotop, netstat 等工具

# 4. 配置日志轮转
# 参考系统日志配置
```

---

## 🎯 域名配置

### DNS解析配置

```
类型    名称    值                 TTL
A       @       your-server-ip    600
A       www     your-server-ip    600
CNAME   api     your-domain.com   600
```

### 多域名支持

```nginx
# 在 Nginx 配置中添加多个 server_name
server_name your-domain.com www.your-domain.com;
```

---

## 🚨 故障排查

### 常见问题

1. **无法访问网站**
   - 检查防火墙设置
   - 检查域名解析
   - 检查服务状态

2. **SSL证书问题**
   - 检查证书有效期
   - 重新申请证书
   - 检查证书文件路径

3. **服务启动失败**
   - 检查端口占用
   - 检查依赖安装
   - 查看错误日志

### 日志查看

```bash
# 系统日志
journalctl -u nginx -f

# 应用日志
tail -f /var/log/smartoffice/backend.log
tail -f /var/log/smartoffice/frontend.log

# Docker日志
docker-compose logs -f
```

---

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排查部分
2. 检查项目 Issues 是否有相关问题
3. 提交新的 Issue 描述具体问题
4. 联系技术支持邮箱：support@example.com

---

## 📈 监控和维护

### 系统监控

```bash
# 1. 安装监控工具
apt install -y htop iotop nethogs

# 2. 设置资源告警
# 可以使用 Prometheus + Grafana 或云服务器自带监控

# 3. 定期检查
# - 磁盘使用率
# - 内存使用率
# - CPU使用率
# - 网络连接数
```

### 数据备份

```bash
# 自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

# 备份数据库
cp /opt/smart-office/backend/users.db $BACKUP_DIR/users_$DATE.db
cp /opt/smart-office/backend/meetings.db $BACKUP_DIR/meetings_$DATE.db

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/smart-office/backend/uploads/

# 删除7天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

---

## 🎉 部署完成

恭喜！您已经成功将智能办公系统部署到公网。现在全世界的用户都可以通过您的域名访问这个系统了。

**重要提醒：**
- 定期更新系统和依赖包
- 监控系统资源使用情况
- 定期备份重要数据
- 关注安全漏洞公告
- 保持SSL证书有效性

祝您使用愉快！🚀 