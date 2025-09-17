// Electron Main Process에서 실행되는 MCP 서비스
import { ipcMain } from 'electron';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

// @ts-ignore
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
// @ts-ignore  
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

export interface MCPServer {
  name: string;
  command: string;
  args: string[];
  env?: { [key: string]: string };
  description: string;
}

class MCPMainService {
  private clients: Map<string, any> = new Map();
  private transports: Map<string, any> = new Map();

  constructor() {
    this.setupIpcHandlers();
  }

  private setupIpcHandlers() {
    
    // MCP 서버 연결
    ipcMain.handle('mcp:connect', async (event, serverConfig: MCPServer) => {
      try {
        console.log(`MCP 서버 연결 시도: ${serverConfig.name}`);
        
        const transport = new StdioClientTransport({
          command: serverConfig.command,
          args: serverConfig.args,
          env: serverConfig.env
        });

        const client = new Client({
          name: `blog-automation-${serverConfig.name}`,
          version: '1.0.0'
        }, {
          capabilities: {
            tools: {}
          }
        });

        await client.connect(transport);
        
        this.clients.set(serverConfig.name, client);
        this.transports.set(serverConfig.name, transport);
        
        console.log(`MCP 서버 연결 성공: ${serverConfig.name}`);
        return { success: true };
      } catch (error) {
        console.error(`MCP 서버 연결 실패: ${serverConfig.name}`, error);
        return { success: false, error: error.message };
      }
    });

    // MCP 서버 연결 해제
    ipcMain.handle('mcp:disconnect', async (event, serverName: string) => {
      try {
        const client = this.clients.get(serverName);
        const transport = this.transports.get(serverName);

        if (client && transport) {
          await client.close();
          await transport.close();
          this.clients.delete(serverName);
          this.transports.delete(serverName);
          console.log(`MCP 서버 연결 해제: ${serverName}`);
        }
        
        return { success: true };
      } catch (error) {
        console.error(`MCP 서버 연결 해제 실패: ${serverName}`, error);
        return { success: false, error: error.message };
      }
    });

    // 연결된 서버 목록 조회
    ipcMain.handle('mcp:getConnectedServers', () => {
      return Array.from(this.clients.keys());
    });

    // 사용 가능한 도구 목록 조회
    ipcMain.handle('mcp:getTools', async (event, serverName: string) => {
      try {
        const client = this.clients.get(serverName);
        if (!client) {
          throw new Error(`MCP 서버에 연결되지 않음: ${serverName}`);
        }

        const response = await client.listTools();
        return {
          success: true,
          tools: response.tools.map((tool: any) => ({
            name: tool.name,
            description: tool.description || '',
            inputSchema: tool.inputSchema
          }))
        };
      } catch (error) {
        console.error(`도구 목록 조회 실패: ${serverName}`, error);
        return { success: false, error: error.message };
      }
    });

    // 도구 호출
    ipcMain.handle('mcp:callTool', async (event, serverName: string, toolName: string, arguments_: any) => {
      try {
        const client = this.clients.get(serverName);
        if (!client) {
          throw new Error(`MCP 서버에 연결되지 않음: ${serverName}`);
        }

        console.log(`도구 호출: ${serverName}.${toolName}`, arguments_);
        const response = await client.callTool({
          name: toolName,
          arguments: arguments_
        });
        
        console.log(`도구 호출 결과: ${serverName}.${toolName}`, response);
        return { success: true, result: response };
      } catch (error) {
        console.error(`도구 호출 실패: ${serverName}.${toolName}`, error);
        return { success: false, error: error.message };
      }
    });

    // 모든 서버 연결 해제
    ipcMain.handle('mcp:disconnectAll', async () => {
      try {
        const serverNames = Array.from(this.clients.keys());
        for (const serverName of serverNames) {
          await this.disconnect(serverName);
        }
        return { success: true };
      } catch (error) {
        console.error('모든 MCP 서버 연결 해제 실패', error);
        return { success: false, error: error.message };
      }
    });

    // API 테스트 (메인 프로세스에서 실행)
    console.log('🔧 api:test 핸들러 등록 중...');
    ipcMain.handle('api:test', async (event, provider: string, apiKey: string) => {
      console.log(`🔍 메인 프로세스에서 ${provider} API 테스트 시작`);
      
      try {
        let response;
        
        if (provider === 'gemini') {
          // Gemini: 모델 목록 조회 (무료) - 레거시 방식 유지
          const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;
          console.log(`🌐 Gemini API 호출: ${url.replace(apiKey, '***')}`);
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 15000);
          
          response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          
        } else if (provider === 'openai') {
          // OpenAI: 모델 목록 조회 (무료)
          console.log(`🌐 OpenAI API 호출: https://api.openai.com/v1/models`);
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 15000);
          
          response = await fetch('https://api.openai.com/v1/models', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${apiKey}`,
              'Content-Type': 'application/json'
            },
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          
        } else if (provider === 'claude') {
          // Claude: 간단한 메시지 테스트
          console.log(`🌐 Claude API 호출: https://api.anthropic.com/v1/messages`);
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000);
          
          response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
              'x-api-key': apiKey,
              'anthropic-version': '2023-06-01',
              'content-type': 'application/json'
            },
            body: JSON.stringify({
              model: 'claude-3-5-haiku-20241022',
              max_tokens: 1,
              messages: [{ role: 'user', content: 'Hi' }]
            }),
            signal: controller.signal
          });
          clearTimeout(timeoutId);
        } else {
          return { success: false, message: '지원되지 않는 AI 제공자입니다.' };
        }

        // 응답 처리
        console.log(`📡 ${provider} API 응답:`, response.status, response.statusText);
        
        if (response.status === 200) {
          if (provider === 'gemini') {
            try {
              const data = await response.json();
              console.log(`🔍 Gemini 응답 데이터:`, data);
              const models = data.models || [];
              console.log(`✅ Gemini 모델 ${models.length}개 발견`);
              return { 
                success: true, 
                message: `API 연결 성공 (사용 가능한 모델: ${models.length}개)` 
              };
            } catch (jsonError) {
              console.error(`❌ Gemini JSON 파싱 오류:`, jsonError);
              return { success: false, message: 'API 응답 파싱 오류' };
            }
          } else if (provider === 'openai') {
            try {
              const data = await response.json();
              console.log(`🔍 OpenAI 응답 데이터:`, data);
              const models = data.data || [];
              const gptModels = models.filter((m: any) => m.id && m.id.toLowerCase().includes('gpt'));
              console.log(`✅ OpenAI GPT 모델 ${gptModels.length}개 발견`);
              return { 
                success: true, 
                message: `API 연결 성공 (GPT 모델: ${gptModels.length}개)` 
              };
            } catch (jsonError) {
              console.error(`❌ OpenAI JSON 파싱 오류:`, jsonError);
              return { success: false, message: 'API 응답 파싱 오류' };
            }
          } else if (provider === 'claude') {
            try {
              const data = await response.json();
              console.log(`🔍 Claude 응답 데이터:`, data);
              if (data.content && data.content.length > 0) {
                console.log(`✅ Claude API 연결 성공`);
                return { success: true, message: 'API 연결 성공' };
              } else {
                return { success: false, message: 'Claude API 응답 형식 오류' };
              }
            } catch (jsonError) {
              console.error(`❌ Claude JSON 파싱 오류:`, jsonError);
              return { success: false, message: 'API 응답 파싱 오류' };
            }
          }
        } else {
          // 오류 응답의 상세 내용도 확인
          let errorMessage = '';
          try {
            const errorData = await response.text();
            console.log(`❌ ${provider} 오류 응답:`, errorData);
            errorMessage = errorData.length > 0 ? ` - ${errorData.substring(0, 100)}` : '';
          } catch (e) {
            console.log(`❌ 오류 응답 읽기 실패`);
          }

          if (response.status === 400) {
            return { success: false, message: `API 키가 유효하지 않거나 잘못된 요청입니다.${errorMessage}` };
          } else if (response.status === 401) {
            return { success: false, message: `API 키가 유효하지 않습니다.${errorMessage}` };
          } else if (response.status === 403) {
            return { success: false, message: `API 키 권한이 부족합니다.${errorMessage}` };
          } else if (response.status === 429) {
            return { success: false, message: `API 호출 한도를 초과했습니다.${errorMessage}` };
          } else {
            return { success: false, message: `API 오류 (상태코드: ${response.status})${errorMessage}` };
          }
        }
        
        return { success: true, message: 'API 연결 성공' };
        
      } catch (error) {
        console.error(`❌ ${provider} API 테스트 실패:`, error);
        
        if (error instanceof Error) {
          console.error(`🔍 에러 상세:`, {
            name: error.name,
            message: error.message,
            stack: error.stack?.substring(0, 200)
          });
          
          if (error.name === 'AbortError') {
            return { success: false, message: '연결 시간 초과 (15초)' };
          } else if (error.message.includes('ENOTFOUND')) {
            return { success: false, message: 'DNS 해결 실패 - 인터넷 연결 확인' };
          } else if (error.message.includes('ECONNREFUSED')) {
            return { success: false, message: '연결 거부됨 - 방화벽 설정 확인' };
          } else if (error.message.includes('timeout')) {
            return { success: false, message: '연결 시간 초과' };
          } else {
            return { success: false, message: `연결 오류: ${error.message}` };
          }
        }
        
        return { success: false, message: `연결 테스트 실패: ${String(error)}` };
      }
    });
    
    // 설정 저장
    ipcMain.handle('settings:save', async (event, settings) => {
      try {
        const settingsDir = path.join(os.homedir(), '.blog-automation-v2');
        const settingsFile = path.join(settingsDir, 'settings.json');
        
        // 디렉토리 생성 (없으면)
        await fs.mkdir(settingsDir, { recursive: true });
        
        // 설정 파일 저장
        await fs.writeFile(settingsFile, JSON.stringify(settings, null, 2), 'utf8');
        
        console.log('✅ 설정 저장 완료:', settingsFile);
        return { success: true };
      } catch (error) {
        console.error('❌ 설정 저장 실패:', error);
        return { success: false, message: error.message };
      }
    });

    // 설정 로드
    ipcMain.handle('settings:load', async () => {
      try {
        const settingsFile = path.join(os.homedir(), '.blog-automation-v2', 'settings.json');
        
        const data = await fs.readFile(settingsFile, 'utf8');
        const loadedData = JSON.parse(data);
        
        // 기존 형식(settings만 있는 경우)과 새 형식(settings + testingStatus) 모두 처리
        if (loadedData.settings) {
          // 새로운 형식
          return loadedData;
        } else {
          // 기존 형식 - 마이그레이션
          return {
            settings: loadedData,
            testingStatus: {}
          };
        }
      } catch (error) {
        // 기본 설정 반환 (새로운 형식)
        return {
          settings: {
            information: { provider: 'gemini', model: 'gemini-2.0-flash', apiKey: '' },
            writing: { provider: 'claude', model: 'claude-sonnet-4-20250514', apiKey: '' },
            image: { provider: 'openai', model: 'gpt-image-1', apiKey: '' }
          },
          testingStatus: {}
        };
      }
    });

    // 기본 설정 저장
    ipcMain.handle('defaults:save', async (event, defaults) => {
      try {
        const settingsDir = path.join(os.homedir(), '.blog-automation-v2');
        const defaultsFile = path.join(settingsDir, 'defaults.json');
        
        // 디렉토리 생성 (없으면)
        await fs.mkdir(settingsDir, { recursive: true });
        
        // 기본 설정 파일 저장
        await fs.writeFile(defaultsFile, JSON.stringify(defaults, null, 2), 'utf8');
        
        console.log('✅ 기본 설정 저장 완료:', defaultsFile);
        return { success: true };
      } catch (error) {
        console.error('❌ 기본 설정 저장 실패:', error);
        return { success: false, message: error.message };
      }
    });

    // 기본 설정 로드
    ipcMain.handle('defaults:load', async () => {
      try {
        const defaultsFile = path.join(os.homedir(), '.blog-automation-v2', 'defaults.json');
        
        const data = await fs.readFile(defaultsFile, 'utf8');
        const defaults = JSON.parse(data);
        
        console.log('✅ 기본 설정 로드 완료:', defaults);
        return defaults;
      } catch (error) {
        console.log('ℹ️ 기본 설정 파일 없음 (첫 실행)');
        return null;
      }
    });

    // 네이버 API 설정 저장
    ipcMain.handle('naverApi:save', async (event, naverApiData) => {
      try {
        const settingsDir = path.join(os.homedir(), '.blog-automation-v2');
        const naverApiFile = path.join(settingsDir, 'naver-api.json');
        
        // 디렉토리 생성 (없으면)
        await fs.mkdir(settingsDir, { recursive: true });
        
        // 네이버 API 설정 저장
        await fs.writeFile(naverApiFile, JSON.stringify(naverApiData, null, 2), 'utf8');
        
        console.log('✅ 네이버 API 설정 저장 완료:', naverApiFile);
        return { success: true };
      } catch (error) {
        console.error('❌ 네이버 API 설정 저장 실패:', error);
        return { success: false, message: error.message };
      }
    });

    // 네이버 API 설정 로드
    ipcMain.handle('naverApi:load', async () => {
      try {
        const naverApiFile = path.join(os.homedir(), '.blog-automation-v2', 'naver-api.json');
        
        const data = await fs.readFile(naverApiFile, 'utf8');
        const naverApiData = JSON.parse(data);
        
        console.log('✅ 네이버 API 설정 로드 완료');
        return { success: true, data: naverApiData };
      } catch (error) {
        console.log('ℹ️ 네이버 API 설정 파일 없음');
        return { success: false, message: 'No Naver API settings found' };
      }
    });

    // 네이버 API 설정 삭제
    ipcMain.handle('naverApi:delete', async () => {
      try {
        const naverApiFile = path.join(os.homedir(), '.blog-automation-v2', 'naver-api.json');
        
        await fs.unlink(naverApiFile);
        
        console.log('✅ 네이버 API 설정 삭제 완료');
        return { success: true };
      } catch (error) {
        if (error.code === 'ENOENT') {
          console.log('ℹ️ 삭제할 네이버 API 설정 파일 없음');
          return { success: true }; // 파일이 없어도 성공으로 처리
        }
        
        console.error('❌ 네이버 API 설정 삭제 실패:', error);
        return { success: false, message: error.message };
      }
    });
  }

  private async disconnect(serverName: string) {
    const client = this.clients.get(serverName);
    const transport = this.transports.get(serverName);

    if (client && transport) {
      await client.close();
      await transport.close();
      this.clients.delete(serverName);
      this.transports.delete(serverName);
    }
  }

  async cleanup() {
    const serverNames = Array.from(this.clients.keys());
    for (const serverName of serverNames) {
      await this.disconnect(serverName);
    }
  }
}

export const mcpMainService = new MCPMainService();