import React, { useState, useEffect } from 'react';
import SimpleDialog from './SimpleDialog';

interface LLMSettingsProps {
  onClose: () => void;
}

interface LLMConfig {
  provider: string;
  model: string;
  apiKey: string;
}

interface LLMSettings {
  information: LLMConfig;
  writing: LLMConfig;
  image: LLMConfig;
}

interface ProviderApiKeys {
  anthropic: string;
  openai: string;
  google: string;
}

const LLMSettings: React.FC<LLMSettingsProps> = ({ onClose }) => {
  // 제공자별 API 키 저장소
  const [providerApiKeys, setProviderApiKeys] = useState<ProviderApiKeys>({
    anthropic: '',
    openai: '',
    google: ''
  });

  // LLM 설정 (UI에서 편집 중인 설정)
  const [settings, setSettings] = useState<LLMSettings>({
    information: { provider: 'google', model: 'gemini-2.0-flash', apiKey: '' },
    writing: { provider: 'anthropic', model: 'claude-sonnet-4-20250514', apiKey: '' },
    image: { provider: 'openai', model: 'gpt-image-1', apiKey: '' }
  });

  // 실제 적용된 설정 (테스트 성공한 설정만)
  const [appliedSettings, setAppliedSettings] = useState<LLMSettings>({
    information: { provider: '', model: '', apiKey: '' },
    writing: { provider: '', model: '', apiKey: '' },
    image: { provider: '', model: '', apiKey: '' }
  });

  const [activeTab, setActiveTab] = useState<'information' | 'writing' | 'image'>('information');
  
  // 다이얼로그 상태 관리
  const [dialog, setDialog] = useState<{
    isOpen: boolean;
    type: 'info' | 'warning' | 'error' | 'success' | 'confirm';
    title: string;
    message: string;
    onConfirm?: () => void;
  }>({
    isOpen: false,
    type: 'info',
    title: '',
    message: ''
  });
  
  // 설정 로드
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const savedData = await (window as any).electronAPI.loadSettings();
        const loadedSettings = savedData.settings || savedData;
        
        // 제공자별 API 키 추출
        const extractedKeys: ProviderApiKeys = {
          anthropic: '',
          openai: '',
          google: ''
        };
        
        // 모든 탭에서 API 키 수집
        const tabs = Object.keys(loadedSettings) as Array<keyof LLMSettings>;
        for (const tab of tabs) {
          const config = loadedSettings[tab];
          if (config.provider && config.apiKey) {
            const providerKey = config.provider as keyof ProviderApiKeys;
            if (extractedKeys[providerKey] === '') {
              extractedKeys[providerKey] = config.apiKey;
            }
          }
        }
        
        setProviderApiKeys(extractedKeys);
        
        // 설정 복원 (API 키는 제공자별 저장소에서 가져오기)
        const restoredSettings = { ...loadedSettings };
        for (const tab of tabs) {
          const config = restoredSettings[tab];
          if (config.provider) {
            const providerKey = config.provider as keyof ProviderApiKeys;
            restoredSettings[tab].apiKey = extractedKeys[providerKey] || '';
          }
        }
        
        setSettings(restoredSettings);
        
        // 테스트 성공한 설정만 appliedSettings에 저장
        const successfulSettings = { ...restoredSettings };
        for (const tab of tabs) {
          const isTestSuccessful = savedData.testingStatus?.[tab]?.success;
          if (!isTestSuccessful) {
            // 테스트 성공하지 않은 설정은 appliedSettings에서 제거
            successfulSettings[tab] = { provider: '', model: '', apiKey: '' };
          }
        }
        setAppliedSettings(successfulSettings);
        
        // 테스트 상태도 복원
        if (savedData.testingStatus) {
          setTestingStatus(savedData.testingStatus);
        }
      } catch (error) {
        // 에러 발생 시 무시 (기본값 사용)
      }
    };
    
    loadSettings();
  }, []);
  
  // API 키 테스트 상태 관리
  const [testingStatus, setTestingStatus] = useState<{
    [key: string]: {
      testing: boolean;
      success: boolean;
      message: string;
    }
  }>({});

  const providers = [
    { id: 'anthropic', name: 'Anthropic', icon: '🟠', color: 'orange' },
    { id: 'openai', name: 'OpenAI', icon: '🔵', color: 'blue' },
    { id: 'google', name: 'Google', icon: '🟢', color: 'green' }
  ];

  const modelsByProvider = {
    anthropic: {
      text: [
        { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', description: '최신 고품질 모델', tier: 'premium' },
        { id: 'claude-opus-4-1-20250805', name: 'Claude Opus 4.1', description: '최고품질 모델', tier: 'premium' },
        { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', description: '빠르고 경제적', tier: 'basic' }
      ]
    },
    openai: {
      text: [
        { id: 'gpt-5', name: 'GPT-5', description: '최고 성능 모델', tier: 'enterprise' },
        { id: 'gpt-5-mini', name: 'GPT-5 Mini', description: '균형잡힌 성능', tier: 'premium' },
        { id: 'gpt-5-nano', name: 'GPT-5 Nano', description: '빠르고 경제적', tier: 'basic' }
      ],
      image: [
        { id: 'gpt-image-1', name: 'GPT Image 1', description: '최고품질 이미지 생성', tier: 'enterprise' }
      ]
    },
    google: {
      text: [
        { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', description: '최고성능 모델', tier: 'premium' },
        { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', description: '경제적 모델', tier: 'basic' }
      ],
      image: [
        { id: 'gemini-2.5-flash-image-preview', name: 'Gemini 2.5 Flash Image', description: '이미지 생성 및 편집', tier: 'enterprise' }
      ]
    }
  };

  const updateSetting = (category: keyof LLMSettings, field: keyof LLMConfig, value: string) => {
    if (field === 'provider') {
      // 제공자 변경 시
      setSettings(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          provider: value,
          apiKey: value ? (providerApiKeys[value as keyof ProviderApiKeys] || '') : ''
        }
      }));
    } else if (field === 'apiKey') {
      // API 키 변경 시 - 제공자별 저장소에도 업데이트
      const provider = settings[category].provider;
      if (provider) {
        setProviderApiKeys(prev => ({
          ...prev,
          [provider as keyof ProviderApiKeys]: value
        }));
      }
      
      setSettings(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          apiKey: value
        }
      }));
    } else {
      // 기타 필드 (모델 등)
      setSettings(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          [field]: value
        }
      }));
    }
    
    // API 키, 제공자, 모델이 변경되면 테스트 상태 초기화
    if (field === 'apiKey' || field === 'provider' || field === 'model') {
      setTestingStatus(prev => ({
        ...prev,
        [category]: { testing: false, success: false, message: '' }
      }));
    }
  };

  // API 키 테스트 함수
  const testApiKey = async (category: keyof LLMSettings) => {
    const { provider, apiKey, model } = settings[category];
    
    if (!apiKey || !provider || !model) {
      setTestingStatus(prev => ({
        ...prev,
        [category]: { testing: false, success: false, message: '❌ 제공자, 모델, API 키를 모두 입력해주세요.' }
      }));
      return;
    }

    // 테스트 시작
    setTestingStatus(prev => ({
      ...prev,
      [category]: { testing: true, success: false, message: '연결 테스트 중...' }
    }));

    try {
      // 실제 API 테스트
      const result = await testAPIConnection(provider, apiKey);
      
      if (result.success) {
        // 성공
        setTestingStatus(prev => ({
          ...prev,
          [category]: { 
            testing: false, 
            success: true, 
            message: `✅ ${provider.toUpperCase()} API 연결 성공! ${model} 모델이 적용되었습니다.` 
          }
        }));
        
        // 테스트 성공 시 appliedSettings 업데이트 및 저장
        try {
          // 테스트 성공한 설정을 appliedSettings에 반영
          const newAppliedSettings = {
            ...appliedSettings,
            [category]: settings[category]
          };
          setAppliedSettings(newAppliedSettings);
          
          // 성공한 테스트 상태도 업데이트
          const newTestingStatus = {
            ...testingStatus,
            [category]: { 
              testing: false, 
              success: true, 
              message: `✅ ${provider.toUpperCase()} API 연결 성공! ${model} 모델이 적용되었습니다.` 
            }
          };
          
          // 설정과 테스트 상태를 함께 저장
          const dataToSave = {
            settings: settings,
            testingStatus: newTestingStatus
          };
          
          const result = await (window as any).electronAPI.saveSettings(dataToSave);
          if (!result.success) {
            console.error('❌ 자동 저장 실패:', result.message);
          }
        } catch (error) {
          console.error('❌ 자동 저장 중 오류:', error);
        }
        
      } else {
        // 실패
        setTestingStatus(prev => ({
          ...prev,
          [category]: { 
            testing: false, 
            success: false, 
            message: `❌ 연결 실패: ${result.message}` 
          }
        }));
      }
    } catch (error: any) {
      // 에러
      console.error('API 테스트 에러:', error);
      setTestingStatus(prev => ({
        ...prev,
        [category]: { 
          testing: false, 
          success: false, 
          message: `❌ 연결 테스트 중 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}` 
        }
      }));
    }
  };

  // 실제 API 연결 테스트 (Electron IPC 사용)
  const testAPIConnection = async (provider: string, apiKey: string): Promise<{success: boolean, message: string}> => {
    console.log(`🔍 Testing ${provider} API with key: ${apiKey.substring(0, 10)}...`);
    
    try {
      // Electron IPC를 통해 Main process에서 API 테스트 실행
      const result = await (window as any).electronAPI.testAPI(provider, apiKey);
      
      console.log(`📡 ${provider} API 테스트 결과:`, result);
      return result;
      
    } catch (error: any) {
      console.error(`❌ ${provider} API 테스트 실패:`, error);
      
      if (error instanceof Error) {
        return { success: false, message: `연결 오류: ${error.message}` };
      }
      
      return { success: false, message: `연결 테스트 실패: ${String(error)}` };
    }
  };

  // API 키 삭제 함수
  const deleteApiKey = async (category: keyof LLMSettings) => {
    const { provider } = settings[category];
    
    if (!provider) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '삭제 불가',
        message: '삭제할 API 키가 없습니다.'
      });
      return;
    }

    // 사용자 확인 다이얼로그
    setDialog({
      isOpen: true,
      type: 'confirm',
      title: 'API 키 삭제',
      message: `${provider.toUpperCase()} API 키를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, 모든 탭에서 해당 제공자의 API 키가 제거됩니다.`,
      onConfirm: () => performDeleteApiKey(category, provider)
    });
  };

  // 실제 API 키 삭제 수행
  const performDeleteApiKey = async (category: keyof LLMSettings, provider: string) => {
    try {
      // 1. 제공자별 저장소에서 해당 제공자의 API 키 제거
      setProviderApiKeys(prev => ({
        ...prev,
        [provider as keyof ProviderApiKeys]: ''
      }));

      // 2. 편집 중인 설정에서 해당 제공자의 모든 API 키 제거
      const newSettings = { ...settings };
      Object.keys(newSettings).forEach(tab => {
        const tabKey = tab as keyof LLMSettings;
        if (newSettings[tabKey].provider === provider) {
          newSettings[tabKey].apiKey = '';
        }
      });
      setSettings(newSettings);

      // 3. 적용된 설정에서도 해당 제공자의 모든 설정 완전 제거 (빈 상태로)
      const newAppliedSettings = { ...appliedSettings };
      Object.keys(newAppliedSettings).forEach(tab => {
        const tabKey = tab as keyof LLMSettings;
        if (newAppliedSettings[tabKey].provider === provider) {
          newAppliedSettings[tabKey] = { provider: '', model: '', apiKey: '' };
        }
      });
      setAppliedSettings(newAppliedSettings);

      // 4. 테스트 상태에서도 해당 제공자의 모든 상태 제거
      const newTestingStatus = { ...testingStatus };
      Object.keys(newTestingStatus).forEach(tab => {
        const tabKey = tab as keyof LLMSettings;
        if (settings[tabKey].provider === provider) {
          delete newTestingStatus[tabKey];
        }
      });
      setTestingStatus(newTestingStatus);

      // 4. 파일에도 저장
      const dataToSave = {
        settings: newSettings,
        testingStatus: newTestingStatus
      };
      
      const result = await (window as any).electronAPI.saveSettings(dataToSave);
      if (result.success) {
        setDialog({
          isOpen: true,
          type: 'success',
          title: '삭제 완료',
          message: `${provider.toUpperCase()} API 키가 성공적으로 삭제되었습니다.`
        });
      } else {
        console.error('❌ 삭제 후 저장 실패:', result.message);
        setDialog({
          isOpen: true,
          type: 'error',
          title: '저장 실패',
          message: `API 키는 삭제되었지만 저장에 실패했습니다:\n${result.message}`
        });
      }
    } catch (error: any) {
      console.error('❌ API 키 삭제 중 오류:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '삭제 오류',
        message: `API 키 삭제 중 오류가 발생했습니다:\n${error.message}`
      });
    }
  };

  const saveSettings = async () => {
    try {
      console.log('💾 설정 저장 시도:', settings);
      
      // 설정과 테스트 상태를 함께 저장
      const dataToSave = {
        settings: settings,
        testingStatus: testingStatus
      };
      
      const result = await (window as any).electronAPI.saveSettings(dataToSave);
      console.log('💾 저장 결과:', result);
      
      if (result.success) {
        setDialog({
          isOpen: true,
          type: 'success',
          title: '저장 완료',
          message: '설정이 성공적으로 저장되었습니다.',
          onConfirm: () => onClose()
        });
      } else {
        console.error('❌ 저장 실패:', result.message);
        setDialog({
          isOpen: true,
          type: 'error',
          title: '저장 실패',
          message: `설정 저장에 실패했습니다:\n${result.message}`
        });
      }
    } catch (error: any) {
      console.error('❌ 설정 저장 오류:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '저장 오류',
        message: `설정 저장 중 오류가 발생했습니다:\n${error.message}`
      });
    }
  };

  const tabs = [
    { id: 'information', name: '🔍 정보처리 LLM', desc: '키워드 추천, 데이터 수집, 요약 등' },
    { id: 'writing', name: '✍️ 글쓰기 LLM', desc: '최종 콘텐츠 생성 (가장 중요!)' },
    { id: 'image', name: '🎨 이미지 LLM', desc: '글 내용 기반 이미지 생성' }
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-4">
      <div className="ultra-card p-6 slide-in">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <div className="section-icon blue" style={{width: '40px', height: '40px', fontSize: '20px'}}>⚙️</div>
            <h2 className="text-2xl font-bold text-slate-900">LLM 설정</h2>
          </div>
        </div>

              {/* 탭 네비게이션 */}
              <div className="flex gap-3 mb-8">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex-1 section-card cursor-pointer transition-all duration-200 ${
                      activeTab === tab.id
                        ? 'ring-2 ring-blue-500 ring-offset-2 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200'
                        : 'hover:shadow-lg hover:-translate-y-0.5'
                    }`}
                    style={{
                      padding: '20px 16px',
                      marginBottom: '0',
                      background: activeTab === tab.id 
                        ? 'linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%)' 
                        : 'white'
                    }}
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className="text-3xl">
                        {tab.name.split(' ')[0]}
                      </div>
                      <div className="text-center">
                        <div className={`font-semibold text-sm ${
                          activeTab === tab.id ? 'text-blue-900' : 'text-slate-900'
                        }`}>
                          {tab.name.split(' ')[1]} {tab.name.split(' ')[2]}
                        </div>
                        <div className={`text-xs mt-1 ${
                          activeTab === tab.id ? 'text-blue-600' : 'text-slate-500'
                        }`}>
                          {tab.desc}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* 설정 내용 */}
              <div className="section-card" style={{padding: '20px', marginBottom: '24px'}}>
                <div className="space-y-6">
                  {/* 1단계: 제공자 선택 */}
                  <div>
                    <label className="ultra-label" style={{fontSize: '13px', marginBottom: '8px'}}>
                      1단계: AI 제공자 선택
                    </label>
                    <select
                      value={settings[activeTab].provider}
                      onChange={(e) => {
                        updateSetting(activeTab, 'provider', e.target.value);
                        updateSetting(activeTab, 'model', ''); // 모델 초기화
                      }}
                      className="ultra-select w-full" style={{padding: '12px 16px', fontSize: '14px'}}
                    >
                      <option value="">제공자를 선택해주세요</option>
                      {providers
                        .filter(provider => {
                          // 이미지 탭에서는 Claude 제외 (이미지 생성 불가)
                          if (activeTab === 'image' && provider.id === 'anthropic') {
                            return false;
                          }
                          return true;
                        })
                        .map((provider) => (
                          <option key={provider.id} value={provider.id}>
                            {provider.icon} {provider.name}
                          </option>
                        ))}
                    </select>
                  </div>

                  {/* 2단계: 모델 선택 */}
                  {settings[activeTab].provider && (
                    <div>
                      <label className="ultra-label" style={{fontSize: '13px', marginBottom: '8px'}}>
                        2단계: 모델 선택
                      </label>
                      <select
                        value={settings[activeTab].model}
                        onChange={(e) => updateSetting(activeTab, 'model', e.target.value)}
                        className="ultra-select w-full" style={{padding: '12px 16px', fontSize: '14px'}}
                      >
                        <option value="">모델을 선택해주세요</option>
                        {(() => {
                          const provider = settings[activeTab].provider;
                          const modelType = activeTab === 'image' ? 'image' : 'text';
                          const models = (modelsByProvider as any)[provider]?.[modelType] || [];
                          
                          return models.map((model: any) => (
                            <option key={model.id} value={model.id}>
                              {model.name} - {model.description} ({model.tier})
                            </option>
                          ));
                        })()}
                      </select>
                    </div>
                  )}

                  {/* 3단계: API 키 입력 */}
                  {settings[activeTab].provider && (
                    <div>
                      <label className="ultra-label" style={{fontSize: '13px', marginBottom: '8px'}}>
                        3단계: API 키 입력
                      </label>
                      <div className="flex gap-3">
                        <input
                          type="password"
                          value={settings[activeTab].apiKey}
                          onChange={(e) => updateSetting(activeTab, 'apiKey', e.target.value)}
                          placeholder={`${settings[activeTab].provider.toUpperCase()} API 키를 입력하세요`}
                          className="ultra-input flex-1" style={{padding: '12px 16px', fontSize: '14px'}}
                        />
                        <button
                          onClick={() => testApiKey(activeTab)}
                          disabled={!settings[activeTab].apiKey || testingStatus[activeTab]?.testing || testingStatus[activeTab]?.success}
                          className={`ultra-btn ${
                            !settings[activeTab].apiKey || testingStatus[activeTab]?.testing || testingStatus[activeTab]?.success
                              ? 'opacity-50 cursor-not-allowed'
                              : ''
                          } px-6 py-3 text-sm whitespace-nowrap`}
                        >
                          <span>{testingStatus[activeTab]?.testing ? '테스트 중...' : testingStatus[activeTab]?.success ? '적용 완료' : '테스트 및 적용'}</span>
                          <span className="text-lg">{testingStatus[activeTab]?.testing ? '🔄' : testingStatus[activeTab]?.success ? '✅' : '🔧'}</span>
                        </button>
                        {/* API 키 삭제 버튼 */}
                        <button
                            onClick={() => deleteApiKey(activeTab)}
                            disabled={testingStatus[activeTab]?.testing || !settings[activeTab].apiKey}
                            className={`text-sm whitespace-nowrap ${
                              testingStatus[activeTab]?.testing || !settings[activeTab].apiKey
                                ? 'opacity-50 cursor-not-allowed'
                                : ''
                            }`}
                            style={{
                              background: (testingStatus[activeTab]?.testing || !settings[activeTab].apiKey) ? '#f1f5f9' : '#ef4444',
                              color: (testingStatus[activeTab]?.testing || !settings[activeTab].apiKey) ? '#94a3b8' : 'white',
                              border: (testingStatus[activeTab]?.testing || !settings[activeTab].apiKey) ? '2px solid #e2e8f0' : 'none',
                              borderRadius: '16px',
                              padding: '12px 16px',
                              fontFamily: 'Poppins, sans-serif',
                              fontWeight: '600',
                              cursor: (testingStatus[activeTab]?.testing || !settings[activeTab].apiKey) ? 'not-allowed' : 'pointer',
                              transition: 'all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1)',
                              outline: 'none',
                              boxShadow: (testingStatus[activeTab]?.testing || !settings[activeTab].apiKey)
                                ? '0 0 0 1px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.06)'
                                : '0 0 0 1px rgba(239, 68, 68, 0.1), 0 2px 4px rgba(239, 68, 68, 0.2)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              minWidth: '80px',
                              justifyContent: 'center'
                            }}
                            onMouseEnter={(e) => {
                              if (!testingStatus[activeTab]?.testing && settings[activeTab].apiKey) {
                                const target = e.target as HTMLElement;
                                target.style.background = '#dc2626';
                                target.style.color = 'white';
                                target.style.transform = 'translateY(-1px)';
                                target.style.boxShadow = '0 0 0 1px rgba(220, 38, 38, 0.1), 0 4px 12px rgba(220, 38, 38, 0.25)';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (!testingStatus[activeTab]?.testing && settings[activeTab].apiKey) {
                                const target = e.target as HTMLElement;
                                target.style.background = '#ef4444';
                                target.style.color = 'white';
                                target.style.transform = 'translateY(0)';
                                target.style.boxShadow = '0 0 0 1px rgba(239, 68, 68, 0.1), 0 2px 4px rgba(239, 68, 68, 0.2)';
                              }
                            }}
                          >
                            <span>삭제</span>
                            <span className="text-lg">🗑️</span>
                          </button>
                      </div>
                      
                      <p className="text-xs text-slate-500 mt-2">
                        API 키는 안전하게 암호화되어 로컬에만 저장됩니다.
                      </p>
                    </div>
                  )}

                  {/* 현재 설정 요약 */}
                  {appliedSettings[activeTab].provider && (
                    <div className="p-4 bg-slate-50 rounded-xl">
                      <h4 className="font-semibold text-sm text-slate-900 mb-3">현재 적용된 설정</h4>
                      <div className="grid grid-cols-4 gap-4 text-xs">
                        <div>
                          <span className="text-slate-600 block mb-1">제공자</span>
                          <span className="font-semibold">{appliedSettings[activeTab].provider.toUpperCase()}</span>
                        </div>
                        <div>
                          <span className="text-slate-600 block mb-1">모델</span>
                          <span className="font-semibold">{appliedSettings[activeTab].model || '미선택'}</span>
                        </div>
                        <div>
                          <span className="text-slate-600 block mb-1">API 키</span>
                          <div className={`flex items-center gap-1 font-semibold ${appliedSettings[activeTab].apiKey ? 'text-green-600' : 'text-red-500'}`}>
                            {appliedSettings[activeTab].apiKey ? <>🔑 설정됨</> : <>🔒 미설정</>}
                          </div>
                        </div>
                        <div>
                          <span className="text-slate-600 block mb-1">연결 상태</span>
                          <div className={`flex items-center gap-1 font-semibold ${
                            testingStatus[activeTab]?.success 
                              ? 'text-green-600' 
                              : testingStatus[activeTab]?.message && !testingStatus[activeTab]?.success
                              ? 'text-red-500'
                              : 'text-slate-500'
                          }`}>
                            {testingStatus[activeTab]?.testing 
                              ? <>🔄 테스트 중...</>
                              : testingStatus[activeTab]?.success 
                              ? <>✅ 연결됨</>
                              : testingStatus[activeTab]?.message && !testingStatus[activeTab]?.success
                              ? <>❌ 연결 실패</>
                              : <>⚪ 미확인</>}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

        {/* 버튼들 */}
        <div className="flex justify-end gap-3 pt-4">
          <button
            onClick={onClose}
            className="ultra-btn px-8 py-3 text-base"
            style={{
              background: '#64748b',
              borderColor: '#64748b'
            }}
          >
            <span>닫기</span>
            <span className="text-lg">✕</span>
          </button>
          <button
            onClick={saveSettings}
            className="ultra-btn px-8 py-3 text-base"
            style={{
              background: '#10b981',
              borderColor: '#10b981'
            }}
          >
            <span>저장</span>
            <span className="text-lg">✓</span>
          </button>
        </div>
      </div>

      {/* 다이얼로그 */}
      <SimpleDialog
        isOpen={dialog.isOpen}
        onClose={() => setDialog(prev => ({ ...prev, isOpen: false }))}
        title={dialog.title}
        message={dialog.message}
        onConfirm={dialog.onConfirm}
        confirmText={dialog.type === 'confirm' ? '삭제' : '확인'}
        cancelText="취소"
      />
    </div>
  );
};

export default LLMSettings;