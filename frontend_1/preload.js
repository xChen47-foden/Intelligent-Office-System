const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  getAppName: () => ipcRenderer.invoke('app-name'),

  // 对话框
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),

  // 系统信息
  platform: process.platform,
  isElectron: true,

  // 文件系统操作（仅限安全操作）
  showItemInFolder: (fullPath) => {
    // 通过主进程安全地显示文件夹中的项目
    ipcRenderer.send('show-item-in-folder', fullPath);
  },

  // 窗口控制
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  maximizeWindow: () => ipcRenderer.send('maximize-window'),
  closeWindow: () => ipcRenderer.send('close-window'),

  // 通知系统
  showNotification: (title, body, icon) => {
    if (Notification.permission === 'granted') {
      new Notification(title, { body, icon });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(title, { body, icon });
        }
      });
    }
  },

  // 开发者工具
  openDevTools: () => ipcRenderer.send('open-dev-tools'),

  // 自定义事件监听
  on: (channel, callback) => {
    // 只允许特定的频道
    const validChannels = ['app-update', 'backend-status', 'notification'];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, callback);
    }
  },

  removeListener: (channel, callback) => {
    const validChannels = ['app-update', 'backend-status', 'notification'];
    if (validChannels.includes(channel)) {
      ipcRenderer.removeListener(channel, callback);
    }
  }
});

// 暴露Node.js环境信息（只读）
contextBridge.exposeInMainWorld('nodeAPI', {
  versions: process.versions,
  platform: process.platform,
  arch: process.arch
});

// 安全日志
contextBridge.exposeInMainWorld('logAPI', {
  info: (message) => console.log(`[INFO] ${message}`),
  warn: (message) => console.warn(`[WARN] ${message}`),
  error: (message) => console.error(`[ERROR] ${message}`),
  debug: (message) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[DEBUG] ${message}`);
    }
  }
}); 