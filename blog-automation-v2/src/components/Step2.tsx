import React, { useState, useEffect } from 'react';
import { WorkflowData } from '../App';
import { DataCollectionEngine, DataCollectionResult, AnalysisProgress } from '../services/data-collection-engine';
import { BlogWritingService, BlogWritingResult } from '../services/blog-writing-service';
import { getContentTypeName, getReviewTypeName, getToneName } from '../constants/content-options';
import SimpleDialog from './SimpleDialog';

interface Step2Props {
  data: WorkflowData;
  onNext: (data: Partial<WorkflowData>) => void;
  onBack: () => void;
  aiModelStatus: {
    information: string;
    writing: string;
    image: string;
  };
}

const Step2: React.FC<Step2Props> = ({ data, onNext, onBack, aiModelStatus }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisProgress[]>([]);
  // 기존 상태가 있으면 그것을 사용, 없으면 null
  const [collectedData, setCollectedData] = useState<DataCollectionResult | null>(
    data.collectedData ? data.collectedData as DataCollectionResult : null
  );
  const [showBlogDetails, setShowBlogDetails] = useState(false);
  const [showYouTubeDetails, setShowYouTubeDetails] = useState(false);
  
  // 글쓰기 상태 관리 - 기존 글쓰기 결과가 있으면 복원
  const [isWriting, setIsWriting] = useState(false);
  const [writingResult, setWritingResult] = useState<BlogWritingResult | null>(
    data.writingResult || null
  );
  const [retryCount, setRetryCount] = useState(0);
  const [maxRetries] = useState(2); // 최대 재시도 횟수
  
  // 이미지 프롬프트 생성 상태 관리
  const [isGeneratingImagePrompts, setIsGeneratingImagePrompts] = useState(false);
  const [imagePromptsGenerated, setImagePromptsGenerated] = useState(() => {
    // 글쓰기 결과에 이미지 프롬프트가 있으면 이미 생성된 것으로 처리
    return !!(data.writingResult?.imagePrompts && data.writingResult.imagePrompts.length > 0);
  });
  const [imagePromptError, setImagePromptError] = useState<string | null>(null);
  
  
  // 참고 검색어 관리 - 저장된 searchKeyword가 있으면 우선 사용
  const [searchKeyword, setSearchKeyword] = useState(() => {
    // 1. 이전에 Step2에서 수정한 searchKeyword가 있으면 그것을 사용
    if (data.searchKeyword) {
      return data.searchKeyword;
    }
    // 2. 없으면 기존 로직 사용
    const selectedTitleData = data.titlesWithSearch?.find(
      item => item.title === data.selectedTitle
    );
    return selectedTitleData?.searchQuery || data.keyword;
  });
  
  // 데이터 변경 시 이미지 프롬프트 생성 상태 업데이트
  useEffect(() => {
    if (data.writingResult?.imagePrompts && data.writingResult.imagePrompts.length > 0) {
      console.log('🎨 이미지 프롬프트가 이미 존재함 - 생성 완료 상태로 설정');
      setImagePromptsGenerated(true);
      setImagePromptError(null);
    }
  }, [data.writingResult?.imagePrompts]);
  
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
    // 1. 기본 설정 완료 여부 확인
    if (!data.platform) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '발행 플랫폼 선택 필요',
        message: '1단계에서 발행 플랫폼을 먼저 선택해주세요.'
      });
      return;
    }

    if (!data.contentType) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '콘텐츠 타입 선택 필요',
        message: '1단계에서 콘텐츠 타입을 먼저 선택해주세요.'
      });
      return;
    }

    if (!data.tone) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '말투 스타일 선택 필요',
        message: '1단계에서 말투 스타일을 먼저 선택해주세요.'
      });
      return;
    }

    // 2. 후기형 선택 시 후기 유형 필수 확인
    if (data.contentType === 'review' && !data.reviewType) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '후기 유형 선택 필요',
        message: '1단계에서 후기형을 선택하셨습니다.\n내돈내산 후기 또는 협찬 후기 중 하나를 선택해주세요.'
      });
      return;
    }

    // 3. 키워드 및 제목 선택 확인
    if (!data.keyword || !data.keyword.trim()) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '메인 키워드 입력 필요',
        message: '1단계에서 메인 키워드를 입력해주세요.'
      });
      return;
    }

    if (!data.selectedTitle) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '제목 선택 필요',
        message: '1단계에서 AI가 추천한 제목 중 하나를 선택해주세요.'
      });
      return;
    }

    // 4. 검색어 유효성 확인
    if (!searchKeyword.trim()) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '서치키워드 입력 필요',
        message: '분석에 사용할 서치키워드를 입력해주세요.'
      });
      return;
    }

    // 5. 정보처리 AI 연결 상태 확인
    try {
      const { LLMClientFactory } = await import('../services/llm-client-factory');
      if (!LLMClientFactory.isInformationClientAvailable()) {
        setDialog({
          isOpen: true,
          type: 'warning',
          title: '정보처리 AI 미설정',
          message: '데이터 수집 및 분석을 위해서는 정보처리 AI가 필요합니다.\n설정에서 정보처리 AI를 먼저 설정해주세요.'
        });
        return;
      }
    } catch (error) {
      console.error('LLMClientFactory 로드 실패:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: 'API 설정 확인 실패',
        message: 'API 설정을 확인할 수 없습니다. 페이지를 새로고침 후 다시 시도해주세요.'
      });
      return;
    }

    setIsAnalyzing(true);
    setCollectedData(null);
    setWritingResult(null); // 새로운 분석 시작 시 기존 글쓰기 결과 초기화
    
    try {
      // 데이터 수집 엔진 생성
      const engine = new DataCollectionEngine((progress) => {
        setAnalysisSteps(progress);
      });

      // 데이터 수집 요청 구성 (사용자가 수정한 검색어 사용)
      const request = {
        keyword: searchKeyword, // 서치키워드 (사용자가 수정 가능) - 기존 호환성
        searchKeyword: searchKeyword, // 공통 인터페이스 필드
        mainKeyword: data.keyword, // 메인키워드 (원본)
        subKeywords: data.subKeywords,
        selectedTitle: data.selectedTitle,
        platform: data.platform,
        contentType: data.contentType,
        reviewType: data.reviewType,
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

  // 자동 재시도 함수
  const handleWritingError = async (error: string) => {
    console.error('❌ 글쓰기 실패:', error);
    
    if (retryCount < maxRetries) {
      const nextRetry = retryCount + 1;
      setRetryCount(nextRetry);
      
      setDialog({
        isOpen: true,
        type: 'warning',
        title: `글쓰기 실패 (${nextRetry}/${maxRetries + 1})`,
        message: `글쓰기가 실패했습니다. 5초 후 자동으로 재시도합니다.\n\n오류: ${error}`,
        onConfirm: () => {
          setTimeout(() => {
            startWriting();
          }, 5000);
        }
      });
    } else {
      // 최대 재시도 횟수 초과
      setDialog({
        isOpen: true,
        type: 'error',
        title: '글쓰기 최종 실패',
        message: `${maxRetries + 1}회 시도 후에도 글쓰기가 실패했습니다.\n\n최종 오류: ${error}\n\n수동으로 재시도하거나 설정을 확인해주세요.`
      });
      setRetryCount(0); // 재시도 카운터 리셋
    }
  };

  // 글쓰기 실행
  const startWriting = async () => {
    if (!collectedData) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '분석 필요',
        message: '먼저 데이터 수집 및 분석을 완료해주세요.'
      });
      return;
    }

    if (!BlogWritingService.isWritingClientAvailable()) {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '글쓰기 AI 미설정',
        message: '글쓰기 AI가 설정되지 않았습니다. 설정에서 글쓰기 AI를 먼저 설정해주세요.'
      });
      return;
    }

    setIsWriting(true);
    setWritingResult(null);

    try {
      console.log('🎯 블로그 글쓰기 시작');
      
      const writingRequest = {
        selectedTitle: data.selectedTitle || '',
        searchKeyword: searchKeyword,
        mainKeyword: data.keyword || '',
        contentType: getContentTypeName(data.contentType || ''),
        tone: getToneName(data.tone || ''),
        reviewType: data.reviewType ? getReviewTypeName(data.reviewType) : undefined,
        bloggerIdentity: data.bloggerIdentity,
        subKeywords: data.subKeywords,
        blogAnalysisResult: collectedData.contentSummary,
        youtubeAnalysisResult: collectedData.youtubeAnalysis,
        crawledBlogs: collectedData.crawledBlogs // 크롤링된 블로그 데이터 (태그 추출용)
      };

      const result = await BlogWritingService.generateBlogContent(writingRequest);
      setWritingResult(result);

      if (result.success) {
        console.log('✅ 블로그 글쓰기 완료');
        setDialog({
          isOpen: true,
          type: 'success',
          title: '글쓰기 완료',
          message: '블로그 글이 성공적으로 생성되었습니다! 이제 이미지 프롬프트를 생성합니다.'
        });
        
        // 글쓰기 완료 후 자동으로 이미지 프롬프트 생성 시작
        setTimeout(() => {
          // 현재 글쓰기 결과를 함께 전달
          if (result.content) {
            generateImagePrompts(result.content, result);
          }
        }, 1000);
      } else {
        // 실패 시 자동 재시도 로직 호출
        await handleWritingError(result.error || '알 수 없는 오류');
      }

    } catch (error) {
      // 예외 발생 시 자동 재시도 로직 호출
      await handleWritingError(error.message || error.toString());
    } finally {
      setIsWriting(false);
    }
  };

  // 이미지 프롬프트 생성 함수
  const generateImagePrompts = async (blogContent: string, currentWritingResult?: BlogWritingResult) => {
    if (!blogContent) return;

    setIsGeneratingImagePrompts(true);
    setImagePromptsGenerated(false);
    setImagePromptError(null); // 이전 에러 초기화

    try {
      console.log('🎨 이미지 프롬프트 생성 시작');
      
      const imagePromptResult = await BlogWritingService.generateImagePrompts(blogContent);
      
      if (imagePromptResult.success) {
        // 현재 글쓰기 결과 또는 상태에서 가져오기
        const currentResult = currentWritingResult || writingResult;
        
        if (currentResult) {
          // 기존 글쓰기 결과에 이미지 프롬프트 추가
          const updatedResult = {
            ...currentResult,
            imagePrompts: imagePromptResult.imagePrompts || [],
            usage: currentResult.usage ? {
              promptTokens: (currentResult.usage.promptTokens || 0) + (imagePromptResult.usage?.promptTokens || 0),
              completionTokens: (currentResult.usage.completionTokens || 0) + (imagePromptResult.usage?.completionTokens || 0),
              totalTokens: (currentResult.usage.totalTokens || 0) + (imagePromptResult.usage?.totalTokens || 0)
            } : imagePromptResult.usage
          };
          
          setWritingResult(updatedResult);
          setImagePromptsGenerated(true);
          
          console.log('✅ 이미지 프롬프트 생성 완료:', imagePromptResult.imagePrompts?.length || 0, '개');
        } else {
          console.error('❌ 글쓰기 결과가 없어 이미지 프롬프트를 추가할 수 없습니다.');
          setImagePromptError('글쓰기 결과가 없어 이미지 프롬프트를 추가할 수 없습니다.');
        }
      } else {
        console.error('❌ 이미지 프롬프트 생성 실패:', imagePromptResult.error);
        setImagePromptError(imagePromptResult.error || '이미지 프롬프트 생성에 실패했습니다.');
      }

    } catch (error) {
      console.error('❌ 이미지 프롬프트 생성 중 오류:', error);
      setImagePromptError(error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setIsGeneratingImagePrompts(false);
    }
  };

  const handleNext = () => {
    if (!collectedData) {
      alert('분석을 완료해주세요.');
      return;
    }

    // 현재 상태를 저장하여 뒤로가기 시에도 유지되도록 함
    onNext({ 
      collectedData,
      writingResult: writingResult?.success ? writingResult : undefined,
      // 검색키워드 변경사항도 저장
      searchKeyword
    });
  };

  return (
    <div className="w-full h-full">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="ultra-card p-5 slide-in">
          {/* 헤더 */}
          <div className="text-center mb-4">
            <div className="relative mb-3">
              <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2 justify-center">
                <span>🔍</span>
                <span>데이터 수집 및 분석</span>
              </h1>
              <div className="absolute right-0 top-0 text-sm text-slate-500">
                정보처리 AI: {aiModelStatus.information}
              </div>
            </div>
            <p className="text-base text-slate-600 leading-relaxed max-w-2xl mx-auto">
              선택된 제목을 기반으로 AI가 멀티플랫폼에서 데이터를 수집하고 분석합니다.
            </p>
            <div className="mt-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-blue-800 text-sm font-medium mb-3">
                📝 선택된 제목: {data.selectedTitle}
              </p>
              
              {/* 키워드 정보 */}
              <div className="mb-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700 font-medium">🎯 메인 키워드:</span>
                    <span className="text-blue-600 ml-2">{data.keyword}</span>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">🔗 서브 키워드:</span>
                    <span className="text-blue-600 ml-2">
                      {data.subKeywords && data.subKeywords.length > 0 ? data.subKeywords.join(', ') : '없음'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 설정 정보 */}
              <div className="mb-2">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700 font-medium">📝 콘텐츠 유형:</span>
                    <span className="text-blue-600 ml-2">{getContentTypeName(data.contentType)}</span>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">💬 말투:</span>
                    <span className="text-blue-600 ml-2">{getToneName(data.tone)}</span>
                  </div>
                  {data.reviewType && (
                    <div>
                      <span className="text-blue-700 font-medium">⭐ 후기 유형:</span>
                      <span className="text-blue-600 ml-2">{getReviewTypeName(data.reviewType)}</span>
                    </div>
                  )}
                </div>
              </div>
              
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
                  {collectedData && (
                    <button
                      onClick={startAnalysis}
                      disabled={isAnalyzing || !searchKeyword.trim()}
                      className={`px-3 py-1 text-xs rounded transition-colors ${
                        isAnalyzing || !searchKeyword.trim()
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-blue-500 text-white hover:bg-blue-600'
                      }`}
                    >
                      🔄 재분석
                    </button>
                  )}
                </div>
                <p className="text-blue-400 text-xs">
                  💡 이 서치키워드로 데이터를 수집합니다. 제목과 연관된 서치키워드가 아니면 수정해주세요.
                  {collectedData && " 키워드 변경 후 재분석 버튼을 눌러 새로운 데이터를 수집할 수 있습니다."}
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
              <div className="flex gap-4 justify-center">
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
                <button
                  onClick={() => {
                    // 더미 데이터 생성
                    const dummyCollectedData = {
                      blogs: [
                        {
                          rank: 1,
                          title: "민생지원금 2차 신청 방법 총정리 (자격요건, 신청기간, 지급액)",
                          url: "https://blog.naver.com/example1",
                          platform: "네이버블로그"
                        },
                        {
                          rank: 2,
                          title: "🏦 민생지원금 2차 놓치면 안되는 이유 (소득기준 완화됨)",
                          url: "https://blog.naver.com/example2",
                          platform: "네이버블로그"
                        },
                        {
                          rank: 3,
                          title: "민생지원금 2차 신청 후기 - 실제 받은 금액과 사용법",
                          url: "https://blog.naver.com/example3",
                          platform: "네이버블로그"
                        }
                      ],
                      allYoutubeVideos: [
                        {
                          videoId: "test123",
                          title: "민생지원금 2차 완벽 가이드 - 신청부터 받기까지",
                          channelTitle: "경제정보TV",
                          publishedAt: "2024-09-15T00:00:00Z",
                          viewCount: 125000,
                          duration: 480,
                          priority: 95
                        },
                        {
                          videoId: "test456",
                          title: "민생지원금 2차 신청 실수하면 안되는 포인트 5가지",
                          channelTitle: "재정정보채널",
                          publishedAt: "2024-09-14T00:00:00Z",
                          viewCount: 89000,
                          duration: 360,
                          priority: 88
                        }
                      ],
                      selectedYoutubeVideos: [
                        {
                          videoId: "test123",
                          title: "민생지원금 2차 완벽 가이드 - 신청부터 받기까지",
                          channelName: "경제정보TV",
                          viewCount: 125000,
                          duration: 480,
                          priority: 95,
                          relevanceReason: "민생지원금 2차 신청 방법에 대한 완벽한 가이드를 제공하여 제목과 정확히 일치"
                        }
                      ],
                      youtube: [
                        {
                          videoId: "test123",
                          title: "민생지원금 2차 완벽 가이드 - 신청부터 받기까지",
                          channelName: "경제정보TV",
                          publishedAt: "2024-09-15T00:00:00Z",
                          duration: 480,
                          viewCount: 125000,
                          priority: 95,
                          summary: "민생지원금 2차 신청 방법에 대해 자세히 설명드리겠습니다. 이번에는 소득 기준이 완화되어 더 많은 분들이 혜택을 받을 수 있게 되었습니다."
                        },
                        {
                          videoId: "test456",
                          title: "민생지원금 2차 신청 실수하면 안되는 포인트 5가지",
                          channelName: "재정정보채널",
                          publishedAt: "2024-09-14T00:00:00Z",
                          duration: 360,
                          viewCount: 89000,
                          priority: 88,
                          summary: "민생지원금 2차 신청할 때 놓치기 쉬운 중요한 포인트들을 알려드리겠습니다."
                        }
                      ],
                      selectedBlogs: [
                        {
                          title: "민생지원금 2차 신청 방법 총정리 (자격요건, 신청기간, 지급액)",
                          url: "https://blog.naver.com/example1",
                          relevanceReason: "신청 방법과 자격 요건을 체계적으로 설명하여 검색 의도와 정확히 일치"
                        }
                      ],
                      crawledBlogs: [
                        {
                          title: "민생지원금 2차 신청 방법 총정리 (자격요건, 신청기간, 지급액)",
                          url: "https://blog.naver.com/example1",
                          success: true,
                          contentLength: 4580,
                          imageCount: 8,
                          gifCount: 1,
                          videoCount: 0,
                          tags: ["민생지원금", "정부지원금", "소비쿠폰", "생활지원", "경제정책"],
                          textContent: "민생지원금 2차 신청이 시작되었습니다..."
                        }
                      ],
                      contentSummary: {
                        competitor_titles: ["민생지원금 2차 신청 방법 총정리"],
                        core_keywords: ["민생지원금 2차", "신청 방법", "자격 요건"],
                        essential_content: ["소득 하위 90% 가구 대상", "1인당 13만원 지급"],
                        key_points: ["기준 중위소득 상향 조정"],
                        improvement_opportunities: ["실제 신청 화면 캡처"]
                      },
                      youtubeAnalysis: {
                        video_summaries: [
                          {
                            video_number: 1,
                            key_points: "건강보험료 기준으로 자격 확인"
                          }
                        ],
                        common_themes: ["소득 기준 완화"],
                        practical_tips: ["카드사 앱 이용"],
                        expert_insights: ["기준 중위소득 상향 조정"],
                        blog_suggestions: ["신청 과정 상세 설명"]
                      },
                      summary: {
                        totalSources: 5,
                        dataQuality: 'high' as const,
                        processingTime: 12500,
                        recommendations: ["실제 신청 화면 캡처 추가", "소득 기준 자세한 설명"]
                      }
                    };
                    
                    // 더미 글쓰기 결과도 함께 생성
                    const dummyWritingResult = {
                      success: true,
                      content: `민생지원금 2차 놓치면 손해! 지금 바로 신청하세요 (신청 방법 포함)

**📢 핵심 답변 먼저 확인하세요!**

민생지원금 2차는 **2024년 12월 31일**까지 신청 가능하며, 소득 하위 90% 가구에게 **1인당 13만원**이 지급됩니다. 건강보험료 기준으로 빠르게 자격 확인이 가능하고, 카드사 앱이나 지자체 앱에서 간단히 신청할 수 있습니다. 지금 바로 신청하지 않으면 혜택을 받을 수 없으니 서둘러 확인해보세요!

(이미지)

## ✅ 나도 받을 수 있을까? 지급 대상 자격 체크리스트

**소득 기준 (다음 중 하나라도 해당되면 신청 가능)**
✓ 건강보험료 본인부담금이 기준 이하인 가구
- 1인 가구: 월 97,000원 이하
- 2인 가구: 월 162,000원 이하  
- 3인 가구: 월 209,000원 이하
- 4인 가구: 월 255,000원 이하

(이미지)

**재산 기준 (모두 충족해야 함)**
✓ 재산세 과세표준액 12억원 이하
✓ 금융소득 연 2,000만원 이하
✓ 기존 복지급여 수급자도 신청 가능

**⚠️ 중요한 변화점**
기준 중위소득이 상향 조정되어 기존에 탈락했던 분들도 다시 신청해볼 필요가 있습니다!

(이미지)

## 📱 민생지원금 2차 신청 방법 단계별 가이드

### 1단계: 신청 채널 선택하기

| 신청 방법 | 특징 | 준비물 | 소요시간 |
|---------|------|--------|----------|
| 카드사 앱/홈페이지 | 가장 간편, 24시간 가능 | 신분증, 카드 | 5분 |
| 지자체 앱 | 지역별 맞춤 서비스 | 신분증, 주소 확인 | 7분 |
| 행정복지센터 | 대면 상담 가능 | 신분증, 가족관계증명서 | 20분 |

(이미지)

### 2단계: 온라인 신청 상세 과정

**카드사 앱 신청 방법**
1. 본인 명의 카드사 앱 접속
2. '민생지원금 2차' 메뉴 선택
3. 본인인증 (휴대폰, 공인인증서)
4. 가구원 정보 입력
5. 소득·재산 정보 확인
6. 신청 완료 및 접수번호 확인

(이미지)

민생지원금 2차는 경제적 부담을 덜어주는 소중한 기회입니다. 복잡한 절차 없이 간단한 온라인 신청으로 13만원의 혜택을 받을 수 있으니, 자격 요건을 확인하고 지금 바로 신청하시기 바랍니다!

#민생지원금2차 #민생지원금신청 #소비쿠폰 #정부지원금 #생활지원금`,
                      imagePrompts: [
                        {
                          index: 1,
                          position: "지급 대상 자격 체크리스트 섹션",
                          context: "민생지원금 신청 자격을 확인하는 모습",
                          prompt: "Korean person checking eligibility criteria for government financial support on smartphone, documents and calculator on desk, clean home office setting"
                        },
                        {
                          index: 2,
                          position: "온라인 신청 상세 과정 섹션",
                          context: "카드사 앱에서 신청하는 화면",
                          prompt: "Mobile phone screen showing Korean government support application interface, clean modern app design, user-friendly application process"
                        },
                        {
                          index: 3,
                          position: "마무리 섹션",
                          context: "혜택을 받는 모습을 보여주는 이미지",
                          prompt: "Happy Korean family receiving government financial support, positive atmosphere, showing gratitude and relief, warm lighting"
                        }
                      ],
                      usage: {
                        totalTokens: 15420,
                        promptTokens: 8240,
                        completionTokens: 7180
                      }
                    };
                    
                    setCollectedData(dummyCollectedData);
                    setWritingResult(dummyWritingResult);
                    console.log('🧪 더미 데이터 및 글쓰기 결과 생성됨');
                  }}
                  className="ultra-btn px-6 py-3 text-sm"
                  style={{
                    background: '#f59e0b',
                    borderColor: '#f59e0b',
                    color: 'white'
                  }}
                >
                  <span className="text-lg">🧪</span>
                  <span>더미 데이터 테스트</span>
                </button>
              </div>
            </div>
          )}

          {isAnalyzing && (
            <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
              <div className="section-header" style={{marginBottom: '12px'}}>
                <div className="section-icon orange" style={{width: '28px', height: '28px', fontSize: '14px'}}>⚡</div>
                <h2 className="section-title" style={{fontSize: '14px'}}>분석 진행 상황</h2>
                <div className="text-xs text-slate-500 ml-auto">
                  {analysisSteps.filter(s => s.status === 'completed').length} / {analysisSteps.length} 완료
                </div>
              </div>

              <div className="space-y-2">
                {analysisSteps.map((step, index) => (
                  <div key={index} className="border border-slate-200 rounded-lg p-3 bg-white">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">{getStatusIcon(step.status)}</span>
                        <span className="font-medium text-sm text-slate-800">{step.step}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {step.status === 'running' && (
                          <div className="ultra-spinner" style={{width: '16px', height: '16px'}}></div>
                        )}
                        <span className="text-xs text-slate-500">{step.progress}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-500 ${
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
                  <div className="grid grid-cols-3 gap-6 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        {collectedData.crawledBlogs.filter(b => b.success).length + collectedData.youtube.length}
                      </div>
                      <div className="text-xs text-slate-600">총 데이터소스</div>
                      <div className="text-xs text-slate-400 mt-1">
                        블로그 {collectedData.crawledBlogs.filter(b => b.success).length}개 + 유튜브 {collectedData.youtube.length}개
                      </div>
                      <div className="text-xs text-slate-400">
                        최종 분석 완료
                      </div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{collectedData.crawledBlogs.filter(b => b.success).length}</div>
                      <div className="text-xs text-slate-600 mb-2">블로그 분석</div>
                      <button
                        onClick={() => setShowBlogDetails(true)}
                        className="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                      >
                        상세보기
                      </button>
                      <div className="text-xs text-slate-400 mt-1">
                        🖼️ 이미지 {(() => {
                          const successBlogs = collectedData.crawledBlogs?.filter(b => b.success) || [];
                          if (successBlogs.length === 0) return '0';
                          const avgImages = successBlogs.reduce((sum, blog) => {
                            const imageCount = (blog.imageCount || 0) + (blog.gifCount || 0);
                            return sum + imageCount;
                          }, 0) / successBlogs.length;
                          return avgImages.toFixed(1);
                        })()} | 🎬 동영상 {(() => {
                          const successBlogs = collectedData.crawledBlogs?.filter(b => b.success) || [];
                          if (successBlogs.length === 0) return '0';
                          const avgVideos = successBlogs.reduce((sum, blog) => sum + (blog.videoCount || 0), 0) / successBlogs.length;
                          return avgVideos.toFixed(1);
                        })()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-red-600">{collectedData.youtube.length}</div>
                      <div className="text-xs text-slate-600 mb-1">유튜브 분석</div>
                      <button
                        onClick={() => setShowYouTubeDetails(true)}
                        className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
                      >
                        상세보기
                      </button>
                      <div className="text-xs text-slate-400 mt-1">
                        자막 추출 {collectedData.youtube.filter(v => v.summary && v.summary.length > 100 && !v.summary.includes('추출 실패')).length}개 성공
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 콘텐츠 분석 결과 - 50/50 사이드바이사이드 레이아웃 */}
              {((collectedData.contentSummary || collectedData.contentSummaryRaw) || (collectedData.youtubeAnalysis || collectedData.youtubeAnalysisRaw)) && (
                <div className="section-card" style={{padding: '12px', marginBottom: '12px'}}>
                  <div className="flex gap-6">
                    {/* 블로그 콘텐츠 분석 - 왼쪽 */}
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <span>📝</span>
                        <span>블로그 콘텐츠 분석</span>
                      </h4>
                      {(collectedData.contentSummary || collectedData.contentSummaryRaw) ? (
                        collectedData.contentSummary ? (
                          <div className="space-y-4">
                            {/* 경쟁 블로그 제목들 */}
                            {collectedData.contentSummary.competitor_titles && collectedData.contentSummary.competitor_titles.length > 0 && (
                              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                                <h5 className="font-medium text-slate-900 mb-3">🏆 경쟁 블로그 제목들</h5>
                                <ul className="space-y-1">
                                  {collectedData.contentSummary.competitor_titles.map((title, idx) => (
                                    <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                                      <span className="text-blue-500 mt-1">•</span>
                                      <span>{title}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 핵심 키워드 */}
                            {collectedData.contentSummary.core_keywords && collectedData.contentSummary.core_keywords.length > 0 && (
                              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                <h5 className="font-medium text-slate-900 mb-3">🔑 핵심 키워드</h5>
                                <div className="flex flex-wrap gap-2">
                                  {collectedData.contentSummary.core_keywords.map((keyword, idx) => (
                                    <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                                      {keyword}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 필수 내용 */}
                            {collectedData.contentSummary.essential_content && collectedData.contentSummary.essential_content.length > 0 && (
                              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                                <h5 className="font-medium text-slate-900 mb-3">✅ 필수 내용</h5>
                                <ul className="space-y-1">
                                  {collectedData.contentSummary.essential_content.map((content, idx) => (
                                    <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                                      <span className="text-green-500 mt-1">•</span>
                                      <span>{content}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 주요 포인트 */}
                            {collectedData.contentSummary.key_points && collectedData.contentSummary.key_points.length > 0 && (
                              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">🎯 주요 포인트</h5>
                                <ul className="space-y-1">
                                  {collectedData.contentSummary.key_points.map((point, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-purple-500 mt-0.5">•</span>
                                      <span>{point}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 개선 기회 */}
                            {collectedData.contentSummary.improvement_opportunities && collectedData.contentSummary.improvement_opportunities.length > 0 && (
                              <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">💡 개선 기회</h5>
                                <ul className="space-y-1">
                                  {collectedData.contentSummary.improvement_opportunities.map((opportunity, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-orange-500 mt-0.5">•</span>
                                      <span>{opportunity}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                            <div className="text-xs text-slate-700 whitespace-pre-wrap">
                              {collectedData.contentSummaryRaw}
                            </div>
                          </div>
                        )
                      ) : (
                        <div className="bg-slate-100 rounded-lg p-3 border border-slate-200 text-center">
                          <span className="text-xs text-slate-500">블로그 분석 데이터 없음</span>
                        </div>
                      )}
                    </div>

                    {/* 구분선 */}
                    <div className="w-px bg-slate-300"></div>

                    {/* 유튜브 콘텐츠 분석 - 오른쪽 */}
                    <div className="flex-1">
                      <h4 className="font-medium text-sm text-slate-900 mb-2 flex items-center gap-2">
                        <span>📺</span>
                        <span>유튜브 콘텐츠 분석</span>
                      </h4>
                      {(collectedData.youtubeAnalysis || collectedData.youtubeAnalysisRaw) ? (
                        collectedData.youtubeAnalysis ? (
                          <div className="space-y-3">
                            {/* 영상별 핵심 내용 요약 */}
                            {collectedData.youtubeAnalysis.video_summaries && collectedData.youtubeAnalysis.video_summaries.length > 0 && (
                              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">📹 영상별 핵심 내용 요약</h5>
                                <div className="space-y-1.5">
                                  {collectedData.youtubeAnalysis.video_summaries.map((summary, idx) => (
                                    <div key={idx} className="bg-white rounded p-2 border border-slate-100">
                                      <div className="flex items-start gap-2">
                                        <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded flex-shrink-0">
                                          {summary.video_number}번
                                        </span>
                                        <span className="text-xs text-slate-700">{summary.key_points}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 공통 주제 및 트렌드 */}
                            {collectedData.youtubeAnalysis.common_themes && collectedData.youtubeAnalysis.common_themes.length > 0 && (
                              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">🔄 공통 주제 및 트렌드</h5>
                                <ul className="space-y-1">
                                  {collectedData.youtubeAnalysis.common_themes.map((theme, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-blue-500 mt-0.5">•</span>
                                      <span>{theme}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 실용적 정보 및 팁 */}
                            {collectedData.youtubeAnalysis.practical_tips && collectedData.youtubeAnalysis.practical_tips.length > 0 && (
                              <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">💡 실용적 정보 및 팁</h5>
                                <ul className="space-y-1">
                                  {collectedData.youtubeAnalysis.practical_tips.map((tip, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-green-500 mt-0.5">•</span>
                                      <span>{tip}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 전문가 인사이트 */}
                            {collectedData.youtubeAnalysis.expert_insights && collectedData.youtubeAnalysis.expert_insights.length > 0 && (
                              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">🎯 전문가 인사이트</h5>
                                <ul className="space-y-1">
                                  {collectedData.youtubeAnalysis.expert_insights.map((insight, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-purple-500 mt-0.5">•</span>
                                      <span>{insight}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* 블로그 활용 제안 */}
                            {collectedData.youtubeAnalysis.blog_suggestions && collectedData.youtubeAnalysis.blog_suggestions.length > 0 && (
                              <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                                <h5 className="font-medium text-xs text-slate-900 mb-2">📝 블로그 활용 제안</h5>
                                <ul className="space-y-1">
                                  {collectedData.youtubeAnalysis.blog_suggestions.map((suggestion, idx) => (
                                    <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                                      <span className="text-orange-500 mt-0.5">•</span>
                                      <span>{suggestion}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                            <div className="text-xs text-slate-700 whitespace-pre-wrap">
                              {collectedData.youtubeAnalysisRaw}
                            </div>
                          </div>
                        )
                      ) : (
                        <div className="bg-slate-100 rounded-lg p-3 border border-slate-200 text-center">
                          <span className="text-xs text-slate-500">유튜브 분석 데이터 없음</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* 글쓰기 카드 */}
              <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
                <div className="section-header" style={{marginBottom: '16px'}}>
                  <div className="section-icon purple" style={{width: '32px', height: '32px', fontSize: '16px'}}>✍️</div>
                  <h2 className="section-title" style={{fontSize: '16px'}}>블로그 글쓰기</h2>
                  <div className="text-sm text-slate-500 ml-auto">
                    글쓰기 AI: {BlogWritingService.getWritingClientInfo()}
                  </div>
                </div>

                {!isWriting && !writingResult && (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">✍️</div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">
                      AI 글쓰기를 시작하세요
                    </h3>
                    <p className="text-slate-600 mb-4">
                      수집된 데이터를 바탕으로 AI가 블로그 글을 작성합니다
                    </p>
                    <button
                      onClick={startWriting}
                      disabled={!collectedData || !BlogWritingService.isWritingClientAvailable()}
                      className={`ultra-btn px-6 py-3 text-sm ${
                        !collectedData || !BlogWritingService.isWritingClientAvailable() 
                          ? 'opacity-50 cursor-not-allowed' 
                          : ''
                      }`}
                      style={{
                        background: collectedData && BlogWritingService.isWritingClientAvailable() ? '#8b5cf6' : '#94a3b8',
                        borderColor: collectedData && BlogWritingService.isWritingClientAvailable() ? '#8b5cf6' : '#94a3b8',
                        color: 'white'
                      }}
                    >
                      <span className="text-lg">🚀</span>
                      <span>글쓰기 시작하기</span>
                    </button>
                    {!BlogWritingService.isWritingClientAvailable() && (
                      <p className="text-red-500 text-sm mt-2">
                        글쓰기 AI가 설정되지 않았습니다. 설정에서 글쓰기 AI를 먼저 설정해주세요.
                      </p>
                    )}
                  </div>
                )}

                {isWriting && (
                  <div className="text-center py-8">
                    <div className="ultra-spinner mx-auto mb-4" style={{width: '32px', height: '32px'}}></div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">
                      AI가 글을 작성하고 있습니다...
                    </h3>
                    <p className="text-slate-600">
                      분석된 데이터를 바탕으로 고품질 블로그 글을 생성 중입니다
                    </p>
                  </div>
                )}

                {writingResult && (
                  <div className="space-y-4">
                    {writingResult.success ? (
                      <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-green-500 text-lg">✅</span>
                          <h3 className="font-semibold text-green-800">글쓰기 완료</h3>
                          {writingResult.usage && (
                            <span className="text-green-600 text-sm ml-auto">
                              토큰: {writingResult.usage.totalTokens.toLocaleString()} 
                              (입력: {writingResult.usage.promptTokens.toLocaleString()}, 출력: {writingResult.usage.completionTokens.toLocaleString()})
                            </span>
                          )}
                        </div>
                        
                        <div className="bg-white rounded-lg p-4 border border-green-200 max-h-96 overflow-y-auto">
                          <div className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                            {BlogWritingService.processWritingResult(writingResult.content || '')}
                          </div>
                        </div>
                        
                        <div className="flex justify-between items-center mt-3">
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(BlogWritingService.processWritingResult(writingResult.content || ''));
                                setDialog({
                                  isOpen: true,
                                  type: 'success',
                                  title: '복사 완료',
                                  message: '블로그 글이 클립보드에 복사되었습니다.'
                                });
                              }}
                              className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
                            >
                              📋 복사하기
                            </button>
                            <button
                              onClick={() => {
                                setWritingResult(null);
                                setIsGeneratingImagePrompts(false);
                                setImagePromptsGenerated(false);
                              }}
                              className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                            >
                              🔄 다시 쓰기
                            </button>
                          </div>
                          <div className="text-xs text-slate-500">
                            {(() => {
                              const content = BlogWritingService.processWritingResult(writingResult.content || '');
                              const withoutSpaces = content.replace(/\s/g, '').length;
                              const withSpaces = content.length;
                              return `글자수: ${withoutSpaces.toLocaleString()} / ${withSpaces.toLocaleString()}(공백포함)`;
                            })()}
                          </div>
                        </div>
                        
                      </div>
                    ) : (
                      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-red-500 text-lg">❌</span>
                          <h3 className="font-semibold text-red-800">글쓰기 실패</h3>
                        </div>
                        <p className="text-red-700 text-sm mb-3">
                          {writingResult.error}
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setWritingResult(null);
                              setRetryCount(0); // 재시도 카운터 리셋
                              // 실패 후 재시도 시 바로 글쓰기 시작
                              setTimeout(() => startWriting(), 100);
                            }}
                            className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                          >
                            🔄 즉시 재시도
                          </button>
                          <button
                            onClick={() => {
                              // 분석 데이터와 이전 설정은 유지하고 글쓰기 결과만 초기화
                              setWritingResult(null);
                              setRetryCount(0); // 재시도 카운터 리셋
                              setIsGeneratingImagePrompts(false);
                              setImagePromptsGenerated(false);
                              setImagePromptError(null);
                              
                              // 글쓰기 다시 시작
                              setTimeout(() => {
                                if (collectedData) {
                                  startWriting();
                                }
                              }, 500);
                            }}
                            className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                          >
                            🔄 정보유지 재시도
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* 이미지 프롬프트 생성 카드 - 글쓰기 완료 후 표시 */}
                {writingResult && writingResult.success && (
                  <div className="space-y-4 mt-4">
                    <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-purple-500 text-lg">🎨</span>
                        <h4 className="font-semibold text-purple-800">이미지 프롬프트 생성</h4>
                        {isGeneratingImagePrompts && (
                          <div className="ultra-spinner ml-2" style={{width: '16px', height: '16px'}}></div>
                        )}
                      </div>
                      
                      {!isGeneratingImagePrompts && !writingResult.imagePrompts?.length && !imagePromptError && (
                        <div className="text-purple-600 text-sm">
                          ⏳ 잠시 후 이미지 프롬프트 생성이 시작됩니다...
                        </div>
                      )}
                      
                      {!isGeneratingImagePrompts && imagePromptError && (
                        <div className="space-y-3">
                          <div className="flex items-start gap-2 text-red-600 text-sm">
                            <span className="text-red-500 text-lg">❌</span>
                            <div>
                              <div className="font-medium">이미지 프롬프트 생성 실패</div>
                              <div className="text-xs mt-1 text-red-500">{imagePromptError}</div>
                            </div>
                          </div>
                          <button
                            onClick={() => writingResult?.content && generateImagePrompts(writingResult.content)}
                            className="px-4 py-2 bg-purple-500 text-white text-sm rounded-lg hover:bg-purple-600 transition-colors flex items-center gap-2"
                          >
                            <span>🔄</span>
                            <span>다시 시도</span>
                          </button>
                        </div>
                      )}
                      
                      {isGeneratingImagePrompts && (
                        <div className="flex items-center gap-3 text-purple-600">
                          <div className="text-sm">
                            🔄 AI가 글 내용을 분석하여 이미지 프롬프트를 생성하고 있습니다...
                          </div>
                        </div>
                      )}
                      
                      {!isGeneratingImagePrompts && writingResult.imagePrompts && writingResult.imagePrompts.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-green-500 text-lg">✅</span>
                            <span className="font-medium text-green-800">
                              이미지 프롬프트 생성 완료 ({writingResult.imagePrompts.length}개)
                            </span>
                          </div>
                          <div className="space-y-3 max-h-64 overflow-y-auto">
                            {writingResult.imagePrompts.map((imagePrompt, idx) => (
                              <div key={idx} className="bg-white rounded-lg p-3 border border-purple-200">
                                <div className="flex items-start gap-3">
                                  <div className="flex-shrink-0 w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                    {imagePrompt.index}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="font-medium text-sm text-purple-900">
                                        📍 {imagePrompt.position}
                                      </span>
                                    </div>
                                    <p className="text-xs text-slate-600 mb-2">
                                      {imagePrompt.context}
                                    </p>
                                    <div className="bg-slate-50 rounded p-2 border border-slate-200">
                                      <span className="text-xs font-medium text-slate-700">AI 프롬프트:</span>
                                      <p className="text-xs text-slate-800 mt-1">
                                        {imagePrompt.prompt}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="mt-3 text-xs text-purple-600">
                            💡 이 프롬프트들은 3단계에서 이미지 생성에 활용됩니다
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
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
      
      {/* 블로그 상세보기 모달 */}
      {showBlogDetails && collectedData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowBlogDetails(false)}>
          <div className="bg-white rounded-lg w-11/12 h-5/6 flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">📝 블로그 상세 분석 결과</h3>
              <button 
                onClick={() => setShowBlogDetails(false)}
                className="text-slate-500 hover:text-slate-700 text-xl"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              
              {/* 크롤링된 블로그 본문 데이터 - 맨 위에 펼쳐진 상태 */}
              {collectedData.crawledBlogs && collectedData.crawledBlogs.filter(blog => blog.success).length > 0 && (
                <div className="section-card" style={{padding: '16px'}}>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <span>📄</span>
                    <span>크롤링된 블로그 본문 ({collectedData.crawledBlogs.filter(blog => blog.success).length}개 성공)</span>
                  </h4>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {collectedData.crawledBlogs.filter(blog => blog.success).map((blog, idx: number) => (
                      <div key={idx} className="border rounded-lg p-3 bg-blue-50 border-blue-200">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold bg-blue-500">
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
                                  <span className="font-medium text-blue-700">본문:</span>
                                  <span className="text-blue-600 ml-1">{blog.contentLength.toLocaleString()}자</span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-700">이미지:</span>
                                  <span className="text-blue-600 ml-1">{blog.imageCount}개</span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-700">GIF:</span>
                                  <span className="text-blue-600 ml-1">{blog.gifCount}개</span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-700">동영상:</span>
                                  <span className="text-blue-600 ml-1">{blog.videoCount}개</span>
                                </div>
                              </div>
                              {blog.textContent && (
                                <div className="mt-2 p-2 bg-white border border-blue-200 rounded text-xs">
                                  <span className="font-medium text-blue-700">본문 미리보기:</span>
                                  <p className="text-slate-600 mt-1">
                                    {blog.textContent.substring(0, 300)}
                                    {blog.textContent.length > 300 && '...'}
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
                </div>
              )}

              {/* AI가 선별한 블로그 - 접힌 상태 */}
              {collectedData.selectedBlogs && collectedData.selectedBlogs.length > 0 && (
                <div className="section-card" style={{padding: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>🤖</span>
                      <span>AI가 선별한 블로그 ({collectedData.selectedBlogs.length}개)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.selectedBlogs.map((blog, idx: number) => (
                        <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-green-50 border-green-200">
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
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* 전체 블로그 수집 결과 - 접힌 상태 */}
              <div className="section-card" style={{padding: '16px'}}>
                <details>
                  <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                    <span>📋</span>
                    <span>전체 블로그 수집 결과 ({collectedData.blogs.length}개)</span>
                  </summary>
                <div className="space-y-3 max-h-96 overflow-y-auto">
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
            </div>
          </div>
        </div>
      )}

      {/* 유튜브 상세보기 모달 */}
      {showYouTubeDetails && collectedData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowYouTubeDetails(false)}>
          <div className="bg-white rounded-lg w-11/12 h-5/6 flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">📺 유튜브 상세 분석 결과</h3>
              <button 
                onClick={() => setShowYouTubeDetails(false)}
                className="text-slate-500 hover:text-slate-700 text-xl"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              
              {/* 자막 추출된 유튜브 영상 - 맨 위에 펼쳐진 상태 */}
              {collectedData.youtube && collectedData.youtube.filter(video => video.summary && video.summary.length > 100).length > 0 && (
                <div className="section-card" style={{padding: '16px'}}>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <span>🎬</span>
                    <span>자막 추출된 유튜브 영상 ({collectedData.youtube.filter(video => video.summary && video.summary.length > 100).length}개 성공)</span>
                  </h4>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {collectedData.youtube.filter(video => video.summary && video.summary.length > 100).map((video, idx: number) => (
                      <div key={idx} className="border rounded-lg p-3 bg-red-50 border-red-200">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold bg-red-500">
                            {idx + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm text-slate-900 leading-relaxed mb-2">
                              {video.title}
                            </p>
                            
                            <div className="mt-2">
                              <div className="grid grid-cols-4 gap-3 mb-2 text-xs">
                                <div>
                                  <span className="font-medium text-red-700">채널:</span>
                                  <span className="text-red-600 ml-1">{video.channelName}</span>
                                </div>
                                <div>
                                  <span className="font-medium text-red-700">길이:</span>
                                  <span className="text-red-600 ml-1">{Math.floor(video.duration / 60)}분</span>
                                </div>
                                <div>
                                  <span className="font-medium text-red-700">조회수:</span>
                                  <span className="text-red-600 ml-1">{video.viewCount ? (video.viewCount >= 10000 ? `${(video.viewCount / 10000).toFixed(1)}만회` : `${video.viewCount.toLocaleString()}회`) : 'N/A'}</span>
                                </div>
                                <div>
                                  <span className="font-medium text-red-700">자막:</span>
                                  <span className="text-red-600 ml-1">{video.summary ? `${video.summary.length.toLocaleString()}자` : '없음'}</span>
                                </div>
                              </div>
                              {video.summary && (
                                <div className="mt-2 p-2 bg-white border border-red-200 rounded text-xs">
                                  <span className="font-medium text-red-700">자막 미리보기:</span>
                                  <p className="text-slate-600 mt-1">
                                    {video.summary.substring(0, 300)}
                                    {video.summary.length > 300 && '...'}
                                  </p>
                                </div>
                              )}
                            </div>
                            
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                              <a 
                                href={`https://www.youtube.com/watch?v=${video.videoId}`}
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-red-500 hover:text-red-700 underline"
                              >
                                🔗 YouTube에서 보기
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI가 선별한 유튜브 영상 - 접힌 상태 */}
              {collectedData.selectedYoutubeVideos && collectedData.selectedYoutubeVideos.length > 0 && (
                <div className="section-card" style={{padding: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>🤖</span>
                      <span>AI가 선별한 유튜브 영상 ({collectedData.selectedYoutubeVideos.length}개)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.selectedYoutubeVideos.map((video, idx: number) => (
                      <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-green-50 border-green-200">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                            {idx + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm text-slate-900 leading-relaxed">
                              {video.title}
                            </p>
                            <p className="text-xs text-green-600 mt-1">
                              💡 {video.relevanceReason}
                            </p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                              <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                                {video.channelName}
                              </span>
                              <span className="text-slate-400">
                                조회수: {video.viewCount >= 10000 ? `${(video.viewCount / 10000).toFixed(1)}만회` : `${video.viewCount.toLocaleString()}회`}
                              </span>
                              <span className="text-slate-400">
                                {Math.floor(video.duration / 60)}분
                              </span>
                              <a 
                                href={`https://www.youtube.com/watch?v=${video.videoId}`}
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-red-500 hover:text-red-700 underline"
                              >
                                🔗 YouTube에서 보기
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

              {/* 전체 유튜브 수집 결과 - 접힌 상태 */}
              {collectedData.allYoutubeVideos && collectedData.allYoutubeVideos.length > 0 && (
                <div className="section-card" style={{padding: '16px'}}>
                  <details>
                    <summary className="font-semibold text-slate-900 mb-3 flex items-center gap-2 cursor-pointer">
                      <span>📋</span>
                      <span>전체 유튜브 수집 결과 ({collectedData.allYoutubeVideos.length}개)</span>
                    </summary>
                    <div className="space-y-3 max-h-96 overflow-y-auto mt-3">
                      {collectedData.allYoutubeVideos.map((video, idx: number) => (
                        <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                              {idx + 1}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-sm text-slate-900 leading-relaxed">
                                {video.title}
                              </p>
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                                  {video.channelTitle}
                                </span>
                                <span className="text-slate-400">
                                  조회수: {video.viewCount ? (video.viewCount >= 10000 ? `${(video.viewCount / 10000).toFixed(1)}만회` : `${video.viewCount.toLocaleString()}회`) : 'N/A'}
                                </span>
                                <a 
                                  href={`https://www.youtube.com/watch?v=${video.videoId}`}
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-red-500 hover:text-red-700 underline"
                                >
                                  🔗 YouTube에서 보기
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
            </div>
          </div>
        </div>
      )}
      
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