import { contextBridge, ipcRenderer } from 'electron';

// IPC API를 렌더러 프로세스에 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // API 테스트 관련
  testAPI: (provider: string, apiKey: string) => 
    ipcRenderer.invoke('api:test', provider, apiKey),
  
  // 설정 저장/로드
  saveSettings: (settings: any) => 
    ipcRenderer.invoke('settings:save', settings),
  loadSettings: () => 
    ipcRenderer.invoke('settings:load'),
  
  // 기본 설정 저장/로드
  saveDefaults: (defaults: any) => 
    ipcRenderer.invoke('defaults:save', defaults),
  loadDefaults: () => 
    ipcRenderer.invoke('defaults:load'),
    
  // 네이버 API 설정 저장/로드/삭제
  saveNaverApiSettings: (naverApiData: any) => 
    ipcRenderer.invoke('naverApi:save', naverApiData),
  loadNaverApiSettings: () => 
    ipcRenderer.invoke('naverApi:load'),
  deleteNaverApiSettings: () => 
    ipcRenderer.invoke('naverApi:delete'),
    
  // YouTube API 설정 저장/로드/삭제
  saveYouTubeApiSettings: (youtubeApiData: any) => 
    ipcRenderer.invoke('youtubeApi:save', youtubeApiData),
  loadYouTubeApiSettings: () => 
    ipcRenderer.invoke('youtubeApi:load'),
  deleteYouTubeApiSettings: () => 
    ipcRenderer.invoke('youtubeApi:delete'),
    
  // 외부 링크 열기
  openExternal: (url: string) => 
    ipcRenderer.invoke('shell:openExternal', url),
    
  // YouTube 자막 추출 (메인 프로세스에서 실행)
  extractYouTubeSubtitles: (videoId: string, language?: string) => 
    ipcRenderer.invoke('youtube:extractSubtitles', videoId, language),
    
  // Playwright 기본 브라우저 제어 API
  playwrightInitialize: () => 
    ipcRenderer.invoke('playwright-initialize'),
  playwrightNavigate: (url: string) => 
    ipcRenderer.invoke('playwright-navigate', url),
  playwrightGetUrl: () => 
    ipcRenderer.invoke('playwright-get-url'),
  playwrightClick: (selector: string) => 
    ipcRenderer.invoke('playwright-click', selector),
  playwrightFill: (selector: string, value: string) => 
    ipcRenderer.invoke('playwright-fill', selector, value),
  playwrightWaitSelector: (selector: string, timeout?: number) => 
    ipcRenderer.invoke('playwright-wait-selector', selector, timeout),
  playwrightWaitTimeout: (milliseconds: number) => 
    ipcRenderer.invoke('playwright-wait-timeout', milliseconds),
  playwrightEvaluate: (script: string) => 
    ipcRenderer.invoke('playwright-evaluate', script),
  playwrightClickInFrames: (selector: string, frameUrlPattern?: string) => 
    ipcRenderer.invoke('playwright-click-in-frames', selector, frameUrlPattern),
  playwrightEvaluateInFrames: (script: string, frameUrlPattern?: string) => 
    ipcRenderer.invoke('playwright-evaluate-in-frames', script, frameUrlPattern),
  playwrightType: (text: string, delay?: number) => 
    ipcRenderer.invoke('playwright-type', text, delay),
  playwrightPress: (key: string) => 
    ipcRenderer.invoke('playwright-press', key),
  playwrightClickAt: (x: number, y: number) => 
    ipcRenderer.invoke('playwright-click-at', x, y),
  playwrightSetClipboard: (text: string) => 
    ipcRenderer.invoke('playwright-set-clipboard', text),
  playwrightSetClipboardHTML: (html: string) => 
    ipcRenderer.invoke('playwright-set-clipboard-html', html),
  playwrightDragDropFile: (filePath: string, targetSelector: string) => 
    ipcRenderer.invoke('playwright-drag-drop-file', filePath, targetSelector),
  playwrightCleanup: () => 
    ipcRenderer.invoke('playwright-cleanup'),
    
  // 파일 관련 API
  saveTempFile: (fileName: string, data: number[]) => 
    ipcRenderer.invoke('file:saveTempFile', { fileName, data }),
  deleteTempFile: (filePath: string) => 
    ipcRenderer.invoke('file:deleteTempFile', filePath),
  saveFile: (defaultPath: string, filters: Array<{ name: string; extensions: string[] }>, data: number[]) => 
    ipcRenderer.invoke('file:saveFile', { defaultPath, filters, data }),
  copyImageToClipboard: (filePath: string) => 
    ipcRenderer.invoke('clipboard:copyImage', filePath),
});

