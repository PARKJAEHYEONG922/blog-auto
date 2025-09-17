// Renderer Process용 MCP 클라이언트 (IPC를 통해 Main Process와 통신)

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: any;
}

export interface MCPServer {
  name: string;
  command: string;
  args: string[];
  env?: { [key: string]: string };
  description: string;
}

export class MCPClientManager {
  async connectToServer(serverConfig: MCPServer): Promise<void> {
    try {
      console.log(`MCP 서버 연결 시도: ${serverConfig.name}`);
      
      const result = await window.electronAPI.mcp.connect(serverConfig);
      if (!result.success) {
        throw new Error(result.error || '연결 실패');
      }
      
      console.log(`MCP 서버 연결 성공: ${serverConfig.name}`);
    } catch (error) {
      console.error(`MCP 서버 연결 실패: ${serverConfig.name}`, error);
      throw error;
    }
  }

  async disconnectServer(serverName: string): Promise<void> {
    try {
      const result = await window.electronAPI.mcp.disconnect(serverName);
      if (!result.success) {
        throw new Error(result.error || '연결 해제 실패');
      }
      console.log(`MCP 서버 연결 해제: ${serverName}`);
    } catch (error) {
      console.error(`MCP 서버 연결 해제 실패: ${serverName}`, error);
      throw error;
    }
  }

  async getAvailableTools(serverName: string): Promise<MCPTool[]> {
    try {
      const result = await window.electronAPI.mcp.getTools(serverName);
      if (!result.success) {
        throw new Error(result.error || '도구 목록 조회 실패');
      }
      return result.tools || [];
    } catch (error) {
      console.error(`도구 목록 조회 실패: ${serverName}`, error);
      throw error;
    }
  }

  async callTool(serverName: string, toolName: string, arguments_: any): Promise<any> {
    try {
      console.log(`도구 호출: ${serverName}.${toolName}`, arguments_);
      
      const result = await window.electronAPI.mcp.callTool(serverName, toolName, arguments_);
      if (!result.success) {
        throw new Error(result.error || '도구 호출 실패');
      }
      
      console.log(`도구 호출 결과: ${serverName}.${toolName}`, result.result);
      return result.result;
    } catch (error) {
      console.error(`도구 호출 실패: ${serverName}.${toolName}`, error);
      throw error;
    }
  }

  async getConnectedServers(): Promise<string[]> {
    try {
      return await window.electronAPI.mcp.getConnectedServers();
    } catch (error) {
      console.error('연결된 서버 목록 조회 실패', error);
      return [];
    }
  }

  async isConnected(serverName: string): Promise<boolean> {
    const connectedServers = await this.getConnectedServers();
    return connectedServers.includes(serverName);
  }

  async disconnectAll(): Promise<void> {
    try {
      const result = await window.electronAPI.mcp.disconnectAll();
      if (!result.success) {
        throw new Error(result.error || '모든 연결 해제 실패');
      }
    } catch (error) {
      console.error('모든 MCP 서버 연결 해제 실패', error);
      throw error;
    }
  }
}

// 기본 MCP 서버 설정들
export const DEFAULT_MCP_SERVERS: MCPServer[] = [
  {
    name: 'naver-search',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-fetch'],
    description: '네이버 검색 API (블로그, 뉴스, 카페)',
    env: {
      // 환경변수로 네이버 API 키 전달 (런타임에 설정)
    }
  },
  {
    name: 'youtube',
    command: 'node',
    args: ['node_modules/@anaisbetts/mcp-youtube/dist/index.js'],
    description: 'YouTube 비디오 분석 및 자막 추출'
  },
  {
    name: 'filesystem',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', 'C:\\temp'],
    description: '파일 시스템 관리 (이미지 저장/읽기)'
  },
  {
    name: 'puppeteer',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-puppeteer'],
    description: '브라우저 자동화 (블로그 자동 발행)'
  }
];

// 싱글톤 인스턴스
export const mcpClientManager = new MCPClientManager();