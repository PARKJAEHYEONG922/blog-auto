import { contextBridge, ipcRenderer } from 'electron';

// IPC API를 렌더러 프로세스에 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // MCP 관련 API
  mcp: {
    connect: (serverConfig: any) => ipcRenderer.invoke('mcp:connect', serverConfig),
    disconnect: (serverName: string) => ipcRenderer.invoke('mcp:disconnect', serverName),
    getConnectedServers: () => ipcRenderer.invoke('mcp:getConnectedServers'),
    getTools: (serverName: string) => ipcRenderer.invoke('mcp:getTools', serverName),
    callTool: (serverName: string, toolName: string, arguments_: any) => 
      ipcRenderer.invoke('mcp:callTool', serverName, toolName, arguments_),
    disconnectAll: () => ipcRenderer.invoke('mcp:disconnectAll'),
  },
  
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
});

// TypeScript 타입 정의
declare global {
  interface Window {
    electronAPI: {
      mcp: {
        connect: (serverConfig: any) => Promise<{ success: boolean; error?: string }>;
        disconnect: (serverName: string) => Promise<{ success: boolean; error?: string }>;
        getConnectedServers: () => Promise<string[]>;
        getTools: (serverName: string) => Promise<{ success: boolean; tools?: any[]; error?: string }>;
        callTool: (serverName: string, toolName: string, arguments_: any) => Promise<{ success: boolean; result?: any; error?: string }>;
        disconnectAll: () => Promise<{ success: boolean; error?: string }>;
      };
      testAPI: (provider: string, apiKey: string) => Promise<{ success: boolean; message: string }>;
      saveSettings: (settings: any) => Promise<{ success: boolean; message?: string }>;
      loadSettings: () => Promise<any>;
      saveDefaults: (defaults: any) => Promise<{ success: boolean; message?: string }>;
      loadDefaults: () => Promise<any>;
    };
  }
}
