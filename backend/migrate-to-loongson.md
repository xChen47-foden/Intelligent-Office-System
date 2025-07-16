# Windows项目迁移到龙芯虚拟机指南

## 📋 迁移前准备

### 1. 在Windows上准备项目文件

```powershell
# 在项目根目录执行以下命令

# 1. 清理不必要的文件
Remove-Item -Path "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist_electron" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend\fastapi_app\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# 2. 创建项目压缩包
# 使用PowerShell压缩（推荐）
Compress-Archive -Path * -DestinationPath ..\smart-office.zip

# 或使用7-Zip（如果已安装）
# 7z a -tzip ..\smart-office.zip * -xr!node_modules -xr!dist -xr!venv -xr!__pycache__
```

### 2. 导出数据库文件

如果项目中已有数据，需要备份：

```powershell
# 复制数据库文件到单独的文件夹
New-Item -ItemType Directory -Path ..\db-backup -Force
Copy-Item backend\users.db ..\db-backup\
Copy-Item backend\meetings.db ..\db-backup\
Copy-Item db\doc.db ..\db-backup\

# 复制上传的文件
Copy-Item -Path backend\uploads -Destination ..\db-backup\uploads -Recurse
```

## 🐉 设置龙芯虚拟机

### 1. 创建龙芯虚拟机

推荐配置：
- **虚拟化软件**: VMware Workstation / VirtualBox（需支持龙芯架构）
- **操作系统镜像**: 
  - 统信UOS 20 SP1 (推荐)
  - 银河麒麟 V10
  - Loongnix
- **虚拟机配置**:
  - CPU: 2-4核心
  - 内存: 4GB或以上
  - 硬盘: 50GB或以上
  - 网络: 桥接模式（方便访问）

### 2. 安装操作系统

1. 下载龙芯系统镜像
2. 创建虚拟机并安装系统
3. 配置网络，确保可以访问互联网
4. 记录虚拟机IP地址

## 📦 传输项目文件

### 方法一：使用SCP传输（推荐）

在Windows上使用PowerShell或Git Bash：

```bash
# 传输项目压缩包
scp smart-office.zip username@龙芯虚拟机IP:/home/username/

# 传输数据库备份
scp -r db-backup username@龙芯虚拟机IP:/home/username/
```

### 方法二：使用共享文件夹

1. 在虚拟机软件中设置共享文件夹
2. 将项目文件复制到共享文件夹
3. 在龙芯虚拟机中访问共享文件夹

### 方法三：使用U盘或移动硬盘

1. 将文件复制到U盘
2. 在龙芯虚拟机中挂载U盘
3. 复制文件到虚拟机

## 🚀 在龙芯虚拟机上部署

### 1. 登录到龙芯虚拟机

```bash
# SSH登录（如果已启用SSH）
ssh username@龙芯虚拟机IP

# 或直接在虚拟机控制台操作
```

### 2. 解压项目文件

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 解压项目文件
unzip ~/smart-office.zip -d smart-office
cd smart-office

# 恢复数据库文件（如果有）
cp ~/db-backup/*.db backend/
cp -r ~/db-backup/uploads backend/
```

### 3. 执行一键部署脚本

```bash
# 赋予执行权限
chmod +x deploy-loongson.sh

# 运行部署脚本
./deploy-loongson.sh
```

### 4. 手动部署（如果自动脚本失败）

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装基础依赖
sudo apt install -y build-essential python3 python3-pip python3-venv nginx redis-server sqlite3

# 3. 安装Node.js（从源码编译）
cd /tmp
wget https://nodejs.org/dist/v18.18.0/node-v18.18.0.tar.gz
tar -xzf node-v18.18.0.tar.gz
cd node-v18.18.0
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install

# 4. 返回项目目录
cd ~/projects/smart-office

# 5. 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 6. 安装Python依赖
pip install --upgrade pip
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
cd backend/fastapi_app
pip install -r requirements.txt
pip install python-multipart sqlalchemy aiosqlite bcrypt pyjwt redis uvicorn
cd ../..

# 7. 安装前端依赖
npm config set registry https://registry.npmmirror.com
npm install

# 8. 构建前端
npm run build

# 9. 配置并启动服务
# 参考 deploy-loongson-guide.md 中的详细步骤
```

## 🔧 配置调整

### 1. 修改API地址

如果前端需要访问后端API，可能需要修改配置：

```javascript
// 在 src/config/env/env-config.ts 或类似文件中
// 修改API地址为龙芯虚拟机的IP
const API_BASE_URL = 'http://龙芯虚拟机IP:3007'
```

### 2. 修改数据库路径

如果数据库路径有变化：

```python
# 在 backend/fastapi_app/main.py 中
# 确保数据库路径正确
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, '../users.db')}"
```

### 3. 配置邮件服务

编辑环境变量或配置文件：

```bash
# 创建 .env 文件
cat > backend/fastapi_app/.env << EOF
EMAIL_USER=your-email@qq.com
EMAIL_PASS=your-app-password
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EOF
```

## 🐛 常见问题解决

### 1. Python包编译失败

```bash
# 安装编译依赖
sudo apt install python3-dev libffi-dev libssl-dev

# 使用--no-binary强制从源码安装
pip install --no-binary :all: package_name
```

### 2. Node.js模块兼容性问题

```bash
# 删除并重新安装
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# 重新编译原生模块
npm rebuild
```

### 3. 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER ~/projects/smart-office
chmod -R 755 ~/projects/smart-office
```

### 4. 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep 3007
sudo netstat -tlnp | grep 80

# 查看错误日志
sudo journalctl -u smart-office-backend -n 100
tail -f /var/log/nginx/error.log
```

## ✅ 验证部署

### 1. 检查服务状态

```bash
# 检查后端服务
curl http://localhost:3007/health

# 检查Nginx
curl http://localhost/

# 检查Redis
redis-cli ping
```

### 2. 从Windows访问

在Windows浏览器中访问：
- 主页面: `http://龙芯虚拟机IP/`
- API文档: `http://龙芯虚拟机IP:3007/docs`

### 3. 功能测试

1. 注册新用户
2. 登录系统
3. 上传文件测试
4. 创建会议测试
5. 使用智能助手

## 📊 性能优化建议

### 1. 虚拟机优化

```bash
# 分配更多内存给虚拟机
# 在虚拟机设置中增加内存到8GB或更多

# 启用虚拟化加速
# 确保主机BIOS中启用了VT-x/AMD-V
```

### 2. 数据库优化

```bash
# 为SQLite启用WAL模式
sqlite3 backend/users.db "PRAGMA journal_mode=WAL;"
sqlite3 backend/meetings.db "PRAGMA journal_mode=WAL;"
```

### 3. 服务优化

```bash
# 增加uvicorn工作进程
# 修改systemd服务文件
ExecStart=/path/to/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3007 --workers 4
```

## 🎉 迁移完成

恭喜！您已成功将项目从Windows迁移到龙芯虚拟机。

**后续维护**：
1. 定期备份虚拟机快照
2. 设置自动备份脚本
3. 监控系统资源使用
4. 定期更新系统和依赖

**注意事项**：
- 龙芯架构与x86架构存在差异，某些软件可能需要重新编译
- 性能可能与原生x86系统有差异，需要根据实际情况优化
- 建议在生产环境部署前进行充分测试 