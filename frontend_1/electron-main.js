const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const isDev = process.env.NODE_ENV === 'development';

// 全局变量
let mainWindow;
let backendProcess;
const BACKEND_PORT = 3007;
const FRONTEND_PORT = 3006;

// 应用程序路径
const APP_PATH = isDev 
  ? __dirname 
  : path.join(process.resourcesPath, 'app');

const BACKEND_PATH = isDev
  ? path.join(__dirname, 'backend')
  : path.join(process.resourcesPath, 'backend');

const UPLOADS_PATH = isDev
  ? path.join(__dirname, 'backend', 'uploads')
  : path.join(process.resourcesPath, 'uploads');

// 创建主窗口
function createWindow() {
  // 设置应用菜单
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: '重做', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' }
      ]
    },
    {
      label: '查看',
      submenu: [
        { label: '刷新', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: '强制刷新', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { label: '开发者工具', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click: async () => {
            await dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: '关于 QXC智能办公',
              message: 'QXC智能办公系统',
              detail: '版本: 1.0.0\n基于大模型的智能办公应用软件\n\n开发团队: QXC Team'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);

  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    icon: path.join(__dirname, 'public/favicon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false,
    titleBarStyle: 'default'
  });

  // 窗口准备显示时显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // 开发模式下打开开发者工具
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // 加载应用
  const startUrl = isDev 
    ? `http://localhost:${FRONTEND_PORT}` 
    : `file://${path.join(__dirname, 'dist/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // 处理窗口关闭
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 处理外部链接
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// 启动后端服务
function startBackendService() {
  return new Promise((resolve, reject) => {
    try {
      console.log('正在启动后端服务...');
      
      // 确保上传目录存在
      if (!fs.existsSync(UPLOADS_PATH)) {
        fs.mkdirSync(UPLOADS_PATH, { recursive: true });
      }

      let backendCmd, backendArgs;
      
      if (isDev) {
        // 开发模式：直接运行Python脚本
        backendCmd = 'python';
        backendArgs = ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()];
        
        backendProcess = spawn(backendCmd, backendArgs, {
          cwd: BACKEND_PATH,
          env: { ...process.env, PYTHONPATH: BACKEND_PATH }
        });
      } else {
        // 生产模式：运行打包的可执行文件
        const exePath = path.join(BACKEND_PATH, 'main.exe');
        if (fs.existsSync(exePath)) {
          backendProcess = spawn(exePath, [], {
            cwd: BACKEND_PATH
          });
        } else {
          // 备用方案：直接运行Python
          backendCmd = 'python';
          backendArgs = ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()];
          
          backendProcess = spawn(backendCmd, backendArgs, {
            cwd: BACKEND_PATH,
            env: { ...process.env, PYTHONPATH: BACKEND_PATH }
          });
        }
      }

      backendProcess.stdout.on('data', (data) => {
        console.log(`后端输出: ${data}`);
        if (data.toString().includes('started server process')) {
          resolve();
        }
      });

      backendProcess.stderr.on('data', (data) => {
        console.error(`后端错误: ${data}`);
      });

      backendProcess.on('close', (code) => {
        console.log(`后端进程退出，代码: ${code}`);
      });

      backendProcess.on('error', (err) => {
        console.error('启动后端服务失败:', err);
        reject(err);
      });

      // 超时处理
      setTimeout(() => {
        resolve(); // 即使没有收到启动消息也继续
      }, 5000);

    } catch (error) {
      console.error('启动后端服务异常:', error);
      reject(error);
    }
  });
}

// 停止后端服务
function stopBackendService() {
  if (backendProcess) {
    console.log('正在停止后端服务...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// 检查端口是否可用
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const server = net.createServer();
    
    server.listen(port, () => {
      server.once('close', () => {
        resolve(true);
      });
      server.close();
    });
    
    server.on('error', () => {
      resolve(false);
    });
  });
}

// 等待服务启动
function waitForService(port, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const checkService = () => {
      const net = require('net');
      const socket = new net.Socket();
      
      socket.setTimeout(1000);
      
      socket.on('connect', () => {
        socket.destroy();
        resolve();
      });
      
      socket.on('error', () => {
        if (Date.now() - startTime < timeout) {
          setTimeout(checkService, 1000);
        } else {
          reject(new Error('服务启动超时'));
        }
      });
      
      socket.on('timeout', () => {
        socket.destroy();
        if (Date.now() - startTime < timeout) {
          setTimeout(checkService, 1000);
        } else {
          reject(new Error('服务启动超时'));
        }
      });
      
      socket.connect(port, 'localhost');
    };
    
    checkService();
  });
}

// 应用程序事件处理
app.whenReady().then(async () => {
  try {
    // 启动后端服务
    await startBackendService();
    
    // 等待后端服务就绪
    await waitForService(BACKEND_PORT);
    
    // 创建主窗口
    createWindow();
    
  } catch (error) {
    console.error('应用启动失败:', error);
    
    // 显示错误对话框
    dialog.showErrorBox('启动失败', 
      '应用程序启动失败，请检查：\n' +
      '1. Python环境是否已安装\n' +
      '2. 端口3007是否被占用\n' +
      '3. 防火墙设置\n\n' +
      `错误详情: ${error.message}`
    );
    
    app.quit();
  }
});

// 所有窗口关闭时退出应用（macOS除外）
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackendService();
    app.quit();
  }
});

// macOS 激活时重新创建窗口
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 应用退出时清理
app.on('before-quit', () => {
  stopBackendService();
});

// IPC 事件处理
ipcMain.handle('app-version', () => {
  return app.getVersion();
});

ipcMain.handle('app-name', () => {
  return app.getName();
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

// 错误处理
process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的Promise拒绝:', reason);
}); 