// TypeScript 타입 정의
declare global {
  interface Window {
    electronAPI: {
      testAPI: (provider: string, apiKey: string) => Promise<{ success: boolean; message: string }>;
      saveSettings: (settings: any) => Promise<{ success: boolean; message?: string }>;
      loadSettings: () => Promise<any>;
      saveDefaults: (defaults: any) => Promise<{ success: boolean; message?: string }>;
      loadDefaults: () => Promise<any>;
      saveNaverApiSettings: (naverApiData: any) => Promise<{ success: boolean; message?: string }>;
      loadNaverApiSettings: () => Promise<{ success: boolean; data?: any; message?: string }>;
      deleteNaverApiSettings: () => Promise<{ success: boolean; message?: string }>;
      saveYouTubeApiSettings: (youtubeApiData: any) => Promise<{ success: boolean; message?: string }>;
      loadYouTubeApiSettings: () => Promise<{ success: boolean; data?: any; message?: string }>;
      deleteYouTubeApiSettings: () => Promise<{ success: boolean; message?: string }>;
      openExternal: (url: string) => Promise<void>;
      extractYouTubeSubtitles: (videoId: string, language?: string) => Promise<{ success: boolean; data?: any; message?: string }>;
      testYouTubeSubtitleExtraction: (testVideoId?: string) => Promise<{ success: boolean; data?: any; message?: string }>;
      playwrightInitialize: () => Promise<{ success: boolean; error?: string }>;
      playwrightNavigate: (url: string) => Promise<{ success: boolean; error?: string }>;
      playwrightGetUrl: () => Promise<{ success: boolean; url?: string; error?: string }>;
      playwrightClick: (selector: string) => Promise<{ success: boolean; error?: string }>;
      playwrightFill: (selector: string, value: string) => Promise<{ success: boolean; error?: string }>;
      playwrightWaitSelector: (selector: string, timeout?: number) => Promise<{ success: boolean; error?: string }>;
      playwrightWaitTimeout: (milliseconds: number) => Promise<{ success: boolean; error?: string }>;
      playwrightEvaluate: (script: string) => Promise<{ success: boolean; result?: any; error?: string }>;
      playwrightClickInFrames: (selector: string, frameUrlPattern?: string) => Promise<{ success: boolean; error?: string }>;
      playwrightEvaluateInFrames: (script: string, frameUrlPattern?: string) => Promise<{ success: boolean; result?: any; error?: string }>;
      playwrightType: (text: string, delay?: number) => Promise<{ success: boolean; error?: string }>;
      playwrightPress: (key: string) => Promise<{ success: boolean; error?: string }>;
      playwrightClickAt: (x: number, y: number) => Promise<{ success: boolean; error?: string }>;
      playwrightSetClipboard: (text: string) => Promise<{ success: boolean; error?: string }>;
      playwrightSetClipboardHTML: (html: string) => Promise<{ success: boolean; error?: string }>;
      playwrightDragDropFile: (filePath: string, targetSelector: string) => Promise<{ success: boolean; error?: string }>;
      playwrightCleanup: () => Promise<{ success: boolean; error?: string }>;
      saveTempFile: (fileName: string, data: number[]) => Promise<{ success: boolean; filePath?: string; error?: string }>;
      deleteTempFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
      saveFile: (defaultPath: string, filters: Array<{ name: string; extensions: string[] }>, data: number[]) => Promise<{ success: boolean; filePath?: string; error?: string }>;
      copyImageToClipboard: (filePath: string) => Promise<{ success: boolean; error?: string }>;
    };
  }
}
