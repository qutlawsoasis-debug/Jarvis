import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import { autoUpdater } from 'electron-updater'

let pyProcess = null
let mainWindow = null

function startPythonBackend() {
  let backendPath
  let args = []
  
  if (app.isPackaged) {
    // В упакованном виде исполняемый файл лежит в resources/bin/jarvis_backend.exe
    backendPath = path.join(process.resourcesPath, 'bin', 'jarvis_backend.exe')
  } else {
    // В режиме разработки используем питон из виртуального окружения venv
    const projectRoot = path.resolve(app.getAppPath(), '..')
    backendPath = process.platform === 'win32'
      ? path.join(projectRoot, 'backend', '.venv', 'Scripts', 'python.exe')
      : path.join(projectRoot, 'backend', '.venv', 'bin', 'python')
    args = ['-u', path.join(projectRoot, 'backend', 'server.py')]
  }
  
  console.log(`[Electron Main] Starting backend: ${backendPath} with args: ${args}`)
  
  if (!fs.existsSync(backendPath)) {
    console.error(`[Electron Main] Error: Backend not found at ${backendPath}`)
    return
  }
  
  pyProcess = spawn(backendPath, args, {
    cwd: app.isPackaged ? path.dirname(backendPath) : path.join(path.resolve(app.getAppPath(), '..'), 'backend'),
    stdio: 'pipe'
  })
  
  pyProcess.stdout.on('data', (data) => {
    console.log(`[Python stdout]: ${data.toString().trim()}`)
  })
  
  pyProcess.stderr.on('data', (data) => {
    console.error(`[Python stderr]: ${data.toString().trim()}`)
  })
  
  pyProcess.on('close', (code) => {
    console.log(`[Electron Main] Backend process exited with code ${code}`)
    pyProcess = null
  })
}

function stopPythonBackend() {
  if (pyProcess) {
    console.log('[Electron Main] Killing Python backend process tree...')
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', pyProcess.pid, '/f', '/t'])
    } else {
      pyProcess.kill('SIGINT')
    }
    pyProcess = null
  }
}

function initAutoUpdater() {
  // Логирование процессов автообновления в стандартную консоль
  autoUpdater.logger = console

  autoUpdater.on('checking-for-update', () => {
    console.log('[Updater] Checking for updates...')
  })

  autoUpdater.on('update-available', (info) => {
    console.log('[Updater] Update available:', info)
  })

  autoUpdater.on('update-not-available', (info) => {
    console.log('[Updater] Update not available:', info)
  })

  autoUpdater.on('error', (err) => {
    console.error('[Updater] Error in auto-updater:', err)
  })

  autoUpdater.on('download-progress', (progressObj) => {
    console.log(`[Updater] Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`)
  })

  autoUpdater.on('update-downloaded', (info) => {
    console.log('[Updater] Update downloaded. Restarting and installing...')
    autoUpdater.quitAndInstall()
  })

  // Запускаем проверку обновлений при готовности приложения
  autoUpdater.checkForUpdatesAndNotify()
}

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    frame: false, // Frameless!
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Start Python Backend
  startPythonBackend()

  // Initialize Auto Updater
  initAutoUpdater()

  // Custom Window IPC handlers
  ipcMain.on('window-minimize', () => {
    if (mainWindow) mainWindow.minimize()
  })
  ipcMain.on('window-close', () => {
    if (mainWindow) mainWindow.close()
  })

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', () => {
  stopPythonBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Ensure python process is killed on explicit app quit
app.on('will-quit', () => {
  stopPythonBackend()
})
