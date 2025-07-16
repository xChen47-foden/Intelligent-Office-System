# 智能办公系统 Docker 镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 安装Python和pip
RUN apk add --no-cache python3 py3-pip redis

# 复制项目文件
COPY . .

# 安装依赖
RUN npm install --production
RUN pip3 install -r backend/requirements.txt

# 构建前端
RUN npm run build

# 创建必要的目录
RUN mkdir -p /app/logs /app/backend/uploads /app/backups

# 暴露端口
EXPOSE 3006 3007

# 设置环境变量
ENV NODE_ENV=production
ENV PYTHONPATH=/app/backend

# 创建启动脚本
RUN echo '#!/bin/sh\n\
# 启动Redis\n\
redis-server --daemonize yes\n\
\n\
# 启动后端服务\n\
cd /app/backend\n\
python3 -m uvicorn main:app --host 0.0.0.0 --port 3007 &\n\
\n\
# 启动前端服务\n\
cd /app\n\
node server-production.js &\n\
\n\
# 等待服务启动\n\
wait\n\
' > /app/start-docker.sh && chmod +x /app/start-docker.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3006/health || exit 1

# 启动命令
CMD ["/app/start-docker.sh"] 