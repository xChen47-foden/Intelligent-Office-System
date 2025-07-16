// 部署配置
export default {
  // 项目基本信息
  name: '智能办公系统',
  description: '基于大模型的智能办公应用系统',
  version: '1.0.0',
  
  // 服务器配置
  server: {
    port: 3006,
    host: '0.0.0.0', // 允许外部访问
    https: false,
    hostname: 'zngb47' // 网络访问主机名
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser'
  },
  
  // API 配置
  api: {
    baseURL: '/api',
    timeout: 10000,
    proxyTarget: 'http://localhost:3007'
  },
  
  // 部署配置
  deploy: {
    // 静态资源部署路径
    staticPath: '/',
    // 是否启用 gzip 压缩
    gzip: true,
    // 是否启用 brotli 压缩
    brotli: true,
    // 缓存策略
    cache: {
      html: 'no-cache',
      js: '1y',
      css: '1y',
      img: '1y'
    }
  }
} 