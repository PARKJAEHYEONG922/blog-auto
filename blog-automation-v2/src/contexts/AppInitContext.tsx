import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { LLMClientFactory } from '../services/llm-client-factory';

// 전역 초기화 상태 (React 외부에서 관리)
let globalInitState = {
  isInitialized: false,
  isInitializing: false
};

interface AppInitContextType {
  isInitialized: boolean;
  isInitializing: boolean;
  aiModelStatus: {
    information: string;
    writing: string;
    image: string;
  };
  refreshModelStatus: () => void;
}

const AppInitContext = createContext<AppInitContextType | undefined>(undefined);

export const useAppInit = () => {
  const context = useContext(AppInitContext);
  if (context === undefined) {
    throw new Error('useAppInit must be used within an AppInitProvider');
  }
  return context;
};

interface AppInitProviderProps {
  children: ReactNode;
}

export const AppInitProvider: React.FC<AppInitProviderProps> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(globalInitState.isInitialized);
  const [isInitializing, setIsInitializing] = useState(globalInitState.isInitializing);
  const [aiModelStatus, setAiModelStatus] = useState({
    information: '미설정',
    writing: '미설정',
    image: '미설정'
  });

  const refreshModelStatus = () => {
    try {
      const status = LLMClientFactory.getCachedModelStatus();
      setAiModelStatus(status);
    } catch (error) {
      console.error('AI 모델 상태 확인 실패:', error);
    }
  };

  // 전역적으로 한 번만 실행되는 초기화 (React 외부 상태로 완전 차단)
  useEffect(() => {
    let isMounted = true;

    const initializeApp = async () => {
      // 전역 상태로 중복 실행 완전 차단
      if (globalInitState.isInitializing || globalInitState.isInitialized) {
        console.log('⏭️ 전역 초기화 이미 진행됨, 스킵');
        // 기존 상태를 React 상태에 동기화
        setIsInitialized(globalInitState.isInitialized);
        setIsInitializing(globalInitState.isInitializing);
        if (globalInitState.isInitialized) {
          refreshModelStatus();
        }
        return;
      }

      // 전역 상태 업데이트
      globalInitState.isInitializing = true;
      setIsInitializing(true);

      try {
        console.log('🚀 앱 전역 초기화 시작');
        
        // LLM 설정 로드 (전역적으로 한 번만)
        await LLMClientFactory.loadDefaultSettings();
        
        if (!isMounted) return;

        console.log('✅ LLM 설정 로드 완료');
        
        // AI 모델 상태 업데이트
        refreshModelStatus();
        console.log('✅ AI 모델 상태 확인 완료');
        
        // 전역 상태 업데이트
        globalInitState.isInitialized = true;
        globalInitState.isInitializing = false;
        setIsInitialized(true);
        setIsInitializing(false);
        
        console.log('🎉 앱 전역 초기화 완료');
        
      } catch (error) {
        if (isMounted) {
          console.error('❌ 앱 초기화 중 오류:', error);
          globalInitState.isInitializing = false;
          setIsInitializing(false);
        }
      }
    };

    initializeApp();

    return () => {
      isMounted = false;
    };
  }, []); // 빈 의존성 배열로 한 번만 실행

  return (
    <AppInitContext.Provider
      value={{
        isInitialized,
        isInitializing,
        aiModelStatus,
        refreshModelStatus
      }}
    >
      {children}
    </AppInitContext.Provider>
  );
};