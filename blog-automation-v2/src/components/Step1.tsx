import React, { useState, useEffect } from 'react';
import { WorkflowData } from '../App';
import Dropdown, { DropdownOption } from './common/Dropdown';
import SimpleDialog from './SimpleDialog';
import { TitleWithSearch } from '../services/title-generation-engine';

interface Step1Props {
  data: WorkflowData;
  onNext: (data: Partial<WorkflowData>) => void;
}

const Step1: React.FC<Step1Props> = ({ data, onNext }) => {
  const [platform, setPlatform] = useState(data.platform || '');
  const [keyword, setKeyword] = useState(data.keyword || '');
  const [subKeywords, setSubKeywords] = useState(data.subKeywords?.join(', ') || '');
  const [contentType, setContentType] = useState(data.contentType || '');
  const [reviewType, setReviewType] = useState(data.reviewType || '');
  const [tone, setTone] = useState(data.tone || '');
  const [customPrompt, setCustomPrompt] = useState(data.customPrompt || '');
  const [blogDescription, setBlogDescription] = useState(
    data.blogDescription || '당신은 네이버 블로그에서 인기 있는 글을 쓰는 블로거입니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다.'
  );
  // 더미 데이터 추가 (테스트용)
  const dummyTitlesWithSearch: TitleWithSearch[] = [
    { title: "블로그 마케팅 완벽 가이드 - 초보자도 쉽게 시작하는 방법", searchQuery: "블로그 마케팅 초보자 가이드" },
    { title: "블로그 마케팅으로 월 100만원 수익 올리는 실전 노하우", searchQuery: "블로그 수익화 노하우" },
    { title: "블로그 마케팅 성공 사례 분석 - 실제 후기와 팁", searchQuery: "블로그 마케팅 성공사례" },
    { title: "블로그 마케팅 도구 추천 TOP 10 - 효과적인 운영법", searchQuery: "블로그 마케팅 도구 추천" },
    { title: "블로그 마케팅 전략 수립부터 실행까지 단계별 가이드", searchQuery: "블로그 마케팅 전략 가이드" }
  ];

  const [generatedTitles, setGeneratedTitles] = useState<string[]>(
    data.generatedTitles?.length ? data.generatedTitles : dummyTitlesWithSearch.map(item => item.title)
  );
  const [titlesWithSearch, setTitlesWithSearch] = useState<TitleWithSearch[]>(
    data.titlesWithSearch?.length ? data.titlesWithSearch : dummyTitlesWithSearch
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedTitle, setSelectedTitle] = useState(data.selectedTitle || '');
  const [isSavingDefaults, setIsSavingDefaults] = useState(false);
  
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

  const platforms: DropdownOption[] = [
    { id: 'naver', name: '네이버 블로그', icon: '🟢' },
    { id: 'tistory', name: '티스토리', icon: '📝' },
    { id: 'blogspot', name: '블로그스팟', icon: '🌐' },
    { id: 'wordpress', name: '워드프레스', icon: '📰' }
  ];

  const contentTypes: DropdownOption[] = [
    { id: 'info', name: '정보/가이드형', icon: '📚', description: '정확한 정보를 체계적으로 제공하여 궁금증 해결' },
    { id: 'review', name: '후기/리뷰형', icon: '⭐', description: '개인 경험과 솔직한 후기로 유일무이한 콘텐츠 작성' },
    { id: 'compare', name: '비교/추천형', icon: '⚖️', description: '체계적 비교분석으로 독자의 선택 고민 해결' },
    { id: 'howto', name: '노하우형', icon: '🛠️', description: '실용적 방법론과 단계별 가이드 제공' }
  ];

  const reviewTypes: DropdownOption[] = [
    { id: 'self-purchase', name: '내돈내산 후기', icon: '💳', description: '직접 구매해서 써본 솔직한 개인 후기' },
    { id: 'sponsored', name: '협찬 후기', icon: '🤝', description: '브랜드에서 제공받은 제품의 정직한 리뷰' },
    { id: 'experience', name: '체험단 후기', icon: '🎁', description: '체험단 참여를 통한 제품 사용 후기' },
    { id: 'rental', name: '대여/렌탈 후기', icon: '📅', description: '렌탈 서비스를 이용한 제품 사용 후기' }
  ];

  const tones: DropdownOption[] = [
    { id: 'formal', name: '정중한 존댓말', icon: '🎩', description: '사용해보았습니다, 추천드립니다 (신뢰감 조성)' },
    { id: 'casual', name: '친근한 반말', icon: '😊', description: '써봤는데 진짜 좋더라, 완전 강추! (편안하고 친근한)' },
    { id: 'friendly', name: '친근한 존댓말', icon: '🤝', description: '써봤는데 좋더라구요, 도움이 될 것 같아요 (따뜻한 느낌)' }
  ];


  // 기본 설정 로드
  useEffect(() => {
    const loadDefaults = async () => {
      try {
        const savedDefaults = await (window as any).electronAPI.loadDefaults();
        if (savedDefaults) {
          if (savedDefaults.platform && !data.platform) setPlatform(savedDefaults.platform);
          if (savedDefaults.contentType && !data.contentType) setContentType(savedDefaults.contentType);
          if (savedDefaults.reviewType && !data.reviewType) setReviewType(savedDefaults.reviewType);
          if (savedDefaults.tone && !data.tone) setTone(savedDefaults.tone);
          if (savedDefaults.blogDescription && !data.blogDescription) setBlogDescription(savedDefaults.blogDescription);
        }
      } catch (error) {
        console.log('기본 설정 로드 실패:', error);
      }
    };
    
    loadDefaults();
  }, []);

  const generateTitles = async () => {
    if (!keyword.trim()) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '키워드 필요',
        message: '키워드를 입력해주세요.'
      });
      return;
    }

    setIsGenerating(true);
    try {
      // 실제 MCP + LLM 연동
      const { TitleGenerationEngine } = await import('../services/title-generation-engine');
      const engine = new TitleGenerationEngine();

      // 선택된 옵션의 한국어 이름 찾기
      const platformName = platforms.find(p => p.id === platform)?.name || platform;
      const contentTypeName = contentTypes.find(c => c.id === contentType)?.name || contentType;
      const reviewTypeName = reviewType ? reviewTypes.find(r => r.id === reviewType)?.name || reviewType : undefined;

      const result = await engine.generateTitles({
        keyword: keyword.trim(),
        subKeywords: subKeywords.split(',').map(k => k.trim()).filter(k => k),
        platform,
        platformName,
        contentType,
        contentTypeName,
        reviewType,
        reviewTypeName,
        tone,
        customPrompt: customPrompt.trim(),
        blogDescription: blogDescription.trim(),
        mode: 'fast'
      });

      setGeneratedTitles(result.titles);
      setTitlesWithSearch(result.titlesWithSearch);
      console.log('제목 생성 메타데이터:', result.metadata);
      console.log('제목과 검색어:', result.titlesWithSearch);
    } catch (error) {
      console.error('제목 생성 오류:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '제목 생성 오류',
        message: `제목 생성 중 오류가 발생했습니다:\n${error.message || error}`
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const saveDefaults = async () => {
    // 필수 항목 검증
    if (!platform || !contentType || !tone) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '저장 불가',
        message: '발행 플랫폼, 콘텐츠 타입, 말투 스타일을 모두 선택해주세요.'
      });
      return;
    }
    
    // 후기형인 경우 후기 유형도 필수
    if (contentType === 'review' && !reviewType) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '저장 불가',
        message: '후기형을 선택했을 때는 후기 유형도 선택해주세요.'
      });
      return;
    }
    
    setIsSavingDefaults(true);
    try {
      // Electron API 존재 여부 확인
      if (!(window as any).electronAPI) {
        throw new Error('Electron API가 초기화되지 않았습니다. 앱을 재시작해주세요.');
      }
      
      if (typeof (window as any).electronAPI.saveDefaults !== 'function') {
        throw new Error('saveDefaults 함수를 찾을 수 없습니다. 앱을 재시작해주세요.');
      }
      
      const defaultSettings = {
        platform,
        contentType,
        reviewType,
        tone,
        blogDescription: blogDescription.trim()
      };
      
      console.log('저장할 기본 설정:', defaultSettings);
      
      const result = await (window as any).electronAPI.saveDefaults(defaultSettings);
      console.log('저장 결과:', result);
      
      if (result && result.success) {
        // 선택된 설정 정보 구성
        const platformName = platforms.find(p => p.id === platform)?.name || platform;
        const contentTypeName = contentTypes.find(c => c.id === contentType)?.name || contentType;
        const reviewTypeName = reviewType ? reviewTypes.find(r => r.id === reviewType)?.name || reviewType : '';
        const toneName = tones.find(t => t.id === tone)?.name || tone;
        
        let settingsInfo = `발행 플랫폼: ${platformName}\n콘텐츠 타입: ${contentTypeName}`;
        if (reviewType) {
          settingsInfo += `\n후기 유형: ${reviewTypeName}`;
        }
        settingsInfo += `\n말투 스타일: ${toneName}`;
        
        setDialog({
          isOpen: true,
          type: 'success',
          title: '저장 완료',
          message: `기본 설정이 성공적으로 저장되었습니다!\n\n${settingsInfo}`
        });
      } else {
        console.error('저장 실패 상세:', result);
        setDialog({
          isOpen: true,
          type: 'error',
          title: '저장 실패',
          message: `기본 설정 저장에 실패했습니다:\n${result?.message || '알 수 없는 오류'}`
        });
      }
    } catch (error) {
      console.error('기본 설정 저장 오류:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '저장 오류',
        message: `기본 설정 저장 중 오류가 발생했습니다:\n${error.message || error}`
      });
    } finally {
      setIsSavingDefaults(false);
    }
  };

  const handleNext = () => {
    if (!platform || !keyword.trim() || !selectedTitle) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '필수 항목 누락',
        message: '발행 플랫폼, 메인 키워드, 선택된 제목을 모두 입력해주세요.'
      });
      return;
    }

    // 선택된 옵션의 상세 설명 찾기
    const contentTypeDescription = contentTypes.find(c => c.id === contentType)?.description || '';
    const reviewTypeDescription = reviewType ? reviewTypes.find(r => r.id === reviewType)?.description || '' : '';
    const toneDescription = tones.find(t => t.id === tone)?.description || '';

    onNext({
      platform,
      keyword: keyword.trim(),
      subKeywords: subKeywords.split(',').map(k => k.trim()).filter(k => k),
      contentType,
      contentTypeDescription,
      reviewType,
      reviewTypeDescription,
      tone,
      toneDescription,
      customPrompt: customPrompt.trim(),
      blogDescription: blogDescription.trim(),
      selectedTitle,
      generatedTitles, // 생성된 제목들 저장
      titlesWithSearch // 제목과 검색어 저장
    });
  };

  return (
    <div className="w-full h-full">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="ultra-card p-5 slide-in">
        {/* 헤더 */}
        <div className="text-center mb-4">
          <div className="inline-flex items-center gap-3 mb-3">
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <span>📝</span>
              <span>콘텐츠 기획</span>
            </h1>
          </div>
          <p className="text-base text-slate-600 leading-relaxed max-w-2xl mx-auto">
            플랫폼을 선택하고 키워드를 입력하여 AI가 최적의 제목을 추천받으세요.
          </p>
        </div>

        <div className="space-y-4">
          {/* 기본 설정 섹션 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon blue" style={{width: '32px', height: '32px', fontSize: '16px'}}>⚙️</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>기본 설정</h2>
            </div>
            
            <div className="grid md:grid-cols-1 gap-4">
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                  발행 플랫폼 <span className="text-red-500">*</span>
                </label>
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="ultra-select" style={{padding: '10px 16px', fontSize: '14px'}}
                >
                  <option value="">플랫폼을 선택해주세요</option>
                  {platforms.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.icon} {option.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>콘텐츠 타입</label>
                <select
                  value={contentType}
                  onChange={(e) => {
                    setContentType(e.target.value);
                    // 후기형이 아닌 경우 reviewType 초기화
                    if (e.target.value !== 'review') {
                      setReviewType('');
                    }
                  }}
                  className="ultra-select" style={{padding: '10px 16px', fontSize: '14px'}}
                >
                  <option value="">글의 유형을 선택해주세요</option>
                  {contentTypes.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.icon} {option.name} - {option.description}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* 후기형 선택 시 세부 유형 드롭박스 */}
              {contentType === 'review' && (
                <div>
                  <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>후기 유형</label>
                  <select
                    value={reviewType}
                    onChange={(e) => setReviewType(e.target.value)}
                    className="ultra-select" style={{padding: '10px 16px', fontSize: '14px'}}
                  >
                    <option value="">후기 유형을 선택해주세요</option>
                    {reviewTypes.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.icon} {option.name} - {option.description}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>말투 스타일</label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="ultra-select" style={{padding: '10px 16px', fontSize: '14px'}}
                >
                  <option value="">글의 말투를 선택해주세요</option>
                  {tones.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.icon} {option.name} - {option.description}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                  블로그 설명 (선택)
                </label>
                <textarea
                  value={blogDescription}
                  onChange={(e) => setBlogDescription(e.target.value)}
                  rows={3}
                  placeholder="예: 10년간 요리를 해온 주부가 운영하는 블로그, 펫샵을 운영하는 사장이 반려동물 정보를 공유하는 블로그"
                  className="ultra-input resize-none" style={{padding: '10px 16px', fontSize: '14px'}}
                />
              </div>
            </div>
            
            {/* 기본값 저장 버튼 */}
            <div className="flex justify-end pt-4 mt-4">
              <button
                onClick={saveDefaults}
                disabled={isSavingDefaults || !platform || !contentType || !tone || (contentType === 'review' && !reviewType)}
                className={`ultra-btn px-3 py-2 text-xs ${
                  (!platform || !contentType || !tone || (contentType === 'review' && !reviewType)) && !isSavingDefaults 
                    ? 'opacity-50 cursor-not-allowed' 
                    : ''
                }`}
                style={{
                  background: '#10b981',
                  borderColor: '#10b981',
                  color: 'white'
                }}
              >
                <span>{isSavingDefaults ? '저장 중...' : '기본값으로 저장'}</span>
                <span className="text-sm">{isSavingDefaults ? '⏳' : '💾'}</span>
              </button>
            </div>
          </div>

          {/* 키워드 입력 섹션 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon green" style={{width: '32px', height: '32px', fontSize: '16px'}}>🔍</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>키워드 설정</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                  메인 키워드 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="예: 블로그 마케팅"
                  className="ultra-input" style={{padding: '10px 16px', fontSize: '14px'}}
                />
              </div>
              <div>
                <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                  서브 키워드 (선택)
                </label>
                <input
                  type="text"
                  value={subKeywords}
                  onChange={(e) => setSubKeywords(e.target.value)}
                  placeholder="예: SEO, 콘텐츠 마케팅 (쉼표로 구분)"
                  className="ultra-input" style={{padding: '10px 16px', fontSize: '14px'}}
                />
              </div>
            </div>
          </div>

          {/* 추가 요청사항 섹션 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon purple" style={{width: '32px', height: '32px', fontSize: '16px'}}>✏️</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>추가 요청사항</h2>
            </div>
            
            <div>
              <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                상세 요청사항 (선택)
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                rows={3}
                placeholder="예: 숫자를 넣어주세요, 질문 형태로 만들어주세요, 따뜻한 느낌으로 써주세요"
                className="ultra-input resize-none" style={{padding: '10px 16px', fontSize: '14px'}}
              />
            </div>
          </div>

          {/* AI 제목 추천 섹션 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon orange" style={{width: '32px', height: '32px', fontSize: '16px'}}>🤖</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>AI 제목 추천</h2>
              <button
                onClick={generateTitles}
                disabled={isGenerating || !keyword.trim()}
                className="ultra-btn px-4 py-2 text-xs ml-auto"
                style={{
                  background: '#10b981',
                  borderColor: '#10b981',
                  color: 'white'
                }}
              >
                <span className="text-sm">💡</span>
                <span>제목 추천</span>
              </button>
            </div>

            {isGenerating && (
              <div className="text-center py-8">
                <div className="ultra-spinner mx-auto mb-4" style={{width: '32px', height: '32px'}}></div>
                <h3 className="text-lg font-semibold text-slate-700 mb-2">
                  💡 AI가 제목을 생성하고 있습니다...
                </h3>
                <div className="text-slate-500 text-sm">
                  <p>잠시만 기다려주세요. 곧 완료됩니다!</p>
                </div>
              </div>
            )}

            {generatedTitles.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <h3 className="text-base font-semibold text-slate-800">
                    AI가 추천하는 제목 ({generatedTitles.length}개)
                  </h3>
                </div>
                <div>
                  <label className="ultra-label" style={{fontSize: '13px', marginBottom: '6px'}}>
                    제목 선택 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedTitle}
                    onChange={(e) => setSelectedTitle(e.target.value)}
                    className="ultra-select" style={{padding: '10px 16px', fontSize: '14px'}}
                  >
                    <option value="">생성된 제목 중 하나를 선택해주세요</option>
                    {titlesWithSearch.map((item, index) => (
                      <option key={index} value={item.title} title={item.searchQuery ? `검색어: ${item.searchQuery}` : ''}>
                        📝 {item.title}
                      </option>
                    ))}
                  </select>
                  {selectedTitle && (
                    <div className="mt-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                      <p className="text-emerald-800 text-sm">
                        <span className="font-semibold">선택된 제목:</span> {selectedTitle}
                      </p>
                      {(() => {
                        const selectedItem = titlesWithSearch.find(item => item.title === selectedTitle);
                        return selectedItem?.searchQuery && (
                          <p className="text-emerald-600 text-xs mt-1">
                            <span className="font-medium">서치키워드:</span> {selectedItem.searchQuery}
                          </p>
                        );
                      })()}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 다음 버튼 */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleNext}
              disabled={!platform || !keyword.trim() || !selectedTitle}
              className="ultra-btn px-3 py-2 text-sm"
            >
              <span>다음 단계로 진행</span>
              <span className="text-sm">→</span>
            </button>
          </div>
        </div>
        </div>
      </div>
      
      {/* SimpleDialog */}
      <SimpleDialog
        isOpen={dialog.isOpen}
        onClose={() => setDialog(prev => ({ ...prev, isOpen: false }))}
        title={dialog.title}
        message={dialog.message}
        onConfirm={dialog.onConfirm}
        confirmText="확인"
        cancelText="취소"
      />
    </div>
  );
};

export default Step1;