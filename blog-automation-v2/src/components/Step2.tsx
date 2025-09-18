import React, { useState, useEffect } from 'react';
import { WorkflowData } from '../App';
import { DataCollectionEngine, DataCollectionResult, AnalysisProgress } from '../services/data-collection-engine';
import SimpleDialog from './SimpleDialog';

interface Step2Props {
  data: WorkflowData;
  onNext: (data: Partial<WorkflowData>) => void;
  onBack: () => void;
}

const Step2: React.FC<Step2Props> = ({ data, onNext, onBack }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisProgress[]>([]);
  const [collectedData, setCollectedData] = useState<DataCollectionResult | null>(null);
  
  // Step1에서 정의된 옵션들과 동일하게 정의
  const contentTypes = [
    { id: 'info', name: '정보/가이드형' },
    { id: 'review', name: '후기/리뷰형' },
    { id: 'compare', name: '비교/추천형' },
    { id: 'howto', name: '노하우형' }
  ];

  const reviewTypes = [
    { id: 'self-purchase', name: '내돈내산 후기' },
    { id: 'sponsored', name: '협찬 후기' },
    { id: 'experience', name: '체험단 후기' },
    { id: 'rental', name: '대여/렌탈 후기' }
  ];

  const tones = [
    { id: 'formal', name: '정중한 존댓말' },
    { id: 'casual', name: '친근한 반말' },
    { id: 'friendly', name: '친근한 존댓말' }
  ];

  // ID를 한국어 이름으로 변환하는 함수들
  const getContentTypeName = (id: string) => contentTypes.find(c => c.id === id)?.name || id;
  const getReviewTypeName = (id: string) => reviewTypes.find(r => r.id === id)?.name || id;
  const getToneName = (id: string) => tones.find(t => t.id === id)?.name || id;
  
  // 참고 검색어 관리
  const [searchKeyword, setSearchKeyword] = useState(() => {
    const selectedTitleData = data.titlesWithSearch?.find(
      item => item.title === data.selectedTitle
    );
    return selectedTitleData?.searchQuery || data.keyword;
  });
  const [isEditingKeyword, setIsEditingKeyword] = useState(false);
  
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

  const startAnalysis = async () => {
    // 검색어 유효성 확인
    if (!searchKeyword.trim()) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '검색어 필요',
        message: '참고 검색어를 입력해주세요.'
      });
      return;
    }

    setIsAnalyzing(true);
    setCollectedData(null);
    
    try {
      // 데이터 수집 엔진 생성
      const engine = new DataCollectionEngine((progress) => {
        setAnalysisSteps(progress);
      });

      // 데이터 수집 요청 구성 (사용자가 수정한 검색어 사용)
      const request = {
        keyword: searchKeyword, // 서치키워드 (사용자가 수정 가능)
        mainKeyword: data.keyword, // 메인키워드 (원본)
        subKeywords: data.subKeywords,
        selectedTitle: data.selectedTitle,
        platform: data.platform,
        contentType: data.contentType,
        contentTypeDescription: data.contentTypeDescription,
        reviewType: data.reviewType,
        reviewTypeDescription: data.reviewTypeDescription,
        mode: 'fast' as const
      };

      console.log(`🔍 검색에 사용할 키워드: "${searchKeyword}" (원본: "${data.keyword}")`);

      console.log('🚀 데이터 수집 시작:', request);

      // 실제 데이터 수집 및 분석 실행
      const result = await engine.collectAndAnalyze(request);
      
      setCollectedData(result);
      console.log('✅ 데이터 수집 완료:', result);

    } catch (error) {
      console.error('❌ 데이터 수집 실패:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '데이터 수집 오류',
        message: `데이터 수집 중 오류가 발생했습니다:\n${error.message || error}\n\n정보처리 AI가 설정되어 있는지 확인해주세요.`
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const handleNext = () => {
    if (!collectedData) {
      alert('분석을 완료해주세요.');
      return;
    }

    onNext({ collectedData });
  };

  return (
    <div className="w-full h-full">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="ultra-card p-5 slide-in">
          {/* 헤더 */}
          <div className="text-center mb-4">
            <div className="inline-flex items-center gap-3 mb-3">
              <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <span>🔍</span>
                <span>데이터 수집 및 분석</span>
              </h1>
            </div>
            <p className="text-base text-slate-600 leading-relaxed max-w-2xl mx-auto">
              선택된 제목을 기반으로 AI가 멀티플랫폼에서 데이터를 수집하고 분석합니다.
            </p>
            <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-blue-800 text-sm font-medium mb-2">
                📝 선택된 제목: {data.selectedTitle}
              </p>
              
              <p className="text-blue-500 text-sm mb-2">
                🎯 메인 키워드: {data.keyword} {data.subKeywords && data.subKeywords.length > 0 && `+ ${data.subKeywords.join(', ')}`} | 📝 콘텐츠 유형: {getContentTypeName(data.contentType)} | 💬 말투: {getToneName(data.tone)}{data.reviewType && ` | ⭐ 후기 유형: ${getReviewTypeName(data.reviewType)}`}
              </p>
              
              {/* 서치 키워드 편집 */}
              <div className="mb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-blue-600 text-sm font-medium">🔍 서치키워드:</span>
                  <input
                    type="text"
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    disabled={isAnalyzing}
                    className={`flex-1 px-2 py-1 text-sm border rounded focus:outline-none ${
                      isAnalyzing 
                        ? 'border-gray-300 bg-gray-100 cursor-not-allowed'
                        : 'border-blue-300 focus:border-blue-500'
                    }`}
                    placeholder="검색에 사용할 키워드를 입력하세요"
                  />
                </div>
                <p className="text-blue-400 text-xs">
                  💡 이 서치키워드로 데이터를 수집합니다. 제목과 연관된 서치키워드가 아니면 수정해주세요.
                </p>
              </div>
            </div>
          </div>

          {!isAnalyzing && !collectedData && (
            <div className="section-card text-center py-12" style={{padding: '48px 32px', marginBottom: '16px'}}>
              <div className="mb-6">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-xl font-semibold text-slate-900 mb-3">
                  지능형 데이터 수집을 시작할 준비가 되었습니다
                </h3>
                <p className="text-slate-600 leading-relaxed">
                  AI가 네이버 블로그, 쇼핑, 유튜브에서 데이터를 수집하고<br />
                  SEO 최적화 인사이트를 제공합니다
                </p>
              </div>
              <button
                onClick={startAnalysis}
                className="ultra-btn px-6 py-3 text-sm"
                style={{
                  background: '#10b981',
                  borderColor: '#10b981',
                  color: 'white'
                }}
              >
                <span className="text-lg">🚀</span>
                <span>분석 시작하기</span>
              </button>
            </div>
          )}

          {isAnalyzing && (
            <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
              <div className="section-header" style={{marginBottom: '16px'}}>
                <div className="section-icon orange" style={{width: '32px', height: '32px', fontSize: '16px'}}>⚡</div>
                <h2 className="section-title" style={{fontSize: '16px'}}>분석 진행 상황</h2>
                <div className="text-sm text-slate-500 ml-auto">
                  {analysisSteps.filter(s => s.status === 'completed').length} / {analysisSteps.length} 완료
                </div>
              </div>

              <div className="space-y-3">
                {analysisSteps.map((step, index) => (
                  <div key={index} className="border border-slate-200 rounded-lg p-4 bg-white">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getStatusIcon(step.status)}</span>
                        <span className="font-medium text-slate-800">{step.step}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {step.status === 'running' && (
                          <div className="ultra-spinner" style={{width: '16px', height: '16px'}}></div>
                        )}
                        <span className="text-sm text-slate-500">{step.progress}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${
                          step.status === 'completed' ? 'bg-green-500' :
                          step.status === 'running' ? 'bg-blue-500' :
                          step.status === 'error' ? 'bg-red-500' : 'bg-slate-300'
                        }`}
                        style={{ width: `${step.progress}%` }}
                      />
                    </div>
                    {step.message && (
                      <p className="text-xs text-red-500 mt-2">{step.message}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {collectedData && (
            <div className="space-y-4">
              {/* 분석 결과 헤더 */}
              <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
                <div className="section-header" style={{marginBottom: '16px'}}>
                  <div className="section-icon green" style={{width: '32px', height: '32px', fontSize: '16px'}}>📊</div>
                  <h2 className="section-title" style={{fontSize: '16px'}}>분석 결과</h2>
                  <div className="text-sm text-slate-500 ml-auto">
                    처리 시간: {(collectedData.summary.processingTime / 1000).toFixed(1)}초
                  </div>
                </div>

                {/* 요약 정보 */}
                <div className="bg-slate-50 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">{collectedData.summary.totalSources}</div>
                      <div className="text-xs text-slate-600">총 데이터 소스</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{collectedData.blogs.length}</div>
                      <div className="text-xs text-slate-600">블로그 분석</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${
                        collectedData.summary.dataQuality === 'high' ? 'text-green-600' :
                        collectedData.summary.dataQuality === 'medium' ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {collectedData.summary.dataQuality === 'high' ? '높음' :
                         collectedData.summary.dataQuality === 'medium' ? '보통' : '낮음'}
                      </div>
                      <div className="text-xs text-slate-600">데이터 품질</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 키워드 분석 & SEO 인사이트 */}
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="section-card" style={{padding: '16px'}}>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <span>🎯</span>
                    <span>키워드 분석</span>
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm text-slate-600 block mb-1">메인 키워드:</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">
                        {collectedData.keywords.mainKeyword}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm text-slate-600 block mb-2">연관 키워드:</span>
                      <div className="flex flex-wrap gap-1">
                        {collectedData.keywords.relatedKeywords.map((kw: string, idx: number) => (
                          <span key={idx} className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm text-slate-600 block mb-2">추천 키워드:</span>
                      <div className="flex flex-wrap gap-1">
                        {collectedData.keywords.suggestions.map((kw: string, idx: number) => (
                          <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="section-card" style={{padding: '16px'}}>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <span>📈</span>
                    <span>SEO 최적화 가이드</span>
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">제목 길이:</span>
                      <span className="font-medium">{collectedData.seoInsights.titleLength}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">키워드 밀도:</span>
                      <span className="font-medium">{collectedData.seoInsights.keywordDensity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">글자 수:</span>
                      <span className="font-medium">{collectedData.seoInsights.contentLength}</span>
                    </div>
                    <div className="pt-2 border-t border-slate-200">
                      <span className="text-slate-600 block mb-1">구조:</span>
                      <span className="text-xs text-slate-500">
                        {typeof collectedData.seoInsights.headingStructure === 'string' 
                          ? collectedData.seoInsights.headingStructure 
                          : JSON.stringify(collectedData.seoInsights.headingStructure)}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 block mb-1">이미지:</span>
                      <span className="text-xs text-slate-500">
                        {typeof collectedData.seoInsights.imageRecommendations === 'string' 
                          ? collectedData.seoInsights.imageRecommendations 
                          : JSON.stringify(collectedData.seoInsights.imageRecommendations)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 크롤링된 블로그 본문 데이터 (성공한 것만 표시) */}
              {collectedData.crawledBlogs && collectedData.crawledBlogs.filter(blog => blog.success).length > 0 && (
                <div className="section-card" style={{padding: '16px', marginBottom: '16px'}}>
                  <details open>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>📝</span>
                      <span>크롤링된 블로그 본문 ({collectedData.crawledBlogs.filter(blog => blog.success).length}개 성공)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.crawledBlogs.filter(blog => blog.success).map((blog, idx: number) => (
                        <div key={idx} className="border rounded-lg p-3 bg-green-50 border-green-200">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold bg-green-500">
                              {idx + 1}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-sm text-slate-900 leading-relaxed mb-2">
                                {blog.title}
                              </p>
                              
                              {/* 해시태그 표시 */}
                              {blog.tags && blog.tags.length > 0 && (
                                <div className="mb-2">
                                  <span className="text-xs text-slate-600 mr-2">태그:</span>
                                  <div className="flex flex-wrap gap-1">
                                    {blog.tags.map((tag, tagIdx) => (
                                      <span key={tagIdx} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                        #{tag}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              <div className="mt-2">
                                <div className="grid grid-cols-4 gap-3 mb-2 text-xs">
                                  <div>
                                    <span className="font-medium text-green-700">본문:</span>
                                    <span className="text-green-600 ml-1">{blog.contentLength.toLocaleString()}자</span>
                                  </div>
                                  <div>
                                    <span className="font-medium text-green-700">이미지:</span>
                                    <span className="text-green-600 ml-1">{blog.imageCount}개</span>
                                  </div>
                                  <div>
                                    <span className="font-medium text-green-700">GIF:</span>
                                    <span className="text-green-600 ml-1">{blog.gifCount}개</span>
                                  </div>
                                  <div>
                                    <span className="font-medium text-green-700">동영상:</span>
                                    <span className="text-green-600 ml-1">{blog.videoCount}개</span>
                                  </div>
                                </div>
                                {blog.textContent && (
                                  <div className="mt-2 p-2 bg-white border border-green-200 rounded text-xs">
                                    <span className="font-medium text-green-700">본문 미리보기:</span>
                                    <p className="text-slate-600 mt-1">
                                      {blog.textContent.substring(0, 200)}
                                      {blog.textContent.length > 200 && '...'}
                                    </p>
                                  </div>
                                )}
                              </div>
                              
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                <a 
                                  href={blog.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-500 hover:text-blue-700 underline"
                                >
                                  🔗 블로그 보기
                                </a>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* AI가 선별한 상위 10개 블로그 (접혀짐) */}
              {collectedData.selectedBlogs && collectedData.selectedBlogs.length > 0 && (
                <div className="section-card" style={{padding: '16px', marginBottom: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>🤖</span>
                      <span>AI가 선별한 블로그 ({collectedData.selectedBlogs.length}개)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.selectedBlogs.map((blog, idx: number) => {
                        // 크롤링된 데이터 찾기
                        const crawledData = collectedData.crawledBlogs?.find(crawled => crawled.url === blog.url);
                        
                        return (
                          <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                {idx + 1}
                              </div>
                              <div className="flex-1">
                                <p className="font-medium text-sm text-slate-900 leading-relaxed">
                                  {blog.title}
                                </p>
                                <p className="text-xs text-green-600 mt-1">
                                  💡 {blog.relevanceReason}
                                </p>
                                
                                
                                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                  <a 
                                    href={blog.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-500 hover:text-blue-700 underline"
                                  >
                                    🔗 블로그 보기
                                  </a>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </details>
                </div>
              )}

              {/* 전체 블로그 수집 결과 (접기/펼치기) */}
              {collectedData.blogs.length > 0 && (
                <div className="section-card" style={{padding: '16px', marginBottom: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>📝</span>
                      <span>전체 블로그 수집 결과 ({collectedData.blogs.length}개)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.blogs.map((blog, idx: number) => (
                        <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                              {blog.rank}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-sm text-slate-900 leading-relaxed">
                                {blog.title}
                              </p>
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                                  {blog.platform}
                                </span>
                                <a 
                                  href={blog.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-500 hover:text-blue-700 underline"
                                >
                                  🔗 블로그 보기
                                </a>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* 유튜브 분석 결과 (간단 표시) */}
              {collectedData.youtube.length > 0 && (
                <div className="section-card" style={{padding: '16px', marginBottom: '16px'}}>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <span>📺</span>
                    <span>유튜브 분석 ({collectedData.youtube.length}개)</span>
                  </h4>
                  <div className="space-y-3">
                    {collectedData.youtube.map((video, idx: number) => (
                      <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-white">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 pr-4">
                            <p className="font-medium text-sm text-slate-900 leading-relaxed">{video.title}</p>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-500 flex-shrink-0">
                            <span>📺 {video.channelName}</span>
                            <span>👥 {video.subscriberCount ? `${(video.subscriberCount / 10000).toFixed(1)}만` : 'N/A'}</span>
                            <span>👍 {video.likeCount || 'N/A'}</span>
                            <span>⏱️ {Math.floor(video.duration / 60)}분</span>
                          </div>
                        </div>
                        {video.summary && (
                          <div className="mt-2 p-2 bg-slate-50 rounded text-xs text-slate-600">
                            <span className="font-medium text-slate-700">📝 내용 요약: </span>
                            {video.summary.substring(0, 150)}{video.summary.length > 150 && '...'}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 블로그 콘텐츠 요약 분석 결과 */}
              {collectedData.contentSummary && (
                <div className="section-card" style={{padding: '16px', marginBottom: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>📊</span>
                      <span>블로그 콘텐츠 요약 분석</span>
                    </summary>
                    <div className="mt-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-sm text-slate-700 whitespace-pre-wrap">
                        {collectedData.contentSummary}
                      </div>
                    </div>
                  </details>
                </div>
              )}

              {/* 추천사항 */}
              <div className="section-card" style={{padding: '16px'}}>
                <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <span>💡</span>
                  <span>AI 추천사항</span>
                </h4>
                <div className="space-y-2">
                  {collectedData.summary.recommendations.map((rec, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-green-500 mt-0.5">•</span>
                      <span className="text-slate-700">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 네비게이션 */}
          <div className="flex justify-between pt-6 border-t border-slate-200">
            <button
              onClick={onBack}
              className="ultra-btn px-4 py-2 text-sm"
              style={{
                background: 'white',
                borderColor: '#e2e8f0',
                color: '#64748b'
              }}
            >
              <span>←</span>
              <span>이전 단계</span>
            </button>
            <button
              onClick={handleNext}
              disabled={!collectedData}
              className={`ultra-btn px-4 py-2 text-sm ${
                !collectedData ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              style={{
                background: collectedData ? '#2563eb' : '#94a3b8',
                borderColor: collectedData ? '#2563eb' : '#94a3b8',
                color: 'white'
              }}
            >
              <span>다음 단계</span>
              <span>→</span>
            </button>
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

export default Step2;