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
    };
  }
}
