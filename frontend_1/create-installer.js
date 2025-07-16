const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');

console.log('🏗️ QXC智能办公 - 安装包生成器');

async function createInstaller() {
  try {
    // 1. 检查便携版文件夹
    const portableDir = 'dist_electron/win-unpacked';
    if (!fs.existsSync(portableDir)) {
      throw new Error('便携版文件夹不存在，请先运行基础构建');
    }

    // 2. 创建安装包目录
    const installerDir = 'dist_installer';
    fs.ensureDirSync(installerDir);

    // 3. 复制便携版到安装包目录
    console.log('📦 准备安装包文件...');
    const appDir = path.join(installerDir, 'app');
    if (fs.existsSync(appDir)) {
      fs.removeSync(appDir);
    }
    fs.copySync(portableDir, appDir);

    // 4. 创建安装脚本
    console.log('📝 创建安装脚本...');
    const installScript = `@echo off
title QXC智能办公系统 - 安装程序
echo.
echo ================================================================
echo                QXC智能办公系统 - 安装程序
echo ================================================================
echo.

set "INSTALL_DIR=%ProgramFiles%\\QXC智能办公"
set "DESKTOP_SHORTCUT=%USERPROFILE%\\Desktop\\QXC智能办公.lnk"
set "STARTMENU_SHORTCUT=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\QXC智能办公.lnk"

echo 安装位置: %INSTALL_DIR%
echo.
echo 正在安装...

:: 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 复制应用文件
echo 正在复制应用文件...
xcopy /E /I /H /Y "%~dp0app\\*" "%INSTALL_DIR%\\"

:: 创建桌面快捷方式
echo 创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\QXC智能办公应用.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\QXC智能办公应用.exe'; $Shortcut.Save()"

:: 创建开始菜单快捷方式
echo 创建开始菜单快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\QXC智能办公应用.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\QXC智能办公应用.exe'; $Shortcut.Save()"

echo.
echo ================================================================
echo                      安装完成！
echo ================================================================
echo.
echo 应用已安装到: %INSTALL_DIR%
echo 桌面快捷方式已创建
echo 开始菜单快捷方式已创建
echo.
echo 双击桌面上的"QXC智能办公"图标即可启动应用
echo.
pause
`;

    fs.writeFileSync(path.join(installerDir, 'install.bat'), installScript, 'utf8');

    // 5. 创建卸载脚本
    const uninstallScript = `@echo off
title QXC智能办公系统 - 卸载程序
echo.
echo ================================================================
echo                QXC智能办公系统 - 卸载程序
echo ================================================================
echo.

set "INSTALL_DIR=%ProgramFiles%\\QXC智能办公"
set "DESKTOP_SHORTCUT=%USERPROFILE%\\Desktop\\QXC智能办公.lnk"
set "STARTMENU_SHORTCUT=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\QXC智能办公.lnk"

echo 正在卸载...

:: 删除桌面快捷方式
if exist "%DESKTOP_SHORTCUT%" del "%DESKTOP_SHORTCUT%"

:: 删除开始菜单快捷方式
if exist "%STARTMENU_SHORTCUT%" del "%STARTMENU_SHORTCUT%"

:: 删除安装目录
if exist "%INSTALL_DIR%" rmdir /S /Q "%INSTALL_DIR%"

echo.
echo 卸载完成！
echo.
pause
`;

    fs.writeFileSync(path.join(installerDir, 'uninstall.bat'), uninstallScript, 'utf8');

    // 6. 创建README文件
    const readmeContent = `# QXC智能办公系统 - 安装包

## 安装方法

1. 以管理员身份运行 install.bat
2. 按照提示完成安装
3. 双击桌面快捷方式启动应用

## 便携版使用

如果不想安装到系统，可以直接使用 app 文件夹中的程序：
- 进入 app 文件夹
- 双击 QXC智能办公应用.exe 启动

## 卸载方法

运行 uninstall.bat 完成卸载

## 系统要求

- Windows 10/11 (64位)
- 至少 4GB 内存
- 至少 2GB 磁盘空间

## 功能特性

- 智能办公管理
- 会议管理系统
- 文档知识库
- AI智能助手
- 任务日程管理

## 技术支持

如有问题，请联系技术支持团队。
`;

    fs.writeFileSync(path.join(installerDir, 'README.txt'), readmeContent, 'utf8');

    // 7. 重命名主程序文件
    const electronExe = path.join(appDir, 'electron.exe');
    const qxcExe = path.join(appDir, 'QXC智能办公应用.exe');
    if (fs.existsSync(electronExe)) {
      fs.moveSync(electronExe, qxcExe);
    }

    console.log('✅ 安装包创建完成！');
    console.log('📁 安装包位置: dist_installer/');
    console.log('📋 包含内容:');
    console.log('   ├── app/ (应用程序文件)');
    console.log('   ├── install.bat (安装脚本)');
    console.log('   ├── uninstall.bat (卸载脚本)');
    console.log('   └── README.txt (说明文档)');
    console.log('');
    console.log('🎯 使用方法:');
    console.log('   1. 以管理员身份运行 install.bat 进行安装');
    console.log('   2. 或直接使用 app 文件夹作为便携版');
    console.log('');

  } catch (error) {
    console.error('❌ 创建安装包失败:', error.message);
  }
}

createInstaller(); 