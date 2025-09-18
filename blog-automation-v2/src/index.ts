import { app, BrowserWindow, ipcMain } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

// 설정 파일 경로
const getConfigPath = (filename: string) => {
  const userDataPath = app.getPath('userData');
  const configPath = path.join(userDataPath, filename);
  console.log(`📁 설정 파일 경로: ${configPath}`);
  return configPath;
};

// IPC 핸들러 설정
const setupIpcHandlers = () => {
  // 기본 설정 저장
  ipcMain.handle('defaults:save', async (event, defaultSettings) => {
    try {
      const configPath = getConfigPath('defaults.json');
      await fs.promises.writeFile(configPath, JSON.stringify(defaultSettings, null, 2));
      console.log('기본 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('기본 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // 기본 설정 로드
  ipcMain.handle('defaults:load', async () => {
    try {
      const configPath = getConfigPath('defaults.json');
      const data = await fs.promises.readFile(configPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.log('기본 설정 파일이 없거나 읽기 실패:', error.message);
      return null;
    }
  });

  // LLM 설정 저장
  ipcMain.handle('settings:save', async (event, settings) => {
    try {
      const configPath = getConfigPath('llm-settings.json');
      await fs.promises.writeFile(configPath, JSON.stringify(settings, null, 2));
      console.log('LLM 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('LLM 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // LLM 설정 로드
  ipcMain.handle('settings:load', async () => {
    try {
      const configPath = getConfigPath('llm-settings.json');
      const data = await fs.promises.readFile(configPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.log('LLM 설정 파일이 없거나 읽기 실패:', error.message);
      return null;
    }
  });

  // 네이버 API 설정 저장
  ipcMain.handle('naverApi:save', async (event, naverApiSettings) => {
    try {
      const configPath = getConfigPath('naver-api.json');
      console.log('🔧 네이버 API 설정 저장 시도:', configPath);
      console.log('📄 저장할 데이터:', naverApiSettings);
      await fs.promises.writeFile(configPath, JSON.stringify(naverApiSettings, null, 2));
      console.log('✅ 네이버 API 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('❌ 네이버 API 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // 네이버 API 설정 로드
  ipcMain.handle('naverApi:load', async () => {
    try {
      const configPath = getConfigPath('naver-api.json');
      console.log('🔍 네이버 API 설정 로드 시도:', configPath);
      const data = await fs.promises.readFile(configPath, 'utf-8');
      const parsedData = JSON.parse(data);
      console.log('✅ 네이버 API 설정 로드 성공:', parsedData);
      return { success: true, data: parsedData };
    } catch (error) {
      console.log('❌ 네이버 API 설정 파일이 없거나 읽기 실패:', error.message);
      return { success: false, data: null };
    }
  });

  // 네이버 API 설정 삭제
  ipcMain.handle('naverApi:delete', async () => {
    try {
      const configPath = getConfigPath('naver-api.json');
      await fs.promises.unlink(configPath);
      console.log('네이버 API 설정 삭제 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('네이버 API 설정 삭제 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // API 테스트 핸들러
  ipcMain.handle('api:test', async (event, provider: string, apiKey: string) => {
    try {
      console.log(`API 테스트 시작: ${provider}`);
      
      // 간단한 API 테스트 구현
      if (provider === 'openai') {
        const response = await fetch('https://api.openai.com/v1/models', {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          return { success: true, message: 'OpenAI API 연결 성공' };
        } else {
          return { success: false, message: `OpenAI API 오류: ${response.status}` };
        }
      } else if (provider === 'anthropic' || provider === 'claude') {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 10,
            messages: [{ role: 'user', content: 'test' }]
          })
        });
        
        if (response.ok) {
          return { success: true, message: 'Claude API 연결 성공' };
        } else {
          return { success: false, message: `Claude API 오류: ${response.status}` };
        }
      } else if (provider === 'gemini') {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
        
        if (response.ok) {
          return { success: true, message: 'Gemini API 연결 성공' };
        } else {
          return { success: false, message: `Gemini API 오류: ${response.status}` };
        }
      } else {
        return { success: false, message: '지원하지 않는 API 제공자입니다' };
      }
    } catch (error) {
      console.error(`API 테스트 실패 (${provider}):`, error);
      return { success: false, message: error.message };
    }
  });
};


// This allows TypeScript to pick up the magic constants that's auto-generated by Forge's Webpack
// plugin that tells the Electron app where to look for the Webpack-bundled app code (depending on
// whether you're running in development or production).
declare const MAIN_WINDOW_WEBPACK_ENTRY: string;
declare const MAIN_WINDOW_PRELOAD_WEBPACK_ENTRY: string;

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

const createWindow = (): void => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    height: 800,
    width: 1200,
    webPreferences: {
      preload: MAIN_WINDOW_PRELOAD_WEBPACK_ENTRY,
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false, // 외부 API 호출 허용
      allowRunningInsecureContent: true,
    },
  });

  // CSP 헤더 제거
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [''],
      },
    });
  });

  // and load the index.html of the app.
  mainWindow.loadURL(MAIN_WINDOW_WEBPACK_ENTRY);

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
  setupIpcHandlers();
  createWindow();
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
