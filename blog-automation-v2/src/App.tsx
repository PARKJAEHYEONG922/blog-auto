import React, { useState, useEffect } from 'react';
import './index.css';

// 3단계 워크플로우 컴포넌트들
import Step1 from './components/Step1';
import Step2 from './components/Step2';
import Step3 from './components/Step3';
import LLMSettings from './components/LLMSettings';
import MCPTestPanel from './components/MCPTestPanel';

// 서비스 임포트
import { LLMClientFactory } from './services/llm-client-factory';

export interface WorkflowData {
  platform: string;
  keyword: string;
  subKeywords: string[];
  contentType: string;
  reviewType: string;
  tone: string;
  customPrompt: string;
  blogDescription: string;
  selectedTitle: string;
  collectedData: unknown;
  generatedContent: string;
}

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [showMCPTest, setShowMCPTest] = useState(false);
  const [workflowData, setWorkflowData] = useState<WorkflowData>({
    platform: '',
    keyword: '',
    subKeywords: [],
    contentType: '',
    reviewType: '',
    tone: '',
    customPrompt: '',
    blogDescription: '',
    selectedTitle: '',
    collectedData: null,
    generatedContent: ''
  });

  // 앱 초기화
  useEffect(() => {
    // LLM 설정 로드
    const loadSettings = async () => {
      try {
        await LLMClientFactory.loadDefaultSettings();
        console.log('LLM 설정 로드 완료');
      } catch (error) {
        console.error('LLM 설정 로드 중 오류:', error);
      }
    };
    loadSettings();
  }, []);

  const updateWorkflowData = (updates: Partial<WorkflowData>) => {
    setWorkflowData(prev => ({ ...prev, ...updates }));
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1
            data={workflowData}
            onNext={(data) => {
              updateWorkflowData(data);
              setCurrentStep(2);
            }}
          />
        );
      case 2:
        return (
          <Step2
            data={workflowData}
            onNext={(data) => {
              updateWorkflowData(data);
              setCurrentStep(3);
            }}
            onBack={() => setCurrentStep(1)}
          />
        );
      case 3:
        return (
          <Step3
            data={workflowData}
            onComplete={(data) => {
              updateWorkflowData(data);
              // 완료 처리
            }}
            onBack={() => setCurrentStep(2)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-screen bg-slate-50 flex flex-col">
      {/* 헤더 - 고정 */}
      <header className="bg-white border-b border-slate-200 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center gap-4">
              <div className="section-icon blue" style={{width: '32px', height: '32px', fontSize: '16px'}}>
                <span>🤖</span>
              </div>
              <h1 className="text-xl font-bold text-slate-900">
                AI 블로그 자동화 V2
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowMCPTest(!showMCPTest);
                    if (!showMCPTest) setShowSettings(false);
                  }}
                  style={{
                    background: showMCPTest ? '#2563eb' : 'white',
                    color: showMCPTest ? 'white' : '#475569',
                    border: showMCPTest ? 'none' : '2px solid #e2e8f0',
                    borderRadius: '16px',
                    padding: '12px 16px',
                    fontFamily: 'Poppins, sans-serif',
                    fontWeight: '600',
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1)',
                    boxShadow: showMCPTest 
                      ? '0 0 0 1px rgba(37, 99, 235, 0.1), 0 2px 4px rgba(37, 99, 235, 0.2)'
                      : '0 0 0 1px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.06)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    minWidth: '80px',
                    justifyContent: 'center'
                  }}
                  onMouseEnter={(e) => {
                    if (!showMCPTest) {
                      const target = e.target as HTMLElement;
                      target.style.background = '#f8fafc';
                      target.style.borderColor = '#cbd5e1';
                      target.style.color = '#334155';
                      target.style.transform = 'translateY(-1px)';
                      target.style.boxShadow = '0 0 0 1px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!showMCPTest) {
                      const target = e.target as HTMLElement;
                      target.style.background = 'white';
                      target.style.borderColor = '#e2e8f0';
                      target.style.color = '#475569';
                      target.style.transform = 'translateY(0)';
                      target.style.boxShadow = '0 0 0 1px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.06)';
                    }
                  }}
                >
                  <span>🔧</span>
                  <span>MCP</span>
                </button>
                <button
                  onClick={() => {
                    setShowSettings(!showSettings);
                    if (!showSettings) setShowMCPTest(false);
                  }}
                  style={{
                    background: showSettings ? '#2563eb' : 'white',
                    color: showSettings ? 'white' : '#475569',
                    border: showSettings ? 'none' : '2px solid #e2e8f0',
                    borderRadius: '16px',
                    padding: '12px 16px',
                    fontFamily: 'Poppins, sans-serif',
                    fontWeight: '600',
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1)',
                    boxShadow: showSettings 
                      ? '0 0 0 1px rgba(37, 99, 235, 0.1), 0 2px 4px rgba(37, 99, 235, 0.2)'
                      : '0 0 0 1px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.06)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    minWidth: '80px',
                    justifyContent: 'center'
                  }}
                  onMouseEnter={(e) => {
                    if (!showSettings) {
                      const target = e.target as HTMLElement;
                      target.style.background = '#f8fafc';
                      target.style.borderColor = '#cbd5e1';
                      target.style.color = '#334155';
                      target.style.transform = 'translateY(-1px)';
                      target.style.boxShadow = '0 0 0 1px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!showSettings) {
                      const target = e.target as HTMLElement;
                      target.style.background = 'white';
                      target.style.borderColor = '#e2e8f0';
                      target.style.color = '#475569';
                      target.style.transform = 'translateY(0)';
                      target.style.boxShadow = '0 0 0 1px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.06)';
                    }
                  }}
                >
                  <span>⚙️</span>
                  <span>API 설정</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 - 스크롤 가능 */}
      <main className="flex-1 overflow-y-auto">
        <div className="h-full">
          {showSettings ? (
            <LLMSettings onClose={() => setShowSettings(false)} />
          ) : showMCPTest ? (
            <MCPTestPanel />
          ) : (
            renderCurrentStep()
          )}
        </div>
      </main>
    </div>
  );
};

export default App;