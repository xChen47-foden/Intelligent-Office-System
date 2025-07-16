#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCommand(command, options = {}) {
  log(`执行命令: ${command}`, 'cyan');
  try {
    const result = execSync(command, {
      stdio: 'inherit',
      encoding: 'utf-8',
      ...options
    });
    return true;
  } catch (error) {
    log(`命令执行失败: ${error.message}`, 'red');
    return false;
  }
}

function checkDependencies() {
  log('检查构建依赖...', 'yellow');
  
  const dependencies = {
    'node': 'Node.js',
    'npm': 'NPM',
    'python': 'Python'
  };
  
  for (const [cmd, name] of Object.entries(dependencies)) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      log(`✓ ${name} 已安装`, 'green');
    } catch (error) {
      log(`✗ ${name} 未安装或不在PATH中`, 'red');
      return false;
    }
  }
  
  return true;
}

function installNodeDependencies() {
  log('安装Node.js依赖...', 'yellow');
  
  // 删除现有的node_modules和package-lock.json
  if (fs.existsSync('node_modules')) {
    log('删除现有node_modules...', 'dim');
    execSync('rmdir /s /q node_modules', { stdio: 'ignore' });
  }
  
  if (fs.existsSync('package-lock.json')) {
    fs.unlinkSync('package-lock.json');
  }
  
  // 安装依赖
  if (!runCommand('npm install')) {
    return false;
  }
  
  // 安装Electron构建依赖
  const electronDeps = [
    'electron@^25.0.0',
    'electron-builder@^24.0.0',
    'concurrently@^8.0.0',
    'wait-on@^7.0.0'
  ];
  
  for (const dep of electronDeps) {
    if (!runCommand(`npm install --save-dev ${dep}`)) {
      return false;
    }
  }
  
  return true;
}

function buildFrontend() {
  log('构建前端应用...', 'yellow');
  
  // 检查是否有Vue CLI或Vite配置
  if (fs.existsSync('vite.config.ts') || fs.existsSync('vite.config.js')) {
    return runCommand('npm run build');
  } else if (fs.existsSync('vue.config.js')) {
    return runCommand('vue-cli-service build');
  } else {
    log('未找到Vue构建配置文件', 'red');
    return false;
  }
}

function buildBackend() {
  log('构建后端服务...', 'yellow');
  
  const backendPath = path.join(__dirname, 'backend');
  if (!fs.existsSync(backendPath)) {
    log('backend目录不存在', 'red');
    return false;
  }
  
  // 检查后端打包脚本
  const buildScript = path.join(backendPath, 'build_backend.py');
  if (!fs.existsSync(buildScript)) {
    log('后端打包脚本不存在', 'red');
    return false;
  }
  
  // 执行后端打包
  return runCommand('python build_backend.py', { cwd: backendPath });
}

function prepareElectronFiles() {
  log('准备Electron文件...', 'yellow');
  
  // 创建dist_electron目录
  const electronDir = path.join(__dirname, 'dist_electron');
  if (!fs.existsSync(electronDir)) {
    fs.mkdirSync(electronDir, { recursive: true });
  }
  
  // 复制Electron主进程文件
  const mainFile = path.join(__dirname, 'electron-main.js');
  const preloadFile = path.join(__dirname, 'preload.js');
  
  if (fs.existsSync(mainFile)) {
    fs.copyFileSync(mainFile, path.join(electronDir, 'index.js'));
  }
  
  if (fs.existsSync(preloadFile)) {
    fs.copyFileSync(preloadFile, path.join(electronDir, 'preload.js'));
  }
  
  // 复制后端构建文件
  const backendDist = path.join(__dirname, 'backend', 'dist');
  const targetBackend = path.join(electronDir, 'backend');
  
  if (fs.existsSync(backendDist)) {
    if (fs.existsSync(targetBackend)) {
      execSync(`rmdir /s /q ${targetBackend}`, { stdio: 'ignore' });
    }
    execSync(`xcopy "${backendDist}" "${targetBackend}" /E /I /Y`, { stdio: 'inherit' });
  }
  
  return true;
}

function createLicense() {
  log('创建许可证文件...', 'yellow');
  
  const licenseContent = `QXC 智能办公应用软件
版权所有 (c) ${new Date().getFullYear()} QXC Team

本软件按"原样"提供，不提供任何明示或暗示的保证，
包括但不限于对适销性、特定用途适用性和非侵权性的保证。

在任何情况下，作者或版权持有人均不对任何索赔、损害
或其他责任负责，无论是在合同行为、侵权行为或其他行为中，
由本软件或本软件的使用或其他交易引起、产生或与之相关。

使用本软件即表示您接受上述条款和条件。
`;
  
  fs.writeFileSync('LICENSE.txt', licenseContent, 'utf-8');
  return true;
}

