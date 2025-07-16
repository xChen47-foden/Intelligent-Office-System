const { execSync } = require('child_process');
const fs = require('fs-extra');
const path = require('path');

console.log('🚀 QXC智能办公 - 临时构建脚本');

try {
  // 1. 清理dist目录
  console.log('📁 清理构建目录...');
  if (fs.existsSync('dist')) {
    fs.removeSync('dist');
  }
  fs.ensureDirSync('dist');

  // 2. 创建基本的index.html
  console.log('📄 生成基本前端文件...');
  const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QXC智能办公系统</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .logo { font-size: 2.5em; color: #409EFF; margin-bottom: 20px; }
        .status { padding: 20px; background: #f5f7fa; border-radius: 8px; margin: 20px 0; }
        .btn { padding: 12px 24px; background: #409EFF; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 10px; }
        .btn:hover { background: #337ecc; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🏢 QXC智能办公系统</div>
        <div class="status">
            <h3>系统正在启动中...</h3>
            <p>请稍候，正在连接后端服务...</p>
            <div id="status"></div>
        </div>
        <button class="btn" onclick="checkBackend()">检查后端状态</button>
        <button class="btn" onclick="openDocs()">查看文档</button>
    </div>

    <script>
        let backendChecked = false;
        
        function checkBackend() {
            document.getElementById('status').innerHTML = '正在检查后端服务...';
            
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = '✅ 后端服务正常运行';
                    if (!backendChecked) {
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 2000);
                    }
                    backendChecked = true;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '❌ 后端服务未启动，请检查服务状态';
                });
        }
        
        function openDocs() {
            window.open('https://github.com/qxc/docs', '_blank');
        }
        
        // 自动检查后端
        setTimeout(checkBackend, 1000);
        setInterval(checkBackend, 5000);
    </script>
</body>
</html>`;

  fs.writeFileSync('dist/index.html', htmlContent);

  // 3. 复制必要的静态文件
  if (fs.existsSync('public')) {
    fs.copySync('public', 'dist');
  }

  // 4. 创建package.json的副本并简化
  console.log('📦 准备electron构建...');
  const packageJson = fs.readJsonSync('package.json');
  
  // 简化构建配置
  packageJson.build.files = [
    "dist/**/*",
    "electron-main.js",
    "preload.js",
    "backend/fastapi_app/**/*",
    "backend/uploads/**/*"
  ];

  packageJson.build.extraResources = [
    {
      "from": "backend/",
      "to": "backend/"
    }
  ];

  fs.writeJsonSync('package.json', packageJson, { spaces: 2 });

  // 5. 构建electron应用
  console.log('⚡ 开始构建Electron应用...');
  execSync('npx electron-builder --win --publish=never', { 
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'production' }
  });

  console.log('✅ 构建完成！');
  console.log('📁 检查以下目录获取安装包：');
  console.log('   - dist_installer/ (Windows安装程序)');
  console.log('   - dist_electron/win-unpacked/ (便携版)');

} catch (error) {
  console.error('❌ 构建失败:', error.message);
  process.exit(1);
} 