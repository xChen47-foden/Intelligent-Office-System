// 云服务器部署配置
module.exports = {
  // 服务器信息
  server: {
    host: '0.0.0.0',           // 监听所有接口
    port: 3006,                // 前端服务端口
    apiPort: 3007,             // 后端API端口
  },
  
  // 域名配置
  domain: {
    // 替换为您的域名
    main: 'your-domain.com',
    api: 'api.your-domain.com',
    // 如果使用子路径，可以配置为 'your-domain.com/api'
  },
  
  // SSL/HTTPS 配置
  ssl: {
    enabled: true,
    certPath: '/etc/letsencrypt/live/your-domain.com/fullchain.pem',
    keyPath: '/etc/letsencrypt/live/your-domain.com/privkey.pem',
  },
  
  // 数据库配置
  database: {
    // 生产环境建议使用 PostgreSQL 或 MySQL
    type: 'sqlite',
    path: './backend/users.db',
    backupPath: './backups/',
  },
  
  // 安全配置
  security: {
    corsOrigins: [
      'https://your-domain.com',
      'https://api.your-domain.com',
    ],
    rateLimit: {
      windowMs: 15 * 60 * 1000, // 15分钟
      max: 100, // 最大请求数
    },
    helmet: true, // 启用安全头
  },
  
  // 部署环境
  environment: 'production',
  
  // 日志配置
  logging: {
    level: 'info',
    path: './logs/',
  },
  
  // 监控配置
  monitoring: {
    enabled: true,
    healthCheck: '/health',
  }
} 