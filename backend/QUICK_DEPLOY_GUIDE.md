# 智能办公系统 - OpenCloudOS 快速部署指南

## 🚀 快速部署（5分钟）

### 1. 准备工作

确保你有：
- OpenCloudOS 虚拟机（4GB内存，20GB硬盘）
- root 或 sudo 权限
- 可用的邮箱账号（用于发送验证码）

### 2. 自动化部署

```bash
# 1. 将项目文件上传到虚拟机（使用 scp 或其他工具）
scp -r ./qxc user@your-vm-ip:/home/user/

# 2. 登录到虚拟机
ssh user@your-vm-ip

# 3. 进入项目目录
cd qxc

# 4. 给部署脚本添加执行权限
chmod +x deploy-opencloudos.sh

# 5. 运行自动化部署脚本
sudo ./deploy-opencloudos.sh
```

脚本会自动完成所有安装和配置步骤。过程中需要输入：
- 邮箱地址（如：xxx@qq.com）
- 邮箱授权码（不是邮箱密码）

### 3. 手动部署（如果自动化脚本失败）

```bash
# 基础环境准备
sudo dnf update -y
sudo dnf install -y python39 python39-pip nodejs redis nginx

# 复制项目文件
sudo cp -r /home/user/qxc /opt/smartoffice
cd /opt/smartoffice

# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy aiosqlite bcrypt pyjwt redis httpx python-multipart aiofiles

# 安装前端依赖并构建
npm install
npm run build

# 启动后端服务
cd backend/fastapi_app
nohup python -m uvicorn main:app --host 0.0.0.0 --port 3007 &

# 配置 Nginx（参考 deploy-opencloudos.md 中的配置）
```

## 📱 访问系统

部署完成后：
1. 打开浏览器访问：`http://虚拟机IP/`
2. 点击"注册"创建新账号
3. 输入邮箱获取验证码
4. 完成注册后登录系统

## 🔧 常用命令

```bash
# 查看后端服务状态
sudo systemctl status smartoffice-backend

# 查看日志
sudo journalctl -u smartoffice-backend -f

# 重启服务
sudo systemctl restart smartoffice-backend

# 停止服务
sudo systemctl stop smartoffice-backend

# 查看端口占用
sudo ss -tulnp | grep -E '(80|3007|6379)'
```

## ❓ 常见问题

### 1. 邮件发送失败
- 检查邮箱授权码是否正确（不是邮箱密码）
- QQ邮箱需要开启 SMTP 服务
- 检查 `.env` 文件中的邮箱配置

### 2. 无法访问网页
- 检查防火墙是否开放 80 端口
- 检查 Nginx 是否正常运行：`sudo systemctl status nginx`
- 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### 3. 后端服务启动失败
- 检查 Python 虚拟环境是否激活
- 检查 Redis 是否运行：`redis-cli ping`
- 查看详细错误：`sudo journalctl -u smartoffice-backend -n 100`

### 4. 前端构建失败
- 清理 node_modules：`rm -rf node_modules package-lock.json`
- 重新安装：`npm install --force`
- 使用淘宝镜像：`npm config set registry https://registry.npmmirror.com`

## 📞 获取帮助

如遇到问题：
1. 查看详细部署文档：`deploy-opencloudos.md`
2. 查看系统日志定位问题
3. 检查所有服务是否正常运行

## 🎉 部署成功标志

- 能访问登录页面
- 能发送和接收验证码
- 能成功注册和登录
- 能看到系统主界面

祝你部署顺利！ 