function buildElectronApp() {
  log('构建Electron应用...', 'yellow');
  
  // 更新package.json中的main字段
  const packageJsonPath = path.join(__dirname, 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  packageJson.main = 'dist_electron/index.js';
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  
  // 构建安装程序
  return runCommand('npm run electron:build-win');
}

function createPortableVersion() {
  log('创建便携版...', 'yellow');
  
  const portableDir = path.join(__dirname, 'dist_portable');
  const installerDir = path.join(__dirname, 'dist_installer');
  
  // 检查是否有构建输出
  if (!fs.existsSync(installerDir)) {
    log('未找到安装程序构建输出', 'red');
    return false;
  }
  
  // 创建便携版目录
  if (fs.existsSync(portableDir)) {
    execSync(`rmdir /s /q ${portableDir}`, { stdio: 'ignore' });
  }
  fs.mkdirSync(portableDir, { recursive: true });
  
  // 复制应用文件
  const winUnpackedDir = path.join(installerDir, 'win-unpacked');
  if (fs.existsSync(winUnpackedDir)) {
    execSync(`xcopy "${winUnpackedDir}" "${portableDir}" /E /I /Y`, { stdio: 'inherit' });
  }
  
  // 创建启动脚本
  const startScript = `@echo off
title QXC 智能办公系统
echo 正在启动 QXC 智能办公系统...
echo 请稍候...
"QXC智能办公.exe"
`;
  
  fs.writeFileSync(path.join(portableDir, 'start.bat'), startScript, 'utf-8');
  
  // 创建说明文件
  const readmeContent = `QXC 智能办公系统 - 便携版

使用说明：
1. 双击 "start.bat" 启动应用程序
2. 或者直接双击 "QXC智能办公.exe"

系统要求：
- Windows 10 或更高版本
- .NET Framework 4.7.2 或更高版本
- 可用内存 4GB 以上
- 硬盘空间 2GB 以上

注意事项：
- 首次启动可能需要较长时间
- 请确保防火墙允许应用程序网络访问
- 如遇问题，请联系技术支持

版本：1.0.0
构建日期：${new Date().toLocaleString('zh-CN')}
`;
  
  fs.writeFileSync(path.join(portableDir, 'README.txt'), readmeContent, 'utf-8');
  
  return true;
}

function cleanupBuildFiles() {
  log('清理构建文件...', 'yellow');
  
  const cleanupDirs = ['build', 'backend/build', 'backend/dist'];
  const cleanupFiles = ['backend.spec'];
  
  for (const dir of cleanupDirs) {
    if (fs.existsSync(dir)) {
      try {
        execSync(`rmdir /s /q ${dir}`, { stdio: 'ignore' });
        log(`已清理: ${dir}`, 'dim');
      } catch (error) {
        // 忽略清理错误
      }
    }
  }
  
  for (const file of cleanupFiles) {
    if (fs.existsSync(file)) {
      try {
        fs.unlinkSync(file);
        log(`已清理: ${file}`, 'dim');
      } catch (error) {
        // 忽略清理错误
      }
    }
  }
}

function showBuildSummary() {
  log('\n构建完成！', 'green');
  log('=' * 50, 'green');
  
  const installerDir = path.join(__dirname, 'dist_installer');
  const portableDir = path.join(__dirname, 'dist_portable');
  
  if (fs.existsSync(installerDir)) {
    log(`📦 安装程序: ${installerDir}`, 'cyan');
    
    // 查找.exe安装文件
    try {
      const files = fs.readdirSync(installerDir);
      const exeFile = files.find(f => f.endsWith('.exe'));
      if (exeFile) {
        log(`   ├─ 安装包: ${exeFile}`, 'cyan');
      }
    } catch (error) {
      // 忽略错误
    }
  }
  
  if (fs.existsSync(portableDir)) {
    log(`📁 便携版: ${portableDir}`, 'cyan');
    log(`   ├─ 启动脚本: start.bat`, 'cyan');
    log(`   └─ 说明文件: README.txt`, 'cyan');
  }
  
  log('\n使用说明:', 'yellow');
  log('1. 安装版：运行安装程序，按提示安装', 'dim');
  log('2. 便携版：解压后双击 start.bat 启动', 'dim');
  log('3. 首次启动需要初始化数据库', 'dim');
  
  log('=' * 50, 'green');
}

// 主构建流程
async function main() {
  log('QXC 智能办公系统 - 自动构建工具', 'bright');
  log('=' * 50, 'bright');
  
  try {
    // 步骤1: 检查依赖
    if (!checkDependencies()) {
      process.exit(1);
    }
    
    // 步骤2: 安装Node.js依赖
    if (!installNodeDependencies()) {
      log('安装Node.js依赖失败', 'red');
      process.exit(1);
    }
    
    // 步骤3: 构建前端
    if (!buildFrontend()) {
      log('前端构建失败', 'red');
      process.exit(1);
    }
    
    // 步骤4: 构建后端
    if (!buildBackend()) {
      log('后端构建失败', 'red');
      process.exit(1);
    }
    
    // 步骤5: 准备Electron文件
    if (!prepareElectronFiles()) {
      log('准备Electron文件失败', 'red');
      process.exit(1);
    }
    
    // 步骤6: 创建许可证
    if (!createLicense()) {
      log('创建许可证失败', 'red');
      process.exit(1);
    }
    
    // 步骤7: 构建Electron应用
    if (!buildElectronApp()) {
      log('Electron应用构建失败', 'red');
      process.exit(1);
    }
    
    // 步骤8: 创建便携版
    if (!createPortableVersion()) {
      log('创建便携版失败', 'red');
      process.exit(1);
    }
    
    // 步骤9: 清理构建文件
    cleanupBuildFiles();
    
    // 步骤10: 显示构建摘要
    showBuildSummary();
    
  } catch (error) {
    log(`构建过程中发生错误: ${error.message}`, 'red');
    process.exit(1);
  }
}

// 运行构建
main(); 