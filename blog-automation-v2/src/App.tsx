import React, { useState } from 'react';
import './index.css';

// 3단계 워크플로우 컴포넌트들
import Step1 from './components/Step1';
import Step2 from './components/Step2';
import Step3 from './components/Step3';
import LLMSettings from './components/LLMSettings';

// Context 제거 - 직접 상태 관리 사용

import { BlogWritingResult } from './services/blog-writing-service';
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
  bloggerIdentity?: string; // 블로거 정체성
  selectedTitle: string;
  generatedTitles?: string[]; // 생성된 제목들
  titlesWithSearch?: { title: string; searchQuery: string }[]; // 제목과 검색어
  collectedData: unknown;
  writingResult?: BlogWritingResult; // 글쓰기 결과
  generatedContent: string;
}

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [isBackFromStep2, setIsBackFromStep2] = useState(false);
  
  // 직접 AI 모델 상태 관리
  const [aiModelStatus, setAiModelStatus] = useState({
    information: '미설정',
    writing: '미설정',
    image: '미설정'
  });

  // 모델 상태 새로고침 함수
  const refreshModelStatus = React.useCallback(() => {
    try {
      const status = LLMClientFactory.getCachedModelStatus();
      setAiModelStatus(status);
    } catch (error) {
      console.error('모델 상태 확인 실패:', error);
    }
  }, []);

  // 초기화 및 상태 확인 (한번만 실행)
  React.useEffect(() => {
    let isInitialized = false;
    
    const initializeAndRefresh = async () => {
      if (isInitialized) return;
      isInitialized = true;
      
      try {
        await LLMClientFactory.loadDefaultSettings();
        // 로드 완료 후 상태 새로고침
        refreshModelStatus();
      } catch (error) {
        console.error('초기화 실패:', error);
      }
    };

    initializeAndRefresh();
  }, []); // 빈 의존성 배열로 한번만 실행
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
    generatedTitles: [],
    titlesWithSearch: [],
    collectedData: null,
    generatedContent: ''
  });

  // 초기화 로직은 모두 AppInitContext로 이동

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
              setIsBackFromStep2(false); // Step1에서 다음으로 갈 때는 리셋
              setCurrentStep(2);
            }}
            isBackFromStep2={isBackFromStep2}
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
            onBack={() => {
              setIsBackFromStep2(true); // Step2에서 돌아갈 때 플래그 설정
              setCurrentStep(1);
            }}
            aiModelStatus={aiModelStatus}
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
              <div className="flex flex-col">
                <h1 className="text-xl font-bold text-slate-900">
                  AI 블로그 자동화 V2
                </h1>
                <div className="flex items-center gap-4 text-xs text-slate-600 mt-1">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    <span>정보처리: {aiModelStatus.information}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    <span>글쓰기: {aiModelStatus.writing}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                    <span>이미지: {aiModelStatus.image}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowSettings(!showSettings);
                    // API 설정 화면 진입 시 스크롤을 최상단으로 이동
                    if (!showSettings) {
                      setTimeout(() => {
                        const mainElement = document.querySelector('main');
                        if (mainElement) {
                          mainElement.scrollTo({ top: 0, behavior: 'smooth' });
                        } else {
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }
                      }, 100);
                    }
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
            <LLMSettings 
              onClose={() => {
                setShowSettings(false);
                setIsBackFromStep2(false); // API 설정에서 나올 때 Step1 스크롤 플래그 리셋
                // 설정 변경 후 상태만 새로고침
                refreshModelStatus();
              }}
              onSettingsChange={refreshModelStatus} // 설정 변경 시 실시간 업데이트
            />
          ) : (
            renderCurrentStep()
          )}
        </div>
      </main>
    </div>
  );
};

export default App;