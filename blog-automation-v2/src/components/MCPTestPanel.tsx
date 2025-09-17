import React, { useState, useEffect } from 'react';
import { mcpClientManager, DEFAULT_MCP_SERVERS, MCPServer } from '../services/mcp-client';

const MCPTestPanel: React.FC = () => {
  const [connectedServers, setConnectedServers] = useState<string[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<{ [key: string]: 'disconnected' | 'connecting' | 'connected' | 'error' }>({});
  const [testResults, setTestResults] = useState<{ [key: string]: any }>({});

  useEffect(() => {
    updateConnectionStatus();
  }, []);

  const updateConnectionStatus = async () => {
    const connected = await mcpClientManager.getConnectedServers();
    setConnectedServers(connected);
    
    const status: { [key: string]: 'disconnected' | 'connecting' | 'connected' | 'error' } = {};
    DEFAULT_MCP_SERVERS.forEach(server => {
      status[server.name] = connected.includes(server.name) ? 'connected' : 'disconnected';
    });
    setConnectionStatus(status);
  };

  const connectToServer = async (server: MCPServer) => {
    setConnectionStatus(prev => ({ ...prev, [server.name]: 'connecting' }));
    
    try {
      await mcpClientManager.connectToServer(server);
      setConnectionStatus(prev => ({ ...prev, [server.name]: 'connected' }));
      updateConnectionStatus();
    } catch (error) {
      console.error(`MCP 서버 연결 실패: ${server.name}`, error);
      setConnectionStatus(prev => ({ ...prev, [server.name]: 'error' }));
    }
  };

  const disconnectFromServer = async (serverName: string) => {
    try {
      await mcpClientManager.disconnectServer(serverName);
      setConnectionStatus(prev => ({ ...prev, [serverName]: 'disconnected' }));
      updateConnectionStatus();
    } catch (error) {
      console.error(`MCP 서버 연결 해제 실패: ${serverName}`, error);
    }
  };

  const testServer = async (serverName: string) => {
    try {
      setTestResults(prev => ({ ...prev, [serverName]: '테스트 중...' }));
      
      // 사용 가능한 도구 목록 조회
      const tools = await mcpClientManager.getAvailableTools(serverName);
      
      setTestResults(prev => ({ 
        ...prev, 
        [serverName]: {
          success: true,
          tools: tools.map(t => t.name),
          toolCount: tools.length
        }
      }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [serverName]: {
          success: false,
          error: error.message
        }
      }));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return '✅';
      case 'connecting': return '🔄';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-blue-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-4">
      <div className="ultra-card p-6 slide-in">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="section-icon orange" style={{width: '40px', height: '40px', fontSize: '20px'}}>🔧</div>
            <h3 className="text-2xl font-bold text-slate-900">MCP 서버 테스트</h3>
          </div>
          <p className="text-base text-slate-600">
            MCP (Model Context Protocol) 서버들과의 연결 상태를 확인하고 테스트할 수 있습니다.
          </p>
        </div>

        <div className="space-y-4">
          {DEFAULT_MCP_SERVERS.map((server) => (
            <div key={server.name} className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getStatusIcon(connectionStatus[server.name])}</span>
                  <div>
                    <h4 className="font-semibold text-slate-900">{server.name}</h4>
                    <span className={`text-sm font-medium ${getStatusColor(connectionStatus[server.name])}`}>
                      {connectionStatus[server.name]}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  {connectionStatus[server.name] === 'connected' ? (
                    <>
                      <button
                        onClick={() => testServer(server.name)}
                        className="ultra-btn px-4 py-2 text-sm"
                      >
                        테스트
                      </button>
                      <button
                        onClick={() => disconnectFromServer(server.name)}
                        className="px-4 py-2 text-sm bg-red-500 text-white rounded-xl hover:bg-red-600 transition-all duration-200"
                      >
                        연결 해제
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => connectToServer(server)}
                      disabled={connectionStatus[server.name] === 'connecting'}
                      className="px-4 py-2 text-sm bg-green-500 text-white rounded-xl hover:bg-green-600 disabled:bg-slate-400 transition-all duration-200"
                    >
                      {connectionStatus[server.name] === 'connecting' ? '연결 중...' : '연결'}
                    </button>
                  )}
                </div>
              </div>
              
              <p className="text-sm text-slate-600 mb-3">{server.description}</p>
              
              <div className="text-xs text-slate-500 bg-slate-50 p-2 rounded-lg">
                <span className="font-medium">명령어: </span>
                <code className="bg-slate-200 px-2 py-1 rounded font-mono">{server.command} {server.args.join(' ')}</code>
              </div>

              {/* 테스트 결과 */}
              {testResults[server.name] && (
                <div className="mt-4 p-3 bg-slate-50 rounded-xl text-sm">
                  <div className="font-semibold text-slate-900 mb-2">테스트 결과:</div>
                  {typeof testResults[server.name] === 'string' ? (
                    <span className="text-slate-600">{testResults[server.name]}</span>
                  ) : testResults[server.name].success ? (
                    <div className="text-green-600">
                      <div className="flex items-center gap-2 mb-2">
                        <span>✅</span>
                        <span className="font-medium">성공 - {testResults[server.name].toolCount}개 도구 사용 가능</span>
                      </div>
                      <div className="text-xs text-slate-600">
                        <span className="font-medium">도구:</span> {testResults[server.name].tools.join(', ')}
                      </div>
                    </div>
                  ) : (
                    <div className="text-red-600 flex items-center gap-2">
                      <span>❌</span>
                      <span>실패 - {testResults[server.name].error}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="section-card" style={{padding: '20px', background: 'linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%)'}}>
          <div className="section-header" style={{marginBottom: '16px'}}>
            <div className="section-icon blue" style={{width: '32px', height: '32px', fontSize: '16px'}}>💡</div>
            <h4 className="section-title" style={{fontSize: '16px'}}>MCP 서버 정보</h4>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <span className="font-semibold text-blue-900">YouTube MCP:</span>
                <span className="text-blue-800 ml-2">유튜브 영상 정보 수집 및 자막 분석</span>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <span className="font-semibold text-blue-900">Filesystem MCP:</span>
                <span className="text-blue-800 ml-2">로컬 파일 시스템 관리 (이미지 저장/읽기)</span>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <span className="font-semibold text-blue-900">Puppeteer MCP:</span>
                <span className="text-blue-800 ml-2">브라우저 자동화 (블로그 자동 발행)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPTestPanel;